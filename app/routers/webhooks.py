"""
GitHub webhook handlers.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.config import settings
from app.services.github_service import get_github_service
from app.services.job_service import get_job_service
from app.supabase_client import supabase


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/github")
async def handle_github_webhook(request: Request):
    """
    Handle GitHub webhook events.
    
    Processes push, pull_request, and other events from GitHub.
    """
    # Get raw payload
    payload = await request.body()
    
    # Get headers
    event_type = request.headers.get("X-GitHub-Event", "")
    signature = request.headers.get("X-Hub-Signature-256", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    
    # Verify signature
    github_service = get_github_service()
    
    if not github_service.verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse payload
    try:
        import json
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Get repository info
    repo_data = data.get("repository", {})
    repo_github_id = repo_data.get("id")
    repo_full_name = repo_data.get("full_name", "")
    
    if not repo_github_id:
        return {"status": "ignored", "reason": "No repository info"}
    
    # Find connected repository
    repo_response = supabase.table("repositories").select("*").eq("github_id", repo_github_id).eq("is_active", True).execute()
    
    if not repo_response.data:
        return {"status": "ignored", "reason": "Repository not connected"}
    
    repo = repo_response.data[0]
    
    # Process event based on type
    result = {"status": "processed", "event": event_type}
    
    if event_type == "push":
        result = await _handle_push_event(repo, data)
    elif event_type == "pull_request":
        result = await _handle_pull_request_event(repo, data)
    elif event_type == "repository":
        result = await _handle_repository_event(repo, data)
    elif event_type == "ping":
        result = {"status": "pong", "zen": data.get("zen", "")}
    else:
        result = {"status": "ignored", "event": event_type}
    
    return result


async def _handle_push_event(repo: dict, data: dict) -> dict[str, Any]:
    """
    Handle push events.
    
    Triggers analysis on push to main/master branch.
    """
    ref = data.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
    
    # Check if this is the default branch
    if branch != repo.get("default_branch", "main"):
        return {
            "status": "ignored",
            "reason": f"Not default branch: {branch}",
        }
    
    # Create sync job to update metadata
    job_service = get_job_service()
    job = await job_service.create_job(
        job_type="sync",
        repository_id=repo["id"],
        payload={
            "trigger": "push",
            "branch": branch,
            "sender": data.get("sender", {}).get("login"),
        },
    )
    
    return {
        "status": "triggered",
        "job_id": job["id"],
        "branch": branch,
    }


async def _handle_pull_request_event(repo: dict, data: dict) -> dict[str, Any]:
    """
    Handle pull request events.
    
    Triggers analysis on PR open/synchronize.
    """
    action = data.get("action", "")
    pr = data.get("pull_request", {})
    pr_number = pr.get("number")
    
    # Only process relevant actions
    if action not in ["opened", "synchronize", "reopened"]:
        return {
            "status": "ignored",
            "reason": f"PR action not relevant: {action}",
        }
    
    # Create sync job
    job_service = get_job_service()
    job = await job_service.create_job(
        job_type="sync",
        repository_id=repo["id"],
        payload={
            "trigger": "pull_request",
            "action": action,
            "pr_number": pr_number,
            "sender": data.get("sender", {}).get("login"),
        },
    )
    
    return {
        "status": "triggered",
        "job_id": job["id"],
        "pr_number": pr_number,
        "action": action,
    }


async def _handle_repository_event(repo: dict, data: dict) -> dict[str, Any]:
    """
    Handle repository events.
    
    Updates repository metadata on changes.
    """
    action = data.get("action", "")
    
    if action == "deleted":
        # Mark repository as inactive
        supabase.table("repositories").update({
            "is_active": False,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", repo["id"]).execute()
        
        return {
            "status": "disconnected",
            "reason": "Repository deleted on GitHub",
        }
    
    # Update metadata
    repo_data = data.get("repository", {})
    
    update_data = {}
    if "name" in repo_data:
        update_data["name"] = repo_data["name"]
    if "description" in repo_data:
        update_data["description"] = repo_data["description"]
    if "private" in repo_data:
        update_data["is_private"] = repo_data["private"]
    if "default_branch" in repo_data:
        update_data["default_branch"] = repo_data["default_branch"]
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        supabase.table("repositories").update(update_data).eq("id", repo["id"]).execute()
    
    return {
        "status": "updated",
        "action": action,
    }


@router.post("/github/verify")
async def verify_webhook(request: Request):
    """
    Verify webhook configuration.
    
    Used during setup to confirm webhook is working.
    """
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    github_service = get_github_service()
    
    is_valid = github_service.verify_webhook_signature(payload, signature)
    
    return {
        "valid": is_valid,
        "signature_received": bool(signature),
    }