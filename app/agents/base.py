"""
Base agent interface for all agents in the platform.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.schemas.agent import AgentExecutionStatus, AgentResponse


class BaseAgent(ABC):
    """
    Abstract base agent that all agents must inherit from.
    
    Provides standard interface for agent lifecycle and capabilities.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        supported_domains: Optional[List[str]] = None,
        priority: int = 0,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.version = version
        self.supported_domains = supported_domains or ["*"]
        self.priority = priority

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        pass

    @property
    @abstractmethod
    def required_tools(self) -> List[str]:
        """Return list of required tools."""
        pass

    @property
    @abstractmethod
    def required_memory(self) -> List[str]:
        """Return list of required memory providers."""
        pass

    @abstractmethod
    async def execute(self, context: "ExecutionContext") -> AgentResponse:
        """
        Execute agent logic.
        
        Args:
            context: Execution context with shared data
            
        Returns:
            AgentResponse with execution result
        """
        pass

    @abstractmethod
    async def validate(self, context: "ExecutionContext") -> bool:
        """
        Validate if agent can execute with given context.
        
        Args:
            context: Execution context
            
        Returns:
            True if validation passes
        """
        pass

    def can_execute(self, required_capabilities: List[str]) -> bool:
        """
        Check if agent can handle required capabilities.
        
        Args:
            required_capabilities: List of required capabilities
            
        Returns:
            True if agent supports all required capabilities
        """
        return all(cap in self.capabilities for cap in required_capabilities)

    async def health(self) -> Dict[str, Any]:
        """
        Health check for agent.
        
        Returns:
            Health status dictionary
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": "healthy",
            "version": self.version,
        }

    def metadata(self) -> Dict[str, Any]:
        """
        Get agent metadata.
        
        Returns:
            Agent metadata dictionary
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "supported_domains": self.supported_domains,
            "required_tools": self.required_tools,
            "required_memory": self.required_memory,
            "priority": self.priority,
        }
