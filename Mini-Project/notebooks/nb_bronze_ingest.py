import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

raw_base_path = os.getenv("RAW_BASE_PATH", "/dbfs/raw")
bronze_base_path = os.getenv("DELTA_BASE_PATH", "/dbfs/delta") + "/bronze"
fmt = os.getenv("STORAGE_FORMAT", "delta")

def save_df(df, path):
    try:
        df.write.format(fmt).mode("overwrite").save(path)
    except Exception:
        df.write.format("parquet").mode("overwrite").save(path)

df_orders_raw = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "false")
    .option("recursiveFileLookup", "true")
    .csv(f"{raw_base_path}/orders")
    .withColumn("_ingested_date", F.current_date())
    .withColumn("_source_file", F.input_file_name())
)

save_df(df_orders_raw, f"{bronze_base_path}/raw_orders")

df_items_raw = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "false")
    .option("recursiveFileLookup", "true")
    .csv(f"{raw_base_path}/order_items")
    .withColumn("_ingested_date", F.current_date())
    .withColumn("_source_file", F.input_file_name())
)

save_df(df_items_raw, f"{bronze_base_path}/raw_order_items")

df_cust_raw = (
    spark.read
    .option("multiline", "true")
    .json(f"{raw_base_path}/customers/customers.json")
    .withColumn("_ingested_date", F.current_date())
    .withColumn("_source_file", F.input_file_name())
)

save_df(df_cust_raw, f"{bronze_base_path}/raw_customers")

df_del_raw = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "false")
    .option("recursiveFileLookup", "true")
    .csv(f"{raw_base_path}/delivery")
    .withColumn("_ingested_date", F.current_date())
    .withColumn("_source_file", F.input_file_name())
)

save_df(df_del_raw, f"{bronze_base_path}/raw_delivery_logs")
