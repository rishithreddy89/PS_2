"""
Metrics and observability API endpoints.
"""

from typing import Any, Dict

from fastapi import APIRouter, status

from app.utils.metrics import metrics_collector, workflow_metrics
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/system", status_code=status.HTTP_200_OK)
async def get_system_metrics() -> Dict[str, Any]:
    """
    Get system-level metrics.
    
    Returns:
        System metrics including counters, gauges, and stats
    """
    return metrics_collector.get_all_metrics()


@router.get("/workflow", status_code=status.HTTP_200_OK)
async def get_workflow_metrics() -> Dict[str, Any]:
    """
    Get workflow execution metrics.
    
    Returns:
        Workflow statistics including success rates and durations
    """
    return {
        "workflow_stats": workflow_metrics.get_workflow_stats(),
        "agent_stats": workflow_metrics.get_agent_stats(),
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def get_health_metrics() -> Dict[str, Any]:
    """
    Get system health metrics.
    
    Returns:
        Health status and key metrics
    """
    workflow_stats = workflow_metrics.get_workflow_stats()
    
    return {
        "status": "healthy",
        "workflow_health": {
            "total_executions": workflow_stats.get("total_executions", 0),
            "success_rate": workflow_stats.get("success_rate", 0),
            "avg_duration_ms": workflow_stats.get("avg_duration_ms", 0),
        },
        "timestamp": "2024-01-01T00:00:00Z",
    }


@router.post("/reset", status_code=status.HTTP_200_OK)
async def reset_metrics() -> Dict[str, str]:
    """
    Reset all metrics (admin only in production).
    
    Returns:
        Success message
    """
    metrics_collector.reset()
    logger.info("Metrics reset")
    
    return {"message": "Metrics reset successfully"}
