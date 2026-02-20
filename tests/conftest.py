"""
Pytest configuration and fixtures.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


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
        yield mock


@pytest.fixture
def client(mock_settings):
    """Create a test client."""
    from app.main import app
    return TestClient(app)