# Tokenizer Service Observability & Metrics Strategy

**Project:** Scribes AI Assistant  
**Component:** TokenizerService  
**Date:** December 9, 2025  
**Status:** Implementation Ready

---

## Executive Summary

**YES - Observability metrics are CRITICAL for TokenizerService** because:

1. **Performance Monitoring:** Detect degradation before users complain
2. **Budget Enforcement:** Ensure token limits aren't exceeded (prevents generation failures)
3. **Cost Tracking:** Monitor token usage for API billing (if using HF Inference API)
4. **Anomaly Detection:** Catch unusual patterns (attacks, bugs, data quality issues)
5. **Capacity Planning:** Understand usage patterns for scaling decisions

**Recommendation:** Implement **3-tier metrics approach**:
- **Tier 1 (Essential):** Performance counters + error tracking → **Implement NOW**
- **Tier 2 (Important):** Business metrics + usage patterns → **Implement in 2 weeks**
- **Tier 3 (Advanced):** Distributed tracing + cost analytics → **Phase 7**

---

## 1. Why Observability Matters for Tokenizer

### 1.1 Critical Questions We Need to Answer

| Question | Why It Matters | Without Metrics |
|----------|----------------|-----------------|
| **"Is tokenization slow?"** | Slow tokenization blocks assistant queries | Can't detect until users complain |
| **"Are we staying within token budgets?"** | Exceeding limits = generation failures | Silent failures, poor UX |
| **"How much text are users sending?"** | Capacity planning, abuse detection | Can't scale proactively |
| **"Are truncations happening?"** | Indicates users losing data | Users don't know their content was cut |
| **"Which operations are expensive?"** | Optimize hot paths | Wasted engineering time |

### 1.2 Real-World Scenarios

**Scenario 1: Performance Degradation**
```
Week 1: chunk_text() avg = 15ms
Week 2: chunk_text() avg = 150ms (10x slower!)
Cause: User uploaded 100k-word sermon transcript
Without metrics: Users complain "assistant is slow" - you have no data
With metrics: Alert fires → investigate → add async wrapper for large texts
```

**Scenario 2: Budget Violations**
```
User query: "Summarize all my notes about faith"
Notes retrieved: 50 chunks × 384 tokens = 19,200 tokens
Token budget: 1,200 tokens
Without metrics: Context builder silently truncates → user gets incomplete answer
With metrics: You see "context_overflow" alert → redesign chunking strategy
```

**Scenario 3: Abuse Detection**
```
Attacker sends 1M-character query to DoS the service
Without metrics: Tokenizer hangs, entire service goes down
With metrics: "text_length_exceeded" alert → rate limit activated
```

---

## 2. Metrics Categories

### 2.1 Performance Metrics (Latency & Throughput)

**What to measure:**
- **Latency (p50, p95, p99)** for each operation
- **Throughput** (operations per second)
- **Queue depth** (if using async wrappers)

**Why:**
- Detect performance regressions
- Identify slow outliers
- Validate optimization efforts

### 2.2 Business Metrics (Token Usage)

**What to measure:**
- **Token counts** (input, output, total)
- **Truncation frequency**
- **Budget violations**
- **Chunk counts** per note

**Why:**
- Ensure token budgets respected
- Track API costs (HF charges per token)
- Understand user behavior

### 2.3 Error Metrics

**What to measure:**
- **Error rate** (tokenization failures)
- **Fallback triggers** (estimate_tokens() usage)
- **Validation errors** (invalid inputs)

**Why:**
- Catch edge cases early
- Measure system reliability
- Debug production issues

### 2.4 Resource Metrics

**What to measure:**
- **Memory usage** (tokenizer model size)
- **CPU utilization** (during tokenization)
- **Thread pool stats** (if using async)

**Why:**
- Prevent OOM crashes
- Right-size infrastructure
- Optimize resource allocation

---

## 3. Implementation Approaches

### 3.1 Option 1: Simple Logging (Tier 1 - Start Here) ✅

**Pros:**
- ✅ Zero dependencies
- ✅ Works with existing `logger`
- ✅ Quick to implement (1 hour)
- ✅ Easy to parse with log aggregators (Datadog, Splunk)

