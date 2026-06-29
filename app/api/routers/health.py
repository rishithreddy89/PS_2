"""
Health check endpoints for monitoring.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import check_db_connection, get_db

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "LexMind AI",
        "version": "1.0.0",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Readiness check endpoint with database connection test.

    Args:
        db: Database session

    Returns:
        Readiness status
    """
    db_healthy = await check_db_connection()

    if not db_healthy:
        return {
            "status": "not_ready",
            "database": "unhealthy",
        }

    return {
        "status": "ready",
        "database": "healthy",
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict:
    """
    Liveness check endpoint for Kubernetes.

    Returns:
        Liveness status
    """
    return {
        "status": "alive",
    }
