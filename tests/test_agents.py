"""
Tests for agent framework - Phase 2.
"""

import pytest

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.agents.factory import AgentFactory
from app.agents.orchestrator import Orchestrator, OrchestratorConfig
from app.agents.planner import PlannerAgent
from app.agents.sample_agents import AnalysisAgent, RecommendationAgent
from app.schemas.agent import AgentExecutionStatus


class TestExecutionContext:
    """Test ExecutionContext."""

    def test_context_creation(self):
        """Test context initialization."""
        context = ExecutionContext(
            case_id="test-case",
            user_id="test-user",
            domain="legal",
            workflow="case_analysis",
            input_data={"test": "data"},
        )

        assert context.case_id == "test-case"
        assert context.user_id == "test-user"
        assert context.domain == "legal"
        assert context.workflow == "case_analysis"
        assert context.input_data == {"test": "data"}
        assert context.request_id is not None

    def test_shared_context(self):
        """Test shared context operations."""
        context = ExecutionContext()

        context.set_shared("key1", "value1")
        assert context.get_shared("key1") == "value1"
        assert context.get_shared("missing", "default") == "default"

    def test_error_tracking(self):
        """Test error tracking."""
        context = ExecutionContext()

        assert not context.has_errors()

        context.add_error("agent1", "Test error")
        assert context.has_errors()
        assert len(context.errors) == 1


class TestAgentFactory:
    """Test AgentFactory."""

    def test_agent_discovery(self):
        """Test agent discovery."""
        factory = AgentFactory()

        # Add sample agents
        analysis = AnalysisAgent()
        recommendation = RecommendationAgent()

        factory._agent_instances[analysis.agent_id] = analysis
        factory._agent_instances[recommendation.agent_id] = recommendation

        # Discover by capability
        agents = factory.discover_agents(capabilities=["analysis"])
        assert len(agents) >= 1

        # Discover by domain
        agents = factory.discover_agents(domain="legal")
        assert len(agents) >= 0

    def test_list_agents(self):
        """Test listing all agents."""
        factory = AgentFactory()

        analysis = AnalysisAgent()
        factory._agent_instances[analysis.agent_id] = analysis

        agents = factory.list_agents()
        assert len(agents) >= 1


@pytest.mark.asyncio
class TestPlannerAgent:
    """Test PlannerAgent."""

    async def test_planner_execution(self):
        """Test planner creates valid execution plan."""
        planner = PlannerAgent()

        context = ExecutionContext(
            domain="general",
            input_data={
                "query": "Test query",
                "analyze_evidence": True,
            },
        )

        response = await planner.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "plan" in response.output
        assert response.duration_ms is not None

    async def test_planner_validation(self):
        """Test planner validation."""
        planner = PlannerAgent()

        context = ExecutionContext(input_data={"test": "data"})
        assert await planner.validate(context) is True

        context_no_data = ExecutionContext()
        assert await planner.validate(context_no_data) is False


@pytest.mark.asyncio
class TestSampleAgents:
    """Test sample agents."""

    async def test_analysis_agent(self):
        """Test analysis agent execution."""
        agent = AnalysisAgent()

        context = ExecutionContext(input_data={"data": "test"})

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "analysis_result" in response.output
        assert response.duration_ms is not None

    async def test_recommendation_agent(self):
        """Test recommendation agent execution."""
        agent = RecommendationAgent()

        context = ExecutionContext(input_data={"data": "test"})

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "recommendations" in response.output
        assert len(response.output["recommendations"]) > 0


@pytest.mark.asyncio
class TestOrchestrator:
    """Test Orchestrator."""

    async def test_orchestrator_execution(self):
        """Test orchestrator executes workflow."""
        from app.agents.init import initialize_agents

        # Initialize agents
        initialize_agents()

        planner = PlannerAgent()
        context = ExecutionContext(
            domain="general",
            input_data={"query": "test", "analyze": True},
        )

        # Create plan
        planner_response = await planner.execute(context)
        assert planner_response.status == AgentExecutionStatus.COMPLETED

        # Extract plan
        from app.schemas.agent import ExecutionPlan

        plan_data = planner_response.output.get("plan")
        plan = ExecutionPlan(**plan_data)

        # Execute with orchestrator
        orchestrator = Orchestrator(OrchestratorConfig())
        result = await orchestrator.execute(plan, context)

        assert result.execution_id is not None
        assert result.request_id == context.request_id
        assert result.total_duration_ms is not None


@pytest.mark.asyncio
class TestPlannerService:
    """Test PlannerService."""

    async def test_workflow_execution(self):
        """Test complete workflow execution."""
        from app.agents.init import initialize_agents
        from app.services.planner import planner_service

        # Initialize agents
        initialize_agents()

        result = await planner_service.execute_workflow(
            input_data={"query": "test query", "analyze": True},
            domain="general",
            workflow="test_workflow",
        )

        assert result.execution_id is not None
        assert result.status in [AgentExecutionStatus.COMPLETED, AgentExecutionStatus.FAILED]
        assert result.total_duration_ms is not None

    async def test_create_plan(self):
        """Test plan creation."""
        from app.agents.init import initialize_agents
        from app.services.planner import planner_service

        # Initialize agents
        initialize_agents()

        plan = await planner_service.create_plan(
            task_requirements={"query": "test", "analyze": True},
            domain="general",
        )

        assert plan is not None
        assert "plan_id" in plan
        assert "workflow_steps" in plan
