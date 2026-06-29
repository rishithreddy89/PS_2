"""
Integrated workflow endpoints for end-to-end execution.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.workflow import WorkflowExecutionService
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class ExecuteCaseWorkflowRequest(BaseModel):
    """Request to execute case workflow."""
    case_id: str = Field(..., description="Case ID")
    documents: Optional[List[Dict[str, Any]]] = Field(None, description="Documents to ingest")
    workflow_type: str = Field("full_analysis", description="Workflow type")
    user_id: Optional[str] = Field(None, description="User ID")


class WorkflowStatusResponse(BaseModel):
    """Workflow execution status."""
    execution_id: str
    case_id: str
    status: str
    current_step: Optional[str] = None
    progress: int
    total_steps: int
    error: Optional[str] = None


@router.post("/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_case_workflow(
    request: ExecuteCaseWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Execute complete case workflow.
    
    Triggers:
    - Document ingestion
    - Planning
    - Agent orchestration
    - Memory updates
    
    Args:
        request: Workflow execution request
        db: Database session
        
    Returns:
        Execution metadata with streaming URL
    """
    try:
        workflow_service = WorkflowExecutionService(db)
        
        execution_id = await workflow_service.trigger_workflow_on_case_creation(
            case_id=request.case_id,
            case_data={
                "workflow_type": request.workflow_type,
                "user_id": request.user_id,
            }
        )
        
        return {
            "execution_id": execution_id,
            "case_id": request.case_id,
            "status": "started",
            "stream_url": f"/api/v1/stream/workflow/{request.case_id}",
            "message": "Workflow execution started. Use stream_url for real-time updates.",
        }
        
    except Exception as e:
        logger.error("Failed to start workflow", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    """
    Get workflow execution status.
    
    Args:
        execution_id: Execution ID
        db: Database session
        
    Returns:
        Execution status
    """
    from app.models.planner_execution import PlannerExecution
    from sqlalchemy import select
    
    result = await db.execute(
        select(PlannerExecution).where(PlannerExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {execution_id}",
        )
    
    # Get trace count from meta_data
    execution_trace = execution.meta_data.get("execution_trace", []) if execution.meta_data else []
    trace_count = len(execution_trace)
    
    # Get plan steps from execution_plan
    plan_steps = len(execution.execution_plan.get("workflow_steps", [])) if execution.execution_plan else 0
    
    return WorkflowStatusResponse(
        execution_id=execution_id,
        case_id=execution.case_id,
        status=execution.status,
        progress=trace_count,
        total_steps=plan_steps,
        error=execution.error_message,
    )


@router.post("/feedback/{recommendation_id}")
async def process_feedback(
    recommendation_id: str,
    feedback: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Process human review feedback and update memory.
    
    Args:
        recommendation_id: Recommendation ID
        feedback: Feedback data (action, rating, comments)
        db: Database session
        
    Returns:
        Success confirmation
    """
    try:
        # Get recommendation to find case_id
        from app.models.recommendation import Recommendation
        from sqlalchemy import select
        
        result = await db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )
        recommendation = result.scalar_one_or_none()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )
        
        workflow_service = WorkflowExecutionService(db)
        await workflow_service.process_feedback_and_update_memory(
            recommendation_id=recommendation_id,
            feedback=feedback,
            case_id=recommendation.case_id,
        )
        
        return {
            "success": True,
            "message": "Feedback processed and memory updated",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process feedback", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}",
        )
