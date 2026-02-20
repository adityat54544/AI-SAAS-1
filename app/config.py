"""
Application configuration using Pydantic Settings.
Provides type-safe configuration management with environment variable support.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = "AutoDevOps AI Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Supabase Configuration
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: Optional[str] = None

    # GitHub OAuth Configuration
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"

    # GitHub Webhook Configuration
    github_webhook_secret: Optional[str] = None

    # AI Configuration
    gemini_api_key: Optional[str] = None
    ai_provider: str = "gemini"
    ai_model: str = "gemini-1.5-flash"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # Encryption Configuration
    encryption_key: Optional[str] = None  # AES-256 key (32 bytes, base64 encoded)

    # Security Settings
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Sentry Configuration (Observability)
    sentry_dsn: Optional[str] = None
    sentry_environment: Optional[str] = None
    sentry_traces_sample_rate: float = 0.1

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Export settings instance for convenience
settings = get_settings()