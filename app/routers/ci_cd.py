"""
CI/CD generation routes.
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.ai.provider import CIConfigRequest
from app.ai.router import get_ai_router
from app.supabase_client import supabase


router = APIRouter(prefix="/ci-cd", tags=["CI/CD"])


# Pydantic models
class CIGenerateRequest(BaseModel):
    repository_id: str
    target_platform: str = "github_actions"
    requirements: list[str] = []


class CIValidateRequest(BaseModel):
    config_yaml: str
    platform: str = "github_actions"


def _get_user_id(request: Request) -> str:
    """Extract user ID from request cookies."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.post("/generate")
async def generate_ci_config(request: Request, data: CIGenerateRequest):
    """
    Generate CI/CD configuration using AI.
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
        
        # Build repository context for AI
        repo_context = {
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "language": repo.get("language"),
            "description": repo.get("description"),
            "default_branch": repo.get("default_branch", "main"),
        }
        
        # Get AI router and generate config
        ai_router = get_ai_router()
        
        ci_request = CIConfigRequest(
            repository_context=repo_context,
            target_platform=data.target_platform,
            requirements=data.requirements,
        )
        
        response = await ai_router.route_ci_generation(ci_request)
        
        # Store artifact
        artifact_data = {
            "org_id": org.get("id"),
            "repository_id": data.repository_id,
            "artifact_type": "ci_config",
            "name": f"{data.target_platform}_config",
            "content": response.config_yaml,
            "format": "yaml",
            "metadata": {
                "platform": data.target_platform,
                "explanations": response.explanations,
                "provider": response.provider,
            },
        }
        
        supabase.table("artifacts").insert(artifact_data).execute()
        
        return {
            "status": "success",
            "config_yaml": response.config_yaml,
            "explanations": response.explanations,
            "platform": data.target_platform,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CI config: {str(e)}")


@router.get("/templates")
async def list_ci_templates():
    """
    List available CI/CD templates.
    """
    templates = [
        {
            "id": "github_actions_basic",
            "name": "GitHub Actions - Basic",
            "platform": "github_actions",
            "description": "Basic CI pipeline with build and test stages",
            "languages": ["*"],
        },
        {
            "id": "github_actions_node",
            "name": "GitHub Actions - Node.js",
            "platform": "github_actions",
            "description": "Node.js CI with npm/yarn, linting, and testing",
            "languages": ["JavaScript", "TypeScript"],
        },
        {
            "id": "github_actions_python",
            "name": "GitHub Actions - Python",
            "platform": "github_actions",
            "description": "Python CI with pip, pytest, and linting",
            "languages": ["Python"],
        },
        {
            "id": "github_actions_docker",
            "name": "GitHub Actions - Docker",
            "platform": "github_actions",
            "description": "Docker build and push workflow",
            "languages": ["*"],
        },
        {
            "id": "gitlab_ci_basic",
            "name": "GitLab CI - Basic",
            "platform": "gitlab_ci",
            "description": "Basic GitLab CI pipeline",
            "languages": ["*"],
        },
        {
            "id": "circleci_basic",
            "name": "CircleCI - Basic",
            "platform": "circleci",
            "description": "Basic CircleCI configuration",
            "languages": ["*"],
        },
    ]
    
    return {"templates": templates}


@router.post("/validate")
async def validate_ci_config(request: Request, data: CIValidateRequest):
    """
    Validate CI/CD configuration.
    """
    user_id = _get_user_id(request)
    
    try:
        # Basic validation
        issues = []
        warnings = []
        
        # Check for common issues
        config = data.config_yaml.lower()
        
        if data.platform == "github_actions":
            if "on:" not in config:
                issues.append("Missing 'on' trigger definition")
            
            if "jobs:" not in config:
                issues.append("Missing 'jobs' section")
            
            if "runs-on" not in config:
                issues.append("Missing 'runs-on' specification")
            
            if "uses:" not in config and "run:" not in config:
                issues.append("No steps defined (missing 'uses' or 'run')")
            
            # Security warnings
            if "${{ secrets." not in data.config_yaml:
                warnings.append("Consider using secrets for sensitive data")
            
            if "checkout" not in config:
                warnings.append("Most workflows need actions/checkout")
        
        # Calculate quality score
        score = 100
        score -= len(issues) * 20
        score -= len(warnings) * 5
        score = max(0, score)
        
        return {
            "valid": len(issues) == 0,
            "score": score,
            "issues": issues,
            "warnings": warnings,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/artifacts/{repository_id}")
async def list_ci_artifacts(request: Request, repository_id: str):
    """
    List CI/CD artifacts for a repository.
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
        
        # Get artifacts
        artifacts_response = (
            supabase.table("artifacts")
            .select("*")
            .eq("repository_id", repository_id)
            .eq("artifact_type", "ci_config")
            .order("created_at", desc=True)
            .execute()
        )
        
        return {"artifacts": artifacts_response.data or []}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list artifacts: {str(e)}")