# Phase 4: Circuit Breakers - Testing Strategy

**Date:** December 27, 2025  
**Status:** 🧪 TESTING GUIDE  
**Goal:** Comprehensive testing strategy for circuit breaker implementation

---

## 🎯 Executive Summary

This document provides complete testing strategies for Phase 4: Circuit Breakers. It covers:

1. **Unit Tests** - Test circuit breaker behavior in isolation
2. **Integration Tests** - Test circuit breaker with real services
3. **Failure Scenarios** - Test state transitions and recovery
4. **Load Tests** - Verify behavior under stress
5. **Production Validation** - Verify deployment success

**Prerequisites:** 
- Read [PHASE_4_PREREQUISITES.md](./PHASE_4_PREREQUISITES.md)
- Complete [PHASE_4_IMPLEMENTATION_PLAN.md](./PHASE_4_IMPLEMENTATION_PLAN.md)

---

## 📋 Testing Levels Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Pyramid                          │
│                                                             │
│                        ▲                                    │
│                       ╱ ╲   Manual Testing                 │
│                      ╱   ╲  (Production Smoke Tests)       │
│                     ╱─────╲                                │
│                    ╱       ╲                                │
│                   ╱  Load   ╲  (1000 concurrent users)     │
│                  ╱───────────╲                             │
│                 ╱             ╲                             │
│                ╱ Integration   ╲  (Real API calls)         │
│               ╱─────────────────╲                          │
│              ╱                   ╲                          │
│             ╱   Unit Tests        ╲  (Isolated behavior)   │
│            ╱───────────────────────╲                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Unit Tests

### Test File Structure

**File:** `tests/unit/test_circuit_breaker.py`

### Test Categories

1. **State Machine Tests** - Verify state transitions
2. **Threshold Tests** - Verify failure counting
3. **Timeout Tests** - Verify recovery timing
4. **Decorator Tests** - Verify async wrapper works
5. **Listener Tests** - Verify logging/monitoring

### Complete Unit Test Implementation

