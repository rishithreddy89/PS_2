"""
Agent Registry API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from app.registry.agent_registry import agent_registry, AgentMetadata
from app.core.enums import AgentStatus

router = APIRouter(prefix="/agents", tags=["Agent Registry"])


@router.get("", status_code=status.HTTP_200_OK)
async def list_agents(agent_status: Optional[str] = None) -> dict:
    """
    List all registered agents.

    Args:
        agent_status: Optional status filter

    Returns:
        List of agents
    """
    status_filter = AgentStatus(agent_status) if agent_status else None
    agents = agent_registry.list_agents(status=status_filter)

    return {
        "agents": [agent.to_dict() for agent in agents],
        "count": len(agents),
    }


@router.get("/discover", status_code=status.HTTP_200_OK)
async def discover_agents(
    capabilities: Optional[List[str]] = None,
    agent_type: Optional[str] = None,
) -> dict:
    """
    Discover agents by capabilities or type.

    Args:
        capabilities: Required capabilities
        agent_type: Agent type filter

    Returns:
        Matching agents
    """
    agents = agent_registry.discover_agents(
        capabilities=capabilities,
        agent_type=agent_type,
    )

    return {
        "agents": [agent.to_dict() for agent in agents],
        "count": len(agents),
    }


@router.get("/{agent_id}", status_code=status.HTTP_200_OK)
async def get_agent(agent_id: str) -> dict:
    """
    Get agent metadata by ID.

    Args:
        agent_id: Agent ID

    Returns:
        Agent metadata

    Raises:
        HTTPException: If agent not found
    """
    agent = agent_registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )

    return agent.to_dict()


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_agent_stats() -> dict:
    """
    Get agent registry statistics.

    Returns:
        Registry statistics
    """
    return {
        "total_agents": agent_registry.get_agent_count(),
        "active_agents": len(agent_registry.list_agents(status=AgentStatus.ACTIVE)),
        "inactive_agents": len(agent_registry.list_agents(status=AgentStatus.INACTIVE)),
    }
