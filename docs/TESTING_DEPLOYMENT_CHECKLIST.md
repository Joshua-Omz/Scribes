# Background Worker Testing & Deployment Checklist

## ✅ Pre-Deployment Checklist

### Phase 1: Database Setup ✅ COMPLETE
- [x] Migration created: `2025-11-18_*_create_background_jobs_table.py`
- [x] Migration applied: `alembic upgrade head`
- [x] Table verified: `background_jobs` exists in PostgreSQL
- [x] Indexes created: `job_id`, `user_status`, `created_at`

### Phase 2: Code Implementation ✅ COMPLETE
- [x] Model: `app/models/background_job_model.py`
- [x] Schemas: `app/schemas/background_job_schemas.py`
- [x] Routes: `app/routes/job_routes.py` (3 endpoints)
- [x] Worker: `app/worker/tasks.py` (2 tasks)
- [x] Config: `app/core/config.py` (Redis settings)
- [x] Script: `run_worker.ps1`

### Phase 3: Dependencies ✅ COMPLETE
- [x] Added to requirements.txt: `redis==5.0.1`, `arq==0.25.0`
- [x] Installed: `pip install redis arq`
- [x] No syntax errors in code

---

## 🚀 Deployment Steps

### Step 1: Install Redis

**Option A: Chocolatey (Recommended for Windows)**
```powershell
# Install Chocolatey if not already installed
# See: https://chocolatey.org/install

# Install Redis
choco install redis-64 -y

# Verify installation
redis-server --version
```

**Option B: Manual Download**
```powershell
# Download from: https://github.com/microsoftarchive/redis/releases
# Latest: Redis-x64-3.0.504.msi
# Install and add to PATH
```

**Option C: WSL (Windows Subsystem for Linux)**
```bash
# In WSL terminal
sudo apt-get update
sudo apt-get install redis-server -y
```

### Step 2: Start Redis Server

**Windows (Installed via Chocolatey):**
```powershell
# Start Redis server
redis-server

# Or as Windows service:
redis-server --service-install
redis-server --service-start
```

**WSL:**
```bash
sudo service redis-server start
```

**Verify Redis is running:**
```powershell
# Should return "PONG"
redis-cli ping

# Or check if port 6379 is listening
netstat -an | findstr "6379"
```

### Step 3: Configure Environment

Ensure `.env` file has:
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379

# ARQ Worker Settings (optional - defaults are fine)
ARQ_JOB_TIMEOUT=3600
ARQ_MAX_JOBS=10
ARQ_KEEP_RESULT=3600
```

### Step 4: Start ARQ Worker  

**Open a NEW terminal** (separate from API server):
```powershell
cd "C:\flutter proj\Scribes\backend2"

# Activate virtual environment
.\venv\Scripts\Activate.ps1
# Start worker using script
.\run_worker.ps1

# OR manually:
arq app.worker.tasks.WorkerSettings
```

**Expected output:**
```
🚀 ARQ Worker starting up...
📍 Redis URL: redis://localhost:6379
⚙️  Max jobs: 10
⏱️  Job timeout: 3600s
✅ ARQ tasks registered: regenerate_embeddings_arq, check_and_send_reminders
Nov 18 12:00:00 [INFO] Starting worker for 2 functions: regenerate_embeddings_arq, check_and_send_reminders
Nov 18 12:00:00 [INFO] redis_version=5.0.1 mem_usage=1.2M clients_connected=1 db_keys=0
```

### Step 5: Start API Server

**In the ORIGINAL terminal:**
```powershell
cd "C:\flutter proj\Scribes\backend2"

