# Background Worker Setup Guide

## Overview

Scribes backend uses **ARQ (Async Redis Queue)** for background task processing. This enables:
- ✅ Async embedding regeneration without blocking API
- ✅ Scheduled reminder sending
- ✅ Task progress tracking
- ✅ Distributed processing across multiple workers
- ✅ Automatic retries and error handling

## Prerequisites

1. **Redis Server** - Message broker for task queue
2. **Python 3.11+** - Worker runtime
3. **Database Access** - Worker needs same DB as API

## Installation

### 1. Install Redis

**Windows:**
```powershell
# Via Chocolatey
choco install redis-64

# Or download from:
# https://github.com/microsoftarchive/redis/releases
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Mac (Homebrew)
brew install redis
```

### 2. Install Python Dependencies

```powershell
pip install redis==5.0.1 arq==0.25.0
```

Dependencies are already in `requirements.txt`.

## Configuration

Add to your `.env` file:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=10

# ARQ Worker Settings
ARQ_JOB_TIMEOUT=3600        # 1 hour max per job
ARQ_MAX_JOBS=10             # Max concurrent jobs
ARQ_KEEP_RESULT=3600        # Keep results for 1 hour
```

## Running the Worker

### Option 1: PowerShell Script (Recommended)

```powershell
cd backend2
.\run_worker.ps1
```

The script will:
- ✅ Check if Redis is running
- ✅ Start the ARQ worker
- ✅ Show helpful error messages

### Option 2: Manual Command

```powershell
cd backend2
arq app.worker.tasks.WorkerSettings
```

### Option 3: Background Service (Production)

**Windows (NSSM):**
```powershell
# Install NSSM
choco install nssm

# Create service
nssm install ScribesWorker "C:\path\to\python.exe" "C:\path\to\backend2\run_worker.ps1"
nssm start ScribesWorker
```

**Linux (systemd):**
```bash
# Create service file: /etc/systemd/system/scribes-worker.service
[Unit]
Description=Scribes ARQ Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend2
ExecStart=/path/to/venv/bin/arq app.worker.tasks.WorkerSettings
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable scribes-worker
sudo systemctl start scribes-worker
```

## Worker Tasks

### Registered Tasks

1. **`regenerate_embeddings_arq`**
   - Regenerates embeddings for all user notes
   - Processes in batches of 100
   - Updates progress in database
   - Can handle 1000s of notes

2. **`check_and_send_reminders`** (Cron)
   - Runs every 15 minutes (0, 15, 30, 45)
   - Queries `reminders` WHERE `scheduled_at <= now()`
   - Sends notifications/emails
   - Updates status to 'sent'

### Task Flow

```
API Server                  Redis Queue              ARQ Worker
────────────                ───────────              ──────────
  │                              │                        │
  │  POST /semantic/regenerate   │                        │
  │──────────────────────────────>                        │
  │                              │                        │
  │  Create BackgroundJob        │                        │
  │  (status='queued')           │                        │
  │                              │                        │
  │  Enqueue ARQ task            │                        │
  │─────────────────────────────>│                        │
  │                              │                        │
  │  Return job_id               │                        │
  │<──────────────────────────────                        │
  │                              │                        │
  │                              │  Dequeue task          │
  │                              │───────────────────────>│
  │                              │                        │
  │                              │        Process notes   │
  │                              │        Update progress │
  │                              │        in database     │
  │                              │                        │
  │  GET /jobs/{job_id}          │                        │
  │──────────────────────────────>                        │
  │  (Check progress)            │                        │
  │                              │                        │
  │  {progress: 67%, ...}        │                        │
  │<──────────────────────────────                        │
  │                              │                        │
  │                              │        Mark completed  │
  │                              │<───────────────────────│
  │                              │                        │
```

## Monitoring

### Check Worker Status

```powershell
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check queue length
redis-cli LLEN "arq:queue:scribes:queue"

# View queued jobs
redis-cli LRANGE "arq:queue:scribes:queue" 0 -1
```

### Worker Logs

The worker outputs to stdout:
```
🚀 ARQ Worker starting up...
📍 Redis URL: redis://localhost:6379
⚙️  Max jobs: 10
⏱️  Job timeout: 3600s
✅ ARQ tasks registered: regenerate_embeddings_arq, check_and_send_reminders
[ARQ] Starting embedding regeneration task for user 1, job abc123...
[ARQ] Processing 150 notes for user 1
[ARQ] Batch complete: 100/150 processed, 0 failed, 67% done
[ARQ] Embedding regeneration complete for job abc123: 150 succeeded, 0 failed
```

### Track Job Progress via API

```bash
# Get job status
curl http://localhost:8000/jobs/{job_id}

# Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress_percent": 67,
  "processed_items": 100,
  "total_items": 150,
  "failed_items": 0,
  ...
}
```

## Troubleshooting

### Worker Won't Start

**Error: "Connection refused"**
- ✅ Check Redis is running: `redis-cli ping`
- ✅ Verify REDIS_URL in .env
- ✅ Check firewall allows port 6379

**Error: "No module named 'arq'"**
- ✅ Install dependencies: `pip install -r requirements.txt`
- ✅ Activate virtual environment

**Error: "Database connection failed"**
- ✅ Verify DATABASE_URL in .env
- ✅ Check PostgreSQL is running
- ✅ Test connection: `psql -U postgres scribes_db`

### Tasks Not Processing

**Jobs stuck in 'queued' status:**
- ✅ Ensure worker is running: `.\run_worker.ps1`
- ✅ Check worker logs for errors
- ✅ Verify Redis queue: `redis-cli LLEN "arq:queue:scribes:queue"`

**Tasks failing silently:**
- ✅ Check worker stdout logs
- ✅ Query BackgroundJob table for error_message
- ✅ Enable debug logging in worker

### Performance Issues

**Worker processing slowly:**
- ✅ Increase `ARQ_MAX_JOBS` (default: 10)
- ✅ Run multiple workers on different machines
- ✅ Optimize batch size in tasks

**High memory usage:**
- ✅ Decrease batch size (currently 100)
- ✅ Add memory limits in systemd/NSSM
- ✅ Monitor with `htop` or Task Manager

## Production Recommendations

1. **Run Multiple Workers**
   - Scale horizontally by starting workers on different machines
   - All connect to same Redis instance
   - Load balances automatically

2. **Monitor with Flower** (Optional)
   - Install: `pip install flower`
   - Run: `celery -A app.worker flower`
   - Dashboard at http://localhost:5555

3. **Set Resource Limits**
   ```env
   ARQ_MAX_JOBS=5            # Conservative for production
   ARQ_JOB_TIMEOUT=7200      # 2 hours max
   ARQ_KEEP_RESULT=86400     # Keep results 24 hours
   ```

4. **Health Checks**
   - Monitor Redis uptime
   - Alert if worker process dies
   - Track job failure rates

5. **Backup Strategy**
   - Redis persistence: Enable AOF or RDB snapshots
   - Database backups: Include `background_jobs` table
   - Monitor disk space

## API Endpoints for Job Tracking

### Trigger Embedding Regeneration
```http
POST /semantic/regenerate-embeddings
Authorization: Bearer {access_token}

Response:
{
  "message": "Embedding regeneration has been queued...",
  "status": "queued",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Job Status
```http
GET /jobs/{job_id}
Authorization: Bearer {access_token}

Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "embedding_regeneration",
  "status": "running",
  "progress_percent": 67,
  "total_items": 150,
  "processed_items": 100,
  "failed_items": 0,
  "created_at": "2025-11-18T00:30:00Z",
  "started_at": "2025-11-18T00:30:05Z",
  "completed_at": null
}
```

### List User Jobs
```http
GET /jobs?limit=20&offset=0&status=running
Authorization: Bearer {access_token}

Response:
{
  "jobs": [...],
  "total": 5
}
```

## Architecture Diagram

```
┌─────────────────┐
│   FastAPI App   │
│   (Port 8000)   │
└────────┬────────┘
         │
         │ Enqueue Task
         ▼
┌─────────────────┐
│  Redis Queue    │
│  (Port 6379)    │
└────────┬────────┘
         │
         │ Dequeue & Process
         ▼
┌─────────────────┐      ┌──────────────────┐
│  ARQ Worker #1  │◄────►│   PostgreSQL     │
└─────────────────┘      │  (Shared State)  │
┌─────────────────┐      │                  │
│  ARQ Worker #2  │◄────►│  - background_jobs│
└─────────────────┘      │  - notes         │
┌─────────────────┐      │  - reminders     │
│  ARQ Worker #N  │◄────►│                  │
└─────────────────┘      └──────────────────┘
```

## Next Steps

1. Start Redis server
2. Run worker: `.\run_worker.ps1`
3. Start API server: `uvicorn app.main:app --reload`
4. Test embedding regeneration via Swagger docs
5. Monitor job progress at `/jobs/{job_id}`
