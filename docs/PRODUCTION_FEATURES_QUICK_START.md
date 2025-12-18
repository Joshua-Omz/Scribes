# Production Features - Quick Start Guide

**Purpose:** Get production infrastructure running in 5 minutes

## Prerequisites

- Python 3.11+
- Redis server running
- PostgreSQL database configured
- HuggingFace API key set

## Installation

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd "c:\flutter proj\Scribes\backend2"

# Install new production dependencies
pip install slowapi==0.1.9
pip install aiocache==0.12.2 msgpack==1.0.7
pip install prometheus-client==0.19.0 prometheus-fastapi-instrumentator==6.1.0
pip install pybreaker==1.0.1
pip install opentelemetry-api==1.21.0 opentelemetry-sdk==1.21.0

# Or install all at once
pip install -r requirements.txt
```

### 2. Start Redis

**Windows (PowerShell):**
```powershell
# If Redis not installed, download from: https://github.com/microsoftarchive/redis/releases
# Or use Docker:
docker run -d -p 6379:6379 --name scribes-redis redis:latest

# Verify Redis is running
docker ps | Select-String redis
# Or if installed locally:
redis-cli ping  # Should return "PONG"
```

**Linux/Mac:**
```bash
# Start Redis
redis-server &

# Verify
redis-cli ping  # Should return "PONG"
```

### 3. Configure Environment

Add to your `.env` file:

```bash
# Rate Limiting Configuration
RATE_LIMITING_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=500
GLOBAL_CONCURRENT_LIMIT=100
GLOBAL_HOURLY_LIMIT=1000
USER_DAILY_COST_LIMIT=5.0
GLOBAL_DAILY_COST_LIMIT=100.0

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=10
```

### 4. Start the API Server

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

### Test 1: Health Check

```bash
# Check if services are healthy
curl http://localhost:8000/api/v1/assistant/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "checks": {
    "assistant_service": "available",
    "redis": "connected"
  }
}
```

### Test 2: Rate Limit Statistics

```bash
# Get your current rate limit status
curl http://localhost:8000/api/v1/assistant/stats \
     -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": 1,
    "timestamp": 1702835600,
    "limits": {
      "minute": {"current": 0, "limit": 10, "remaining": 10},
      "hour": {"current": 0, "limit": 100, "remaining": 100},
      "day": {"current": 0, "limit": 500, "remaining": 500}
    },
    "cost": {
      "today": 0.0,
      "limit": 5.0,
      "remaining": 5.0
    }
  }
}
```

### Test 3: Make a Query

```bash
# Make a normal query
curl -X POST http://localhost:8000/api/v1/assistant/query \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is grace?"
     }'
