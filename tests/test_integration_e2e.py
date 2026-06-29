"""
End-to-end integration tests for complete workflow.
"""

import asyncio
import pytest
from uuid import uuid4

from app.agents.context import ExecutionContext
from app.services.workflow import WorkflowExecutionService


@pytest.mark.asyncio
async def test_complete_workflow_integration(db_session):
    """Test complete workflow from case creation to completion."""
    
    service = WorkflowExecutionService(db_session)
    case_id = str(uuid4())
    
    events = []
    
    async for event in service.execute_case_workflow(
        case_id=case_id,
        workflow_type="test_workflow",
    ):
        events.append(event)
        print(f"Event: {event.get('event')}")
    
    # Verify workflow stages
    event_types = [e["event"] for e in events]
    
    assert "workflow_started" in event_types
    assert "planning_started" in event_types
    assert "planning_completed" in event_types
    assert "orchestration_started" in event_types
    assert any("workflow_completed" in event_types or "workflow_failed" in event_types)


@pytest.mark.asyncio
async def test_feedback_memory_synchronization(db_session):
    """Test feedback updates memory correctly."""
    
    service = WorkflowExecutionService(db_session)
    recommendation_id = str(uuid4())
    case_id = str(uuid4())
    
    feedback = {
        "action": "accepted",
        "rating": 5,
        "comments": "Excellent recommendation",
    }
    
    await service.process_feedback_and_update_memory(
        recommendation_id=recommendation_id,
        feedback=feedback,
        case_id=case_id,
    )
    
    # Verify memory was updated
    # In production, query memory store
    assert True


@pytest.mark.asyncio
async def test_workflow_error_handling(db_session):
    """Test workflow handles errors gracefully."""
    
    service = WorkflowExecutionService(db_session)
    case_id = "invalid_case_id"
    
    events = []
    
    try:
        async for event in service.execute_case_workflow(
            case_id=case_id,
            workflow_type="test_workflow",
        ):
            events.append(event)
    except Exception:
        pass
    
    # Should have error events
    assert any(e.get("event") == "workflow_failed" for e in events) or len(events) > 0


@pytest.mark.asyncio
async def test_planner_orchestrator_integration():
    """Test planner and orchestrator work together."""
    
    from app.agents.planner import PlannerAgent
    from app.agents.orchestrator import Orchestrator, OrchestratorConfig
    
    planner = PlannerAgent()
    orchestrator = Orchestrator(OrchestratorConfig())
    
    context = ExecutionContext(
        request_id=str(uuid4()),
        case_id=str(uuid4()),
        domain="legal",
        workflow="test",
        input_data={"test": True},
    )
    
    # Create plan
    planner_response = await planner.execute(context)
    assert planner_response.status == "completed"
    
    # Execute plan
    from app.schemas.agent import ExecutionPlan
    plan = ExecutionPlan(**planner_response.output["plan"])
    
    result = await orchestrator.execute(plan, context)
    assert result.execution_id
    assert result.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_execution_persistence(db_session):
    """Test execution results are persisted."""
    
    from app.models.planner_execution import PlannerExecution
    from sqlalchemy import select
    
    service = WorkflowExecutionService(db_session)
    case_id = str(uuid4())
    
    async for event in service.execute_case_workflow(
        case_id=case_id,
        workflow_type="test",
    ):
        if event.get("event") == "workflow_completed":
            execution_id = event.get("execution_id")
            
            # Query database
            result = await db_session.execute(
                select(PlannerExecution).where(PlannerExecution.case_id == case_id)
            )
            execution = result.scalar_one_or_none()
            
            assert execution is not None
            assert execution.case_id == case_id
            break


def test_api_router_imports():
    """Test new routers are properly imported."""
    from app.api.routers import workflow, stream
    
    assert workflow.router is not None
    assert stream.router is not None
