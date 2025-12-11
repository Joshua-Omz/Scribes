# 🧠 Phase 5: Semantic Embeddings Service Construction Guide

## 1. Overview

The **Semantic Embeddings Service** is the foundation for intelligent features in **Scribes**. It enables meaning-based (semantic) relationships between notes, empowering features such as:

* Semantic search (find notes by meaning, not just keywords)
* Cross-reference generation
* The future "AI Growth Guide" and thematic clustering

This service transforms sermon notes into high-dimensional vectors stored in the database using **PgVector**, allowing efficient cosine similarity searches.

---

## 2. Architecture

| Layer             | Responsibility                               | Components             |
| ----------------- | -------------------------------------------- | ---------------------- |
| **Model Layer**   | Stores note vectors                          | PostgreSQL + PgVector  |
| **Service Layer** | Generates embeddings and computes similarity | `EmbeddingService`     |
| **Worker Layer**  | Handles background embedding generation      | Celery/RQ (future)     |
| **API Layer**     | Exposes search endpoints                     | `/api/semantic/search` |

---

## 3. Database Setup

### 3.1 Add Embedding Column

Use Alembic to create a new migration:

```bash
alembic revision -m "add embedding column to notes"
```

Edit the migration file:

```python
def upgrade():
    op.add_column('notes', sa.Column('embedding', sa.dialects.postgresql.ARRAY(sa.Float), nullable=True))
```

> **Optionally**, if PgVector is installed:

```python
def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    op.add_column('notes', sa.Column('embedding', sa.dialects.postgresql.VECTOR(1536)))
    op.execute('CREATE INDEX IF NOT EXISTS idx_notes_embedding ON notes USING ivfflat (embedding vector_cosine_ops);')
```

---

## 4. Service Layer

Create: `app/services/embedding_service.py`

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate(self, text: str) -> list[float]:
        if not text.strip():
            return []
        return self.model.encode(text).tolist()

    def similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
```

---

## 5. Integration with Notes

In `app/services/note_service.py`, hook into note creation and updates:

```python
from app.services.embedding_service import EmbeddingService

def create_note_service(db, note_data, user_id):
    note = note_repository.create_note(db, note_data, user_id)
    emb = EmbeddingService()
    note.embedding = emb.generate(note.content)
    db.commit()
    return note
```

> Later, move embedding generation to a background task queue (Celery) to improve performance.

---

## 6. Semantic Search API

Create `app/routes/semantic_routes.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.embedding_service import EmbeddingService
from app.db.session import get_db
from app.models import Note
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/semantic", tags=["Semantic"])

@router.get("/search")
def search_notes(query: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    emb = EmbeddingService()
    query_vec = emb.generate(query)

    results = db.execute(
        """
        SELECT id, title, content
        FROM notes
        WHERE user_id = :uid
        ORDER BY embedding <=> :query_vec
        LIMIT 10
        """,
        {"uid": user.id, "query_vec": query_vec}
    ).fetchall()

    return [{"id": r.id, "title": r.title, "content": r.content} for r in results]
```

---

## 7. Testing

### 7.1 Unit Tests

Create `tests/test_embeddings.py`:

```python
def test_embedding_generation():
    text = "Faith comes by hearing the word of God."
    vec = EmbeddingService().generate(text)
    assert isinstance(vec, list)
    assert len(vec) > 100

def test_semantic_similarity():
    e = EmbeddingService()
    v1, v2 = e.generate("God is love."), e.generate("The Lord loves us.")
    assert e.similarity(v1, v2) > 0.7
```

### 7.2 Integration Tests

Simulate search with live DB data:

```python
def test_semantic_search(client, db, test_user, test_notes):
    response = client.get(f"/api/semantic/search?query=faith", headers=auth_header(test_user))
    assert response.status_code == 200
    assert len(response.json()) <= 10
```

---

## 8. AI Integration Slot

This is where **AI capabilities** plug into Scribes’ spiritual intelligence system:

| Feature               | Uses Embeddings | Description                                 |
| --------------------- | --------------- | ------------------------------------------- |
| **CrossRef**          | ✅               | Finds related notes using vector similarity |
| **Growth Guide AI**   | ✅               | Tracks user growth thematically             |
| **Paraphraser**       | ⚙️              | Context-aware rephrasing                    |
| **Thematic Clusters** | ✅               | Groups sermons by revelation themes         |

> Think of embeddings as the *language of meaning* that all AI features speak in.

---

## 9. Performance Tips

* Use **MiniLM** or **Instructor-XL** for local embedding generation.
* Use **batch encoding** for large note collections.
* Consider caching frequently queried vectors.
* Switch to **async workers** for non-blocking inference.

---

## 10. Deliverables Checklist

* [ ] Alembic migration with `embedding` column
* [ ] `EmbeddingService` implemented
* [ ] Integrated into Note create/update flows
* [ ] `/api/semantic/search` endpoint working
* [ ] Tests validated
* [ ] Docs updated under `/docs/phase_5_embeddings.md`

---

### ✅ Outcome

Once this phase is complete, **Scribes** will gain semantic understanding of its stored notes — enabling intelligent search, contextual recommendations, and AI-guided spiritual growth in later phases.
