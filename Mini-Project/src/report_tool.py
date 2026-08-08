from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "output" / "ecommerce.db"

GRAINS = {
    "daily": "DATE(order_date)",
    "weekly": "STRFTIME('%Y-W%W', order_date)",
    "monthly": "STRFTIME('%Y-%m', order_date)",
}
BUCKET_LABEL = {"daily": "Day", "weekly": "Week", "monthly": "Month"}

SUMMARY_SQL = """
    SELECT COUNT(DISTINCT order_id)          AS orders,
           COALESCE(SUM(line_revenue), 0)    AS revenue,
           COUNT(DISTINCT customer_id)       AS customers
    FROM revenue_lines
    WHERE order_day BETWEEN ? AND ?
"""

TOP_PRODUCTS_SQL = """
    SELECT product_name,
           SUM(quantity)    AS units,
           SUM(line_revenue) AS revenue
    FROM revenue_lines
    WHERE order_day BETWEEN ? AND ?
    GROUP BY product_id, product_name
    ORDER BY revenue DESC
    LIMIT 3
"""


def parse_date(text: str) -> date:
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"'{text}' is not a date in YYYY-MM-DD format")


def previous_window(start: date, end: date) -> tuple[date, date]:
    length = (end - start).days + 1
    return start - timedelta(days=length), start - timedelta(days=1)


def percent_change(current: float, previous: float) -> str:
    if not previous:
        return "n/a"
    return f"{(current - previous) / abs(previous) * 100:+.1f}%"


def fetch_summary(connection: sqlite3.Connection, start: date, end: date) -> dict:
    row = connection.execute(SUMMARY_SQL, (start.isoformat(), end.isoformat())).fetchone()
    return {"orders": row[0], "revenue": row[1], "customers": row[2]}


def fetch_buckets(connection: sqlite3.Connection, start: date, end: date, grain: str) -> list:
    sql = f"""
        SELECT {GRAINS[grain]}             AS bucket,
               COUNT(DISTINCT order_id)    AS orders,
               SUM(line_revenue)           AS revenue,
               COUNT(DISTINCT customer_id) AS customers
        FROM revenue_lines
        WHERE order_day BETWEEN ? AND ?
        GROUP BY bucket
        ORDER BY bucket
    """
    return connection.execute(sql, (start.isoformat(), end.isoformat())).fetchall()


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(head) for head in headers]
    for row in rows:
        widths = [max(width, len(str(cell))) for width, cell in zip(widths, row)]
    line = "  ".join(head.ljust(width) for head, width in zip(headers, widths))
    print(line)
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(cell).rjust(width) if index else str(cell).ljust(width)
                        for index, (cell, width) in enumerate(zip(row, widths))))


def ask(prompt: str, default: str) -> str:
    answer = input(f"{prompt} [{default}]: ").strip()
    return answer or default


def collect_inputs(args: argparse.Namespace, connection: sqlite3.Connection) -> tuple[str, date, date]:
    last_day = connection.execute("SELECT MAX(order_day) FROM revenue_lines").fetchone()[0]
    default_end = parse_date(last_day)
    default_start = default_end.replace(day=1)

    report_type = args.type or ask("Report type (daily/weekly/monthly)", "monthly")
    if report_type not in GRAINS:
        raise SystemExit(f"Report type must be one of: {', '.join(GRAINS)}")

    start = parse_date(args.start) if args.start else parse_date(
        ask("Start date (YYYY-MM-DD)", default_start.isoformat()))
    end = parse_date(args.end) if args.end else parse_date(
        ask("End date (YYYY-MM-DD)", default_end.isoformat()))
    if start > end:
        raise SystemExit("Start date must not be after the end date")
    return report_type, start, end


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="E-commerce summary report")
    parser.add_argument("--type", choices=sorted(GRAINS), help="reporting grain")
    parser.add_argument("--start", help="start date, YYYY-MM-DD")
    parser.add_argument("--end", help="end date, YYYY-MM-DD")
    parser.add_argument("--db", default=str(DB_PATH), help="path to the SQLite database")
    args = parser.parse_args(argv)

    if not Path(args.db).exists():
        raise SystemExit(f"Database not found at {args.db}. Run: python -m src.database")

    connection = sqlite3.connect(args.db)
    try:
        report_type, start, end = collect_inputs(args, connection)
        prior_start, prior_end = previous_window(start, end)

        current = fetch_summary(connection, start, end)
        previous = fetch_summary(connection, prior_start, prior_end)
        buckets = fetch_buckets(connection, start, end, report_type)
        top = connection.execute(TOP_PRODUCTS_SQL, (start.isoformat(), end.isoformat())).fetchall()

        print(f"\n{report_type.upper()} REPORT   {start} to {end}   ({(end - start).days + 1} days)")
        print("=" * 78)

        if not buckets:
            print("No revenue-bearing orders in this window.")
            return

        print_table(
            [BUCKET_LABEL[report_type], "Orders", "Revenue", "Customers"],
            [[bucket, f"{orders:,}", f"{revenue:,.2f}", f"{customers:,}"]
             for bucket, orders, revenue, customers in buckets],
        )

        print(f"\nSummary vs previous {(end - start).days + 1} days ({prior_start} to {prior_end})")
        print("-" * 78)
        print_table(
            ["Metric", "This period", "Previous", "Change"],
            [
                ["Total orders", f"{current['orders']:,}", f"{previous['orders']:,}",
                 percent_change(current["orders"], previous["orders"])],
                ["Revenue", f"{current['revenue']:,.2f}", f"{previous['revenue']:,.2f}",
                 percent_change(current["revenue"], previous["revenue"])],
                ["Unique customers", f"{current['customers']:,}", f"{previous['customers']:,}",
                 percent_change(current["customers"], previous["customers"])],
            ],
        )

        print("\nTop 3 products by revenue")
        print("-" * 78)
        print_table(
            ["Product", "Units", "Revenue"],
            [[name, f"{units:,}", f"{revenue:,.2f}"] for name, units, revenue in top],
        )
        print()
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\ncancelled")
