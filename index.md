# 📁 Scribes Backend - Complete Directory Structure

**Last Updated:** December 12, 2025

---

## 🗂️ Complete Project Tree

```
Scribes/backend2/
│
├── 📄 Configuration & Documentation
│   ├── .env                              # Environment variables (not in git)
│   ├── .env.example                      # Environment template
│   ├── requirements.txt                   # Python dependencies
│   ├── pytest.ini                         # Test configuration
│   ├── alembic.ini                        # Migration configuration
│   │
│   ├── README.md                          # ⭐ Main project README
│   ├── PROJECT_ORGANIZATION.md            # 📚 Master navigation guide
│   ├── ORGANIZATION_COMPLETE.md           # 🎉 Organization summary
│   ├── REORGANIZATION_SUMMARY.md          # 📖 What changed in docs/scripts/tests
│   ├── APP_REORGANIZATION_PLAN.md         # 📋 App structure plan
│   └── APP_REORGANIZATION_COMPLETE.md     # ✅ App structure complete
│
├── 📱 app/                                # APPLICATION SOURCE CODE
│   ├── main.py                            # FastAPI application entry point
│   │
│   ├── 🎯 core/                           # Core framework components
│   │   ├── config.py                      # Application configuration
│   │   ├── database.py                    # Database setup & connection
│   │   ├── security.py                    # Security utilities (JWT, hashing)
│   │   ├── dependencies.py                # FastAPI dependencies
│   │   │
│   │   └── ai/                            # ✨ AI-specific core components
│   │       ├── __init__.py
│   │       └── prompt_engine.py           # LLM prompt template management
│   │
│   ├── 🔧 services/                       # Business logic services
│   │   │
│   │   ├── ai/                            # ✨ AI & ML services
│   │   │   ├── __init__.py               # Clean exports
│   │   │   ├── assistant_service.py       # RAG pipeline orchestrator
│   │   │   ├── embedding_service.py       # 384-dim vector generation
│   │   │   ├── retrieval_service.py       # Semantic search (pgvector)
│   │   │   ├── tokenizer_service.py       # Token-aware text processing
│   │   │   ├── chunking_service.py        # Text chunking with overlap
│   │   │   ├── context_builder.py         # Smart context assembly
│   │   │   └── hf_textgen_service.py      # Hugging Face API integration
│   │   │
│   │   └── business/                      # ✨ Business logic services
│   │       ├── __init__.py               # Clean exports
│   │       ├── auth_service.py            # Authentication & authorization
│   │       ├── note_service.py            # Notes CRUD operations
│   │       └── cross_ref_service.py       # Cross-reference management
│   │
│   ├── 🛣️ routes/                         # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py                      # Health check endpoint
│   │   ├── assistant_routes.py            # AI Assistant endpoints
│   │   ├── semantic_routes.py             # Semantic search endpoints
│   │   ├── auth_routes.py                 # Authentication endpoints
│   │   ├── note_routes.py                 # Note CRUD endpoints
│   │   ├── cross_ref_routes.py            # Cross-reference endpoints
│   │   └── job_routes.py                  # Background job endpoints
│   │
│   ├── 💾 models/                         # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── base.py                        # Base model class
│   │   ├── user_model.py                  # User model
│   │   ├── user_profile_model.py          # User profile
│   │   ├── note_model.py                  # Note model
│   │   ├── note_chunk_model.py            # Note chunks with embeddings
│   │   ├── annotation_model.py            # Annotations
│   │   ├── cross_ref_model.py             # Cross-references
│   │   ├── background_job_model.py        # Background jobs
│   │   ├── export_job_model.py            # Export jobs
│   │   ├── notification_model.py          # Notifications
│   │   ├── reminder_model.py              # Reminders
│   │   ├── password_reset_model.py        # Password resets
│   │   ├── refresh_model.py               # Refresh tokens
│   │   ├── circle_model.py                # User circles
│   │   └── events.py                      # Event models
│   │
│   ├── 📋 schemas/                        # Pydantic schemas (validation)
│   │   ├── __init__.py
│   │   ├── user_schema.py                 # User schemas
│   │   ├── note_schema.py                 # Note schemas
│   │   ├── auth_schema.py                 # Auth schemas
│   │   └── ... (other schemas)
│   │
│   ├── 🗄️ repositories/                   # Data access layer
│   │   ├── __init__.py
│   │   ├── user_repository.py             # User data access
│   │   ├── note_repository.py             # Note data access
│   │   └── cross_ref_repository.py        # Cross-ref data access
│   │
│   ├── 🛠️ utils/                          # Utility functions
│   │   ├── __init__.py
│   │   │
│   │   ├── helpers/                       # ✨ General utilities
│   │   │   ├── __init__.py
│   │   │   ├── text_utils.py              # Text manipulation
│   │   │   ├── validation.py              # Input validation
│   │   │   └── formatters.py              # Data formatting
│   │   │
│   │   └── email/                         # ✨ Email utilities
│   │       ├── __init__.py
│   │       └── email.py                   # Email sending
│   │
│   └── 👷 worker/                         # Background job workers
│       ├── __init__.py
│       └── worker.py                      # ARQ worker configuration
│
├── 🧪 tests/                              # TEST SUITE
│   ├── README.md                          # 📖 Complete testing guide
│   │
│   ├── unit/                              # ✨ Unit tests (isolated)
│   │   ├── test_assistant_service.py      # AI Assistant tests (13 tests)
│   │   ├── test_hf_textgen_service.py     # Text generation tests
│   │   ├── test_chunking.py               # Chunking tests
│   │   └── test_prompt_engine.py          # Prompt engine tests
│   │
│   ├── integration/                       # ✨ Integration tests
│   │   ├── test_background_jobs.py        # Job system tests
│   │   ├── test_arq_queue.py              # Queue tests
│   │   └── test_job_system.py             # Complete workflow tests
│   │
│   ├── e2e/                               # ✨ End-to-end tests
│   │   └── e2e_test_jobs.py               # Full workflow tests
│   │
│   └── utilities/                         # ✨ Test utilities
│       ├── database_connection.py         # Test DB helpers
│       └── verify_semantic_v2.py          # Semantic search verification
│
├── 🔧 scripts/                            # UTILITY SCRIPTS
│   ├── README.md                          # 📖 Scripts documentation
│   │
│   ├── admin/                             # ✨ Admin scripts
│   │   └── bootstrap_admin.py             # Create admin user
│   │
│   ├── database/                          # ✨ Database scripts
│   │   └── config_validationScripts.py    # Validate DB config
│   │
│   ├── testing/                           # ✨ Testing scripts
│   │   ├── create_test_data.py            # Generate test data
│   │   └── run_embedding_tests.ps1        # Run embedding tests
│   │
│   └── workers/                           # ✨ Worker scripts
│       └── run_worker.ps1                 # Start background worker
│
├── 📚 docs/                               # DOCUMENTATION
│   ├── README.md                          # Docs index
│   │
│   ├── services/                          # Service documentation
│   │   └── ai-assistant/                  # ✨ AI Assistant docs (consolidated)
│   │       ├── README.md                  # 📚 Complete AI index (600+ lines)
│   │       ├── QUICK_START_ASSISTANT.md   # Getting started
│   │       ├── AI_Assistant_infrastructure.md
│   │       ├── ARCHITECTURE_DIAGRAM.md
│   │       ├── ASSISTANT_INTEGRATION_PLAN.md
│   │       ├── ASSISTANT_SERVICE_IMPLEMENTATION_COMPLETE.md
│   │       ├── ASSISTANT_UNIT_TESTS_COMPLETE.md
│   │       ├── ASSISTANT_MANUAL_TESTING_GUIDE.md  # 700+ lines
│   │       ├── HF_TEXTGEN_IMPLEMENTATION_COMPLETE.md
│   │       ├── HF_TEXTGEN_SERVICE_BLUEPRINT.md
│   │       ├── PHASE_1_COMPLETE.md
│   │       ├── PHASE_2_CHECKLIST.md
│   │       ├── PHASE_2_IMPLEMENTATION_GUIDE.md
│   │       ├── PHASE_2_SERVICE_IMPLEMENTATION_COMPLETE.md
│   │       ├── TOKENIZER_ASYNC_ANALYSIS.md
│   │       ├── TOKENIZER_OBSERVABILITY_METRICS.md
│   │       └── UNIT_TESTS_COMPLETE.md
│   │
│   ├── guides/                            # Implementation guides
│   │   ├── backend implementations/
│   │   │   ├── GETTING_STARTED.md
│   │   │   ├── CrossRef_feature.md
│   │   │   ├── CrossRef_Implementation.md
│   │   │   ├── Embedding_implementations.md
│   │   │   └── Notefeature_guide.md
│   │   │
│   │   ├── DEPLOYMENT_CHECKLIST_V2.md
│   │   ├── EMBEDDING_CLEANUP_SUMMARY.md
│   │   ├── IMPLEMENTATION_SUMMARY.md
│   │   ├── PATCH_Implementation_Summary.md
│   │   ├── PATCH_Update_Implementation_Plan.md
│   │   ├── PATCH_Update_Quick_Reference.md
│   │   ├── Semantic_Embeddings_Implementation.md
│   │   └── SEMANTIC_SEARCH_V2_IMPLEMENTATION.md
│   │
│   ├── database/                          # Database documentation
│   ├── authentication/                    # Auth documentation
│   ├── admin/                             # Admin guides
│   ├── email/                             # Email docs
│   ├── troubleshooting/                   # Troubleshooting guides
│   │
│   ├── BACKGROUND_OPERATIONS_IMPLEMENTATION.md
│   ├── BACKGROUND_WORKER_SETUP.md
│   ├── PRODUCTION_REQUIREMENTS_AUDIT.md
│   ├── suggestedUpdateformatImplementation.md
│   └── TESTING_DEPLOYMENT_CHECKLIST.md
│
├── 🗄️ alembic/                           # DATABASE MIGRATIONS
│   ├── env.py                             # Alembic environment
│   ├── script.py.mako                     # Migration template
│   └── versions/                          # Migration files
│       ├── 001_notes_scripture_refs.py
│       ├── 002_create_cross_refs_table.py
│       ├── 2025-11-04_*_add_embeddings_to_notes.py
│       ├── 2025-11-07_*_add_embedding_column_to_notes.py
│       ├── 2025-11-09_*_add_hnsw_index_for_embeddings.py
│       ├── 2025-11-11_*_change_embedding_dimension_to_384.py
│       ├── 2025-11-18_*_create_background_jobs_table.py
│       └── 2025-11-23_create_note_chunks_table.py
│
└── 🐍 venv/                               # Virtual environment (not in git)
```

