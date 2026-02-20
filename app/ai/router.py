"""
AI Router for provider selection and request routing.
Abstracts the choice of AI provider for flexibility.
"""

from typing import Any, Optional

from app.ai.provider import (
    AIProviderBase,
    AIProviderError,
    AnalysisRequest,
    AIResponse,
    CIConfigRequest,
    CIConfigResponse,
)
from app.ai.gemini_provider import GeminiProvider, get_gemini_provider
from app.config import settings


class AIRouter:
    """
    AI provider router.
    
    Routes AI requests to the configured provider.
    Supports dynamic provider switching for testing and future extensibility.
    """
    
    def __init__(self, provider: Optional[AIProviderBase] = None):
        """
        Initialize AI router.
        
        Args:
            provider: AI provider instance. If not provided, uses configured provider.
        """
        self._provider = provider
        self._provider_name = settings.ai_provider
    
    @property
    def provider(self) -> AIProviderBase:
        """Get the current AI provider instance."""
        if self._provider is None:
            self._provider = self._create_provider()
        return self._provider
    
    def _create_provider(self) -> AIProviderBase:
        """
        Create AI provider based on configuration.
        
        Returns:
            AI provider instance.
        
        Raises:
            AIProviderError: If provider creation fails.
        """
        provider_name = self._provider_name.lower()
        
        if provider_name == "gemini":
            return get_gemini_provider()
        
        # Future providers can be added here:
        # elif provider_name == "openrouter":
        #     return get_openrouter_provider()
        # elif provider_name == "openai":
        #     return get_openai_provider()
        
        raise AIProviderError(f"Unknown AI provider: {provider_name}")
    
    async def route_analysis(self, request: AnalysisRequest) -> AIResponse:
        """
        Route analysis request to the configured provider.
        
        Args:
            request: Analysis request with repository context.
        
        Returns:
            AIResponse from the provider.
        
        Raises:
            AIProviderError: If analysis fails.
        """
        return await self.provider.analyze(request)
    
    async def route_ci_generation(self, request: CIConfigRequest) -> CIConfigResponse:
        """
        Route CI/CD generation request to the configured provider.
        
        Args:
            request: CI config request.
        
        Returns:
            CIConfigResponse from the provider.
        
        Raises:
            AIProviderError: If generation fails.
        """
        return await self.provider.generate_ci_config(request)
    
    async def route_remediation(
        self,
        file_path: str,
        original_code: str,
        issue_description: str,
    ) -> dict[str, Any]:
        """
        Route remediation request to the configured provider.
        
        Args:
            file_path: Path to the file.
            original_code: Original code block.
            issue_description: Description of the issue.
        
        Returns:
            Remediation dictionary from the provider.
        
        Raises:
            AIProviderError: If generation fails.
        """
        return await self.provider.generate_remediation(
            file_path,
            original_code,
            issue_description,
        )
    
    def switch_provider(self, provider_name: str) -> None:
        """
        Switch to a different AI provider.
        
        Args:
            provider_name: Name of the provider to switch to.
        """
        self._provider_name = provider_name
        self._provider = None  # Reset to create new provider on next request
    
    def get_provider_name(self) -> str:
        """
        Get the current provider name.
        
        Returns:
            Provider name string.
        """
        return self._provider_name


# Singleton instance
_ai_router: Optional[AIRouter] = None


def get_ai_router() -> AIRouter:
    """Get the singleton AI router instance."""
    global _ai_router
    if _ai_router is None:
        _ai_router = AIRouter()
    return _ai_router