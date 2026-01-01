# Phase 4: Circuit Breakers - Prerequisites Guide

**Date:** December 27, 2025  
**Status:** 📚 PREREQUISITES  
**Goal:** Understand all concepts, tools, and principles before implementing circuit breakers

---

## 🎯 Executive Summary

Before implementing circuit breakers for the AssistantService, you need to understand:
- **What circuit breakers are** and why they're critical for fault tolerance
- **How PyBreaker works** and its state machine
- **Integration patterns** with async Python and FastAPI
- **Failure detection strategies** for LLM APIs
- **Graceful degradation** using cached responses
- **Testing strategies** for failure scenarios

This guide provides the foundational knowledge needed to implement Phase 4 successfully.

---

## 📋 Table of Contents

1. [Core Concepts](#core-concepts)
2. [The Circuit Breaker Pattern](#the-circuit-breaker-pattern)
3. [PyBreaker Library](#pybreaker-library)
4. [Integration with AsyncIO](#integration-with-asyncio)
5. [Failure Detection Strategies](#failure-detection-strategies)
6. [Graceful Degradation Patterns](#graceful-degradation-patterns)
7. [Testing Circuit Breakers](#testing-circuit-breakers)
8. [Production Considerations](#production-considerations)
9. [Prerequisites Checklist](#prerequisites-checklist)

---

## 🧠 Core Concepts

### What is a Circuit Breaker?

A **circuit breaker** is a design pattern that prevents your application from repeatedly calling a failing external service. It acts like an electrical circuit breaker:

```
Normal Operation → Many Failures → Stop Calling → Wait → Try Again → Recover or Repeat
```

**Real-World Analogy:**
```
🏠 Home Electrical Circuit:
- CLOSED: Power flows normally (requests succeed)
- OPEN: Breaker trips, power cut off (stop calling failing service)
- HALF-OPEN: Test if power restored (try one request to check recovery)
```

### Why Do We Need Circuit Breakers?

#### Problem Without Circuit Breaker:
```python
# HuggingFace API is down (500 errors)
for i in range(100):  # 100 users try to use assistant
    try:
        answer = await call_huggingface_api(query)  # Takes 30s to timeout
    except:
        # Try again... and again... and again...
        pass

# Result:
# - 100 * 30s = 3000 seconds of wasted waiting
# - Database connections exhausted
# - Redis connections exhausted
# - App becomes unresponsive
# - Users get generic "500 Internal Server Error"
# - No automatic recovery when HF comes back online
```

#### Solution With Circuit Breaker:
```python
# HuggingFace API is down
# First 5 requests fail → Circuit OPENS
# Next 95 requests fail instantly with "Service Unavailable"
# After 30 seconds → Circuit goes HALF-OPEN
# Try 1 test request → Succeeds → Circuit CLOSES
# All requests resume normally

# Result:
# - Only 5 * 30s = 150 seconds of timeout waiting
# - 95 requests fail instantly (< 1ms)
# - Users get helpful message: "AI service temporarily unavailable, using cached response"
# - Automatic recovery when HF comes back
# - App remains responsive
```

---

## 🔄 The Circuit Breaker Pattern

### State Machine

Circuit breakers operate as a finite state machine with 3 states:

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    │        CLOSED (Normal)              │
                    │   All requests go through           │
                    │                                     │
                    └──────────┬──────────────────────────┘
                               │
                     5 failures in 60s
                               │
                               ▼
                    ┌─────────────────────────────────────┐
                    │                                     │
         ┌─────────▶│          OPEN (Failing)             │
         │          │   All requests fail instantly       │
         │          │                                     │
         │          └──────────┬──────────────────────────┘
         │                     │
         │           After 30 seconds (timeout)
         │                     │
         │                     ▼
         │          ┌─────────────────────────────────────┐
         │          │                                     │
         │          │      HALF-OPEN (Testing)            │
         │          │   Allow 1 test request              │
    Test fails      │                                     │
         │          └──────────┬──────────────────────────┘
         │                     │
         │               Test succeeds
         │                     │
         └─────────────────────┴─────────────────────────►
                                                   Back to CLOSED
```

### State Descriptions

#### **CLOSED State** (Normal Operation)
- **Behavior:** All requests pass through to the external service
- **Failure Tracking:** Count failures within a time window
- **Transition:** After `fail_max` failures → OPEN

```python
# Configuration
fail_max = 5              # Threshold
fail_window = 60          # Count failures in last 60 seconds

# Example scenario:
# t=0s:  Request 1 fails
# t=5s:  Request 2 fails
# t=10s: Request 3 succeeds (reset counter)
# t=15s: Request 4 fails (count = 1)
# t=20s: Request 5 fails (count = 2)
# t=25s: Request 6 fails (count = 3)
# t=30s: Request 7 fails (count = 4)
# t=35s: Request 8 fails (count = 5) → Circuit OPENS
```

#### **OPEN State** (Fault Detected)
- **Behavior:** All requests fail immediately without calling external service
- **Duration:** Wait for `timeout_duration` seconds
- **Purpose:** Give the external service time to recover
- **Transition:** After timeout → HALF-OPEN

```python
# Configuration
timeout_duration = 30     # Wait 30 seconds before testing

# Example scenario:
# Circuit opens at t=0s
# t=0s-29s:  All requests fail instantly (< 1ms)
# t=30s:     Circuit transitions to HALF-OPEN
```

#### **HALF-OPEN State** (Testing Recovery)
- **Behavior:** Allow ONE test request through
- **Success:** If request succeeds → CLOSED (fully recovered)
- **Failure:** If request fails → OPEN (stay in failure mode)

```python
# Example scenario:

# Success case:
# t=0s: Circuit goes HALF-OPEN
# t=0s: Request 1 passes through → Succeeds!
# t=0s: Circuit goes CLOSED (recovered)
# t=1s: All subsequent requests work normally

# Failure case:
# t=0s: Circuit goes HALF-OPEN
# t=0s: Request 1 passes through → Fails!
# t=0s: Circuit goes back to OPEN
# t=30s: Try again (back to HALF-OPEN)
```

---

## 🐍 PyBreaker Library

### Overview

**PyBreaker** is a Python implementation of the Circuit Breaker pattern. It's:
- **Pure Python** (no external dependencies)
- **Thread-safe** (works with async code)
- **Configurable** (thresholds, timeouts, listeners)
- **Lightweight** (< 500 lines of code)

### Installation

```bash
pip install pybreaker==1.0.1
```

✅ **Already installed in your project!** (See `requirements.txt`)

### Basic Usage

```python
from pybreaker import CircuitBreaker

# Create a circuit breaker
db_breaker = CircuitBreaker(
    fail_max=5,              # Open after 5 failures
    timeout_duration=30,     # Wait 30s before testing
    name='database'          # For logging/monitoring
)

# Wrap function calls
@db_breaker
def query_database(sql):
    # This call is protected
    return db.execute(sql)

# Alternative: Manual wrapping
def query_database(sql):
    return db_breaker.call(db.execute, sql)
```

### Configuration Options

```python
CircuitBreaker(
    # === Failure Thresholds ===
    fail_max=5,
    # How many failures trigger the circuit to OPEN
    # Higher = more tolerant of transient errors
    # Lower = fail fast, protect system sooner
    
    # === Time Windows ===
    timeout_duration=30,
    # Seconds to wait in OPEN state before testing (HALF-OPEN)
    # Longer = give service more recovery time
    # Shorter = recover faster when service is back
    
    reset_timeout=60,
    # Seconds to reset failure counter in CLOSED state
    # Failures older than this don't count toward fail_max
    
    # === Exceptions ===
    exclude=[ValueError],
    # Don't count these exceptions as failures
    # Use for validation errors that aren't service failures
    
    expected_exception=TimeoutError,
    # Only count this type of exception as failure
    # Useful if you want circuit to only trip on timeouts
    
    # === Callbacks ===
    listeners=[my_listener],
    # Functions called on state changes (for logging/metrics)
    
    # === Naming ===
    name='my_service',
    # Identifier for logging and monitoring
)
```

### State Inspection

```python
breaker = CircuitBreaker(fail_max=5, timeout_duration=30)

# Check current state
print(breaker.current_state)  # 'closed', 'open', or 'half-open'

# Check if circuit is open
if breaker.current_state == 'open':
    print("Service is down, using fallback")

# Get failure count
print(breaker.fail_counter)  # Number of recent failures

# Get last failure time
print(breaker.last_failure_time)  # Timestamp
```

### Listeners (for Monitoring)

```python
from pybreaker import CircuitBreakerListener

class MetricsListener(CircuitBreakerListener):
    """Custom listener for Prometheus metrics"""
    
    def state_change(self, cb, old_state, new_state):
        """Called when circuit state changes"""
        print(f"{cb.name}: {old_state} → {new_state}")
        # Update Prometheus gauge
        circuit_state_metric.labels(cb.name).set(
            0 if new_state == 'closed' else 1
        )
    
    def failure(self, cb, exc):
        """Called on every failure"""
        print(f"{cb.name} failed: {exc}")
        failure_counter.labels(cb.name).inc()
    
    def success(self, cb):
        """Called on every success"""
        success_counter.labels(cb.name).inc()

# Attach listener
breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=30,
    listeners=[MetricsListener()]
)
```

---

## ⚡ Integration with AsyncIO

### Challenge: PyBreaker is Synchronous

PyBreaker was designed for synchronous Python code, but our FastAPI app uses `async`/`await`. We need to bridge the gap.

### Solution 1: Wrapper Function (Recommended)

```python
from pybreaker import CircuitBreaker
from functools import wraps

# Create sync circuit breaker
llm_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=30,
    name='huggingface'
)

def async_circuit_breaker(breaker):
    """Decorator to apply circuit breaker to async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check circuit state before calling
            if breaker.current_state == 'open':
                # Circuit is open, fail fast
                raise Exception(f"Circuit {breaker.name} is OPEN")
            
            try:
                # Call the async function
                result = await func(*args, **kwargs)
                
                # Success - notify breaker
                breaker.call_succeeded()
                
                return result
                
            except Exception as e:
                # Failure - notify breaker
                breaker.call_failed()
                raise
        
        return wrapper
    return decorator

# Usage
@async_circuit_breaker(llm_breaker)
async def call_huggingface(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api-inference.huggingface.co/...",
            json={"inputs": prompt}
        )
        return response.json()
```

### Solution 2: Manual State Management

```python
async def call_huggingface_with_breaker(prompt: str):
    # Check if circuit is open
    if llm_breaker.current_state == 'open':
        # Fail fast with helpful message
        raise ServiceUnavailableError(
            "HuggingFace API is currently unavailable. "
            "Please try again in a few moments."
        )
    
    try:
        # Make the actual call
        result = await _call_huggingface_internal(prompt)
        
        # Notify success
        llm_breaker.call_succeeded()
        
        return result
        
    except (httpx.TimeoutError, httpx.HTTPStatusError) as e:
        # Notify failure
        llm_breaker.call_failed()
        
        # Re-raise for upstream handling
        raise
```

### Key Principles for Async Integration

1. **Check state BEFORE calling** - Don't waste time on open circuits
2. **Notify success/failure** - Keep the circuit breaker state accurate
3. **Handle CircuitBreakerError** - Provide fallback when circuit opens
4. **Don't block event loop** - Circuit breaker operations are fast (< 1ms)

---

## 🎯 Failure Detection Strategies

### What Counts as a Failure?

Not all errors should trip the circuit breaker. You need to distinguish:

#### ✅ **Count as Failures** (Trip Circuit)
```python
# Service-level failures (external dependency down)
httpx.TimeoutError          # API took too long
httpx.ConnectError          # Can't reach API
httpx.HTTPStatusError       # 500, 502, 503, 504 errors

# Model-specific failures
GenerationError             # LLM returned invalid output
ModelLoadError              # Model failed to load
```

#### ❌ **Don't Count as Failures** (Keep Circuit Closed)
```python
# Client errors (user's fault, not service fault)
httpx.HTTPStatusError       # 400, 401, 403, 404 errors
ValueError                  # Invalid input (empty prompt)
ValidationError             # Pydantic validation failed

# Expected conditions
EmptyContextError           # No sermon content found (valid scenario)
```

### Implementation Strategy

```python
from pybreaker import CircuitBreaker

# Create breaker with explicit exception handling
hf_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=30,
    name='huggingface',
    
    # Only count these exceptions as failures
    expected_exception=(
        httpx.TimeoutError,
        httpx.ConnectError,
        GenerationError,
        ModelLoadError
    )
)

# Alternative: Use exclude for client errors
hf_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=30,
    exclude=[
        ValueError,           # Don't count validation errors
        httpx.HTTPStatusError # Don't count 4xx errors
    ]
)
```

### Failure Window Configuration

```python
# Scenario 1: Strict (fail fast)
strict_breaker = CircuitBreaker(
    fail_max=3,               # Trip after just 3 failures
    timeout_duration=60,      # Long recovery window
    reset_timeout=30          # Short memory (30s window)
)
# Use for: Critical paths, expensive operations

# Scenario 2: Lenient (tolerate transients)
lenient_breaker = CircuitBreaker(
    fail_max=10,              # Tolerate 10 failures
    timeout_duration=10,      # Quick recovery attempts
    reset_timeout=120         # Long memory (2 min window)
)
# Use for: Non-critical features, flaky networks

# Scenario 3: Balanced (recommended for LLMs)
balanced_breaker = CircuitBreaker(
    fail_max=5,               # Reasonable threshold
    timeout_duration=30,      # Standard recovery time
    reset_timeout=60          # 1 minute window
)
# Use for: HuggingFace API calls
```

---

## 🛡️ Graceful Degradation Patterns

### What is Graceful Degradation?

When the circuit breaker opens, you have 3 options:

1. **Fail Hard** ❌ - Return error to user (bad UX)
2. **Fallback** ⚠️ - Use alternative service (complex)
3. **Graceful Degradation** ✅ - Provide reduced functionality (best)

### Pattern 1: Return Cached Response

```python
@async_circuit_breaker(llm_breaker)
async def generate_answer(query: str, context: str):
    # Primary path: Call LLM
    return await call_huggingface(query, context)

async def generate_answer_with_fallback(query: str, context: str):
    """Generate answer with circuit breaker and cache fallback"""
    
    try:
        # Try primary path
        return await generate_answer(query, context)
        
    except CircuitBreakerError:
        # Circuit is open - try cache fallback
        cached = await query_cache.get(query)
        
        if cached:
            logger.info("Circuit open, returning cached response")
            return {
                **cached,
                "metadata": {
                    **cached.get("metadata", {}),
                    "from_fallback": True,
                    "fallback_reason": "service_unavailable"
                }
            }
        
        # No cache available - return helpful error
        raise ServiceUnavailableError(
            "AI assistant is temporarily unavailable. "
            "No cached response available for this query."
        )
```

### Pattern 2: Simplified Response

```python
async def generate_answer_with_fallback(query: str, context: str):
    """Generate answer with simplified fallback"""
    
    try:
        # Try full AI generation
        return await generate_answer(query, context)
        
    except CircuitBreakerError:
        # Fallback: Return context excerpts without LLM
        logger.warning("Circuit open, returning context excerpts")
        
        excerpts = extract_relevant_excerpts(query, context)
        
        return {
            "answer": (
                "I'm temporarily unable to generate a custom response. "
                "Here are relevant excerpts from your sermons:\n\n" +
                "\n\n".join(excerpts)
            ),
            "sources": [],
            "metadata": {
                "from_fallback": True,
                "fallback_type": "excerpts_only"
            }
        }
```

### Pattern 3: Queue for Later

```python
async def generate_answer_with_fallback(query: str, context: str):
    """Queue request for later processing if circuit open"""
    
    try:
        return await generate_answer(query, context)
        
    except CircuitBreakerError:
        # Add to background job queue
        job_id = await background_queue.enqueue(
            "generate_answer_delayed",
            query=query,
            context=context,
            user_id=user_id
        )
        
        return {
            "answer": (
                "AI assistant is temporarily overloaded. "
                "Your query has been queued and will be processed shortly. "
                f"Check back in a few minutes (Job ID: {job_id})."
            ),
            "metadata": {
                "from_fallback": True,
                "fallback_type": "queued",
                "job_id": job_id
            }
        }
```

### Recommended Strategy for AssistantService

```python
async def query_with_circuit_protection(
    user_query: str,
    context: str,
    user_id: int
):
    """
    Multi-level fallback strategy:
    1. Try LLM (primary)
    2. Try L1 cache (if circuit open)
    3. Return context excerpts (if no cache)
    """
    
    try:
        # Primary path: Full AI generation
        return await generate_answer(user_query, context)
        
    except CircuitBreakerError:
        logger.warning(f"Circuit open for user {user_id}, attempting fallback")
        
        # Fallback 1: L1 cache
        cached = await query_cache.get(user_id, user_query)
        if cached:
            logger.info("Circuit open, L1 cache hit")
            return {
                **cached,
                "metadata": {
                    **cached.get("metadata", {}),
                    "from_fallback": True,
                    "fallback_reason": "circuit_open",
                    "fallback_level": "l1_cache"
                }
            }
        
        # Fallback 2: Simplified response from context
        logger.info("Circuit open, L1 miss, returning excerpts")
        excerpts = extract_top_excerpts(user_query, context, max_excerpts=3)
        
        return {
            "answer": (
                "The AI assistant is temporarily unavailable. "
                "Here are the most relevant excerpts from your sermons:\n\n" +
                "\n\n".join(f"• {e}" for e in excerpts)
            ),
            "sources": [],
            "metadata": {
                "from_fallback": True,
                "fallback_reason": "circuit_open_no_cache",
                "fallback_level": "excerpts"
            }
        }
```

---

## 🧪 Testing Circuit Breakers

### Testing Challenges

Circuit breakers are hard to test because:
- They require **repeated failures** (need to simulate)
- They have **time-based behavior** (need to wait or mock time)
- They have **state transitions** (need to verify state machine)
- They interact with **external services** (need mocking)

### Unit Test Strategy

```python
import pytest
from pybreaker import CircuitBreaker, CircuitBreakerError
import time

class TestCircuitBreaker:
    """Unit tests for circuit breaker behavior"""
    
    def test_closed_state_allows_requests(self):
        """Circuit starts closed and allows requests through"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        
        # Should be closed initially
        assert breaker.current_state == 'closed'
        
        # Should allow calls
        @breaker
        def my_func():
            return "success"
        
        result = my_func()
        assert result == "success"
    
    def test_opens_after_threshold_failures(self):
        """Circuit opens after reaching failure threshold"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=10)
        
        @breaker
        def failing_func():
            raise Exception("Service down")
        
        # Fail 3 times (threshold)
        for i in range(3):
            with pytest.raises(Exception):
                failing_func()
        
        # Circuit should now be open
        assert breaker.current_state == 'open'
        
        # Next call should fail fast without calling function
        with pytest.raises(CircuitBreakerError):
            failing_func()
    
    def test_half_open_after_timeout(self):
        """Circuit transitions to half-open after timeout"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=1)  # 1 second
        
        @breaker
        def failing_func():
            raise Exception("Service down")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                failing_func()
        
        assert breaker.current_state == 'open'
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Check state (accessing state triggers transition)
        assert breaker.current_state == 'half-open'
    
    def test_closes_after_successful_half_open_call(self):
        """Circuit closes after successful call in half-open state"""
        breaker = CircuitBreaker(fail_max=3, timeout_duration=1)
        
        call_count = [0]  # Mutable counter
        
        @breaker
        def sometimes_failing_func():
            call_count[0] += 1
            if call_count[0] <= 3:
                raise Exception("Service down")
            return "success"  # Works after 3 failures
        
        # Open circuit (3 failures)
        for i in range(3):
            with pytest.raises(Exception):
                sometimes_failing_func()
        
        assert breaker.current_state == 'open'
        
        # Wait for timeout → half-open
        time.sleep(1.1)
        
        # Next call should succeed and close circuit
        result = sometimes_failing_func()
        assert result == "success"
        assert breaker.current_state == 'closed'
```

### Integration Test Strategy

```python
@pytest.mark.asyncio
async def test_circuit_breaker_with_huggingface_timeout():
    """Test circuit breaker with actual HuggingFace service timeout"""
    
    # Create breaker with low threshold for testing
    test_breaker = CircuitBreaker(fail_max=2, timeout_duration=5)
    
    @async_circuit_breaker(test_breaker)
    async def call_hf_with_timeout(prompt: str):
        async with httpx.AsyncClient(timeout=0.1) as client:  # Very short timeout
            response = await client.post(
                "https://api-inference.huggingface.co/...",
                json={"inputs": prompt}
            )
            return response.json()
    
    # First 2 calls should timeout and fail
    for i in range(2):
        with pytest.raises(httpx.TimeoutError):
            await call_hf_with_timeout("test")
    
    # Circuit should now be open
    assert test_breaker.current_state == 'open'
    
    # Next call should fail fast
    with pytest.raises(CircuitBreakerError):
        await call_hf_with_timeout("test")

@pytest.mark.asyncio
async def test_fallback_to_cache_when_circuit_open():
    """Test that cache fallback works when circuit is open"""
    
    # Manually open circuit
    test_breaker.call_failed()
    test_breaker.call_failed()
    test_breaker.call_failed()
    
    assert test_breaker.current_state == 'open'
    
    # Call assistant service
    result = await assistant_service.query(
        user_query="What is faith?",
        user_id=1,
        db=db_session
    )
    
    # Should return cached response
    assert result is not None
    assert result["metadata"]["from_fallback"] == True
```

### Load Test Strategy

```python
import asyncio
from locust import HttpUser, task, between

class CircuitBreakerLoadTest(HttpUser):
    """Load test to verify circuit breaker under stress"""
    
    wait_time = between(1, 3)
    
    @task
    def query_assistant(self):
        """Repeatedly query assistant to trigger failures"""
        
        response = self.client.post(
            "/api/assistant/query",
            json={
                "query": "What is grace?",
                "include_metadata": True
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 503:
            # Circuit is open - verify fallback metadata
            data = response.json()
            assert "from_fallback" in data.get("metadata", {})
            print("✅ Circuit open, fallback working")
        
        elif response.status_code == 200:
            # Normal response
            print("✅ Normal response")
        
        else:
            print(f"❌ Unexpected status: {response.status_code}")

# Run test:
# locust -f test_circuit_load.py --host=http://localhost:8000
```

---

## 🏭 Production Considerations

### Configuration Values

```python
# Production-recommended configuration
PRODUCTION_CONFIG = {
    "fail_max": 5,
    # 5 failures is enough to confirm service is down
    # Not too sensitive (won't trip on single timeout)
    # Not too lenient (won't let too many requests fail)
    
    "timeout_duration": 30,
    # 30 seconds gives service time to recover
    # Not too short (service needs recovery time)
    # Not too long (users wait for service to come back)
    
    "reset_timeout": 60,
    # Count failures in last 60 seconds
    # Transient errors older than 1 min don't count
    
    "exclude": [
        ValueError,           # Input validation
        httpx.HTTPStatusError # 4xx client errors
    ],
    
    "name": "huggingface_api"
}
```

### Monitoring and Alerting

```python
from prometheus_client import Counter, Gauge

# Metrics
circuit_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['breaker_name']
)

circuit_failures = Counter(
    'circuit_breaker_failures_total',
    'Total failures detected by circuit breaker',
    ['breaker_name']
)

circuit_openings = Counter(
    'circuit_breaker_openings_total',
    'Number of times circuit has opened',
    ['breaker_name']
)

# Listener to update metrics
class PrometheusListener(CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        state_map = {'closed': 0, 'open': 1, 'half-open': 2}
        circuit_state.labels(cb.name).set(state_map[new_state])
        
        if new_state == 'open':
            circuit_openings.labels(cb.name).inc()
    
    def failure(self, cb, exc):
        circuit_failures.labels(cb.name).inc()
```

### Logging

```python
import logging

class LoggingListener(CircuitBreakerListener):
    """Log all circuit breaker events"""
    
    def __init__(self):
        self.logger = logging.getLogger('circuit_breaker')
    
    def state_change(self, cb, old_state, new_state):
        self.logger.warning(
            f"Circuit breaker state change",
            extra={
                "breaker": cb.name,
                "old_state": old_state,
                "new_state": new_state,
                "fail_count": cb.fail_counter
            }
        )
    
    def failure(self, cb, exc):
        self.logger.error(
            f"Circuit breaker failure",
            extra={
                "breaker": cb.name,
                "exception": str(exc),
                "fail_count": cb.fail_counter,
                "state": cb.current_state
            }
        )
```

### Health Check Endpoint

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health/circuit-breakers")
async def get_circuit_breaker_status():
    """Health check for circuit breakers"""
    return {
        "huggingface": {
            "state": hf_breaker.current_state,
            "fail_count": hf_breaker.fail_counter,
            "last_failure": hf_breaker.last_failure_time,
            "healthy": hf_breaker.current_state == 'closed'
        }
    }
```

---

## ✅ Prerequisites Checklist

Before implementing Phase 4, ensure you understand:

### Conceptual Understanding
- [ ] **Circuit Breaker Pattern** - 3 states, state transitions, purpose
- [ ] **Failure vs Success** - What counts as a failure
- [ ] **Graceful Degradation** - Fallback strategies
- [ ] **State Machine** - CLOSED → OPEN → HALF-OPEN → CLOSED

### Technical Knowledge
- [ ] **PyBreaker API** - CircuitBreaker class, configuration options
- [ ] **Async Integration** - How to use sync breaker with async code
- [ ] **Exception Handling** - CircuitBreakerError, expected_exception, exclude
- [ ] **Listeners** - How to attach monitoring/logging

### Design Patterns
- [ ] **Fallback Hierarchy** - Primary → Cache → Simplified → Error
- [ ] **Failure Detection** - Which exceptions to count
- [ ] **Configuration** - fail_max, timeout_duration, reset_timeout
- [ ] **State Inspection** - current_state, fail_counter

### Testing Strategies
- [ ] **Unit Tests** - State transitions, thresholds, timeouts
- [ ] **Integration Tests** - Real service failures, fallbacks
- [ ] **Load Tests** - Circuit behavior under stress

### Production Concerns
- [ ] **Monitoring** - Prometheus metrics, Grafana dashboards
- [ ] **Alerting** - When circuit opens, high failure rates
- [ ] **Logging** - State changes, failures, recoveries
- [ ] **Health Checks** - Circuit status endpoints

---

## 📚 Further Reading

### Official Documentation
- [PyBreaker GitHub](https://github.com/danielfm/pybreaker)
- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Release It! Book](https://pragprog.com/titles/mnee2/release-it-second-edition/)

### Python Async Resources
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [AsyncIO Exception Handling](https://docs.python.org/3/library/asyncio-exceptions.html)
- [HTTPX Async Client](https://www.python-httpx.org/async/)

### Fault Tolerance Patterns
- [Bulkhead Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
- [Retry Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)
- [Timeout Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/timeout)

---

## 🎯 Next Steps

Once you've reviewed this prerequisites guide:

1. ✅ **Mark checklist items** as you understand each concept
2. 📖 **Read the Implementation Plan** (`PHASE_4_IMPLEMENTATION_PLAN.md`)
3. 🧪 **Review the Testing Strategy** (`PHASE_4_TESTING_STRATEGY.md`)
4. 🚀 **Begin implementation** following the step-by-step guide

---

**Document Status:** ✅ COMPLETE  
**Last Updated:** December 27, 2025  
**Next Document:** [Phase 4 Implementation Plan](./PHASE_4_IMPLEMENTATION_PLAN.md)
