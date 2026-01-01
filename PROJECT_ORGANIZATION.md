# 📁 Scribes Backend - Project Organization Guide

Complete guide to the Scribes backend project structure, documentation, and resources.

---

## 🗂️ Project Structure

```
backend2/
├── 📱 app/                    # Application code
│   ├── core/                  # Core configuration and dependencies
│   ├── models/                # Database models
│   ├── routes/                # API endpoints
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic services
│   ├── repositories/          # Data access layer
│   ├── utils/                 # Utility functions
│   └── worker/                # Background job workers
│
├── 📚 docs/                   # Documentation
│   ├── services/              # Service-specific documentation
│   │   └── ai-assistant/      # AI Assistant complete docs
│   ├── guides/                # Implementation guides
│   ├── database/              # Database documentation
│   ├── authentication/        # Auth documentation
│   ├── admin/                 # Admin guides
│   └── troubleshooting/       # Troubleshooting guides
│
├── 🧪 tests/                  # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── e2e/                   # End-to-end tests
│   └── utilities/             # Test utilities
│
├── 🔧 scripts/                # Utility scripts
│   ├── admin/                 # Admin scripts
│   ├── database/              # Database utilities
│   ├── testing/               # Test data generators
│   └── workers/               # Worker scripts
│
├── 🗄️ alembic/               # Database migrations
│   └── versions/              # Migration files
│
└── 📄 Configuration files
    ├── .env                   # Environment variables (not committed)
    ├── .env.example           # Environment template
    ├── requirements.txt       # Python dependencies
    ├── pytest.ini             # Test configuration
    └── alembic.ini            # Migration configuration
```

---

## 📚 Documentation Index

### 🏠 Main Documentation

- **[README.md](./README.md)** - Project overview and quick start
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture
- **[ADMIN_QUICK_START.md](./ADMIN_QUICK_START.md)** - Admin setup guide

### 🤖 AI Assistant Documentation

**Location:** [`docs/services/ai-assistant/`](./docs/services/ai-assistant/)

**Essential Reading:**
1. **[README.md](./docs/services/ai-assistant/README.md)** - Complete AI Assistant index
2. **[QUICK_START_ASSISTANT.md](./docs/services/ai-assistant/QUICK_START_ASSISTANT.md)** - Getting started
3. **[ASSISTANT_MANUAL_TESTING_GUIDE.md](./docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md)** - Testing guide (700+ lines)
4. **[ASSISTANT_SERVICE_IMPLEMENTATION_COMPLETE.md](./docs/services/ai-assistant/ASSISTANT_SERVICE_IMPLEMENTATION_COMPLETE.md)** - Implementation details

**All AI Assistant docs:**
- AI_Assistant_infrastructure.md
- ARCHITECTURE_DIAGRAM.md
- ASSISTANT_INTEGRATION_PLAN.md
- ASSISTANT_UNIT_TESTS_COMPLETE.md
- HF_TEXTGEN_IMPLEMENTATION_COMPLETE.md
- HF_TEXTGEN_SERVICE_BLUEPRINT.md
- PHASE_1_COMPLETE.md
- PHASE_2_CHECKLIST.md
- TOKENIZER_ASYNC_ANALYSIS.md
- TOKENIZER_OBSERVABILITY_METRICS.md
- UNIT_TESTS_COMPLETE.md

### 📖 Implementation Guides

**Location:** [`docs/guides/backend implementations/`](./docs/guides/backend%20implementations/)

- **CrossRef_feature.md** - Cross-reference feature
- **CrossRef_Implementation.md** - Cross-ref implementation
- **Embedding_implementations.md** - Embedding service
- **Notefeature_guide.md** - Note feature guide
- **GETTING_STARTED.md** - Developer onboarding

### 🔐 Authentication & Admin

**Location:** [`docs/authentication/`](./docs/authentication/) and [`docs/admin/`](./docs/admin/)

- User authentication flows
- Admin panel setup
- Role-based access control

### 💾 Database Documentation

**Location:** [`docs/database/`](./docs/database/)

- Schema documentation
- Migration guides
- pgvector setup

### 🐛 Troubleshooting

**Location:** [`docs/troubleshooting/`](./docs/troubleshooting/)

- Common issues and solutions
- Debug procedures
- Log analysis

### 📋 Deployment & Operations

- **[BACKGROUND_WORKER_SETUP.md](./docs/BACKGROUND_WORKER_SETUP.md)** - Worker setup
- **[TESTING_DEPLOYMENT_CHECKLIST.md](./docs/TESTING_DEPLOYMENT_CHECKLIST.md)** - Deployment checklist
- **[PRODUCTION_REQUIREMENTS_AUDIT.md](./docs/PRODUCTION_REQUIREMENTS_AUDIT.md)** - Production requirements

---

## 🧪 Testing

**Complete test documentation:** [`tests/README.md`](./tests/README.md)

### Test Structure

```
tests/
├── unit/                      # Fast, isolated tests
│   ├── test_assistant_service.py
│   ├── test_hf_textgen_service.py
│   ├── test_chunking.py
│   └── test_prompt_engine.py
│
├── integration/               # Multi-component tests
│   ├── test_background_jobs.py
│   ├── test_arq_queue.py
│   └── test_job_system.py
│
├── e2e/                       # End-to-end workflows
│   └── e2e_test_jobs.py
│
└── utilities/                 # Test helpers
    ├── database_connection.py
    └── verify_semantic_v2.py
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_assistant_service.py -v
```

