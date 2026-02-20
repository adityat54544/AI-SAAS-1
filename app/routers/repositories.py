"""
Repository management routes.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.github_service import get_github_service
from app.supabase_client import supabase


router = APIRouter(prefix="/repositories", tags=["Repositories"])


# Pydantic models
class RepositoryConnect(BaseModel):
    github_id: int
    org_id: str


class RepositoryResponse(BaseModel):
    id: str
    org_id: str
    github_id: int
    name: str
    full_name: str
    description: Optional[str]
    html_url: str
    language: Optional[str]
    stargazers_count: int
    forks_count: int
    is_private: bool
    is_active: bool
    last_analyzed_at: Optional[str]


class HealthResponse(BaseModel):
    overall_score: float
    security_score: float
    performance_score: float
    code_quality_score: float
    ci_cd_score: float
    dependencies_score: float


def _get_user_id(request: Request) -> str:
    """Extract user ID from request cookies."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


async def _get_user_token(user_id: str) -> tuple[str, str]:
    """Get decrypted GitHub token for user."""
    token_response = supabase.table("github_tokens").select("*").eq("user_id", user_id).limit(1).execute()
    
    if not token_response.data:
        raise HTTPException(status_code=400, detail="GitHub not connected")
    
    token_record = token_response.data[0]
    github_service = get_github_service()
    
    access_token = github_service.decrypt_token(token_record["access_token_encrypted"])
    org_id = token_record["org_id"]
    
    return access_token, org_id


@router.get("")
async def list_repositories(request: Request):
    """
    List connected repositories for the user's organizations.
    """
    user_id = _get_user_id(request)
    
    try:
        # Get user's organizations
        orgs_response = supabase.table("organizations").select("id").eq("owner_id", user_id).execute()
        org_ids = [org["id"] for org in orgs_response.data] if orgs_response.data else []
        
        if not org_ids:
            return {"repositories": []}
        
        # Get repositories for these organizations
        repos_response = (
            supabase.table("repositories")
            .select("*, repository_health(*)")
            .in_("org_id", org_ids)
            .eq("is_active", True)
            .order("last_analyzed_at", desc=True)
            .execute()
        )
        
        return {"repositories": repos_response.data or []}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list repositories: {str(e)}")


@router.get("/github")
async def list_github_repositories(request: Request, page: int = 1, per_page: int = 30):
    """
    List repositories from GitHub for connection.
    """
    user_id = _get_user_id(request)
    
    try:
        access_token, org_id = await _get_user_token(user_id)
        github_service = get_github_service()
        
        repos = await github_service.get_user_repositories(
            access_token=access_token,
            page=page,
            per_page=per_page,
        )
        
        # Get existing connected repos
        existing_response = supabase.table("repositories").select("github_id").eq("org_id", org_id).execute()
        existing_ids = {r["github_id"] for r in existing_response.data} if existing_response.data else set()
        
        # Mark which repos are already connected
        for repo in repos:
            repo["is_connected"] = repo["id"] in existing_ids
        
        return {"repositories": repos, "page": page, "per_page": per_page}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list GitHub repositories: {str(e)}")


