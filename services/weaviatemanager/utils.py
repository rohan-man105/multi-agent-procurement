import weaviate
from sentence_transformers import SentenceTransformer


_client = None

def get_client():
    global _client
    if _client is None or not _client.is_connected():
        _client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051
        )
    return _client

client = get_client()

model = SentenceTransformer("all-MiniLM-L6-v2")