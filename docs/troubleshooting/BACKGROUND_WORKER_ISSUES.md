# Background Worker Troubleshooting Guide

## 🐛 Common Issues & Solutions

This guide documents issues encountered during the background worker implementation and their solutions.

---

## Issue #1: Jobs Queued But Not Processed ✅ FIXED

### Symptoms
- `POST /semantic/regenerate-embeddings` returns a job_id
- Job status shows `"queued"` in database
- Worker terminal shows no activity
- Job never transitions to `"running"` or `"completed"`

### Root Cause
**Queue name mismatch** between API and worker:
- **Worker configuration** (`app/worker/arq_config.py`): Uses queue name `"scribes:queue"`
- **API code** (`app/routes/semantic_routes.py`): Was using ARQ's default queue name `"arq:queue"`
- **Result**: Jobs were enqueued to `"arq:queue"` but worker was listening to `"scribes:queue"`

### Diagnosis Steps
```powershell
# Check Redis keys
redis-cli KEYS "*"

# Expected output should include:
# "arq:queue:scribes:queue"  ← Correct queue

# If you see just "arq:queue" instead, that's the problem!
```

### Solution Applied
Modified `app/routes/semantic_routes.py` line ~451:

**Before:**
```python
arq_job = await redis.enqueue_job(
    'regenerate_embeddings_arq',
    current_user.id,
    str(job.job_id)
)
```


**After:**
```python
arq_job = await redis.enqueue_job(
    'regenerate_embeddings_arq',
    current_user.id,
    str(job.job_id),
    _queue_name="scribes:queue"  # ✅ Must match WorkerSettings.queue_name
)
```

### Verification
1. Restart ARQ worker: `./run_worker.ps1`
2. Clear Redis: `redis-cli FLUSHDB` (only if needed)
3. Trigger job: `POST /semantic/regenerate-embeddings`
4. Check worker logs - should immediately show:
   ```
   [ARQ] Starting embedding regeneration task for user 1, job abc123...
   ```

---

## Issue #2: Reminder Cron Job Failing ✅ FIXED

### Symptoms
```
[ARQ CRON] Failed to send reminder 2: 'Reminder' object has no attribute 'message'
AttributeError: 'Reminder' object has no attribute 'message'
```

### Root Cause
**Model field mismatch**:
- Worker code tried to access `reminder.message`
- Reminder model (`app/models/reminder_model.py`) doesn't have a `message` field
- Actual fields: `id`, `user_id`, `note_id`, `scheduled_at`, `status`, `created_at`, `updated_at`

### Solution Applied
Modified `app/worker/tasks.py` line ~243:

**Before:**
```python
logger.info(f"[ARQ CRON] Sending reminder {reminder.id}: {reminder.message}")
```

**After:**
```python
logger.info(f"[ARQ CRON] Sending reminder {reminder.id} for note {reminder.note_id} to user {reminder.user_id}")
```

### Verification
1. Wait for next cron run (every 15 minutes: :00, :15, :30, :45)
2. OR create a reminder scheduled in the past:
   ```sql
   INSERT INTO reminders (user_id, note_id, scheduled_at, status)
   VALUES (1, 1, NOW() - INTERVAL '1 hour', 'pending');
   ```
3. Watch worker logs - should show:
   ```
   [ARQ CRON] Checking for due reminders...
   [ARQ CRON] Found 1 due reminders
   [ARQ CRON] Sending reminder 1 for note 1 to user 1
   [ARQ CRON] Reminder processing complete: 1 sent, 0 failed
   ```

---

## Issue #3: Redis Type Error ⚠️ PARTIALLY RESOLVED

### Symptoms
```
redis.exceptions.ResponseError: WRONGTYPE Operation against a key holding the wrong kind of value
```

### Root Cause
- Redis keys from different queue implementations conflicted
- Mixing ARQ queue operations with raw Redis list operations
- Previous corrupted data in Redis

### Solution
```powershell
# Clear Redis database (WARNING: Deletes all Redis data)
redis-cli FLUSHDB

# Or more selectively, delete only ARQ keys:
redis-cli --scan --pattern "arq:*" | xargs redis-cli DEL
```

### Prevention
- Always use `_queue_name` parameter when enqueuing jobs
- Don't mix ARQ operations with manual Redis list operations
- Use ARQ's built-in methods for queue inspection

---

## Issue #4: Worker Not Starting

