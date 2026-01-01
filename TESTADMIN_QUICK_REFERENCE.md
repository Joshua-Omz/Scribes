# Quick Reference: Using testadmin with Test Scripts

## testadmin User Credentials
```
Email:     testadmin@example.com
Username:  testadmin
Password:  TestAdmin123
Role:      admin
Superuser: true
User ID:   1 (dynamically retrieved by scripts)
```

## Quick Start Commands

### 1. Create/Verify testadmin user
```bash
cd /workspace
python scripts/admin/bootstrap_admin.py testadmin@example.com TestAdmin123
```

### 2. Create test data for testadmin
```bash
cd /workspace
PYTHONPATH=/workspace python scripts/testing/create_test_data.py
```

### 3. Verify everything is ready
```bash
PYTHONPATH=/workspace python scripts/testing/verify_test_data.py
```

## Common Test Scripts

### Check data integrity
```bash
# Check for duplicate chunks
PYTHONPATH=/workspace python scripts/testing/check_chunks.py

# Check embedding storage quality
PYTHONPATH=/workspace python scripts/testing/check_embedding_storage.py
```

### Debug relevance scores
```bash
# Quick score check
PYTHONPATH=/workspace python scripts/testing/quick_score_check.py

# Detailed relevance analysis
PYTHONPATH=/workspace python scripts/testing/debug_relevance_scores.py

# Deep investigation of low scores
PYTHONPATH=/workspace python scripts/testing/investigate_low_scores.py
```

### Test caching pipeline
```bash
# Full pipeline caching test (6 scenarios)
PYTHONPATH=/workspace python scripts/testing/test_pipeline_caching.py
```

### Cleanup when needed
```bash
# Remove all test data for testadmin
PYTHONPATH=/workspace python scripts/testing/cleanup_test_chunks.py
# (Will prompt for confirmation)
```

## API Testing with Swagger

### 1. Start the server
```bash
cd /workspace
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access Swagger UI
Open: http://localhost:8000/docs

### 3. Login with testadmin
- Endpoint: `POST /auth/login`
- Body:
  ```json
  {
    "email": "testadmin@example.com",
    "password": "TestAdmin123"
  }
  ```
- Copy the `access_token` from response

### 4. Authorize
- Click "Authorize" button (🔒 icon)
- Paste token in format: `Bearer YOUR_ACCESS_TOKEN`
- Click "Authorize"

### 5. Test AI Assistant
- Endpoint: `POST /assistant/query`
- Body:
  ```json
  {
    "query": "What is grace according to my sermon notes?"
  }
  ```

## What Changed?

All 9 test scripts now:
- ✅ Use `testadmin@example.com` instead of `test@scribes.local`
- ✅ Dynamically look up user ID instead of hardcoding `user_id = 7`
- ✅ Use parameterized SQL queries (`:user_id`)
- ✅ Show helpful error messages pointing to `bootstrap_admin.py`

## Verification Output

When you run `verify_test_data.py`, you should see:

```
✅ PASS: Test user found
   Username: testadmin
   Email: testadmin@example.com
   User ID: 1

✅ PASS: 5 notes found
✅ PASS: No duplicates found (10 chunks)
✅ PASS: All chunks have embeddings
✅ PASS: Embedding dimensions correct (384)
✅ PASS: Retrieved 5 chunks for relevance test

✅ ALL CHECKS PASSED - TEST DATA IS READY!
```

## Troubleshooting

### If testadmin doesn't exist:
```bash
python scripts/admin/bootstrap_admin.py testadmin@example.com TestAdmin123
```

### If no test data exists:
```bash
PYTHONPATH=/workspace python scripts/testing/create_test_data.py
```

### If data is corrupted:
```bash
# Cleanup and recreate
PYTHONPATH=/workspace python scripts/testing/cleanup_test_chunks.py
PYTHONPATH=/workspace python scripts/testing/create_test_data.py
```

### If imports fail:
Always use `PYTHONPATH=/workspace` when running scripts:
```bash
PYTHONPATH=/workspace python scripts/testing/[script_name].py
```

## Current Test Data

When you run `create_test_data.py`, it creates:
- **5 theological notes** with real sermon content:
  1. Understanding God's Grace
  2. The Power of Faith
  3. God's Unfailing Love
  4. The Practice of Prayer
  5. Walking in the Spirit
  
- **10 chunks** (2 per note)
- **10 embeddings** (384-dimensional vectors)
- All data owned by **testadmin** user

---

**Ready to test!** 🚀
