import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "freshmart_data"

RAW_BASE_PATH = os.getenv("RAW_BASE_PATH", str(DATA_DIR))
DELTA_BASE_PATH = os.getenv("DELTA_BASE_PATH", str(BASE_DIR / "delta"))

BRONZE_PATH = f"{DELTA_BASE_PATH}/bronze"
SILVER_PATH = f"{DELTA_BASE_PATH}/silver"
GOLD_PATH = f"{DELTA_BASE_PATH}/gold"

CITIES = ["Delhi", "Mumbai", "Bengaluru"]
