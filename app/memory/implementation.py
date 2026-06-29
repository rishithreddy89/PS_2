"""In-memory implementation of memory providers."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import asyncio

from app.memory.providers import (
    ShortTermMemory,
    LongTermMemory,
    ConversationMemory,
    CaseMemory
)
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class InMemoryShortTermMemory(ShortTermMemory):
    """In-memory short-term storage."""
    
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        expire_at = None
        if ttl:
            expire_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._store[key] = {
            "value": value,
            "expire_at": expire_at
        }
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        
        entry = self._store[key]
        if entry["expire_at"] and datetime.utcnow() > entry["expire_at"]:
            del self._store[key]
            return None
        
        return entry["value"]
    
    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None
    
    async def clear(self) -> bool:
        self._store.clear()
        return True


class InMemoryLongTermMemory(LongTermMemory):
    """In-memory long-term storage."""
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self._store[key] = value
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)
    
    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        return key in self._store
    
    async def clear(self) -> bool:
        self._store.clear()
        return True
    
    async def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for key, value in self._store.items():
            if isinstance(value, dict):
                match = all(
                    value.get(k) == v for k, v in query.items()
                )
                if match:
                    results.append({"key": key, **value})
        return results


class InMemoryConversationMemory(ConversationMemory):
    """In-memory conversation storage."""
    
    def __init__(self):
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._current_session = "default"
    
    def set_session(self, session_id: str):
        self._current_session = session_id
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if self._current_session not in self._conversations:
            self._conversations[self._current_session] = []
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        return self._conversations.get(self._current_session, [])
    
    async def delete(self, key: str) -> bool:
        if self._current_session in self._conversations:
            del self._conversations[self._current_session]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        return self._current_session in self._conversations
    
    async def clear(self) -> bool:
        self._conversations.clear()
        return True
    
    async def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        if self._current_session not in self._conversations:
            self._conversations[self._current_session] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self._conversations[self._current_session].append(message)
        return True
    
    async def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        messages = self._conversations.get(self._current_session, [])
        return messages[-limit:]


class InMemoryCaseMemory(CaseMemory):
    """In-memory case-specific storage."""
    
    def __init__(self):
        self._cases: Dict[str, Dict[str, Any]] = {}
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        parts = key.split(":", 1)
        if len(parts) == 2:
            case_id, field = parts
            if case_id not in self._cases:
                self._cases[case_id] = {}
            self._cases[case_id][field] = value
            return True
        return False
    
    async def get(self, key: str) -> Optional[Any]:
        parts = key.split(":", 1)
        if len(parts) == 2:
            case_id, field = parts
            return self._cases.get(case_id, {}).get(field)
        return self._cases.get(key)
    
    async def delete(self, key: str) -> bool:
        if ":" in key:
            case_id, field = key.split(":", 1)
            if case_id in self._cases and field in self._cases[case_id]:
                del self._cases[case_id][field]
                return True
        elif key in self._cases:
            del self._cases[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None
    
    async def clear(self) -> bool:
        self._cases.clear()
        return True
    
    async def set_case_context(self, case_id: str, context: Dict[str, Any]) -> bool:
        self._cases[case_id] = context
        return True
    
    async def get_case_context(self, case_id: str) -> Optional[Dict[str, Any]]:
        return self._cases.get(case_id)


class MemoryManager:
    """Centralized memory manager."""
    
    def __init__(self):
        self.short_term = InMemoryShortTermMemory()
        self.long_term = InMemoryLongTermMemory()
        self.conversation = InMemoryConversationMemory()
        self.case_memory = InMemoryCaseMemory()
    
    async def store_recommendation(
        self,
        case_id: str,
        recommendation: Dict[str, Any],
        status: str
    ):
        """Store recommendation with status."""
        key = f"recommendations:{case_id}:{status}"
        existing = await self.long_term.get(key) or []
        existing.append({
            **recommendation,
            "stored_at": datetime.utcnow().isoformat()
        })
        await self.long_term.set(key, existing)
    
    async def get_case_recommendations(
        self,
        case_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations for case."""
        if status:
            key = f"recommendations:{case_id}:{status}"
            return await self.long_term.get(key) or []
        
        all_recs = []
        for status in ["accepted", "rejected", "modified"]:
            key = f"recommendations:{case_id}:{status}"
            recs = await self.long_term.get(key) or []
            all_recs.extend(recs)
        
        return all_recs
    
    async def store_feedback(self, case_id: str, feedback: Dict[str, Any]):
        """Store lawyer feedback."""
        key = f"feedback:{case_id}"
        existing = await self.long_term.get(key) or []
        existing.append({
            **feedback,
            "stored_at": datetime.utcnow().isoformat()
        })
        await self.long_term.set(key, existing)
    
    async def get_memory_context(self, case_id: str) -> Dict[str, Any]:
        """Get comprehensive memory context for case."""
        return {
            "case_context": await self.case_memory.get_case_context(case_id) or {},
            "recommendations": await self.get_case_recommendations(case_id),
            "feedback": await self.long_term.get(f"feedback:{case_id}") or [],
            "conversation": await self.conversation.get_history(limit=20)
        }


_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get singleton memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
