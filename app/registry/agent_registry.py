"""
Agent Registry for dynamic agent discovery and management.

Provides centralized registry for all agents in the platform.
"""

from typing import Any, Dict, List, Optional

from app.core.enums import AgentStatus
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class AgentMetadata:
    """Agent metadata structure."""

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        capabilities: List[str],
        description: str,
        version: str = "1.0.0",
        status: AgentStatus = AgentStatus.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize agent metadata.

        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            agent_type: Agent type classification
            capabilities: List of agent capabilities
            description: Agent description
            version: Agent version
            status: Agent status
            metadata: Additional metadata
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.description = description
        self.version = version
        self.status = status
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "description": self.description,
            "version": self.version,
            "status": self.status,
            "metadata": self.metadata,
        }


class AgentRegistry:
    """
    Agent Registry for managing agent lifecycle.
    
    Provides:
    - Agent registration
    - Agent discovery
    - Agent metadata management
    - Dynamic agent loading
    """

    def __init__(self) -> None:
        """Initialize agent registry."""
        self._agents: Dict[str, AgentMetadata] = {}
        logger.info("Agent Registry initialized")

    def register_agent(self, metadata: AgentMetadata) -> bool:
        """
        Register an agent in the registry.

        Args:
            metadata: Agent metadata

        Returns:
            True if registered successfully
        """
        if metadata.agent_id in self._agents:
            logger.warning(
                "Agent already registered, updating",
                agent_id=metadata.agent_id,
            )

        self._agents[metadata.agent_id] = metadata
        logger.info(
            "Agent registered",
            agent_id=metadata.agent_id,
            agent_name=metadata.agent_name,
            capabilities=metadata.capabilities,
        )
        return True

    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry.

        Args:
            agent_id: Agent ID

        Returns:
            True if removed successfully
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info("Agent removed", agent_id=agent_id)
            return True
        
        logger.warning("Agent not found for removal", agent_id=agent_id)
        return False

    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get agent metadata by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent metadata or None
        """
        return self._agents.get(agent_id)

    def discover_agents(
        self, capabilities: Optional[List[str]] = None, agent_type: Optional[str] = None
    ) -> List[AgentMetadata]:
        """
        Discover agents by capabilities or type.

        Args:
            capabilities: Required capabilities
            agent_type: Agent type filter

        Returns:
            List of matching agents
        """
        agents = list(self._agents.values())

        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]

        if capabilities:
            agents = [
                a for a in agents
                if all(cap in a.capabilities for cap in capabilities)
            ]

        agents = [a for a in agents if a.status == AgentStatus.ACTIVE]

        logger.info(
            "Agents discovered",
            count=len(agents),
            capabilities=capabilities,
            agent_type=agent_type,
        )
        return agents

    def list_agents(self, status: Optional[AgentStatus] = None) -> List[AgentMetadata]:
        """
        List all agents with optional status filter.

        Args:
            status: Agent status filter

        Returns:
            List of agents
        """
        agents = list(self._agents.values())

        if status:
            agents = [a for a in agents if a.status == status]

        return agents

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """
        Update agent status.

        Args:
            agent_id: Agent ID
            status: New status

        Returns:
            True if updated successfully
        """
        if agent_id in self._agents:
            self._agents[agent_id].status = status
            logger.info("Agent status updated", agent_id=agent_id, status=status)
            return True

        logger.warning("Agent not found for status update", agent_id=agent_id)
        return False

    def get_agent_count(self) -> int:
        """
        Get total number of registered agents.

        Returns:
            Agent count
        """
        return len(self._agents)

    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        logger.info("Agent registry cleared")


agent_registry = AgentRegistry()
