import weaviate.classes.query as wq
from services.weaviatemanager.utils import get_client,model



def get_info(query:str , limit: int=5) -> list[dict]:
    client = get_client()

    try:
        query_vector = model.encode(query,normalize_embeddings=True)
        order_collection = client.collections.use("Order")

        result = order_collection.query.hybrid(
            query=query,
            vector=query_vector,
            target_vector=wq.TargetVectors.average(
                ["ItemName_vector", "Category_vector",
                 "Supplier_vector", "Buyer_vector"]
            ),
            alpha=0.7,
            limit=limit,
            query_properties=["ItemName", "Category", "Supplier", "Buyer"],
            return_properties=[
    "transactionID", "itemName", "category", "quantity",
    "unitPrice", "totalCost", "purchaseDate", "supplier", "buyer"
],
            return_metadata=wq.MetadataQuery(score=True)
        )

        return [
            {**obj.properties, "_score": obj.metadata.score}
            for obj in result.objects
        ]

    except Exception as e:
        print(f"[Weaviate Error] {e}")
        return []


def format_docs(docs: list[dict]) -> str:
    if not docs:
        return "No matching orders were found for this query."

    blocks = []
    for i, doc in enumerate(docs, start=1):
        block = (
            f"[Order {i}] (relevance score: {doc.get('_score', 'N/A'):.3f})\n"
            f"  Transaction ID : {doc.get('transactionID', doc.get('TransactionID', 'N/A'))}\n"
            f"  Item Name      : {doc.get('itemName', doc.get('ItemName', 'N/A'))}\n"
            f"  Category       : {doc.get('category', doc.get('Category', 'N/A'))}\n"
            f"  Quantity       : {doc.get('quantity', doc.get('Quantity', 'N/A'))}\n"
            f"  Unit Price     : {doc.get('unitPrice', doc.get('UnitPrice', 'N/A'))}\n"
            f"  Total Cost     : {doc.get('totalCost', doc.get('TotalCost', 'N/A'))}\n"
            f"  Purchase Date  : {doc.get('purchaseDate', doc.get('PurchaseDate', 'N/A'))}\n"
            f"  Supplier       : {doc.get('supplier', doc.get('Supplier', 'N/A'))}\n"
            f"  Buyer          : {doc.get('buyer', doc.get('Buyer', 'N/A'))}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)   