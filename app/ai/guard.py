"""
AI Usage Guard - Cost Controls and Quota Management.

This module enforces per-user and per-repository budget/quotas for AI usage,
ensuring cost control and preventing abuse.
"""

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.config import settings


class QuotaExceededError(Exception):
    """Raised when a quota has been exceeded."""
    def __init__(self, message: str, quota_type: str, limit: int, current: int):
        super().__init__(message)
        self.quota_type = quota_type
        self.limit = limit
        self.current = current


class UsageType(str, Enum):
    """Types of AI usage."""
    ANALYSIS = "analysis"
    CI_GENERATION = "ci_generation"
    CHAT = "chat"
    EMBEDDING = "embedding"


@dataclass
class UsageRecord:
    """Record of AI usage for tracking."""
    user_id: str
    repository_id: Optional[str]
    usage_type: UsageType
    tokens_used: int
    model: str
    timestamp: datetime
    request_id: str
    cost_estimate: float


class UsageQuota(BaseModel):
    """Quota configuration for AI usage."""
    max_tokens_per_task: int = 32000
    daily_tokens_per_user: int = 100000
    daily_tokens_per_repo: int = 500000
    monthly_tokens_per_user: int = 2000000
    monthly_tokens_per_org: int = 10000000


class UsageStats(BaseModel):
    """Usage statistics for a user or repository."""
    user_id: str
    daily_tokens: int = 0
    monthly_tokens: int = 0
    daily_requests: int = 0
    monthly_requests: int = 0
    last_reset_daily: Optional[datetime] = None
    last_reset_monthly: Optional[datetime] = None


