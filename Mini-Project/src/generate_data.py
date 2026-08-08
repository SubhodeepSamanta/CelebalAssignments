"""
Part 1 - data generation.

Writes the four raw CSVs into data/raw/ using only the standard library.
The data is deliberately messy; every defect is injected by one of the
inject_* functions and the counts are printed so the cleaning stage can be
checked against a known answer.

Run:  python -m src.generate_data
"""

from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from typing import Iterable, Sequence

from src import config

TAXONOMY = {
    "Electronics": ["Laptops", "Smartphones", "Audio", "Cameras", "Wearables"],
    "Clothing": ["Menswear", "Womenswear", "Footwear", "Activewear"],
    "Home": ["Kitchen", "Furniture", "Decor", "Bedding"],
    "Books": ["Fiction", "Non-Fiction", "Academic", "Children"],
}
COST_RANGE = {
    "Electronics": (60.0, 1400.0),
    "Clothing": (8.0, 180.0),
    "Home": (12.0, 900.0),
    "Books": (3.0, 60.0),
}

BRANDS = [
    "Arclight", "Northbay", "Kestrel", "Lumen", "Vantage", "Orbita", "Pinegate",
    "Riverstone", "Solace", "Trident", "Umbra", "Waypoint", "Zephyr", "Cobalt",
    "Meridian", "Halcyon", "Everline", "Foxglove",
]
MODEL_NOUNS = {
    "Laptops": ["Notebook", "Ultrabook", "Workstation"],
    "Smartphones": ["Phone", "Handset", "Smartphone"],
    "Audio": ["Headphones", "Earbuds", "Speaker", "Soundbar"],
    "Cameras": ["Camera", "Camcorder", "Action Cam"],
    "Wearables": ["Smartwatch", "Fitness Band", "Ring Tracker"],
    "Menswear": ["Oxford Shirt", "Chinos", "Overcoat", "Knit Sweater"],
    "Womenswear": ["Wrap Dress", "Blouse", "Tailored Trousers", "Cardigan"],
    "Footwear": ["Runners", "Loafers", "Ankle Boots", "Sandals"],
    "Activewear": ["Training Tee", "Leggings", "Track Jacket", "Shorts"],
    "Kitchen": ["Stand Mixer", "Chef Knife", "Cookware Set", "Kettle"],
    "Furniture": ["Armchair", "Bookcase", "Desk", "Dining Table"],
    "Decor": ["Floor Lamp", "Wall Mirror", "Rug", "Vase"],
    "Bedding": ["Duvet", "Pillow Set", "Sheet Set", "Throw"],
    "Fiction": ["Novel", "Short Stories", "Anthology"],
    "Non-Fiction": ["Biography", "Field Guide", "Essays"],
    "Academic": ["Textbook", "Problem Set", "Casebook"],
    "Children": ["Picture Book", "Activity Book", "Early Reader"],
}

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Meera", "Kabir", "Isha", "Vivaan", "Diya",
    "Arjun", "Sara", "Neel", "Priya", "Dev", "Tara", "Yash", "Nisha",
    "Omar", "Lena", "Marcus", "Elena", "Hugo", "Freya", "Ivan", "Chloe",
    "Noah", "Zara", "Felix", "Maya", "Leo", "Ruby", "Ethan", "Nora",
    "Adam", "Iris", "Jonas", "Alice", "Victor", "Wren", "Milo", "Cleo",
]
LAST_NAMES = [
    "Sharma", "Patel", "Nair", "Iyer", "Khan", "Bose", "Reddy", "Kapoor",
    "Mehta", "Rao", "Verma", "Joshi", "Dutta", "Gill", "Bhatt", "Haddad",
    "Novak", "Cole", "Petrova", "Muller", "Larsen", "Sokolov", "Dupont",
    "Bennett", "Weber", "Fischer", "Grant", "Sullivan", "Ford", "Blake",
    "Mercer", "Quinn", "Vaughn", "Hale", "Rossi", "Kim", "Tanaka", "Costa",
]
EMAIL_DOMAINS = ["example.com", "mailbox.net", "shopmail.org", "inbox.co"]
REGION_CODES = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

