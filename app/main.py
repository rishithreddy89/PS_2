"""
LexMind AI - Enterprise Agentic Decision Intelligence Platform

Main FastAPI application entry point.
"""

import numpy as np
np.float_ = np.float64
np.int_ = np.int64

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.middleware.cors import setup_cors
from app.api.middleware.logging import RequestLoggingMiddleware
from app.api.routers import agents, cases, health, memory, planner, recommendations, tools, nba, workflow, stream, metrics, documents, analysis, review, search
from app.api.routers import settings as settings_router
from app.core.config import settings
from app.database.session import check_db_connection, close_db, init_db
from app.utils.logging.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    logger.info("Starting LexMind AI application", environment=settings.environment)

    try:
        await init_db()
        logger.info("Database initialized successfully")

        db_healthy = await check_db_connection()
        if db_healthy:
            logger.info("Database connection verified")
        else:
            logger.warning("Database connection check failed")

        # Check required dependencies
        required_deps = [
            ('python-docx', 'from docx import Document'),
            ('PyPDF2', 'import PyPDF2'),
            ('sentence-transformers', 'import sentence_transformers'),
            ('chromadb', 'import chromadb'),
        ]
        
        for package_name, import_stmt in required_deps:
            try:
                exec(import_stmt)
                logger.info(f"✓ {package_name} loaded")
            except ImportError:
                logger.error(f"✗ {package_name} NOT installed")
                raise ImportError(f"{package_name} is required. Install with: pip install {package_name}")
        


        # Initialize embedding service (loads model once)
        from app.knowledge.local_embedding import get_local_embedding_service
        embedding_svc = get_local_embedding_service()
        logger.info("Local embedding service initialized", model=embedding_svc.model_name)

        # Initialize agents
        from app.agents.init import initialize_agents
        initialize_agents()
        logger.info("Agents initialized successfully")

        logger.info("Application startup complete")

    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        raise

    yield

    logger.info("Shutting down LexMind AI application")
    
    # Shutdown agents
    from app.agents.init import shutdown_agents
    shutdown_agents()
    
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise Agentic Decision Intelligence Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

setup_cors(app)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(cases.router, prefix=settings.api_v1_prefix)
app.include_router(recommendations.router, prefix=settings.api_v1_prefix)
app.include_router(agents.router, prefix=settings.api_v1_prefix)
app.include_router(tools.router, prefix=settings.api_v1_prefix)
app.include_router(planner.router, prefix=settings.api_v1_prefix)
app.include_router(memory.router, prefix=settings.api_v1_prefix)
app.include_router(workflow.router, prefix=settings.api_v1_prefix)
app.include_router(stream.router, prefix=settings.api_v1_prefix)
app.include_router(metrics.router, prefix=settings.api_v1_prefix)
app.include_router(documents.router, prefix=settings.api_v1_prefix)
app.include_router(analysis.router, prefix=settings.api_v1_prefix)
app.include_router(review.router, prefix=settings.api_v1_prefix)
app.include_router(settings_router.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(nba.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors.

    Args:
        request: HTTP request
        exc: Validation error exception

    Returns:
        JSON error response
    """
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=exc.errors(),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all uncaught exceptions.

    Args:
        request: HTTP request
        exc: Exception

    Returns:
        JSON error response
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "message": "Welcome to LexMind AI",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }
