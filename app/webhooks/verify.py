"""
Webhook Verification Utility.

Provides secure verification of GitHub webhooks using X-Hub-Signature-256.
"""

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)


class WebhookVerificationError(Exception):
    """Raised when webhook verification fails."""
    def __init__(self, message: str, reason: str = "invalid_signature"):
        super().__init__(message)
        self.reason = reason


def verify_github_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (format: sha256=<hex>)
        secret: Webhook secret
        
    Returns:
        True if signature is valid
        
    Raises:
        WebhookVerificationError: If signature is invalid or missing
    """
    if not signature:
        raise WebhookVerificationError(
            "Missing X-Hub-Signature-256 header",
            reason="missing_signature"
        )
    
    if not secret:
        raise WebhookVerificationError(
            "Webhook secret not configured",
            reason="configuration_error"
        )
    
    # Parse signature format: sha256=<hex_digest>
    if not signature.startswith("sha256="):
        raise WebhookVerificationError(
            "Invalid signature format. Expected sha256=<hex>",
            reason="invalid_format"
        )
    
    expected_sig = signature[7:]  # Remove 'sha256=' prefix
    
    # Compute HMAC-SHA256
    computed_sig = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(computed_sig, expected_sig):
        raise WebhookVerificationError(
            "Webhook signature verification failed",
            reason="invalid_signature"
        )
    
    return True


def verify_webhook_request(
    request: Request,
    payload: bytes,
) -> bool:
    """
    Verify a webhook request from the FastAPI request object.
    
    Args:
        request: FastAPI Request object
        payload: Raw request body bytes
        
    Returns:
        True if verification succeeds
        
    Raises:
        HTTPException: If verification fails
    """
    # Get signature header
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Get webhook secret from settings
    secret = getattr(settings, 'github_webhook_secret', None)
    
    if not secret:
        logger.error("GitHub webhook secret not configured")
        raise HTTPException(
            status_code=500,
            detail="Webhook verification not configured"
        )
    
    try:
        verify_github_signature(payload, signature, secret)
        return True
    except WebhookVerificationError as e:
        logger.warning(
            "Webhook verification failed",
            extra={
                "reason": e.reason,
                "path": request.url.path,
                "method": request.method,
            }
        )
        raise HTTPException(
            status_code=401,
            detail=f"Webhook verification failed: {e.reason}"
        )


class WebhookVerifier:
    """
    Webhook verifier class for more complex verification scenarios.
    
    Features:
    - Signature verification
    - Event type validation
    - Delivery ID tracking (for replay protection)
    """
    
    def __init__(self, secret: Optional[str] = None):
        """Initialize the webhook verifier."""
        self.secret = secret or getattr(settings, 'github_webhook_secret', None)
        self._seen_deliveries: set = set()
    
    def verify(
        self,
        payload: bytes,
        signature: str,
        delivery_id: Optional[str] = None,
    ) -> bool:
        """
        Verify a webhook request.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header
            delivery_id: Optional X-GitHub-Delivery header for replay protection
            
        Returns:
            True if verification succeeds
        """
        if not self.secret:
            raise WebhookVerificationError(
                "Webhook secret not configured",
                reason="configuration_error"
            )
        
        # Check for replay attacks if delivery ID provided
        if delivery_id:
            if delivery_id in self._seen_deliveries:
                raise WebhookVerificationError(
                    "Duplicate webhook delivery detected",
                    reason="replay_attack"
                )
            self._seen_deliveries.add(delivery_id)
            # Limit memory usage by cleaning old delivery IDs
            if len(self._seen_deliveries) > 10000:
                self._seen_deliveries.clear()
        
        return verify_github_signature(payload, signature, self.secret)
    
    def verify_event_type(
        self,
        event_type: str,
        allowed_events: Optional[list] = None,
    ) -> bool:
        """
        Verify the event type is allowed.
        
        Args:
            event_type: X-GitHub-Event header value
            allowed_events: List of allowed event types (None = all allowed)
            
        Returns:
            True if event type is allowed
        """
        if allowed_events is None:
            return True
        
        if event_type not in allowed_events:
            raise WebhookVerificationError(
                f"Event type '{event_type}' not allowed",
                reason="invalid_event_type"
            )
        
        return True


def create_signature(payload: bytes, secret: str) -> str:
    """
    Create a webhook signature for testing purposes.
    
    Args:
        payload: Payload to sign
        secret: Webhook secret
        
    Returns:
        Signature in the format: sha256=<hex>
    """
    signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


# Convenience functions for common webhook events
def is_push_event(request: Request) -> bool:
    """Check if the request is a push event."""
    return request.headers.get("X-GitHub-Event") == "push"


def is_pull_request_event(request: Request) -> bool:
    """Check if the request is a pull request event."""
    return request.headers.get("X-GitHub-Event") == "pull_request"


def get_event_type(request: Request) -> str:
    """Get the webhook event type."""
    return request.headers.get("X-GitHub-Event", "")


def get_delivery_id(request: Request) -> str:
    """Get the webhook delivery ID."""
    return request.headers.get("X-GitHub-Delivery", "")