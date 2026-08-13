import os
import sys
import importlib

dbutils = globals().get("dbutils")

if dbutils:
    dbutils.notebook.run("nb_bronze_ingest", 0)
    dbutils.notebook.run("nb_silver_transform", 0)
    dbutils.notebook.run("nb_gold_aggregate", 0)
else:
    importlib.import_module("notebooks.nb_bronze_ingest")
    importlib.import_module("notebooks.nb_silver_transform")
    importlib.import_module("notebooks.nb_gold_aggregate")

print("FreshMart Medallion ETL pipeline executed successfully.")
