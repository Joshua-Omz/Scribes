Joshua — based on the finalized Scribes SRS, here’s the **most effective and scalable way to implement the PUT (update) endpoint** for notes.

### ✅ 1. **Use `PATCH /v1/notes/:id` (not `PUT`)**

The SRS explicitly lists:

```
PATCH /v1/notes/:id  {content, fields}
```

So the update method should follow **partial update semantics**, not full replacement.
Reason: users may edit small fragments (like content or tags) while offline, and a full overwrite risks sync conflicts.

---

### 🧩 2. **Update Flow (FastAPI Implementation Blueprint)**

**Endpoint:**

```python
@router.patch("/v1/notes/{note_id}")
async def update_note(
    note_id: UUID,
    payload: NoteUpdateSchema,
    user: User = Depends(current_user)
):
    existing = await Note.get(note_id, user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")

    # Apply only changed fields
    updated_data = payload.dict(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(existing, key, value)

    existing.updated_at = datetime.utcnow()
    await existing.save()

    # Trigger background embedding/sync job if content or tags changed
    if any(k in updated_data for k in ["content", "tags", "topics"]):
        enqueue_embedding_update(note_id)

    return existing
```

---

### ⚙️ 3. **Schema Design**

```python
class NoteUpdateSchema(BaseModel):
    title: Optional[str]
    content: Optional[str]
    preacher: Optional[str]
    series: Optional[str]
    venue: Optional[str]
    event: Optional[str]
    dateTime: Optional[datetime]
    tags: Optional[List[str]]
    topics: Optional[List[str]]
    scriptureTags: Optional[List[ScriptureTagSchema]]
```

Use `exclude_unset=True` so only provided fields are updated.

---

### 🔄 4. **Offline Sync & Conflict Resolution**

Follow the spec’s FR-4: *“last-writer-wins + diff merge when possible.”*
That means:

* If both local and remote versions differ, compare timestamps.
* If newer local version exists, push it.
* If conflict (same timestamp), run a **diff merge service** (e.g. unified diff at paragraph level).

---

### 🧠 5. **Trigger Side Services**

Whenever the note is updated:

* **Embeddings refresh** (for search & cross-refs)
* **Version history** update (FR-3)
* **Reminder rescheduling** (if dateTime or tags change)

---

### 💡 6. **Summary**

| Concern     | Approach                                           |
| ----------- | -------------------------------------------------- |
| Update type | `PATCH` (partial updates)                          |
| Sync model  | Offline-first, conflict-aware                      |
| Triggers    | Background reindex + version logging               |
| Security    | JWT + ownership check                              |
| Performance | Redis caching; PgVector embedding refresh deferred |

---

Think of it like this:

> **“PATCH is a scalpel, PUT is a bulldozer.”**
> Since Scribes syncs small fragments and maintains version history, you want precision updates — not full replacements.

