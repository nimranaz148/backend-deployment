# src/services/embedding_service.py
from typing import List
from openai import OpenAI
from src.core.config import settings

class EmbeddingService:
    def __init__(self):
        # Initialize OpenAI client for embeddings
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Sasta aur acha embedding model
        self.model = "text-embedding-3-small"

    def get_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a single text string."""
        try:
            # New OpenAI syntax for embeddings
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []