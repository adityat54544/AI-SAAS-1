"""
Gemini AI provider implementation.
Uses Google Generative AI (Gemini 1.5 Flash) for repository analysis.
Handles test/CI environments gracefully with mock fallback.
"""

import json
import logging
import os
from typing import Any, Optional

from app.ai.provider import (
    AIProviderBase,
    AIProviderError,
    AnalysisRequest,
    AIResponse,
    CIConfigRequest,
    CIConfigResponse,
)
from app.ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    SECURITY_ANALYSIS_PROMPT,
    PERFORMANCE_ANALYSIS_PROMPT,
    CI_GENERATION_PROMPT,
    REMEDIATION_PROMPT,
)
from app.config import settings

logger = logging.getLogger(__name__)


def _is_test_environment() -> bool:
    """Check if running in test or CI environment."""
    env = os.environ.get("ENVIRONMENT", "").lower()
    return env in ("test", "ci", "testing") or os.environ.get("CI") == "true"


class GeminiProvider(AIProviderBase):
    """
    Gemini AI provider implementation.
    
    Uses Google's Gemini 1.5 Flash model for fast and efficient
    repository analysis, CI/CD generation, and remediation suggestions.
    
    Falls back to mock responses in test environments when API key is unavailable.
    """
    
    PROVIDER_NAME = "gemini"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google AI API key.
            model_name: Model name to use (default: gemini-1.5-flash).
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.ai_model
        self._is_mock = False
        
        if not self.api_key:
            if _is_test_environment():
                logger.info("Using mock Gemini provider for test environment")
                self._is_mock = True
                self._model = None
                return
            raise AIProviderError("Gemini API key is required")
        
        # Check if this is a test API key
        if self.api_key.startswith("test-"):
            self._is_mock = True
            self._model = None
            return
        
        # Configure the client
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                },
            )
        except Exception as e:
            if _is_test_environment():
                logger.warning(f"Failed to initialize Gemini: {e}. Using mock provider.")
                self._is_mock = True
                self._model = None
            else:
                raise AIProviderError(f"Failed to initialize Gemini: {e}")
    
    async def analyze(self, request: AnalysisRequest) -> AIResponse:
        """
        Perform repository analysis using Gemini.
        
        Args:
            request: Analysis request with repository context.
        
        Returns:
            AIResponse with analysis results.
        
        Raises:
            AIProviderError: If analysis fails.
        """
        try:
            # Build context
            context = self.build_context(
                request.repository_context,
                request.file_contents,
            )
            
            # Select appropriate prompt based on analysis type
            if request.analysis_type == "security":
                system_prompt = SECURITY_ANALYSIS_PROMPT
            elif request.analysis_type == "performance":
                system_prompt = PERFORMANCE_ANALYSIS_PROMPT
            else:
                system_prompt = ANALYSIS_SYSTEM_PROMPT
            
            # Add custom prompt if provided
            if request.custom_prompt:
                system_prompt = f"{system_prompt}\n\n{request.custom_prompt}"
            
            # Build the full prompt
            full_prompt = f"""{system_prompt}

Analyze the following repository context and provide a comprehensive analysis:

{context}

Provide your response in the following JSON format:
{{
    "summary": "Brief summary of the analysis",
    "overall_score": <number between 0-100>,
    "recommendations": [
        {{
            "category": "security|performance|code_quality|ci_cd|dependencies",
            "severity": "critical|high|medium|low|info",
            "title": "Short title",
            "description": "Detailed description",
            "file_path": "path/to/file (optional)",
            "line_number": <line number (optional)>,
            "suggested_fix": "Suggested fix (optional)"
        }}
    ],
    "security_score": <0-100>,
    "performance_score": <0-100>,
    "code_quality_score": <0-100>,
    "ci_cd_score": <0-100>,
    "dependencies_score": <0-100>
}}
"""
            
            # Call Gemini API
            response = await self._generate_async(full_prompt)
            
            # Parse response
            content = response.text
            structured = self.parse_structured_response(content)
            
            # Estimate tokens (Gemini doesn't always return this)
            tokens_used = self._estimate_tokens(full_prompt, content)
            
            return AIResponse(
                content=content,
                model_used=self.model_name,
                tokens_used=tokens_used,
                provider=self.PROVIDER_NAME,
                structured_results=structured,
            )
        
        except Exception as e:
            raise AIProviderError(f"Gemini analysis failed: {e}")
    
    async def generate_ci_config(self, request: CIConfigRequest) -> CIConfigResponse:
        """
        Generate CI/CD configuration using Gemini.
        
        Args:
            request: CI config request with repository context and requirements.
        
        Returns:
            CIConfigResponse with generated configuration.
        
        Raises:
            AIProviderError: If generation fails.
        """
        try:
            # Build context
            context = self.build_context(request.repository_context)
            
            # Map platform to proper name
            platform_names = {
                "github_actions": "GitHub Actions",
                "gitlab_ci": "GitLab CI",
                "circleci": "CircleCI",
                "jenkins": "Jenkins",
            }
            platform = platform_names.get(
                request.target_platform,
                request.target_platform,
            )
            
            full_prompt = f"""{CI_GENERATION_PROMPT}

Generate a {platform} configuration for the following repository:

{context}

Requirements: {', '.join(request.requirements) if request.requirements else 'Standard CI/CD pipeline'}

Provide your response in the following JSON format:
{{
    "config_yaml": "The complete YAML configuration",
    "explanations": [
        "Explanation of step 1",
        "Explanation of step 2",
        ...
    ]
}}
"""
            
            # Call Gemini API
            response = await self._generate_async(full_prompt)
            content = response.text
            
            # Parse response
            structured = self.parse_structured_response(content)
            
            if not structured:
                # Fallback: extract YAML from response
                config_yaml = self._extract_yaml(content)
                explanations = self._extract_explanations(content)
            else:
                config_yaml = structured.get("config_yaml", "")
                explanations = structured.get("explanations", [])
            
            return CIConfigResponse(
                config_yaml=config_yaml,
                explanations=explanations,
                provider=self.PROVIDER_NAME,
            )
        
        except Exception as e:
            raise AIProviderError(f"Gemini CI generation failed: {e}")
    
    async def generate_remediation(
        self,
        file_path: str,
        original_code: str,
        issue_description: str,
    ) -> dict[str, Any]:
        """
        Generate code remediation suggestion using Gemini.
        
        Args:
            file_path: Path to the file.
            original_code: Original code block.
            issue_description: Description of the issue to fix.
        
        Returns:
            Dictionary with suggested_code and explanation.
        
        Raises:
            AIProviderError: If generation fails.
        """
        try:
            full_prompt = f"""{REMEDIATION_PROMPT}

File: {file_path}

Original Code:
```
{original_code}
```

Issue: {issue_description}

Provide your response in the following JSON format:
{{
    "suggested_code": "The fixed code",
    "explanation": "Explanation of the changes made"
}}
"""
            
            response = await self._generate_async(full_prompt)
            content = response.text
            
            # Parse response
            structured = self.parse_structured_response(content)
            
            if structured:
                return {
                    "suggested_code": structured.get("suggested_code", original_code),
                    "explanation": structured.get("explanation", "No explanation provided"),
                }
            
            # Fallback: extract code from response
            suggested_code = self._extract_code(content)
            
            return {
                "suggested_code": suggested_code or original_code,
                "explanation": content,
            }
        
        except Exception as e:
            raise AIProviderError(f"Gemini remediation failed: {e}")
    
    async def _generate_async(self, prompt: str) -> Any:
        """
        Generate content asynchronously.
        
        Args:
            prompt: The prompt to send to Gemini.
        
        Returns:
            Gemini response object or mock response.
        """
        # Handle mock mode
        if self._is_mock or self._model is None:
            return self._generate_mock_response(prompt)
        
        # Use synchronous API in async context
        # Note: google-generativeai has limited async support
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self._model.generate_content,
                prompt,
            )
        return result
    
    def _generate_mock_response(self, prompt: str) -> Any:
        """
        Generate a mock response for testing.
        
        Args:
            prompt: The input prompt.
        
        Returns:
            Mock response object.
        """
        # Create a simple mock response object
        class MockResponse:
            def __init__(self, text: str):
                self.text = text
        
        # Generate appropriate mock response based on prompt content
        if "analysis" in prompt.lower() or "analyze" in prompt.lower():
            mock_content = json.dumps({
                "summary": "Mock analysis for testing",
                "overall_score": 85,
                "recommendations": [
                    {
                        "category": "code_quality",
                        "severity": "info",
                        "title": "Test recommendation",
                        "description": "This is a mock recommendation for testing"
                    }
                ],
                "security_score": 90,
                "performance_score": 85,
                "code_quality_score": 80,
                "ci_cd_score": 75,
                "dependencies_score": 85
            })
        elif "ci" in prompt.lower() or "pipeline" in prompt.lower():
            mock_content = json.dumps({
                "config_yaml": "# Mock CI configuration\nname: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4",
                "explanations": ["Mock CI configuration for testing"]
            })
        else:
            mock_content = "Mock response for testing purposes"
        
        return MockResponse(mock_content)
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """
        Estimate token usage.
        
        Args:
            prompt: The input prompt.
            response: The output response.
        
        Returns:
            Estimated total tokens.
        """
        # Rough estimation: ~4 characters per token
        prompt_tokens = len(prompt) // 4
        response_tokens = len(response) // 4
        return prompt_tokens + response_tokens
    
    def _extract_yaml(self, content: str) -> str:
        """Extract YAML content from response."""
        # Try to find YAML in code blocks
        yaml_markers = ["```yaml", "```yml", "```"]
        
        for marker in yaml_markers:
            if marker in content:
                start = content.find(marker) + len(marker)
                end = content.find("```", start)
                if end > start:
                    return content[start:end].strip()
        
        # Return empty if no YAML found
        return ""
    
    def _extract_code(self, content: str) -> Optional[str]:
        """Extract code content from response."""
        if "```" in content:
            start = content.find("```")
            # Skip language identifier if present
            newline_after_start = content.find("\n", start)
            if newline_after_start > start:
                start = newline_after_start + 1
            else:
                start += 3
            
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()
        
        return None
    
    def _extract_explanations(self, content: str) -> list[str]:
        """Extract explanations from response."""
        explanations = []
        
        # Try to find numbered or bulleted lists
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("- ", "* ", "• ")):
                explanations.append(line[2:])
            elif len(line) > 2 and line[0].isdigit() and line[1] in ".)":
                explanations.append(line[2:].strip())
        
        return explanations


# Singleton instance
_gemini_provider: Optional[GeminiProvider] = None


def get_gemini_provider() -> GeminiProvider:
    """Get the singleton Gemini provider instance."""
    global _gemini_provider
    if _gemini_provider is None:
        _gemini_provider = GeminiProvider()
    return _gemini_provider