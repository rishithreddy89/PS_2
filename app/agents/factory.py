"""
Agent factory for agent instantiation and registration.
"""

from typing import Dict, List, Optional, Type

from app.agents.base import BaseAgent
from app.core.enums import AgentStatus
from app.registry.agent_registry import AgentMetadata, agent_registry
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory for creating and managing agent instances.
    
    Provides:
    - Agent registration
    - Agent instantiation
    - Dependency injection
    - Agent discovery
    """

    def __init__(self):
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}

    def register_agent_class(self, agent_class: Type[BaseAgent]) -> None:
        """
        Register agent class for instantiation.
        
        Args:
            agent_class: Agent class to register
        """
        # Create temporary instance to get metadata
        temp_instance = agent_class(
            agent_id=f"temp_{agent_class.__name__}",
            name=agent_class.__name__,
            description="Temporary instance for metadata extraction",
        )
        
        agent_id = temp_instance.agent_id
        self._agent_classes[agent_id] = agent_class
        
        logger.info(
            "Agent class registered",
            agent_id=agent_id,
            agent_name=temp_instance.name,
        )

    def create_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        **kwargs
    ) -> Optional[BaseAgent]:
        """
        Create agent instance.
        
        Args:
            agent_id: Agent ID
            name: Agent name
            description: Agent description
            version: Agent version
            **kwargs: Additional agent parameters
            
        Returns:
            Agent instance or None
        """
        if agent_id not in self._agent_classes:
            logger.error("Agent class not registered", agent_id=agent_id)
            return None

        agent_class = self._agent_classes[agent_id]
        agent = agent_class(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            **kwargs
        )

        self._agent_instances[agent_id] = agent

        # Register in agent registry
        metadata = AgentMetadata(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            agent_type=agent.__class__.__name__,
            capabilities=agent.capabilities,
            description=agent.description,
            version=agent.version,
            status=AgentStatus.ACTIVE,
            metadata=agent.metadata(),
        )
        agent_registry.register_agent(metadata)

        logger.info(
            "Agent instance created",
            agent_id=agent_id,
            agent_name=name,
        )

        return agent

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent instance by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent instance or None
        """
        return self._agent_instances.get(agent_id)

    def discover_agents(
        self,
        capabilities: Optional[List[str]] = None,
        domain: Optional[str] = None,
    ) -> List[BaseAgent]:
        """
        Discover agents by capabilities and domain.
        
        Args:
            capabilities: Required capabilities
            domain: Target domain
            
        Returns:
            List of matching agents
        """
        agents = list(self._agent_instances.values())

        if capabilities:
            agents = [a for a in agents if a.can_execute(capabilities)]

        if domain:
            agents = [
                a for a in agents
                if domain in a.supported_domains or "*" in a.supported_domains
            ]

        # Sort by priority
        agents.sort(key=lambda x: x.priority, reverse=True)

        return agents

    def list_agents(self) -> List[BaseAgent]:
        """
        List all registered agent instances.
        
        Returns:
            List of all agents
        """
        return list(self._agent_instances.values())

    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove agent instance.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if removed successfully
        """
        if agent_id in self._agent_instances:
            del self._agent_instances[agent_id]
            agent_registry.remove_agent(agent_id)
            logger.info("Agent instance removed", agent_id=agent_id)
            return True
        
        return False


# Global agent factory instance
agent_factory = AgentFactory()
