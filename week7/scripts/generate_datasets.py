from __future__ import annotations

import os
import random
import re
import unicodedata

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

RAW = os.path.join(DATA, "superstore_raw.csv")
MASTER_OUT = os.path.join(DATA, "customer_master.csv")
INCR_OUT = os.path.join(DATA, "customer_incremental.csv")

SNAPSHOT_DATE = "2019-12-31"
INCREMENT_DATE = "2020-01-15"

COLUMNS = [
    "customer_id",
    "customer_name",
    "segment",
    "country",
    "city",
    "state",
    "postal_code",
    "region",
    "total_orders",
    "total_sales",
    "total_profit",
    "last_order_date",
    "loyalty_tier",
    "email",
    "record_updated_at",
]


def slugify(name: str) -> str:
    txt = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    txt = re.sub(r"[^a-zA-Z ]", "", txt).strip().lower()
    return ".".join(txt.split())


def loyalty_tier(sales: float) -> str:
    if sales >= 5000:
        return "PLATINUM"
    if sales >= 2500:
        return "GOLD"
    if sales >= 1000:
        return "SILVER"
    return "BRONZE"


def build_customer_dimension() -> pd.DataFrame:
    orders = pd.read_csv(RAW, encoding="latin-1")
    orders.columns = [c.strip() for c in orders.columns]
    orders["Order Date"] = pd.to_datetime(orders["Order Date"], format="%m/%d/%Y")

    def mode_or_first(s: pd.Series):
        m = s.mode()
        return m.iloc[0] if len(m) else s.iloc[0]

    orders["_loc"] = list(
        zip(orders["City"], orders["State"], orders["Postal Code"], orders["Region"])
    )
    loc = (
        orders.groupby(["Customer ID", "_loc"])
        .size()
        .reset_index(name="_n")
        .sort_values(["Customer ID", "_n"], ascending=[True, False])
        .groupby("Customer ID")
        .head(1)
        .set_index("Customer ID")["_loc"]
    )

    dim = (
        orders.groupby("Customer ID")
        .agg(
            customer_name=("Customer Name", "first"),
            segment=("Segment", mode_or_first),
            country=("Country", mode_or_first),
            total_orders=("Order ID", "nunique"),
            total_sales=("Sales", "sum"),
            total_profit=("Profit", "sum"),
            last_order_date=("Order Date", "max"),
        )
        .reset_index()
        .rename(columns={"Customer ID": "customer_id"})
    )

    loc_df = pd.DataFrame(
        loc.tolist(), index=loc.index, columns=["city", "state", "postal_code", "region"]
    ).reset_index().rename(columns={"Customer ID": "customer_id"})
    dim = dim.merge(loc_df, on="customer_id", how="left")

    dim["total_sales"] = dim["total_sales"].round(2)
    dim["total_profit"] = dim["total_profit"].round(2)
    dim["postal_code"] = dim["postal_code"].astype("Int64").astype(str).str.zfill(5)
    dim["last_order_date"] = dim["last_order_date"].dt.strftime("%Y-%m-%d")
    dim["loyalty_tier"] = dim["total_sales"].apply(loyalty_tier)
    dim["email"] = dim["customer_name"].apply(lambda n: f"{slugify(n)}@example.com")
    dim["record_updated_at"] = f"{SNAPSHOT_DATE} 22:00:00"

    return dim[COLUMNS].sort_values("customer_id").reset_index(drop=True)


def dirty_master(clean: pd.DataFrame) -> pd.DataFrame:
    df = clean.copy()
    n = len(df)
    rng = np.random.default_rng(SEED)

    def pick(k):
        return rng.choice(n, size=k, replace=False)

    df.loc[pick(18), "segment"] = np.nan
    df.loc[pick(12), "city"] = np.nan
    df.loc[pick(30), "postal_code"] = np.nan
    df.loc[pick(10), "total_sales"] = np.nan
    df.loc[pick(8), "region"] = np.nan
    df.loc[pick(40), "email"] = np.nan
    df.loc[pick(6), "loyalty_tier"] = np.nan

    for idx in pick(35):
        val = df.at[idx, "segment"]
        if isinstance(val, str):
            df.at[idx, "segment"] = f"  {val.upper()} "
    for idx in pick(25):
        val = df.at[idx, "region"]
        if isinstance(val, str):
            df.at[idx, "region"] = f"{val.lower()}  "
    for idx in pick(20):
        df.at[idx, "customer_name"] = f" {df.at[idx, 'customer_name']}  "

    orphan = df.sample(3, random_state=SEED).copy()
    orphan["customer_id"] = np.nan

    exact_dupes = df.sample(45, random_state=SEED).copy()

    late = df.sample(25, random_state=SEED + 1).copy()
    late["record_updated_at"] = f"{SNAPSHOT_DATE} 23:45:00"
    late["total_sales"] = (late["total_sales"].fillna(0) * 1.05).round(2)
    late["loyalty_tier"] = late["total_sales"].apply(loyalty_tier)

    dirty = pd.concat([df, exact_dupes, late, orphan], ignore_index=True)
    return dirty.sample(frac=1.0, random_state=SEED).reset_index(drop=True)


