"""
Memory service interface for agent memory management.

This is a placeholder for future implementation in Phase 2.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class MemoryService(ABC):
    """
    Memory service interface for agent memory operations.
    
    Future implementation will handle:
    - Short-term memory
    - Long-term memory
    - Conversation memory
    - Case memory
    - Memory persistence
    """

    @abstractmethod
    async def store(self, key: str, value: Any, memory_type: str = "short_term") -> bool:
        """
        Store data in memory.

        Args:
            key: Memory key
            value: Memory value
            memory_type: Type of memory

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def retrieve(self, key: str, memory_type: str = "short_term") -> Optional[Any]:
        """
        Retrieve data from memory.

        Args:
            key: Memory key
            memory_type: Type of memory

        Returns:
            Stored value or None
        """
        pass

    @abstractmethod
    async def delete(self, key: str, memory_type: str = "short_term") -> bool:
        """
        Delete data from memory.

        Args:
            key: Memory key
            memory_type: Type of memory

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def clear(self, memory_type: str = "short_term") -> bool:
        """
        Clear all data from memory type.

        Args:
            memory_type: Type of memory

        Returns:
            Success status
        """
        pass
