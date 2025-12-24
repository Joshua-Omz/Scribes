# Gateway-First Architecture

**Clean Separation: What Lives Where**

This document clarifies the architectural boundary between **API Gateway responsibilities** and **FastAPI Service responsibilities** for production-ready systems.

---

## 🏛️ The Mental Model

```
Client (Mobile/Web)
    ↓
┌─────────────────────────────────────────────────┐
│          API GATEWAY / CLOUD PLATFORM           │
│                                                 │
│  Handles: Cross-cutting, infrastructure concerns│
│  - Rate limiting (per-IP, per-user, global)    │
│  - Authentication & authorization              │
│  - Edge caching (static content, read-heavy)   │
│  - Request correlation IDs                     │
│  - Global retries & timeouts                   │
│  - Load balancing                              │
│  - SSL termination                             │
│  - DDoS protection                             │
│  - Traffic metrics (RPS, latency, errors)      │
│                                                 │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│         FASTAPI SERVICE (AssistantService)      │
│                                                 │
│  Handles: Domain-specific, AI concerns         │
│  - AI-specific caching (semantic queries)      │
│  - LLM circuit breakers (HuggingFace)          │
│  - Cost tracking (token usage)                 │
│  - Semantic metrics (quality, relevance)       │
│  - Business logic (RAG pipeline)               │
│  - Domain errors                               │
│                                                 │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
      ▼           ▼           ▼
  PostgreSQL   Redis     HuggingFace
  (pgvector)   (Cache)   (LLM API)
```

---

## ❌ What Does NOT Belong in FastAPI

These are **gateway responsibilities**. Don't duplicate them in your service.

### 1. Rate Limiting

**Why gateway?**
- Applies to *all services* (Notes, Circles, Assistant, etc.)
- Stops traffic *before* it hits Python (CPU/memory savings)
- Centralized configuration
- Per-IP and per-user limits
- No code duplication

**Gateway implementation:**
```yaml
# Example: Kong, AWS API Gateway, Azure APIM
rate_limiting:
  per_user: 10/minute
  per_ip: 100/minute
  global: 1000/concurrent
```

**FastAPI: Nothing needed** ✅

**What we removed:**
- ❌ `app/middleware/rate_limiter.py` (439 lines)
- ❌ `app/core/redis.py` (68 lines for rate limiting)
- ❌ `slowapi` dependency
- ❌ Rate limit checks in routes
- ❌ Rate limit configuration (8 settings)

---

### 2. Global Traffic Metrics

**Why gateway?**
- RPS, latency, error rates apply to all services
- Gateway already sees all traffic
- Prometheus/Grafana integration at gateway level
- No per-service instrumentation needed

**Gateway provides:**
- `http_requests_total` (counter)
- `http_request_duration_seconds` (histogram)
- `http_requests_in_flight` (gauge)

**FastAPI: Don't duplicate** ✅

**What we removed:**
- ❌ `prometheus-fastapi-instrumentator` dependency
- ❌ Global metrics endpoints
- ❌ Traffic monitoring middleware

---

### 3. Edge Caching (Static Content)

**Why gateway?**
- Faster than Python + Redis
- Lower infrastructure cost
- Zero service code

**Good for:**
- Scripture lookups (rarely change)
- Static AI prompts
- Read-heavy GET endpoints

**Gateway implementation:**
```yaml
# Example: CDN, API Gateway cache
cache:
  scripture_lookup: 24h
  user_profile: 5m
  static_content: 1w
```

**FastAPI: Only domain-specific caching** ✅ (see below)

---

### 4. Request Correlation IDs

**Why gateway?**
- Gateway generates `X-Request-ID`
- Services just propagate it
- Consistent across all services

**Gateway injects:**
```http
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Trace-ID: 7d9e3b4a-8f1c-4d5e-9a2b-1c3d4e5f6a7b
```

**FastAPI: Use it, don't create it** ✅

---

## ✅ What DOES Belong in FastAPI

These are **service responsibilities**. Gateway can't handle these.

### 1. AI-Specific Caching ⭐

**Why service?**
Gateway doesn't understand:
- Semantic similarity (same question, different words)
- User context (personalized responses)
- Embedding reuse

**What to cache:**