```python
"""
Unit Tests for Circuit Breaker

Tests the circuit breaker in isolation without real API calls.
Verifies state machine, thresholds, timeouts, and error handling.

Author: Development Team
Date: December 27, 2025
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from pybreaker import CircuitBreaker, CircuitBreakerError
import httpx

from app.services.ai.circuit_breaker import (
    get_huggingface_circuit_breaker,
    async_circuit_breaker,
    CircuitBreakerMetricsListener,
    get_circuit_status,
    ServiceUnavailableError
)
from app.core.config import settings


class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state machine"""
    
    def test_starts_in_closed_state(self):
        """Circuit breaker should start in CLOSED state"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        assert breaker.current_state == 'closed'
    
    def test_opens_after_threshold_failures(self):
        """Circuit should OPEN after reaching failure threshold"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        
        @breaker
        def failing_func():
            raise httpx.TimeoutError("API timeout")
        
        # Fail 3 times (threshold)
        for i in range(3):
            with pytest.raises(httpx.TimeoutError):
                failing_func()
        
        # Circuit should now be OPEN
        assert breaker.current_state == 'open'
        assert breaker.fail_counter == 3
    
    def test_fails_fast_when_open(self):
        """Circuit should fail instantly when OPEN without calling function"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        
        call_count = [0]  # Mutable counter
        
        @breaker
        def counting_func():
            call_count[0] += 1
            raise httpx.TimeoutError("API timeout")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(httpx.TimeoutError):
                counting_func()
        
        assert breaker.current_state == 'open'
        assert call_count[0] == 3  # Called 3 times to open
        
        # Next call should fail fast WITHOUT calling function
        with pytest.raises(CircuitBreakerError):
            counting_func()
        
        assert call_count[0] == 3  # Still 3 - function not called
    
    def test_transitions_to_half_open_after_timeout(self):
        """Circuit should go HALF-OPEN after timeout expires"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=1)  # 1 second timeout
        
        @breaker
        def failing_func():
            raise httpx.TimeoutError("API timeout")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(httpx.TimeoutError):
                failing_func()
        
        assert breaker.current_state == 'open'
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Accessing state triggers transition check
        assert breaker.current_state == 'half-open'
    
    def test_closes_on_successful_half_open_call(self):
        """Circuit should CLOSE after successful call in HALF-OPEN"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=1)
        
        call_count = [0]
        
        @breaker
        def sometimes_failing_func():
            call_count[0] += 1
            if call_count[0] <= 3:
                raise httpx.TimeoutError("API timeout")
            return "success"  # Works after failures
        
        # Open circuit
        for i in range(3):
            with pytest.raises(httpx.TimeoutError):
                sometimes_failing_func()
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Next call should succeed and close circuit
        result = sometimes_failing_func()
        assert result == "success"
        assert breaker.current_state == 'closed'
        assert call_count[0] == 4  # 3 failures + 1 success
    
    def test_reopens_on_failed_half_open_call(self):
        """Circuit should go back to OPEN if half-open test fails"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=1)
        
        @breaker
        def failing_func():
            raise httpx.TimeoutError("Still failing")
        
        # Open circuit
        for i in range(3):
            with pytest.raises(httpx.TimeoutError):
                failing_func()
        
        # Wait for timeout → HALF-OPEN
        time.sleep(1.1)
        assert breaker.current_state == 'half-open'
        
        # Test call fails → back to OPEN
        with pytest.raises(httpx.TimeoutError):
            failing_func()
        
        assert breaker.current_state == 'open'


class TestCircuitBreakerThresholds:
    """Test failure counting and thresholds"""
    
    def test_does_not_open_below_threshold(self):
        """Circuit should stay CLOSED if failures below threshold"""
        breaker = CircuitBreaker(fail_max=5, timeout_duration=10)
        
        @breaker
        def failing_func():
            raise httpx.TimeoutError("API timeout")
        
        # Fail 4 times (below threshold of 5)
        for i in range(4):
            with pytest.raises(httpx.TimeoutError):
                failing_func()
        
        # Should still be closed
        assert breaker.current_state == 'closed'
        assert breaker.fail_counter == 4
    
    def test_reset_timeout_clears_old_failures(self):
        """Old failures should not count toward threshold"""
        breaker = CircuitBreaker(
            fail_max=3,
            timeout_duration=10,
            reset_timeout=2  # Reset after 2 seconds
        )
        
        @breaker
        def failing_func():
            raise httpx.TimeoutError("API timeout")
        
        # First 2 failures
        for i in range(2):
            with pytest.raises(httpx.TimeoutError):
                failing_func()
        
        assert breaker.fail_counter == 2
        
        # Wait for reset timeout
        time.sleep(2.1)
        
        # Fail again - counter should have reset
        with pytest.raises(httpx.TimeoutError):
            failing_func()
        
        # Should only count recent failure
        assert breaker.fail_counter == 1
        assert breaker.current_state == 'closed'
    
    def test_success_does_not_reset_counter_immediately(self):
        """One success doesn't reset failure counter in CLOSED state"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        
        fail_count = [0]
        
        @breaker
        def sometimes_failing():
            fail_count[0] += 1
            if fail_count[0] in [1, 2, 4]:  # Fail on calls 1, 2, 4
                raise httpx.TimeoutError("Fail")
            return "success"
        
        # Fail twice
        for i in range(2):
            with pytest.raises(httpx.TimeoutError):
                sometimes_failing()
        
        assert breaker.fail_counter == 2
        
        # Succeed once
        result = sometimes_failing()
        assert result == "success"
        
        # Fail again
        with pytest.raises(httpx.TimeoutError):
            sometimes_failing()
        
        # Should now have 3 failures → OPEN
        assert breaker.current_state == 'open'


class TestCircuitBreakerExceptions:
    """Test exception filtering"""
    
    def test_counts_expected_exceptions(self):
        """Only expected exceptions should count as failures"""
        breaker = CircuitBreaker(
            fail_max=3,
            timeout_duration=10,
            expected_exception=(httpx.TimeoutError, httpx.ConnectError)
        )
        
        @breaker
        def func_with_mixed_errors(error_type):
            if error_type == "timeout":
                raise httpx.TimeoutError("Timeout")
            elif error_type == "connect":
                raise httpx.ConnectError("Can't connect")
            elif error_type == "value":
                raise ValueError("Bad input")
        
        # These should count (expected exceptions)
        with pytest.raises(httpx.TimeoutError):
            func_with_mixed_errors("timeout")
        assert breaker.fail_counter == 1
        
        with pytest.raises(httpx.ConnectError):
            func_with_mixed_errors("connect")
        assert breaker.fail_counter == 2
        
        # This should NOT count (not in expected list)
        with pytest.raises(ValueError):
            func_with_mixed_errors("value")
        assert breaker.fail_counter == 2  # Still 2
    
    def test_excludes_specified_exceptions(self):
        """Excluded exceptions should not count as failures"""
        breaker = CircuitBreaker(
            fail_max=3,
            timeout_duration=10,
            exclude=[ValueError, TypeError]
        )
        
        @breaker
        def func_with_errors(error_type):
            if error_type == "timeout":
                raise httpx.TimeoutError("Timeout")
            elif error_type == "value":
                raise ValueError("Validation")
        
        # ValueError should not count
        with pytest.raises(ValueError):
            func_with_errors("value")
        assert breaker.fail_counter == 0
        
        # Timeout should count
        with pytest.raises(httpx.TimeoutError):
            func_with_errors("timeout")
        assert breaker.fail_counter == 1


class TestAsyncCircuitBreakerDecorator:
    """Test async wrapper decorator"""
    
    @pytest.mark.asyncio
    async def test_wraps_async_function(self):
        """Decorator should work with async functions"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        
        @async_circuit_breaker(breaker)
        async def async_func():
            await asyncio.sleep(0.01)
            return "success"
        
        result = await async_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_catches_async_exceptions(self):
        """Decorator should catch exceptions from async functions"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        
        @async_circuit_breaker(breaker)
        async def failing_async_func():
            await asyncio.sleep(0.01)
            raise httpx.TimeoutError("Async timeout")
        
        # Should raise original exception
        with pytest.raises(httpx.TimeoutError):
            await failing_async_func()
        
        assert breaker.fail_counter == 1
    
    @pytest.mark.asyncio
    async def test_fails_fast_when_circuit_open(self):
        """Decorator should raise CircuitBreakerError when circuit open"""
        breaker = CircuitBreaker(fail_max=2, timeout_duration=10)
        
        call_count = [0]
        
        @async_circuit_breaker(breaker)
        async def counting_async_func():
            call_count[0] += 1
            raise httpx.TimeoutError("Fail")
        
        # Open circuit
        for i in range(2):
            with pytest.raises(httpx.TimeoutError):
                await counting_async_func()
        
        # Next call should fail fast
        with pytest.raises(CircuitBreakerError):
            await counting_async_func()
        
        assert call_count[0] == 2  # Function not called when circuit open
    
    @pytest.mark.asyncio
    async def test_respects_disabled_flag(self):
        """Should bypass circuit breaker when disabled"""
        breaker = CircuitBreaker(fail_max=1, timeout_duration=10)
        
        with patch.object(settings, 'circuit_breaker_enabled', False):
            @async_circuit_breaker(breaker)
            async def failing_func():
                raise httpx.TimeoutError("Fail")
            
            # Should raise error but not trip circuit
            with pytest.raises(httpx.TimeoutError):
                await failing_func()
            
            # Circuit should still be closed (breaker disabled)
            assert breaker.current_state == 'closed'
            assert breaker.fail_counter == 0


class TestCircuitBreakerListeners:
    """Test listener callbacks"""
    
    def test_listener_called_on_state_change(self):
        """Listener should be notified of state changes"""
        listener = Mock(spec=CircuitBreakerMetricsListener)
        breaker = CircuitBreaker(
            fail_max=2,
            timeout_duration=1,
            listeners=[listener]
        )
        
        @breaker
        def failing_func():
            raise httpx.TimeoutError("Fail")
        
        # Open circuit (triggers state change)
        for i in range(2):
            with pytest.raises(httpx.TimeoutError):
                failing_func()
        
        # Verify listener was called
        listener.state_change.assert_called_once()
        call_args = listener.state_change.call_args
        assert call_args[0][1] == 'closed'  # old_state
        assert call_args[0][2] == 'open'    # new_state
    
    def test_listener_called_on_failure(self):
        """Listener should be notified of failures"""
        listener = Mock(spec=CircuitBreakerMetricsListener)
        breaker = CircuitBreaker(
            fail_max=3,
            timeout_duration=10,
            listeners=[listener]
        )
        
        @breaker
        def failing_func():
            raise httpx.TimeoutError("Fail")
        
        with pytest.raises(httpx.TimeoutError):
            failing_func()
        
        # Verify failure callback
        listener.failure.assert_called_once()
    
    def test_listener_called_on_success(self):
        """Listener should be notified of successes"""
        listener = Mock(spec=CircuitBreakerMetricsListener)
        breaker = CircuitBreaker(
            fail_max=3,
            timeout_duration=10,
            listeners=[listener]
        )
        
        @breaker
        def success_func():
            return "ok"
        
        result = success_func()
        
        # Verify success callback
        listener.success.assert_called_once()


class TestCircuitBreakerStatus:
    """Test status inspection"""
    
    def test_get_circuit_status(self):
        """Should return circuit breaker status"""
        status = get_circuit_status()
        
        assert 'name' in status
        assert 'state' in status
        assert 'fail_count' in status
        assert 'is_healthy' in status
        assert 'enabled' in status
        
        # Initial state should be closed and healthy
        assert status['state'] == 'closed'
        assert status['is_healthy'] == True


# Run tests with:
# pytest tests/unit/test_circuit_breaker.py -v
# pytest tests/unit/test_circuit_breaker.py::TestCircuitBreakerStateTransitions -v
```