@router.post("/connect")
async def connect_repository(request: Request, data: RepositoryConnect):
    """
    Connect a GitHub repository to the platform.
    """
    user_id = _get_user_id(request)
    
    try:
        access_token, user_org_id = await _get_user_token(user_id)
        github_service = get_github_service()
        
        # Verify org_id belongs to user
        org_response = supabase.table("organizations").select("*").eq("id", data.org_id).eq("owner_id", user_id).execute()
        
        if not org_response.data:
            raise HTTPException(status_code=403, detail="Organization not found or access denied")
        
        # Check if already connected
        existing = supabase.table("repositories").select("id").eq("org_id", data.org_id).eq("github_id", data.github_id).execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail="Repository already connected")
        
        # Get repository metadata from GitHub
        # First, find the repo in user's repos to get full_name
        repos = await github_service.get_user_repositories(access_token)
        repo_info = next((r for r in repos if r["id"] == data.github_id), None)
        
        if not repo_info:
            raise HTTPException(status_code=404, detail="Repository not found in user's GitHub account")
        
        owner, name = repo_info["full_name"].split("/", 1)
        
        # Get detailed metadata
        metadata = await github_service.get_repository_metadata(owner, name, access_token)
        
        # Create webhook
        webhook_url = f"{request.base_url}webhooks/github"
        webhook_config = await github_service.create_webhook(
            owner=owner,
            repo=name,
            access_token=access_token,
            webhook_url=webhook_url,
        )
        
        # Insert repository
        repo_data = {
            "org_id": data.org_id,
            "github_id": metadata.github_id,
            "name": metadata.name,
            "full_name": metadata.full_name,
            "description": metadata.description,
            "html_url": metadata.html_url,
            "language": metadata.language,
            "stargazers_count": metadata.stargazers_count,
            "forks_count": metadata.forks_count,
            "is_private": metadata.is_private,
            "default_branch": metadata.default_branch,
            "topics": metadata.topics,
            "webhook_id": webhook_config.get("id"),
            "is_active": True,
        }
        
        response = supabase.table("repositories").insert(repo_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create repository")
        
        return {"status": "success", "repository": response.data[0]}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect repository: {str(e)}")


@router.delete("/{repository_id}")
async def disconnect_repository(request: Request, repository_id: str):
    """
    Disconnect a repository from the platform.
    """
    user_id = _get_user_id(request)
    
    try:
        # Get repository and verify ownership
        repo_response = supabase.table("repositories").select("*, organizations!inner(*)").eq("id", repository_id).execute()
        
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = repo_response.data[0]
        org = repo.get("organizations", {})
        
        if org.get("owner_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete webhook from GitHub
        if repo.get("webhook_id"):
            try:
                access_token, _ = await _get_user_token(user_id)
                github_service = get_github_service()
                owner, name = repo["full_name"].split("/", 1)
                
                await github_service.delete_webhook(
                    owner=owner,
                    repo=name,
                    hook_id=repo["webhook_id"],
                    access_token=access_token,
                )
            except Exception:
                pass  # Continue even if webhook deletion fails
        
        # Soft delete by setting is_active to False
        supabase.table("repositories").update({"is_active": False}).eq("id", repository_id).execute()
        
        return {"status": "success", "message": "Repository disconnected"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect repository: {str(e)}")


@router.get("/{repository_id}")
async def get_repository(request: Request, repository_id: str):
    """
    Get repository details.
    """
    user_id = _get_user_id(request)
    
    try:
        repo_response = (
            supabase.table("repositories")
            .select("*, organizations!inner(*), repository_health(*)")
            .eq("id", repository_id)
            .execute()
        )
        
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = repo_response.data[0]
        org = repo.get("organizations", {})
        
        # Verify access
        if org.get("owner_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {"repository": repo}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repository: {str(e)}")


@router.get("/{repository_id}/health")
async def get_repository_health(request: Request, repository_id: str):
    """
    Get repository health score.
    """
    user_id = _get_user_id(request)
    
    try:
        # Verify access
        repo_response = (
            supabase.table("repositories")
            .select("id, organizations!inner(owner_id), repository_health(*)")
            .eq("id", repository_id)
            .execute()
        )
        
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = repo_response.data[0]
        org = repo.get("organizations", {})
        
        if org.get("owner_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        health = repo.get("repository_health")
        
        return {"health": health}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health: {str(e)}")


@router.post("/{repository_id}/sync")
async def sync_repository(request: Request, repository_id: str):
    """
    Sync repository metadata from GitHub.
    """
    user_id = _get_user_id(request)
    
    try:
        # Get repository and verify ownership
        repo_response = supabase.table("repositories").select("*, organizations!inner(owner_id)").eq("id", repository_id).execute()
        
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = repo_response.data[0]
        org = repo.get("organizations", {})
        
        if org.get("owner_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        access_token, _ = await _get_user_token(user_id)
        github_service = get_github_service()
        
        owner, name = repo["full_name"].split("/", 1)
        metadata = await github_service.get_repository_metadata(owner, name, access_token)
        
        # Update repository
        update_data = {
            "name": metadata.name,
            "description": metadata.description,
            "language": metadata.language,
            "stargazers_count": metadata.stargazers_count,
            "forks_count": metadata.forks_count,
            "default_branch": metadata.default_branch,
            "topics": metadata.topics,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        response = supabase.table("repositories").update(update_data).eq("id", repository_id).execute()
        
        return {"status": "success", "repository": response.data[0] if response.data else None}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync repository: {str(e)}")