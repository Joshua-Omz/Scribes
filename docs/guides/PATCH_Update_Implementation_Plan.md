# PATCH Update Implementation Plan
## Transition from PUT to PATCH for Note Updates

**Date:** November 7, 2025  
**Status:** Planning Phase  
**Reference:** `docs/suggestedUpdateformatImplementation.md`

---

## 📋 Executive Summary

This plan outlines the transition from the current `PUT /notes/{id}` endpoint to a proper `PATCH /v1/notes/{id}` implementation that supports:
- Partial updates (already partially implemented)
- Extended schema fields (series, venue, event, dateTime, topics)
- Offline-first sync with conflict resolution
- Version history tracking
- Background job triggers for embeddings and related services

---

## 🔍 Current State Analysis

### Existing Implementation

**Endpoint:** `PUT /notes/{note_id}`
- **Location:** `app/api/note_routes.py` (lines 111-133)
- **Service:** `app/services/note_service.py::update_note()` (lines 169-228)
- **Schema:** `app/schemas/note_schemas.py::NoteUpdate` (lines 62-107)

**Current Features:**
✅ Partial updates via `exclude_unset=True`  
✅ Ownership verification  
✅ Auto-embedding regeneration on content changes  
✅ Field validation (non-empty title/content)  
❌ No version history  
❌ No conflict resolution  
❌ Limited schema (missing series, venue, event, dateTime, topics)  
❌ No background job queue  
❌ Uses PUT instead of PATCH (wrong HTTP semantics)

### Current Schema Coverage

**Existing Fields:**
- `title` (String, required in create, optional in update)
- `content` (Text, required in create, optional in update)
- `preacher` (String, optional)
- `tags` (String, comma-separated, optional)
- `scripture_refs` (String, optional)
- `embedding` (Vector, auto-generated)

**Missing Fields (from proposal):**
- `series` (String) - sermon series name
- `venue` (String) - location/church name
- `event` (String) - special event name
- `dateTime` (DateTime) - sermon date/time
- `topics` (List[str]) - structured topic tags
- `scriptureTags` (List[ScriptureTag]) - structured scripture references

---

## 🎯 Implementation Phases

### Phase 1: Schema Enhancement ⏱️ Est: 2-3 hours

**Goal:** Extend Note model and schemas with missing fields

**Tasks:**

#### 1.1 Update Note Model
**File:** `app/models/note_model.py`

```python
# Add new columns
series = Column(String(100), nullable=True)
venue = Column(String(200), nullable=True)
event = Column(String(200), nullable=True)
date_time = Column(DateTime(timezone=True), nullable=True)
topics = Column(Text, nullable=True)  # JSON array stored as text
version = Column(Integer, default=1, nullable=False)  # For optimistic locking
```

**Rationale:**
- `series`, `venue`, `event`: Optional metadata fields for better organization
- `date_time`: Enables time-based sorting and reminder triggers
- `topics`: Structured alternative to comma-separated tags
- `version`: Optimistic locking for conflict detection

#### 1.2 Create Scripture Tag Schema
**File:** `app/schemas/note_schemas.py`

```python
class ScriptureTagSchema(BaseModel):
    """Structured scripture reference."""
    book: str = Field(..., description="Bible book name", examples=["John"])
    chapter: int = Field(..., ge=1, description="Chapter number")
    verse_start: int = Field(..., ge=1, description="Starting verse")
    verse_end: Optional[int] = Field(None, ge=1, description="Ending verse (if range)")
    translation: Optional[str] = Field("NIV", description="Bible translation")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"book": "John", "chapter": 3, "verse_start": 16, "translation": "NIV"},
                {"book": "Romans", "chapter": 8, "verse_start": 28, "verse_end": 39, "translation": "ESV"}
            ]
        }
    )
```

#### 1.3 Update NoteUpdate Schema
**File:** `app/schemas/note_schemas.py`

```python
class NoteUpdate(BaseSchema):
    """Schema for updating a note (PATCH semantics - all fields optional)."""
    
    # Existing fields
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    preacher: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=255)
    scripture_refs: Optional[str] = Field(None, max_length=255)
    
    # New fields
    series: Optional[str] = Field(None, max_length=100, description="Sermon series name")
    venue: Optional[str] = Field(None, max_length=200, description="Church/venue name")
    event: Optional[str] = Field(None, max_length=200, description="Special event name")
    date_time: Optional[datetime] = Field(None, description="Sermon date and time")
    topics: Optional[List[str]] = Field(None, description="Structured topic tags")
    scripture_tags: Optional[List[ScriptureTagSchema]] = Field(None, description="Structured scripture references")
    
    # Version for optimistic locking
    version: Optional[int] = Field(None, description="Expected version number for conflict detection")
```

#### 1.4 Create Migration
**File:** `alembic/versions/004_add_note_extended_fields.py`

```python
def upgrade() -> None:
    op.add_column('notes', sa.Column('series', sa.String(100), nullable=True))
    op.add_column('notes', sa.Column('venue', sa.String(200), nullable=True))
    op.add_column('notes', sa.Column('event', sa.String(200), nullable=True))
    op.add_column('notes', sa.Column('date_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('notes', sa.Column('topics', sa.Text(), nullable=True))
    op.add_column('notes', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Create index on date_time for time-based queries
    op.create_index('ix_notes_date_time', 'notes', ['date_time'])
```

---

### Phase 2: Endpoint Transition ⏱️ Est: 1-2 hours

**Goal:** Change from PUT to PATCH with proper semantics

#### 2.1 Update Route Decorator
**File:** `app/api/note_routes.py`

**Current:**
```python
@router.put("/{note_id}", ...)
```

**New:**
```python
@router.patch("/{note_id}", ...)  # or "/v1/notes/{note_id}" for versioning
```

#### 2.2 Update Documentation
```python
@router.patch(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Partially update a note",
    description="Update specific fields of an existing note. Only provided fields will be modified."
)
async def update_note(...):
    """
    Partially update a note (PATCH semantics).
    
    - Supports offline-first sync
    - Only updates provided fields
    - Triggers background jobs for embeddings/reminders
    - Includes conflict detection via version number
    """
```

**Rationale:**
- PATCH is semantically correct for partial updates
- PUT should be reserved for full resource replacement
- Improves API clarity and REST compliance

---

### Phase 3: Enhanced Update Logic ⏱️ Est: 3-4 hours

**Goal:** Add version history, conflict resolution, and side effects

#### 3.1 Create Version History Model
**File:** `app/models/note_version_model.py`

```python
class NoteVersion(Base):
    __tablename__ = "note_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Track what changed
    changed_fields = Column(Text, nullable=False)  # JSON array of field names
    old_values = Column(Text, nullable=True)  # JSON object of old values
    new_values = Column(Text, nullable=True)  # JSON object of new values
    
    # Metadata
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    note = relationship("Note", backref="versions")
    user = relationship("User")
    
    __table_args__ = (
        Index('ix_note_versions_note_version', 'note_id', 'version_number', unique=True),
    )
```

#### 3.2 Enhanced Update Service
**File:** `app/services/note_service.py`

