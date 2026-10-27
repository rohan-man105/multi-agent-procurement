from __future__ import annotations

import uuid
from typing import Any


EMBED_COLUMNS = ["ItemName", "Category", "Supplier", "Buyer"]


def _properties(order: dict[str, Any]) -> dict[str, Any]:
    return {
        "TransactionID": order.get("TransactionID", ""),
        "OrderType": order.get("OrderType", ""),
        "ParentTransactionID": order.get("ParentTransactionID", ""),
        "Status": order.get("Status", ""),
        "ItemName": order.get("ItemName", ""),
        "Category": order.get("Category", ""),
        "Quantity": order.get("Quantity", ""),
        "UnitPrice": order.get("UnitPrice", ""),
        "TotalCost": order.get("TotalCost", ""),
        "PurchaseDate": order.get("PurchaseDate", ""),
        "Supplier": order.get("Supplier", ""),
        "Buyer": order.get("Buyer", ""),
        "Currency": order.get("Currency", "USD"),
    }


def upsert_order(order: dict[str, Any]) -> None:
    """Insert or replace one order in Weaviate using a stable UUID."""
    from services.weaviatemanager.utils import get_client, model

    client = get_client()
    collection = client.collections.use("Order")
    properties = _properties(order)
    vectors = {
        f"{column}_vector": model.encode(
            str(properties[column]), normalize_embeddings=True
        ).tolist()
        for column in EMBED_COLUMNS
    }
    object_uuid = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"procurement-order:{properties['TransactionID']}",
    )

    try:
        collection.data.replace(
            uuid=object_uuid,
            properties=properties,
            vector=vectors,
        )
    except Exception:
        collection.data.insert(
            uuid=object_uuid,
            properties=properties,
            vector=vectors,
        )
