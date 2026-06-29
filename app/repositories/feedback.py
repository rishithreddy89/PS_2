"""
Feedback repository for database operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for Feedback model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize feedback repository.

        Args:
            db: Database session
        """
        super().__init__(Feedback, db)
