# Rate Limiting Implementation

**Status:** ✅ IMPLEMENTED  
**Date:** December 17, 2024  
**Priority:** CRITICAL - Production Infrastructure

## Overview

Multi-tier rate limiting system to prevent abuse, control API costs, and ensure fair resource allocation across users.

## Architecture

### Components

1. **RateLimiter** (`app/middleware/rate_limiter.py`)
   - Redis-backed sliding window algorithm
   - Per-user and global limits
   - Cost-based limiting
   - Metrics collection

2. **Redis Connection Pool** (`app/core/redis.py`)
   - Centralized connection management
   - Connection pooling for performance
   - Graceful error handling

3. **Configuration** (`app/core/config.py`)
   - Environment-based limit configuration
   - Development vs production profiles

4. **Route Integration** (`app/routes/assistant_routes.py`)
   - Endpoint-level rate limiting
   - Cost tracking
   - 429 error responses with Retry-After

## Rate Limit Tiers

### Per-User Limits

| Window | Limit | Purpose |
|--------|-------|---------|
| 1 minute | 10 requests | Prevent rapid-fire spam |
| 1 hour | 100 requests | Daily usage cap (1/10th) |
| 1 day | 500 requests | Max daily usage |

### Global System Limits

| Limit Type | Value | Purpose |
|------------|-------|---------|
| Concurrent requests | 100 | Prevent resource exhaustion |
| Hourly requests | 1,000 | System-wide capacity |

### Cost-Based Limits

| Scope | Daily Limit | Purpose |
|-------|-------------|---------|
| Per user | $5.00 USD | Individual cost protection |
| System-wide | $100.00 USD | Total budget protection |

## Algorithm: Sliding Window

Uses Redis Sorted Sets (ZSET) for accurate sliding window tracking:

```python
# Redis key structure
ratelimit:user:{user_id}:minute   # TTL: 2 minutes
ratelimit:user:{user_id}:hour     # TTL: 2 hours
ratelimit:user:{user_id}:day      # TTL: 2 days

# Cost tracking
ratelimit:cost:user:{user_id}:daily  # TTL: 24 hours
ratelimit:cost:global:daily          # TTL: 24 hours

# Concurrent tracking
ratelimit:global:concurrent  # Counter (incremented/decremented)
```

**How it works:**

1. **Store requests as sorted set members**:
   - Score: Unix timestamp
   - Value: Unique request ID (`{timestamp}:{user_id}:{endpoint}`)

2. **Remove expired entries**:
   ```python
   window_start = now - window_seconds
   ZREMRANGEBYSCORE key 0 window_start
   ```

3. **Count requests in window**:
   ```python
   current_count = ZCARD key
   ```

4. **Allow or deny**:
   - If `current_count < limit`: ALLOW
   - If `current_count >= limit`: DENY with 429

5. **Calculate Retry-After**:
   ```python
   oldest_timestamp = ZRANGE key 0 0 WITHSCORES
   retry_after = oldest_timestamp + window - now
   ```

## API Response Behavior

### Successful Request (200 OK)

```json
{
  "answer": "...",
  "sources": [...],
  "metadata": {
    "request_duration_seconds": 3.16,
    "api_cost_usd": 0.000342,
    "rate_limited": false,
    "query_tokens": 12,
    "context_tokens": 856,
    "output_tokens": 145
  }
}
```

### Rate Limit Exceeded (429 Too Many Requests)

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 42
Content-Type: application/json

{
  "detail": "Rate limit exceeded: 10 requests per per minute"
}
```

**Headers:**
- `Retry-After`: Seconds until limit resets
- `X-RateLimit-Limit`: Max requests allowed
- `X-RateLimit-Remaining`: Requests remaining (TODO)
- `X-RateLimit-Reset`: Unix timestamp when limit resets (TODO)

## Configuration

### Environment Variables

```bash
# Rate Limiting
RATE_LIMITING_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=500
GLOBAL_CONCURRENT_LIMIT=100
GLOBAL_HOURLY_LIMIT=1000
USER_DAILY_COST_LIMIT=5.0
GLOBAL_DAILY_COST_LIMIT=100.0

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=10
```

### Production vs Development

**Development** (`.env.development`):
```bash
RATE_LIMITING_ENABLED=false  # Disable for testing
RATE_LIMIT_PER_MINUTE=100    # High limits
```

**Production** (`.env.production`):
```bash
RATE_LIMITING_ENABLED=true
RATE_LIMIT_PER_MINUTE=10     # Strict limits
USER_DAILY_COST_LIMIT=5.0    # Cost protection
```

## Usage Examples

### Endpoint Integration

```python
from app.middleware.rate_limiter import get_rate_limiter

