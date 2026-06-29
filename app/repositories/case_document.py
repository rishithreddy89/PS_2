"""
Case document repository for document operations.
"""

from typing import List, Optional
from sqlalchemy import select, func, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_document import CaseDocument
from app.repositories.base import BaseRepository


class CaseDocumentRepository(BaseRepository[CaseDocument]):
    """Repository for case document operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(CaseDocument, db)

    async def get_by_case_id(self, case_id: str) -> List[CaseDocument]:
        """
        Get all documents for a case.

        Args:
            case_id: Case ID

        Returns:
            List of case documents
        """
        result = await self.db.execute(
            select(CaseDocument).where(CaseDocument.case_id == case_id)
        )
        return list(result.scalars().all())

    async def get_indexed_documents(self, case_id: str) -> List[CaseDocument]:
        """
        Get indexed documents for a case.
        
        Uses SQLAlchemy 2.x compatible JSON extraction for MySQL.

        Args:
            case_id: Case ID

        Returns:
            List of indexed documents
        """
        # Use func.json_extract for MySQL JSON fields with SQLAlchemy 2.x
        result = await self.db.execute(
            select(CaseDocument).where(
                CaseDocument.case_id == case_id,
                func.json_extract(CaseDocument.meta_data, '$.status') == 'indexed'
            )
        )
        return list(result.scalars().all())

    async def count_indexed_documents(self, case_id: str) -> int:
        """
        Count indexed documents for a case.

        Args:
            case_id: Case ID

        Returns:
            Number of indexed documents
        """
        result = await self.db.execute(
            select(func.count()).select_from(CaseDocument).where(
                CaseDocument.case_id == case_id,
                func.json_extract(CaseDocument.meta_data, '$.status') == 'indexed'
            )
        )
        return result.scalar_one()

    async def get_by_status(self, case_id: str, status: str) -> List[CaseDocument]:
        """
        Get documents by status.

        Args:
            case_id: Case ID
            status: Document status

        Returns:
            List of documents with the given status
        """
        result = await self.db.execute(
            select(CaseDocument).where(
                CaseDocument.case_id == case_id,
                func.json_extract(CaseDocument.meta_data, '$.status') == status
            )
        )
        return list(result.scalars().all())


def get_case_document_repository(db: AsyncSession) -> CaseDocumentRepository:
    """Get case document repository instance."""
    return CaseDocumentRepository(db)
