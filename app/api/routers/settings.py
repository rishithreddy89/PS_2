"""
Settings API endpoints.

Manages application configuration including LLM settings,
API keys, and system preferences.
"""

import os
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.database.session import check_db_connection
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsResponse(BaseModel):
    """Settings response model with sensitive fields masked."""
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    temperature: float = 0.2
    max_tokens: int = 2000
    embedding_model: str = ""
    top_k_results: int = 5
    llm_provider: str = ""
    environment: str = ""
    debug: bool = False
    database_connected: bool = False


class SettingsUpdate(BaseModel):
    """Settings update model."""
    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    embedding_model: Optional[str] = None
    top_k_results: Optional[int] = None
    llm_provider: Optional[str] = None


# Runtime overrides (in-memory, lost on restart unless saved to .env)
_runtime_overrides: dict = {}


def _mask_key(key: str) -> str:
    """Mask an API key, showing only last 4 characters."""
    if not key or len(key) < 8:
        return "****" if key else ""
    return "****" + key[-4:]


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """
    Get current application settings.
    API keys are masked for security.
    """
    db_connected = await check_db_connection()

    return SettingsResponse(
        openrouter_api_key=_mask_key(_runtime_overrides.get("openrouter_api_key", settings.openrouter_api_key)),
        openrouter_model=_runtime_overrides.get("openrouter_model", settings.openrouter_model),
        temperature=_runtime_overrides.get("temperature", settings.temperature),
        max_tokens=_runtime_overrides.get("max_tokens", settings.max_tokens),
        embedding_model=_runtime_overrides.get("embedding_model", settings.embedding_model),
        top_k_results=_runtime_overrides.get("top_k_results", settings.top_k_results),
        llm_provider=_runtime_overrides.get("llm_provider", settings.llm_provider),
        environment=settings.environment,
        debug=settings.debug,
        database_connected=db_connected,
    )


@router.put("")
async def update_settings(update: SettingsUpdate) -> dict:
    """
    Update application settings.
    Changes are applied at runtime and optionally saved to .env file.
    """
    updated_fields = []

    update_dict = update.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            # Don't overwrite API key if masked value is sent back
            if field == "openrouter_api_key" and value.startswith("****"):
                continue
            _runtime_overrides[field] = value
            updated_fields.append(field)

            # Also update the live settings object where possible
            if field == "openrouter_api_key" and value and not value.startswith("****"):
                os.environ["OPENROUTER_API_KEY"] = value
            elif field == "openrouter_model":
                os.environ["OPENROUTER_MODEL"] = value
            elif field == "temperature":
                os.environ["TEMPERATURE"] = str(value)
            elif field == "max_tokens":
                os.environ["MAX_TOKENS"] = str(value)
            elif field == "embedding_model":
                os.environ["EMBEDDING_MODEL"] = value
            elif field == "top_k_results":
                os.environ["TOP_K_RESULTS"] = str(value)
            elif field == "llm_provider":
                os.environ["LLM_PROVIDER"] = value

    logger.info("Settings updated", fields=updated_fields)

    return {
        "status": "success",
        "message": f"Updated {len(updated_fields)} setting(s)",
        "updated_fields": updated_fields,
    }


@router.post("/test-connection")
async def test_connection() -> dict:
    """
    Test backend connectivity including database and LLM provider.
    """
    results = {
        "backend": {"status": "healthy", "version": settings.app_version},
        "database": {"status": "unknown"},
        "llm": {"status": "unknown"},
    }

    # Test database
    try:
        db_healthy = await check_db_connection()
        results["database"]["status"] = "connected" if db_healthy else "disconnected"
    except Exception as e:
        results["database"]["status"] = "error"
        results["database"]["error"] = str(e)

    # Test LLM provider
    provider = _runtime_overrides.get("llm_provider", settings.llm_provider)
    api_key = _runtime_overrides.get("openrouter_api_key", settings.openrouter_api_key)

    if provider == "openrouter" and api_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            model = _runtime_overrides.get("openrouter_model", settings.openrouter_model)
            # Make a quick test call
            import asyncio
            async def test_call():
                return await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
                    max_tokens=10
                )
            
            asyncio.run(test_call())
            
            results["llm"]["status"] = "connected"
            results["llm"]["provider"] = "openrouter"
            results["llm"]["model"] = model
        except Exception as e:
            results["llm"]["status"] = "error"
            results["llm"]["error"] = str(e)
    else:
        results["llm"]["status"] = "not_configured"
        results["llm"]["provider"] = provider

    return results
