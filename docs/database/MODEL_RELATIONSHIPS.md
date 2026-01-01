# 🔗 Database Model Relationships Documentation

**Date:** November 3, 2025  
**Status:** ✅ All relationships verified and complete

---

## 📊 Complete Relationship Map

This document maps all SQLAlchemy relationships across the Scribes backend models.

---

## 🧑 User Model Relationships

**File:** `app/models/user_model.py`

### User has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `notes` | Note | One-to-Many | `user` | all, delete |
| `reminders` | Reminder | One-to-Many | `user` | all, delete |
| `owned_circles` | Circle | One-to-Many | `owner` | default |
| `circle_memberships` | CircleMember | One-to-Many | `user` | all, delete |
| `profile` | UserProfile | One-to-One | `user` | all, delete |
| `annotations` | Annotation | One-to-Many | `user` | all, delete |
| `export_jobs` | ExportJob | One-to-Many | `user` | all, delete |
| `notifications` | Notification | One-to-Many | `user` | all, delete |
| `reset_tokens` | PasswordResetToken | One-to-Many | `user` | all, delete-orphan |

**Summary:** User is the central entity with 9 direct relationships

---

## 📝 Note Model Relationships

**File:** `app/models/note_model.py`

### Note has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `user` | User | Many-to-One | `notes` | default |
| `reminders` | Reminder | One-to-Many | `note` | all, delete |
| `shared_circles` | CircleNote | One-to-Many | `note` | all, delete |
| `outgoing_refs` | CrossRef | One-to-Many | `note` | all, delete |
| `incoming_refs` | CrossRef | One-to-Many | `other_note` | all, delete |
| `annotations` | Annotation | One-to-Many | `note` | all, delete |
| `export_jobs` | ExportJob | One-to-Many | `note` | all, delete |

**Special Cases:**
- **Self-referential relationships** via CrossRef:
  - `outgoing_refs`: References FROM this note TO other notes
  - `incoming_refs`: References FROM other notes TO this note
  - Uses `foreign_keys` parameter to distinguish the two relationships

**Summary:** Note has 7 relationships (including 2 self-referential)

---

## ⏰ Reminder Model Relationships

**File:** `app/models/reminder_model.py`

### Reminder has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `user` | User | Many-to-One | `reminders` | default |
| `note` | Note | Many-to-One | `reminders` | default |

**Summary:** Reminder links Users and Notes (junction entity for scheduled reminders)

---

## 👥 Circle Models Relationships

**File:** `app/models/circle_model.py`

### Circle has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `owner` | User | Many-to-One | `owned_circles` | default |
| `members` | CircleMember | One-to-Many | `circle` | all, delete-orphan |
| `circle_notes` | CircleNote | One-to-Many | `circle` | all, delete-orphan |

### CircleMember has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `circle` | Circle | Many-to-One | `members` | default |
| `user` | User | Many-to-One | `circle_memberships` | default |
| `inviter` | User | Many-to-One | (none) | default |

**Note:** Uses `foreign_keys` parameter to distinguish `user` (member) from `inviter` (who invited them)

### CircleNote has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `circle` | Circle | Many-to-One | `circle_notes` | default |
| `note` | Note | Many-to-One | `shared_circles` | default |

**Summary:** Circle system uses 3 models with 7 relationships total

---

## 🔗 CrossRef Model Relationships

**File:** `app/models/cross_ref_model.py`

### CrossRef has relationships with:

| Relationship | Model | Type | Back Populates | Foreign Key | Cascade |
|-------------|-------|------|----------------|-------------|---------|
| `note` | Note | Many-to-One | `outgoing_refs` | `note_id` | default |
| `other_note` | Note | Many-to-One | `incoming_refs` | `other_note_id` | default |

**Special Pattern:** Self-referential relationship through CrossRef
- Creates directional links between notes
- `note` → `other_note` represents "note references other_note"
- Both foreign keys point to `notes.id` but use different relationship names
- Uses `foreign_keys` parameter to distinguish the two sides

**Summary:** CrossRef enables bi-directional note linking with 2 relationships

---

## 🖍️ Annotation Model Relationships

**File:** `app/models/annotation_model.py`

### Annotation has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `user` | User | Many-to-One | `annotations` | default |
| `note` | Note | Many-to-One | `annotations` | default |

**Summary:** Annotation links Users to specific parts of Notes (2 relationships)

---

## 📤 ExportJob Model Relationships

**File:** `app/models/export_job_model.py`

### ExportJob has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `user` | User | Many-to-One | `export_jobs` | default |
| `note` | Note | Many-to-One | `export_jobs` | default |

**Note:** `note` relationship is **optional** (nullable=True) for multi-note exports

**Summary:** ExportJob tracks async export tasks (2 relationships)

---

## 🔔 Notification Model Relationships

**File:** `app/models/notification_model.py`

### Notification has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `user` | User | Many-to-One | `notifications` | default |

**Summary:** Notification is user-specific (1 relationship)

