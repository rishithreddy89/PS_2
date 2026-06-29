"""
Analysis execution API endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import AsyncGenerator

from app.database.session import get_db
from app.services.workflow import WorkflowExecutionService
from app.repositories.case_document import get_case_document_repository
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])


async def event_stream(case_id: str, db: AsyncSession) -> AsyncGenerator[str, None]:
    """Server-sent events stream for analysis progress.
    
    GUARANTEE: This generator will ALWAYS emit a terminal 'completed' event
    before closing, even if the workflow crashes mid-stream.
    """
    workflow_service = WorkflowExecutionService(db)
    terminal_sent = False
    
    logger.info("SSE stream opened", case_id=case_id)
    
    try:
        async for event in workflow_service.execute_case_workflow(
            case_id=case_id,
            workflow_type="full_analysis"
        ):
            event_type = event.get('event', 'unknown')
            
            if event_type == 'planning_started':
                logger.info("Planner started", case_id=case_id)
            elif event_type == 'orchestration_started':
                logger.info("Orchestration started", case_id=case_id)
            elif event_type == 'agent_completed':
                logger.info("Agent completed", agent=event.get('agent_name'), case_id=case_id)
            elif event_type == 'workflow_completed':
                logger.info("Analysis completed", case_id=case_id)
            elif event_type == 'workflow_failed':
                logger.error("Analysis failed", case_id=case_id, error=event.get('error'))
            elif event_type == 'completed':
                terminal_sent = True
                logger.info("Terminal completed event", case_id=case_id)
            
            safe_event = jsonable_encoder(event)
            yield f"data: {json.dumps(safe_event)}\n\n"
    except Exception as e:
        logger.error("Stream error", error=str(e), case_id=case_id)
        error_event = jsonable_encoder({'event': 'workflow_failed', 'error': str(e)})
        yield f"data: {json.dumps(error_event)}\n\n"
    finally:
        # ALWAYS send a terminal event so the frontend can stop loading
        if not terminal_sent:
            logger.info("Sending guaranteed terminal event", case_id=case_id)
            terminal = jsonable_encoder({'event': 'completed', 'status': 'failed', 'error': 'Stream ended unexpectedly'})
            yield f"data: {json.dumps(terminal)}\n\n"


@router.post("/cases/{case_id}/analyze")
async def start_analysis(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Start case analysis (non-blocking)."""
    # Validate case exists
    from app.models.case import Case
    from sqlalchemy import select
    
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Check for indexed documents
    doc_repo = get_case_document_repository(db)
    docs = await doc_repo.get_indexed_documents(case_id)
    
    if not docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexed documents found for this case."
        )
    
    # Check if analysis is already running
    from app.models.planner_execution import PlannerExecution
    from sqlalchemy import desc
    
    recent_result = await db.execute(
        select(PlannerExecution)
        .where(PlannerExecution.case_id == case_id)
        .order_by(desc(PlannerExecution.created_at))
        .limit(1)
    )
    recent = recent_result.scalar_one_or_none()
    
    if recent and recent.status in ['pending', 'running']:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis is already running for this case."
        )
    
    logger.info("Analysis started", case_id=case_id, documents=len(docs))
    
    return {
        "case_id": case_id,
        "status": "started",
        "message": "Analysis workflow started",
        "stream_url": f"/api/v1/analysis/cases/{case_id}/stream"
    }


@router.get("/cases/{case_id}/stream")
async def stream_analysis(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream case analysis progress (SSE)."""
    return StreamingResponse(
        event_stream(case_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/cases/{case_id}/analysis/status")
async def get_analysis_status(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get current analysis status."""
    # Return latest execution status
    from app.models.planner_execution import PlannerExecution
    from sqlalchemy import select, desc
    
    result = await db.execute(
        select(PlannerExecution)
        .where(PlannerExecution.case_id == case_id)
        .order_by(desc(PlannerExecution.created_at))
        .limit(1)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        return {"status": "not_started"}
    
    return {
        "execution_id": execution.id,
        "status": execution.status,
        "duration_ms": execution.duration_ms,
        "error": execution.error_message,
        "created_at": execution.created_at.isoformat(),
    }
