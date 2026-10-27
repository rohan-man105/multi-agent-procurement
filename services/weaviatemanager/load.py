from pathlib import Path

import pandas as pd
import weaviate.classes.config as wc

from services.weaviatemanager.sync import EMBED_COLUMNS, upsert_order
from services.weaviatemanager.utils import get_client


DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset" / "spend_analysis_dataset.csv"


def create_embeddings():
    client = get_client()
    if not client.collections.exists("Order"):
        client.collections.create(
            name="Order",
            vectorizer_config=[
                wc.Configure.NamedVectors.none(name=f"{column}_vector")
                for column in EMBED_COLUMNS
            ],
        )

    data = pd.read_csv(DATASET_PATH).fillna("")
    for row in data.to_dict(orient="records"):
        upsert_order(row)

    print(f"\nOrder Embeddings Synchronized: {len(data)}\n")
