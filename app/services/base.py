"""
Base service interface for business logic layer.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseService(ABC, Generic[T]):
    """Base service interface for business logic operations."""

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data: Entity data

        Returns:
            Created entity
        """
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None
        """
        pass

    @abstractmethod
    async def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Get multiple entities.

        Args:
            skip: Number to skip
            limit: Maximum number to return
            filters: Filter conditions

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity.

        Args:
            id: Entity ID
            data: Update data

        Returns:
            Updated entity or None
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete an entity.

        Args:
            id: Entity ID

        Returns:
            True if deleted
        """
        pass
