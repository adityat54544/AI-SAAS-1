"""
Cloud Supabase client for the SaaS application.
This module provides a singleton Supabase client instance for database operations.
Handles test/CI environments gracefully with mock client fallback.
"""

import os
import logging
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Check if we're in a test/CI environment
def _is_test_environment() -> bool:
    """Check if running in test or CI environment."""
    env = os.environ.get("ENVIRONMENT", "").lower()
    return env in ("test", "ci", "testing") or os.environ.get("CI") == "true"


def _create_mock_supabase():
    """Create a mock Supabase client for testing."""
    mock = MagicMock()
    # Configure common operations
    mock.table.return_value.select.return_value.limit.return_value.execute.return_value = {
        "data": [{"id": "test-id"}]
    }
    mock.table.return_value.insert.return_value.execute.return_value = {
        "data": [{"id": "test-id", "created": True}]
    }
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = {
        "data": [{"id": "test-id", "updated": True}]
    }
    mock.table.return_value.delete.return_value.eq.return_value.execute.return_value = {
        "data": [{"id": "test-id", "deleted": True}]
    }
    mock.auth.sign_in_with_oauth.return_value = {"url": "https://github.com/login/oauth"}
    mock.auth.get_session.return_value = None
    mock.auth.sign_out.return_value = None
    return mock


def _create_supabase_client():
    """Create Supabase client with graceful fallback for tests."""
    # In test environment with missing credentials, use mock
    if _is_test_environment():
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            logger.info("Using mock Supabase client for test environment")
            return _create_mock_supabase()
    
    # In production/development, require real credentials
    if not SUPABASE_URL:
        if _is_test_environment():
            logger.warning("SUPABASE_URL not set, using mock client")
            return _create_mock_supabase()
        raise ValueError(
            "SUPABASE_URL environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    
    if not SUPABASE_SERVICE_ROLE_KEY:
        if _is_test_environment():
            logger.warning("SUPABASE_SERVICE_ROLE_KEY not set, using mock client")
            return _create_mock_supabase()
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    
    # Create real Supabase client
    try:
        from supabase.client import create_client
        logger.info(f"Connected to Supabase at {SUPABASE_URL}")
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        if _is_test_environment():
            logger.warning(f"Failed to create Supabase client: {e}. Using mock client.")
            return _create_mock_supabase()
        raise


# Create and export the Supabase client
supabase = _create_supabase_client()


def get_supabase_client():
    """
    Get the Supabase client instance.
    Useful for dependency injection in tests.
    """
    return supabase


def is_real_supabase() -> bool:
    """Check if we're using a real Supabase connection (not a mock)."""
    return not isinstance(supabase, MagicMock)