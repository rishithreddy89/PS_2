"""Knowledge base models."""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document types."""
    STATUTE = "statute"
    CASE_LAW = "case_law"
    COURT_JUDGMENT = "court_judgment"
    PLAYBOOK = "playbook"
    TEMPLATE = "template"
    SAMPLE_CASE = "sample_case"
    POLICY = "policy"
    MARKDOWN = "markdown"
    TEXT = "text"
    PDF = "pdf"


class Document(BaseModel):
    """Knowledge base document."""
    document_id: str
    title: str
    content: str
    document_type: DocumentType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ingested_at: Optional[datetime] = None


class DocumentChunk(BaseModel):
    """Document chunk for embedding."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Single retrieval result."""
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_type: Optional[DocumentType] = None


class HybridRetrievalResult(BaseModel):
    """Hybrid retrieval result with multiple scores."""
    document_id: str
    chunk_id: str
    content: str
    vector_score: float
    bm25_score: float
    final_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_type: Optional[DocumentType] = None
