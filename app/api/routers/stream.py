"""
Server-Sent Events (SSE) endpoints for real-time streaming.
"""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.workflow import WorkflowExecutionService
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/stream", tags=["Streaming"])


async def event_stream(generator: AsyncGenerator) -> AsyncGenerator[str, None]:
    """
    Format generator output as SSE events.
    
    Args:
        generator: Async generator yielding events
        
    Yields:
        SSE formatted strings
    """
    try:
        async for event in generator:
            event_type = event.get("event", "message")
            safe_event = jsonable_encoder(event)
            data = json.dumps(safe_event)
            yield f"event: {event_type}\ndata: {data}\n\n"
            await asyncio.sleep(0.01)  # Small delay for streaming
    except Exception as e:
        error_event = jsonable_encoder({"event": "error", "error": str(e)})
        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"


@router.get("/workflow/{case_id}")
async def stream_workflow_execution(
    case_id: str,
    workflow_type: str = "full_analysis",
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Stream workflow execution updates in real-time.
    
    Args:
        case_id: Case ID to execute workflow for
        workflow_type: Type of workflow
        db: Database session
        
    Returns:
        SSE stream of execution events
    """
    logger.info("Starting workflow stream", case_id=case_id)
    
    workflow_service = WorkflowExecutionService(db)
    
    generator = workflow_service.execute_case_workflow(
        case_id=case_id,
        workflow_type=workflow_type,
    )
    
    return StreamingResponse(
        event_stream(generator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/executions/{execution_id}")
async def stream_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Stream execution status updates.
    
    Args:
        execution_id: Execution ID
        db: Database session
        
    Returns:
        SSE stream of status updates
    """
    
    async def status_generator() -> AsyncGenerator[dict, None]:
        """Generate status updates."""
        from app.models.planner_execution import PlannerExecution
        from sqlalchemy import select
        
        for _ in range(30):  # Poll for 30 seconds
            result = await db.execute(
                select(PlannerExecution).where(PlannerExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            
            if execution:
                # Get execution_trace from meta_data
                execution_trace = execution.meta_data.get("execution_trace", []) if execution.meta_data else []
                
                yield {
                    "event": "status_update",
                    "execution_id": execution_id,
                    "status": execution.status,
                    "progress": len(execution_trace),
                }
                
                if execution.status in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_stream(status_generator()),
        media_type="text/event-stream",
    )