# Activate virtual environment if not already
.\venv\Scripts\Activate.ps1

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
🚀 Starting Scribes v0.1.0
📍 Environment: development
🔧 Debug mode: True
✅ Registered automatic embedding generation listeners
```

### Step 6: Verify System Health

**Open browser to:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Check all 3 components running:**
1. ✅ Redis Server (port 6379)
2. ✅ ARQ Worker (separate terminal)
3. ✅ FastAPI Server (port 8000)

---

## 🧪 Testing Workflow

### Test 1: Job Status Endpoint

**GET /jobs (List user jobs):**
```http
GET http://localhost:8000/jobs
Authorization: Bearer {your_access_token}
```

**Expected Response:**
```json
{
  "jobs": [],
  "total": 0
}
```

### Test 2: Trigger Embedding Regeneration

**Prerequisites:**
- User must be logged in
- User must have at least 1 note

**POST /semantic/regenerate-embeddings:**
```http
POST http://localhost:8000/semantic/regenerate-embeddings
Authorization: Bearer {your_access_token}
```

**Expected Response:**
```json
{
  "message": "Embedding regeneration has been queued. Track progress at GET /jobs/{job_id}",
  "status": "queued",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Worker logs should show:**
```
[ARQ] Starting embedding regeneration task for user 1, job 550e8400-...
[ARQ] Processing 150 notes for user 1
[ARQ] Batch complete: 100/150 processed, 0 failed, 67% done
[ARQ] Embedding regeneration complete for job 550e8400-...: 150 succeeded, 0 failed
```

### Test 3: Monitor Job Progress

**GET /jobs/{job_id}:**
```http
GET http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {your_access_token}
```

**While running:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "embedding_regeneration",
  "status": "running",
  "progress_percent": 67,
  "total_items": 150,
  "processed_items": 100,
  "failed_items": 0,
  "created_at": "2025-11-18T12:00:00Z",
  "started_at": "2025-11-18T12:00:05Z",
  "completed_at": null
}
```

**After completion:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress_percent": 100,
  "total_items": 150,
  "processed_items": 150,
  "failed_items": 0,
  "result_data": {
    "embeddings_generated": 150,
    "failed_notes": 0,
    "total_notes": 150,
    "completion_time": "2025-11-18T12:02:30Z"
  },
  "completed_at": "2025-11-18T12:02:30Z"
}
```

### Test 4: Reminder Scheduling

**Create a reminder:**
```http
POST http://localhost:8000/reminders
Authorization: Bearer {your_access_token}
Content-Type: application/json

{
  "note_id": 123,
  "message": "Review sermon notes",
  "scheduled_at": "2025-11-18T12:15:00Z"
}
```

**Wait for cron to run** (every 15 minutes: :00, :15, :30, :45)

**Worker logs should show:**
```
[ARQ CRON] Checking for due reminders...
[ARQ CRON] Found 1 due reminders
[ARQ CRON] Sending reminder 456: Review sermon notes
[ARQ CRON] Reminder processing complete: 1 sent, 0 failed
```

**Verify reminder updated:**
```http
GET http://localhost:8000/reminders/{reminder_id}
```

**Response:**
```json
{
  "id": 456,
  "status": "sent",  // Changed from "pending"
  ...
}
```

### Test 5: Worker Persistence

**Stop and restart worker:**
```powershell
# In worker terminal: Ctrl+C to stop
# Then restart:
.\run_worker.ps1
```

