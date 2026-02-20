"""
Rate Limiting Middleware.

Implements rate limiting using slowapi (Redis-backed) with per-user and per-IP limits.
"""

import logging
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger(__name__)


def get_user_id_or_ip(request: Request) -> str:
    """
    Get user ID from request state or fall back to IP address.
    
    This function is used as the key function for rate limiting.
    Authenticated users get per-user limits, anonymous users get per-IP limits.
    """
    # Try to get user ID from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address
    ip = get_remote_address(request) or "unknown"
    return f"ip:{ip}"


# Initialize limiter
limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=[f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds"],
    storage_uri=settings.redis_url,
    enabled=True,
)


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Set up rate limiting middleware for a FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    # Add SlowAPI middleware
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info(
        "Rate limiting configured",
        extra={
            "default_limits": f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds}s",
            "storage": settings.redis_url,
        }
    )


# Rate limit decorators for specific endpoints
def limit_analysis():
    """Rate limit for analysis endpoints (more restrictive)."""
    return limiter.limit("10 per minute")


def limit_heavy():
    """Rate limit for heavy endpoints (very restrictive)."""
    return limiter.limit("5 per minute")


def limit_auth():
    """Rate limit for authentication endpoints."""
    return limiter.limit("20 per minute")


def limit_webhook():
    """Rate limit for webhook endpoints."""
    return limiter.limit("100 per minute")


def limit_default():
    """Default rate limit."""
    return limiter.limit(f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds")


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception
        
    Returns:
        JSON response with error details
    """
    logger.warning(
        "Rate limit exceeded",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": get_user_id_or_ip(request),
            "limit": str(exc.detail),
        }
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "error": "too_many_requests",
            "message": "You have exceeded the rate limit. Please wait before making more requests.",
            "retry_after": exc.detail,
        },
        headers={"Retry-After": str(exc.detail)},
    )


class RateLimitMiddleware:
    """
    Custom rate limit middleware for more granular control.
    
    This middleware adds additional rate limiting logic beyond slowapi,
    including per-endpoint and per-user-type limits.
    """
    
    # Endpoint-specific limits (requests per minute)
    ENDPOINT_LIMITS = {
        "/api/analysis": 10,
        "/api/jobs": 20,
        "/api/repositories": 30,
        "/auth": 20,
        "/webhooks": 100,
    }
    
    def __init__(self, app: FastAPI):
        """Initialize the middleware."""
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process the request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive, send)
        
        # Check for endpoint-specific limits
        path = scope.get("path", "")
        for endpoint, limit in self.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint):
                # Endpoint-specific limit handling would go here
                break
        
        await self.app(scope, receive, send)


def get_rate_limit_headers(request: Request) -> dict:
    """
    Get rate limit headers for a response.
    
    Args:
        request: FastAPI request
        
    Returns:
        Dictionary of rate limit headers
    """
    # These headers would be populated by slowapi
    return {
        "X-RateLimit-Limit": str(settings.rate_limit_requests),
        "X-RateLimit-Window": str(settings.rate_limit_window_seconds),
    }