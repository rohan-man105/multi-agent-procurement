import random
from datetime import date

import pandas as pd

from env import url


SUPPLIERS = [
    "TechMart Inc.",
    "CloudSoft Corp.",
    "FurniWorks Ltd.",
    "OfficePro Ltd.",
]

BUYERS = [
    "Kelly Joseph",
    "Luis Holland",
    "Kevin Adams",
    "Rohan Sharma",
]


def generate_transaction_id(df: pd.DataFrame) -> str:
    existing_ids = set(df["TransactionID"].astype(str))

    max_num = 0
    for transaction_id in existing_ids:
        if transaction_id.startswith("TXN"):
            try:
                max_num = max(max_num, int(transaction_id.replace("TXN", "")))
            except ValueError:
                pass

    new_num = max_num + 1
    return f"TXN{new_num:03d}"


def add_new_order(item_name: str, category: str, quantity: str) -> dict:
    df = pd.read_csv(url)

    quantity_value = int(float(quantity))
    unit_price = round(random.uniform(5, 500), 2)
    total_cost = round(quantity_value * unit_price, 2)

    new_order = {
        "TransactionID": generate_transaction_id(df),
        "ItemName": item_name,
        "Category": category,
        "Quantity": quantity_value,
        "UnitPrice": unit_price,
        "TotalCost": total_cost,
        "PurchaseDate": date.today().isoformat(),
        "Supplier": random.choice(SUPPLIERS),
        "Buyer": random.choice(BUYERS),
    }

    df = pd.concat([df, pd.DataFrame([new_order])], ignore_index=True)
    df.to_csv(url, index=False)

    return new_order