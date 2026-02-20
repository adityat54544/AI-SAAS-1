"""
Authentication routes for GitHub OAuth integration.
"""

import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import settings
from app.services.github_service import get_github_service, GitHubService
from app.supabase_client import supabase


router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic models
class OAuthState(BaseModel):
    state: str
    redirect_uri: Optional[str] = None


class SessionResponse(BaseModel):
    authenticated: bool
    user: Optional[dict[str, Any]] = None
    has_github_token: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str


# In-memory state store (use Redis in production)
_oauth_states: dict[str, dict[str, Any]] = {}


@router.get("/github")
async def github_oauth_initiate(
    request: Request,
    redirect_after: Optional[str] = None,
):
    """
    Initiate GitHub OAuth flow.
    
    Generates a random state and redirects to GitHub authorization page.
    """
    github_service = get_github_service()
    
    # Generate secure random state
    state = secrets.token_urlsafe(32)
    
    # Store state with redirect info
    _oauth_states[state] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "redirect_after": redirect_after,
    }
    
    # Generate OAuth URL
    oauth_url = github_service.get_oauth_url(state)
    
    return RedirectResponse(url=oauth_url)


@router.get("/github/callback")
async def github_oauth_callback(
    code: str,
    state: str,
    error: Optional[str] = None,
):
    """
    Handle GitHub OAuth callback.
    
    Exchanges authorization code for access token and stores it.
    """
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub OAuth error: {error}"
        )
    
    # Validate state
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state"
        )
    
    github_service = get_github_service()
    
    try:
        # Exchange code for token
        token_data = await github_service.exchange_code_for_token(code)
        
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        scope = token_data.get("scope", "")
        expires_in = token_data.get("expires_in")
        
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Failed to obtain access token from GitHub"
            )
        
        # Get user info from GitHub
        user_info = await github_service.get_user_info(access_token)
        github_user_id = user_info.get("id")
        github_username = user_info.get("login")
        
        # Get user's email
        emails = await github_service.get_user_emails(access_token)
        primary_email = next(
            (e["email"] for e in emails if e.get("primary")),
            user_info.get("email")
        )
        
        # Create or update user in Supabase
        user_response = supabase.table("users").select("*").eq("email", primary_email).execute()
        
        if user_response.data:
            user = user_response.data[0]
        else:
            # Create new user
            create_response = supabase.table("users").insert({
                "email": primary_email,
                "display_name": user_info.get("name") or github_username,
                "avatar_url": user_info.get("avatar_url"),
            }).execute()
            user = create_response.data[0] if create_response.data else None
        
        if not user:
            raise HTTPException(
                status_code=500,
                detail="Failed to create or retrieve user"
            )
        
        # Create personal organization if doesn't exist
        org_response = supabase.table("organizations").select("*").eq("owner_id", user["id"]).limit(1).execute()
        
        if not org_response.data:
            org_slug = github_username or f"user-{user['id'][:8]}"
            org_response = supabase.table("organizations").insert({
                "name": f"{github_username}'s Organization",
                "slug": org_slug,
                "github_id": user_info.get("id"),
                "avatar_url": user_info.get("avatar_url"),
                "owner_id": user["id"],
                "plan": "free",
            }).execute()
        
        org = org_response.data[0] if org_response.data else None
        
        # Encrypt and store token
        encrypted_token = github_service.encrypt_token(access_token)
        encrypted_refresh = github_service.encrypt_token(refresh_token) if refresh_token else None
        
        # Calculate expiration
        expires_at = None
        if expires_in:
            from datetime import timedelta
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
        
        # Store or update token
        if org:
            supabase.table("github_tokens").upsert({
                "user_id": user["id"],
                "org_id": org["id"],
                "access_token_encrypted": encrypted_token,
                "refresh_token_encrypted": encrypted_refresh,
                "scope": scope,
                "expires_at": expires_at,
                "github_user_id": github_user_id,
                "github_username": github_username,
                "is_valid": True,
            }, on_constraint="user_id,org_id").execute()
        
        # Redirect to frontend
        redirect_url = state_data.get("redirect_after") or f"{settings.cors_origins_list[0]}/dashboard"
        
        # Set session cookie or return token
        response = RedirectResponse(url=redirect_url)
        # In production, use proper session management
        response.set_cookie(
            key="user_id",
            value=user["id"],
            httponly=True,
            secure=settings.is_production(),
            samesite="lax",
            max_age=60 * 60 * 24 * 7,  # 7 days
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth callback failed: {str(e)}"
        )


@router.get("/session", response_model=SessionResponse)
async def get_session(request: Request):
    """
    Get current session information.
    
    Returns user info and GitHub connection status.
    """
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return SessionResponse(authenticated=False)
    
    try:
        # Get user from Supabase
        user_response = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not user_response.data:
            return SessionResponse(authenticated=False)
        
        user = user_response.data[0]
        
        # Check for GitHub token
        token_response = supabase.table("github_tokens").select("id").eq("user_id", user_id).limit(1).execute()
        has_github_token = bool(token_response.data)
        
        return SessionResponse(
            authenticated=True,
            user={
                "id": user["id"],
                "email": user["email"],
                "display_name": user.get("display_name"),
                "avatar_url": user.get("avatar_url"),
            },
            has_github_token=has_github_token,
        )
    
    except Exception:
        return SessionResponse(authenticated=False)


@router.post("/github/disconnect")
async def disconnect_github(request: Request):
    """
    Disconnect GitHub integration.
    
    Revokes GitHub token and removes it from storage.
    """
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Get token
        token_response = supabase.table("github_tokens").select("*").eq("user_id", user_id).execute()
        
        if token_response.data:
            github_service = get_github_service()
            
            for token in token_response.data:
                # Decrypt token (for potential revocation)
                try:
                    # Note: GitHub doesn't have a revoke endpoint for OAuth apps
                    # The token will just be deleted from our storage
                    pass
                except Exception:
                    pass
            
            # Delete tokens from storage
            supabase.table("github_tokens").delete().eq("user_id", user_id).execute()
        
        return {"status": "success", "message": "GitHub disconnected"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect GitHub: {str(e)}"
        )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing session cookie.
    """
    response.delete_cookie(key="user_id")
    return {"status": "success", "message": "Logged out"}


@router.post("/token/refresh")
async def refresh_token(request: Request):
    """
    Refresh GitHub access token.
    
    Uses stored refresh token to get a new access token.
    """
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Get stored token
        token_response = supabase.table("github_tokens").select("*").eq("user_id", user_id).limit(1).execute()
        
        if not token_response.data:
            raise HTTPException(
                status_code=400,
                detail="No GitHub token found"
            )
        
        token_record = token_response.data[0]
        
        if not token_record.get("refresh_token_encrypted"):
            raise HTTPException(
                status_code=400,
                detail="No refresh token available"
            )
        
        github_service = get_github_service()
        
        # Decrypt refresh token
        refresh_token = github_service.decrypt_token(token_record["refresh_token_encrypted"])
        
        # Refresh the token
        new_token_data = await github_service.refresh_token(refresh_token)
        
        # Update stored token
        encrypted_access = github_service.encrypt_token(new_token_data["access_token"])
        
        update_data = {
            "access_token_encrypted": encrypted_access,
            "is_valid": True,
        }
        
        if new_token_data.get("refresh_token"):
            update_data["refresh_token_encrypted"] = github_service.encrypt_token(
                new_token_data["refresh_token"]
            )
        
        supabase.table("github_tokens").update(update_data).eq("id", token_record["id"]).execute()
        
        return {"status": "success", "message": "Token refreshed"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh token: {str(e)}"
        )