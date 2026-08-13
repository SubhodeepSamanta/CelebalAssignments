import os
import glob
import csv
import json
import random
from pathlib import Path
from src.config import DATA_DIR


def generate_customers_json():
    cust_dir = DATA_DIR / "customers"
    cust_dir.mkdir(parents=True, exist_ok=True)
    json_path = cust_dir / "customers.json"

    customer_ids = set()
    order_files = glob.glob(str(DATA_DIR / "orders" / "orders_*.csv"))

    for filepath in order_files:
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("customer_id", "").strip()
                if cid:
                    customer_ids.add(cid)

    customer_ids.update(["CUST-4421", "CUST-8834", "CUST-2201"])
    sorted_ids = sorted(list(customer_ids))

    random.seed(42)
    sample_names = [
        "Rohan Mehta", "Sneha Patil", "Aarav Sharma", "Priya Singh",
        "Vikram Malhotra", "Ananya Gupta", "Kabir Verma", "Diya Joshi",
        "Rahul Nair", "Neha Iyer", "Amit Patel", "Kavya Reddy",
        "Siddharth Rao", "Pooja Kapoor", "Rohan Das", "Shruti Saxena",
        "Karan Bhatia", "Tanvi Choudhury", "Aditya Roy", "Meera Kulkarni"
    ]
    cities = ["Delhi", "Mumbai", "Bengaluru"]

    customers = []
    for idx, cid in enumerate(sorted_ids):
        name = sample_names[idx % len(sample_names)]
        email_name = name.lower().replace(" ", ".")
        email = f"{email_name}{idx}@example.com" if idx >= len(sample_names) else f"{email_name}@example.com"
        phone = f"+91-9{random.randint(100000009, 999999999)}"
        city = cities[idx % len(cities)]
        registered_on = f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        loyalty_points = random.randint(50, 850)

        customers.append({
            "customer_id": cid,
            "name": name,
            "email": email,
            "phone": phone,
            "city": city,
            "registered_on": registered_on,
            "loyalty_points": loyalty_points
        })

    with open(json_path, mode="w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)

    return json_path


if __name__ == "__main__":
    generate_customers_json()