**Cons:**
- ❌ Not real-time
- ❌ Manual aggregation needed
- ❌ No built-in dashboards

**Implementation:**
```python
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def log_performance(operation_name: str):
    """Decorator to log performance metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # Log metrics in structured format
                logger.info(
                    "tokenizer_operation",
                    extra={
                        "operation": operation_name,
                        "duration_ms": duration_ms,
                        "status": "success",
                        "args_count": len(args),
                    }
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    "tokenizer_operation_failed",
                    extra={
                        "operation": operation_name,
                        "duration_ms": duration_ms,
                        "status": "error",
                        "error": str(e),
                    }
                )
                raise
        return wrapper
    return decorator

# Usage
class TokenizerService:
    @log_performance("count_tokens")
    def count_tokens(self, text: str) -> int:
        # ... existing implementation
        pass
```

**Log Query Example (Datadog):**
```
# Find slow tokenizations
operation:count_tokens duration_ms:>50

# Count errors
operation:chunk_text status:error | count by error
```

### 3.2 Option 2: Prometheus Metrics (Tier 2 - Production)

**Pros:**
- ✅ Industry standard
- ✅ Real-time dashboards (Grafana)
- ✅ Alerting built-in
- ✅ Time-series analysis

**Cons:**
- ❌ Requires Prometheus server
- ❌ More complex setup
- ❌ Needs `/metrics` endpoint

**Dependencies:**
```bash
pip install prometheus-client
```

**Implementation:**
```python
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Define metrics
TOKENIZER_OPERATIONS = Counter(
    'tokenizer_operations_total',
    'Total tokenizer operations',
    ['operation', 'status']
)

TOKENIZER_LATENCY = Histogram(
    'tokenizer_operation_duration_seconds',
    'Tokenizer operation latency',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

TOKEN_COUNTS = Histogram(
    'tokenizer_token_count',
    'Token counts processed',
    ['operation'],
    buckets=[10, 50, 100, 200, 384, 512, 1000, 2000, 5000]
)

TRUNCATION_EVENTS = Counter(
    'tokenizer_truncations_total',
    'Number of truncation events',
    ['operation']
)

TOKENIZER_ERRORS = Counter(
    'tokenizer_errors_total',
    'Tokenizer errors',
    ['operation', 'error_type']
)

def observe_metrics(operation_name: str):
    """Decorator to record Prometheus metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                
                # Record success
                TOKENIZER_OPERATIONS.labels(
                    operation=operation_name,
                    status='success'
                ).inc()
                
                # Record latency
                duration = time.perf_counter() - start_time
                TOKENIZER_LATENCY.labels(operation=operation_name).observe(duration)
                
                return result
            except Exception as e:
                # Record error
                TOKENIZER_OPERATIONS.labels(
                    operation=operation_name,
                    status='error'
                ).inc()
                
                TOKENIZER_ERRORS.labels(
                    operation=operation_name,
                    error_type=type(e).__name__
                ).inc()
                
                raise
        return wrapper
    return decorator

# Usage in TokenizerService
class TokenizerService:
    @observe_metrics("count_tokens")
    def count_tokens(self, text: str) -> int:
        if not text or not isinstance(text, str):
            return 0
        
        try:
            tokens = self.tokenizer.encode(text, add_special_tokens=True)
            token_count = len(tokens)
            
            # Record token count distribution
            TOKEN_COUNTS.labels(operation='count_tokens').observe(token_count)
            
            return token_count
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}. Falling back to estimate.")
            return self.estimate_tokens(text)
    
    @observe_metrics("truncate_to_tokens")
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        # ... existing validation ...
        
        current_tokens = self.count_tokens(text)
        if current_tokens <= max_tokens:
            return text
        
        # Record truncation event
        TRUNCATION_EVENTS.labels(operation='truncate_to_tokens').inc()
        
        logger.debug(f"Truncating text from {current_tokens} to {max_tokens} tokens")
        
        # ... existing truncation logic ...
```

