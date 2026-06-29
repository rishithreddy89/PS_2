"""
Core configuration module for LexMind AI platform.

Centralized configuration management using Pydantic Settings.
All configuration loaded from environment variables with validation.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading and validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    app_name: str = Field(default="LexMind AI", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1024, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, description="Number of workers")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    database_url: str = Field(
        default="mysql+aiomysql://lexmind:lexmind_password@localhost:3306/lexmind_db",
        description="MySQL connection URL",
    )
    database_pool_size: int = Field(default=20, ge=5, description="Database pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Database max overflow")
    database_echo: bool = Field(default=False, description="Echo SQL statements")

    secret_key: str = Field(
        default="your-secret-key-here-change-in-production-minimum-32-characters-long",
        min_length=32,
        description="Secret key for JWT",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, ge=1, description="Refresh token expiration in days"
    )

    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_allow_methods: List[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")

    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or console")
    log_output: str = Field(default="stdout", description="Log output: stdout or file")

    llm_provider: str = Field(default="openrouter", description="LLM provider")
    llm_model: str = Field(
        default="qwen/qwen-2.5-7b-instruct", description="LLM model identifier"
    )
    llm_api_key: str = Field(default="", description="LLM API key")
    llm_max_tokens: int = Field(default=4096, ge=1, description="LLM max tokens")
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM temperature")

    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_model: str = Field(default="qwen/qwen-2.5-7b-instruct", description="OpenRouter chat model")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )
    
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Default embedding model"
    )
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=6000, ge=1, description="Max tokens for completion")
    top_k_results: int = Field(default=5, ge=1, description="Number of retrieval results")

    vector_db_provider: str = Field(default="chromadb", description="Vector database provider")
    vector_db_path: str = Field(default="./data/chroma", description="Vector database path")
    vector_db_dimension: int = Field(default=1536, ge=1, description="Vector dimension")
    chroma_persist_directory: str = Field(
        default="./chroma_db", description="ChromaDB persistence directory"
    )

    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking")

    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, ge=1, description="Requests per minute")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        allowed_formats = ["json", "console"]
        v_lower = v.lower()
        if v_lower not in allowed_formats:
            raise ValueError(f"Log format must be one of {allowed_formats}")
        return v_lower

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        allowed_envs = ["development", "staging", "production", "testing"]
        v_lower = v.lower()
        if v_lower not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v_lower

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.database_url.replace("+aiomysql", "")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing."""
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()


settings = get_settings()
