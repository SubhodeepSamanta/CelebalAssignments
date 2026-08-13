import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DecimalType, DoubleType

spark = SparkSession.builder.getOrCreate()

bronze_base_path = os.getenv("DELTA_BASE_PATH", "/dbfs/delta") + "/bronze"
silver_base_path = os.getenv("DELTA_BASE_PATH", "/dbfs/delta") + "/silver"
fmt = os.getenv("STORAGE_FORMAT", "delta")

def load_df(path):
    try:
        return spark.read.format(fmt).load(path)
    except Exception:
        return spark.read.format("parquet").load(path)

def save_df(df, path):
    try:
        df.write.format(fmt).mode("overwrite").save(path)
    except Exception:
        df.write.format("parquet").mode("overwrite").save(path)

df_bronze_items = load_df(f"{bronze_base_path}/raw_order_items")

discount_col_name = "discount_pct" if "discount_pct" in df_bronze_items.columns else "discount"

df_silver_items = (
    df_bronze_items
    .filter(F.col("item_id").isNotNull())
    .dropDuplicates(["item_id"])
    .withColumn("qty", F.col("qty").cast(IntegerType()))
    .withColumn("unit_price", F.col("unit_price").cast(DecimalType(10, 2)))
    .withColumn("discount_pct", F.col(discount_col_name).cast(DecimalType(5, 2)))
    .withColumn(
        "net_price",
        F.round(
            F.col("qty") * F.col("unit_price") * (1 - (F.coalesce(F.col("discount_pct"), F.lit(0)) / 100)),
            2
        ).cast(DecimalType(10, 2))
    )
    .withColumn(
        "discount_amount",
        F.round(
            F.col("qty") * F.col("unit_price") * (F.coalesce(F.col("discount_pct"), F.lit(0)) / 100),
            2
        ).cast(DecimalType(10, 2))
    )
    .select(
        "item_id", "order_id", "product_id", "product_name",
        "category", "qty", "unit_price", "discount_pct",
        "discount_amount", "net_price", "_ingested_date"
    )
)

save_df(df_silver_items, f"{silver_base_path}/order_items")

df_bronze_orders = load_df(f"{bronze_base_path}/raw_orders")

df_order_financials = (
    df_silver_items
    .groupBy("order_id")
    .agg(
        F.sum("net_price").alias("order_total"),
        F.sum("discount_amount").alias("total_discount")
    )
)

df_silver_orders = (
    df_bronze_orders
    .filter(F.col("order_id").isNotNull())
    .dropDuplicates(["order_id"])
    .withColumn("order_date", F.to_timestamp("order_date"))
    .withColumn("city", F.trim(F.col("city")))
    .withColumn("payment_mode", F.trim(F.col("payment_mode")))
    .withColumn("status", F.lower(F.trim(F.col("status"))))
    .join(df_order_financials, "order_id", "left")
    .withColumn("order_total", F.coalesce(F.col("order_total"), F.lit(0.00)).cast(DecimalType(10, 2)))
    .withColumn("total_discount", F.coalesce(F.col("total_discount"), F.lit(0.00)).cast(DecimalType(10, 2)))
    .select(
        "order_id", "customer_id", "order_date", "city",
        "payment_mode", "status", "order_total", "total_discount", "_ingested_date"
    )
)

save_df(df_silver_orders, f"{silver_base_path}/orders")

df_bronze_cust = load_df(f"{bronze_base_path}/raw_customers")

df_silver_cust = (
    df_bronze_cust
    .filter(F.col("customer_id").isNotNull())
    .dropDuplicates(["customer_id"])
    .withColumn("name", F.trim(F.col("name")))
    .withColumn("city", F.trim(F.col("city")))
    .withColumn("registered_on", F.to_date("registered_on"))
    .withColumn("loyalty_points", F.col("loyalty_points").cast(IntegerType()))
    .withColumn("email_hash", F.sha2(F.lower(F.trim(F.col("email"))), 256))
    .withColumn("phone_hash", F.sha2(F.trim(F.col("phone")), 256))
    .select(
        "customer_id", "name", "email_hash", "phone_hash",
        "city", "registered_on", "loyalty_points", "_ingested_date"
    )
)

save_df(df_silver_cust, f"{silver_base_path}/customers")

df_bronze_del = load_df(f"{bronze_base_path}/raw_delivery_logs")

distance_col = "distance_km" if "distance_km" in df_bronze_del.columns else "dist_km"

df_silver_del = (
    df_bronze_del
    .filter(F.col("delivery_id").isNotNull())
    .dropDuplicates(["delivery_id"])
    .withColumn("pickup_time", F.to_timestamp("pickup_time"))
    .withColumn("delivery_time", F.to_timestamp("delivery_time"))
    .withColumn("dist_km", F.col(distance_col).cast(DoubleType()))
    .withColumn("status", F.lower(F.trim(F.col("status"))))
    .withColumn("zone", F.trim(F.col("zone")))
    .withColumn(
        "delivery_duration_mins",
        F.round(
            (F.unix_timestamp("delivery_time") - F.unix_timestamp("pickup_time")) / 60,
            2
        ).cast(DoubleType())
    )
    .withColumn(
        "is_incomplete",
        F.when(F.col("delivery_time").isNull() | (F.col("status") != "success"), True).otherwise(False)
    )
    .select(
        "delivery_id", "order_id", "rider_id", "pickup_time",
        "delivery_time", "zone", "dist_km", "status",
        "delivery_duration_mins", "is_incomplete", "_ingested_date"
    )
)

save_df(df_silver_del, f"{silver_base_path}/delivery_logs")
