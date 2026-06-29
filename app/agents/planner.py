"""
Planner agent for dynamic orchestration.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.registry.agent_registry import agent_registry
from app.schemas.agent import (
    AgentExecutionStatus,
    AgentResponse,
    ExecutionPlan,
    PlannerDecision,
    WorkflowStep,
)
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    """
    Planner agent for dynamic agent orchestration.
    
    Responsibilities:
    - Analyze incoming requests
    - Determine required capabilities
    - Discover available agents
    - Build execution plan
    - Estimate complexity and duration
    """

    def __init__(self):
        super().__init__(
            agent_id="planner",
            name="Planner Agent",
            description="Dynamic agent orchestration and planning",
            version="1.0.0",
            supported_domains=["*"],
            priority=100,
        )

    @property
    def capabilities(self) -> List[str]:
        return ["planning", "orchestration", "analysis"]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """
        Create execution plan based on context.
        
        Args:
            context: Execution context
            
        Returns:
            AgentResponse with execution plan
        """
        start_time = datetime.utcnow()
        
        try:
            # Analyze request
            required_capabilities = self._analyze_request(context)
            
            # Discover agents
            available_agents = self._discover_agents(required_capabilities, context.domain)
            
            if not available_agents:
                return AgentResponse(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    status=AgentExecutionStatus.FAILED,
                    error="No agents available for required capabilities",
                    duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                )
            
            # Build execution plan
            plan = self._build_plan(required_capabilities, available_agents, context)
            
            # Store in context
            context.planner_state["execution_plan"] = plan.model_dump()
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Execution plan created",
                plan_id=plan.plan_id,
                agent_count=len(available_agents),
                capabilities=required_capabilities,
            )
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={"plan": plan.model_dump()},
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Planner execution failed", error=str(e))
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.FAILED,
                error=str(e),
                duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            )

    async def validate(self, context: ExecutionContext) -> bool:
        """Validate planner can execute."""
        return context.input_data is not None

    def _analyze_request(self, context: ExecutionContext) -> List[str]:
        """
        Analyze request to determine required capabilities.
        
        Args:
            context: Execution context
            
        Returns:
            List of required capabilities
        """
        capabilities = []
        input_data = context.input_data
        
        # Analyze based on input data
        if input_data.get("documents"):
            capabilities.append("document_parsing")
        
        if input_data.get("query") or input_data.get("search"):
            capabilities.append("retrieval")
        
        if input_data.get("analyze_evidence"):
            capabilities.append("evidence_analysis")
        
        if input_data.get("risk_assessment"):
            capabilities.append("risk_analysis")
        
        if input_data.get("generate_recommendation"):
            capabilities.append("recommendation")
        
        # Default capabilities
        if not capabilities:
            capabilities = ["analysis", "recommendation"]
        
        return capabilities

    def _discover_agents(
        self, capabilities: List[str], domain: str
    ) -> List[Dict[str, Any]]:
        """
        Discover agents that match required capabilities.
        
        Args:
            capabilities: Required capabilities
            domain: Target domain
            
        Returns:
            List of matching agent metadata
        """
        discovered = []
        
        # Get all active agents
        all_agents = agent_registry.list_agents()
        
        for agent_meta in all_agents:
            # Skip planner itself
            if agent_meta.agent_id == self.agent_id:
                continue
            
            # Check domain support
            if domain not in agent_meta.metadata.get("supported_domains", ["*"]) and \
               "*" not in agent_meta.metadata.get("supported_domains", ["*"]):
                continue
            
            # Check capabilities
            agent_caps = agent_meta.metadata.get("capabilities", [])
            if any(cap in agent_caps for cap in capabilities):
                discovered.append(agent_meta.to_dict())
        
        # Sort by priority
        discovered.sort(key=lambda x: x.get("metadata", {}).get("priority", 0), reverse=True)
        
        return discovered

    def _build_plan(
        self,
        capabilities: List[str],
        agents: List[Dict[str, Any]],
        context: ExecutionContext,
    ) -> ExecutionPlan:
        """
        Build execution plan with workflow steps.
        
        Args:
            capabilities: Required capabilities
            agents: Available agents
            context: Execution context
            
        Returns:
            ExecutionPlan
        """
        plan_id = str(uuid.uuid4())
        steps = []
        selected_agents = []
        execution_order = []
        
        # Create workflow steps
        for i, agent_meta in enumerate(agents):
            agent_id = agent_meta["agent_id"]
            agent_caps = agent_meta.get("metadata", {}).get("capabilities", [])
            
            step = WorkflowStep(
                step_id=f"step_{i+1}",
                agent_id=agent_id,
                agent_name=agent_meta["agent_name"],
                required_capabilities=[cap for cap in capabilities if cap in agent_caps],
                dependencies=[],
                priority=agent_meta.get("metadata", {}).get("priority", 0),
                can_skip=False,
            )
            steps.append(step)
            selected_agents.append(agent_id)
            execution_order.append(agent_id)
        
        # Build decision
        decision = PlannerDecision(
            required_capabilities=capabilities,
            selected_agents=selected_agents,
            execution_order=execution_order,
            reasoning=f"Selected {len(agents)} agents based on required capabilities: {', '.join(capabilities)}",
            estimated_complexity="medium",
            estimated_duration_ms=len(agents) * 1000.0,
            confidence=0.85,
        )
        
        return ExecutionPlan(
            plan_id=plan_id,
            workflow_steps=steps,
            decision=decision,
            metadata={
                "domain": context.domain,
                "workflow": context.workflow,
                "case_id": context.case_id,
            },
        )