def build_incremental(clean: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 7)

    changed = clean.sample(100, random_state=SEED + 2).copy()
    changed["total_sales"] = (
        changed["total_sales"] * rng.uniform(1.05, 1.60, size=len(changed))
    ).round(2)
    changed["total_profit"] = (
        changed["total_profit"] * rng.uniform(1.00, 1.45, size=len(changed))
    ).round(2)
    changed["total_orders"] = changed["total_orders"] + rng.integers(1, 5, size=len(changed))
    changed["last_order_date"] = INCREMENT_DATE
    changed["loyalty_tier"] = changed["total_sales"].apply(loyalty_tier)

    movers = changed.sample(30, random_state=SEED + 3).index
    new_cities = [
        ("Austin", "Texas", "78701", "Central"),
        ("Seattle", "Washington", "98101", "West"),
        ("Miami", "Florida", "33101", "South"),
        ("Boston", "Massachusetts", "02108", "East"),
        ("Denver", "Colorado", "80202", "West"),
    ]
    for i, idx in enumerate(movers):
        city, state, pc, region = new_cities[i % len(new_cities)]
        changed.loc[idx, ["city", "state", "postal_code", "region"]] = [city, state, pc, region]

    seg_changers = changed.sample(15, random_state=SEED + 4).index
    seg_map = {"Consumer": "Corporate", "Corporate": "Home Office", "Home Office": "Consumer"}
    changed.loc[seg_changers, "segment"] = changed.loc[seg_changers, "segment"].map(seg_map)

    untouched = clean[~clean["customer_id"].isin(changed["customer_id"])]
    unchanged = untouched.sample(12, random_state=SEED + 5).copy()

    first = [
        "Aarav", "Diya", "Rohan", "Meera", "Kabir", "Ananya", "Vivaan", "Isha",
        "Arjun", "Sara", "Neel", "Priya", "Dev", "Tara", "Yash", "Nisha",
        "Omar", "Lena", "Marcus", "Elena", "Hugo", "Freya", "Ivan", "Chloe",
        "Noah", "Zara", "Felix", "Maya", "Leo", "Ruby", "Ethan", "Nora",
        "Adam", "Iris", "Jonas", "Alice", "Victor", "Wren", "Milo", "Cleo",
        "Rafael", "Sana", "Theo", "Amara", "Kian",
    ]
    last = [
        "Sharma", "Patel", "Nair", "Iyer", "Khan", "Bose", "Reddy", "Kapoor",
        "Mehta", "Rao", "Verma", "Joshi", "Ali", "Dutta", "Gill", "Bhatt",
        "Haddad", "Novak", "Cole", "Petrova", "Muller", "Larsen", "Sokolov",
        "Dupont", "Bennett", "Aziz", "Weber", "Fischer", "Grant", "Sullivan",
        "Ford", "Blake", "Mercer", "Quinn", "Vaughn", "Hale", "Rossi", "Kim",
        "Tanaka", "Costa", "Silva", "Okafor", "Mensah", "Torres", "Nolan",
    ]
    cities = [
        ("New York City", "New York", "10024", "East"),
        ("Los Angeles", "California", "90036", "West"),
        ("Chicago", "Illinois", "60610", "Central"),
        ("Houston", "Texas", "77041", "Central"),
        ("Philadelphia", "Pennsylvania", "19140", "East"),
        ("Phoenix", "Arizona", "85023", "West"),
        ("San Diego", "California", "92024", "West"),
        ("Atlanta", "Georgia", "30318", "South"),
    ]
    segments = ["Consumer", "Corporate", "Home Office"]

    rows = []
    for i in range(45):
        fn, ln = first[i], last[i]
        name = f"{fn} {ln}"
        cid = f"{fn[0]}{ln[0]}-{20000 + i * 7}"
        city, state, pc, region = cities[i % len(cities)]
        sales = round(float(rng.uniform(120, 9500)), 2)
        rows.append(
            {
                "customer_id": cid,
                "customer_name": name,
                "segment": segments[i % 3],
                "country": "United States",
                "city": city,
                "state": state,
                "postal_code": pc,
                "region": region,
                "total_orders": int(rng.integers(1, 12)),
                "total_sales": sales,
                "total_profit": round(sales * float(rng.uniform(-0.05, 0.28)), 2),
                "last_order_date": INCREMENT_DATE,
                "loyalty_tier": loyalty_tier(sales),
                "email": f"{slugify(name)}@example.com",
                "record_updated_at": f"{INCREMENT_DATE} 06:30:00",
            }
        )
    new_customers = pd.DataFrame(rows)

    incr = pd.concat([changed, unchanged, new_customers], ignore_index=True)
    incr["record_updated_at"] = f"{INCREMENT_DATE} 06:30:00"

    dupes = incr.sample(5, random_state=SEED + 6).copy()
    incr = pd.concat([incr, dupes], ignore_index=True)

    incr.loc[incr.sample(4, random_state=SEED + 8).index, "email"] = np.nan
    incr.loc[incr.sample(3, random_state=SEED + 9).index, "city"] = np.nan

    return incr[COLUMNS].sample(frac=1.0, random_state=SEED).reset_index(drop=True)


def main() -> None:
    clean_dim = build_customer_dimension()
    print(f"customer dimension built from superstore : {len(clean_dim):,} customers")

    master = dirty_master(clean_dim)
    incr = build_incremental(clean_dim)

    master.to_csv(MASTER_OUT, index=False)
    incr.to_csv(INCR_OUT, index=False)

    print(f"-> {MASTER_OUT}  ({len(master):,} rows, {master['customer_id'].nunique():,} unique ids)")
    print(f"-> {INCR_OUT}  ({len(incr):,} rows, {incr['customer_id'].nunique():,} unique ids)")
    print("\nmaster null counts:")
    print(master.isna().sum()[lambda s: s > 0].to_string())
    print(f"\nexact duplicate rows in master : {master.duplicated().sum()}")
    print(f"duplicate customer_id in master: {master['customer_id'].duplicated().sum()}")
    print(f"duplicate customer_id in incr  : {incr['customer_id'].duplicated().sum()}")


if __name__ == "__main__":
    main()
