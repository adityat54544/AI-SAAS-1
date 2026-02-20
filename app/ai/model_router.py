"""
AI Model Router - Intelligent Model Selection.

Selects the appropriate AI model based on task complexity and user quota.
"""

from typing import Optional, Tuple

from app.ai.token_estimator import TokenEstimator, estimate_complexity
from app.config import settings


class ModelRouter:
    """
    Intelligent model router for AI requests.
    
    Selects between Gemini 1.5 Flash (fast, cheap) and Gemini 2.5 Pro
    (capable, expensive) based on task requirements.
    """
    
    # Model configurations
    MODELS = {
        "gemini-1.5-flash": {
            "max_tokens": 1000000,
            "cost_per_1k_input": 0.00001875,
            "cost_per_1k_output": 0.000075,
            "supports_vision": True,
            "supports_code": True,
            "description": "Fast and efficient for most tasks",
        },
        "gemini-1.5-pro": {
            "max_tokens": 2000000,
            "cost_per_1k_input": 0.00125,
            "cost_per_1k_output": 0.005,
            "supports_vision": True,
            "supports_code": True,
            "description": "More capable for complex reasoning",
        },
        "gemini-2.5-pro": {
            "max_tokens": 2000000,
            "cost_per_1k_input": 0.00125,
            "cost_per_1k_output": 0.005,
            "supports_vision": True,
            "supports_code": True,
            "description": "Most capable for complex tasks",
        },
    }
    
    # Complexity thresholds for model selection
    COMPLEXITY_THRESHOLD_PRO = 0.7
    
    def __init__(self):
        """Initialize the model router."""
        self.default_model = getattr(settings, 'ai_model_default', 'gemini-1.5-flash')
        self.estimator = TokenEstimator()
    
    def select_model(
        self,
        task_type: str,
        content: str,
        user_tier: str = "free",
        estimated_tokens: Optional[int] = None,
    ) -> Tuple[str, dict]:
        """
        Select the appropriate model for a task.
        
        Args:
            task_type: Type of task (analysis, ci_generation, chat, etc.)
            content: Content to process
            user_tier: User subscription tier
            estimated_tokens: Pre-calculated token estimate
            
        Returns:
            Tuple of (model_name, model_config)
        """
        # Get complexity score
        complexity = estimate_complexity(content)
        
        # Estimate tokens if not provided
        if estimated_tokens is None:
            estimated_tokens = self.estimator.estimate(content)
        
        # Check if content is code
        is_code = task_type in ["analysis", "ci_generation"]
        if is_code:
            estimated_tokens = self.estimator.estimate(content, is_code=True)
        
        # Select model based on rules
        model = self._select_by_rules(
            task_type=task_type,
            complexity=complexity,
            user_tier=user_tier,
            estimated_tokens=estimated_tokens,
        )
        
        return model, self.MODELS.get(model, self.MODELS[self.default_model])
    
    def _select_by_rules(
        self,
        task_type: str,
        complexity: float,
        user_tier: str,
        estimated_tokens: int,
    ) -> str:
        """
        Apply selection rules to choose a model.
        
        Args:
            task_type: Type of task
            complexity: Complexity score (0-1)
            user_tier: User subscription tier
            estimated_tokens: Estimated token count
            
        Returns:
            Selected model name
        """
        # Rule 1: Free tier always uses flash
        if user_tier == "free":
            return "gemini-1.5-flash"
        
        # Rule 2: Simple tasks always use flash
        if complexity < 0.3:
            return "gemini-1.5-flash"
        
        # Rule 3: Large token requests use flash (cost control)
        if estimated_tokens > 50000:
            return "gemini-1.5-flash"
        
        # Rule 4: High complexity for pro/enterprise uses pro model
        if complexity >= self.COMPLEXITY_THRESHOLD_PRO and user_tier in ["pro", "enterprise"]:
            return "gemini-2.5-pro"
        
        # Rule 5: CI generation for pro tier can use pro model
        if task_type == "ci_generation" and user_tier in ["pro", "enterprise"]:
            return "gemini-1.5-pro"
        
        # Default: use flash model
        return self.default_model
    
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
    ) -> float:
        """
        Estimate the cost for a model call.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        config = self.MODELS.get(model)
        if not config:
            return 0.0
        
        input_cost = (input_tokens / 1000) * config["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * config["cost_per_1k_output"]
        
        return input_cost + output_cost
    
    def get_model_info(self, model: str) -> Optional[dict]:
        """Get information about a model."""
        return self.MODELS.get(model)
    
    def should_split_request(
        self,
        estimated_tokens: int,
        model: str = "gemini-1.5-flash",
    ) -> bool:
        """
        Determine if a request should be split into smaller chunks.
        
        Args:
            estimated_tokens: Estimated total tokens
            model: Target model
            
        Returns:
            True if request should be split
        """
        config = self.MODELS.get(model)
        if not config:
            return False
        
        # Split if tokens exceed 50% of model capacity
        max_safe_tokens = config["max_tokens"] * 0.5
        
        return estimated_tokens > max_safe_tokens


def select_ai_model(
    task_type: str,
    content: str,
    user_tier: str = "free",
) -> Tuple[str, dict]:
    """
    Convenience function to select an AI model.
    
    Args:
        task_type: Type of task
        content: Content to process
        user_tier: User subscription tier
        
    Returns:
        Tuple of (model_name, model_config)
    """
    router = ModelRouter()
    return router.select_model(task_type, content, user_tier)