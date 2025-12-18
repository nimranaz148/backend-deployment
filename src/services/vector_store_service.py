# src/services/vector_store_service.py
from qdrant_client import QdrantClient, models
from typing import List, Dict
import hashlib

from src.core.config import settings

class VectorStoreService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        self.collection_name = "textbook_embeddings"

        self.vector_size = 1536  # OpenAI text-embedding-3-small standard size

    def recreate_collection(self):
        """Deletes and recreates the collection."""
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
        )

    def upsert_vectors(self, chunks: List[Dict[str, str]], embeddings: List[List[float]]):
        """Upserts vectors and their payloads to the Qdrant collection."""
        points = []
        for i, chunk in enumerate(chunks):
            # Create a consistent integer ID from the hash
            chunk_id = int(hashlib.md5(chunk["chunk_hash"].encode()).hexdigest(), 16) % (2**63 - 1)
            
            points.append(
                models.PointStruct(
                    id=chunk_id,
                    vector=embeddings[i],
                    payload={
                        "text": chunk["content"],
                        "source_file": chunk["source_file"],
                        "chunk_hash": chunk["chunk_hash"],
                    },
                )
            )
        
        operation_info = self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points,
        )
        return operation_info

    def search_vectors(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Searches for similar vectors in the collection."""
        try:
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                with_payload=True,
            )
            results = []
            for point in response.points:
                results.append({
                    "score": point.score,
                    "text": point.payload.get("text"),
                    "source_file": point.payload.get("source_file"),
                })
            return results
        except Exception as e:
            print(f"Error searching vectors: {e}")
            return []