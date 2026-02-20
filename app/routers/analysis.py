"""
Analysis routes for repository analysis operations.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.ai.provider import AnalysisRequest
from app.ai.router import get_ai_router
from app.services.analysis_service import get_analysis_service
from app.services.job_service import get_job_service
from app.supabase_client import supabase


router = APIRouter(prefix="/analysis", tags=["Analysis"])


# Pydantic models
class AnalysisCreate(BaseModel):
    repository_id: str
    analysis_type: str = "full"


class AnalysisResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    analysis_type: str
    triggered_by: str
    created_at: str


def _get_user_id(request: Request) -> str:
    """Extract user ID from request cookies."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.post("")
async def create_analysis(request: Request, data: AnalysisCreate):
    """
    Trigger a new repository analysis.
    """
    user_id = _get_user_id(request)
    
    try:
        # Verify repository access
        repo_response = (
            supabase.table("repositories")
            .select("*, organizations!inner(owner_id)")
            .eq("id", data.repository_id)
            .execute()
        )
        
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = repo_response.data[0]
        org = repo.get("organizations", {})
        
        if org.get("owner_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create analysis record
        analysis_service = get_analysis_service()
        analysis = await analysis_service.create_analysis(
            repository_id=data.repository_id,
            analysis_type=data.analysis_type,
            triggered_by=user_id,
        )
        
        # Create job for background processing
        job_service = get_job_service()
        job = await job_service.create_job(
            job_type="analysis",
            repository_id=data.repository_id,
            payload={
                "analysis_id": analysis["id"],
                "analysis_type": data.analysis_type,
            },
        )
        
        return {
            "status": "success",
            "analysis": analysis,
            "job_id": job["id"],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create analysis: {str(e)}")


@router.get("/{analysis_id}")
async def get_analysis(request: Request, analysis_id: str):
    """
    Get analysis details and results.
    """
    user_id = _get_user_id(request)
    
    try:
        analysis_service = get_analysis_service()
        analysis = await analysis_service.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Verify access through repository
        repo_response = (
            supabase.table("repositories")
            .select("organizations!inner(owner_id)")
            .eq("id", analysis["repository_id"])
            .execute()
        )
        
        if repo_response.data:
            org = repo_response.data[0].get("organizations", {})
            if org.get("owner_id") != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return {"analysis": analysis}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@router.get("/{analysis_id}/recommendations")
async def get_recommendations(
    request: Request,
    analysis_id: str,
    category: Optional[str] = None,
    severity: Optional[str] = None,
):
    """
    Get recommendations from an analysis.
    """
    user_id = _get_user_id(request)
    
    try:
        analysis_service = get_analysis_service()
        
        # Verify analysis exists and user has access
        analysis = await analysis_service.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Verify access
        repo_response = (
            supabase.table("repositories")
            .select("organizations!inner(owner_id)")
            .eq("id", analysis["repository_id"])
            .execute()
        )
        
        if repo_response.data:
            org = repo_response.data[0].get("organizations", {})
            if org.get("owner_id") != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        recommendations = await analysis_service.get_recommendations(
            analysis_id=analysis_id,
            category=category,
            severity=severity,
        )
        
        return {"recommendations": recommendations}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/{analysis_id}/remediations")
async def get_remediations(request: Request, analysis_id: str):
    """
    Get remediation snippets from an analysis.
    """
    user_id = _get_user_id(request)
    
    try:
        analysis_service = get_analysis_service()
        
        # Verify analysis exists and user has access
        analysis = await analysis_service.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Verify access
        repo_response = (
            supabase.table("repositories")
            .select("organizations!inner(owner_id)")
            .eq("id", analysis["repository_id"])
            .execute()
        )
        
        if repo_response.data:
            org = repo_response.data[0].get("organizations", {})
            if org.get("owner_id") != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        remediations = await analysis_service.get_remediation_snippets(analysis_id)
        
        return {"remediations": remediations}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get remediations: {str(e)}")


@router.get("/repository/{repository_id}")
async def list_repository_analyses(
    request: Request,
    repository_id: str,
    limit: int = 10,
    offset: int = 0,
):
    """
    List analyses for a repository.
    """
    user_id = _get_user_id(request)
    
    try:
        # Verify access
        repo_response = (
            supabase.table("repositories")
            .select("organizations!inner(owner_id)")
            .eq("id", repository_id)
            .execute()
        )
        
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        org = repo_response.data[0].get("organizations", {})
        
        if org.get("owner_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        analysis_service = get_analysis_service()
        analyses = await analysis_service.get_repository_analyses(
            repository_id=repository_id,
            limit=limit,
            offset=offset,
        )
        
        return {"analyses": analyses}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list analyses: {str(e)}")


@router.post("/{analysis_id}/apply")
async def apply_remediation(
    request: Request,
    analysis_id: str,
    remediation_id: str,
):
    """
    Apply a remediation (simulation mode - does not actually modify files).
    """
    user_id = _get_user_id(request)
    
    try:
        analysis_service = get_analysis_service()
        
        # Verify analysis and access
        analysis = await analysis_service.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        repo_response = (
            supabase.table("repositories")
            .select("organizations!inner(owner_id)")
            .eq("id", analysis["repository_id"])
            .execute()
        )
        
        if repo_response.data:
            org = repo_response.data[0].get("organizations", {})
            if org.get("owner_id") != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Update remediation status (simulation mode)
        response = (
            supabase.table("remediation_snippets")
            .update({
                "apply_status": "applied",
                "applied_by": user_id,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", remediation_id)
            .eq("analysis_id", analysis_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Remediation not found")
        
        return {
            "status": "success",
            "message": "Remediation marked as applied (simulation mode)",
            "remediation": response.data[0],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply remediation: {str(e)}")