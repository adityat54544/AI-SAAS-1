"""
AutoDevOps AI Platform - Main FastAPI Application.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.routers import (
    auth_router,
    repositories_router,
    analysis_router,
    jobs_router,
    webhooks_router,
    ci_cd_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    
    # Initialize Sentry if configured
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment or settings.environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
        )
        print("Sentry initialized")
    
    yield
    
    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
AutoDevOps AI Platform - Intelligent repository analysis and CI/CD automation.

## Features

* **Repository Analysis**: AI-powered analysis of code quality, security, and performance
* **CI/CD Generation**: Automated generation of CI/CD configurations
* **GitHub Integration**: Seamless integration with GitHub repositories
* **Real-time Updates**: Live progress updates via Supabase realtime

## Authentication

This API uses GitHub OAuth for authentication. Use the `/auth/github` endpoint to initiate the OAuth flow.
        """,
        docs_url="/docs" if settings.is_development() else None,
        redoc_url="/redoc" if settings.is_development() else None,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Log the error
        print(f"Unhandled error: {exc}")
        
        # Send to Sentry if configured
        if settings.sentry_dsn:
            sentry_sdk.capture_exception(exc)
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": str(exc) if settings.is_development() else "An unexpected error occurred",
            },
        )
    
    # Include routers
    app.include_router(auth_router)
    app.include_router(repositories_router)
    app.include_router(analysis_router)
    app.include_router(jobs_router)
    app.include_router(webhooks_router)
    app.include_router(ci_cd_router)
    
    return app


# Create the app instance
app = create_app()


# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.is_development() else "disabled",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


# Readiness probe for Kubernetes
@app.get("/ready", tags=["Health"])
def readiness_check():
    """Readiness probe for Kubernetes deployments."""
    # Check database connection
    try:
        from app.supabase_client import supabase
        # Simple query to check connection
        supabase.table("users").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Redis connection (optional)
    redis_status = "not_configured"
    if settings.redis_url:
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            redis_status = "connected"
        except Exception as e:
            redis_status = f"error: {str(e)}"
    
    is_ready = db_status == "connected"
    
    return {
        "ready": is_ready,
        "checks": {
            "database": db_status,
            "redis": redis_status,
        },
    }


# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["Monitoring"])
def metrics():
    """Prometheus metrics endpoint."""
    # Basic metrics
    metrics_data = f"""# HELP app_info Application information
# TYPE app_info gauge
app_info{{version="{settings.app_version}",environment="{settings.environment}"}} 1

# HELP app_requests_total Total number of requests
# TYPE app_requests_total counter
# This would be populated by a metrics middleware in production
"""
    return Response(content=metrics_data, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development(),
    )