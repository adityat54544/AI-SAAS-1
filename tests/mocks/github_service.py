from unittest.mock import Mock, AsyncMock
import json

class MockGitHubService:
    """Mock GitHub service for deterministic testing."""
    
    def __init__(self):
        self.mock_repo_data = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "private": False,
            "html_url": "https://github.com/owner/test-repo",
            "description": "Test repository for unit testing",
            "language": "Python",
            "stargazers_count": 100,
        }
        self.mock_file_content = {"content": "test file content"}
        self.mock_branches = [
            {"name": "main", "commit": {"sha": "abc123"}},
            {"name": "develop", "commit": {"sha": "def456"}},
        ]
    
    async def get_repository(self, token: str, repo_name: str):
        """Mock get repository operation."""
        return self.mock_repo_data
    
    async def get_file_content(self, token: str, repo_name: str, path: str):
        """Mock get file content operation."""
        return self.mock_file_content
    
    async def get_branches(self, token: str, repo_name: str):
        """Mock get branches operation."""
        return self.mock_branches
    
    async def create_webhook(self, token: str, repo_name: str, config: dict):
        """Mock create webhook operation."""
        return {"id": 12345, "url": f"https://github.com/{repo_name}/hooks/12345"}
    
    async def list_webhooks(self, token: str, repo_name: str):
        """Mock list webhooks operation."""
        return []
    
    async def delete_webhook(self, token: str, repo_name: str, hook_id: int):
        """Mock delete webhook operation."""
        return True


class MockGitHubServiceFactory:
    """Factory for creating mock GitHub service instances."""
    
    @staticmethod
    def create() -> MockGitHubService:
        """Create a new mock GitHub service instance."""
        return MockGitHubService()
    
    @staticmethod
    def create_with_custom_data(repo_data: dict = None, file_content: dict = None) -> MockGitHubService:
        """Create a mock GitHub service with custom data."""
        service = MockGitHubService()
        if repo_data:
            service.mock_repo_data = repo_data
        if file_content:
            service.mock_file_content = file_content
        return service