#### L1: Query Result Cache
```python
# Cache complete AI responses
cache_key = hash(query_text + user_id + context_ids)
ttl = 24h  # Repeated questions
```

#### L2: Embedding Cache
```python
# Cache query embeddings (expensive to compute)
cache_key = hash(query_text)
ttl = 7d  # Reuse for similar queries
```

#### L3: Context Cache
```python
# Cache retrieved sermon chunks
cache_key = hash(query_embedding)
ttl = 1h  # Recent searches
```

**Implementation:**
```python
# Keep: AI caching with Redis
from aiocache import Cache
cache = Cache.REDIS(endpoint=redis_url, namespace="ai")
```

**Expected impact:**
- 60-80% cost reduction
- <1s cached responses
- Semantic deduplication

---

### 2. Circuit Breakers (LLM Dependencies) ⭐

**Why service?**
- Gateway protects *services*
- Service protects *external dependencies*

**What to protect:**
- HuggingFace API (LLM generation)
- Embedding models (if external)
- Vector search (if cloud-hosted)

**Implementation:**
```python
# Keep: Circuit breaker for LLM
from pybreaker import CircuitBreaker

llm_breaker = CircuitBreaker(
    fail_max=5,         # Open after 5 failures
    timeout_duration=30  # Retry after 30s
)

@llm_breaker
async def call_huggingface(prompt: str):
    # Call LLM API
    pass
```

**Graceful degradation:**
- Return cached response if circuit open
- User-friendly error message
- Automatic recovery when LLM healthy

---

### 3. Cost Tracking (Token Usage) ⭐

**Why service?**
Only the service knows:
- Token counts (query, context, output)
- Model pricing ($/token)
- Prompt size

Gateway sees requests, not tokens.

**Implementation:**
```python
# Keep: Calculate cost per request
def calculate_cost(metadata: dict) -> float:
    input_tokens = metadata["query_tokens"] + metadata["context_tokens"]
    output_tokens = metadata["output_tokens"]
    
    # Llama-3.2-3B pricing
    input_cost = input_tokens * 0.0000002
    output_cost = output_tokens * 0.0000006
    
    return input_cost + output_cost
```

**Return in metadata:**
```json
{
  "answer": "...",
  "metadata": {
    "api_cost_usd": 0.00026,
    "query_tokens": 45,
    "context_tokens": 850,
    "output_tokens": 120
  }
}
```

---

### 4. Semantic Metrics ⭐

**Why service?**
Gateway doesn't understand:
- Answer quality
- Context relevance
- No-context detection rate

**What to track:**
```python
# Service-specific metrics (OpenTelemetry)
metrics = {
    "ai_query_quality_score": histogram,      # 0-1 quality
    "ai_context_relevance_score": histogram,  # 0-1 relevance
    "ai_no_context_responses_total": counter, # Answered without context
    "ai_cache_hit_rate": gauge,               # AI cache efficiency
    "ai_token_usage_total": counter           # Token consumption
}
```

---

### 5. Domain Errors ⭐

**Why service?**
- Gateway normalizes HTTP errors (502, 504, 429)
- Service raises domain-specific errors

**Service responsibility:**
```python
class InsufficientContextError(Exception):
    """Not enough sermon content to answer."""

class EmbeddingFailureError(Exception):
    """Failed to embed query."""

class LLMTimeoutError(Exception):
    """LLM took too long to respond."""
```

**Gateway responsibility:**
- Convert 500 → 502 for upstream failures
- Add `Retry-After` header for 429
- Standard error format

---

## 🧹 What We Cleaned Up

### Removed Files

1. **`app/middleware/rate_limiter.py`** (439 lines)
   - Multi-tier rate limiting
   - Redis sliding window
   - Cost-based limits
   - **Reason:** Gateway handles this

2. **`app/core/redis.py`** (68 lines)
   - Redis connection pool for rate limiting
   - **Reason:** Keep Redis for AI caching only

### Simplified Files

3. **`app/routes/assistant_routes.py`**
   - Removed: Rate limit checks, `/stats` endpoint
   - Kept: Input validation, cost tracking
   - Result: 120 lines removed

4. **`app/core/config.py`**
   - Removed: 8 rate limiting settings
   - Kept: Cost limit settings (for alerts/metrics)
   - Result: Cleaner configuration

