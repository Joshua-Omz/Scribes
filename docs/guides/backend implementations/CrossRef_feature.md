# 🔗 CrossRef Feature Construction Guide (Phase 5)

This document outlines the design, implementation, and testing plan for the **CrossRef (Cross Reference)** feature in the Scribes backend. The CrossRef system enables automatic linking of related notes based on shared scriptures, keywords, or semantic similarity — enhancing the user's ability to study and connect messages over time.

---

## 1. Overview

### Purpose

The CrossRef feature identifies relationships between notes by analyzing:

* Shared **scriptural references** (e.g., both notes mention *John 3:16*)
* Shared **tags** or **topics**
* Semantic similarity (AI-driven in future phases)

### Key Benefits

* Helps users see how different sermons or studies connect.
* Provides a visual and spiritual knowledge network across notes.
* Supports spiritual reflection by revealing recurring divine themes.

---

## 2. Architecture Overview

### Core Components

* **CrossRef Model** — Stores links between related notes.
* **CrossRef Repository** — Handles database operations for relationships.
* **CrossRef Service** — Core logic for building, updating, and retrieving references.
* **CrossRef Routes** — API endpoints for building and fetching relationships.
* **CrossRef Worker** — Background task to asynchronously compute and update relationships.

### Data Flow

```
User adds or updates a note → CrossRef Service → Match engine finds related notes →
CrossRef entries are saved → Frontend retrieves via /crossref/{note_id}/stats or /crossref/{note_id}/related
```

---

## 3. Database Design

### 3.1 CrossRef Table

```python
class CrossRef(Base):
    __tablename__ = "crossrefs"

    id = Column(Integer, primary_key=True, index=True)
    source_note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    target_note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    match_type = Column(String(50), nullable=False)  # 'scripture', 'tag', 'semantic'
    confidence = Column(Float, nullable=True)        # relevance score (0.0–1.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 3.2 Relationships

* Each note can have many related notes.
* Cascade delete ensures integrity when a note is removed.
* `confidence` field supports future AI-based scoring.

---

## 4. Repository Layer (`app/db/repositories/crossref_repository.py`)

### Functions

* `create_crossref()` – Create or update a relationship.
* `get_related_notes(note_id)` – Retrieve all related notes.
* `get_crossref_stats(note_id)` – Count relationships by match type.
* `delete_crossrefs_by_note_id(note_id)` – Cleanup when a note is deleted.

---

## 5. Service Layer (`app/services/crossref_service.py`)

### 5.1 Core Logic

The service layer performs matching operations in phases:

#### a. Scripture Matching

* Parse scripture tags from a note (e.g., “John 3:16”).
* Compare with scripture tags in all other notes.
* Create crossrefs where matches exist.

#### b. Tag Matching

* Compare `tags` fields (comma-separated values).
* Create tag-based relationships.

#### c. Semantic Matching (AI Slot)

* **Future AI integration point**: send note content to an AI embedding model (e.g., OpenAI Embeddings or Sentence Transformers) and compute similarity.
* Store the confidence score in `confidence`.

### 5.2 Methods

* `build_crossrefs_for_note()` – Called when a note is created or updated.
* `get_crossref_stats()` – Returns stats grouped by type.
* `get_related_notes()` – Returns a detailed list of related notes with metadata.

---

## 6. Routes (`app/routes/crossref_routes.py`)

### Endpoints

#### 1️⃣ Build CrossRefs for a Note

```
POST /api/crossref/{note_id}/build
```

**Response:**

```json
{
  "message": "Cross-references built successfully",
  "note_id": 12,
  "count": 4
}
```

#### 2️⃣ Retrieve CrossRef Stats

```
GET /api/crossref/{note_id}/stats
```

**Response:**

```json
{
  "note_id": 12,
  "counts": { "scripture": 3, "tag": 1, "semantic": 0 }
}
```

#### 3️⃣ Fetch Related Notes

```
GET /api/crossref/{note_id}/related
```

**Response:**

```json
[
  {
    "target_note_id": 14,
    "title": "Faith and Endurance",
    "match_type": "scripture",
    "confidence": null
  }
]
```

---

## 7. Testing Strategy

### Unit Tests

* Verify scripture matching logic.
* Verify tag-based relationships.
* Test cascade delete when a note is removed.

### Integration Tests

* Test end-to-end `/crossref/{note_id}/build` and `/crossref/{note_id}/stats` routes.

### Mock AI Tests (Future)

* Use mock embeddings to test semantic similarity flow.

---

## 8. AI Integration Slot (Future Expansion)

### Phase 2 AI Integration Plan

* Use **vector embeddings** to represent note content semantically.
* Store embeddings in PostgreSQL with `pgvector`.
* During CrossRef build:

  * Compute vector similarity between note embeddings.
  * Create CrossRefs for semantically similar notes (confidence > threshold).

**Tech Stack (Planned):**

* `sentence-transformers` for local inference or OpenAI API for embeddings.
* `pgvector` PostgreSQL extension for similarity search.

---

## 9. UI & UX Implications

### CrossRef Display Ideas

* Related notes section at the bottom of each note: *“You might also want to revisit…”*
* Color-coded relationship types: scripture (blue), tag (green), semantic (gold).
* Stats widget: show the number of related notes by type.

**Example:**

```
📖 3 related notes — 2 scripture | 1 tag
```

---

## 10. Definition of Done (Phase 5)

✅ CrossRef table created & migration applied
✅ Endpoints operational: build, stats, related
✅ Scripture + Tag matching functional
✅ Tested and verified via Swagger UI
✅ Placeholder slot for AI semantic engine
✅ Documentation finalized for backend–frontend integration

---

### 🧭 Next Steps (After CrossRef)

* Implement **semantic embeddings service** (AI phase)
* Build **frontend display for related notes**
* Integrate **CrossRef rebuild triggers** on note updates/deletions
