# PATCH Update Implementation - Quick Reference

## 📌 TL;DR

Transitioning from `PUT /notes/{id}` to `PATCH /notes/{id}` with enhanced features:
- ✅ Proper PATCH semantics (already using `exclude_unset=True`)
- ✅ Extended schema (series, venue, event, dateTime, topics, scripture_tags)
- ✅ Version history tracking (audit trail + rollback capability)
- ✅ Conflict detection (optimistic locking)
- ✅ Background jobs (embedding refresh, reminder updates, cross-ref reindexing)

**Total Effort:** 13-19 hours (2-3 days)  
**Risk Level:** Medium (requires database migration + background job infrastructure)  
**Impact:** High (enables offline-first sync, better UX, audit compliance)

---

## 🎯 What Changes

### API Layer
```diff
- @router.put("/{note_id}")
+ @router.patch("/{note_id}")

# Request body (all optional)
{
  "title": "string",           # existing
  "content": "string",          # existing
  "preacher": "string",         # existing
  "tags": "string",             # existing
  "scripture_refs": "string",   # existing
+ "series": "string",           # NEW
+ "venue": "string",            # NEW
+ "event": "string",            # NEW
+ "date_time": "2025-11-10T10:00:00Z",  # NEW
+ "topics": ["faith", "hope"],  # NEW
+ "scripture_tags": [           # NEW
+   {"book": "John", "chapter": 3, "verse_start": 16}
+ ],
+ "version": 5                  # NEW (for conflict detection)
}
```

### Database Schema
```sql
-- Add to notes table
ALTER TABLE notes ADD COLUMN series VARCHAR(100);
ALTER TABLE notes ADD COLUMN venue VARCHAR(200);
ALTER TABLE notes ADD COLUMN event VARCHAR(200);
ALTER TABLE notes ADD COLUMN date_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE notes ADD COLUMN topics TEXT;
ALTER TABLE notes ADD COLUMN version INTEGER DEFAULT 1 NOT NULL;

-- New table for version history
CREATE TABLE note_versions (
    id SERIAL PRIMARY KEY,
    note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    changed_fields TEXT NOT NULL,
    old_values TEXT,
    new_values TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changed_by INTEGER REFERENCES users(id),
    UNIQUE(note_id, version_number)
);
```

### Service Layer
```python
# Enhanced update logic
async def update_note(...):
    # 1. Check version for conflicts (optimistic locking)
    if note_data.version and existing.version != note_data.version:
        raise HTTPException(409, "Version conflict")
    
    # 2. Save version history
    await save_version_history(old_values, new_values)
    
    # 3. Increment version
    note.version += 1
    
    # 4. Trigger background jobs
    if content_changed:
        enqueue_embedding_update.delay(note_id)
    if datetime_changed:
        enqueue_reminder_update.delay(note_id)
```

---

## 🚀 5-Phase Implementation

| Phase | What | Time | Files Changed |
|-------|------|------|---------------|
| **1. Schema** | Add model fields + migration | 2-3h | `note_model.py`, `note_schemas.py`, `alembic/versions/004_*.py` |
| **2. Endpoint** | Change PUT→PATCH | 1-2h | `note_routes.py` |
| **3. Logic** | Version history + conflicts | 3-4h | `note_service.py`, `note_version_model.py` |
| **4. Jobs** | Celery + Redis setup | 4-6h | `celery_app.py`, `note_tasks.py`, `requirements.txt` |
| **5. Tests** | Unit + integration tests | 3-4h | `test_note_update_patch.py`, API docs |

---

## ⚠️ Critical Decisions Needed

### 1. API Versioning Strategy
**Decision:** Should we version the API path?

**Option A:** Keep current path
```
PATCH /notes/{id}
```
✅ Simpler migration  
❌ Breaking change for existing clients

**Option B:** Add version prefix
```
PATCH /v1/notes/{id}
```
✅ Non-breaking (PUT still works on old path)  
✅ Future-proof for v2 changes  
❌ More complex routing

**Recommendation:** Option B if you have existing mobile apps in production