---

## 🔗 Integration Tests

### Test File Structure

**File:** `tests/integration/test_circuit_breaker_integration.py`

### Test Categories

1. **Real API Tests** - Test with actual HuggingFace API
2. **Fallback Tests** - Test cache fallback when circuit opens
3. **End-to-End Tests** - Test full assistant query flow
4. **Recovery Tests** - Test automatic recovery

### Complete Integration Test Implementation

```python
"""
Integration Tests for Circuit Breaker

Tests circuit breaker with real services and dependencies.
Verifies end-to-end behavior with HuggingFace API and caching.

Author: Development Team
Date: December 27, 2025
"""

import pytest
import asyncio
import httpx
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.hf_textgen_service import HFTextGenService, get_hf_textgen_service
from app.services.ai.assistant_service import AssistantService
from app.services.ai.circuit_breaker import (
    get_huggingface_circuit_breaker,
    ServiceUnavailableError
)
from app.core.cache import RedisCacheManager


@pytest.fixture
async def reset_circuit_breaker():
    """Reset circuit breaker state before each test"""
    breaker = get_huggingface_circuit_breaker()
    # Reset state
    breaker._state_storage._state = 'closed'
    breaker._state_storage._fail_counter = 0
    yield
    # Cleanup after test
    breaker._state_storage._state = 'closed'
    breaker._state_storage._fail_counter = 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestCircuitBreakerWithRealAPI:
    """Test circuit breaker with actual HuggingFace API"""
    
    async def test_circuit_opens_on_repeated_timeouts(self, reset_circuit_breaker):
        """Circuit should open after multiple API timeouts"""
        service = get_hf_textgen_service()
        breaker = get_huggingface_circuit_breaker()
        
        # Mock API to always timeout
        with patch.object(service, '_client', new_callable=AsyncMock) as mock_client:
            mock_client.post.side_effect = httpx.TimeoutError("API timeout")
            
            # Try to generate 5 times (threshold)
            for i in range(5):
                with pytest.raises(ServiceUnavailableError):
                    await service.generate("Test prompt")
            
            # Circuit should be open
            assert breaker.current_state == 'open'
    
    async def test_circuit_stays_closed_on_single_timeout(self, reset_circuit_breaker):
        """Single timeout should not open circuit"""
        service = get_hf_textgen_service()
        breaker = get_huggingface_circuit_breaker()
        
        with patch.object(service, '_client', new_callable=AsyncMock) as mock_client:
            # First call timeouts
            mock_client.post.side_effect = httpx.TimeoutError("Timeout")
            
            with pytest.raises(ServiceUnavailableError):
                await service.generate("Test prompt")
            
            # Circuit should still be closed
            assert breaker.current_state == 'closed'
            assert breaker.fail_counter == 1
    
    async def test_circuit_closes_after_successful_recovery(self, reset_circuit_breaker):
        """Circuit should close after service recovers"""
        service = get_hf_textgen_service()
        breaker = get_huggingface_circuit_breaker()
        
        call_count = [0]
        
        async def mock_post(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 5:
                # First 5 calls fail
                raise httpx.TimeoutError("Timeout")
            # Subsequent calls succeed
            return AsyncMock(
                status_code=200,
                json=lambda: {"generated_text": "Success!"}
            )
        
        with patch.object(service, '_client', new_callable=AsyncMock) as mock_client:
            mock_client.post = mock_post
            
            # Open circuit (5 failures)
            for i in range(5):
                with pytest.raises(ServiceUnavailableError):
                    await service.generate("Test")
            
            assert breaker.current_state == 'open'
            
            # Wait for circuit to go half-open
            await asyncio.sleep(31)  # timeout_duration + 1
            
            # Next call should succeed and close circuit
            result = await service.generate("Test")
            assert result == "Success!"
            assert breaker.current_state == 'closed'


@pytest.mark.integration
@pytest.mark.asyncio
class TestCircuitBreakerWithAssistantService:
    """Test circuit breaker in full assistant flow"""
    
    async def test_assistant_returns_cached_response_when_circuit_open(
        self,
        db_session: AsyncSession,
        reset_circuit_breaker
    ):
        """Assistant should return cached response when circuit open"""
        # Setup
        assistant = AssistantService()
        breaker = get_huggingface_circuit_breaker()
        
        # First, make successful query to populate cache
        with patch.object(assistant.generator, 'generate') as mock_generate:
            mock_generate.return_value = "Cached answer"
            
            result1 = await assistant.query(
                user_query="What is faith?",
                user_id=1,
                db=db_session,
                include_metadata=True
            )
            
            assert result1["answer"] == "Cached answer"
        
        # Now open the circuit
        for i in range(5):
            breaker.call_failed()
        
        assert breaker.current_state == 'open'
        
        # Query again - should use cache fallback
        result2 = await assistant.query(
            user_query="What is faith?",
            user_id=1,
            db=db_session,
            include_metadata=True
        )
        
        assert result2["answer"] == "Cached answer"
        assert result2["metadata"]["from_fallback"] == True
        assert result2["metadata"]["fallback_source"] == "l1_cache"
    
    async def test_assistant_returns_excerpts_when_no_cache(
        self,
        db_session: AsyncSession,
        reset_circuit_breaker
    ):
        """Assistant should return excerpts when circuit open and no cache"""
        assistant = AssistantService()
        breaker = get_huggingface_circuit_breaker()
        
        # Open circuit
        for i in range(5):
            breaker.call_failed()
        
        # Query with no prior cache
        result = await assistant.query(
            user_query="What is grace?",  # Different query, no cache
            user_id=1,
            db=db_session,
            include_metadata=True
        )
        
        # Should return excerpts fallback
        assert "temporarily unavailable" in result["answer"].lower()
        assert result["metadata"]["from_fallback"] == True
        assert result["metadata"]["fallback_source"] == "excerpts"


@pytest.mark.integration
@pytest.mark.asyncio
class TestCircuitBreakerRecovery:
    """Test automatic recovery scenarios"""
    
    async def test_circuit_attempts_recovery_after_timeout(self, reset_circuit_breaker):
        """Circuit should attempt recovery after timeout expires"""
        service = get_hf_textgen_service()
        breaker = get_huggingface_circuit_breaker()
        
        # Open circuit
        with patch.object(service, 'generate', side_effect=ServiceUnavailableError("Fail")):
            for i in range(5):
                with pytest.raises(ServiceUnavailableError):
                    await service.generate("Test")
        
        assert breaker.current_state == 'open'
        
        # Wait for timeout
        await asyncio.sleep(31)
        
        # Circuit should be half-open
        assert breaker.current_state == 'half-open'
    
    async def test_circuit_reopens_if_recovery_fails(self, reset_circuit_breaker):
        """Circuit should reopen if recovery test fails"""
        service = get_hf_textgen_service()
        breaker = get_huggingface_circuit_breaker()
        
        # Open circuit
        for i in range(5):
            breaker.call_failed()
        
        # Wait for half-open
        await asyncio.sleep(31)
        
        # Recovery attempt fails
        with patch.object(service, 'generate', side_effect=ServiceUnavailableError("Still failing")):
            with pytest.raises(ServiceUnavailableError):
                await service.generate("Test")
        
        # Should be open again
        assert breaker.current_state == 'open'


# Run with:
# pytest tests/integration/test_circuit_breaker_integration.py -v
# pytest tests/integration/test_circuit_breaker_integration.py -v --log-cli-level=INFO
```

---

## 🚀 Load Tests

### Test Strategy

Use **Locust** to simulate realistic load and verify circuit breaker behavior under stress.

### Load Test Implementation

**File:** `tests/load/test_circuit_breaker_load.py`

```python
"""
Load Test for Circuit Breaker

Simulates high traffic to verify circuit breaker behavior under load.
Tests:
- Normal operation under load
- Circuit opening under failure
- Fallback performance
- Recovery behavior

Run with:
locust -f tests/load/test_circuit_breaker_load.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import random
import time


class AssistantUser(HttpUser):
    """Simulated user querying the assistant"""
    
    wait_time = between(1, 3)  # Random wait 1-3 seconds between requests
    
    def on_start(self):
        """Login before starting tests"""
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]
    
    @task(10)  # Weight: 10x more common than admin tasks
    def query_assistant(self):
        """Normal assistant query"""
        queries = [
            "What is faith?",
            "Explain grace",
            "What does the Bible say about love?",
            "Tell me about redemption",
            "What is salvation?"
        ]
        
        response = self.client.post(
            "/api/assistant/query",
            json={
                "query": random.choice(queries),
                "include_metadata": True
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("metadata", {}).get("from_fallback"):
                # Mark fallback responses
                events.request.fire(
                    request_type="fallback",
                    name="query_assistant_fallback",
                    response_time=response.elapsed.total_seconds() * 1000,
                    response_length=len(response.content),
                    exception=None,
                    context={}
                )
        
        elif response.status_code == 503:
            # Service unavailable - circuit open
            events.request.fire(
                request_type="circuit_open",
                name="query_assistant_circuit_open",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.content),
                exception=None,
                context={}
            )
    
    @task(1)  # Weight: Less common
    def check_circuit_status(self):
        """Check circuit breaker health"""
        self.client.get(
            "/api/assistant/health/circuit-breaker",
            headers={"Authorization": f"Bearer {self.token}"}
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test configuration"""
    print("\n" + "="*60)
    print("CIRCUIT BREAKER LOAD TEST")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'TBD'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test results"""
    print("\n" + "="*60)
    print("CIRCUIT BREAKER TEST RESULTS")
    print("="*60)
    
    stats = environment.stats
    
    # Print normal requests
    if "query_assistant" in stats.entries:
        entry = stats.entries["query_assistant"]
        print(f"\nNormal Queries:")
        print(f"  Total: {entry.num_requests}")
        print(f"  Failures: {entry.num_failures}")
        print(f"  Avg Response: {entry.avg_response_time:.0f}ms")
        print(f"  Max Response: {entry.max_response_time:.0f}ms")
    
    # Print fallback responses
    if "query_assistant_fallback" in stats.entries:
        entry = stats.entries["query_assistant_fallback"]
        print(f"\nFallback Responses:")
        print(f"  Total: {entry.num_requests}")
        print(f"  Avg Response: {entry.avg_response_time:.0f}ms")
    
    # Print circuit open
    if "query_assistant_circuit_open" in stats.entries:
        entry = stats.entries["query_assistant_circuit_open"]
        print(f"\nCircuit Open (503s):")
        print(f"  Total: {entry.num_requests}")
        print(f"  Avg Response: {entry.avg_response_time:.0f}ms")
    
    print("="*60 + "\n")


# Test scenarios:

# Scenario 1: Normal load
# locust -f test_circuit_breaker_load.py --users 100 --spawn-rate 10 --run-time 5m

# Scenario 2: Spike load
# locust -f test_circuit_breaker_load.py --users 500 --spawn-rate 50 --run-time 2m

# Scenario 3: Sustained load with failures
# (Manually disable HuggingFace API during test to trigger circuit)
# locust -f test_circuit_breaker_load.py --users 200 --spawn-rate 20 --run-time 10m
```

