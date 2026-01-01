# 🧩 Notes Feature Construction Guide (Phase 4)

This guide documents how to **design, implement, test, and document** the Notes feature in the Scribes backend. It assumes that authentication and database setup are already complete.

---

## 🗂️ Feature Overview

The **Notes module** enables users to:

* Create, update, delete, and retrieve sermon/study notes.
* Attach metadata (tags, preacher, scripture references).
* Maintain data integrity through user ownership.
* Support pagination, search, and later, AI-assisted cross-referencing.

### Folder Structure

```
app/
 ├─ models/
 │  └─ note.py
 ├─ schemas/
 │  └─ note_schemas.py
 ├─ db/
 │  └─ repositories/
 │     └─ note_repository.py
 ├─ services/
 │  └─ note_service.py
 ├─ api/
 │  └─ routes/
 │     └─ note_routes.py
```

---

## 🧱 Database Layer

### **File:** `app/models/note.py`

Defines the SQLAlchemy model for the `notes` table.

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    preacher = Column(String(100), nullable=True)
    tags = Column(String(255), nullable=True)
    scripture_tags = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="notes")
```

**Next:**

```bash
alembic revision --autogenerate -m "create notes table"
alembic upgrade head
```

---

## 🧩 Schema Layer (Validation & Serialization)

### **File:** `app/schemas/note_schemas.py`

Defines how API requests and responses are structured.

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NoteBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=5)
    preacher: Optional[str] = None
    tags: Optional[List[str]] = []
    scripture_tags: Optional[List[str]] = []

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]
    preacher: Optional[str]
    tags: Optional[List[str]]
    scripture_tags: Optional[List[str]]

class NoteResponse(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
```

---

## 🔧 Repository Layer (Data Access)

### **File:** `app/db/repositories/note_repository.py`

Handles all direct database operations.

```python
from sqlalchemy.orm import Session
from app.models.note import Note
from app.schemas.note_schemas import NoteCreate, NoteUpdate

def create_note(db: Session, note_data: NoteCreate, user_id: int):
    db_note = Note(
        user_id=user_id,
        title=note_data.title,
        content=note_data.content,
        preacher=note_data.preacher,
        tags=",".join(note_data.tags) if note_data.tags else None,
        scripture_tags=",".join(note_data.scripture_tags) if note_data.scripture_tags else None
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def get_notes_by_user(db: Session, user_id: int, skip=0, limit=100):
    return db.query(Note).filter(Note.user_id == user_id).offset(skip).limit(limit).all()

def get_note_by_user(db: Session, note_id: int, user_id: int):
    return db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()

def update_note(db: Session, note: Note, update_data: NoteUpdate):
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(note, key, value)
    db.commit()
    db.refresh(note)
    return note

def delete_note(db: Session, note: Note):
    db.delete(note)
    db.commit()
```

---

## ⚙️ Service Layer (Business Logic)

### **File:** `app/services/note_service.py`

Handles validation, authorization, and error handling.

```python
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.repositories import note_repository
from app.schemas.note_schemas import NoteCreate, NoteUpdate

def create_note_service(db: Session, note_data: NoteCreate, user_id: int):
    if not note_data.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    return note_repository.create_note(db, note_data, user_id)

def get_notes_service(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return note_repository.get_notes_by_user(db, user_id, skip, limit)

def get_note_service(db: Session, note_id: int, user_id: int):
    note = note_repository.get_note_by_user(db, note_id, user_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

def update_note_service(db: Session, note_id: int, update_data: NoteUpdate, user_id: int):
    note = get_note_service(db, note_id, user_id)
    return note_repository.update_note(db, note, update_data)

def delete_note_service(db: Session, note_id: int, user_id: int):
    note = get_note_service(db, note_id, user_id)
    return note_repository.delete_note(db, note)
```

---

## 🧠 API Layer

### **File:** `app/api/routes/note_routes.py`

Manages HTTP endpoints and request flow.

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.note_schemas import NoteCreate, NoteUpdate, NoteResponse
from app.services.note_service import *
from app.security.jwt import get_current_user

router = APIRouter(prefix="/api/notes", tags=["Notes"])

@router.post("/", response_model=NoteResponse)
def create_note(note_data: NoteCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_note_service(db, note_data, current_user.id)

@router.get("/", response_model=List[NoteResponse])
def get_notes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_notes_service(db, current_user.id)

@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_note_service(db, note_id, current_user.id)

@router.put("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_data: NoteUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return update_note_service(db, note_id, note_data, current_user.id)

@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    delete_note_service(db, note_id, current_user.id)
    return {"message": "Note deleted successfully"}
```

In `main.py`, include the router:

```python
from app.api.routes import note_routes
app.include_router(note_routes.router)
```

---

## 🧪 Testing the Notes Feature

### Via Swagger UI:

1. **Login** and copy access token.
2. Click **Authorize** → Paste Bearer token.
3. Test each endpoint:

   * `POST /api/notes/` → Create note
   * `GET /api/notes/` → Fetch all notes
   * `GET /api/notes/{id}` → Fetch single note
   * `PUT /api/notes/{id}` → Update note
   * `DELETE /api/notes/{id}` → Delete note

Expected responses:

* 201 for POST
* 200 for GET/PUT
* 204 or 200 for DELETE

---

## 🧩 Extensibility Hooks

Once CRUD is verified, integrate:

* **CrossRef:** Auto-link related notes.
* **AI Summaries:** Auto-generate highlights.
* **Reminder Sync:** Schedule revisits via tags.

The Notes module forms the **core semantic unit** of Scribes—all other features extend it.

---

### ✅ Deliverables for Phase 4

* Notes model + migration ✅
* Schema validation ✅
* Repository + service logic ✅
* API endpoints ✅
* Testing via Swagger ✅
* Documentation (this file) ✅

---

**Next Step:** Begin implementing **CrossRef** – the semantic linking engine that builds on your Notes foundation.
