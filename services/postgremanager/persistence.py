from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text

from services.postgremanager.utils import engine


ORDER_DB_COLUMNS = [
    "transactionid", "ordertype", "parenttransactionid", "status",
    "itemname", "category", "quantity", "unitprice", "totalcost",
    "purchasedate", "supplier", "buyer", "currency",
]

ORDER_FIELD_MAP = {
    "TransactionID": "transactionid",
    "OrderType": "ordertype",
    "ParentTransactionID": "parenttransactionid",
    "Status": "status",
    "ItemName": "itemname",
    "Category": "category",
    "Quantity": "quantity",
    "UnitPrice": "unitprice",
    "TotalCost": "totalcost",
    "PurchaseDate": "purchasedate",
    "Supplier": "supplier",
    "Buyer": "buyer",
    "Currency": "currency",
}


def _db_values(order: dict[str, Any]) -> dict[str, Any]:
    values = {
        ORDER_FIELD_MAP[key]: order.get(key, "")
        for key in ORDER_FIELD_MAP
    }
    for key in ("quantity", "unitprice", "totalcost"):
        if values[key] == "":
            values[key] = None
    return values


def next_transaction_id() -> str:
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT COALESCE(
                MAX(CAST(SUBSTRING(transactionid FROM 4) AS INTEGER)), 0
            )
            FROM orders
            WHERE transactionid ~ '^TXN[0-9]+$'
        """)).scalar_one()
    return f"TXN{int(result) + 1:03d}"


def insert_order(order: dict[str, Any]) -> None:
    values = _db_values(order)
    columns = ", ".join(ORDER_DB_COLUMNS)
    placeholders = ", ".join(f":{column}" for column in ORDER_DB_COLUMNS)
    with engine.begin() as connection:
        connection.execute(
            text(f"INSERT INTO orders ({columns}) VALUES ({placeholders})"),
            values,
        )


def get_order_by_id(transaction_id: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT * FROM orders WHERE transactionid = :transaction_id"),
            {"transaction_id": transaction_id.strip()},
        ).mappings().first()
    return dict(row) if row else None


def update_order_in_db(transaction_id: str, fields: dict[str, Any]) -> None:
    allowed = set(ORDER_DB_COLUMNS)
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        raise ValueError("No valid order fields supplied")

    assignments = ", ".join(f"{key} = :{key}" for key in updates)
    updates["transaction_id"] = transaction_id.strip()
    with engine.begin() as connection:
        result = connection.execute(
            text(
                f"UPDATE orders SET {assignments} "
                "WHERE transactionid = :transaction_id"
            ),
            updates,
        )
    if result.rowcount != 1:
        raise ValueError(f"No order found for {transaction_id}")


def ensure_audit_table() -> None:
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS order_audit_log (
                eventid VARCHAR(32) PRIMARY KEY,
                eventtype VARCHAR(64) NOT NULL,
                transactionid VARCHAR(32) NOT NULL,
                parenttransactionid VARCHAR(32),
                field VARCHAR(64),
                oldvalue TEXT,
                newvalue TEXT,
                actor VARCHAR(128),
                eventdate DATE NOT NULL
            )
        """))


def record_audit_event(
    event_id: str,
    event_type: str,
    transaction_id: str,
    parent_transaction_id: str,
    field: str,
    old_value: str,
    new_value: str,
    actor: str,
) -> None:
    ensure_audit_table()
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO order_audit_log (
                    eventid, eventtype, transactionid, parenttransactionid,
                    field, oldvalue, newvalue, actor, eventdate
                ) VALUES (
                    :event_id, :event_type, :transaction_id,
                    :parent_transaction_id, :field, :old_value,
                    :new_value, :actor, :event_date
                )
            """),
            {
                "event_id": event_id,
                "event_type": event_type,
                "transaction_id": transaction_id,
                "parent_transaction_id": parent_transaction_id or None,
                "field": field or None,
                "old_value": old_value,
                "new_value": new_value,
                "actor": actor,
                "event_date": date.today(),
            },
        )