**Grafana Dashboard Queries:**
```promql
# Average tokenization latency (p50, p95, p99)
histogram_quantile(0.50, tokenizer_operation_duration_seconds_bucket{operation="count_tokens"})
histogram_quantile(0.95, tokenizer_operation_duration_seconds_bucket{operation="count_tokens"})
histogram_quantile(0.99, tokenizer_operation_duration_seconds_bucket{operation="count_tokens"})

# Tokenization throughput (ops/sec)
rate(tokenizer_operations_total{status="success"}[1m])

# Error rate (%)
100 * rate(tokenizer_operations_total{status="error"}[5m]) / rate(tokenizer_operations_total[5m])

# Truncation frequency
rate(tokenizer_truncations_total[5m])

# Token count distribution
histogram_quantile(0.95, tokenizer_token_count_bucket{operation="count_tokens"})
```

### 3.3 Option 3: Custom Metrics Class (Tier 2 - Flexible)

**Pros:**
- ✅ Framework-agnostic
- ✅ Can switch backends later
- ✅ Custom business logic
- ✅ Easy testing

**Cons:**
- ❌ More code to maintain
- ❌ No built-in visualization

**Implementation:**
```python
from typing import Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import time

@dataclass
class MetricSnapshot:
    """Single metric observation."""
    operation: str
    duration_ms: float
    token_count: Optional[int] = None
    text_length: Optional[int] = None
    status: str = "success"
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

class TokenizerMetrics:
    """
    Centralized metrics collector for TokenizerService.
    
    Collects metrics in-memory and can export to various backends
    (Prometheus, Datadog, CloudWatch, etc.)
    """
    
    def __init__(self):
        self._operations: List[MetricSnapshot] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._start_time = time.time()
    
    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        status: str = "success",
        token_count: Optional[int] = None,
        text_length: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Record a single operation."""
        snapshot = MetricSnapshot(
            operation=operation,
            duration_ms=duration_ms,
            token_count=token_count,
            text_length=text_length,
            status=status,
            error=error
        )
        self._operations.append(snapshot)
        self._counters[f"{operation}_{status}"] += 1
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated statistics."""
        ops = [op for op in self._operations if operation is None or op.operation == operation]
        
        if not ops:
            return {}
        
        durations = [op.duration_ms for op in ops if op.status == "success"]
        token_counts = [op.token_count for op in ops if op.token_count is not None]
        
        return {
            "total_operations": len(ops),
            "success_count": sum(1 for op in ops if op.status == "success"),
            "error_count": sum(1 for op in ops if op.status == "error"),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "p95_duration_ms": self._percentile(durations, 0.95) if durations else 0,
            "p99_duration_ms": self._percentile(durations, 0.99) if durations else 0,
            "avg_tokens": sum(token_counts) / len(token_counts) if token_counts else 0,
            "uptime_seconds": time.time() - self._start_time
        }
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        # Implementation for Prometheus exposition format
        pass
    
    def export_json(self) -> Dict[str, Any]:
        """Export metrics as JSON."""
        return {
            "summary": self.get_stats(),
            "operations": [
                {
                    "operation": op.operation,
                    "duration_ms": op.duration_ms,
                    "status": op.status,
                    "timestamp": op.timestamp.isoformat()
                }
                for op in self._operations[-100:]  # Last 100 operations
            ]
        }

# Global metrics instance
_tokenizer_metrics = TokenizerMetrics()

def get_tokenizer_metrics() -> TokenizerMetrics:
    """Get global metrics instance."""
    return _tokenizer_metrics

# Usage in TokenizerService
class TokenizerService:
    def __init__(self, ...):
        # ... existing init ...
        self.metrics = get_tokenizer_metrics()
    
    def count_tokens(self, text: str) -> int:
        start_time = time.perf_counter()
        
        if not text or not isinstance(text, str):
            return 0
        
        try:
            tokens = self.tokenizer.encode(text, add_special_tokens=True)
            token_count = len(tokens)
            
            # Record metrics
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.metrics.record_operation(
                operation="count_tokens",
                duration_ms=duration_ms,
                status="success",
                token_count=token_count,
                text_length=len(text)
            )
            
            return token_count
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.metrics.record_operation(
                operation="count_tokens",
                duration_ms=duration_ms,
                status="error",
                error=str(e)
            )
            logger.warning(f"Error counting tokens: {e}. Falling back to estimate.")
            return self.estimate_tokens(text)
```

---

