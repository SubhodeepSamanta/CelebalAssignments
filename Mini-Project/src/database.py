"""
Builds the SQLite database from the cleaned CSVs.

The schema in sql/schema.sql carries primary keys, foreign keys and CHECK
constraints, so this load doubles as a test: if cleaning missed something the
insert raises IntegrityError instead of quietly storing bad data.

Run:  python -m src.database
"""

from __future__ import annotations

import sqlite3

import pandas as pd

from src import config


def connect(path=None) -> sqlite3.Connection:
    connection = sqlite3.connect(path or config.DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def build_database(path=None) -> dict[str, int]:
    config.ensure_dirs()
    connection = connect(path)
    loaded = {}
    try:
        connection.executescript(config.SCHEMA_PATH.read_text(encoding="utf-8"))
        for table in config.TABLES:
            frame = pd.read_csv(config.CLEAN_DIR / f"{table}.csv")
            frame.to_sql(table, connection, if_exists="append", index=False)
            loaded[table] = len(frame)

        broken = connection.execute("PRAGMA foreign_key_check").fetchall()
        if broken:
            raise RuntimeError(f"{len(broken)} foreign key violations after load")
        connection.commit()
        connection.execute("ANALYZE")
    finally:
        connection.close()
    return loaded


def main() -> None:
    loaded = build_database()
    print("database built at", config.DB_PATH)
    for table, rows in loaded.items():
        print(f"  {table:<12} {rows:>7,} rows")

    connection = connect()
    revenue = connection.execute("SELECT ROUND(SUM(line_revenue), 2) FROM revenue_lines").fetchone()[0]
    span = connection.execute("SELECT MIN(order_day), MAX(order_day) FROM order_lines").fetchone()
    connection.close()
    print(f"\n  net revenue  {revenue:,.2f} over {span[0]} to {span[1]}")


if __name__ == "__main__":
    main()