STATUS_WEIGHTS = {
    "DELIVERED": 0.56,
    "SHIPPED": 0.14,
    "PLACED": 0.12,
    "CANCELLED": 0.13,
    "RETURNED": 0.05,
}
CUSTOMER_TYPE_WEIGHTS = {"REGULAR": 0.62, "PREMIUM": 0.28, "VIP": 0.10}
ORDERS_PER_CUSTOMER = {"REGULAR": (1, 8), "PREMIUM": (3, 14), "VIP": (6, 24)}
DISCOUNT_CHOICES = [0, 0, 0, 5, 10, 10, 15, 20, 25, 30, 40, 50]

NULL_CUSTOMER_ID_RATE = 0.05
BAD_DATE_FORMAT_RATE = 0.04
DIRTY_PRODUCT_NAME_RATE = 0.12
INVALID_EMAIL_RATE = 0.02
FUTURE_ORDER_COUNT = 10
ZERO_QUANTITY_COUNT = 20
OVER_100_DISCOUNT_COUNT = 12
ORPHAN_ITEM_COUNT = 15
N_DEFECT_PRODUCTS = 12


def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]


def random_datetime(rng: random.Random, start: date, end: date) -> datetime:
    span = max((end - start).days, 0)
    day = start + timedelta(days=rng.randint(0, span))
    hour = rng.choices(range(24), weights=[1] * 8 + [4] * 12 + [2] * 4, k=1)[0]
    return datetime(day.year, day.month, day.day, hour, rng.randint(0, 59), rng.randint(0, 59))


