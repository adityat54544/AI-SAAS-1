"""
GitHub API integration service.
Handles OAuth, repository metadata, and webhook management.
"""

import base64
import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import urlencode

import httpx
from github import Github, GithubException
from github.Repository import Repository

from app.config import settings
from app.services.encryption_service import get_encryption_service


class GitHubError(Exception):
    """Raised when GitHub API operations fail."""
    pass


class GitHubRateLimitError(GitHubError):
    """Raised when GitHub API rate limit is exceeded."""
    pass


class GitHubAuthError(GitHubError):
    """Raised when GitHub authentication fails."""
    pass


class RepositoryMetadata:
    """Repository metadata container."""
    
    def __init__(
        self,
        github_id: int,
        name: str,
        full_name: str,
        description: Optional[str],
        html_url: str,
        language: Optional[str],
        stargazers_count: int,
        forks_count: int,
        is_private: bool,
        default_branch: str,
        topics: list[str],
        license_name: Optional[str],
        created_at: str,
        updated_at: str,
        pushed_at: Optional[str],
        open_issues_count: int,
        size: int,
    ):
        self.github_id = github_id
        self.name = name
        self.full_name = full_name
        self.description = description
        self.html_url = html_url
        self.language = language
        self.stargazers_count = stargazers_count
        self.forks_count = forks_count
        self.is_private = is_private
        self.default_branch = default_branch
        self.topics = topics
        self.license_name = license_name
        self.created_at = created_at
        self.updated_at = updated_at
        self.pushed_at = pushed_at
        self.open_issues_count = open_issues_count
        self.size = size
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "github_id": self.github_id,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "html_url": self.html_url,
            "language": self.language,
            "stargazers_count": self.stargazers_count,
            "forks_count": self.forks_count,
            "is_private": self.is_private,
            "default_branch": self.default_branch,
            "topics": self.topics,
            "license": self.license_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "pushed_at": self.pushed_at,
            "open_issues_count": self.open_issues_count,
            "size": self.size,
        }


