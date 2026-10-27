from pathlib import Path

import pandas as pd

from services.postgremanager.persistence import ensure_audit_table
from services.postgremanager.utils import engine


DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset" / "spend_analysis_dataset.csv"


def sql_load():
    """Seed PostgreSQL from the CSV during application startup."""
    orders = pd.read_csv(DATASET_PATH)
    orders.columns = orders.columns.str.lower().str.replace(" ", "_", regex=False)
    orders.to_sql("orders", engine, if_exists="replace", index=False)
    ensure_audit_table()
    print(f"Orders Loaded: {len(orders)}\n")
