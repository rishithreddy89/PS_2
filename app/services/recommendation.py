"""
Recommendation service for business logic operations.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.repositories.recommendation import RecommendationRepository
from app.services.base import BaseService


class RecommendationService(BaseService[Recommendation]):
    """Service for Recommendation business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize recommendation service.

        Args:
            db: Database session
        """
        self.repository = RecommendationRepository(db)

    async def create(self, data: Dict[str, Any]) -> Recommendation:
        """Create a new recommendation."""
        return await self.repository.create(data)

    async def get_by_id(self, id: str) -> Optional[Recommendation]:
        """Get recommendation by ID."""
        return await self.repository.get_by_id(id)

    async def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """Get multiple recommendations."""
        return await self.repository.get_multi(skip=skip, limit=limit, filters=filters)

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Recommendation]:
        """Update a recommendation."""
        return await self.repository.update(id, data)

    async def delete(self, id: str) -> bool:
        """Delete a recommendation."""
        return await self.repository.delete(id)

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count recommendations with optional filters."""
        return await self.repository.count(filters)