```python
async def update_note(
    self, 
    note_id: int, 
    note_data: NoteUpdate, 
    user_id: int
) -> Note:
    """
    Update a note with version history and conflict resolution.
    """
    # 1. Get existing note
    existing_note = await self.get_note(note_id, user_id)
    
    # 2. Optimistic locking - check version
    if note_data.version is not None:
        if existing_note.version != note_data.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Version conflict detected",
                    "expected_version": note_data.version,
                    "current_version": existing_note.version,
                    "message": "The note was modified by another client. Please refresh and try again."
                }
            )
    
    # 3. Extract update data
    update_dict = note_data.model_dump(exclude_unset=True, exclude={'version'})
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # 4. Validate fields
    if "title" in update_dict and not update_dict["title"].strip():
        raise HTTPException(400, "Title cannot be empty")
    if "content" in update_dict and not update_dict["content"].strip():
        raise HTTPException(400, "Content cannot be empty")
    
    # 5. Store old values for version history
    old_values = {field: getattr(existing_note, field) for field in update_dict.keys()}
    
    # 6. Apply updates
    updated_note = await self.note_repo.update(note_id, note_data)
    
    # 7. Increment version
    updated_note.version += 1
    
    # 8. Save version history
    await self._save_version_history(
        note_id=note_id,
        version_number=updated_note.version,
        changed_fields=list(update_dict.keys()),
        old_values=old_values,
        new_values=update_dict,
        user_id=user_id
    )
    
    # 9. Trigger side effects
    await self._trigger_update_side_effects(updated_note, update_dict)
    
    await self.db.commit()
    
    return updated_note
```

#### 3.3 Side Effects Handler
```python
async def _trigger_update_side_effects(self, note: Note, changed_fields: dict):
    """Trigger background jobs based on what changed."""
    
    # Embedding refresh for content changes
    content_fields = {'title', 'content', 'preacher', 'scripture_refs', 'tags', 'topics', 'scripture_tags'}
    if any(field in changed_fields for field in content_fields):
        await self._generate_embedding(note)
        # TODO: Enqueue background job for cross-ref reindexing
        # enqueue_crossref_reindex(note.id)
    
    # Reminder rescheduling if date/time changed
    if 'date_time' in changed_fields or 'tags' in changed_fields:
        # TODO: Enqueue reminder recalculation job
        # enqueue_reminder_update(note.id)
        pass
    
    # Cross-reference update for scripture changes
    if 'scripture_refs' in changed_fields or 'scripture_tags' in changed_fields:
        # TODO: Trigger cross-ref suggestions
        # enqueue_crossref_suggestions(note.id)
        pass
```

#### 3.4 Version History Helper
```python
async def _save_version_history(
    self,
    note_id: int,
    version_number: int,
    changed_fields: List[str],
    old_values: dict,
    new_values: dict,
    user_id: int
):
    """Save a version history entry."""
    import json
    
    version_entry = NoteVersion(
        note_id=note_id,
        version_number=version_number,
        changed_fields=json.dumps(changed_fields),
        old_values=json.dumps(old_values, default=str),  # default=str handles datetime
        new_values=json.dumps(new_values, default=str),
        changed_by=user_id
    )
    
    self.db.add(version_entry)
```

---

### Phase 4: Background Job Infrastructure ⏱️ Est: 4-6 hours

**Goal:** Set up async task queue for long-running operations

#### 4.1 Install Dependencies
```bash
pip install celery redis
```

**Update:** `requirements.txt`
```
celery==5.3.1
redis==4.6.0
```

#### 4.2 Create Celery App
**File:** `app/core/celery_app.py`

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "scribes",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

celery_app.autodiscover_tasks(['app.tasks'])
```

#### 4.3 Create Task Definitions
**File:** `app/tasks/note_tasks.py`

```python
from app.core.celery_app import celery_app
from app.core.database import get_async_session
from app.services.embedding_service import get_embedding_service
from app.repositories.note_repository import NoteRepository
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def enqueue_embedding_update(self, note_id: int):
    """Background task to regenerate note embedding."""
    try:
        # Run async task in sync context
        import asyncio
        asyncio.run(_update_embedding_async(note_id))
    except Exception as e:
        logger.error(f"Embedding update failed for note {note_id}: {e}")
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute

async def _update_embedding_async(note_id: int):
    """Async helper to update embedding."""
    async with get_async_session() as db:
        repo = NoteRepository(db)
        note = await repo.get_by_id(note_id)
        
        if note:
            embedding_service = get_embedding_service()
            text = embedding_service.combine_text_for_embedding(
                title=note.title,
                content=note.content,
                preacher=note.preacher,
                scripture_refs=note.scripture_refs,
                tags=note.tags
            )
            embedding = embedding_service.generate(text)
            note.embedding = embedding
            await db.commit()

