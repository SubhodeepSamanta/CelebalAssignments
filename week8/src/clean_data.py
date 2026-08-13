from __future__ import annotations

import json
import re
from datetime import datetime

import pandas as pd

from src import config

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")
NULL_TOKENS = {"", "null", "none", "nan", "na", "n/a", "-"}

DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"]


class QualityReport:
    def __init__(self) -> None:
        self.issues: list[dict] = []
        self.row_counts: dict[str, dict[str, int]] = {}
        self.quarantined: dict[str, pd.DataFrame] = {}

    def log(self, table: str, issue: str, count: int, action: str) -> None:
        if count:
            self.issues.append({"table": table, "issue": issue, "rows": int(count), "action": action})

    def quarantine(self, table: str, rows: pd.DataFrame, reason: str) -> None:
        if rows.empty:
            return
        tagged = rows.copy()
        tagged.insert(0, "quarantine_reason", reason)
        previous = self.quarantined.get(table)
        self.quarantined[table] = pd.concat([previous, tagged]) if previous is not None else tagged

    def count_rows(self, table: str, before: int, after: int) -> None:
        self.row_counts[table] = {"raw": before, "clean": after, "dropped": before - after}

    def to_dict(self) -> dict:
        return {
            "generated_at": datetime.now().strftime(config.TIMESTAMP_FORMAT),
            "reference_date": config.REFERENCE_DATE.strftime(config.TIMESTAMP_FORMAT),
            "row_counts": self.row_counts,
            "total_issue_rows": sum(item["rows"] for item in self.issues),
            "issues": self.issues,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Data quality report",
            "",
            f"Generated {datetime.now():%Y-%m-%d %H:%M:%S} | "
            f"reference date {config.REFERENCE_DATE:%Y-%m-%d}",
            "",
            "## Row counts",
            "",
            "| Table | Raw | Clean | Dropped |",
            "|---|---:|---:|---:|",
        ]
        for table, counts in self.row_counts.items():
            lines.append(
                f"| {table} | {counts['raw']:,} | {counts['clean']:,} | {counts['dropped']:,} |"
            )
        lines += ["", "## Issues found", "", "| Table | Issue | Rows | Action taken |", "|---|---|---:|---|"]
        for item in self.issues:
            lines.append(f"| {item['table']} | {item['issue']} | {item['rows']:,} | {item['action']} |")
        lines += ["", f"**{sum(i['rows'] for i in self.issues):,} problem rows across "
                      f"{len(self.issues)} distinct issues.**", ""]
        return "\n".join(lines)


def tidy(series: pd.Series) -> pd.Series:
    return series.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()


def blank_to_na(series: pd.Series) -> pd.Series:
    cleaned = tidy(series)
    return cleaned.mask(cleaned.str.lower().isin(NULL_TOKENS))


def parse_dates(series: pd.Series) -> pd.Series:
    values = blank_to_na(series)
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        pending = parsed.isna() & values.notna()
        if not pending.any():
            break
        parsed[pending] = pd.to_datetime(values[pending], format=fmt, errors="coerce")
    return parsed


def read_raw(name: str) -> pd.DataFrame:
    return pd.read_csv(config.RAW_DIR / f"{name}.csv", dtype=str, keep_default_na=False)


def _drop(df: pd.DataFrame, mask: pd.Series, report: QualityReport | None,
          table: str, issue: str, action: str) -> pd.DataFrame:
    mask = mask.fillna(False)
    if report is not None and mask.any():
        report.log(table, issue, int(mask.sum()), action)
        report.quarantine(table, df.loc[mask], issue)
    return df.loc[~mask].copy()


def validate_emails(customers: pd.DataFrame) -> list[str]:
    email = blank_to_na(customers["email"])
    valid = email.notna() & email.str.match(EMAIL_PATTERN).fillna(False)
    return customers.loc[~valid, "customer_id"].tolist()


