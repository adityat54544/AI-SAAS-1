"""
Tests for AI resilience patterns including circuit breaker and retry logic.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.client import (
    CircuitBreaker,
    CircuitState,
    RetryConfig,
    RobustAIClient,
    AIClientError,
    CircuitOpenError,
    AIResponse,
)


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""
    
    def test_initial_state_is_closed(self):
        """Test that circuit breaker starts in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_can_execute_when_closed(self):
        """Test that requests can pass through when closed."""
        cb = CircuitBreaker()
        assert cb.can_execute() is True
    
    def test_records_success(self):
        """Test that success resets failure count."""
        cb = CircuitBreaker()
        cb.failure_count = 3
        cb.record_success()
        assert cb.failure_count == 0
    
    def test_opens_after_threshold(self):
        """Test that circuit opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        
        # Record failures up to threshold
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
    
    def test_cannot_execute_when_open(self):
        """Test that requests are blocked when open."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False
    
    def test_transitions_to_half_open_after_timeout(self):
        """Test that circuit transitions to half-open after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        import time
        time.sleep(0.2)
        
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_half_open_closes_on_success(self):
        """Test that half-open closes on success."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.state = CircuitState.HALF_OPEN
        
        cb.record_success()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_half_open_opens_on_failure(self):
        """Test that half-open opens on failure."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.state = CircuitState.HALF_OPEN
        
        cb.record_failure()
        
        assert cb.state == CircuitState.OPEN


class TestRetryConfig:
    """Tests for the RetryConfig class."""
    
    def test_calculate_delay_increases_exponentially(self):
        """Test that delay increases with each attempt."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        
        delay1 = config.calculate_delay(0)
        delay2 = config.calculate_delay(1)
        delay3 = config.calculate_delay(2)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
    
    def test_delay_is_capped_at_max(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=False
        )
        
        # Would be 64 without cap
        delay = config.calculate_delay(10)
        assert delay == 10.0
    
    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delay."""
        config = RetryConfig(
            base_delay=1.0,
            jitter=True
        )
        
        delays = [config.calculate_delay(0) for _ in range(10)]
        
        # Delays should vary due to jitter
        assert len(set(delays)) > 1


class TestRobustAIClient:
    """Tests for the RobustAIClient class."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return RobustAIClient(
            timeout=5.0,
            retry_config=RetryConfig(max_retries=2, base_delay=0.1, jitter=False),
            circuit_breaker=CircuitBreaker(failure_threshold=3)
        )
    
    @pytest.mark.asyncio
    async def test_execute_success(self, client):
        """Test successful execution."""
        async def operation():
            return "success"
        
        result = await client.execute_with_retry(operation, "test")
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, client):
        """Test that client retries on transient errors."""
        call_count = 0
        
        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return "success"
        
        result = await client.execute_with_retry(operation, "test")
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_fails_after_max_retries(self, client):
        """Test that client fails after max retries."""
        async def operation():
            raise Exception("Persistent error")
        
        with pytest.raises(AIClientError) as exc_info:
            await client.execute_with_retry(operation, "test")
        
        assert "All retries exhausted" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self, client):
        """Test that circuit breaker blocks requests when open."""
        # Force circuit open
        for _ in range(5):
            client.circuit_breaker.record_failure()
        
        assert client.circuit_breaker.state == CircuitState.OPEN
        
        async def operation():
            return "should not be called"
        
        with pytest.raises(CircuitOpenError):
            await client.execute_with_retry(operation, "test")
    
    @pytest.mark.asyncio
    async def test_generate_returns_response(self, client):
        """Test that generate returns an AIResponse."""
        with patch.object(client, '_call_gemini', new_callable=AsyncMock) as mock:
            mock.return_value = AIResponse(
                content="test response",
                model="gemini-1.5-flash",
                tokens_used=100,
                finish_reason="stop",
                request_id="test",
                latency_ms=0
            )
            
            response = await client.generate("test prompt")
            
            assert response.content == "test response"
            assert response.model == "gemini-1.5-flash"
            assert response.tokens_used == 100
    
    @pytest.mark.asyncio
    async def test_generate_returns_fallback_on_circuit_open(self, client):
        """Test that generate returns fallback when circuit is open."""
        # Force circuit open
        for _ in range(5):
            client.circuit_breaker.record_failure()
        
        response = await client.generate("test prompt")
        
        assert response.fallback_used is True
        assert "temporarily unavailable" in response.content.lower()
    
    def test_get_metrics(self, client):
        """Test that metrics are tracked correctly."""
        client._request_count = 10
        client._total_latency = 5000.0
        client._error_count = 2
        
        metrics = client.get_metrics()
        
        assert metrics["request_count"] == 10
        assert metrics["error_count"] == 2
        assert metrics["average_latency_ms"] == 500.0
        assert "circuit_breaker" in metrics


class TestAIResponse:
    """Tests for the AIResponse model."""
    
    def test_create_response(self):
        """Test creating an AI response."""
        response = AIResponse(
            content="test",
            model="gemini-1.5-flash",
            tokens_used=50,
            finish_reason="stop",
            request_id="abc123",
            latency_ms=100.5
        )
        
        assert response.content == "test"
        assert response.model == "gemini-1.5-flash"
        assert response.tokens_used == 50
        assert response.from_cache is False
        assert response.fallback_used is False


# Run tests with: pytest tests/test_ai_resilience.py -v