### 2. Background Job Priority
**Decision:** Which background jobs are MVP?

**Must Have (Phase 4a):**
- ✅ Embedding regeneration (already exists)

**Nice to Have (Phase 4b):**
- ⚠️ Reminder rescheduling (if reminders feature exists)
- ⚠️ Cross-ref reindexing (if cross-refs use embeddings)

**Recommendation:** Start with embeddings only, add others incrementally

### 3. Migration Strategy
**Decision:** Big bang or gradual?

**Option A: Big Bang** (deploy everything at once)
- ✅ Faster completion
- ❌ Higher risk
- Best for: Low traffic apps, staging-first deployments

**Option B: Gradual** (4-week rollout)
- Week 1: Database changes only
- Week 2: Add PATCH alongside PUT
- Week 3: Migrate clients to PATCH
- Week 4: Deprecate PUT
- ✅ Lower risk
- ❌ Slower completion
- Best for: Production apps with active users

**Recommendation:** Option A for MVP, Option B for production

---

## 📦 New Dependencies

```txt
# requirements.txt additions
celery==5.3.1
redis==4.6.0
```

**Infrastructure needs:**
- Redis server (local or cloud)
- Celery worker process

**Local dev setup:**
```bash
# Install Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis

# Start Redis
redis-server

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

---

## 🧪 Testing Checklist

**Before merging:**
- [ ] Unit tests for version conflict detection
- [ ] Integration test for partial updates
- [ ] Test background job execution
- [ ] Test migration on copy of production DB
- [ ] Load test PATCH endpoint (simulate 100 concurrent updates)
- [ ] Test rollback procedure

**After deploying:**
- [ ] Monitor Redis queue depth
- [ ] Monitor Celery worker health
- [ ] Check version_history table growth rate
- [ ] Verify no 409 Conflict false positives
- [ ] Confirm embedding jobs completing <5 minutes

---

## 🔥 Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Version conflicts overused | Medium | High | Set version optional, use only for critical updates |
| Redis outage breaks updates | Low | High | Make background jobs optional, degrade gracefully |
| Migration data loss | Low | Critical | Test on staging, backup before migration |
| Performance degradation | Medium | Medium | Add indexes on new columns, monitor query times |
| Celery worker crashes | Medium | Low | Use supervisor/systemd for auto-restart |

---

## 💡 Quick Wins (Do These First)

If time is limited, implement in this order:

**MVP (4-6 hours):**
1. Change PUT → PATCH (1h)
2. Add `series`, `venue`, `event` fields (2h)
3. Basic migration (1h)
4. Update tests (1h)

**Phase 2 (3-4 hours):**
5. Add `version` field for conflicts (2h)
6. Add version history model (2h)

**Phase 3 (4-6 hours):**
7. Set up Celery + Redis (3h)
8. Move embedding generation to background (2h)

**Nice-to-Have:**
9. Add `date_time` and reminder integration
10. Add structured `topics` and `scripture_tags`

---

## 📞 Who to Consult

**Before starting:**
- [ ] Product Owner - Confirm new fields align with roadmap
- [ ] Mobile Team - Ensure Flutter app can handle new schema
- [ ] DevOps - Verify Redis infrastructure available

**During development:**
- [ ] Backend Lead - Review version history schema
- [ ] QA Lead - Coordinate test plan

**Before deployment:**
- [ ] DBA - Review migration plan
- [ ] DevOps - Coordinate Celery worker deployment

---

## 🎬 Next Actions

1. **Review this plan** with team (30 min meeting)
2. **Make decisions** on versioning and migration strategy
3. **Set up local Redis** for development
4. **Create feature branch** `feature/patch-update-endpoint`
5. **Start with Phase 1** (schema changes)
6. **Daily standups** to track progress
7. **Code review** after each phase
8. **Deploy to staging** after Phase 5
9. **Production deployment** (coordinated with mobile team)

---

## 📚 Full Documentation

See: `docs/guides/PATCH_Update_Implementation_Plan.md` for complete details

**Questions?** Contact: Backend Team Lead
