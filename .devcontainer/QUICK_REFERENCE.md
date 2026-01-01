# Dev Container Quick Reference

**Last Updated:** December 18, 2024

## Quick Commands

### Start Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/v1/assistant/health

### Database Commands
```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/scribes_db

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Redis Commands
```bash
# Connect to Redis
redis-cli

# Check connection
redis-cli ping

# Monitor activity
redis-cli monitor

# View rate limit keys
redis-cli KEYS "ratelimit:*"
```

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py -v
```

## Production Features

### ✅ Rate Limiting (Implemented)

**Check Health:**
```bash
curl http://localhost:8000/api/v1/assistant/health
```

**Get Rate Limit Stats:**
```bash
# First, get auth token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')

# Check your stats
curl http://localhost:8000/api/v1/assistant/stats \
     -H "Authorization: Bearer $TOKEN" | jq
```

**Test Rate Limiting:**
```bash
# Send 11 requests (10/min limit)
for i in {1..11}; do
    curl -X POST http://localhost:8000/api/v1/assistant/query \
         -H "Authorization: Bearer $TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"query":"test"}' &
done
wait
# Expected: 10 succeed (200), 1 fails (429)
```

**Monitor Redis Rate Limits:**
```bash
# View all rate limit keys
redis-cli KEYS "ratelimit:*"

# Check specific user's minute limit
redis-cli ZRANGE ratelimit:user:1:minute 0 -1 WITHSCORES

# Check user's daily cost
redis-cli GET ratelimit:cost:user:1:daily

# Clear user's limits (dev only)
redis-cli DEL ratelimit:user:1:minute ratelimit:user:1:hour ratelimit:user:1:day
```

**Configuration:**
```bash
# Dev container default limits
RATE_LIMITING_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=500
USER_DAILY_COST_LIMIT=5.0
```

### ⏳ Response Caching (Phase 2 - Coming Soon)

**Expected Features:**
- Query cache (24h TTL) - Redis
- Embedding cache (7d TTL) - Redis
- Context cache (1h TTL) - In-memory LRU
- 60-80% cost reduction
- <1s cached response time

**Test When Available:**
```bash
# First request: uncached (~3-5s)
time curl -X POST http://localhost:8000/api/v1/assistant/query \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"What is grace?"}'

# Second identical request: cached (<1s)
time curl -X POST http://localhost:8000/api/v1/assistant/query \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"What is grace?"}'
```

### ⏳ Observability Metrics (Phase 3 - Coming Soon)

**Planned Endpoint:**
```bash
curl http://localhost:8000/metrics
```

**Expected Metrics:**
- `assistant_query_duration_seconds` - Latency histogram
- `assistant_queries_total` - Request counter
- `assistant_errors_total` - Error counter
- `assistant_cache_hit_rate` - Cache performance
- `assistant_api_cost_usd_total` - Cost tracking

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection string ✅
- `REDIS_URL` - Redis connection string ✅
- `HUGGINGFACE_API_KEY` - HF API token ⚠️ **ADD YOUR KEY**

### Optional (Defaults Provided)
- `JWT_SECRET_KEY` - Token signing secret
- `RATE_LIMITING_ENABLED` - Enable/disable rate limiting
- `RATE_LIMIT_PER_MINUTE` - Per-user minute limit
- `APP_ENV` - Environment (development/production)
- `DEBUG` - Debug mode

### AI Assistant Config
- `HF_GENERATION_MODEL` - Llama-3.2-3B-Instruct
- `HF_EMBEDDING_MODEL` - all-MiniLM-L6-v2
- `ASSISTANT_MAX_CONTEXT_TOKENS` - 1200
- `ASSISTANT_USER_QUERY_TOKENS` - 150
- `ASSISTANT_MAX_OUTPUT_TOKENS` - 400

## Common Tasks

### Create Test User
```bash
# Using create_test_data.py
python create_test_data.py

# Or via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@example.com",
    "password": "DevPass123!",
    "full_name": "Dev User"
  }'
```

### Login and Get Token
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@example.com",
    "password": "DevPass123!"
  }' | jq -r '.access_token' > token.txt

# Use token
TOKEN=$(cat token.txt)
curl http://localhost:8000/api/v1/user/me \
  -H "Authorization: Bearer $TOKEN"
```

### Create Note
```bash
curl -X POST http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sermon on Grace",
    "content": "Grace is the unmerited favor of God...",
    "note_type": "sermon"
  }'
```

### Query AI Assistant
```bash
curl -X POST http://localhost:8000/api/v1/assistant/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is grace according to my notes?"
  }' | jq
```

## Debugging

### View Logs
```bash
# API logs (in container)
tail -f logs/app.log

# Filter for rate limiting
tail -f logs/app.log | grep -i "rate"

