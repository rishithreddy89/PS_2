"""Embedding service for document vectorization."""

from typing import List, Optional
import asyncio

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.dimension = settings.vector_db_dimension
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                logger.info(f"Embedded batch {i//batch_size + 1}", count=len(batch))
            except Exception as e:
                logger.error("Batch embedding failed", batch=i//batch_size, error=str(e))
                raise
        
        return embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        return await self.embed_text(query)


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
