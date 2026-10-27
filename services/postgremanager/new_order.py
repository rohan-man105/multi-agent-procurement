from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import pandas as pd

from services.postgremanager.persistence import (
    ORDER_FIELD_MAP,
    get_order_by_id,
    insert_order,
    next_transaction_id,
    record_audit_event,
    update_order_in_db,
)
from services.weaviatemanager.sync import upsert_order


DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "dataset" / "spend_analysis_dataset.csv"
)

DATASET_COLUMNS = [
    "TransactionID", "OrderType", "ParentTransactionID", "Status",
    "ItemName", "Category", "Quantity", "UnitPrice", "TotalCost",
    "PurchaseDate", "Supplier", "Buyer", "Currency",
]

AUDIT_PATH = DATASET_PATH.with_name("order_audit_log.csv")
AUDIT_COLUMNS = [
    "EventID", "EventType", "TransactionID", "ParentTransactionID",
    "Field", "OldValue", "NewValue", "Actor", "EventDate",
]


def generate_transaction_id(df: pd.DataFrame) -> str:
    """Generate the next TXN identifier without relying on row count."""
    numbers = []
    for transaction_id in df["TransactionID"].astype(str):
        if transaction_id.startswith("TXN"):
            try:
                numbers.append(int(transaction_id[3:]))
            except ValueError:
                continue
    return f"TXN{max(numbers, default=0) + 1:03d}"


def _money(value, field_name: str) -> Decimal:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a valid number") from exc
    if amount < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return amount


def _quantity(value) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("quantity must be a positive whole number") from exc
    if quantity <= 0:
        raise ValueError("quantity must be a positive whole number")
    return quantity