---

## 🎯 Key Directories Explained

### Application Code (`app/`)

**Core Framework** (`app/core/`)
- Framework essentials: config, database, security
- **NEW:** `core/ai/` for AI-specific core components

**Services** (`app/services/`)
- **NEW:** `services/ai/` - All AI & ML services (7 services)
- **NEW:** `services/business/` - Business logic services (3 services)

**API Routes** (`app/routes/`)
- All FastAPI endpoint definitions
- Organized by feature domain

**Data Layer** (`app/models/`, `app/schemas/`, `app/repositories/`)
- Models: SQLAlchemy ORM models
- Schemas: Pydantic validation schemas
- Repositories: Data access layer

**Utilities** (`app/utils/`)
- **NEW:** `utils/helpers/` - General utilities (text, validation, formatting)
- **NEW:** `utils/email/` - Email-specific utilities

---

### Testing (`tests/`)

**Organized by Test Type:**
- `unit/` - Fast, isolated tests (4 files)
- `integration/` - Multi-component tests (3 files)
- `e2e/` - End-to-end workflows (1 file)
- `utilities/` - Test helpers (2 files)

---

### Scripts (`scripts/`)

**Organized by Purpose:**
- `admin/` - Admin user management
- `database/` - DB validation and utilities
- `testing/` - Test data generation
- `workers/` - Background worker scripts