## 4. Recommended Metrics to Track

### 4.1 Essential Metrics (Tier 1 - Implement Now)

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `count_tokens_latency_ms` | Histogram | Detect slow tokenizations | p99 > 50ms |
| `chunk_text_latency_ms` | Histogram | Monitor chunking performance | p99 > 200ms |
| `truncate_latency_ms` | Histogram | Track truncation overhead | p99 > 100ms |
| `tokenizer_errors_total` | Counter | Track failure rate | Error rate > 1% |
| `fallback_triggered_total` | Counter | Monitor estimate_tokens() usage | > 10 calls/min |

### 4.2 Business Metrics (Tier 2 - Week 2)

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `tokens_processed_total` | Counter | Track total token usage | - |
| `token_count_distribution` | Histogram | Understand input sizes | p95 > 2000 tokens |
| `truncation_events_total` | Counter | Track data loss | > 100/hour |
| `chunk_count_distribution` | Histogram | Monitor chunking patterns | avg > 20 chunks/note |
| `text_length_bytes` | Histogram | Input size distribution | p99 > 100KB |

### 4.3 Advanced Metrics (Tier 3 - Phase 7)

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `tokens_per_user` | Gauge | Track per-user usage | > 100K tokens/day |
| `tokenizer_memory_bytes` | Gauge | Monitor memory usage | > 2GB |
| `thread_pool_queue_depth` | Gauge | Async wrapper backlog | > 50 |
| `cost_per_operation_usd` | Counter | API cost tracking | - |

---

## 5. Implementation Roadmap

### Phase 1: Basic Observability (Week 1) ✅ START HERE

**Goal:** Get visibility into performance and errors

**Tasks:**
1. Add structured logging to all methods
2. Log latency, token counts, errors
3. Set up log aggregation (if not already)
4. Create basic dashboard (log queries)

**Effort:** 4-6 hours

**Code Changes:**
```python
# Add to each method
import time

def count_tokens(self, text: str) -> int:
    start = time.perf_counter()
    try:
        # ... existing logic ...
        result = len(tokens)
        
        # Log metrics
        logger.info(
            "tokenizer.count_tokens",
            extra={
                "duration_ms": (time.perf_counter() - start) * 1000,
                "token_count": result,
                "text_length": len(text),
                "status": "success"
            }
        )
        return result
    except Exception as e:
        logger.error(
            "tokenizer.count_tokens.error",
            extra={
                "duration_ms": (time.perf_counter() - start) * 1000,
                "error": str(e),
                "status": "error"
            }
        )
        raise
```

### Phase 2: Prometheus Integration (Week 2-3)

**Goal:** Real-time metrics and alerting

**Tasks:**
1. Install `prometheus-client`
2. Define metrics (counters, histograms)
3. Add `/metrics` endpoint to FastAPI
4. Set up Prometheus scraper
5. Create Grafana dashboards
6. Configure alerts

**Effort:** 2-3 days

**Alert Rules:**
```yaml
# prometheus_alerts.yml
groups:
  - name: tokenizer
    rules:
      - alert: TokenizerHighLatency
        expr: histogram_quantile(0.99, tokenizer_operation_duration_seconds_bucket{operation="chunk_text"}) > 0.2
        for: 5m
        annotations:
          summary: "Tokenizer chunking is slow (p99 > 200ms)"
      
      - alert: TokenizerHighErrorRate
        expr: rate(tokenizer_errors_total[5m]) / rate(tokenizer_operations_total[5m]) > 0.01
        for: 5m
        annotations:
          summary: "Tokenizer error rate > 1%"
      
      - alert: HighTruncationRate
        expr: rate(tokenizer_truncations_total[5m]) > 2
        for: 10m
        annotations:
          summary: "Frequent truncations detected (>2/min)"
```

### Phase 3: Advanced Analytics (Phase 7)

**Goal:** Cost tracking, capacity planning, anomaly detection

**Tasks:**
1. Add per-user metrics
2. Implement cost tracking
3. Set up anomaly detection (ML-based)
4. Create executive dashboards
5. Add usage forecasting

**Effort:** 1-2 weeks

---

## 6. Dashboard Design

### 6.1 Operational Dashboard (Engineers)

