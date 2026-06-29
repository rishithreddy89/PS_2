"""Local embedding service using sentence-transformers."""

from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sentence_transformers import SentenceTransformer

from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class LocalEmbeddingService:
    """Service for generating embeddings locally using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._load_model()
    
    def _load_model(self):
        """Load the sentence-transformers model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                lambda: self.model.encode(text, convert_to_tensor=False).tolist()
            )
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                lambda: self.model.encode(
                    texts,
                    convert_to_tensor=False,
                    batch_size=batch_size,
                    show_progress_bar=False
                ).tolist()
            )
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise
    
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        return await self.embed_text(query)


_local_embedding_service: Optional[LocalEmbeddingService] = None


def get_local_embedding_service() -> LocalEmbeddingService:
    """Get singleton local embedding service."""
    global _local_embedding_service
    if _local_embedding_service is None:
        _local_embedding_service = LocalEmbeddingService()
    return _local_embedding_service
