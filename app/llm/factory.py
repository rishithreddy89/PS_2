"""LLM service factory supporting multiple providers."""

from typing import Union, Optional
from app.core.config import get_settings
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

# Import services with optional dependencies
try:
    from app.llm.openrouter_service import OpenRouterService, get_openrouter_service
except ImportError:
    OpenRouterService = None
    get_openrouter_service = None

settings = get_settings()


class LLMServiceFactory:
    """Factory for creating LLM services based on configuration."""
    
    @staticmethod
    def get_service() -> OpenRouterService:
        """Get LLM service based on environment configuration."""
        provider = settings.llm_provider.lower()
        
        if provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY not configured")
            if OpenRouterService is None:
                raise ImportError("OpenRouter package not installed")
            return get_openrouter_service()
        
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported: openrouter"
            )
    
    @staticmethod
    def get_openrouter_service() -> Optional[OpenRouterService]:
        """Get OpenRouter service if available."""
        if not settings.openrouter_api_key:
            return None
        if OpenRouterService is None:
            return None
        return get_openrouter_service()


def get_llm_service() -> OpenRouterService:
    """Get configured LLM service."""
    return LLMServiceFactory.get_service()
