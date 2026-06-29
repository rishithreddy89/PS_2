"""Knowledge base module."""

from app.knowledge.models import (
    Document,
    DocumentChunk,
    DocumentType,
    RetrievalResult,
    HybridRetrievalResult
)
from app.knowledge.embedding import get_embedding_service, EmbeddingService
from app.knowledge.local_embedding import get_local_embedding_service, LocalEmbeddingService
from app.knowledge.chroma_service import get_chroma_service, ChromaDBService
from app.knowledge.ingestion import get_ingestion_service, IngestionService
from app.knowledge.retrieval import get_retrieval_service, HybridRetrievalService

__all__ = [
    "Document",
    "DocumentChunk",
    "DocumentType",
    "RetrievalResult",
    "HybridRetrievalResult",
    "get_embedding_service",
    "EmbeddingService",
    "get_local_embedding_service",
    "LocalEmbeddingService",
    "get_chroma_service",
    "ChromaDBService",
    "get_ingestion_service",
    "IngestionService",
    "get_retrieval_service",
    "HybridRetrievalService"
]