**Panels:**
1. **Latency Trends** (p50, p95, p99 over time)
2. **Throughput** (operations/sec)
3. **Error Rate** (%)
4. **Operation Mix** (pie chart: count_tokens vs chunk_text vs truncate)
5. **Recent Errors** (table: timestamp, operation, error)

**Refresh:** 10 seconds

### 6.2 Business Dashboard (Product/Management)

**Panels:**
1. **Total Tokens Processed** (today, this week, this month)
2. **Truncation Events** (count + trend)
3. **Average Query Size** (tokens)
4. **Top Users by Token Usage** (table)
5. **Cost Projection** (if using API)

**Refresh:** 1 minute

### 6.3 Example Grafana Panel Queries

```promql
# Panel 1: Latency by operation (p95)
histogram_quantile(0.95, sum(rate(tokenizer_operation_duration_seconds_bucket[5m])) by (operation, le))

# Panel 2: Throughput
sum(rate(tokenizer_operations_total{status="success"}[1m])) by (operation)

# Panel 3: Error rate (%)
100 * (
  sum(rate(tokenizer_operations_total{status="error"}[5m]))
  /
  sum(rate(tokenizer_operations_total[5m]))
)

# Panel 4: Token count distribution
histogram_quantile(0.95, sum(rate(tokenizer_token_count_bucket[5m])) by (le))

# Panel 5: Truncations per hour
sum(increase(tokenizer_truncations_total[1h]))
```

---

## 7. Alerting Strategy

### 7.1 Critical Alerts (Page Immediately)

| Alert | Condition | Action |
|-------|-----------|--------|
| **TokenizerDown** | No metrics in 5 min | Check service health |
| **ExtremeLatency** | p99 > 1 second | Investigate load/resources |
| **HighErrorRate** | Errors > 5% | Check logs, rollback if needed |

### 7.2 Warning Alerts (Slack/Email)

| Alert | Condition | Action |
|-------|-----------|--------|
| **SlowChunking** | chunk_text p99 > 200ms | Consider async wrapper |
| **FrequentTruncation** | > 100 truncations/hour | Review token budgets |
| **HighMemory** | Tokenizer memory > 2GB | Check for leaks |

### 7.3 Info Alerts (Monitoring Channel)

| Alert | Condition | Action |
|-------|-----------|--------|
| **UnusualTokenCount** | p95 > 5000 tokens | Monitor for abuse |
| **LowUsage** | < 10 ops/min (during peak) | Check if frontend broken |

---

## 8. Cost Tracking (If Using HF API)

### 8.1 Token-Based Billing

**HuggingFace Pricing (example):**
- $0.06 per 1M tokens (input)
- $0.12 per 1M tokens (output)

**Metrics to track:**
```python
# Track tokens sent to API
HF_API_TOKENS_SENT = Counter(
    'hf_api_tokens_sent_total',
    'Total tokens sent to HF API',
    ['model', 'operation']
)

# Track estimated cost
HF_API_COST_USD = Counter(
    'hf_api_cost_usd_total',
    'Estimated HF API cost in USD',
    ['model']
)

# In generation service
def generate(self, prompt: str, max_new_tokens: int) -> str:
    input_tokens = self.tokenizer.count_tokens(prompt)
    
    # Record input tokens
    HF_API_TOKENS_SENT.labels(
        model=self.model_name,
        operation='input'
    ).inc(input_tokens)
    
    # Estimate cost ($0.06 per 1M input tokens)
    input_cost = (input_tokens / 1_000_000) * 0.06
    HF_API_COST_USD.labels(model=self.model_name).inc(input_cost)
    
    # ... make API call ...
    
    output_tokens = self.tokenizer.count_tokens(response)
    HF_API_TOKENS_SENT.labels(
        model=self.model_name,
        operation='output'
    ).inc(output_tokens)
    
    output_cost = (output_tokens / 1_000_000) * 0.12
    HF_API_COST_USD.labels(model=self.model_name).inc(output_cost)
    
    return response
```

**Dashboard Query:**
```promql
# Total cost today
sum(increase(hf_api_cost_usd_total[24h]))

# Cost per user (requires user label)
topk(10, sum(increase(hf_api_cost_usd_total[24h])) by (user_id))

# Cost projection (next 30 days)
sum(increase(hf_api_cost_usd_total[7d])) * 4.3
```