@router.post("/assistant/query")
async def query_assistant(
    request: AssistantQueryRequest,
    current_user: User = Depends(get_current_active_user),
):
    limiter = get_rate_limiter()
    
    # Check rate limit (raises HTTPException if exceeded)
    await limiter.check_rate_limit(
        user_id=current_user.id,
        endpoint="assistant.query",
        cost=0.0  # Will update after calculating actual cost
    )
    
    # Process request...
    result = await assistant.query(...)
    
    # Update with actual cost
    cost = calculate_request_cost(result["metadata"])
    await limiter.check_rate_limit(
        user_id=current_user.id,
        endpoint="assistant.query",
        cost=cost
    )
    
    # Always release concurrent slot
    await limiter.release_concurrent_slot()
```

### Decorator Pattern

```python
from app.middleware.rate_limiter import rate_limit

@rate_limit(endpoint="assistant.query")
async def process_query(user_id: int, query: str):
    # Automatically rate limited
    # Concurrent slot automatically released
    return await assistant.query(user_id, query)
```

### Get User Statistics

```python
limiter = get_rate_limiter()
stats = await limiter.get_user_stats(user_id=123)

# Returns:
{
  "user_id": 123,
  "timestamp": 1702835600,
  "limits": {
    "minute": {
      "current": 3,
      "limit": 10,
      "remaining": 7
    },
    "hour": {
      "current": 24,
      "limit": 100,
      "remaining": 76
    },
    "day": {
      "current": 156,
      "limit": 500,
      "remaining": 344
    }
  },
  "cost": {
    "today": 0.52,
    "limit": 5.0,
    "remaining": 4.48
  }
}
```

## Cost Calculation

### Pricing Model

Based on Llama-3.2-3B-Instruct approximate pricing:

| Token Type | Cost per Token |
|------------|----------------|
| Input (query + context) | $0.0000002 |
| Output (generated text) | $0.0000006 |

### Formula

```python
def calculate_request_cost(metadata: dict) -> float:
    query_tokens = metadata["query_tokens"]
    context_tokens = metadata["context_tokens"]
    output_tokens = metadata["output_tokens"]
    
    input_cost = (query_tokens + context_tokens) * 0.0000002
    output_cost = output_tokens * 0.0000006
    
    return input_cost + output_cost
```

### Example

Query with:
- Query: 12 tokens
- Context: 856 tokens
- Output: 145 tokens

```
Input cost:  (12 + 856) × $0.0000002 = $0.00017360
Output cost: 145 × $0.0000006 =        $0.00008700
Total cost:                             $0.00026060
```

For 500 requests/day at this average:
```
Daily cost: 500 × $0.00026060 = $0.13030
```

Well within the $5/day limit.

## Monitoring & Alerts

### Metrics to Track

1. **Rate Limit Events**
   - `rate_limit_exceeded:per_minute`
   - `rate_limit_exceeded:per_hour`
   - `rate_limit_exceeded:per_day`
   - `rate_limit_exceeded:cost`

2. **Usage Patterns**
   - Requests per user (histogram)
   - Cost per user (histogram)
   - Peak concurrent requests (gauge)

3. **Health Indicators**
   - Redis connection failures
   - Rate limiter errors (fail-open count)
   - 429 response rate

### Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| **CRITICAL** | Global cost >$100/day | PagerDuty + auto-disable |
| **WARNING** | User cost >$5/day | Email user + warning |
| **INFO** | 429 rate >10% | Slack notification |
| **INFO** | Redis connection lost | Switch to fail-open, alert ops |

## Error Handling

### Fail-Open Strategy

If Redis is unavailable, rate limiter **fails open** (allows requests):

```python
async def _check_sliding_window(...):
    try:
        # Redis operations...
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True, {"error": str(e)}  # ✅ ALLOW REQUEST
```

**Rationale:**
- Availability > strict limiting when Redis down
- Better UX (no false 429s)
- Logged for alerting/debugging

### Redis Reconnection

Connection pool handles reconnection automatically:
- Retry on timeout: `retry_on_timeout=True`
- Socket timeout: 5 seconds
- Connect timeout: 5 seconds

## Testing

### Manual Testing

```bash
# Test per-minute limit (10 requests)
for i in {1..15}; do
    curl -X POST http://localhost:8000/api/v1/assistant/query \
         -H "Authorization: Bearer $TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"query":"test"}' &
done
wait

