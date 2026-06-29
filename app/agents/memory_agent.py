"""
Memory Agent - Interfaces with memory providers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.memory.providers import (
    CaseMemory,
    ConversationMemory,
    LongTermMemory,
    ShortTermMemory,
)
from app.memory.implementation import get_memory_manager
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.specialized_agents import MemoryContext
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class MemoryAgent(BaseAgent):
    """
    Memory Agent for managing agent memory.
    
    Interfaces with memory providers to load, store, and merge context.
    Does NOT implement database memory - only interfaces.
    """

    def __init__(
        self,
        short_term: Optional[ShortTermMemory] = None,
        long_term: Optional[LongTermMemory] = None,
        conversation: Optional[ConversationMemory] = None,
        case_memory: Optional[CaseMemory] = None,
    ):
        super().__init__(
            agent_id="memory_agent",
            name="Memory Agent",
            description="Manages agent memory and context",
            version="1.0.0",
            supported_domains=["*"],
            priority=10,
        )

        # Use injected providers or fall back to MemoryManager defaults
        _manager = get_memory_manager()
        self.short_term = short_term or _manager.short_term
        self.long_term = long_term or _manager.long_term
        self.conversation = conversation or _manager.conversation
        self.case_memory = case_memory or _manager.case_memory

    @property
    def capabilities(self) -> List[str]:
        return [
            "memory_loading",
            "memory_storage",
            "context_merging",
            "memory_retrieval",
        ]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return ["short_term", "long_term", "conversation", "case_memory"]

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute memory operations."""
        start_time = datetime.utcnow()
        
        try:
            await self._validate_execution(context)
            
            operation = context.input_data.get("operation", "load")
            
            if operation == "load":
                memory_context = await self._load_memory(context)
            elif operation == "store":
                memory_context = await self._store_memory(context)
            elif operation == "update":
                memory_context = await self._update_memory(context)
            elif operation == "merge":
                memory_context = await self._merge_context(context)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            context.set_shared("memory_context", memory_context)
            context.memory = memory_context.dict()
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={"memory_context": memory_context.dict()},
                duration_ms=duration,
                metadata={"operation": operation},
            )
            
        except Exception as e:
            logger.error("Memory agent failed", error=str(e), request_id=context.request_id)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.FAILED,
                error=str(e),
                duration_ms=duration,
            )

    async def validate(self, context: ExecutionContext) -> bool:
        """Validate execution context."""
        operation = context.input_data.get("operation")
        return operation in ["load", "store", "update", "merge"]

    async def _validate_execution(self, context: ExecutionContext) -> None:
        """Validate before execution."""
        if not await self.validate(context):
            raise ValueError("Invalid operation specified")

    async def _load_memory(self, context: ExecutionContext) -> MemoryContext:
        """Load memory from providers."""
        memory_ctx = MemoryContext(
            case_id=context.case_id,
            execution_id=context.request_id,
        )
        
        # Load from short-term memory
        if self.short_term and context.request_id:
            key = f"execution:{context.request_id}"
            short_term_data = await self.short_term.get(key)
            if short_term_data:
                memory_ctx.short_term = short_term_data
        
        # Load from long-term memory
        if self.long_term and context.case_id:
            key = f"case_history:{context.case_id}"
            long_term_data = await self.long_term.get(key)
            if long_term_data:
                memory_ctx.long_term = long_term_data
        
        # Load conversation history
        if self.conversation and context.case_id:
            conversation_data = await self.conversation.get_history(limit=20)
            if conversation_data:
                memory_ctx.conversation = conversation_data
        
        # Load case-specific memory
        if self.case_memory and context.case_id:
            case_data = await self.case_memory.get_case_context(context.case_id)
            if case_data:
                memory_ctx.case_specific = case_data
        
        logger.info("Memory loaded", case_id=context.case_id, execution_id=context.request_id)
        return memory_ctx

    async def _store_memory(self, context: ExecutionContext) -> MemoryContext:
        """Store memory to providers."""
        memory_data = context.input_data.get("memory_data", {})
        
        memory_ctx = MemoryContext(
            case_id=context.case_id,
            execution_id=context.request_id,
        )
        
        # Store to short-term memory
        if self.short_term and context.request_id:
            key = f"execution:{context.request_id}"
            short_term_data = {
                "execution_id": context.request_id,
                "agent_outputs": {k: v.dict() for k, v in context.agent_outputs.items()},
                "shared_context": context.shared_context,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.short_term.set(key, short_term_data, ttl=3600)
            memory_ctx.short_term = short_term_data
        
        # Store to long-term memory
        if self.long_term and context.case_id and memory_data.get("long_term"):
            key = f"case_history:{context.case_id}"
            await self.long_term.set(key, memory_data["long_term"])
            memory_ctx.long_term = memory_data["long_term"]
        
        # Store to case memory
        if self.case_memory and context.case_id:
            case_context = {
                "case_id": context.case_id,
                "last_execution": context.request_id,
                "shared_context": context.shared_context,
                "updated_at": datetime.utcnow().isoformat(),
            }
            await self.case_memory.set_case_context(context.case_id, case_context)
            memory_ctx.case_specific = case_context
        
        logger.info("Memory stored", case_id=context.case_id, execution_id=context.request_id)
        return memory_ctx

    async def _update_memory(self, context: ExecutionContext) -> MemoryContext:
        """Update existing memory."""
        # First load existing memory
        memory_ctx = await self._load_memory(context)
        
        # Merge with updates
        updates = context.input_data.get("updates", {})
        
        if "short_term" in updates:
            memory_ctx.short_term.update(updates["short_term"])
            if self.short_term and context.request_id:
                key = f"execution:{context.request_id}"
                await self.short_term.set(key, memory_ctx.short_term, ttl=3600)
        
        if "long_term" in updates:
            memory_ctx.long_term.update(updates["long_term"])
            if self.long_term and context.case_id:
                key = f"case_history:{context.case_id}"
                await self.long_term.set(key, memory_ctx.long_term)
        
        if "case_specific" in updates:
            memory_ctx.case_specific.update(updates["case_specific"])
            if self.case_memory and context.case_id:
                await self.case_memory.set_case_context(context.case_id, memory_ctx.case_specific)
        
        logger.info("Memory updated", case_id=context.case_id, execution_id=context.request_id)
        return memory_ctx

    async def _merge_context(self, context: ExecutionContext) -> MemoryContext:
        """Merge contexts for LLM prompts."""
        memory_ctx = await self._load_memory(context)
        
        # Merge execution context
        merged = {
            "case_id": context.case_id,
            "execution_id": context.request_id,
            "domain": context.domain,
            "workflow": context.workflow,
        }
        
        # Add agent outputs
        if context.agent_outputs:
            merged["agent_outputs"] = {
                agent_id: response.output
                for agent_id, response in context.agent_outputs.items()
            }
        
        # Add shared context
        merged["shared_context"] = context.shared_context
        
        # Add memory context
        merged["memory"] = {
            "short_term": memory_ctx.short_term,
            "long_term": memory_ctx.long_term,
            "conversation": memory_ctx.conversation,
            "case_specific": memory_ctx.case_specific,
        }
        
        memory_ctx.case_specific["merged_context"] = merged
        
        logger.info("Context merged", case_id=context.case_id, execution_id=context.request_id)
        return memory_ctx
