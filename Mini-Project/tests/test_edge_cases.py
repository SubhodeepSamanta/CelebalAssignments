"""
Part 5 - edge case tests.

Each function covers one of the four questions in the brief and checks it twice:
once against the cleaning functions, and once against the database constraints
that would catch it if cleaning ever regressed.

Run:  python tests/test_edge_cases.py      (or pytest tests, if pytest is installed)
"""

from __future__ import annotations

import sqlite3
import sys
import traceback
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config
from src.clean_data import check_referential_integrity, clean_order_items, clean_orders

ORDER_COLUMNS = ["order_id", "customer_id", "order_date", "status", "region_code"]
ITEM_COLUMNS = ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"]

PRODUCTS = pd.DataFrame([["PROD001", "Test Widget", "Home", "Decor", 10.0]],
                        columns=["product_id", "product_name", "category", "subcategory", "cost_price"])


def make_orders(rows: list[list[str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=ORDER_COLUMNS, dtype=str)


def make_items(rows: list[list[str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=ITEM_COLUMNS, dtype=str)


def memory_db() -> sqlite3.Connection:
    """Empty database with the real schema and one valid parent row per table."""
    connection = sqlite3.connect(":memory:")
    connection.executescript(config.SCHEMA_PATH.read_text(encoding="utf-8"))
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("INSERT INTO customers VALUES ('CUST001', 'Test Buyer', 'a@b.com', '2025-01-01', 'REGULAR')")
    connection.execute("INSERT INTO products  VALUES ('PROD001', 'Test Widget', 'Home', 'Decor', 10.0)")
    connection.execute("INSERT INTO orders    VALUES ('ORD001', 'CUST001', '2026-01-05 10:00:00', 'DELIVERED', 'NORTH')")
    return connection


def raises_integrity_error(connection: sqlite3.Connection, sql: str) -> bool:
    try:
        connection.execute(sql)
    except sqlite3.IntegrityError:
        return True
    return False


def test_order_item_references_a_missing_order():
    """An order_item whose order_id was never issued must not reach the database."""
    orders = make_orders([["ORD001", "CUST001", "2026-01-05 10:00:00", "DELIVERED", "NORTH"]])
    items = make_items([
        ["ITEM001", "ORD001", "PROD001", "2", "10.00", "0"],
        ["ITEM002", "ORD404", "PROD001", "1", "10.00", "0"],
    ])

    orphans = check_referential_integrity(items, orders)
    assert list(orphans["item_id"]) == ["ITEM002"], "the orphan should be reported"

    cleaned = clean_order_items(items, clean_orders(orders), PRODUCTS)
    assert list(cleaned["item_id"]) == ["ITEM001"], "the orphan should not survive cleaning"

    connection = memory_db()
    assert raises_integrity_error(
        connection,
        "INSERT INTO order_items VALUES ('ITEM002', 'ORD404', 'PROD001', 1, 10.0, 0, 0)",
    ), "the foreign key should reject it even if cleaning let it through"
    connection.close()


def test_discount_percent_above_100():
    """A discount over 100 is clamped, so a sale can never produce negative revenue."""
    orders = make_orders([["ORD001", "CUST001", "2026-01-05 10:00:00", "DELIVERED", "NORTH"]])
    items = make_items([
        ["ITEM001", "ORD001", "PROD001", "2", "50.00", "150"],
        ["ITEM002", "ORD001", "PROD001", "1", "50.00", "20"],
    ])

    cleaned = clean_order_items(items, clean_orders(orders), PRODUCTS)
    clamped = cleaned.loc[cleaned["item_id"] == "ITEM001", "discount_percent"].iloc[0]
    assert clamped == 100, f"expected the discount clamped to 100, got {clamped}"

    revenue = cleaned["quantity"] * cleaned["unit_price"] * (1 - cleaned["discount_percent"] / 100)
    assert revenue.min() >= 0, "clamping must leave every sale line at zero or above"
    assert round(revenue.iloc[0], 2) == 0.0, "a 100% discount is a free item, not a refund"

    connection = memory_db()
    assert raises_integrity_error(
        connection,
        "INSERT INTO order_items VALUES ('ITEM003', 'ORD001', 'PROD001', 1, 50.0, 150, 0)",
    ), "the CHECK constraint should reject a discount outside 0-100"
    connection.close()


def test_quantity_is_zero():
    """A line for zero units is not a transaction, so it is dropped."""
    orders = make_orders([["ORD001", "CUST001", "2026-01-05 10:00:00", "DELIVERED", "NORTH"]])
    items = make_items([
        ["ITEM001", "ORD001", "PROD001", "0", "50.00", "10"],
        ["ITEM002", "ORD001", "PROD001", "-2", "50.00", "10"],
        ["ITEM003", "ORD001", "PROD001", "3", "50.00", "10"],
    ])

    cleaned = clean_order_items(items, clean_orders(orders), PRODUCTS)
    assert "ITEM001" not in set(cleaned["item_id"]), "zero-quantity line should be dropped"
    assert "ITEM002" in set(cleaned["item_id"]), "negative quantity is a return, not an error"
    assert cleaned.loc[cleaned["item_id"] == "ITEM002", "is_return"].iloc[0] == 1

    connection = memory_db()
    assert raises_integrity_error(
        connection,
        "INSERT INTO order_items VALUES ('ITEM001', 'ORD001', 'PROD001', 0, 50.0, 10, 0)",
    ), "the CHECK constraint should reject quantity = 0"
    connection.close()


def test_order_date_in_the_future():
    """Future-dated orders are quarantined; a past date on the same batch survives."""
    future = (config.REFERENCE_DATE.replace(year=config.REFERENCE_DATE.year + 1)
              .strftime(config.TIMESTAMP_FORMAT))
    orders = make_orders([
        ["ORD001", "CUST001", "2026-01-05 10:00:00", "DELIVERED", "NORTH"],
        ["ORD002", "CUST001", future, "PLACED", "NORTH"],
        ["ORD003", "CUST001", "05-01-2026", "SHIPPED", "NORTH"],
    ])

    cleaned = clean_orders(orders)
    assert "ORD002" not in set(cleaned["order_id"]), "future-dated order should be dropped"
    assert set(cleaned["order_id"]) == {"ORD001", "ORD003"}

    reparsed = cleaned.loc[cleaned["order_id"] == "ORD003", "order_date"].iloc[0]
    assert reparsed == "2026-01-05 00:00:00", f"DD-MM-YYYY should be re-parsed, got {reparsed}"

    items = make_items([["ITEM001", "ORD002", "PROD001", "1", "50.00", "0"]])
    survivors = clean_order_items(items, cleaned, PRODUCTS)
    assert survivors.empty, "items belonging to a dropped order must go with it"


def main() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception:
            failures += 1
            print(f"FAIL  {test.__name__}")
            traceback.print_exc()
        else:
            print(f"pass  {test.__name__:<44} {test.__doc__.strip().splitlines()[0]}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