def check_referential_integrity(order_items: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    known = set(orders["order_id"])
    return order_items.loc[~order_items["order_id"].isin(known)].copy()


def clean_customers(customers: pd.DataFrame, report: QualityReport | None = None) -> pd.DataFrame:
    raw_rows = len(customers)
    df = customers.copy()

    df["customer_id"] = blank_to_na(df["customer_id"])
    df["customer_name"] = tidy(df["customer_name"]).str.title()
    df["email"] = blank_to_na(df["email"]).str.lower()
    df["customer_type"] = tidy(df["customer_type"]).str.upper()

    df = _drop(df, df["customer_id"].isna(), report, "customers",
               "missing customer_id", "row dropped")
    df = _drop(df, df["customer_id"].duplicated(keep="first"), report, "customers",
               "duplicate customer_id", "first occurrence kept")

    registration = parse_dates(df["registration_date"])
    df = _drop(df, registration.isna(), report, "customers",
               "unparseable registration_date", "row dropped")
    df["registration_date"] = registration.loc[df.index].dt.strftime(config.DATE_FORMAT)

    unknown_type = ~df["customer_type"].isin(config.CUSTOMER_TYPES)
    if report is not None:
        report.log("customers", "customer_type outside REGULAR/PREMIUM/VIP",
                   int(unknown_type.sum()), "set to REGULAR")
    df.loc[unknown_type, "customer_type"] = "REGULAR"

    if report is not None:
        report.log("customers", "invalid email address", len(validate_emails(df)),
                   "value kept, ids listed in the JSON report")
        report.count_rows("customers", raw_rows, len(df))
    return df.reset_index(drop=True)


def clean_products(products: pd.DataFrame, report: QualityReport | None = None) -> pd.DataFrame:
    raw_rows = len(products)
    df = products.copy()

    df["product_id"] = blank_to_na(df["product_id"])
    normalised = tidy(df["product_name"]).str.title()
    if report is not None:
        report.log("products", "product_name needed trimming or re-casing",
                   int((normalised != df["product_name"]).sum()), "normalised to Title Case")
    df["product_name"] = normalised
    df["category"] = tidy(df["category"]).str.title()
    df["subcategory"] = tidy(df["subcategory"]).str.title()
    df["cost_price"] = pd.to_numeric(blank_to_na(df["cost_price"]), errors="coerce")

    df = _drop(df, df["product_id"].isna(), report, "products",
               "missing product_id", "row dropped")
    df = _drop(df, df["product_id"].duplicated(keep="first"), report, "products",
               "duplicate product_id", "first occurrence kept")
    df = _drop(df, df["cost_price"].isna() | (df["cost_price"] <= 0), report, "products",
               "cost_price missing or not positive", "row dropped")

    df["cost_price"] = df["cost_price"].round(2)
    if report is not None:
        report.count_rows("products", raw_rows, len(df))
    return df.reset_index(drop=True)


def clean_orders(orders: pd.DataFrame, report: QualityReport | None = None) -> pd.DataFrame:
    raw_rows = len(orders)
    df = orders.copy()

    df["order_id"] = blank_to_na(df["order_id"])
    df["customer_id"] = blank_to_na(df["customer_id"])
    df["status"] = tidy(df["status"]).str.upper()
    df["region_code"] = tidy(df["region_code"]).str.upper()

    if report is not None:
        report.log("orders", "customer_id missing or the literal text 'NULL'",
                   int(df["customer_id"].isna().sum()), "kept as SQL NULL")

    df = _drop(df, df["order_id"].isna(), report, "orders", "missing order_id", "row dropped")
    df = _drop(df, df["order_id"].duplicated(keep="first"), report, "orders",
               "duplicate order_id", "first occurrence kept")

    parsed = parse_dates(df["order_date"])
    non_iso = parsed.notna() & (df["order_date"].str.len() != 19)
    if report is not None:
        report.log("orders", "order_date not in YYYY-MM-DD HH:MM:SS",
                   int(non_iso.sum()), "re-parsed and rewritten as ISO")

    df["order_date"] = parsed
    df = _drop(df, df["order_date"].isna(), report, "orders",
               "unparseable order_date", "row dropped")
    df = _drop(df, df["order_date"] > config.REFERENCE_DATE, report, "orders",
               "order_date in the future", "row dropped")
    df = _drop(df, ~df["status"].isin(config.ORDER_STATUSES), report, "orders",
               "status outside the allowed set", "row dropped")

    df["region_code"] = df["region_code"].fillna("UNKNOWN")
    df["order_date"] = df["order_date"].dt.strftime(config.TIMESTAMP_FORMAT)
    if report is not None:
        report.count_rows("orders", raw_rows, len(df))
    return df.reset_index(drop=True)


def clean_order_items(items: pd.DataFrame, orders: pd.DataFrame, products: pd.DataFrame,
                      report: QualityReport | None = None) -> pd.DataFrame:
    raw_rows = len(items)
    df = items.copy()

    df["item_id"] = blank_to_na(df["item_id"])
    df["order_id"] = blank_to_na(df["order_id"])
    df["product_id"] = blank_to_na(df["product_id"])
    for column in ("quantity", "unit_price", "discount_percent"):
        df[column] = pd.to_numeric(blank_to_na(df[column]), errors="coerce")

    df = _drop(df, df["item_id"].isna(), report, "order_items", "missing item_id", "row dropped")
    df = _drop(df, df["item_id"].duplicated(keep="first"), report, "order_items",
               "duplicate item_id", "first occurrence kept")
    df = _drop(df, df[["order_id", "product_id"]].isna().any(axis=1), report, "order_items",
               "missing order_id or product_id", "row dropped")

    orphans = set(check_referential_integrity(df, orders)["item_id"])
    df = _drop(df, df["item_id"].isin(orphans), report, "order_items",
               "order_id not present in cleaned orders", "row dropped")
    df = _drop(df, ~df["product_id"].isin(set(products["product_id"])), report, "order_items",
               "product_id not present in cleaned products", "row dropped")

    df = _drop(df, df["quantity"].isna() | (df["quantity"] == 0), report, "order_items",
               "quantity is zero or unreadable", "row dropped")
    df = _drop(df, df["unit_price"].isna() | (df["unit_price"] <= 0), report, "order_items",
               "unit_price missing or not positive", "row dropped")

    out_of_range = df["discount_percent"].isna() | ~df["discount_percent"].between(0, 100)
    if report is not None:
        report.log("order_items", "discount_percent outside 0-100",
                   int(out_of_range.sum()), "clamped into 0-100 (missing treated as 0)")
    df["discount_percent"] = df["discount_percent"].fillna(0).clip(0, 100)

    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].round(2)
    df["is_return"] = (df["quantity"] < 0).astype(int)
    if report is not None:
        report.log("order_items", "negative quantity (return lines)",
                   int(df["is_return"].sum()), "kept and flagged with is_return = 1")
        report.count_rows("order_items", raw_rows, len(df))
    return df.reset_index(drop=True)