# Expected: 10 succeed (200), 5 fail (429)
```

### Unit Tests

```python
@pytest.mark.asyncio
async def test_rate_limit_per_minute(rate_limiter, user_id):
    # Make 10 requests (should succeed)
    for i in range(10):
        allowed, _ = await rate_limiter.check_rate_limit(
            user_id=user_id,
            endpoint="test"
        )
        assert allowed
    
    # 11th request should fail
    with pytest.raises(HTTPException) as exc:
        await rate_limiter.check_rate_limit(
            user_id=user_id,
            endpoint="test"
        )
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers
```

### Load Testing

```python
# Locust load test
class AssistantUser(HttpUser):
    @task
    def query_assistant(self):
        self.client.post(
            "/api/v1/assistant/query",
            json={"query": "What is grace?"},
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    wait_time = between(1, 3)  # 1-3 seconds between requests

# Run: locust -f load_test.py --users 100 --spawn-rate 10
```

## Performance Considerations

### Redis Operations

- **ZREMRANGEBYSCORE**: O(log(N) + M) - N=set size, M=removed
- **ZCARD**: O(1) - constant time
- **ZADD**: O(log(N)) - logarithmic

For typical usage (100 requests/window):
- Check: ~1ms
- Cleanup: ~2ms
- **Total overhead: <5ms per request**

### Memory Usage

Per user per window:
```
Request entry: ~50 bytes (timestamp + ID)
100 requests: 5KB per user per window
1000 users: 5MB per window
3 windows: 15MB total
```

**Very low memory footprint.**

### Network Latency

- Local Redis: <1ms
- Same datacenter: <5ms
- Cross-region: 20-50ms

**Recommendation:** Co-locate Redis with API server.

## Troubleshooting

### Issue: All requests getting 429

**Cause:** Limits too low or clock skew

**Fix:**
```bash
# Check Redis time
redis-cli TIME

# Check limits
redis-cli GET ratelimit:user:123:minute
redis-cli ZRANGE ratelimit:user:123:minute 0 -1 WITHSCORES

# Adjust limits in .env
RATE_LIMIT_PER_MINUTE=50
```

### Issue: Rate limiting not working

**Cause:** Redis not connected or disabled

**Fix:**
```bash
# Check Redis connection
redis-cli PING

# Check rate limiting enabled
grep RATE_LIMITING_ENABLED .env

# Check logs
tail -f logs/app.log | grep -i "rate"
```

### Issue: Memory growing in Redis

**Cause:** TTL not set or keys not expiring

**Fix:**
```bash
# Check TTLs
redis-cli TTL ratelimit:user:123:minute
# Should return 60-120 seconds

# Manual cleanup if needed
redis-cli KEYS "ratelimit:*" | xargs redis-cli DEL
```

## Future Enhancements

### Phase 2 Features

1. **Premium Tier Limits**
   - Higher limits for paid users
   - Custom limits per user/organization
   ```python
   @router.post("/query")
   async def query(user: User):
       limit = user.premium_tier.rate_limit  # 100/min vs 10/min
       await limiter.check_rate_limit(user_id, limit=limit)
   ```

2. **Adaptive Rate Limiting**
   - Increase limits during low-traffic periods
   - Decrease during high-traffic periods
   - AI-based anomaly detection

3. **Rate Limit Headers**
   - `X-RateLimit-Limit`: Max requests
   - `X-RateLimit-Remaining`: Requests left
   - `X-RateLimit-Reset`: Reset timestamp
   ```python
   headers = {
       "X-RateLimit-Limit": str(limit),
       "X-RateLimit-Remaining": str(remaining),
       "X-RateLimit-Reset": str(reset_time)
   }
   ```

4. **Distributed Rate Limiting**
   - Multiple API servers sharing limits
   - Redis Cluster for horizontal scaling
   - Token bucket algorithm for smoother limits

5. **Cost Prediction**
   - Estimate cost before processing
   - Deny expensive queries preemptively
   - Suggest query simplification

## References

- **Sliding Window Algorithm**: [https://en.wikipedia.org/wiki/Leaky_bucket](https://en.wikipedia.org/wiki/Leaky_bucket)
- **Redis ZSET Commands**: [https://redis.io/commands#sorted-set](https://redis.io/commands#sorted-set)
- **FastAPI Rate Limiting**: [https://slowapi.readthedocs.io](https://slowapi.readthedocs.io)
- **429 Status Code**: [RFC 6585](https://datatracker.ietf.org/doc/html/rfc6585#section-4)

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2024-12-17 | 1.0.0 | Initial implementation with multi-tier limiting |
| TBD | 1.1.0 | Add premium tier support |
| TBD | 1.2.0 | Add adaptive rate limiting |

---

**Implementation Complete:** ✅  
**Production Ready:** ✅  
**Next Steps:** Implement response caching (Phase 2)
