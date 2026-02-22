"""
Job management routes.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import get_current_user, SupabaseUser
from app.services.job_service import get_job_service
from app.supabase_client import supabase


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("")
async def list_jobs(
    request: Request,
    repository_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user: SupabaseUser = Depends(get_current_user),
):
    """
    List jobs for the user's repositories.
    """
    user_id = user.id
    
    try:
        # Get user's organizations
        orgs_response = supabase.table("organizations").select("id").eq("owner_id", user_id).execute()
        org_ids = [org["id"] for org in orgs_response.data] if orgs_response.data else []
        
        if not org_ids:
            return {"jobs": []}
        
        # Get repositories for these organizations
        repos_response = supabase.table("repositories").select("id").in_("org_id", org_ids).execute()
        repo_ids = [repo["id"] for repo in repos_response.data] if repos_response.data else []
        
        if not repo_ids:
            return {"jobs": []}
        
        # Build query
        query = supabase.table("jobs").select("*").in_("repository_id", repo_ids)
        
        if repository_id:
            query = query.eq("repository_id", repository_id)
        
        if status:
            query = query.eq("status", status)
        
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return {"jobs": response.data or []}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/{job_id}")
async def get_job(
    request: Request,
    job_id: str,
    user: SupabaseUser = Depends(get_current_user),
):
    """
    Get job details.
    """
    user_id = user.id
    
    try:
        job_service = get_job_service()
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify access through repository
        if job.get("repository_id"):
            repo_response = (
                supabase.table("repositories")
                .select("organizations!inner(owner_id)")
                .eq("id", job["repository_id"])
                .execute()
            )
            
            if repo_response.data:
                org = repo_response.data[0].get("organizations", {})
                if org.get("owner_id") != user_id:
                    raise HTTPException(status_code=403, detail="Access denied")
        
        return {"job": job}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.get("/{job_id}/logs")
async def get_job_logs(
    request: Request,
    job_id: str,
    limit: int = 100,
    user: SupabaseUser = Depends(get_current_user),
):
    """
    Get job logs.
    """
    user_id = user.id
    
    try:
        job_service = get_job_service()
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify access
        if job.get("repository_id"):
            repo_response = (
                supabase.table("repositories")
                .select("organizations!inner(owner_id)")
                .eq("id", job["repository_id"])
                .execute()
            )
            
            if repo_response.data:
                org = repo_response.data[0].get("organizations", {})
                if org.get("owner_id") != user_id:
                    raise HTTPException(status_code=403, detail="Access denied")
        
        # Get logs from Redis
        logs = await job_service.get_job_logs(job_id, limit)
        
        return {"logs": logs}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job logs: {str(e)}")


@router.delete("/{job_id}")
async def cancel_job(
    request: Request,
    job_id: str,
    user: SupabaseUser = Depends(get_current_user),
):
    """
    Cancel a queued job.
    """
    user_id = user.id
    
    try:
        job_service = get_job_service()
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify access
        if job.get("repository_id"):
            repo_response = (
                supabase.table("repositories")
                .select("organizations!inner(owner_id)")
                .eq("id", job["repository_id"])
                .execute()
            )
            
            if repo_response.data:
                org = repo_response.data[0].get("organizations", {})
                if org.get("owner_id") != user_id:
                    raise HTTPException(status_code=403, detail="Access denied")
        
        # Cancel the job
        result = await job_service.cancel_job(job_id)
        
        return {"status": "success", "job": result}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/queue/stats")
async def get_queue_stats(
    request: Request,
    user: SupabaseUser = Depends(get_current_user),
):
    """
    Get job queue statistics.
    """
    try:
        job_service = get_job_service()
        
        queue_length = job_service.get_queue_length()
        
        # Get counts by status
        response = supabase.table("jobs").select("status").execute()
        
        status_counts = {}
        if response.data:
            for job in response.data:
                status = job.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "queue_length": queue_length,
            "status_counts": status_counts,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")