### Symptoms
- `./run_worker.ps1` fails
- Error: "No module named 'arq'"
- Error: "Connection refused"

### Solutions

**Problem: Missing dependencies**
```powershell
# Verify installation
pip list | findstr "arq redis"

# Should show:
# arq        0.25.0
# redis      5.0.1

# If missing:
pip install -r requirements.txt
```

**Problem: Redis not running**
```powershell
# Check if Redis is running
redis-cli ping

# Should return: PONG

# If fails, start Redis:
redis-server

# Or as Windows service:
redis-server --service-start
```

**Problem: Wrong Python environment**
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Then run worker
./run_worker.ps1
```

---

## Issue #5: Database Connection Errors in Worker

### Symptoms
```
asyncpg.exceptions.InvalidPasswordError: password authentication failed
sqlalchemy.exc.OperationalError: could not connect to server
```

### Root Cause
- Worker creates its own database engine
- `.env` file not loaded properly
- Wrong DATABASE_URL in environment

### Solution
1. Verify `.env` file exists in project root
2. Check DATABASE_URL is correct:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/scribes_db
   ```
3. Test connection manually:
   ```python
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine
   
   async def test():
       engine = create_async_engine("postgresql+asyncpg://...")
       async with engine.connect() as conn:
           print("Connected!")
   
   asyncio.run(test())
   ```

---

## Issue #6: Jobs Stuck in "Running" Status

### Symptoms
- Job shows `status: "running"`
- Worker has crashed or been stopped
- Job never completes or fails

### Root Cause
- Worker crashed mid-execution
- Worker was stopped before job completed
- Database transaction not committed

### Solution

**Manual cleanup:**
```sql
-- Find stuck jobs (running for > 1 hour)
SELECT job_id, job_type, 
       EXTRACT(EPOCH FROM (NOW() - started_at)) / 60 as minutes_running
FROM background_jobs
WHERE status = 'running'
  AND started_at < NOW() - INTERVAL '1 hour';

-- Mark as failed
UPDATE background_jobs
SET status = 'failed',
    error_message = 'Worker stopped unexpectedly',
    completed_at = NOW()
WHERE status = 'running'
  AND started_at < NOW() - INTERVAL '1 hour';
```

**Prevention:**
- Use ARQ's `job_timeout` setting (default: 3600s = 1 hour)
- ARQ automatically marks jobs as failed after timeout
- Implement graceful shutdown handling

---

## Diagnostic Commands

### Check System Status

```powershell
# 1. Redis status
redis-cli ping                                    # Should return: PONG
redis-cli INFO | findstr "redis_version"         # Check version

# 2. Check queue
redis-cli LLEN "arq:queue:scribes:queue"         # Number of queued jobs
redis-cli KEYS "arq:*"                           # All ARQ keys

# 3. Check worker is running
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# 4. API server status
curl http://localhost:8000/health                # Health check
```

### Check Database

```sql
-- Recent jobs
SELECT job_id, job_type, status, progress_percent, 
       created_at, started_at, completed_at
FROM background_jobs
ORDER BY created_at DESC
LIMIT 10;

-- Jobs by status
SELECT status, COUNT(*) as count
FROM background_jobs
GROUP BY status;

-- Failed jobs
SELECT job_id, job_type, error_message, created_at
FROM background_jobs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;

-- Average completion time
SELECT job_type,
       AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_seconds
FROM background_jobs
WHERE status = 'completed'
GROUP BY job_type;
```

### Monitor Worker Logs

```powershell
# Worker terminal should show:
# ✅ Good:
# [ARQ] Starting embedding regeneration task...
# [ARQ] Processing 150 notes for user 1
# [ARQ] Batch complete: 100/150 processed, 0 failed, 67% done

# ❌ Bad:
# Connection refused
# No module named...
# AttributeError...
# Database connection failed
```

---

## Testing Checklist

Use this checklist to verify everything works:

