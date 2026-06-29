"""
Case document model for storing document metadata.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class CaseDocument(Base, BaseModel):
    """Case document model for document management."""

    __tablename__ = "case_documents"

    case_id = Column(CHAR(36), ForeignKey("cases.id"), nullable=False, index=True)

    document_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    file_path = Column(String(1000), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    source = Column(String(100), nullable=True)
    source_url = Column(String(1000), nullable=True)

    vector_store_ids = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)

    case = relationship("Case", back_populates="documents")

    def __repr__(self) -> str:
        """String representation."""
        return f"<CaseDocument(id={self.id}, title={self.title}, document_type={self.document_type})>"