@celery_app.task
def enqueue_reminder_update(note_id: int):
    """Background task to recalculate reminders."""
    # TODO: Implement reminder logic
    pass

@celery_app.task
def enqueue_crossref_reindex(note_id: int):
    """Background task to update cross-references."""
    # TODO: Implement cross-ref logic
    pass
```

#### 4.4 Update Config
**File:** `app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
```

#### 4.5 Start Celery Worker
**File:** `start_celery.ps1`

```powershell
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

---

### Phase 5: Testing & Documentation ⏱️ Est: 3-4 hours

#### 5.1 Create Tests
**File:** `app/tests/test_note_update_patch.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_patch_partial_update(async_client: AsyncClient, auth_headers):
    """Test PATCH with only title update."""
    # Create note
    create_response = await async_client.post(
        "/notes/",
        json={"title": "Original", "content": "Original content"},
        headers=auth_headers
    )
    note_id = create_response.json()["id"]
    
    # Patch only title
    patch_response = await async_client.patch(
        f"/notes/{note_id}",
        json={"title": "Updated Title"},
        headers=auth_headers
    )
    
    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Original content"  # Unchanged

@pytest.mark.asyncio
async def test_version_conflict_detection(async_client: AsyncClient, auth_headers):
    """Test optimistic locking prevents concurrent updates."""
    # Create note
    create_response = await async_client.post(
        "/notes/",
        json={"title": "Test", "content": "Content"},
        headers=auth_headers
    )
    note_id = create_response.json()["id"]
    version = create_response.json()["version"]
    
    # First update succeeds
    update1 = await async_client.patch(
        f"/notes/{note_id}",
        json={"title": "Update 1", "version": version},
        headers=auth_headers
    )
    assert update1.status_code == 200
    
    # Second update with stale version fails
    update2 = await async_client.patch(
        f"/notes/{note_id}",
        json={"title": "Update 2", "version": version},  # Stale version
        headers=auth_headers
    )
    assert update2.status_code == 409  # Conflict

@pytest.mark.asyncio
async def test_side_effects_triggered(async_client: AsyncClient, auth_headers, mocker):
    """Test that content changes trigger embedding update."""
    mock_embedding = mocker.patch('app.tasks.note_tasks.enqueue_embedding_update.delay')
    
    # Create and update note
    create_response = await async_client.post(
        "/notes/",
        json={"title": "Test", "content": "Content"},
        headers=auth_headers
    )
    note_id = create_response.json()["id"]
    
    await async_client.patch(
        f"/notes/{note_id}",
        json={"content": "New content"},
        headers=auth_headers
    )
    
    # Verify embedding task was queued
    mock_embedding.assert_called_once_with(note_id)
```

#### 5.2 Update API Documentation
**File:** `docs/api/NOTE_UPDATE_API.md`

```markdown
# Note Update API (PATCH)

## Endpoint
`PATCH /notes/{note_id}`

## Description
Partially update an existing note. Only provided fields will be modified.

## Request Body
All fields are optional. Provide only the fields you want to update.

```json
{
  "title": "Updated Title",
  "content": "Updated content...",
  "series": "Faith Series",
  "venue": "Main Church",
  "date_time": "2025-11-10T10:00:00Z",
  "topics": ["faith", "grace"],
  "scripture_tags": [
    {"book": "John", "chapter": 3, "verse_start": 16}
  ],
  "version": 5  // Optional: for conflict detection
}
```

## Response
Returns the updated note with incremented version number.

## Conflict Resolution
If `version` is provided and doesn't match current version, returns 409 Conflict:

```json
{
  "error": "Version conflict detected",
  "expected_version": 5,
  "current_version": 6,
  "message": "The note was modified by another client..."
}
```

## Side Effects
Updates trigger background jobs:
- **Content changes** → Embedding regeneration, cross-ref reindexing
- **DateTime changes** → Reminder recalculation
- **All changes** → Version history entry created
```

