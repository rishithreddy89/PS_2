"""
Case service for business logic operations.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.repositories.case import CaseRepository
from app.services.base import BaseService


class CaseService(BaseService[Case]):
    """Service for Case business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize case service.

        Args:
            db: Database session
        """
        self.repository = CaseRepository(db)

    async def create(self, data: Dict[str, Any]) -> Case:
        """Create a new case."""
        return await self.repository.create(data)

    async def get_by_id(self, id: str) -> Optional[Case]:
        """Get case by ID."""
        return await self.repository.get_by_id(id)

    async def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[Case]:
        """Get multiple cases."""
        return await self.repository.get_multi(skip=skip, limit=limit, filters=filters)

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Case]:
        """Update a case."""
        return await self.repository.update(id, data)

    async def delete(self, id: str) -> bool:
        """Delete a case."""
        return await self.repository.delete(id)

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count cases with optional filters."""
        return await self.repository.count(filters)