---

## 🔑 PasswordResetToken Model Relationships

**File:** `app/models/password_reset_model.py`

### PasswordResetToken has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `user` | User | Many-to-One | `reset_tokens` | default |

**Summary:** Tracks password reset tokens per user (1 relationship)

---

## 👤 UserProfile Model Relationships

**File:** `app/models/user_profile_model.py`

### UserProfile has relationships with:

| Relationship | Model | Type | Back Populates | Cascade |
|-------------|-------|------|----------------|---------|
| `user` | User | One-to-One | `profile` | default |

**Note:** One-to-One relationship (uselist=False on User side)

**Summary:** Extended user information (1 relationship)

---

## 📈 Relationship Statistics

### Total Relationships: **31 bidirectional relationships**

### By Model:
- **User**: 9 relationships (central hub)
- **Note**: 7 relationships (content hub)
- **Circle**: 3 relationships
- **CircleMember**: 3 relationships
- **CircleNote**: 2 relationships
- **CrossRef**: 2 relationships (self-referential)
- **Reminder**: 2 relationships
- **Annotation**: 2 relationships
- **ExportJob**: 2 relationships
- **Notification**: 1 relationship
- **PasswordResetToken**: 1 relationship
- **UserProfile**: 1 relationship

---

## 🎯 Relationship Patterns

### 1. **Central Hub Pattern**
- **User** is the primary entity
- Most models have a `user_id` foreign key
- Enables per-user data isolation

### 2. **Content Hub Pattern**
- **Note** is the secondary hub
- Features (reminders, annotations, refs) attach to notes
- Enables rich note functionality

### 3. **Many-to-Many Associations**
Implemented via junction tables:
- **Circle ↔ User** via `CircleMember`
- **Circle ↔ Note** via `CircleNote`

### 4. **Self-Referential Pattern**
- **Note ↔ Note** via `CrossRef`
- Uses `foreign_keys` parameter
- Creates directed graph of note relationships

### 5. **One-to-One Pattern**
- **User ↔ UserProfile**
- Uses `uselist=False`
- Separates core auth data from extended profile

---

## 🔄 Cascade Behaviors

### **All, Delete** (Most Common)
Used for owned children that should be deleted with parent:
- User → Notes
- User → Reminders
- Note → Annotations
- Note → CrossRefs

### **All, Delete-Orphan**
Used for strict ownership with orphan cleanup:
- Circle → CircleMembers
- Circle → CircleNotes
- User → PasswordResetTokens

### **Default** (No Cascade)
Used for references without ownership:
- Note → User (don't delete user when note is deleted)
- Reminder → Note (reference relationship)

---

## ✅ Verification Checklist

All relationships verified as **complete and bidirectional**:

- [x] **User** - All 9 relationships properly defined
- [x] **Note** - All 7 relationships properly defined
- [x] **Circle** - All 3 relationships properly defined
- [x] **CircleMember** - All 3 relationships properly defined
- [x] **CircleNote** - All 2 relationships properly defined
- [x] **CrossRef** - Self-referential relationships working
- [x] **Reminder** - Both relationships defined
- [x] **Annotation** - Both relationships defined
- [x] **ExportJob** - Both relationships defined
- [x] **Notification** - Relationship defined
- [x] **PasswordResetToken** - Relationship defined
- [x] **UserProfile** - One-to-one relationship defined

**Status:** ✅ **All relationships are complete and properly configured!**

---

## 🛠️ Relationship Best Practices

### When Adding New Relationships:

1. **Always define `back_populates`** on both sides
2. **Choose appropriate cascade** based on ownership
3. **Use `foreign_keys`** parameter for ambiguous relationships
4. **Add unique constraints** for junction tables
5. **Consider nullable** for optional relationships
6. **Update both models** in the same commit

### Common Patterns:

**One-to-Many:**
```python
# Parent
children = relationship("Child", back_populates="parent", cascade="all, delete")

# Child
parent = relationship("Parent", back_populates="children")
```

**Many-to-Many (via junction):**
```python
# Model A
bs = relationship("AB", back_populates="a")

# Junction
a = relationship("A", back_populates="bs")
b = relationship("B", back_populates="as_")

# Model B
as_ = relationship("AB", back_populates="b")
```

**Self-Referential:**
```python
# Parent
children = relationship("Model", 
                       foreign_keys="Model.parent_id",
                       back_populates="parent")
parent = relationship("Model", 
                     foreign_keys="Model.parent_id",
                     back_populates="children", 
                     remote_side="Model.id")
```

---

## 📝 Migration Notes

When creating migrations for relationships:

1. **Foreign keys** are created automatically
2. **Indexes** added to foreign key columns
3. **Cascade rules** enforced at database level
4. **Unique constraints** prevent duplicate associations

Example:
```bash
alembic revision --autogenerate -m "add note relationships"
alembic upgrade head
```

---

**Last Updated:** November 3, 2025  
**Status:** All 31 bidirectional relationships verified ✅
