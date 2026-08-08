"""
Shared configuration.

Every stage of the pipeline imports its paths and its constants from here, so
there is exactly one place to edit if the folder layout or the data volume moves.
Importing this module has no side effects other than creating output folders on
demand via ensure_dirs().
"""

from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
QUARANTINE_DIR = ROOT / "data" / "quarantine"
SQL_DIR = ROOT / "sql"
QUERY_DIR = SQL_DIR / "queries"
OUTPUT_DIR = ROOT / "output"
RESULTS_DIR = OUTPUT_DIR / "query_results"

SCHEMA_PATH = SQL_DIR / "schema.sql"
DB_PATH = OUTPUT_DIR / "ecommerce.db"
QUALITY_REPORT_MD = OUTPUT_DIR / "data_quality_report.md"
QUALITY_REPORT_JSON = OUTPUT_DIR / "data_quality_report.json"

TABLES = ("customers", "products", "orders", "order_items")

ORDER_STATUSES = ("PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED")
CUSTOMER_TYPES = ("REGULAR", "PREMIUM", "VIP")

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

SEED = 42
N_CUSTOMERS = 800
N_PRODUCTS = 500
HISTORY_START = date(2024, 8, 1)
HISTORY_END = date(2026, 8, 1)

REFERENCE_DATE = datetime(2026, 8, 1, 23, 59, 59)


def ensure_dirs() -> None:
    """Create the directories the pipeline writes into. Safe to call repeatedly."""
    for folder in (RAW_DIR, CLEAN_DIR, QUARANTINE_DIR, OUTPUT_DIR, RESULTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)
