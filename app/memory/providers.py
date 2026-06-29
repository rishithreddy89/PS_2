"""
Memory provider interfaces for agent memory management.

This module defines abstract interfaces for future memory implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MemoryProvider(ABC):
    """
    Base memory provider interface.
    
    All memory implementations should inherit from this interface.
    """

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in memory.

        Args:
            key: Memory key
            value: Value to store
            ttl: Time-to-live in seconds (optional)

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from memory.

        Args:
            key: Memory key

        Returns:
            Stored value or None
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from memory.

        Args:
            key: Memory key

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in memory.

        Args:
            key: Memory key

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all memory.

        Returns:
            Success status
        """
        pass


class ShortTermMemory(MemoryProvider):
    """
    Short-term memory interface for temporary storage.
    
    Used for:
    - Active execution context
    - Agent intermediate results
    - Session data
    
    Typically implemented with Redis or in-memory cache.
    """

    pass


class LongTermMemory(MemoryProvider):
    """
    Long-term memory interface for persistent storage.
    
    Used for:
    - Historical data
    - Learning feedback
    - User preferences
    - Case history
    
    Typically implemented with database storage.
    """

    @abstractmethod
    async def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search long-term memory.

        Args:
            query: Search query

        Returns:
            Search results
        """
        pass


class ConversationMemory(MemoryProvider):
    """
    Conversation memory interface for dialogue context.
    
    Used for:
    - Multi-turn conversations
    - Context tracking
    - User intent history
    """

    @abstractmethod
    async def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to conversation history.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        pass


class CaseMemory(MemoryProvider):
    """
    Case memory interface for case-specific context.
    
    Used for:
    - Case-specific data
    - Execution context per case
    - Agent outputs per case
    """

    @abstractmethod
    async def set_case_context(self, case_id: str, context: Dict[str, Any]) -> bool:
        """
        Set case context.

        Args:
            case_id: Case ID
            context: Case context data

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def get_case_context(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get case context.

        Args:
            case_id: Case ID

        Returns:
            Case context or None
        """
        pass
