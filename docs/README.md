# 📚 Scribes Backend Documentation

Welcome to the Scribes Backend API documentation. This guide will help you navigate the documentation structure and find what you need quickly.

## 📁 Documentation Structure

```
docs/
├── README.md (you are here)
├── authentication/     # Authentication & verification docs
├── email/             # Email configuration & troubleshooting
├── admin/             # Admin features & user management
├── database/          # Database schema & models
├── guides/            # Getting started & tutorials
└── troubleshooting/   # Status reports & issue tracking
```

---

## 🚀 Quick Start

**New to the project?** Start here:
- [Getting Started Guide](guides/GETTING_STARTED.md) - Initial setup and first steps

**Setting up authentication?**
- [Authentication Setup Guide](authentication/AUTH_SETUP_GUIDE.md) - Complete auth system setup
- [Authentication Flow](authentication/AUTH_FLOW.md) - How the auth system works

**Need to verify users?**
- [Existing User Verification](authentication/EXISTING_USER_VERIFICATION.md) - How to verify already registered users

---

## 🔐 Authentication Documentation

Located in: `docs/authentication/`

| Document | Description |
|----------|-------------|
| [AUTH_SETUP_GUIDE.md](authentication/AUTH_SETUP_GUIDE.md) | Complete guide to setting up the authentication system |
| [AUTH_FLOW.md](authentication/AUTH_FLOW.md) | Detailed explanation of authentication flows and token types |
| [FRONTEND_INTEGRATION_GUIDE.md](authentication/FRONTEND_INTEGRATION_GUIDE.md) | **Flutter frontend integration guide with complete examples** |
| [VERIFICATION_TOKEN_EXPLANATION.md](authentication/VERIFICATION_TOKEN_EXPLANATION.md) | Understanding verification vs access tokens |
| [VERIFICATION_TOKEN_ISSUE_FIX.md](authentication/VERIFICATION_TOKEN_ISSUE_FIX.md) | Troubleshooting verification token issues |
| [EXISTING_USER_VERIFICATION.md](authentication/EXISTING_USER_VERIFICATION.md) | How to get verification tokens for existing users |

**Key Topics:**
- JWT token types (access, refresh, verification, reset)
- Email verification flow
- Password reset flow
- Token expiration and renewal
- Resending verification emails

---

## 📧 Email Documentation

Located in: `docs/email/`

| Document | Description |
|----------|-------------|
| [EMAIL_TROUBLESHOOTING.md](email/EMAIL_TROUBLESHOOTING.md) | Complete guide to fixing email issues |
| [EMAIL_ISSUE_DIAGNOSIS.md](email/EMAIL_ISSUE_DIAGNOSIS.md) | Diagnosing email sending problems |

**Key Topics:**
- SMTP configuration (Gmail, Outlook, etc.)
- Gmail App Password setup
- SSL/TLS connection issues
- Testing email functionality
- Debug logging for emails

---

## 👑 Admin Documentation

Located in: `docs/admin/`

| Document | Description |
|----------|-------------|
| [ADMIN_PRIVILEGE_MANAGEMENT.md](admin/ADMIN_PRIVILEGE_MANAGEMENT.md) | Managing admin users and privileges |
| [GET_ALL_USERS_ENDPOINT.md](admin/GET_ALL_USERS_ENDPOINT.md) | User listing and management endpoints |

**Key Topics:**
- Creating admin users
- Bootstrap admin script
- Updating user roles
- Managing superuser status
- Admin-only endpoints
- User privilege management

**Quick Commands:**
```powershell
# Create first admin user
python bootstrap_admin.py your-email@example.com

# List all admins
python bootstrap_admin.py --list
```

---

## 🗄️ Database Documentation

Located in: `docs/database/`

| Document | Description |
|----------|-------------|
| [MODEL_SCHEMA_CREATION_SUMMARY.md](database/MODEL_SCHEMA_CREATION_SUMMARY.md) | How to create new models and schemas |
| [SCHEMA_CONSOLIDATION.md](database/SCHEMA_CONSOLIDATION.md) | Schema file organization strategy |
| [SCHEMA_FILE_CONSOLIDATION.md](database/SCHEMA_FILE_CONSOLIDATION.md) | Consolidating redundant schema files |
| [SQLALCHEMY_METADATA_FIX.md](database/SQLALCHEMY_METADATA_FIX.md) | Fixing SQLAlchemy metadata issues |

**Key Topics:**
- SQLAlchemy 2.0 async patterns
- Creating models and schemas
- Database migrations with Alembic
- Schema validation with Pydantic
- Fixing common database errors

---

## 📖 Guides

Located in: `docs/guides/`

| Document | Description |
|----------|-------------|
| [GETTING_STARTED.md](guides/GETTING_STARTED.md) | Complete getting started guide |

