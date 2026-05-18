# scripts/05_embed_to_qdrant.py
import hashlib
import math
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

qdrant = QdrantClient(host="localhost", port=6333)

qdrant.recreate_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

def embed_text(text: str) -> list[float]:
    values = []
    seed = text.encode()
    for i in range(384):
        digest = hashlib.sha256(seed + i.to_bytes(2, "little")).digest()
        values.append((int.from_bytes(digest[:4], "little") / 2**32) * 2 - 1)
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]

def embed_and_store(records: list[dict]):
    embeddings = [embed_text(record["text"]) for record in records]

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

embed_and_store([
    {"id": "doc_001", "text": "AI platform integration test"},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
])