def clean_all() -> tuple[dict[str, pd.DataFrame], QualityReport]:
    config.ensure_dirs()
    report = QualityReport()

    raw_orders = read_raw("orders")
    raw_items = read_raw("order_items")

    customers = clean_customers(read_raw("customers"), report)
    products = clean_products(read_raw("products"), report)
    orders = clean_orders(raw_orders, report)

    true_orphans = check_referential_integrity(raw_items, raw_orders)
    report.log("order_items", "order_id never existed in the raw orders file",
               len(true_orphans), "row dropped (subset of the check below)")

    items = clean_order_items(raw_items, orders, products, report)

    unknown_customer = ~orders["customer_id"].isin(set(customers["customer_id"]))
    report.log("orders", "customer_id not present in cleaned customers",
               int((unknown_customer & orders["customer_id"].notna()).sum()),
               "kept, treated as anonymous")

    frames = {"customers": customers, "products": products, "orders": orders, "order_items": items}
    for name, frame in frames.items():
        frame.to_csv(config.CLEAN_DIR / f"{name}.csv", index=False)
    for name, frame in report.quarantined.items():
        frame.to_csv(config.QUARANTINE_DIR / f"{name}.csv", index=False)

    payload = report.to_dict()
    payload["invalid_email_customer_ids"] = validate_emails(customers)
    config.QUALITY_REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    config.QUALITY_REPORT_MD.write_text(report.to_markdown(), encoding="utf-8")
    return frames, report


def main() -> None:
    frames, report = clean_all()

    print("clean CSVs written to", config.CLEAN_DIR)
    for table, counts in report.row_counts.items():
        print(f"  {table:<12} {counts['raw']:>7,} raw -> {counts['clean']:>7,} clean "
              f"({counts['dropped']:,} dropped)")

    print(f"\n{len(report.issues)} distinct issues found:")
    for item in report.issues:
        print(f"  [{item['table']:<11}] {item['issue']:<52} {item['rows']:>5,}  {item['action']}")

    print(f"\nreport written to {config.QUALITY_REPORT_MD.name} and {config.QUALITY_REPORT_JSON.name}")
    if report.quarantined:
        print("quarantined rows written to", config.QUARANTINE_DIR)
    print(f"revenue-bearing lines retained: {len(frames['order_items']):,}")


if __name__ == "__main__":
    main()
