import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, DoubleType, IntegerType

spark = SparkSession.builder.getOrCreate()

silver_base_path = os.getenv("DELTA_BASE_PATH", "/dbfs/delta") + "/silver"
gold_base_path = os.getenv("DELTA_BASE_PATH", "/dbfs/delta") + "/gold"
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

df_orders = load_df(f"{silver_base_path}/orders")
df_items = load_df(f"{silver_base_path}/order_items")
df_cust = load_df(f"{silver_base_path}/customers")
df_del = load_df(f"{silver_base_path}/delivery_logs")

df_daily_rev = (
    df_orders
    .filter(F.col("status") != "cancelled")
    .withColumn("order_day", F.to_date("order_date"))
    .groupBy("order_day", "city")
    .agg(
        F.round(F.sum("order_total"), 2).cast(DecimalType(12, 2)).alias("total_revenue"),
        F.countDistinct("order_id").alias("total_orders"),
        F.round(F.avg("order_total"), 2).cast(DecimalType(10, 2)).alias("avg_basket_size")
    )
    .orderBy(F.desc("order_day"), "city")
)

save_df(df_daily_rev, f"{gold_base_path}/daily_revenue_by_city")

df_product_returns = (
    df_items
    .join(df_orders.select("order_id", "status"), "order_id", "inner")
    .groupBy("category", "product_id", "product_name")
    .agg(
        F.sum("qty").alias("total_units_sold"),
        F.countDistinct("order_id").alias("total_orders"),
        F.sum(F.when(F.col("status") == "returned", F.col("qty")).otherwise(0)).alias("returned_units"),
        F.countDistinct(F.when(F.col("status") == "returned", F.col("order_id"))).alias("returned_orders")
    )
    .withColumn(
        "return_rate_pct",
        F.round(
            (F.col("returned_units") / F.when(F.col("total_units_sold") == 0, 1).otherwise(F.col("total_units_sold"))) * 100,
            2
        ).cast(DoubleType())
    )
    .orderBy(F.desc("return_rate_pct"), F.desc("returned_units"))
)

save_df(df_product_returns, f"{gold_base_path}/product_return_summary")

df_zone_perf = (
    df_del
    .groupBy("zone")
    .agg(
        F.count("delivery_id").alias("total_deliveries"),
        F.count(F.when(F.col("status") == "success", 1)).alias("successful_deliveries"),
        F.count(F.when(F.col("status") != "success", 1)).alias("failed_deliveries"),
        F.round(F.avg(F.when(F.col("status") == "success", F.col("delivery_duration_mins"))), 2).alias("avg_delivery_time_mins"),
        F.round(F.avg("dist_km"), 2).alias("avg_distance_km")
    )
    .withColumn(
        "failure_rate_pct",
        F.round(
            (F.col("failed_deliveries") / F.when(F.col("total_deliveries") == 0, 1).otherwise(F.col("total_deliveries"))) * 100,
            2
        ).cast(DoubleType())
    )
    .orderBy(F.desc("failure_rate_pct"), F.desc("total_deliveries"))
)

save_df(df_zone_perf, f"{gold_base_path}/delivery_zone_performance")

df_cust_metrics = (
    df_orders
    .filter(F.col("customer_id").isNotNull() & (F.col("customer_id") != "") & (F.col("status") != "cancelled"))
    .groupBy("customer_id")
    .agg(
        F.countDistinct("order_id").alias("total_orders"),
        F.round(F.sum("order_total"), 2).cast(DecimalType(12, 2)).alias("total_spend"),
        F.max("order_date").alias("last_order_date"),
        F.round(F.avg("order_total"), 2).cast(DecimalType(10, 2)).alias("avg_order_value")
    )
)

df_cust_summary = (
    df_cust
    .join(df_cust_metrics, "customer_id", "left")
    .withColumn("total_orders", F.coalesce(F.col("total_orders"), F.lit(0)).cast(IntegerType()))
    .withColumn("total_spend", F.coalesce(F.col("total_spend"), F.lit(0.00)).cast(DecimalType(12, 2)))
    .withColumn("avg_order_value", F.coalesce(F.col("avg_order_value"), F.lit(0.00)).cast(DecimalType(10, 2)))
    .select(
        "customer_id", "name", "city", "registered_on",
        "loyalty_points", "total_orders", "total_spend",
        "avg_order_value", "last_order_date"
    )
    .orderBy(F.desc("total_spend"))
)

save_df(df_cust_summary, f"{gold_base_path}/customer_summary")
