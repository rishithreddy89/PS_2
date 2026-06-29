"""
Recommendation repository for database operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository for Recommendation model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize recommendation repository.

        Args:
            db: Database session
        """
        super().__init__(Recommendation, db)
