"""
AI Provider abstract base class.
Defines the interface for AI provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class AIProviderError(Exception):
    """Raised when AI provider operations fail."""
    pass


class AnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repository_context: dict[str, Any]
    file_contents: Optional[list[dict[str, str]]] = None
    analysis_type: str = "full"
    custom_prompt: Optional[str] = None


class AIResponse(BaseModel):
    """Response model for AI operations."""
    content: str
    model_used: str
    tokens_used: int
    provider: str
    structured_results: Optional[dict[str, Any]] = None


class CIConfigRequest(BaseModel):
    """Request model for CI/CD configuration generation."""
    repository_context: dict[str, Any]
    target_platform: str = "github_actions"
    requirements: list[str] = []


class CIConfigResponse(BaseModel):
    """Response model for CI/CD configuration generation."""
    config_yaml: str
    explanations: list[str]
    provider: str


class AIProviderBase(ABC):
    """
    Abstract base class for AI providers.
    
    Defines the interface that all AI provider implementations must follow.
    Supports analysis, CI/CD generation, and remediation suggestions.
    """
    
    PROVIDER_NAME: str = "base"
    
    @abstractmethod
    async def analyze(self, request: AnalysisRequest) -> AIResponse:
        """
        Perform repository analysis.
        
        Args:
            request: Analysis request with repository context.
        
        Returns:
            AIResponse with analysis results.
        
        Raises:
            AIProviderError: If analysis fails.
        """
        pass
    
    @abstractmethod
    async def generate_ci_config(self, request: CIConfigRequest) -> CIConfigResponse:
        """
        Generate CI/CD configuration.
        
        Args:
            request: CI config request with repository context and requirements.
        
        Returns:
            CIConfigResponse with generated configuration.
        
        Raises:
            AIProviderError: If generation fails.
        """
        pass
    
    @abstractmethod
    async def generate_remediation(
        self,
        file_path: str,
        original_code: str,
        issue_description: str,
    ) -> dict[str, Any]:
        """
        Generate code remediation suggestion.
        
        Args:
            file_path: Path to the file.
            original_code: Original code block.
            issue_description: Description of the issue to fix.
        
        Returns:
            Dictionary with suggested_code and explanation.
        
        Raises:
            AIProviderError: If generation fails.
        """
        pass
    
    def build_context(
        self,
        repository_context: dict[str, Any],
        file_contents: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        Build context string for AI prompt.
        
        Args:
            repository_context: Repository metadata and structure.
            file_contents: Optional list of file contents to include.
        
        Returns:
            Formatted context string.
        """
        context_parts = []
        
        # Add repository metadata
        if "name" in repository_context:
            context_parts.append(f"Repository: {repository_context['name']}")
        
        if "language" in repository_context:
            context_parts.append(f"Primary Language: {repository_context['language']}")
        
        if "description" in repository_context:
            context_parts.append(f"Description: {repository_context['description']}")
        
        if "structure" in repository_context:
            context_parts.append(f"Structure:\n{repository_context['structure']}")
        
        if "dependencies" in repository_context:
            context_parts.append(f"Dependencies: {repository_context['dependencies']}")
        
        # Add file contents if provided
        if file_contents:
            context_parts.append("\n--- File Contents ---")
            for file_info in file_contents[:10]:  # Limit to 10 files
                path = file_info.get("path", "unknown")
                content = file_info.get("content", "")
                context_parts.append(f"\n### {path}\n```\n{content[:2000]}\n```")  # Limit content
        
        return "\n".join(context_parts)
    
    def parse_structured_response(
        self,
        content: str,
        format_type: str = "json",
    ) -> Optional[dict[str, Any]]:
        """
        Parse structured response from AI output.
        
        Args:
            content: Raw AI response content.
            format_type: Expected format type (json, yaml, etc.).
        
        Returns:
            Parsed dictionary or None if parsing fails.
        """
        import json
        
        if format_type == "json":
            # Try to extract JSON from the response
            try:
                # Try direct parse first
                return json.loads(content)
            except json.JSONDecodeError:
                pass
            
            # Try to find JSON in code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    try:
                        return json.loads(content[start:end].strip())
                    except json.JSONDecodeError:
                        pass
            
            # Try to find any JSON-like structure
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end + 1])
                except json.JSONDecodeError:
                    pass
        
        return None