def _read_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH, dtype=str).fillna("")
    missing = [column for column in DATASET_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError("Dataset is missing required columns: " + ", ".join(missing))
    return df[DATASET_COLUMNS]


def _write_audit_event(
    event_type: str,
    transaction_id: str,
    parent_transaction_id: str,
    field: str,
    old_value: str,
    new_value: str,
    actor: str,
) -> None:
    if AUDIT_PATH.exists():
        audit_df = pd.read_csv(AUDIT_PATH, dtype=str).fillna("")
    else:
        audit_df = pd.DataFrame(columns=AUDIT_COLUMNS)

    event = {
        "EventID": f"EVT{len(audit_df) + 1:05d}",
        "EventType": event_type,
        "TransactionID": transaction_id,
        "ParentTransactionID": parent_transaction_id,
        "Field": field,
        "OldValue": old_value,
        "NewValue": new_value,
        "Actor": actor,
        "EventDate": date.today().isoformat(),
    }
    audit_df = pd.concat([audit_df, pd.DataFrame([event], columns=AUDIT_COLUMNS)], ignore_index=True)
    audit_df.to_csv(AUDIT_PATH, index=False)
    record_audit_event(
        event["EventID"], event_type, transaction_id, parent_transaction_id,
        field, old_value, new_value, actor,
    )


def _sync_search_index(order: dict) -> None:
    try:
        upsert_order(order)
    except Exception as exc:
        # PostgreSQL remains authoritative; a retry can rebuild this index.
        print(f"[Weaviate Sync Warning] {exc}")


def add_new_order(
    item_name: str,
    category: str,
    quantity,
    *,
    unit_price=None,
    supplier: str | None = None,
    buyer: str | None = None,
    status: str = "draft",
    currency: str = "USD",
    order_type: str = "new",
    parent_transaction_id: str = "",
    purchase_date: str | None = None,
) -> dict:
    """Append one validated procurement record to the dataset.

    Price and supplier are optional while a request is still a draft. The
    function never invents financial or ownership data.
    """
    item_name = item_name.strip()
    category = category.strip()
    supplier = supplier.strip() if supplier else ""
    buyer = buyer.strip() if buyer else ""
    status = status.strip().lower()
    order_type = order_type.strip().lower()
    currency = currency.strip().upper()

    if not item_name or not category:
        raise ValueError("item_name and category are required")
    if order_type not in {"new", "renewal", "modification"}:
        raise ValueError("order_type must be new, renewal, or modification")
    if status not in {"draft", "pending_approval", "approved", "ordered", "completed", "cancelled"}:
        raise ValueError("unsupported order status")
    if not currency:
        raise ValueError("currency is required")

    quantity_value = _quantity(quantity)
    unit_price_value = None if unit_price in (None, "") else _money(unit_price, "unit_price")
    total_cost_value = (
        None if unit_price_value is None
        else (unit_price_value * quantity_value).quantize(Decimal("0.01"))
    )

    df = _read_dataset()

    new_order = {
        "TransactionID": next_transaction_id(),
        "OrderType": order_type,
        "ParentTransactionID": parent_transaction_id.strip(),
        "Status": status,
        "ItemName": item_name,
        "Category": category,
        "Quantity": quantity_value,
        "UnitPrice": "" if unit_price_value is None else str(unit_price_value),
        "TotalCost": "" if total_cost_value is None else str(total_cost_value),
        "PurchaseDate": purchase_date or date.today().isoformat(),
        "Supplier": supplier,
        "Buyer": buyer,
        "Currency": currency,
    }

    updated_df = pd.concat(
        [df[DATASET_COLUMNS], pd.DataFrame([new_order], columns=DATASET_COLUMNS)],
        ignore_index=True,
    )
    insert_order(new_order)
    updated_df.to_csv(DATASET_PATH, index=False)
    _sync_search_index(new_order)
    return new_order


def create_renewal_from_order(
    parent_transaction_id: str,
    edit_field: str,
    edit_value: str,
    *,
    actor: str = "system",
) -> dict:
    """Create a new renewal row linked to an existing transaction."""
    parent_transaction_id = parent_transaction_id.strip()
    edit_field = edit_field.strip().lower().replace(" ", "_")
    edit_value = edit_value.strip()
    source = get_order_by_id(parent_transaction_id)
    if source is None:
        raise ValueError(f"No order found for {parent_transaction_id}")

    field_map = {
        "item": "item_name",
        "item_name": "item_name",
        "itemname": "item_name",
        "quantity": "quantity",
        "supplier": "supplier",
        "buyer": "buyer",
        "unit_price": "unit_price",
        "unitprice": "unit_price",
    }
    normalized_field = field_map.get(edit_field)
    if normalized_field is None:
        raise ValueError("Renewal field must be item_name, quantity, supplier, buyer, or unit_price")
    if not edit_value:
        raise ValueError("Renewal value is required")

    db_field_map = {
        "item_name": "itemname", "quantity": "quantity", "supplier": "supplier",
        "buyer": "buyer", "unit_price": "unitprice",
    }
    old_value = str(source.get(db_field_map[normalized_field]) or "")
    values = {
        "item_name": source["itemname"],
        "category": source["category"],
        "quantity": source["quantity"],
        "unit_price": source["unitprice"] or None,
        "supplier": source["supplier"],
        "buyer": source["buyer"],
    }
    values[normalized_field] = edit_value

    renewal = add_new_order(
        item_name=values["item_name"],
        category=values["category"],
        quantity=values["quantity"],
        unit_price=values["unit_price"],
        supplier=values["supplier"],
        buyer=values["buyer"],
        status="pending_approval",
        currency=source["currency"] or "USD",
        order_type="renewal",
        parent_transaction_id=source["transactionid"],
    )
    _write_audit_event(
        "renewal_created",
        renewal["TransactionID"],
        source["TransactionID"],
        normalized_field,
        old_value,
        edit_value,
        actor,
    )
    return renewal


def update_order(
    transaction_id: str,
    field: str,
    value: str,
    *,
    actor: str = "system",
) -> dict:
    """Update an existing order and write an audit event."""
    transaction_id = transaction_id.strip()
    source = get_order_by_id(transaction_id)
    if source is None:
        raise ValueError(f"No order found for {transaction_id}")
    field_map = {
        "item_name": "ItemName", "itemname": "ItemName", "quantity": "Quantity",
        "supplier": "Supplier", "buyer": "Buyer", "unit_price": "UnitPrice",
        "unitprice": "UnitPrice", "status": "Status",
    }
    column = field_map.get(field.strip().lower().replace(" ", "_"))
    if column is None:
        raise ValueError("Unsupported order field")

    old_value = str(source.get(column.lower()) or "")
    if column == "Quantity":
        value = str(_quantity(value))
    elif column == "UnitPrice":
        value = str(_money(value, "unit_price"))
    df.at[index, column] = value.strip()

    if column in {"Quantity", "UnitPrice"}:
        quantity_value = _quantity(
            value if column == "Quantity" else source.get("quantity")
        )
        unit_price_value = _money(
            value if column == "UnitPrice" else source.get("unitprice"),
            "unit_price",
        )
        total_cost = str((quantity_value * unit_price_value).quantize(Decimal("0.01")))
    else:
        total_cost = None

    db_field = ORDER_FIELD_MAP[column]
    update_fields = {db_field: value.strip()}
    if total_cost is not None:
        update_fields["totalcost"] = total_cost
    update_order_in_db(transaction_id, update_fields)

    df = _read_dataset()
    matches = df[df["TransactionID"].str.upper() == transaction_id.upper()]
    if matches.empty:
        raise ValueError(f"CSV export has no order for {transaction_id}")
    index = matches.index[0]
    df.at[index, column] = value.strip()
    if total_cost is not None:
        df.at[index, "TotalCost"] = total_cost
    df.to_csv(DATASET_PATH, index=False)
    updated_order = df.loc[index].to_dict()
    _sync_search_index(updated_order)
    _write_audit_event(
        "order_modified",
        transaction_id,
        source.get("parenttransactionid") or "",
        column,
        old_value,
        value,
        actor,
    )
    return updated_order
