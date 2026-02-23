"""
Supabase token validation for FastAPI routes.
Validates Bearer tokens and HttpOnly cookies by calling Supabase Auth API.
"""

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import Any, Optional

from app.config import settings


# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


class SupabaseUser(BaseModel):
    """Supabase user model extracted from JWT token."""
    id: str
    email: Optional[str] = None
    role: Optional[str] = None
    aud: Optional[str] = None
    app_metadata: dict[str, Any] = {}
    user_metadata: dict[str, Any] = {}
    
    @property
    def display_name(self) -> Optional[str]:
        """Get display name from user metadata."""
        name = self.user_metadata.get("full_name")
        return name if isinstance(name, str) else self.user_metadata.get("name")
    
    @property
    def avatar_url(self) -> Optional[str]:
        """Get avatar URL from user metadata."""
        url = self.user_metadata.get("avatar_url")
        return url if isinstance(url, str) else self.user_metadata.get("picture")


async def validate_supabase_token(token: str) -> SupabaseUser:
    """
    Validate a Supabase JWT token by calling the Supabase Auth API.
    
    Args:
        token: The JWT access token to validate.
    
    Returns:
        SupabaseUser: The validated user object.
    
    Raises:
        HTTPException: If token validation fails.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    supabase_url = settings.supabase_url
    if not supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase URL not configured",
        )
    
    # Call Supabase Auth API to validate token
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.supabase_service_role_key,
                },
                timeout=10.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to reach authentication service: {str(e)}",
            )
    
    if response.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = response.json()
    
    return SupabaseUser(
        id=user_data.get("id"),
        email=user_data.get("email"),
        role=user_data.get("role"),
        aud=user_data.get("aud"),
        app_metadata=user_data.get("app_metadata", {}),
        user_metadata=user_data.get("user_metadata", {}),
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> SupabaseUser:
    """
    FastAPI dependency to get the current authenticated user.
    
    Validates the Bearer token from the Authorization header.
    
    Returns:
        SupabaseUser: The authenticated user.
    
    Raises:
        HTTPException: If not authenticated.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await validate_supabase_token(credentials.credentials)


async def get_current_user_from_cookie(
    request: Request,
) -> SupabaseUser:
    """
    FastAPI dependency to get the current authenticated user from HttpOnly cookie.
    
    This is the primary authentication method for frontend integration.
    Reads the session_token cookie set by /auth/callback endpoint.
    
    Returns:
        SupabaseUser: The authenticated user.
    
    Raises:
        HTTPException: If not authenticated.
    """
    # Read session token from cookie
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await validate_supabase_token(session_token)


async def get_current_user_optional(
    request: Request,
) -> Optional[SupabaseUser]:
    """
    FastAPI dependency to optionally get the current authenticated user from cookie.
    
    Returns None if not authenticated, instead of raising an exception.
    This is useful for optional authentication on public endpoints.
    
    Returns:
        Optional[SupabaseUser]: The authenticated user or None.
    """
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        return None
    
    try:
        return await validate_supabase_token(session_token)
    except HTTPException:
        return None


def require_user_id(request: Request, user: SupabaseUser = Depends(get_current_user)) -> str:
    """
    Dependency that extracts and returns the user ID.
    
    Use this when you only need the user ID, not the full user object.
    
    Returns:
        str: The authenticated user's ID.
    """
    return user.id