5. **`requirements.txt`**
   - Removed: `slowapi`, `prometheus-fastapi-instrumentator`
   - Kept: `aiocache`, `pybreaker`, `opentelemetry-api`
   - Result: Lighter dependencies

---

## 📊 Revised Production Readiness Plan

### ❌ Removed (Gateway Responsibilities)

- **Phase 1: Rate Limiting** → Gateway handles
- **Phase 3: Global Metrics** → Gateway handles
- **Edge Caching** → Gateway handles

### ✅ Keeping (Service Responsibilities)

**Phase 2: AI-Specific Caching** (HIGH PRIORITY)
- Query result cache (24h TTL)
- Embedding cache (7d TTL)
- Context cache (1h TTL)
- Expected: 60-80% cost reduction

**Phase 4: Circuit Breakers** (MEDIUM PRIORITY)
- HuggingFace API protection
- Graceful degradation
- Automatic recovery

**Phase 5: Model Optimization** (LOW PRIORITY)
- Singleton model cache
- Connection pooling
- 90% faster subsequent requests

**Phase 6: Request Tracing** (MEDIUM PRIORITY)
- Service-level spans (not root trace)
- Child spans for: embed, search, generate
- OpenTelemetry integration

**Phase 7: Cost Tracking** (MEDIUM PRIORITY)
- Per-user cost aggregation
- Cost alerts (80% of budget)
- Cost analytics dashboard

---

## 🎯 The Golden Rule

**If every service needs it → Gateway**  
**If only this service needs it → Service**

### Examples

| Feature | Where? | Why? |
|---------|--------|------|
| Rate limiting (10/min) | Gateway | All services need protection |
| AI query cache | Service | Specific to RAG pipeline |
| Request ID injection | Gateway | Consistent across services |
| Token cost tracking | Service | Only AI services have tokens |
| SSL termination | Gateway | Infrastructure concern |
| Circuit breaker for LLM | Service | Specific to AI dependencies |
| Global RPS metrics | Gateway | Traffic-level concern |
| Answer quality metrics | Service | Domain-specific |

---

## 🚀 Implementation Priority

### This Week (Critical)

1. **Implement AI Caching** (Phase 2)
   - Query result cache
   - Embedding cache
   - Context cache
   - **Impact:** 60-80% cost reduction

2. **Add Circuit Breakers** (Phase 4)
   - HuggingFace API protection
   - Graceful failure handling
   - **Impact:** Better resilience

### Next Week (Important)

3. **Add Service Tracing** (Phase 6)
   - OpenTelemetry child spans
   - Performance visibility
   - **Impact:** Easier debugging

4. **Build Cost Tracking** (Phase 7)
   - Per-user cost aggregation
   - Alert system
   - **Impact:** Budget control

### Future (Nice to Have)

5. **Model Optimization** (Phase 5)
   - Singleton pattern
   - Connection pooling
   - **Impact:** Marginal improvement

---

## 💡 Key Takeaways

### What Changed

**Before (Confused):**
```
FastAPI Service = Mini Gateway + Business Logic
- Rate limiting ❌
- Global metrics ❌
- Redis for rate limiting ❌
- AI logic ✅
```

**After (Clean):**
```
Gateway = Cross-cutting concerns
- Rate limiting ✅
- Global metrics ✅
- Edge caching ✅
- Load balancing ✅

Service = Domain-specific concerns
- AI caching ✅
- LLM circuit breakers ✅
- Cost tracking ✅
- Business logic ✅
```

### Benefits

1. **Lighter Services**
   - 500+ lines removed
   - Simpler dependencies
   - Faster to test

2. **No Duplication**
   - Rate limiting in one place (gateway)
   - Easier to update limits
   - Consistent across services

3. **Clearer Ownership**
   - Infrastructure team → Gateway
   - Backend team → Services
   - No confusion

4. **Better Scalability**
   - Gateway scales independently
   - Services scale based on domain needs
   - Optimal resource allocation

---

## 📚 Further Reading

- [12-Factor App: Backing Services](https://12factor.net/backing-services)
- [API Gateway Pattern](https://microservices.io/patterns/apigateway.html)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)

---

**Document Version:** 1.0  
**Last Updated:** December 20, 2024  
**Status:** Architecture cleanup complete  
**Next Steps:** Implement Phase 2 (AI Caching)