# Filter for errors
tail -f logs/app.log | grep ERROR
```

### Interactive Python
```bash
# Start IPython with app context
ipython

# Import and test
from app.core.database import get_db
from app.services.ai.assistant_service import get_assistant_service
```

### Debug with ipdb
```python
# Add to your code
import ipdb; ipdb.set_trace()

# When breakpoint hits:
# n - next line
# s - step into
# c - continue
# l - list code
# p variable - print variable
```

### Check Service Health
```bash
# All services
docker-compose -f .devcontainer/docker-compose.yml ps

# Check PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/scribes_db -c "SELECT 1"

# Check Redis
redis-cli ping

# Check API
curl http://localhost:8000/health || curl http://localhost:8000/api/v1/assistant/health
```

## Performance Testing

### Single Request Timing
```bash
# Measure request latency
time curl -X POST http://localhost:8000/api/v1/assistant/query \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"What is faith?"}'
```

### Load Testing (Locust)
```bash
# Install Locust
pip install locust

# Run load test (create load_test.py first)
locust -f tests/manual/load_test.py --users 10 --spawn-rate 2
```

### Redis Performance
```bash
# Benchmark Redis
redis-cli --intrinsic-latency 100
# Expected: <1ms avg latency

# Monitor Redis stats
redis-cli INFO stats
redis-cli INFO memory
```

## Troubleshooting

### Container Won't Start
```bash
# Rebuild container
# In VS Code: Cmd+Shift+P -> "Dev Containers: Rebuild Container"

# Check Docker logs
docker-compose -f .devcontainer/docker-compose.yml logs app
docker-compose -f .devcontainer/docker-compose.yml logs db
docker-compose -f .devcontainer/docker-compose.yml logs redis
```

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker-compose -f .devcontainer/docker-compose.yml ps db

# Restart database
docker-compose -f .devcontainer/docker-compose.yml restart db

# Check database logs
docker-compose -f .devcontainer/docker-compose.yml logs db
```

### Redis Connection Failed
```bash
# Check if Redis is running
docker-compose -f .devcontainer/docker-compose.yml ps redis

# Restart Redis
docker-compose -f .devcontainer/docker-compose.yml restart redis

# Clear Redis data
redis-cli FLUSHALL
```

### Rate Limiting Not Working
```bash
# Check if enabled
grep RATE_LIMITING_ENABLED .devcontainer/.env.devcontainer

# Check Redis connection
redis-cli ping

# Check rate limit keys
redis-cli KEYS "ratelimit:*"

# Clear stale keys
redis-cli KEYS "ratelimit:*" | xargs redis-cli DEL
```

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac/Linux

# Kill process or change port
uvicorn app.main:app --reload --port 8001
```

## Documentation

### Project Documentation
- **Main README:** `../README.md`
- **Project Organization:** `../PROJECT_ORGANIZATION.md`
- **AI Assistant Docs:** `../docs/services/ai-assistant/README.md`
- **Test Documentation:** `../tests/README.md`

### Production Features
- **Quick Start:** `../docs/PRODUCTION_FEATURES_QUICK_START.md`
- **Rate Limiting:** `../docs/RATE_LIMITING_IMPLEMENTATION.md`
- **Progress Tracking:** `../docs/PRODUCTION_INFRASTRUCTURE_PROGRESS.md`
- **Production Plan:** `../docs/PRODUCTION_READINESS_PLAN.md`

### API Documentation
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Useful Links

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [pgvector Docs](https://github.com/pgvector/pgvector)
- [Redis Docs](https://redis.io/docs/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Pytest Docs](https://docs.pytest.org/)

## Production Features Status

| Feature | Status | Phase | Docs |
|---------|--------|-------|------|
| Rate Limiting | ✅ READY | 1 | [Details](../docs/RATE_LIMITING_IMPLEMENTATION.md) |
| Response Caching | ⏳ PENDING | 2 | [Plan](../docs/PRODUCTION_READINESS_PLAN.md) |
| Observability | ⏳ PENDING | 3 | [Plan](../docs/PRODUCTION_READINESS_PLAN.md) |
| Circuit Breakers | ⏳ PENDING | 4 | [Plan](../docs/PRODUCTION_READINESS_PLAN.md) |
| Model Caching | ⏳ PENDING | 5 | [Plan](../docs/PRODUCTION_READINESS_PLAN.md) |
| Request Tracing | ⏳ PENDING | 6 | [Plan](../docs/PRODUCTION_READINESS_PLAN.md) |
| Cost Tracking | ⏳ PENDING | 7 | [Plan](../docs/PRODUCTION_READINESS_PLAN.md) |

**Overall Progress:** 1/7 features (14% complete)

---

**Need Help?** Check the full documentation in `../docs/` or open an issue on GitHub.