---

## ✅ Manual Testing Checklist

### Scenario 1: Normal Operation

```bash
# 1. Start services
docker-compose up -d

# 2. Check circuit status (should be closed)
curl http://localhost:8000/api/assistant/health/circuit-breaker

# 3. Make normal query
curl -X POST http://localhost:8000/api/assistant/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is faith?", "include_metadata": true}'

# 4. Verify response is normal (not from fallback)
```

**Expected Results:**
- Circuit state: `closed`
- Response contains: `"from_fallback": false`
- Response time: 2-5 seconds

---

### Scenario 2: Circuit Opens on Failures

```bash
# 1. Temporarily break HuggingFace API (wrong API key)
export HUGGINGFACE_API_KEY="invalid_key"
docker-compose restart scribes-api

# 2. Make 5+ queries (to trigger threshold)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/assistant/query \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query": "Test query '$i'", "include_metadata": true}'
  echo "\n---\n"
done

# 3. Check circuit status (should be open)
curl http://localhost:8000/api/assistant/health/circuit-breaker

# 4. Try another query (should fail fast)
time curl -X POST http://localhost:8000/api/assistant/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Fast fail test", "include_metadata": true}'
```

**Expected Results:**
- After 5 failures: Circuit state `open`
- Subsequent queries: Response time < 100ms (fail fast)
- Response: 503 Service Unavailable or fallback

