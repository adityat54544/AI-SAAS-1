"""
Application configuration using Pydantic Settings.
Provides type-safe configuration management with environment variable support.
Includes CI-safe fallbacks for testing and development.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_test_environment() -> bool:
    """Check if running in test or CI environment."""
    env = os.environ.get("ENVIRONMENT", "").lower()
    return env in ("test", "ci", "testing") or os.environ.get("CI") == "true"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=None,  # Use Railway environment variables only
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

    # Supabase Configuration (with CI-safe fallbacks)
    supabase_url: str = "https://test-project.supabase.co" if _is_test_environment() else ""
    supabase_service_role_key: str = "test-service-role-key" if _is_test_environment() else ""
    supabase_anon_key: Optional[str] = "test-anon-key" if _is_test_environment() else None

    # GitHub OAuth Configuration (with CI-safe fallbacks)
    github_client_id: str = "test-github-client-id" if _is_test_environment() else ""
    github_client_secret: str = "test-github-client-secret" if _is_test_environment() else ""
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"

    # GitHub Webhook Configuration
    github_webhook_secret: Optional[str] = "test-webhook-secret" if _is_test_environment() else None

    # AI Configuration (with CI-safe fallbacks)
    gemini_api_key: Optional[str] = "test-gemini-api-key" if _is_test_environment() else None
    ai_provider: str = "gemini"
    ai_model: str = "gemini-1.5-flash"

    # Redis Configuration
    # Primary Redis URL - can be standalone Redis or Upstash
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    
    # Supabase Redis Configuration (alternative to standalone Redis)
    # If set, takes precedence over redis_url for Supabase-managed Redis
    supabase_redis_url: Optional[str] = None
    supabase_redis_password: Optional[str] = None

    # Encryption Configuration (with CI-safe fallback)
    encryption_key: Optional[str] = "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcy1sb25n" if _is_test_environment() else None  # AES-256 key (32 bytes, base64 encoded)

    # Security Settings
    # CORS origins - comma-separated list of allowed origins
    # In production, set CORS_ORIGINS env var to include your frontend URL
    # Example: https://your-app.vercel.app,https://your-custom-domain.com
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Frontend URL for OAuth redirects
    # In production, set FRONTEND_URL env var to your production frontend
    # Example: https://your-app.vercel.app
    frontend_url: str = "http://localhost:3000"
    
    jwt_secret: Optional[str] = "test-jwt-secret-for-ci-testing-only" if _is_test_environment() else None
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

    @property
    def effective_redis_url(self) -> str:
        """
        Get the effective Redis URL.
        
        Priority order:
        1. SUPABASE_REDIS_URL if set (Supabase-managed Redis)
        2. REDIS_URL (standalone Redis or Upstash)
        3. Default localhost Redis for development
        
        Returns:
            The Redis connection URL to use.
        """
        if self.supabase_redis_url:
            # Use Supabase Redis if configured
            return self.supabase_redis_url
        return self.redis_url

    @property
    def effective_redis_password(self) -> Optional[str]:
        """
        Get the effective Redis password.
        
        Priority order:
        1. SUPABASE_REDIS_PASSWORD if set
        2. REDIS_PASSWORD if set
        3. None
        
        Returns:
            The Redis password to use, or None.
        """
        if self.supabase_redis_url and self.supabase_redis_password:
            return self.supabase_redis_password
        return self.redis_password

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment.lower() in ("test", "ci", "testing")
    
    def has_supabase_config(self) -> bool:
        """Check if real Supabase credentials are configured."""
        return bool(
            self.supabase_url and 
            not self.supabase_url.startswith("https://test-project") and
            self.supabase_service_role_key and 
            not self.supabase_service_role_key.startswith("test-")
        )
    
    def has_github_config(self) -> bool:
        """Check if real GitHub OAuth credentials are configured."""
        return bool(
            self.github_client_id and 
            not self.github_client_id.startswith("test-") and
            self.github_client_secret and 
            not self.github_client_secret.startswith("test-")
        )
    
    def has_gemini_config(self) -> bool:
        """Check if real Gemini API key is configured."""
        return bool(
            self.gemini_api_key is not None and 
            not self.gemini_api_key.startswith("test-")
        )
    
    def has_redis_config(self) -> bool:
        """Check if Redis is available (either external or local)."""
        return bool(self.effective_redis_url)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Export settings instance for convenience
settings = get_settings()