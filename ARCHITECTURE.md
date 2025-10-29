# 🏗️ Scribes Backend - Architecture Overview

## 📐 Design Principles

### Clean Architecture
- **Separation of Concerns**: Each layer has a single responsibility
- **Dependency Rule**: Dependencies point inward (routes → services → repositories → models)
- **Testability**: Easy to mock and test each layer independently

### Layer Responsibilities

```
┌─────────────────────────────────────┐
│         API Layer (Routes)          │  ← HTTP Request/Response
├─────────────────────────────────────┤
│         Service Layer               │  ← Business Logic
├─────────────────────────────────────┤
│       Repository Layer              │  ← Data Access
├─────────────────────────────────────┤
│      Database (PostgreSQL)          │  ← Persistence
└─────────────────────────────────────┘
```

## 📂 Directory Structure Explained

### `/app/core/`
Core application components that are used across the entire app:
- `config.py` - Environment configuration and settings
- `database.py` - Database connection and session management
- `security.py` - Authentication, hashing, JWT utilities

### `/app/models/`
SQLAlchemy ORM models representing database tables:
- `base.py` - Base model with common fields (id, timestamps)
- Future: `user.py`, `note.py`, `circle.py`, etc.

### `/app/schemas/`
Pydantic schemas for request/response validation:
- `common.py` - Shared schemas (pagination, errors)
- Future: `user.py`, `note.py`, `auth.py`, etc.

### `/app/api/`
FastAPI route definitions (HTTP endpoints):
- `health.py` - Health check endpoint
- Future: `auth.py`, `notes.py`, `circles.py`, etc.

### `/app/services/`
Business logic layer - processes data, enforces rules:
- Future: `auth_service.py`, `note_service.py`, etc.
- Orchestrates multiple repository calls
- Handles complex business rules

### `/app/repositories/`
Data access layer - database operations:
- Future: `user_repository.py`, `note_repository.py`, etc.
- CRUD operations
- Query builders
- No business logic

### `/app/utils/`
Helper utilities and common functions:
- `email.py` - Email sending utilities
- Future: `validators.py`, `formatters.py`, etc.

### `/app/tests/`
Test suite:
- `conftest.py` - Pytest fixtures and configuration
- `test_*.py` - Test files for each module

### `/alembic/`
Database migration management:
- `env.py` - Alembic environment configuration
- `versions/` - Migration files

## 🔄 Request Flow Example

### User Registration Flow:
```
1. POST /auth/register
   ↓
2. API Layer (auth.py)
   - Validates request schema
   - Calls AuthService
   ↓
3. Service Layer (auth_service.py)
   - Checks business rules
   - Hashes password
   - Calls UserRepository
   - Creates verification token
   - Sends verification email
   ↓
4. Repository Layer (user_repository.py)
   - Creates user in database
   - Returns user model
   ↓
5. Response flows back up
   - Repository → Service → API
   - API returns JSON response
```

## 🗄️ Database Design Standards

### All tables include:
- `id` - Primary key (auto-increment integer)
- `created_at` - Timestamp of creation
- `updated_at` - Timestamp of last update

### Naming Conventions:
- Tables: snake_case plural (e.g., `users`, `notes`, `scribes_circles`)
- Columns: snake_case (e.g., `user_id`, `email_verified`)
- Indexes: `ix_table_column` (e.g., `ix_users_email`)
- Foreign Keys: `fk_table_column` (e.g., `fk_notes_user_id`)

## 🔐 Security Architecture

### Authentication Flow:
1. User submits credentials
2. Verify password hash
3. Generate JWT access token (30 min expiry)
4. Generate JWT refresh token (7 day expiry)
5. Return both tokens

### Authorization:
- Role-based access control (user, admin)
- JWT token verification middleware
- Permission checks in service layer

### Password Security:
- Bcrypt hashing with salt
- Minimum length enforcement
- Password reset tokens (1 hour expiry)

## 📊 API Response Standards

### Success Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2025-10-29T12:00:00Z"
}
```

### Error Response:
```json
{
  "detail": "User not found",
  "error_code": "USER_NOT_FOUND",
  "timestamp": "2025-10-29T12:00:00Z"
}
```

### Paginated Response:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## 🧪 Testing Strategy

### Test Types:
1. **Unit Tests** - Test individual functions/methods
2. **Integration Tests** - Test API endpoints with test database
3. **Service Tests** - Test business logic layer

### Test Database:
- Separate database: `scribes_test_db`
- Fresh schema for each test
- Isolated transactions
- Rollback after each test

## 🚀 Deployment Checklist

### Environment Configuration:
- [ ] Set production `DATABASE_URL`
- [ ] Generate secure `JWT_SECRET_KEY`
- [ ] Configure SMTP credentials
- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Configure CORS origins

### Database:
- [ ] Create production database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Enable SSL connections
- [ ] Set up backups

### Security:
- [ ] Use HTTPS only
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure logging

## 📈 Future Enhancements

### Phase 1: Authentication (Next)
- User registration with email verification
- Login/logout with JWT
- Password reset flow
- Role management

### Phase 2: Notes Module
- CRUD for notes
- Tagging system
- Full-text search
- Reminders

### Phase 3: AI Integration
- Embeddings with pgvector
- Semantic search
- Cross-referencing
- AI summarization

### Phase 4: Collaboration
- Scribes Circles (study groups)
- Sharing permissions
- Activity feeds

## 🔧 Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/user-authentication
```

### 2. Define Model
```python
# app/models/user.py
class User(BaseModel):
    __tablename__ = "users"
    email = Column(String, unique=True, index=True)
    # ...
```

### 3. Create Migration
```bash
alembic revision --autogenerate -m "add users table"
alembic upgrade head
```

### 4. Create Schemas
```python
# app/schemas/user.py
class UserCreate(BaseSchema):
    email: str
    password: str
```

### 5. Create Repository
```python
# app/repositories/user_repository.py
class UserRepository:
    async def create(self, db: AsyncSession, user_data: UserCreate):
        # Implementation
```

### 6. Create Service
```python
# app/services/auth_service.py
class AuthService:
    async def register(self, user_data: UserCreate):
        # Business logic
```

### 7. Create Routes
```python
# app/api/auth.py
@router.post("/register")
async def register(user_data: UserCreate):
    # Route handler
```

### 8. Write Tests
```python
# app/tests/test_auth.py
async def test_register(client):
    # Test implementation
```

### 9. Run Tests & Commit
```bash
pytest
git add .
git commit -m "feat: add user registration"
```

## 📝 Code Style Guidelines

### Python Style:
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for all public functions

### Naming:
- Classes: PascalCase (e.g., `UserRepository`)
- Functions: snake_case (e.g., `create_user`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_PAGE_SIZE`)
- Private: prefix with `_` (e.g., `_internal_helper`)

### Imports Order:
1. Standard library
2. Third-party packages
3. Local application imports

### Commit Messages:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

---

**Ready to build something amazing! 🚀**