---

## 9. Testing Metrics

### 9.1 Unit Tests for Metrics

```python
# tests/test_tokenizer_metrics.py
import pytest
from app.services.tokenizer_service import TokenizerService, get_tokenizer_metrics

def test_count_tokens_records_metrics():
    """Verify metrics are recorded on count_tokens()."""
    service = TokenizerService()
    metrics = get_tokenizer_metrics()
    
    # Clear previous metrics
    metrics._operations.clear()
    
    # Perform operation
    text = "Hello world"
    result = service.count_tokens(text)
    
    # Check metrics recorded
    stats = metrics.get_stats("count_tokens")
    assert stats["total_operations"] == 1
    assert stats["success_count"] == 1
    assert stats["error_count"] == 0
    assert stats["avg_duration_ms"] > 0

def test_metrics_on_error():
    """Verify errors are tracked."""
    service = TokenizerService()
    metrics = get_tokenizer_metrics()
    
    metrics._operations.clear()
    
    # Trigger error
    with pytest.raises(ValueError):
        service.truncate_to_tokens("test", -1)  # Invalid max_tokens
    
    stats = metrics.get_stats("truncate_to_tokens")
    assert stats["error_count"] == 1
```

### 9.2 Load Testing with Metrics

```python
# tests/test_tokenizer_load.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

def test_tokenizer_under_load():
    """Stress test tokenizer and verify metrics."""
    service = TokenizerService()
    metrics = get_tokenizer_metrics()
    
    # Simulate 1000 concurrent requests
    texts = ["Test sermon " * 100 for _ in range(1000)]
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(service.count_tokens, texts))
    duration = time.time() - start
    
    # Verify all succeeded
    assert len(results) == 1000
    
    # Check metrics
    stats = metrics.get_stats("count_tokens")
    assert stats["total_operations"] >= 1000
    assert stats["p99_duration_ms"] < 100  # p99 under 100ms
    
    # Check throughput
    throughput = 1000 / duration
    assert throughput > 100  # At least 100 ops/sec
```

---

## 10. Recommended Implementation

### 10.1 Start Simple, Iterate

**Week 1: Structured Logging**
```python
# Add to tokenizer_service.py
import time
import logging

logger = logging.getLogger(__name__)

def _log_operation(operation: str, duration_ms: float, **kwargs):
    """Helper to log metrics in consistent format."""
    logger.info(
        f"tokenizer.{operation}",
        extra={
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            **kwargs
        }
    )

# Use in methods
def count_tokens(self, text: str) -> int:
    start = time.perf_counter()
    # ... logic ...
    _log_operation(
        "count_tokens",
        (time.perf_counter() - start) * 1000,
        token_count=result,
        text_length=len(text)
    )
    return result
```

**Week 2-3: Add Prometheus** (if running in production)

**Phase 7: Advanced analytics** (cost tracking, ML anomaly detection)

---

## 11. Summary & Action Plan

### ✅ YES - Implement Observability

**Recommended Approach:**
1. **Now:** Add structured logging (4 hours)
2. **Week 2:** Prometheus + Grafana (2 days)
3. **Week 3:** Alerts + dashboards (1 day)
4. **Phase 7:** Advanced analytics (1 week)

**Key Metrics (Priority Order):**
1. **Latency** (p50, p95, p99) - detect performance issues
2. **Error rate** - measure reliability
3. **Token counts** - track usage & costs
4. **Truncation events** - prevent data loss
5. **Throughput** - capacity planning

**Tools:**
- **Logging:** Python `logging` module ✅ (already have)
- **Metrics:** Prometheus + Grafana
- **Alerting:** Prometheus Alertmanager
- **Visualization:** Grafana dashboards

**ROI:**
- Catch issues before users complain
- Optimize hot paths with data
- Track costs accurately
- Scale proactively
- Improve system reliability

---

**Next Steps:** Say "implement tier 1 metrics" and I'll add structured logging to your TokenizerService.

**Document Status:** Final  
**Owner:** Joshua  
**Review Date:** After 1 month of metrics collection
