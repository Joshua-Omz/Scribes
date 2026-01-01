# 🚀 Authentication System - Setup & Testing Guide

**Created:** October 29, 2025  
**Status:** ✅ Ready for Testing

---

## ✅ What's Been Implemented

### 1. **Pydantic Schemas** ✅
- `schemas/user.py` - User models (Create, Update, Response, PasswordChange)
- `schemas/auth.py` - Auth models (Login, Token, Verification, Reset)

### 2. **Repository Layer** ✅
- `repositories/user_repository.py` - Complete CRUD operations
  - create, get_by_id, get_by_email, get_by_username
  - update, update_password, verify_email
  - activate, deactivate, delete
  - list_users, count_users

### 3. **Service Layer** ✅
- `services/auth_service.py` - Complete business logic
  - register (with email verification)
  - login (with JWT tokens)
  - verify_email
  - refresh_access_token
  - forgot_password
  - reset_password
  - revoke_refresh_token

### 4. **API Routes** ✅
- `api/auth.py` - Full authentication endpoints
  - POST `/auth/register` - User registration
  - POST `/auth/login` - User login
  - POST `/auth/refresh` - Refresh access token
  - POST `/auth/verify-email` - Verify email
  - POST `/auth/forgot-password` - Request password reset
  - POST `/auth/reset-password` - Reset password
  - GET `/auth/me` - Get current user
  - PUT `/auth/me` - Update current user
  - POST `/auth/change-password` - Change password
  - POST `/auth/logout` - Logout (revoke refresh token)
  - DELETE `/auth/me` - Delete account

### 5. **Dependencies** ✅
- `core/dependencies.py` - Route protection middleware
  - get_current_user
  - get_current_active_user
  - get_current_verified_user
  - get_current_admin_user
  - get_optional_current_user

### 6. **Tests** ✅
- `tests/test_auth.py` - Comprehensive test coverage
  - Registration tests (success, duplicate email/username, weak password)
  - Login tests (success, wrong password, nonexistent user)
  - Token tests (current user, refresh, invalid token)
  - Email verification tests
  - Password reset tests
  - Password change tests
  - Logout tests

---

## 🗄️ Database Setup

### Step 1: Ensure PostgreSQL is Running

```powershell
# Check if PostgreSQL is running
Get-Service -Name postgresql*

# Start PostgreSQL if not running
Start-Service -Name postgresql-x64-14  # Adjust version number
```

### Step 2: Create Database

```powershell
# Using psql
psql -U postgres

# In psql prompt:
CREATE DATABASE scribes_db;
\q
```

Or using PowerShell:
```powershell
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -c "CREATE DATABASE scribes_db;"
```

### Step 3: Update .env File

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/scribes_db
JWT_SECRET_KEY=your-super-secret-key-change-this
```

Generate a secure JWT secret:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Create Migration

```powershell
# Navigate to project directory
cd "c:\flutter proj\Scribes\backend2"

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Create migration
alembic revision --autogenerate -m "add authentication tables"
```

### Step 5: Apply Migration

```powershell
# Apply migration to database
alembic upgrade head

# Verify tables were created
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d scribes_db -c "\dt"
```

You should see these tables:
- users
- refresh_tokens
- notes
- circles
- circle_members
- circle_notes
- reminders

---

## 🚀 Running the Application

### Start the Server

```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Start FastAPI server
python -m app.main
```

Or with uvicorn directly:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access API Documentation

Once the server is running:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🧪 Testing the Authentication Flow

### Using Swagger UI (http://localhost:8000/docs)

#### 1. Register a New User

**Endpoint:** `POST /auth/register`

```json
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "Test1234!",
  "full_name": "Test User"
}
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-10-29T12:00:00Z",
  "updated_at": "2025-10-29T12:00:00Z"
}
```

#### 2. Login

**Endpoint:** `POST /auth/login`

```json
{
  "email": "test@example.com",
  "password": "Test1234!"
}
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 3. Access Protected Endpoint

**Endpoint:** `GET /auth/me`

