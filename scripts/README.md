# Scribes Backend - Utility Scripts

This directory contains all utility scripts for development, testing, database management, and operations.

## 📁 Directory Structure

```
scripts/
├── admin/           # Administrative and setup scripts
├── database/        # Database utilities and validation
├── testing/         # Test data generation and test runners
└── workers/         # Background worker scripts
```

## 🔧 Admin Scripts (`admin/`)

### `bootstrap_admin.py`
Creates the initial admin user for the application.

**Usage:**
```bash
python scripts/admin/bootstrap_admin.py
```

**What it does:**
- Creates a superuser account with admin privileges
- Sets up initial user profile
- Useful for first-time deployment or resetting admin access

**Requirements:**
- Database must be initialized (run migrations first)
- Environment variables configured (.env file)

---

## 💾 Database Scripts (`database/`)

### `config_validationScripts.py`
Validates database configuration and connection settings.

**Usage:**
```bash
python scripts/database/config_validationScripts.py
```

**What it does:**
- Checks database connection
- Validates environment variables
- Tests pgvector extension availability
- Verifies table schemas

**When to use:**
- After fresh deployment
- Troubleshooting connection issues
- Before running migrations

---

## 🧪 Testing Scripts (`testing/`)

### `create_test_data.py`
Generates realistic test data for AI Assistant manual testing.

**Usage:**
```bash
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Run the script
python scripts/testing/create_test_data.py
```

**What it does:**
- Creates test user: `test@scribes.local`
- Generates 5 theological notes with rich content
- Chunks each note into semantic segments (~200 tokens each)
- Generates 384-dimensional embeddings for each chunk
- Stores everything in database for RAG testing

**Output:**
- Test User ID: 7
- 5 Notes with theological content
- ~10 chunks per note run
- All chunks have embeddings ready for semantic search

**Use case:**
- Manual testing of AI Assistant queries
- Validating RAG pipeline end-to-end
- Testing semantic search accuracy

**See also:**
- `docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md`

---

### `run_embedding_tests.ps1`
PowerShell script to run embedding-related tests.

**Usage:**
```powershell
.\scripts\testing\run_embedding_tests.ps1
```

**What it does:**
- Runs pytest for embedding service tests
- Validates embedding dimensions (384)
- Tests chunking logic
- Verifies semantic search functionality

---

## 👷 Worker Scripts (`workers/`)

### `run_worker.ps1`
Starts the ARQ background worker for async job processing.

**Usage:**
```powershell
.\scripts\workers\run_worker.ps1
```

**What it does:**
- Starts the ARQ worker process
- Processes background jobs (exports, embeddings, etc.)
- Monitors Redis queue
- Handles job retries and failures

**Requirements:**
- Redis server must be running
- Environment variables configured
- Virtual environment activated

**For production:**
- Use process manager (systemd, supervisor, or PM2)
- See: `docs/BACKGROUND_WORKER_SETUP.md`

---

## 🚀 Quick Start Guide

### First-Time Setup
```bash
# 1. Set up virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Validate database config
python scripts/database/config_validationScripts.py

# 5. Run migrations
alembic upgrade head

# 6. Create admin user
python scripts/admin/bootstrap_admin.py
```

### Testing Setup
```bash
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Create test data
python scripts/testing/create_test_data.py

# 3. Run tests
pytest
# or run specific test suite
.\scripts\testing\run_embedding_tests.ps1
```

### Production Deployment
```bash
# 1. Validate configuration
python scripts/database/config_validationScripts.py

# 2. Run migrations
alembic upgrade head

# 3. Create admin user
python scripts/admin/bootstrap_admin.py

# 4. Start background worker (in separate process/terminal)
.\scripts\workers\run_worker.ps1

# 5. Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📚 Related Documentation

- **Testing Guide:** `docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md`
- **Background Jobs:** `docs/BACKGROUND_WORKER_SETUP.md`
- **Database Setup:** `docs/database/`
- **Admin Guide:** `ADMIN_QUICK_START.md`

---

## 🛠️ Troubleshooting

### Script Import Errors
If you get `ModuleNotFoundError`:
```bash
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Verify you're in project root
cd "C:\flutter proj\Scribes\backend2"

# Run script with python -m to ensure proper imports
python -m scripts.testing.create_test_data
```

### Database Connection Issues
```bash
# Validate configuration
python scripts/database/config_validationScripts.py

# Check if PostgreSQL is running
# Check .env file has correct DATABASE_URL
```

### Worker Not Processing Jobs
```bash
# Check Redis connection
redis-cli ping

# Verify environment variables
# Check app/worker/worker.py configuration
```

---

## 💡 Best Practices

1. **Always activate virtual environment** before running scripts
2. **Run validation scripts** before deployment
3. **Use test data scripts** in development, never in production
4. **Check logs** in `logs/` directory if scripts fail
5. **Keep .env secure** and never commit it to version control

---

## 🔐 Security Notes

- **bootstrap_admin.py**: Prompts for password securely (no echo)
- **create_test_data.py**: Only for development/testing environments
- **Never run test scripts in production** - they create mock data
- **Validate .env permissions** (should be 600 on Unix systems)

---

**Last Updated:** December 12, 2025