```

**Expected Response:**
```json
{
  "answer": "Grace is...",
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

### Test 4: Trigger Rate Limit

```bash
# Send 11 requests rapidly (limit is 10/minute)
for i in {1..11}; do
    curl -X POST http://localhost:8000/api/v1/assistant/query \
         -H "Authorization: Bearer YOUR_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"query":"test"}' &
done
wait
```

**Expected Behavior:**
- First 10 requests: `200 OK`
- 11th request: `429 Too Many Requests`

**429 Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 42
Content-Type: application/json

{
  "detail": "Rate limit exceeded: 10 requests per per minute"
}
```

### Test 5: Monitor Redis

```bash
# Check Redis keys
redis-cli KEYS "ratelimit:*"

# Check specific user's limits
redis-cli ZRANGE ratelimit:user:1:minute 0 -1 WITHSCORES

# Check concurrent requests
redis-cli GET ratelimit:global:concurrent

# Check cost tracking
redis-cli GET ratelimit:cost:user:1:daily
```

## Troubleshooting

### Redis Connection Failed

**Symptom:**
```
ERROR: Failed to connect to Redis: Connection refused
```

**Solution:**
```bash
# Start Redis
docker start scribes-redis
# OR
redis-server &

# Verify connection
redis-cli ping
```

### Rate Limiting Not Working

**Check 1: Is rate limiting enabled?**
```bash
grep RATE_LIMITING_ENABLED .env
# Should show: RATE_LIMITING_ENABLED=true
```

**Check 2: Is Redis connected?**
```bash
# Check logs
tail -f logs/app.log | grep -i redis
# Should see: "Redis client connected successfully"
```

**Check 3: Are limits too high?**
```bash
# Temporarily lower limits for testing
export RATE_LIMIT_PER_MINUTE=2
uvicorn app.main:app --reload
```

### All Requests Return 429

**Cause:** Clock skew or old entries in Redis

**Solution:**
```bash
# Check Redis time
redis-cli TIME

# Clear all rate limit keys
redis-cli KEYS "ratelimit:*" | xargs redis-cli DEL

# Restart API server
```

### Rate Limiter Fails Open

**Symptom:**
```
WARNING: Rate limit check failed: [Redis error]
```

**Behavior:** Requests are allowed (fail-open strategy)

**Solution:**
1. Fix Redis connection
2. Monitor logs for errors
3. Once Redis is back, rate limiting resumes automatically

## Performance Validation

### Latency Check

```bash
# Measure request latency
time curl -X POST http://localhost:8000/api/v1/assistant/query \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"What is faith?"}'
```

**Expected:**
- First request: ~3-5 seconds (cold start)
- Subsequent requests: ~3-5 seconds (no caching yet)
- Rate limit check overhead: <5ms

### Redis Performance

```bash
# Benchmark Redis operations
redis-cli --intrinsic-latency 100

# Should show: <1ms avg latency for local Redis
```

### Load Test (Optional)

**Install Locust:**
```bash
pip install locust
```

**Create `load_test.py`:**
```python
from locust import HttpUser, task, between

class AssistantUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
    
    @task
    def query_assistant(self):
        self.client.post(
            "/api/v1/assistant/query",
            json={"query": "What is grace?"},
            headers={"Authorization": f"Bearer {self.token}"}
        )

# Run: locust -f load_test.py --users 10 --spawn-rate 2
```

## Monitoring

### Check Metrics Endpoint (Future)

```bash
# Once metrics implemented
curl http://localhost:8000/metrics
```

**Expected (Prometheus format):**
```
# HELP assistant_queries_total Total assistant queries
# TYPE assistant_queries_total counter
assistant_queries_total{endpoint="query",status="success",cached="false"} 42.0

# HELP assistant_query_duration_seconds Query duration
# TYPE assistant_query_duration_seconds histogram
assistant_query_duration_seconds_bucket{le="1.0"} 10
assistant_query_duration_seconds_bucket{le="5.0"} 38
assistant_query_duration_seconds_sum 134.5
assistant_query_duration_seconds_count 42
```

### Redis Monitoring

```bash
# Real-time monitoring
redis-cli MONITOR

# Stats
redis-cli INFO stats

# Memory usage
redis-cli INFO memory
```

## Configuration Profiles

### Development Profile

**`.env.development`:**
```bash
RATE_LIMITING_ENABLED=false  # Disable for easier testing
RATE_LIMIT_PER_MINUTE=1000   # Very high limits
RATE_LIMIT_PER_HOUR=10000
USER_DAILY_COST_LIMIT=100.0  # Higher cost limits
```

### Production Profile

**`.env.production`:**
```bash
RATE_LIMITING_ENABLED=true   # Always enabled
RATE_LIMIT_PER_MINUTE=10     # Strict limits
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=500
USER_DAILY_COST_LIMIT=5.0    # Budget protection
GLOBAL_DAILY_COST_LIMIT=100.0
```

### Testing Profile

**`.env.testing`:**
```bash
RATE_LIMITING_ENABLED=true   # Test the feature
RATE_LIMIT_PER_MINUTE=2      # Very low for easy testing
RATE_LIMIT_PER_HOUR=10
USER_DAILY_COST_LIMIT=1.0
```

## Next Steps

1. ✅ **Rate Limiting:** Complete
2. ⏳ **Response Caching:** Implement next (60-80% cost savings)
3. ⏳ **Observability:** Add Prometheus metrics
4. ⏳ **Circuit Breakers:** Add HuggingFace API protection

## Support

**Documentation:**
- Full implementation: `docs/RATE_LIMITING_IMPLEMENTATION.md`
- Production plan: `docs/PRODUCTION_READINESS_PLAN.md`
- Progress tracking: `docs/PRODUCTION_INFRASTRUCTURE_PROGRESS.md`

**Logs:**
```bash
# Check rate limiter logs
tail -f logs/app.log | grep -i "rate"

# Check errors
tail -f logs/app.log | grep ERROR
```

**Redis Commands:**
```bash
# View all rate limit keys
redis-cli KEYS "ratelimit:*"

# View user stats
redis-cli ZCARD ratelimit:user:1:minute
redis-cli GET ratelimit:cost:user:1:daily

# Clear user's limits (admin only)
redis-cli DEL ratelimit:user:1:minute ratelimit:user:1:hour ratelimit:user:1:day

# Clear all rate limits (admin only - use with caution)
redis-cli FLUSHDB
```

---

**Last Updated:** December 17, 2024  
**Version:** 1.0.0  
**Status:** Production Ready ✅