class AIGuard:
    """
    Guard for AI usage that enforces quotas and tracks usage.
    
    Features:
    - Per-user and per-repository token quotas
    - Daily and monthly limits
    - Cost estimation and tracking
    - Redis-backed distributed counters (optional)
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize the AI guard.
        
        Args:
            redis_client: Optional Redis client for distributed quota tracking
        """
        self.redis_client = redis_client
        self.quota = UsageQuota(
            max_tokens_per_task=getattr(settings, 'ai_max_tokens_per_task', 32000),
            daily_tokens_per_user=getattr(settings, 'ai_daily_quota_per_user', 100000),
        )
        # In-memory fallback for quota tracking
        self._usage_cache: dict[str, UsageStats] = {}
    
    def _get_cache_key(self, prefix: str, identifier: str, date: datetime) -> str:
        """Generate a cache key for quota tracking."""
        date_str = date.strftime("%Y-%m-%d")
        return f"ai_usage:{prefix}:{identifier}:{date_str}"
    
    def _hash_identifier(self, identifier: str) -> str:
        """Hash an identifier for privacy in logs."""
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    async def check_quota(
        self,
        user_id: str,
        repository_id: Optional[str] = None,
        requested_tokens: int = 0,
    ) -> bool:
        """
        Check if the user/repository has quota available.
        
        Args:
            user_id: User ID making the request
            repository_id: Optional repository ID
            requested_tokens: Estimated tokens for the request
            
        Returns:
            True if quota is available
            
        Raises:
            QuotaExceededError: If quota has been exceeded
        """
        now = datetime.utcnow()
        
        # Check per-task limit
        if requested_tokens > self.quota.max_tokens_per_task:
            raise QuotaExceededError(
                f"Request exceeds per-task limit of {self.quota.max_tokens_per_task} tokens",
                quota_type="per_task",
                limit=self.quota.max_tokens_per_task,
                current=requested_tokens,
            )
        
        # Get or create usage stats
        cache_key = self._get_cache_key("user", user_id, now)
        
        if self.redis_client:
            # Use Redis for distributed tracking
            daily_usage = await self._get_redis_counter(cache_key)
        else:
            # Use in-memory tracking
            stats = self._usage_cache.get(user_id)
            if stats is None:
                stats = UsageStats(user_id=user_id)
                self._usage_cache[user_id] = stats
            
            # Reset daily counter if needed
            if stats.last_reset_daily is None or (now - stats.last_reset_daily) > timedelta(days=1):
                stats.daily_tokens = 0
                stats.daily_requests = 0
                stats.last_reset_daily = now
            
            daily_usage = stats.daily_tokens
        
        # Check daily user quota
        if daily_usage + requested_tokens > self.quota.daily_tokens_per_user:
            raise QuotaExceededError(
                f"Daily token quota exceeded for user",
                quota_type="daily_user",
                limit=self.quota.daily_tokens_per_user,
                current=daily_usage,
            )
        
        return True
    
    async def record_usage(
        self,
        user_id: str,
        repository_id: Optional[str],
        usage_type: UsageType,
        tokens_used: int,
        model: str,
        request_id: str,
    ) -> UsageRecord:
        """
        Record AI usage for quota tracking.
        
        Args:
            user_id: User ID making the request
            repository_id: Optional repository ID
            usage_type: Type of usage (analysis, ci_generation, etc.)
            tokens_used: Number of tokens consumed
            model: Model used
            request_id: Request ID for correlation
            
        Returns:
            UsageRecord with cost estimate
        """
        now = datetime.utcnow()
        
        # Estimate cost (Gemini 1.5 Flash pricing as of 2024)
        cost_per_1k_tokens = self._get_cost_per_1k_tokens(model)
        cost_estimate = (tokens_used / 1000) * cost_per_1k_tokens
        
        record = UsageRecord(
            user_id=user_id,
            repository_id=repository_id,
            usage_type=usage_type,
            tokens_used=tokens_used,
            model=model,
            timestamp=now,
            request_id=request_id,
            cost_estimate=cost_estimate,
        )
        
        # Update usage tracking
        if self.redis_client:
            cache_key = self._get_cache_key("user", user_id, now)
            await self._increment_redis_counter(cache_key, tokens_used)
        else:
            stats = self._usage_cache.get(user_id)
            if stats:
                stats.daily_tokens += tokens_used
                stats.daily_requests += 1
        
        return record
    
    def _get_cost_per_1k_tokens(self, model: str) -> float:
        """
        Get the cost per 1k tokens for a model.
        
        Pricing as of 2024 (subject to change):
        - Gemini 1.5 Flash: $0.00001875 / 1k characters (input)
        - Gemini 2.5 Pro: $0.00125 / 1k characters (input)
        """
        pricing = {
            "gemini-1.5-flash": 0.00001875,
            "gemini-1.5-pro": 0.00125,
            "gemini-2.5-pro": 0.00125,
        }
        return pricing.get(model, 0.0001)  # Default fallback
    
    async def _get_redis_counter(self, key: str) -> int:
        """Get counter value from Redis."""
        if not self.redis_client:
            return 0
        try:
            value = await self.redis_client.get(key)
            return int(value) if value else 0
        except Exception:
            return 0
    
    async def _increment_redis_counter(self, key: str, amount: int) -> None:
        """Increment counter in Redis with TTL."""
        if not self.redis_client:
            return
        try:
            await self.redis_client.incrby(key, amount)
            # Set TTL to 48 hours to cover timezone issues
            await self.redis_client.expire(key, 172800)
        except Exception:
            pass  # Fail silently for tracking
    
    def get_usage_stats(self, user_id: str) -> Optional[UsageStats]:
        """Get usage statistics for a user."""
        return self._usage_cache.get(user_id)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        
        Uses a simple heuristic: ~4 characters per token for English text.
        For more accurate estimation, use tiktoken.
        """
        return len(text) // 4
    
    def should_use_pro_model(self, complexity_score: float, user_tier: str = "free") -> str:
        """
        Determine which model to use based on complexity and user tier.
        
        Args:
            complexity_score: Complexity score from 0-1
            user_tier: User subscription tier
            
        Returns:
            Model name to use
        """
        default_model = getattr(settings, 'ai_model_default', 'gemini-1.5-flash')
        
        # Free tier always uses flash model
        if user_tier == "free":
            return default_model
        
        # Pro tier can use pro model for complex tasks
        if complexity_score > 0.8 and user_tier in ["pro", "enterprise"]:
            return "gemini-2.5-pro"
        
        return default_model


# Global guard instance
_guard_instance: Optional[AIGuard] = None


def get_ai_guard() -> AIGuard:
    """Get the global AI guard instance."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = AIGuard()
    return _guard_instance


async def check_ai_quota(
    user_id: str,
    repository_id: Optional[str] = None,
    estimated_tokens: int = 0,
) -> bool:
    """
    Convenience function to check AI quota.
    
    Args:
        user_id: User ID
        repository_id: Optional repository ID
        estimated_tokens: Estimated tokens for the request
        
    Returns:
        True if quota is available
    """
    guard = get_ai_guard()
    return await guard.check_quota(user_id, repository_id, estimated_tokens)


async def record_ai_usage(
    user_id: str,
    tokens_used: int,
    usage_type: UsageType = UsageType.ANALYSIS,
    repository_id: Optional[str] = None,
    model: str = "gemini-1.5-flash",
    request_id: str = "",
) -> UsageRecord:
    """
    Convenience function to record AI usage.
    
    Args:
        user_id: User ID
        tokens_used: Number of tokens consumed
        usage_type: Type of usage
        repository_id: Optional repository ID
        model: Model used
        request_id: Request ID for correlation
        
    Returns:
        UsageRecord with cost estimate
    """
    guard = get_ai_guard()
    return await guard.record_usage(
        user_id=user_id,
        repository_id=repository_id,
        usage_type=usage_type,
        tokens_used=tokens_used,
        model=model,
        request_id=request_id,
    )