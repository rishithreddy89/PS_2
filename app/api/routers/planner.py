"""
Planner API endpoints.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.planner import planner_service
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/planner", tags=["Planner"])


class ExecuteWorkflowRequest(BaseModel):
    """Request model for workflow execution."""
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow")
    case_id: Optional[str] = Field(None, description="Optional case ID")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    domain: str = Field("general", description="Target domain")
    workflow: str = Field("default", description="Workflow type")


class CreatePlanRequest(BaseModel):
    """Request model for plan creation."""
    task_requirements: Dict[str, Any] = Field(..., description="Task requirements")
    domain: str = Field("general", description="Target domain")


@router.post("/execute", status_code=status.HTTP_200_OK)
async def execute_workflow(request: ExecuteWorkflowRequest) -> Dict[str, Any]:
    """
    Execute a complete workflow with planning and orchestration.

    Args:
        request: Workflow execution request

    Returns:
        Execution result
    """
    try:
        result = await planner_service.execute_workflow(
            input_data=request.input_data,
            case_id=request.case_id,
            user_id=request.user_id,
            domain=request.domain,
            workflow=request.workflow,
        )
        
        return result.model_dump()
        
    except Exception as e:
        logger.error("Workflow execution failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.post("/plan", status_code=status.HTTP_200_OK)
async def create_plan(request: CreatePlanRequest) -> Dict[str, Any]:
    """
    Create execution plan without executing.

    Args:
        request: Plan creation request

    Returns:
        Execution plan
    """
    try:
        plan = await planner_service.create_plan(
            task_requirements=request.task_requirements,
            domain=request.domain,
        )
        
        return {"plan": plan}
        
    except Exception as e:
        logger.error("Plan creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan creation failed: {str(e)}",
        )


@router.get("/executions/{execution_id}", status_code=status.HTTP_200_OK)
async def get_execution_status(execution_id: str) -> Dict[str, Any]:
    """
    Get planner execution status.

    Args:
        execution_id: Execution ID

    Returns:
        Execution status
    """
    try:
        status_result = await planner_service.get_execution_status(execution_id)
        return status_result
        
    except Exception as e:
        logger.error("Failed to get execution status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution status: {str(e)}",
        )


@router.get("/executions", status_code=status.HTTP_200_OK)
async def list_executions(
    case_id: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    List planner execution history.

    Args:
        case_id: Optional case ID filter
        limit: Maximum number of results
        db: Database session

    Returns:
        List of executions
    """
    from sqlalchemy import select, desc
    from app.models.planner_execution import PlannerExecution

    try:
        query = select(PlannerExecution).order_by(desc(PlannerExecution.created_at)).limit(limit)
        
        if case_id:
            query = query.where(PlannerExecution.case_id == case_id)
        
        result = await db.execute(query)
        executions = result.scalars().all()
        
        return {
            "executions": [
                {
                    "id": ex.id,
                    "case_id": ex.case_id,
                    "status": ex.status,
                    "workflow_type": ex.workflow_type if hasattr(ex, 'workflow_type') else "full_analysis",
                    "duration_ms": ex.duration_ms if hasattr(ex, 'duration_ms') else None,
                    "error_message": ex.error_message if hasattr(ex, 'error_message') else None,
                    "execution_plan": ex.execution_plan if hasattr(ex, 'execution_plan') else None,
                    "meta_data": ex.meta_data,
                    "created_at": ex.created_at.isoformat() if ex.created_at else None,
                    "updated_at": ex.updated_at.isoformat() if ex.updated_at else None,
                }
                for ex in executions
            ],
            "total": len(executions),
        }
    except Exception as e:
        logger.error("Failed to list executions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}",
        )
