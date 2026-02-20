"""
Robust AI Client with Resilience Patterns.

Implements timeouts, exponential backoff with jitter, circuit breaker,
and fallback handling for LLM API calls.
"""

import asyncio
import hashlib
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    Implements the circuit breaker pattern:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Requests fail fast, no calls to downstream
    - HALF_OPEN: Limited requests to test recovery
    """
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    half_open_max_calls: int = 3
    
    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0
    
    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time is None:
                self.state = CircuitState.HALF_OPEN
                return True
            
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests in half-open state
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def record_success(self) -> None:
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            # Recovery successful, close circuit
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open, back to open
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt with optional jitter."""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter (0-25% of delay)
            delay *= (1 + random.random() * 0.25)
        
        return delay


class AIResponse(BaseModel):
    """Standardized AI response with metadata."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    request_id: str
    latency_ms: float
    from_cache: bool = False
    fallback_used: bool = False


class AIClientError(Exception):
    """Base exception for AI client errors."""
    def __init__(
        self,
        message: str,
        is_retryable: bool = False,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.is_retryable = is_retryable
        self.original_error = original_error


class CircuitOpenError(AIClientError):
    """Raised when circuit breaker is open."""
    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message, is_retryable=False)


class QuotaExceededError(AIClientError):
    """Raised when quota is exceeded."""
    def __init__(self, message: str = "Quota exceeded"):
        super().__init__(message, is_retryable=False)


class RobustAIClient:
    """
    Robust AI client with resilience patterns.
    
    Features:
    - Circuit breaker protection
    - Exponential backoff with jitter
    - Timeout handling
    - Request/response logging
    - Fallback mechanisms
    """
    
    def __init__(
        self,
        timeout: float = 60.0,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """Initialize the robust AI client."""
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self._request_count = 0
        self._total_latency = 0.0
        self._error_count = 0
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        random_bytes = random.randbytes(8).hex()
        return hashlib.sha256(f"{timestamp}-{random_bytes}".encode()).hexdigest()[:16]
    
    async def execute_with_retry(
        self,
        operation: Callable[[], T],
        operation_name: str = "ai_call",
    ) -> T:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Async callable to execute
            operation_name: Name for logging
            
        Returns:
            Result of the operation
            
        Raises:
            AIClientError: If all retries fail
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                raise CircuitOpenError(
                    f"Circuit breaker is open for {operation_name}"
                )
            
            try:
                if attempt > 0:
                    delay = self.retry_config.calculate_delay(attempt - 1)
                    logger.info(
                        f"Retrying {operation_name}",
                        extra={
                            "attempt": attempt,
                            "delay_ms": delay * 1000,
                        }
                    )
                    await asyncio.sleep(delay)
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    operation(),
                    timeout=self.timeout
                )
                
                # Record success
                self.circuit_breaker.record_success()
                return result
                
            except asyncio.TimeoutError as e:
                last_error = e
                self.circuit_breaker.record_failure()
                logger.warning(
                    f"Timeout in {operation_name}",
                    extra={"attempt": attempt, "timeout": self.timeout}
                )
                
            except AIClientError as e:
                last_error = e
                if not e.is_retryable:
                    raise
                self.circuit_breaker.record_failure()
                
            except Exception as e:
                last_error = e
                self.circuit_breaker.record_failure()
                logger.error(
                    f"Error in {operation_name}",
                    extra={"attempt": attempt, "error": str(e)}
                )
        
        # All retries exhausted
        self._error_count += 1
        raise AIClientError(
            f"All retries exhausted for {operation_name}",
            is_retryable=False,
            original_error=last_error
        )
    
    async def generate(
        self,
        prompt: str,
        model: str = "gemini-1.5-flash",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> AIResponse:
        """
        Generate text using the AI model with resilience.
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            **kwargs: Additional model-specific parameters
            
        Returns:
            AIResponse with generated content
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        async def _call_model():
            # This would be the actual model call
            # For now, return a placeholder that would be replaced
            # with actual Gemini/other provider calls
            return await self._call_gemini(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                request_id=request_id,
                **kwargs,
            )
        
        try:
            response = await self.execute_with_retry(_call_model, "generate")
            
            # Update metrics
            latency = (time.time() - start_time) * 1000
            self._request_count += 1
            self._total_latency += latency
            
            response.latency_ms = latency
            response.request_id = request_id
            
            return response
            
        except CircuitOpenError:
            # Return a fallback response
            logger.warning("Circuit breaker open, returning fallback response")
            return AIResponse(
                content="Service temporarily unavailable. Please try again later.",
                model=model,
                tokens_used=0,
                finish_reason="circuit_open",
                request_id=request_id,
                latency_ms=(time.time() - start_time) * 1000,
                fallback_used=True,
            )
    
    async def _call_gemini(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        request_id: str,
        **kwargs,
    ) -> AIResponse:
        """
        Make actual call to Gemini API.
        
        This is a placeholder that would be implemented with the actual
        Gemini SDK or HTTP client.
        """
        # Placeholder - actual implementation would use google-generativeai
        # This simulates a successful response for testing
        return AIResponse(
            content="AI response placeholder",
            model=model,
            tokens_used=len(prompt) // 4 + 100,
            finish_reason="stop",
            request_id=request_id,
            latency_ms=0,
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        avg_latency = (
            self._total_latency / self._request_count
            if self._request_count > 0
            else 0
        )
        
        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "average_latency_ms": avg_latency,
            "circuit_breaker": self.circuit_breaker.get_state(),
        }


# Global client instance
_client_instance: Optional[RobustAIClient] = None


def get_ai_client() -> RobustAIClient:
    """Get the global AI client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = RobustAIClient()
    return _client_instance


async def generate_with_resilience(
    prompt: str,
    model: str = "gemini-1.5-flash",
    **kwargs,
) -> AIResponse:
    """
    Convenience function for resilient text generation.
    
    Args:
        prompt: Input prompt
        model: Model to use
        **kwargs: Additional parameters
        
    Returns:
        AIResponse with generated content
    """
    client = get_ai_client()
    return await client.generate(prompt, model=model, **kwargs)