**Step-by-step tutorials for:**
- Initial project setup
- Running the development server
- Testing endpoints with Swagger UI
- Creating your first admin user
- Testing authentication flows

---

## 🔧 Troubleshooting

Located in: `docs/troubleshooting/`

| Document | Description |
|----------|-------------|
| [PROJECT_STATUS.md](troubleshooting/PROJECT_STATUS.md) | Current project status and known issues |
| [STATUS_OVERVIEW.md](troubleshooting/STATUS_OVERVIEW.md) | Overview of implementation status |

**Common Issues:**
- Authentication errors
- Email sending failures
- Database connection issues
- Token validation problems
- Schema validation errors

---

## 🎯 Common Tasks

### First Time Setup

1. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```powershell
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run Migrations**
   ```powershell
   alembic upgrade head
   ```

4. **Create Admin User**
   ```powershell
   python bootstrap_admin.py your-email@example.com
   ```

5. **Start Server**
   ```powershell
   python -m uvicorn app.main:app --reload
   ```

6. **Access Swagger UI**
   http://localhost:8000/docs

---

### Testing Authentication

1. **Register a new user** - `POST /auth/register`
2. **Check console** for verification token (if DEBUG=True)
3. **Verify email** - `POST /auth/verify-email`
4. **Login** - `POST /auth/login`
5. **Use access token** in Swagger UI "Authorize" button

---

### Managing Users as Admin

1. **Login as admin** - `POST /auth/login`
2. **Get access token** from response
3. **Authorize in Swagger** - Click "Authorize", paste token
4. **List users** - `GET /auth/users`
5. **Manage privileges** - Use admin endpoints under `/auth/admin/*`

---

### Verifying Existing Users

**Method 1: Resend Verification**
- `POST /auth/resend-verification` with user's email
- User receives new verification email
- Token printed to console if DEBUG=True

**Method 2: Admin Manual Verification**
- `POST /admin/verify-user/{user_id}` as admin
- Instantly verifies user without token

**Method 3: Database Direct**
- Only for development: `UPDATE users SET is_verified = true WHERE email = 'user@example.com';`

---

## 🛠️ Development Tools

### Swagger UI (Interactive API Docs)
**URL:** http://localhost:8000/docs
- Test all endpoints
- View request/response schemas
- Authorize with JWT tokens

### ReDoc (Alternative API Docs)
**URL:** http://localhost:8000/redoc
- Clean, searchable documentation
- Export as PDF or print

### Database Admin
**pgAdmin** or **DBeaver** for PostgreSQL management

---

## 📊 Project Architecture

```
Scribes Backend (FastAPI)
├── Authentication Layer
│   ├── JWT Tokens (4 types)
│   ├── Email Verification
│   └── Password Reset
├── Admin System
│   ├── Role-Based Access Control
│   ├── User Management
│   └── Privilege Management
├── Email System
│   ├── SMTP Configuration
│   ├── Email Templates
│   └── Async Sending
└── Database Layer
    ├── SQLAlchemy 2.0 Async
    ├── PostgreSQL
    └── Alembic Migrations
```

---

## 🔗 Important Links

- **Main README:** [../README.md](../README.md)
- **API Swagger Docs:** http://localhost:8000/docs
- **Architecture Overview:** [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **Admin Quick Start:** [../ADMIN_QUICK_START.md](../ADMIN_QUICK_START.md)

---

## 📝 Documentation Standards

When adding new documentation:

1. **Choose the right folder:**
   - `authentication/` - Auth, tokens, verification
   - `email/` - SMTP, email sending
   - `admin/` - User management, privileges
   - `database/` - Models, schemas, migrations
   - `guides/` - Tutorials, how-tos
   - `troubleshooting/` - Issues, fixes, status

2. **Use clear naming:**
   - Use UPPERCASE for doc names
   - Use descriptive names (not generic)
   - Include dates for status/issue docs

3. **Follow markdown structure:**
   - Use proper heading hierarchy (# → ## → ###)
   - Include code examples
   - Add emoji for better scanning 🎯
   - Include links to related docs

4. **Keep updated:**
   - Update docs when features change
   - Mark deprecated features clearly
   - Update this README when adding new docs

---

## 🤝 Contributing

When contributing to documentation:

1. **Update this README** if you add new docs
2. **Cross-reference** related documentation
3. **Test code examples** before committing
4. **Use consistent formatting** with existing docs
5. **Add to git** after changes

---

## 📬 Need Help?

- Check the appropriate folder above
- Search docs for keywords
- Review troubleshooting section
- Check Swagger UI for API reference

---

**Last Updated:** November 3, 2025

**Current Status:** ✅ Authentication system complete, Email working, Admin system operational