**Verify:**
- Jobs in "queued" status are picked up
- Jobs in "running" status are NOT restarted (this is expected - they're marked as failed after timeout)
- Completed jobs remain in database

**Query database:**
```sql
SELECT job_id, status, progress_percent 
FROM background_jobs 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Redis Issues

**Error: "Connection refused"**
```
Fix: Start Redis server
  redis-server
```

**Error: "redis-cli not found"**
```
Fix: Add Redis to PATH or use full path
  C:\Program Files\Redis\redis-cli.exe ping
```

**Error: "Could not connect to Redis at localhost:6379"**
```
Fix: Check Redis is running
  netstat -an | findstr "6379"
  
If not running:
  redis-server
```

### Worker Issues

**Error: "No module named 'arq'"**
```
Fix: Install dependencies
  pip install -r requirements.txt
```

**Error: "Database connection failed"**
```
Fix: Check DATABASE_URL in .env
  Verify PostgreSQL is running
```

**Worker starts but doesn't process jobs**
```
Fix: Check Redis connection in worker
  - Verify REDIS_URL in .env
  - Test: redis-cli ping
  - Check worker logs for connection errors
```

### API Issues

**Error: "Job not found" when querying /jobs/{job_id}**
```
Fix: Verify:
  - Using correct access token
  - Job belongs to authenticated user
  - job_id is valid UUID
```

**Jobs stuck in "queued" status**
```
Fix: 
  - Ensure worker is running
  - Check worker logs for errors
  - Verify Redis queue: redis-cli LLEN "arq:queue:scribes:queue"
```

---

## 📊 Monitoring Commands

### Check Redis Status
```powershell
# Ping test
redis-cli ping

# Get info
redis-cli INFO

# Check queue length
redis-cli LLEN "arq:queue:scribes:queue"

# View all keys
redis-cli KEYS "*"
```

### Check Database
```sql
-- Recent jobs
SELECT job_id, job_type, status, progress_percent, created_at
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
ORDER BY created_at DESC;

-- Long-running jobs
SELECT job_id, job_type, 
       EXTRACT(EPOCH FROM (NOW() - started_at)) / 60 as minutes_running
FROM background_jobs
WHERE status = 'running'
ORDER BY started_at;
```

### Check API Health
```powershell
# Health endpoint
curl http://localhost:8000/health

# API documentation
# Open: http://localhost:8000/docs
```

---

## ✅ Success Criteria

### All Tests Pass When:

1. **Redis is running**
   - `redis-cli ping` returns "PONG"
   - Port 6379 is listening

2. **Worker is running**
   - Terminal shows "ARQ Worker starting up..."
   - No connection errors
   - Cron job logs appear every 15 minutes

3. **API server is running**
   - http://localhost:8000/docs accessible
   - Health check returns 200 OK

4. **Job creation works**
   - POST /semantic/regenerate-embeddings returns job_id
   - job_id is not null

5. **Progress tracking works**
   - GET /jobs/{job_id} shows progress increasing
   - Status changes: queued → running → completed
   - progress_percent goes from 0 → 100

6. **Reminders work**
   - Cron job runs every 15 minutes
   - Due reminders change status to "sent"
   - Worker logs show reminder processing

7. **Persistence works**
   - Worker restart doesn't lose queued jobs
   - Database contains job history
   - Failed jobs have error messages

---

## 🎊 Final Verification

Run this SQL to see complete job history:
```sql
SELECT 
    job_id,
    job_type,
    status,
    progress_percent || '%' as progress,
    processed_items || '/' || total_items as items,
    CASE 
        WHEN status = 'completed' THEN 'COMPLETED in ' || 
             EXTRACT(EPOCH FROM (completed_at - started_at)) || 's'
        WHEN status = 'failed' THEN 'FAILED: ' || error_message
        WHEN status = 'running' THEN 'RUNNING for ' || 
             EXTRACT(EPOCH FROM (NOW() - started_at)) || 's'
        ELSE status
    END as details,
    created_at
FROM background_jobs
ORDER BY created_at DESC
LIMIT 20;
```

**Expected Output:**
```
job_id                               | job_type              | status    | progress | items   | details                  | created_at
-------------------------------------+-----------------------+-----------+----------+---------+--------------------------+-------------------
550e8400-e29b-41d4-a716-446655440000 | embedding_regeneration| completed | 100%     | 150/150 | COMPLETED in 125.3s     | 2025-11-18 12:00:00
```

---

## 📝 Documentation References

- **Setup Guide:** `docs/BACKGROUND_WORKER_SETUP.md`
- **Implementation Summary:** `docs/BACKGROUND_OPERATIONS_IMPLEMENTATION.md`
- **API Docs:** http://localhost:8000/docs (when server running)

---

## 🚀 Ready for Production?

Before deploying to production, ensure:
- [ ] Redis has persistence enabled (AOF or RDB)
- [ ] Worker runs as system service
- [ ] Health checks configured
- [ ] Alerting on job failures
- [ ] Log aggregation setup
- [ ] Multiple workers for redundancy
- [ ] Database backups include `background_jobs` table

---

**Implementation Status: 9/10 Todos Complete!**

Only remaining: Install Redis and run end-to-end test (this checklist guides you through it).
