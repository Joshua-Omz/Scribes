# 📘 Scribes Backend

A knowledge and note organization system powered by AI, built with **FastAPI** and **PostgreSQL**.

**Status:** ✅ Functional | 🚧 Production Infrastructure In Progress (20% complete)

---

## 🎯 Production Readiness Status

| Feature | Status | Impact | Docs |
|---------|--------|--------|------|
| **Rate Limiting** | ✅ READY | Abuse prevention, cost control | [Details](./docs/RATE_LIMITING_IMPLEMENTATION.md) |
| **Response Caching** | ⏳ PENDING | 60-80% cost reduction | [Plan](./docs/PRODUCTION_READINESS_PLAN.md) |
| **Observability** | ⏳ PENDING | Production monitoring | [Plan](./docs/PRODUCTION_READINESS_PLAN.md) |
| **Circuit Breakers** | ⏳ PENDING | Fault tolerance | [Plan](./docs/PRODUCTION_READINESS_PLAN.md) |

**Quick Start:** [Production Features Guide](./docs/PRODUCTION_FEATURES_QUICK_START.md)  
**Full Progress:** [Implementation Status](./docs/PRODUCTION_INFRASTRUCTURE_PROGRESS.md)

---

## 🗺️ Quick Navigation

**New to the project?** Start here:

- 📁 **[PROJECT_ORGANIZATION.md](./PROJECT_ORGANIZATION.md)** - Complete project structure guide
- 📖 **[REORGANIZATION_SUMMARY.md](./REORGANIZATION_SUMMARY.md)** - What changed and where things are
- 🤖 **[AI Assistant Docs](./docs/services/ai-assistant/README.md)** - Complete AI Assistant documentation
- 🧪 **[Test Documentation](./tests/README.md)** - How to run and write tests
- 🔧 **[Scripts Documentation](./scripts/README.md)** - All utility scripts explained

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ with `asyncpg` support
- Git

### 1️⃣ Clone & Setup

```powershell
# Clone the repository
git clone https://github.com/Joshua-Omz/Scribes-.git
cd Scribes-/backend2

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

```powershell
# Copy the example environment file
copy .env.example .env

# Edit .env with your actual configuration
notepad .env
```

**Required configurations:**
- `DATABASE_URL`: Your PostgreSQL connection string
- `JWT_SECRET_KEY`: Generate a secure secret key
- SMTP settings (if using email features)

### 3️⃣ Database Setup

```powershell
# Create PostgreSQL database
# In psql or your PostgreSQL client:
# CREATE DATABASE scribes_db;

# Run migrations to create tables
alembic upgrade head
```

### 4️⃣ Run the Application

```powershell
# Development mode with auto-reload
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
backend2/
├── app/
│   ├── main.py              # Application entry point
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management
│   │   └── database.py      # Database setup
│   ├── models/              # SQLAlchemy models
│   │   └── base.py          # Base model with timestamps
│   ├── schemas/             # Pydantic schemas
│   │   └── common.py        # Common schemas
│   ├── api/                 # API routes
│   │   └── health.py        # Health check endpoint
│   ├── services/            # Business logic layer
│   ├── repositories/        # Data access layer
│   ├── utils/               # Helper functions
│   └── tests/               # Test suite
├── alembic/                 # Database migrations
│   ├── env.py               # Alembic environment
│   ├── script.py.mako       # Migration template
│   └── versions/            # Migration files
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── alembic.ini              # Alembic configuration
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🗄️ Database Migrations

### Create a new migration

```powershell
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration
alembic revision -m "description of changes"
```

### Apply migrations

```powershell
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Show current version
alembic current

# Show migration history
alembic history
```

### Rollback migrations

```powershell
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade to base (empty database)
alembic downgrade base
```

## 🧪 Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_health.py

# Run with verbose output
pytest -v
```

## 📡 API Endpoints

### Health Check
- **GET** `/health` - Check API status

*More endpoints will be added as features are implemented.*

## 🔐 Security

- JWT token-based authentication
- Password hashing with bcrypt
- CORS configuration
- Environment-based secrets management

## 🛠️ Development Commands

```powershell
# Format code with black
black app/

# Sort imports with isort
isort app/

# Lint with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ | - |
| `JWT_SECRET_KEY` | Secret key for JWT signing | ✅ | - |
| `JWT_ALGORITHM` | JWT algorithm | ❌ | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | ❌ | 30 |
| `SMTP_HOST` | SMTP server host | ⚠️ | smtp.gmail.com |
| `SMTP_PORT` | SMTP server port | ⚠️ | 587 |
| `SMTP_USER` | SMTP username | ⚠️ | - |
| `SMTP_PASSWORD` | SMTP password | ⚠️ | - |
| `CORS_ORIGINS` | Allowed CORS origins | ❌ | localhost:3000 |
| `APP_ENV` | Environment (development/production) | ❌ | development |
| `DEBUG` | Enable debug mode | ❌ | True |

⚠️ = Required for email features

## 🎯 Roadmap

### Phase 1: Authentication ✅ (Next)
- [ ] User registration with email verification
- [ ] Login with JWT tokens
- [ ] Password reset flow
- [ ] Role-based access control

### Phase 2: Notes Module
- [ ] CRUD operations for notes
- [ ] Tagging system
- [ ] Search functionality
- [ ] Reminder fields

### Phase 3: Scribes Circles
- [ ] Create/join study groups
- [ ] Share notes within circles
- [ ] Invite/remove members

### Phase 4: AI Integration
- [ ] Semantic search with embeddings
- [ ] Cross-reference engine
- [ ] AI summarization
- [ ] Contextual tagging

### Phase 5: Advanced Features
- [ ] Spaced repetition system
- [ ] Export to Markdown/PDF
- [ ] Notification system

## 🤝 Contributing

1. Create a new branch for your feature
2. Follow the code structure and naming conventions
3. Write tests for new features
4. Ensure all tests pass before committing
5. Update documentation as needed

## 📄 License

This project is proprietary and confidential.

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI and PostgreSQL**
