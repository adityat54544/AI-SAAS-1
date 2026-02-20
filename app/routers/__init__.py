"""
API routers for AutoDevOps AI Platform.
"""

from app.routers.auth import router as auth_router
from app.routers.repositories import router as repositories_router
from app.routers.analysis import router as analysis_router
from app.routers.jobs import router as jobs_router
from app.routers.webhooks import router as webhooks_router
from app.routers.ci_cd import router as ci_cd_router

__all__ = [
    "auth_router",
    "repositories_router",
    "analysis_router",
    "jobs_router",
    "webhooks_router",
    "ci_cd_router",
]