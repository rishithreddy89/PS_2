"""
Case repository for database operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    """Repository for Case model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize case repository.

        Args:
            db: Database session
        """
        super().__init__(Case, db)