1. Click the 🔒 "Authorize" button at the top right of Swagger UI
2. Enter your access token (without "Bearer" prefix)
3. Click "Authorize"
4. Try the `/auth/me` endpoint

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-10-29T12:00:00Z",
  "updated_at": "2025-10-29T12:00:00Z"
}
```

---

## 🧪 Running Automated Tests

### Run All Tests

```powershell
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run only auth tests
pytest app/tests/test_auth.py -v
```

### Expected Test Results

All 15+ authentication tests should pass:
- ✅ test_register_success
- ✅ test_register_duplicate_email
- ✅ test_register_duplicate_username
- ✅ test_register_weak_password
- ✅ test_login_success
- ✅ test_login_wrong_password
- ✅ test_login_nonexistent_user
- ✅ test_get_current_user
- ✅ test_get_current_user_unauthorized
- ✅ test_get_current_user_invalid_token
- ✅ test_refresh_token
- ✅ test_verify_email
- ✅ test_forgot_password
- ✅ test_forgot_password_nonexistent_email
- ✅ test_change_password
- ✅ test_logout

---

## 📊 API Endpoints Summary

### Public Endpoints (No Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login user |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/verify-email` | Verify email with token |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| GET | `/health` | Health check |

### Protected Endpoints (Requires Authentication)

| Method | Endpoint | Description | Required |
|--------|----------|-------------|----------|
| GET | `/auth/me` | Get current user | Access token |
| PUT | `/auth/me` | Update current user | Access token + Active |
| POST | `/auth/change-password` | Change password | Access token + Active |
| POST | `/auth/logout` | Logout (revoke token) | Access token |
| DELETE | `/auth/me` | Delete account | Access token + Active |

---

## 🔐 Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### JWT Token Configuration
- **Access Token:** 30 minutes expiry
- **Refresh Token:** 7 days expiry
- **Algorithm:** HS256
- **Verification Token:** 24 hours expiry
- **Reset Token:** 1 hour expiry

### Security Best Practices Implemented
✅ Password hashing with bcrypt  
✅ JWT token-based authentication  
✅ Refresh token rotation  
✅ Email verification  
✅ Password reset with time-limited tokens  
✅ User account activation/deactivation  
✅ Role-based access control (user/admin)  
✅ Secure token storage in database  
✅ Token revocation on password change  
✅ Protection against email enumeration  

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Could not connect to database"

```powershell
# Check PostgreSQL service
Get-Service -Name postgresql*

# Verify DATABASE_URL in .env
# Verify database exists
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -l
```

### Issue: "Alembic cannot find app module"

This has been fixed in `alembic/env.py`. The project root is now added to Python path.

### Issue: "Table already exists"

```powershell
# Drop all tables and recreate
alembic downgrade base
alembic upgrade head
```

### Issue: "Invalid token" errors

- Ensure JWT_SECRET_KEY is set in .env
- Check token hasn't expired
- Verify token format: `Bearer <token>`

---

## 📈 Next Steps

### Completed ✅
- [x] User authentication system
- [x] JWT token management
- [x] Email verification flow
- [x] Password reset flow
- [x] Protected routes
- [x] Comprehensive tests

### Ready to Implement 🎯
1. **Notes Module** - CRUD for notes
2. **Circles Module** - Study groups
3. **Reminders Module** - Scheduled reminders
4. **Search Module** - Full-text search
5. **AI Integration** - Embeddings and cross-references

---

## 💡 Quick Testing Script

Save this as `test_auth.py` for manual testing:

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register
register_response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "demo@example.com",
        "username": "demouser",
        "password": "Demo1234!",
        "full_name": "Demo User"
    }
)
print("Register:", register_response.status_code)

# 2. Login
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "demo@example.com",
        "password": "Demo1234!"
    }
)
print("Login:", login_response.status_code)
tokens = login_response.json()

# 3. Get current user
me_response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {tokens['access_token']}"}
)
print("Get Me:", me_response.status_code)
print("User:", me_response.json())
```

Run with:
```powershell
python test_auth.py
```

---

**🎉 Authentication system is complete and ready for testing!**

Start the server and visit http://localhost:8000/docs to explore all endpoints.