### ✅ Pre-Test Setup
- [ ] Redis server running (`redis-cli ping` returns PONG)
- [ ] PostgreSQL running
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip list | findstr "arq redis"`)
- [ ] `.env` file configured

### ✅ Worker Test
- [ ] Worker starts without errors: `./run_worker.ps1`
- [ ] Sees startup message: "🚀 ARQ Worker starting up..."
- [ ] Shows registered functions: "Starting worker for 2 functions"
- [ ] No connection errors in logs

### ✅ API Test
- [ ] API starts: `uvicorn app.main:app --reload`
- [ ] Swagger docs accessible: http://localhost:8000/docs
- [ ] Health check passes: http://localhost:8000/health

### ✅ End-to-End Test
- [ ] Login successful (get access token)
- [ ] Trigger regeneration: `POST /semantic/regenerate-embeddings`
- [ ] Returns valid job_id (not null)
- [ ] Worker picks up job immediately (check logs)
- [ ] Job status endpoint works: `GET /jobs/{job_id}`
- [ ] Progress updates in real-time (0% → 100%)
- [ ] Job completes successfully
- [ ] Result data populated in database

### ✅ Reminder Test
- [ ] Create reminder in past
- [ ] Wait for cron (max 15 minutes)
- [ ] Worker processes reminder
- [ ] Status changes to "sent"
- [ ] No errors in logs

---

## Quick Fixes

### Reset Everything
```powershell
# 1. Stop worker (Ctrl+C in worker terminal)
# 2. Stop API (Ctrl+C in API terminal)
# 3. Clear Redis
redis-cli FLUSHDB

# 4. Reset stuck jobs in database
# Run SQL: UPDATE background_jobs SET status = 'failed' WHERE status = 'running';

# 5. Restart worker
./run_worker.ps1

# 6. Restart API
uvicorn app.main:app --reload

# 7. Test again
```

### Force Job Cleanup
```sql
-- Mark all queued/running jobs as failed
UPDATE background_jobs
SET status = 'failed',
    error_message = 'Manual cleanup - system reset',
    completed_at = NOW()
WHERE status IN ('queued', 'running');
```

### Inspect Specific Job
```python
# Run this in Python REPL
import asyncio
from sqlalchemy import select
from app.core.database import get_db
from app.models.background_job_model import BackgroundJob

async def check_job(job_id_str):
    async for db in get_db():
        from uuid import UUID
        result = await db.execute(
            select(BackgroundJob).where(BackgroundJob.job_id == UUID(job_id_str))
        )
        job = result.scalar_one_or_none()
        if job:
            print(f"Status: {job.status}")
            print(f"Progress: {job.progress_percent}%")
            print(f"Items: {job.processed_items}/{job.total_items}")
            print(f"Error: {job.error_message}")
        else:
            print("Job not found")
        break

asyncio.run(check_job("your-job-id-here"))
```

---

## When to Contact Support

If you've tried all the above and still have issues:

1. **Collect diagnostic info:**
   ```powershell
   # System info
   python --version
   redis-cli --version
   pip freeze > installed_packages.txt
   
   # Redis status
   redis-cli INFO > redis_info.txt
   
   # Database status
   # Run: SELECT * FROM background_jobs ORDER BY created_at DESC LIMIT 5;
   # Save output
   ```

2. **Check logs:**
   - Worker terminal output (last 50 lines)
   - API server logs
   - PostgreSQL logs (`pg_log/`)

3. **Describe the issue:**
   - What were you doing?
   - What did you expect?
   - What actually happened?
   - Error messages (full text)

---

## Success Indicators

You know everything is working when:

✅ Worker terminal shows:
```
🚀 ARQ Worker starting up...
📍 Redis URL: redis://localhost:6379
⚙️  Max jobs: 10
Starting worker for 2 functions: regenerate_embeddings_arq, cron:check_and_send_reminders
```

✅ Job processing shows:
```
[ARQ] Starting embedding regeneration task for user 1, job abc-123...
[ARQ] Processing 150 notes for user 1
[ARQ] Batch complete: 100/150 processed, 0 failed, 67% done
[ARQ] Embedding regeneration complete: 150 succeeded, 0 failed
```

✅ API returns:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress_percent": 100,
  "result_data": {
    "embeddings_generated": 150,
    "failed_notes": 0
  }
}
```

---

## Additional Resources

- **Setup Guide:** `docs/BACKGROUND_WORKER_SETUP.md`
- **Implementation Summary:** `docs/BACKGROUND_OPERATIONS_IMPLEMENTATION.md`
- **Testing Checklist:** `docs/TESTING_DEPLOYMENT_CHECKLIST.md`
- **ARQ Documentation:** https://arq-docs.helpmanual.io/
- **Redis Documentation:** https://redis.io/docs/

---

**Last Updated:** November 20, 2025  
**Issues Resolved:** 6  
**Status:** Production Ready ✅
