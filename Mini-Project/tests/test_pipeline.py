import os
import unittest
from pyspark.sql import SparkSession

class TestFreshMartPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder.getOrCreate()
        cls.delta_path = os.getenv("DELTA_BASE_PATH", os.path.join(os.path.dirname(__file__), "..", "delta"))

    def _load(self, path):
        try:
            return self.spark.read.format("delta").load(path)
        except Exception:
            return self.spark.read.format("parquet").load(path)

    def test_bronze_tables_exist(self):
        bronze_orders = self._load(f"{self.delta_path}/bronze/raw_orders")
        self.assertGreater(bronze_orders.count(), 0)
        self.assertIn("_ingested_date", bronze_orders.columns)
        self.assertIn("_source_file", bronze_orders.columns)

    def test_silver_pii_masking(self):
        silver_cust = self._load(f"{self.delta_path}/silver/customers")
        self.assertGreater(silver_cust.count(), 0)
        self.assertIn("email_hash", silver_cust.columns)
        self.assertNotIn("email", silver_cust.columns)
        first_row = silver_cust.first()
        self.assertEqual(len(first_row["email_hash"]), 64)

    def test_gold_daily_revenue(self):
        gold_rev = self._load(f"{self.delta_path}/gold/daily_revenue_by_city")
        self.assertGreater(gold_rev.count(), 0)
        self.assertIn("total_revenue", gold_rev.columns)

if __name__ == "__main__":
    unittest.main()