---

### Documentation (`docs/`)

**Organized by Topic:**
- `services/ai-assistant/` - **All AI docs consolidated** (15+ files)
- `guides/` - Implementation guides
- `database/` - Database docs
- `authentication/` - Auth docs
- Root-level deployment and operations docs

---

## 📊 Directory Statistics

| Category | Count |
|----------|-------|
| **Total Directories** | 35+ |
| **Application Files** | 60+ |
| **Test Files** | 10 |
| **Documentation Files** | 40+ |
| **Script Files** | 5 |
| **Migration Files** | 8 |

---

## 🌟 New Structure Highlights

### ✨ AI Services Separated
```
app/services/ai/
    ├── assistant_service.py      # RAG orchestrator
    ├── embedding_service.py       # Embeddings
    ├── retrieval_service.py       # Semantic search
    └── ... (4 more AI services)
```

### ✨ Business Services Organized
```
app/services/business/
    ├── auth_service.py            # Authentication
    ├── note_service.py            # Notes CRUD
    └── cross_ref_service.py       # Cross-references
```

### ✨ Utilities Categorized
```
app/utils/
    ├── helpers/                   # General utilities
    │   ├── text_utils.py
    │   ├── validation.py
    │   └── formatters.py
    └── email/                     # Email utilities
        └── email.py
```

### ✨ Tests Categorized
```
tests/
    ├── unit/                      # Unit tests
    ├── integration/               # Integration tests
    ├── e2e/                       # End-to-end tests
    └── utilities/                 # Test helpers
```

### ✨ Scripts Organized
```
scripts/
    ├── admin/                     # Admin scripts
    ├── database/                  # DB scripts
    ├── testing/                   # Test scripts
    └── workers/                   # Worker scripts
```

### ✨ AI Docs Consolidated
```
docs/services/ai-assistant/
    ├── README.md                  # Complete index
    ├── QUICK_START_ASSISTANT.md
    ├── ASSISTANT_MANUAL_TESTING_GUIDE.md
    └── ... (12 more AI docs)
```

---

## 🎨 Design Principles

✅ **Separation of Concerns** - AI, business, utilities clearly separated  
✅ **Domain-Driven Organization** - Files grouped by purpose  
✅ **Discoverability** - Obvious where everything belongs  
✅ **Scalability** - Easy to add new features  
✅ **Maintainability** - Clear structure reduces cognitive load  
✅ **Professional** - Enterprise-grade organization  

---

## 🚀 Quick Navigation

**Want to find:**
- **AI services?** → `app/services/ai/`
- **Business logic?** → `app/services/business/`
- **API endpoints?** → `app/routes/`
- **Database models?** → `app/models/`
- **Tests?** → `tests/` (organized by type)
- **Scripts?** → `scripts/` (organized by purpose)
- **AI documentation?** → `docs/services/ai-assistant/`
- **General docs?** → `docs/`

---

**Last Updated:** December 12, 2025  
**Organization Status:** ✅ Complete and Professional!
