"""
Part 3 - runs the SQL analysis.

Executes every file in sql/queries/ against the database, prints a preview and
writes the full result to output/query_results/.

Run:  python -m src.run_analysis        all sixteen
      python -m src.run_analysis 7 13   only those numbers
"""

from __future__ import annotations

import sys

import pandas as pd

from src import config
from src.database import connect

PREVIEW_ROWS = 8


def query_files(wanted: list[str] | None = None) -> list:
    files = sorted(config.QUERY_DIR.glob("*.sql"))
    if not wanted:
        return files
    prefixes = {f"{int(number):02d}" for number in wanted}
    return [path for path in files if path.name[:2] in prefixes]


def title_of(sql: str) -> str:
    for line in sql.splitlines():
        if line.startswith("--"):
            return line.lstrip("-").strip()
    return ""


def run(wanted: list[str] | None = None) -> dict[str, int]:
    config.ensure_dirs()
    if not config.DB_PATH.exists():
        raise SystemExit("No database found. Run: python -m src.database")

    connection = connect()
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)
    results = {}
    try:
        for path in query_files(wanted):
            sql = path.read_text(encoding="utf-8")
            frame = pd.read_sql_query(sql, connection)
            frame.to_csv(config.RESULTS_DIR / f"{path.stem}.csv", index=False)
            results[path.stem] = len(frame)

            print(f"\n{'=' * 100}\n{title_of(sql)}\n{'-' * 100}")
            if frame.empty:
                print("(no rows)")
                continue
            print(frame.head(PREVIEW_ROWS).to_string(index=False))
            if len(frame) > PREVIEW_ROWS:
                print(f"... {len(frame):,} rows total -> query_results/{path.stem}.csv")
    finally:
        connection.close()
    return results


def main() -> None:
    results = run(sys.argv[1:] or None)
    print(f"\n{'=' * 100}")
    print(f"{len(results)} queries executed, results written to {config.RESULTS_DIR}")
    for name, rows in results.items():
        print(f"  {name:<40} {rows:>6,} rows")


if __name__ == "__main__":
    main()
