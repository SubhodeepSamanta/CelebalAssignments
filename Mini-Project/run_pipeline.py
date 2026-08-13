import sys
import os

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import importlib
from pyspark.sql import SparkSession

try:
    delta_module = importlib.import_module("delta")
    configure_spark_with_delta_pip = getattr(delta_module, "configure_spark_with_delta_pip")
    builder = (
        SparkSession.builder
        .appName("FreshMartPipeline")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
except Exception:
    spark = SparkSession.builder.appName("FreshMartPipeline").getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

from src.data_generator import generate_customers_json

generate_customers_json()

raw_dir = os.path.join(os.path.dirname(__file__), "freshmart_data")
delta_dir = os.path.join(os.path.dirname(__file__), "delta")

os.environ["RAW_BASE_PATH"] = raw_dir
os.environ["DELTA_BASE_PATH"] = delta_dir

importlib.import_module("notebooks.nb_bronze_ingest")
importlib.import_module("notebooks.nb_silver_transform")
importlib.import_module("notebooks.nb_gold_aggregate")

print("FreshMart Medallion ETL pipeline executed successfully.")

spark.stop()
os._exit(0)
