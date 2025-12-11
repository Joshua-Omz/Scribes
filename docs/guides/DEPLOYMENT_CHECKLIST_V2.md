# Semantic Search V2 - Deployment Checklist

## Pre-Deployment

### 1. Install Dependencies
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify `tenacity==8.2.3` is installed
- [ ] Verify `sentence-transformers==5.1.2` is installed (upgraded from 2.2.2)
- [ ] Verify `pgvector==0.2.5` is installed

**Command:**
```bash
pip list | findstr "tenacity sentence-transformers pgvector"
```

### 2. Database Preparation
- [ ] Ensure PostgreSQL has pgvector extension installed
- [ ] Backup current database (optional but recommended)
- [ ] Check current Alembic revision

**Commands:**
```bash
# Check pgvector is available
psql -d your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Check current revision
alembic current

# Backup (optional)
pg_dump your_database > backup_$(date +%Y%m%d).sql
```

### 3. Apply Migration
- [ ] Review the HNSW index migration
- [ ] Apply migration to development environment first
- [ ] Apply migration to production

**Command:**
```bash
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 31ac95978827 -> 70c020ced272, add_hnsw_index_for_embeddings
```

### 4. Switch to New Routes

**Option A: Gradual Migration (Recommended)**

Update `app/main.py`:
```python
# Keep old routes for backward compatibility
from app.api.semantic_routes import router as semantic_router_v1
app.include_router(semantic_router_v1, prefix="/api/v1/semantic")

# Add new routes
from app.api.semantic_routes_v2 import router as semantic_router_v2
app.include_router(semantic_router_v2, prefix="/api/semantic")
```

Test both endpoints are accessible:
- [ ] Old: `GET /api/v1/semantic/status`
- [ ] New: `GET /api/semantic/status`

**Option B: Direct Replacement**

Update `app/main.py`:
```python
# Replace this line:
# from app.api.semantic_routes import router as semantic_router

# With this:
from app.api.semantic_routes_v2 import router as semantic_router
```

## Deployment Steps

### 1. Stop Application
- [ ] Stop uvicorn/gunicorn server
- [ ] Verify no background tasks are running

### 2. Update Code
- [ ] Pull latest code from repository
- [ ] Verify all new files are present:
  - `app/services/embedding_service.py` (updated)
  - `app/models/events.py` (new)
  - `app/api/semantic_routes_v2.py` (new)
  - `app/main.py` (updated)
  - `alembic/versions/2025-11-09_70c020ced272_add_hnsw_index_for_embeddings.py` (new)

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migration
```bash
alembic upgrade head
```

### 5. Start Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Check startup logs for:**
```
✅ Registered automatic embedding generation listeners
```

## Post-Deployment Verification

### 1. Health Checks
- [ ] Server starts without errors
- [ ] Health endpoint responds: `GET /health`
- [ ] Event listeners registered (check logs)

### 2. Embedding Status Check
```bash
curl -X GET http://localhost:8000/semantic/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "total_notes": 123,
  "notes_with_embeddings": 120,
  "notes_without_embeddings": 3,
  "coverage_percentage": 97.56,
  "model_info": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "target_dimension": 1536,
    "padding_used": true
  }
}
```

### 3. Test Automatic Embedding Generation
```bash
# Create a new note
curl -X POST http://localhost:8000/notes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Sermon",
    "content": "Amazing message about grace and mercy",
    "preacher": "Test Preacher"
  }'

# Check that embedding was generated automatically
curl -X GET http://localhost:8000/semantic/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Verify:** `notes_with_embeddings` count increased by 1

### 4. Test Search with Pagination
```bash
# First page
curl -X POST http://localhost:8000/semantic/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "faith",
    "limit": 10,
    "offset": 0
  }'

# Second page
curl -X POST http://localhost:8000/semantic/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "faith",
    "limit": 10,
    "offset": 10
  }'
```

**Verify:** Both return results with different notes

### 5. Test Similar Notes
```bash
curl -X GET http://localhost:8000/semantic/similar/1?limit=5 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Verify:** Returns similar notes with similarity scores

### 6. Test Background Regeneration
```bash
curl -X POST http://localhost:8000/semantic/regenerate-embeddings \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "message": "Embedding regeneration has been queued...",
  "status": "queued",
  "task_id": null
}
```

**Check server logs for background processing:**
```
INFO:app.api.semantic_routes_v2:Regeneration batch: processed 100 notes (offset 0)
INFO:app.api.semantic_routes_v2:Regeneration complete: 150 succeeded, 0 failed
```

## Performance Verification

### 1. Check HNSW Index
```sql
-- Connect to database
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'notes' AND indexname = 'idx_notes_embedding_hnsw';
```

**Expected:**
```
idx_notes_embedding_hnsw | CREATE INDEX idx_notes_embedding_hnsw ON notes USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')
```

### 2. Benchmark Search Speed
```bash
# Time a search query
time curl -X POST http://localhost:8000/semantic/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "salvation", "limit": 20}'
```

**Expected:** < 100ms for most datasets

## Rollback Plan

If issues occur:

### 1. Revert Code Changes
```bash
git checkout HEAD~1 app/main.py
git checkout HEAD~1 app/api/semantic_routes.py
```

### 2. Revert Database Migration
```bash
alembic downgrade -1
```

This will remove the HNSW index but keep all data intact.

### 3. Restart Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Monitoring

### Key Metrics to Watch

1. **Embedding Coverage**
   - Target: >95% of notes have embeddings
   - Check: `/semantic/status` endpoint

2. **Search Performance**
   - Target: <100ms average response time
   - Monitor: Application logs, APM tools

3. **Background Task Success Rate**
   - Target: >99% success rate
   - Monitor: Server logs for error messages

4. **Error Rates**
   - Target: <1% of requests fail
   - Monitor: `HTTPException` logs at ERROR level

### Log Patterns to Monitor

**Success Patterns:**
```
INFO:app.models.events:Generated embedding for note 123
INFO:app.api.semantic_routes_v2:Regeneration batch: processed 100 notes
```

**Error Patterns:**
```
ERROR:app.models.events:Failed to generate embedding for note 456: Service timeout
ERROR:app.services.embedding_service:Error generating embedding: Model not loaded
```

## Troubleshooting

### Issue: Event listeners not registered
**Symptom:** New notes don't have embeddings  
**Fix:** Check `app/main.py` lifespan function has:
```python
from app.models.events import register_note_events
register_note_events()
```

### Issue: HNSW index creation fails
**Symptom:** Migration fails with "operator class not found"  
**Fix:** Ensure pgvector extension is installed:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: Background tasks not running
**Symptom:** Regeneration returns "queued" but nothing happens  
**Fix:** Check server logs for task execution. Ensure server isn't restarting immediately after response.

### Issue: Import errors for tenacity
**Symptom:** `ModuleNotFoundError: No module named 'tenacity'`  
**Fix:**
```bash
pip install tenacity==8.2.3
```

## Success Criteria

Deployment is successful when:

- [x] All migrations applied without errors
- [x] Application starts with event listener registration message
- [x] New notes automatically get embeddings
- [x] Search queries return results in <100ms
- [x] Status endpoint shows >95% embedding coverage
- [x] Background regeneration completes successfully
- [x] No increase in error rates compared to baseline

## Support Contacts

- **Development Team:** [Your team contact]
- **Database Admin:** [DBA contact]
- **Infrastructure:** [DevOps contact]

## Additional Resources

- [SEMANTIC_SEARCH_V2_IMPLEMENTATION.md](./SEMANTIC_SEARCH_V2_IMPLEMENTATION.md) - Full implementation guide
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