---

## 🚦 Migration Strategy

### Option A: Big Bang Migration (Recommended for Low Traffic)
1. Deploy all changes at once during maintenance window
2. Run database migrations
3. Update API clients to use PATCH
4. Monitor for issues

### Option B: Gradual Migration (Recommended for Production)
1. **Week 1:** Deploy model changes + migration (backward compatible)
2. **Week 2:** Add PATCH endpoint alongside existing PUT
3. **Week 3:** Update clients to use PATCH, monitor both endpoints
4. **Week 4:** Deprecate PUT endpoint
5. **Week 5:** Remove PUT endpoint

---

## ✅ Validation Checklist

Before deploying to production:

- [ ] All migrations tested on staging database
- [ ] Version history working correctly
- [ ] Conflict detection prevents data loss
- [ ] Background jobs processing successfully
- [ ] Redis/Celery running and monitored
- [ ] API documentation updated
- [ ] Client SDKs updated (Flutter app)
- [ ] Rollback plan documented
- [ ] Performance testing completed
- [ ] Error handling tested (network failures, timeouts)

---

## 📊 Success Metrics

**Technical Metrics:**
- [ ] <100ms p50 response time for PATCH endpoint
- [ ] <500ms p99 response time
- [ ] >99.9% success rate
- [ ] Background job completion >95% within 5 minutes

**Business Metrics:**
- [ ] Zero data loss incidents
- [ ] Sync conflicts <1% of updates
- [ ] User-reported bugs <5 per 1000 updates

---

## 🔄 Rollback Plan

If critical issues arise:

1. **Immediate:** Switch API gateway to route PATCH→PUT temporarily
2. **Database:** Alembic downgrade to previous version
3. **Code:** Revert to previous deployment
4. **Monitoring:** Check for orphaned background jobs
5. **Communication:** Notify users of temporary service degradation

**Rollback Time:** Estimated 15-30 minutes

---

## 📝 Implementation Timeline

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Schema | 2-3 hrs | High | None |
| Phase 2: Endpoint | 1-2 hrs | High | Phase 1 |
| Phase 3: Enhanced Logic | 3-4 hrs | High | Phases 1-2 |
| Phase 4: Background Jobs | 4-6 hrs | Medium | Phase 3 |
| Phase 5: Testing | 3-4 hrs | High | All phases |
| **Total** | **13-19 hrs** | | |

**Recommended Sprint:** 2-3 days with dedicated developer

---

## 🎓 Key Learnings from Current Implementation

**What's Working Well:**
✅ `exclude_unset=True` enables proper partial updates  
✅ Ownership verification prevents unauthorized access  
✅ Embedding regeneration keeps search index fresh  
✅ Field validation prevents data corruption

**What Needs Improvement:**
❌ PUT vs PATCH semantics confusion  
❌ No version history for auditing/rollback  
❌ No conflict detection for concurrent edits  
❌ Limited schema fields  
❌ Synchronous embedding generation blocks response

---

## 🔗 Related Documentation

- [Semantic Embeddings Implementation](./Semantic_Embeddings_Implementation.md)
- [Flutter Notes Implementation](./Flutter_Notes_Implementation.md)
- [Database Schema Guide](../database/SCHEMA.md)
- [API Versioning Strategy](../api/VERSIONING.md)

---

## 👥 Stakeholder Sign-off

- [ ] Backend Lead - Schema changes approved
- [ ] Mobile Lead - API changes compatible with Flutter app
- [ ] DevOps - Infrastructure ready (Redis, Celery)
- [ ] QA Lead - Test plan reviewed
- [ ] Product Owner - Feature prioritization confirmed

---

**Next Steps:**
1. Review this plan with team
2. Set up development environment with Redis
3. Begin Phase 1 implementation
4. Schedule code review checkpoints
5. Plan staging deployment
