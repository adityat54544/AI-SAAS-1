"""
Pytest configuration and fixtures.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient


# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires Redis)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis connection"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection based on markers.
    
    Integration tests requiring Redis are skipped if:
    - No REDIS_URL is configured
    - No SUPABASE_REDIS_URL is configured
    """
    redis_url = os.environ.get("REDIS_URL") or os.environ.get("SUPABASE_REDIS_URL")
    
    skip_integration = pytest.mark.skip(
        reason="Skipping integration test: No Redis URL configured. Set REDIS_URL or SUPABASE_REDIS_URL."
    )
    
    for item in items:
        # Skip integration tests if no Redis is available
        if "integration" in item.keywords and not redis_url:
            item.add_marker(skip_integration)


@pytest.fixture
def redis_url():
    """Get the configured Redis URL for testing."""
    return os.environ.get("REDIS_URL") or os.environ.get("SUPABASE_REDIS_URL") or "redis://localhost:6379/0"


@pytest.fixture
def mock_redis():
    """
    Mock Redis client for unit tests.
    
    Use this fixture when testing code that uses Redis but you don't want
    to require a real Redis connection.
    """
    mock = MagicMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.lpush.return_value = 1
    mock.rpush.return_value = 1
    mock.lrange.return_value = []
    mock.llen.return_value = 0
    mock.incrby.return_value = 1
    mock.expire.return_value = True
    return mock


@pytest.fixture
def mock_redis_async():
    """
    Mock async Redis client for unit tests.
    
    Use this fixture when testing async code that uses Redis.
    """
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.lpush = AsyncMock(return_value=1)
    mock.rpush = AsyncMock(return_value=1)
    mock.lrange = AsyncMock(return_value=[])
    mock.llen = AsyncMock(return_value=0)
    mock.incrby = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch("app.supabase_client.supabase") as mock:
        mock.table.return_value.select.return_value.limit.return_value.execute.return_value = {
            "data": [{"id": "test-id"}]
        }
        yield mock


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch("app.config.settings") as mock:
        mock.app_name = "AutoDevOps AI Platform"
        mock.app_version = "1.0.0"
        mock.environment = "test"
        mock.is_development.return_value = True
        mock.is_production.return_value = False
        mock.cors_origins_list = ["http://localhost:3000"]
        mock.redis_url = "redis://localhost:6379/0"
        mock.supabase_redis_url = None
        mock.effective_redis_url = "redis://localhost:6379/0"
        yield mock


@pytest.fixture
def client(mock_settings):
    """Create a test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def client_with_mocked_redis(mock_settings, mock_redis):
    """Create a test client with mocked Redis."""
    with patch("redis.from_url", return_value=mock_redis):
        from app.main import app
        return TestClient(app)
