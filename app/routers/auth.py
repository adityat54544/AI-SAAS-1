"""
Authentication routes - Backend-owned OAuth with cookie sessions.
Single source of truth for frontend identity.

This module provides:
- /auth/me: Get current authenticated user (SSoT for frontend)
- /auth/github: Initiate GitHub OAuth flow
- /auth/callback: Handle OAuth callback, set session cookie
- /auth/signout: Clear session cookie

Session is managed via HttpOnly cookies with SameSite=None for cross-domain.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth import get_current_user_from_cookie, get_current_user_optional, SupabaseUser
from app.config import settings
from app.supabase_client import supabase


router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserResponse(BaseModel):
    """User response for /me endpoint - frontend identity model."""
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None


# Cookie settings for cross-domain (Vercel ↔ Railway)
COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


@router.get("/me", response_model=UserResponse)
async def get_me(user: SupabaseUser = Depends(get_current_user_from_cookie)):
    """
    Get current authenticated user.
    
    This is the SINGLE SOURCE OF TRUTH for frontend identity.
    Frontend calls this to hydrate auth state after:
    - Initial page load
    - Page refresh
    - Session validation
    
    The frontend should call this endpoint with credentials: "include"
    to automatically send the session cookie.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        role=user.role,
    )


@router.get("/github")
async def github_oauth(request: Request):
    """
    Initiate GitHub OAuth flow.
    
    Redirects to Supabase OAuth which handles GitHub authorization.
    After authorization, GitHub redirects back to /auth/callback.
    
    The frontend should redirect to this endpoint, not call it directly.
    """
    frontend_url = settings.frontend_url
    
    if not frontend_url:
        raise HTTPException(
            status_code=500,
            detail="Frontend URL not configured"
        )
    
    # Build the callback URL that Supabase will use
    # This must match what's configured in Supabase dashboard
    callback_base = str(request.base_url).rstrip("/")
    redirect_to = f"{callback_base}/auth/callback"
    
    # Build Supabase OAuth URL
    # Using the authorize endpoint directly for more control
    supabase_oauth_url = (
        f"{settings.supabase_url}/auth/v1/authorize?"
        f"provider=github&"
        f"redirect_to={redirect_to}&"
        f"scopes=repo user:email"
    )
    
    return RedirectResponse(url=supabase_oauth_url)


@router.get("/callback")
async def auth_callback(request: Request, code: Optional[str] = None):
    """
    Handle OAuth callback from Supabase.
    
    Exchange authorization code for session tokens,
    set HttpOnly cookie, redirect to frontend dashboard.
    
    Cookie attributes:
    - HttpOnly: Prevents JavaScript access (security)
    - Secure: Required for SameSite=None (HTTPS only)
    - SameSite=None: Allows cross-domain (Vercel ↔ Railway)
    - Path=/: Available on all routes
    - Max-age: 7 days session duration
    """
    frontend_url = settings.frontend_url
    
    if not code:
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?error=no_code"
        )
    
    try:
        # Exchange code for session with Supabase
        # Using the token exchange endpoint with code grant
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.supabase_url}/auth/v1/token?grant_type=authorization_code",
                json={
                    "code": code,
                    "redirect_uri": f"{str(request.base_url).rstrip('/')}/auth/callback",
                },
                headers={
                    "apikey": settings.supabase_anon_key,
                    "Content-Type": "application/json",
                },
                timeout=15.0,
            )
        
        if response.status_code != 200:
            error_detail = "auth_failed"
            try:
                error_data = response.json()
                error_detail = error_data.get("error_description", error_data.get("msg", "auth_failed"))
            except Exception:
                pass
            
            return RedirectResponse(
                url=f"{frontend_url}/dashboard?error={error_detail}"
            )
        
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", COOKIE_MAX_AGE)
        
        # Create redirect response to frontend
        response = RedirectResponse(
            url=f"{frontend_url}/dashboard?auth=success"
        )
        
        # Set main session cookie
        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            max_age=expires_in,
            httponly=True,
            secure=True,  # Required for SameSite=None
            samesite="none",
            path="/",
            domain=None,  # Let browser handle domain
        )
        
        # Set refresh token cookie (longer expiry)
        if refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=COOKIE_MAX_AGE * 4,  # 28 days
                httponly=True,
                secure=True,
                samesite="none",
                path="/",
                domain=None,
            )
        
        return response
        
    except httpx.RequestError as e:
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?error=network_error"
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Auth callback error: {e}")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?error=unknown"
        )


@router.post("/signout")
async def signout(request: Request, user: SupabaseUser = Depends(get_current_user_from_cookie)):
    """
    Sign out user by clearing session cookies.
    
    Clears both the session token and refresh token cookies.
    User is redirected to login page by frontend after receiving success.
    """
    response = Response(
        status_code=200, 
        content='{"status":"signed_out"}',
        media_type="application/json"
    )
    
    # Clear session cookies
    response.delete_cookie(COOKIE_NAME, path="/", samesite="none", secure=True)
    response.delete_cookie("refresh_token", path="/", samesite="none", secure=True)
    
    return response


@router.get("/status")
async def auth_status(user: Optional[SupabaseUser] = Depends(get_current_user_optional)):
    """
    Check authentication status.
    
    Returns user info if authenticated, empty response if not.
    Useful for frontend to check session validity.
    """
    if user is None:
        return {"authenticated": False}
    
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "email": user.email,
        }
    }