class RateLimitInfo:
    """GitHub API rate limit information."""
    
    def __init__(self, limit: int, remaining: int, reset_time: int):
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time  # Unix timestamp
    
    @property
    def reset_in_seconds(self) -> int:
        """Seconds until rate limit resets."""
        return max(0, self.reset_time - int(time.time()))
    
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted."""
        return self.remaining <= 0


class GitHubService:
    """
    GitHub API integration service.
    
    Handles OAuth flow, repository management, and webhook operations.
    """
    
    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        """
        Initialize GitHub service.
        
        Args:
            client_id: GitHub OAuth client ID.
            client_secret: GitHub OAuth client secret.
            redirect_uri: OAuth redirect URI.
        """
        self.client_id = client_id or settings.github_client_id
        self.client_secret = client_secret or settings.github_client_secret
        self.redirect_uri = redirect_uri or settings.github_redirect_uri
        self._encryption_service = get_encryption_service()
    
    def get_oauth_url(self, state: str, scopes: Optional[list[str]] = None) -> str:
        """
        Generate GitHub OAuth authorization URL.
        
        Args:
            state: Random state string for CSRF protection.
            scopes: List of OAuth scopes to request.
        
        Returns:
            Full OAuth authorization URL.
        """
        if scopes is None:
            scopes = ["repo", "user:email", "read:org"]
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "response_type": "code",
        }
        
        return f"{self.GITHUB_AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """
        Exchange OAuth authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback.
        
        Returns:
            Token response containing access_token, token_type, scope, etc.
        
        Raises:
            GitHubAuthError: If token exchange fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GITHUB_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            
            if response.status_code != 200:
                raise GitHubAuthError(f"Token exchange failed: {response.text}")
            
            data = response.json()
            
            if "error" in data:
                raise GitHubAuthError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")
            
            return data
    
    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: GitHub refresh token.
        
        Returns:
            New token response.
        
        Raises:
            GitHubAuthError: If refresh fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GITHUB_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Accept": "application/json"},
            )
            
            if response.status_code != 200:
                raise GitHubAuthError(f"Token refresh failed: {response.text}")
            
            data = response.json()
            
            if "error" in data:
                raise GitHubAuthError(f"Token refresh error: {data.get('error_description', data['error'])}")
            
            return data
    
    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Get authenticated user information.
        
        Args:
            access_token: GitHub access token.
        
        Returns:
            User information dictionary.
        
        Raises:
            GitHubAuthError: If request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code == 401:
                raise GitHubAuthError("Invalid or expired access token")
            
            if response.status_code != 200:
                raise GitHubError(f"Failed to get user info: {response.text}")
            
            return response.json()
    
    async def get_user_emails(self, access_token: str) -> list[dict[str, Any]]:
        """
        Get authenticated user's email addresses.
        
        Args:
            access_token: GitHub access token.
        
        Returns:
            List of email objects.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code != 200:
                return []
            
            return response.json()
    
    async def get_user_repositories(
        self,
        access_token: str,
        page: int = 1,
        per_page: int = 100,
        sort: str = "updated",
        affiliation: str = "owner,collaborator,organization_member",
    ) -> list[dict[str, Any]]:
        """
        Get repositories accessible to the authenticated user.
        
        Args:
            access_token: GitHub access token.
            page: Page number.
            per_page: Results per page (max 100).
            sort: Sort field (created, updated, pushed, full_name).
            affiliation: Repository affiliation filter.
        
        Returns:
            List of repository objects.
        
        Raises:
            GitHubError: If request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/user/repos",
                params={
                    "page": page,
                    "per_page": per_page,
                    "sort": sort,
                    "affiliation": affiliation,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code == 401:
                raise GitHubAuthError("Invalid or expired access token")
            
            if response.status_code == 403:
                raise GitHubRateLimitError("Rate limit exceeded")
            
            if response.status_code != 200:
                raise GitHubError(f"Failed to get repositories: {response.text}")
            
            return response.json()
    
    async def get_repository_metadata(
        self,
        owner: str,
        repo: str,
        access_token: str,
    ) -> RepositoryMetadata:
        """
        Get detailed metadata for a specific repository.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            access_token: GitHub access token.
        
        Returns:
            RepositoryMetadata object.
        
        Raises:
            GitHubError: If request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code == 404:
                raise GitHubError(f"Repository {owner}/{repo} not found")
            
            if response.status_code == 401:
                raise GitHubAuthError("Invalid or expired access token")
            
            if response.status_code != 200:
                raise GitHubError(f"Failed to get repository: {response.text}")
            
            data = response.json()
            
            return RepositoryMetadata(
                github_id=data["id"],
                name=data["name"],
                full_name=data["full_name"],
                description=data.get("description"),
                html_url=data["html_url"],
                language=data.get("language"),
                stargazers_count=data.get("stargazers_count", 0),
                forks_count=data.get("forks_count", 0),
                is_private=data.get("private", False),
                default_branch=data.get("default_branch", "main"),
                topics=data.get("topics", []),
                license_name=data.get("license", {}).get("name") if data.get("license") else None,
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
                pushed_at=data.get("pushed_at"),
                open_issues_count=data.get("open_issues_count", 0),
                size=data.get("size", 0),
            )
    
    async def create_webhook(
        self,
        owner: str,
        repo: str,
        access_token: str,
        webhook_url: str,
        events: Optional[list[str]] = None,
        secret: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a webhook for a repository.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            access_token: GitHub access token.
            webhook_url: URL to receive webhook payloads.
            events: List of event types to subscribe to.
            secret: Webhook secret for signature verification.
        
        Returns:
            Webhook configuration.
        
        Raises:
            GitHubError: If webhook creation fails.
        """
        if events is None:
            events = ["push", "pull_request", "issues", "repository"]
        
        if secret is None:
            secret = settings.github_webhook_secret
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/hooks",
                json={
                    "name": "web",
                    "active": True,
                    "events": events,
                    "config": {
                        "url": webhook_url,
                        "content_type": "json",
                        "secret": secret,
                        "insecure_ssl": "0" if settings.is_production() else "1",
                    },
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code == 401:
                raise GitHubAuthError("Invalid or expired access token")
            
            if response.status_code == 403:
                raise GitHubError("Insufficient permissions to create webhook")
            
            if response.status_code not in [200, 201]:
                raise GitHubError(f"Failed to create webhook: {response.text}")
            
            return response.json()
    
    async def delete_webhook(
        self,
        owner: str,
        repo: str,
        hook_id: int,
        access_token: str,
    ) -> bool:
        """
        Delete a webhook from a repository.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            hook_id: Webhook ID.
            access_token: GitHub access token.
        
        Returns:
            True if deletion was successful.
        
        Raises:
            GitHubError: If deletion fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/hooks/{hook_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code == 204:
                return True
            
            if response.status_code == 404:
                return False  # Webhook doesn't exist
            
            raise GitHubError(f"Failed to delete webhook: {response.text}")
    
    async def get_rate_limit(self, access_token: str) -> RateLimitInfo:
        """
        Get current rate limit status.
        
        Args:
            access_token: GitHub access token.
        
        Returns:
            RateLimitInfo object.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/rate_limit",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code != 200:
                # Return default rate limit if we can't fetch it
                return RateLimitInfo(limit=5000, remaining=5000, reset_time=int(time.time()) + 3600)
            
            data = response.json()
            core = data.get("resources", {}).get("core", {})
            
            return RateLimitInfo(
                limit=core.get("limit", 5000),
                remaining=core.get("remaining", 5000),
                reset_time=core.get("reset", int(time.time()) + 3600),
            )
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: Optional[str] = None,
    ) -> bool:
        """
        Verify GitHub webhook signature.
        
        Args:
            payload: Raw request payload bytes.
            signature: X-Hub-Signature-256 header value.
            secret: Webhook secret (uses settings if not provided).
        
        Returns:
            True if signature is valid.
        """
        secret = secret or settings.github_webhook_secret
        
        if not secret:
            return False
        
        if not signature.startswith("sha256="):
            return False
        
        expected_signature = signature[7:]  # Remove 'sha256=' prefix
        
        computed_signature = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, computed_signature)
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a GitHub access token for storage.
        
        Args:
            token: Plain-text access token.
        
        Returns:
            Encrypted token string.
        """
        return self._encryption_service.encrypt(token)
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a stored GitHub access token.
        
        Args:
            encrypted_token: Encrypted token string.
        
        Returns:
            Plain-text access token.
        """
        return self._encryption_service.decrypt(encrypted_token)


# Singleton instance
_github_service: Optional[GitHubService] = None


def get_github_service() -> GitHubService:
    """
    Get the singleton GitHub service instance.
    
    Returns:
        GitHubService instance.
    """
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service