---

## 🔧 Scripts

**Complete script documentation:** [`scripts/README.md`](./scripts/README.md)

### Available Scripts

#### Admin Scripts (`scripts/admin/`)
```bash
# Create admin user
python scripts/admin/bootstrap_admin.py
```

#### Database Scripts (`scripts/database/`)
```bash
# Validate database configuration
python scripts/database/config_validationScripts.py
```

#### Testing Scripts (`scripts/testing/`)
```bash
# Generate test data for AI Assistant
python scripts/testing/create_test_data.py

# Run embedding tests
.\scripts\testing\run_embedding_tests.ps1
```

#### Worker Scripts (`scripts/workers/`)
```bash
# Start background worker
.\scripts\workers\run_worker.ps1
```

---

## 🚀 Common Workflows

### 1. First-Time Setup

```bash
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Validate database
python scripts/database/config_validationScripts.py

# 5. Run migrations
alembic upgrade head

# 6. Create admin user
python scripts/admin/bootstrap_admin.py
```

### 2. Running the Application

```bash
# Activate environment
.\venv\Scripts\Activate.ps1

# Start API server
uvicorn app.main:app --reload

# In separate terminal: Start background worker
.\venv\Scripts\Activate.ps1
.\scripts\workers\run_worker.ps1
```

### 3. Development Workflow

```bash
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes to code

# 4. Run tests
pytest

# 5. Run linting (if configured)
flake8 app/

# 6. Commit changes
git add .
git commit -m "Add my feature"

# 7. Push to remote
git push origin feature/my-feature
```

### 4. AI Assistant Testing

```bash
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Generate test data
python scripts/testing/create_test_data.py

# 3. Run unit tests
pytest tests/unit/test_assistant_service.py -v

# 4. Manual testing
# See: docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md
```

### 5. Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## 🎯 Quick Navigation

### I want to...

**Set up the project for the first time**
→ See [First-Time Setup](#1-first-time-setup)

**Understand the AI Assistant**
→ [`docs/services/ai-assistant/README.md`](./docs/services/ai-assistant/README.md)

**Test the AI Assistant**
→ [`docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md`](./docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md)

**Generate test data**
→ [`scripts/README.md`](./scripts/README.md) → Testing Scripts

**Run tests**
→ [`tests/README.md`](./tests/README.md)

**Create database migrations**
→ [Database Migrations](#5-database-migrations)

**Deploy to production**
→ [`docs/TESTING_DEPLOYMENT_CHECKLIST.md`](./docs/TESTING_DEPLOYMENT_CHECKLIST.md)

**Troubleshoot issues**
→ [`docs/troubleshooting/`](./docs/troubleshooting/)

**Set up background workers**
→ [`docs/BACKGROUND_WORKER_SETUP.md`](./docs/BACKGROUND_WORKER_SETUP.md)

---

## 📦 Key Dependencies

### Core Framework
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM
- **Pydantic** - Data validation
- **Alembic** - Database migrations

### AI & ML
- **sentence-transformers** - Embedding generation
- **transformers** - Tokenization
- **pgvector** - Vector similarity search
- **Hugging Face API** - Text generation

### Background Processing
- **ARQ** - Async job queue
- **Redis** - Queue backend

### Testing
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **httpx** - Async HTTP client for tests

---

## 🔐 Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Keep API keys secure** - Use environment variables only
3. **Validate all inputs** - Pydantic schemas handle this
4. **Use parameterized queries** - SQLAlchemy prevents SQL injection
5. **Implement rate limiting** - In production environments
6. **Regular dependency updates** - Security patches

---

## 📈 Performance Guidelines

### AI Assistant Response Times
- Target: <5 seconds total
- Embedding: <100ms
- Retrieval: <200ms
- Generation: <3s

### Database Queries
- Use indexes for frequent queries
- Implement connection pooling
- Monitor slow queries

### Background Jobs
- Use ARQ for long-running tasks
- Implement job retries
- Monitor queue depth

---

## 🤝 Contributing

1. Create feature branch
2. Write tests for new features
3. Ensure all tests pass
4. Update documentation
5. Submit pull request

---

## 📞 Support & Resources

### Documentation
- **Main docs:** `docs/`
- **AI Assistant:** `docs/services/ai-assistant/`
- **Scripts:** `scripts/README.md`
- **Tests:** `tests/README.md`

### Troubleshooting
- Check `docs/troubleshooting/`
- Review test output
- Check application logs

---

## 🗺️ Project Roadmap

### ✅ Phase 1: Core Features (Complete)
- User authentication
- Note management
- AI Assistant RAG pipeline
- Background job processing
- Semantic search

### 🚧 Phase 2: Advanced Features (Planned)
- Conversation history
- Multi-turn dialogue
- Response streaming
- Advanced prompt templates
- Performance optimizations

### 📋 Phase 3: Production (Upcoming)
- Comprehensive monitoring
- Advanced security features
- Scalability improvements
- API rate limiting
- Caching strategies

---

**Last Updated:** December 12, 2025
**Current Phase:** Phase 1 Complete ✅