---

### Scenario 3: Cache Fallback

```bash
# 1. Make successful query first (populate cache)
curl -X POST http://localhost:8000/api/assistant/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is grace?", "include_metadata": true}' \
  | jq '.answer'

# 2. Break API and open circuit (as in Scenario 2)

# 3. Query same question again
curl -X POST http://localhost:8000/api/assistant/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is grace?", "include_metadata": true}' \
  | jq '.metadata.from_fallback, .metadata.fallback_source'
```

**Expected Results:**
- First query: Normal response, cached
- Second query: Same answer from cache
- Metadata: `"from_fallback": true`, `"fallback_source": "l1_cache"`
- Response time: < 100ms

---

### Scenario 4: Automatic Recovery

```bash
# 1. Open circuit (as in Scenario 2)

# 2. Fix API key
export HUGGINGFACE_API_KEY="your_real_key"
docker-compose restart scribes-api

# 3. Wait 31 seconds (timeout_duration + 1)
sleep 31

# 4. Check circuit status (should be half-open)
curl http://localhost:8000/api/assistant/health/circuit-breaker

# 5. Make test query
curl -X POST http://localhost:8000/api/assistant/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Recovery test", "include_metadata": true}'

# 6. Check circuit status again (should be closed)
curl http://localhost:8000/api/assistant/health/circuit-breaker
```