def write_csv(path, header: Sequence[str], rows: Iterable[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def build_customers(rng: random.Random) -> list[dict]:
    customers = []
    for i in range(1, config.N_CUSTOMERS + 1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        registered = config.HISTORY_START + timedelta(days=rng.randint(0, 640))
        customers.append(
            {
                "customer_id": f"CUST{i:05d}",
                "customer_name": f"{first} {last}",
                "email": f"{first}.{last}{rng.randint(1, 99)}@{rng.choice(EMAIL_DOMAINS)}".lower(),
                "registration_date": registered.strftime(config.DATE_FORMAT),
                "customer_type": weighted_choice(rng, CUSTOMER_TYPE_WEIGHTS),
            }
        )
    return customers


def build_products(rng: random.Random) -> list[dict]:
    products = []
    for i in range(1, config.N_PRODUCTS + 1):
        category = rng.choice(list(TAXONOMY))
        subcategory = rng.choice(TAXONOMY[category])
        low, high = COST_RANGE[category]
        cost = round(low + (high - low) * rng.random() ** 2.2, 2)
        noun = rng.choice(MODEL_NOUNS[subcategory])
        products.append(
            {
                "product_id": f"PROD{i:04d}",
                "product_name": f"{rng.choice(BRANDS)} {noun} {rng.choice('XSMLQZ')}{rng.randint(100, 999)}",
                "category": category,
                "subcategory": subcategory,
                "cost_price": f"{cost:.2f}",
            }
        )
    return products


def build_orders(rng: random.Random, customers: list[dict]) -> list[dict]:
    orders = []
    counter = 0
    for customer in customers:
        if rng.random() < 0.10:
            continue
        low, high = ORDERS_PER_CUSTOMER[customer["customer_type"]]
        registered = datetime.strptime(customer["registration_date"], config.DATE_FORMAT).date()
        region = rng.choice(REGION_CODES)
        for _ in range(rng.randint(low, high)):
            counter += 1
            orders.append(
                {
                    "order_id": f"ORD{counter:06d}",
                    "customer_id": customer["customer_id"],
                    "order_date": random_datetime(rng, registered, config.HISTORY_END).strftime(
                        config.TIMESTAMP_FORMAT
                    ),
                    "status": weighted_choice(rng, STATUS_WEIGHTS),
                    "region_code": region,
                }
            )
    orders.sort(key=lambda row: row["order_date"])
    return orders


def build_order_items(rng: random.Random, orders: list[dict], products: list[dict]) -> list[dict]:
    """
    Line items. Referential integrity holds by construction because order_ids
    are only ever read out of the `orders` list; the broken references the
    cleaner has to catch are appended later by inject_item_defects().

    RETURNED orders are credit notes, so all of their lines are negative.
    """
    ids = [p["product_id"] for p in products]
    purchase_weights = {pid: rng.random() ** 2 * 10 + 0.15 for pid in ids}
    unit_price = {
        p["product_id"]: round(float(p["cost_price"]) * rng.uniform(1.25, 2.30), 2)
        for p in products
    }

    return_weights = dict(purchase_weights)
    for pid in rng.sample(ids, N_DEFECT_PRODUCTS):
        purchase_weights[pid] *= 0.05
        return_weights[pid] = 90.0

    popular = sorted(ids, key=lambda pid: -purchase_weights[pid])[:80]
    bundles = [tuple(rng.sample(popular, 2)) for _ in range(30)]

    buy_w = [purchase_weights[pid] for pid in ids]
    return_w = [return_weights[pid] for pid in ids]

    def pick_distinct(weights: list[float], n: int, seeded: Iterable[str] = ()) -> list[str]:
        chosen = list(seeded)
        while len(chosen) < n:
            candidate = rng.choices(ids, weights=weights, k=1)[0]
            if candidate not in chosen:
                chosen.append(candidate)
        return chosen

    items = []
    counter = 0
    for order in orders:
        is_return = order["status"] == "RETURNED"
        if is_return:
            chosen = pick_distinct(return_w, rng.choices([1, 2], weights=[70, 30])[0])
        else:
            n_lines = rng.choices([1, 2, 3, 4, 5], weights=[34, 28, 20, 12, 6])[0]
            seed = bundles[rng.randrange(len(bundles))] if rng.random() < 0.30 else ()
            chosen = pick_distinct(buy_w, n_lines, seed)

        for product_id in chosen:
            counter += 1
            quantity = rng.choices([1, 2, 3, 4], weights=[58, 24, 12, 6])[0]
            items.append(
                {
                    "item_id": f"ITEM{counter:06d}",
                    "order_id": order["order_id"],
                    "product_id": product_id,
                    "quantity": -quantity if is_return else quantity,
                    "unit_price": f"{unit_price[product_id] * rng.uniform(0.97, 1.03):.2f}",
                    "discount_percent": rng.choice(DISCOUNT_CHOICES),
                }
            )
    return items


def inject_customer_defects(rng: random.Random, customers: list[dict]) -> dict:
    victims = rng.sample(customers, int(len(customers) * INVALID_EMAIL_RATE))
    for i, customer in enumerate(victims):
        local, _, domain = customer["email"].partition("@")
        customer["email"] = f"{local}{domain}" if i % 2 == 0 else f"{local}@"
    return {"invalid_emails": len(victims)}


def inject_product_defects(rng: random.Random, products: list[dict]) -> dict:
    victims = rng.sample(products, int(len(products) * DIRTY_PRODUCT_NAME_RATE))
    for i, product in enumerate(victims):
        name = product["product_name"]
        if i % 3 == 0:
            product["product_name"] = f"  {name.upper()} "
        elif i % 3 == 1:
            product["product_name"] = f"{name.lower()}   "
        else:
            product["product_name"] = name.replace(" ", "   ")
    return {"dirty_product_names": len(victims)}


def inject_order_defects(rng: random.Random, orders: list[dict]) -> dict:
    missing = rng.sample(orders, int(len(orders) * NULL_CUSTOMER_ID_RATE))
    for i, order in enumerate(missing):
        order["customer_id"] = "NULL" if i % 2 == 0 else ""

    n_reformatted = int(len(orders) * BAD_DATE_FORMAT_RATE)
    touched = rng.sample(range(len(orders)), n_reformatted + FUTURE_ORDER_COUNT)
    for position in touched[:n_reformatted]:
        stamp = datetime.strptime(orders[position]["order_date"], config.TIMESTAMP_FORMAT)
        orders[position]["order_date"] = stamp.strftime("%d-%m-%Y")
    for position in touched[n_reformatted:]:
        ahead = config.REFERENCE_DATE + timedelta(days=rng.randint(20, 400))
        orders[position]["order_date"] = ahead.strftime(config.TIMESTAMP_FORMAT)

    return {
        "null_customer_id": len(missing),
        "wrong_date_format": n_reformatted,
        "future_order_date": FUTURE_ORDER_COUNT,
    }


def inject_item_defects(rng: random.Random, items: list[dict]) -> dict:
    spoiled = rng.sample(range(len(items)), OVER_100_DISCOUNT_COUNT + ZERO_QUANTITY_COUNT)
    for position in spoiled[:OVER_100_DISCOUNT_COUNT]:
        items[position]["discount_percent"] = rng.choice([105, 110, 120, 150, 200])
    for position in spoiled[OVER_100_DISCOUNT_COUNT:]:
        items[position]["quantity"] = 0

    next_id = len(items)
    for i, source in enumerate(rng.sample(items, ORPHAN_ITEM_COUNT), start=1):
        orphan = dict(source)
        orphan["item_id"] = f"ITEM{next_id + i:06d}"
        orphan["order_id"] = f"ORD9{rng.randint(10000, 99999)}"
        items.append(orphan)

    return {
        "discount_over_100": OVER_100_DISCOUNT_COUNT,
        "zero_quantity": ZERO_QUANTITY_COUNT,
        "orphan_order_items": ORPHAN_ITEM_COUNT,
    }


def generate() -> dict:
    rng = random.Random(config.SEED)
    config.ensure_dirs()

    customers = build_customers(rng)
    products = build_products(rng)
    orders = build_orders(rng, customers)
    items = build_order_items(rng, orders, products)

    injected = {}
    injected.update(inject_customer_defects(rng, customers))
    injected.update(inject_product_defects(rng, products))
    injected.update(inject_order_defects(rng, orders))
    injected.update(inject_item_defects(rng, items))
    injected["negative_quantity"] = sum(1 for row in items if int(row["quantity"]) < 0)

    write_csv(config.RAW_DIR / "customers.csv",
              ["customer_id", "customer_name", "email", "registration_date", "customer_type"],
              customers)
    write_csv(config.RAW_DIR / "products.csv",
              ["product_id", "product_name", "category", "subcategory", "cost_price"],
              products)
    write_csv(config.RAW_DIR / "orders.csv",
              ["order_id", "customer_id", "order_date", "status", "region_code"],
              orders)
    write_csv(config.RAW_DIR / "order_items.csv",
              ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"],
              items)

    return {
        "injected": injected,
        "row_counts": {
            "customers": len(customers),
            "products": len(products),
            "orders": len(orders),
            "order_items": len(items),
        },
    }


def main() -> None:
    summary = generate()
    counts, injected = summary["row_counts"], summary["injected"]
    denominator = {
        "invalid_emails": "customers",
        "dirty_product_names": "products",
        "null_customer_id": "orders",
        "wrong_date_format": "orders",
        "future_order_date": "orders",
        "negative_quantity": "order_items",
    }

    print("raw CSVs written to", config.RAW_DIR)
    for table, rows in counts.items():
        print(f"  {table:<12} {rows:>7,} rows")

    print("\ndefects injected on purpose:")
    for name, value in injected.items():
        table = denominator.get(name)
        share = f"  ({value / counts[table]:.1%} of {table})" if table else ""
        print(f"  {name:<22} {value:>6,}{share}")


if __name__ == "__main__":
    main()
