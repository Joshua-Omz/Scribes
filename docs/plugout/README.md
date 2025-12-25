# Scribes - External Team Onboarding

**Welcome to the Scribes Plugout Documentation!**

This folder contains comprehensive documentation designed for external teams integrating with, deploying, or testing the Scribes application.

---

## 📁 What's in This Folder

### Current Documents

1. **[AI_CACHING_SYSTEM_OVERVIEW.md](./AI_CACHING_SYSTEM_OVERVIEW.md)**
   - Complete guide to the 3-layer AI caching system
   - Testing journey and bug fixes
   - Monitoring and operations guide
   - Integration instructions for all roles

---

## 👥 Documentation by Role

### 🎨 Frontend Developers
**What you need to know:**
- API contract remains unchanged
- Cache status available in response metadata
- Performance: 1,711x faster for cached queries
- **Read:** [AI Caching System - Integration Guide](./AI_CACHING_SYSTEM_OVERVIEW.md#for-frontend-developers)

**Key Takeaways:**
- Display cache indicators using `_cache_metadata.from_cache`
- No code changes required in your API calls
- Response times improved dramatically (4.4s → 2.58ms)

---

### 🔧 DevOps Engineers
**What you need to deploy:**
- Redis server (version 7.x recommended)
- Environment variables configuration
- Docker/Kubernetes deployment templates
- **Read:** [AI Caching System - DevOps Guide](./AI_CACHING_SYSTEM_OVERVIEW.md#for-devops-engineers)

**Quick Start:**
```bash
# Start Redis
docker run -d -p 6379:6379 --name scribes-redis redis:7-alpine

# Configure app
export CACHE_ENABLED=true
export REDIS_URL=redis://localhost:6379

# Deploy
docker-compose up -d
```

---

### ☁️ Cloud Engineers
**Infrastructure options:**
- AWS ElastiCache for Redis
- Google Cloud Memorystore
- Azure Cache for Redis
- Self-hosted on compute instances
- **Read:** [AI Caching System - Cloud Deployment](./AI_CACHING_SYSTEM_OVERVIEW.md#for-cloud-engineers)

**Cost Estimates:**
- Development: $0/month (local Docker)
- Staging: $40-50/month (basic tier)
- Production: $200/month (HA setup)

---

### 🧪 QA/Testers
**Test scenarios provided:**
1. Cache hit performance test
2. Cache invalidation test
3. User isolation test
4. TTL expiration test
5. Graceful degradation test
- **Read:** [AI Caching System - Testing Guide](./AI_CACHING_SYSTEM_OVERVIEW.md#for-qatesters)

**Key Metrics:**
- L1 cache hit: < 10ms ✅
- Cold start: < 5 seconds ✅
- Cache hit rate: > 50% ✅
- Memory usage: < 2GB ✅

---

## 📊 System Performance

### At a Glance
- **Speedup:** 1,711x faster for cached queries
- **Cost Savings:** 60-80% reduction in API costs
- **Latency:** 99.9% reduction (4.4s → 2.58ms)
- **Reliability:** Graceful degradation when cache unavailable

### Production Impact
At 1,000 queries/day:
- **Before:** $93.60/year
- **After:** $36.00/year
- **Savings:** $57.60/year (62%)

Plus: Much faster response times = better user experience!

---

## 🔍 Monitoring Options

Choose the tool that fits your workflow:

### Option 1: Redis CLI (Built-in)
```bash
redis-cli -h localhost -p 6379
> MONITOR                    # Real-time operations
> KEYS ai:*                  # List cache keys
> INFO memory                # Memory usage
```

### Option 2: RedisInsight (GUI)
- Download: https://redis.io/insight/
- Visual browser for all keys
- Real-time performance graphs
- Perfect for development

### Option 3: Prometheus + Grafana (Production)
- Export metrics: cache hits, misses, response times
- Build dashboards for hit rates
- Set up alerts for low performance

### Option 4: Application Logs
```bash
grep "CACHE HIT" app.log     # Count hits
grep "CACHE MISS" app.log    # Count misses
```

### Option 5: Custom Monitoring Endpoint
```bash
curl http://localhost:8000/monitoring/cache-stats
```

**Full details:** [Monitoring & Operations](./AI_CACHING_SYSTEM_OVERVIEW.md#monitoring--operations)

---

## 🚀 Quick Start by Role

### Frontend Developer
```bash
# No changes needed! Just observe faster responses
curl -X POST http://localhost:8000/api/assistant/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is grace?", "user_id": 1}'

# Check response metadata
{
  "answer": "...",
  "_cache_metadata": {
    "from_cache": true  # ← Display this in UI!
  }
}
```

### DevOps Engineer
```bash
# 1. Deploy Redis
docker run -d -p 6379:6379 redis:7-alpine

# 2. Configure app
export CACHE_ENABLED=true
export REDIS_URL=redis://localhost:6379

# 3. Start app
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Monitor
redis-cli MONITOR
```

### Cloud Engineer
```bash
# AWS ElastiCache
aws elasticache create-cache-cluster \
  --cache-cluster-id scribes-redis \
  --cache-node-type cache.t3.medium \
  --engine redis

# Or GCP Memorystore
gcloud redis instances create scribes-redis \
  --size=2 \
  --region=us-central1
```

### QA/Tester
```bash
# Run tests
pytest tests/unit/test_ai_caching.py -v

# Integration test
python scripts/testing/test_pipeline_caching.py

# Load test
locust -f locustfile.py
```

---

## 📚 Additional Resources

### Core Documentation
- **Main README:** `/workspace/README.md`
- **Architecture:** `/workspace/ARCHITECTURE.md`
- **API Docs:** http://localhost:8000/docs (Swagger UI)

### Production Readiness
- **Phase 2 Caching:** `/workspace/docs/production-readiness/PHASE_2_CACHING_COMPLETE.md`
- **Prerequisites:** `/workspace/docs/production-readiness/PHASE_2_PREREQUISITES.md`
- **Test Results:** `/workspace/PIPELINE_CACHING_TEST_RESULTS.md`

### AI Services
- **Assistant README:** `/workspace/docs/services/ai-assistant/README.md`
- **Manual Testing Guide:** `/workspace/docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md`

---

## 🐛 Common Issues & Solutions

### Cache Not Working
**Problem:** All queries slow, no speedup on repeats

**Solution:**
1. Check Redis is running: `redis-cli ping`
2. Verify `CACHE_ENABLED=true` in `.env`
3. Restart application

**Details:** [Troubleshooting Guide](./AI_CACHING_SYSTEM_OVERVIEW.md#troubleshooting)

### High Memory Usage
**Problem:** Redis using > 2GB

**Solution:**
```bash
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Cache Not Invalidating
**Problem:** Stale data after note updates

**Solution:**
```bash
# Manual clear
redis-cli KEYS "context:v1:USER_ID:*" | xargs redis-cli DEL
```

---

## 🎯 Getting Help

### For Technical Questions
1. Read the [comprehensive overview](./AI_CACHING_SYSTEM_OVERVIEW.md)
2. Check [troubleshooting section](./AI_CACHING_SYSTEM_OVERVIEW.md#troubleshooting)
3. Review test files in `/workspace/tests/unit/`

### For Deployment Issues
1. Check [DevOps guide](./AI_CACHING_SYSTEM_OVERVIEW.md#for-devops-engineers)
2. Review [cloud deployment options](./AI_CACHING_SYSTEM_OVERVIEW.md#for-cloud-engineers)
3. Consult Docker/K8s templates in overview

### For Integration Questions
1. See [frontend integration guide](./AI_CACHING_SYSTEM_OVERVIEW.md#for-frontend-developers)
2. Review API response examples
3. Check Swagger docs: http://localhost:8000/docs

---

## 📝 Document Updates

This folder will be continuously updated with:
- New feature documentation
- Deployment guides
- Performance optimization tips
- Integration examples
- Best practices

**Last Updated:** December 24, 2025  
**Version:** 1.0

---

## ✅ Checklist for New Team Members

### Before You Start
- [ ] Read this README
- [ ] Read [AI Caching System Overview](./AI_CACHING_SYSTEM_OVERVIEW.md)
- [ ] Identify your role (Frontend/DevOps/Cloud/QA)
- [ ] Review role-specific section

### For Development
- [ ] Clone repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
- [ ] Configure `.env` file
- [ ] Run app: `uvicorn app.main:app --reload`
- [ ] Test API: http://localhost:8000/docs

### For Deployment
- [ ] Choose Redis hosting option
- [ ] Set environment variables
- [ ] Deploy Redis instance
- [ ] Deploy application
- [ ] Verify cache working: `redis-cli MONITOR`
- [ ] Set up monitoring

### For Testing
- [ ] Run unit tests: `pytest tests/unit/test_ai_caching.py -v`
- [ ] Run integration tests: `python scripts/testing/test_pipeline_caching.py`
- [ ] Perform load testing
- [ ] Validate performance metrics

---

**Welcome to the team! 🎉**

The Scribes AI caching system is production-ready and delivers **1,711x performance improvements**. This documentation will help you integrate, deploy, and monitor the system successfully.

For detailed technical information, start with [AI_CACHING_SYSTEM_OVERVIEW.md](./AI_CACHING_SYSTEM_OVERVIEW.md).
