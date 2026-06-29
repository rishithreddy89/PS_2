"""
Agent initialization and registration.
"""

from app.agents.factory import agent_factory
from app.agents.planner import PlannerAgent
from app.agents.sample_agents import (
    AnalysisAgent,
    DocumentParsingAgent,
)
from app.agents.recommendation_agent import RecommendationAgent
# Import specialized agents
from app.agents.evidence_agent import EvidenceAgent
from app.agents.ingest_agent import IngestAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAgent
from app.agents.timeline_agent import TimelineAgent
# Import Phase 5 agents
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.reflection_agent import ReflectionAgent
from app.agents.explainability_agent import ExplainabilityAgent
from app.agents.human_review_agent import HumanReviewAgent
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


from app.agents.legal_issue_agent import LegalIssueAgent

def initialize_agents() -> None:
    """
    Initialize and register all agents.
    
    This should be called on application startup.
    """
    logger.info("Initializing agents")
    
    # Create and register planner
    planner = PlannerAgent()
    agent_factory._agent_instances[planner.agent_id] = planner
    
    # Create and register sample agents
    agents = [
        DocumentParsingAgent(),
        AnalysisAgent(),
        RecommendationAgent(),
    ]
    
    # Create and register specialized agents (Phase 3)
    specialized_agents = [
        IngestAgent(),
        RetrievalAgent(),
        EvidenceAgent(),
        TimelineAgent(),
        LegalIssueAgent(),
        RiskAgent(),
        MemoryAgent(),
    ]
    
    # Create and register Phase 5 Decision Intelligence agents
    phase5_agents = [
        EvaluationAgent(),
        ReflectionAgent(),
        ExplainabilityAgent(),
        HumanReviewAgent(),
    ]
    
    # Combine all agents
    all_agents = agents + specialized_agents + phase5_agents
    
    for agent in all_agents:
        agent_factory._agent_instances[agent.agent_id] = agent
        
        # Register in agent registry
        from app.core.enums import AgentStatus
        from app.registry.agent_registry import AgentMetadata, agent_registry
        
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
        "Agents initialized",
        total_agents=len(agent_factory._agent_instances),
        specialized_agents=len(specialized_agents),
        phase5_agents=len(phase5_agents),
    )


def shutdown_agents() -> None:
    """
    Cleanup agents on application shutdown.
    """
    logger.info("Shutting down agents")
    agent_factory._agent_instances.clear()