**Expected Results:**
- After wait: Circuit state `half-open`
- After successful query: Circuit state `closed`
- Subsequent queries work normally

---

## 📊 Production Validation

### Post-Deployment Checks

#### 1. Verify Circuit Breaker Initialized

```bash
# Check logs for initialization message
docker logs scribes-api | grep "circuit breaker"

# Expected output:
# INFO: Initializing HuggingFace circuit breaker
# INFO: Circuit breaker enabled=True, fail_threshold=5, timeout=30
```

#### 2. Health Check Endpoint

```bash
curl https://api.scribes.app/api/assistant/health/circuit-breaker

# Expected response:
{
  "circuit_breaker": {
    "name": "huggingface_api",
    "state": "closed",
    "fail_count": 0,
    "last_failure_time": null,
    "is_healthy": true,
    "enabled": true
  },
  "timestamp": 1703700000.0
}
```

#### 3. Monitor Logs

```bash
# Watch for circuit breaker events
docker logs -f scribes-api | grep -i "circuit"

# Look for:
# - "Circuit breaker state change" (WARNING)
# - "Circuit breaker failure" (ERROR)
# - "Circuit open" (WARNING)
# - "Returning fallback response" (INFO)
```

#### 4. Trigger Test Failure (Staging Only!)

```bash
# In staging environment, temporarily break API to test
# DO NOT DO THIS IN PRODUCTION

# 1. Set invalid API key
kubectl set env deployment/scribes-api HUGGINGFACE_API_KEY=invalid

# 2. Make queries until circuit opens

# 3. Verify circuit opens and fallbacks work

# 4. Restore API key
kubectl set env deployment/scribes-api HUGGINGFACE_API_KEY=real_key

# 5. Verify automatic recovery
```

---

## 🎯 Success Criteria Summary

### Unit Tests
- ✅ All state transitions work correctly
- ✅ Threshold detection accurate
- ✅ Timeout behavior correct
- ✅ Exception filtering works
- ✅ Async decorator functional
- ✅ 95%+ code coverage

### Integration Tests
- ✅ Works with real HuggingFace API
- ✅ Cache fallback functions
- ✅ End-to-end assistant flow works
- ✅ Automatic recovery successful

### Load Tests
- ✅ Handles 100+ concurrent users
- ✅ Circuit opens under failure
- ✅ Fallbacks perform well (< 100ms)
- ✅ No memory leaks or crashes

### Production Validation
- ✅ Circuit breaker initializes correctly
- ✅ Health endpoint works
- ✅ Logging structured and useful
- ✅ Automatic recovery verified
- ✅ Zero production incidents

---

**Document Status:** ✅ COMPLETE  
**Last Updated:** December 27, 2025  
**Related Documents:**
- [Phase 4 Prerequisites](./PHASE_4_PREREQUISITES.md)
- [Phase 4 Implementation Plan](./PHASE_4_IMPLEMENTATION_PLAN.md)
