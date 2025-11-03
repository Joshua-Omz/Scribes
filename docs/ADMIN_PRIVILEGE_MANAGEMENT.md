# Admin Privilege Management - Implementation Guide

**Date:** November 3, 2025  
**Status:** ✅ Fully Implemented

## 🎯 Overview

A complete admin privilege management system has been implemented with the following capabilities:
- Create new admin users
- Update user roles (user ↔ admin)
- Update superuser status (true ↔ false)
- Update multiple privileges at once
- Self-demotion protection

## 📋 Available Endpoints

### 1. **Create Admin User**
**POST** `/auth/admin/users`

Creates a new user with admin role and optionally superuser status.

**Authentication:** Required (Admin only)

**Request Body:**
```json
{
  "email": "admin@example.com",
  "username": "adminuser",
  "full_name": "Admin User",
  "password": "SecurePass123"
}
```

**Query Parameters:**
- `is_superuser` (boolean, default: true) - Whether user should be superuser

**Response:** `201 Created`
```json
{
  "id": 5,
  "email": "admin@example.com",
  "username": "adminuser",
  "full_name": "Admin User",
  "role": "admin",
  "is_active": true,
  "is_superuser": true,
  "is_verified": false,
  "created_at": "2025-11-03T12:00:00",
  "updated_at": null
}
```

**Errors:**
- `400` - Email already registered or username taken
- `401` - Not authenticated
- `403` - Not admin

---

### 2. **Update User Role**
**PATCH** `/auth/admin/users/{user_id}/role`

Changes a user's role between "user" and "admin".

**Authentication:** Required (Admin only)

**Path Parameters:**
- `user_id` (integer) - ID of user to update

**Query Parameters:**
- `role` (string, required) - New role: "user" or "admin"

**Example:**
```
PATCH /auth/admin/users/3/role?role=admin
```

**Response:** `200 OK`
```json
{
  "id": 3,
  "email": "user@example.com",
  "username": "regularuser",
  "role": "admin",
  "is_active": true,
  "is_superuser": false,
  ...
}
```

**Errors:**
- `400` - Invalid role or attempting self-demotion
- `401` - Not authenticated
- `403` - Not admin
- `404` - User not found

---

### 3. **Update Superuser Status**
**PATCH** `/auth/admin/users/{user_id}/superuser`

Toggles a user's superuser status.

**Authentication:** Required (Admin only)

**Path Parameters:**
- `user_id` (integer) - ID of user to update

**Query Parameters:**
- `is_superuser` (boolean, required) - New superuser status

**Example:**
```
PATCH /auth/admin/users/3/superuser?is_superuser=true
```

**Response:** `200 OK`
```json
{
  "id": 3,
  "email": "user@example.com",
  "username": "regularuser",
  "role": "user",
  "is_active": true,
  "is_superuser": true,
  ...
}
```

**Errors:**
- `400` - Attempting self-demotion
- `401` - Not authenticated
- `403` - Not admin
- `404` - User not found

---

### 4. **Update Multiple Privileges**
**PATCH** `/auth/admin/users/{user_id}/privileges`

Updates multiple user privileges in a single request.

**Authentication:** Required (Admin only)

**Path Parameters:**
- `user_id` (integer) - ID of user to update

**Query Parameters:** (at least one required)
- `role` (string, optional) - New role: "user" or "admin"
- `is_superuser` (boolean, optional) - Superuser status
- `is_active` (boolean, optional) - Active status

**Example:**
```
PATCH /auth/admin/users/3/privileges?role=admin&is_superuser=true&is_active=true
```

**Response:** `200 OK`
```json
{
  "id": 3,
  "email": "user@example.com",
  "username": "regularuser",
  "role": "admin",
  "is_active": true,
  "is_superuser": true,
  ...
}
```

**Errors:**
- `400` - Invalid parameters or attempting self-demotion
- `401` - Not authenticated
- `403` - Not admin
- `404` - User not found

---

## 🚀 How to Use

### Method 1: Via Swagger UI (Recommended for Testing)

1. **Start your server:**
   ```powershell
   cd "c:\flutter proj\Scribes\backend2"
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open Swagger UI:**
   - Go to: http://localhost:8000/docs

3. **Login as Admin:**
   - Use `POST /auth/login` to get access token
   - Click "Authorize" button at top right
   - Paste token in format: `Bearer your-token-here`
   - Click "Authorize"

4. **Use Admin Endpoints:**
   - Scroll to "Authentication" section
   - Find the admin endpoints (marked with 🔒)
   - Test them with the forms

### Method 2: Via cURL

#### Create Admin User:
```bash
curl -X POST "http://localhost:8000/auth/admin/users?is_superuser=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newadmin@example.com",
    "username": "newadmin",
    "full_name": "New Admin",
    "password": "SecurePass123"
  }'
```

#### Promote User to Admin:
```bash
curl -X PATCH "http://localhost:8000/auth/admin/users/3/role?role=admin" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Make User Superuser:
```bash
curl -X PATCH "http://localhost:8000/auth/admin/users/3/superuser?is_superuser=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Update Multiple Privileges:
```bash
curl -X PATCH "http://localhost:8000/auth/admin/users/3/privileges?role=admin&is_superuser=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔒 Security Features

### 1. Admin-Only Access
All endpoints require `get_current_admin_user` dependency, which checks:
- User must be authenticated
- User must be active
- User must have `role="admin"` OR `is_superuser=True`

### 2. Self-Demotion Protection
Admins cannot:
- Change their own role from "admin" to "user"
- Set their own `is_superuser` to `false`

This prevents accidental lockouts.

### 3. Input Validation
- Role must be exactly "user" or "admin"
- At least one privilege must be specified for multi-update
- Email and username uniqueness checked

---

## 🎯 Bootstrap First Admin

If you don't have any admin users yet, you need to create one manually:

### Option 1: Direct Database Update (SQL)

```sql
-- Connect to your database
psql -U postgres -d scribes_db

-- Update existing user to admin
UPDATE users 
SET role = 'admin', is_superuser = true 
WHERE email = 'your-email@example.com';

-- Verify
SELECT id, email, username, role, is_superuser FROM users WHERE role = 'admin';
```

### Option 2: Python Script

Create `bootstrap_admin.py`:

```python
"""Bootstrap first admin user."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user_model import User

async def create_first_admin():
    """Create or update first admin user."""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get user by email
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.role = "admin"
            user.is_superuser = True
            print(f"✅ Updated {user.email} to admin with superuser")
        else:
            # Create new admin
            from app.core.security import hash_password
            user = User(
                email="admin@example.com",
                username="admin",
                full_name="System Admin",
                hashed_password=hash_password("ChangeMe123"),
                role="admin",
                is_superuser=True,
                is_active=True,
                is_verified=True
            )
            session.add(user)
            print(f"✅ Created new admin: {user.email}")
        
        await session.commit()
        print(f"   ID: {user.id}")
        print(f"   Role: {user.role}")
        print(f"   Superuser: {user.is_superuser}")

if __name__ == "__main__":
    asyncio.run(create_first_admin())
```

Run it:
```powershell
python bootstrap_admin.py
```

### Option 3: Via Existing Registration

1. Register a regular user
2. Manually update database to make them admin
3. Use that admin to create more admins via API

---

## 📊 User Roles and Permissions

### Role: `user` (Default)
- Access to own data
- Cannot manage other users
- Cannot access admin endpoints

### Role: `admin`
- Access to admin endpoints
- Can view all users
- Can create admin users
- Can update user privileges
- Cannot demote self

### Superuser Status: `is_superuser=true`
- Highest level of access
- Can be combined with any role
- Checked by `get_current_admin_user` dependency
- Cannot remove own superuser status

### Combined Permissions:

| Role | Superuser | Can Access Admin Endpoints |
|------|-----------|----------------------------|
| user | false | ❌ No |
| user | true | ✅ Yes |
| admin | false | ✅ Yes |
| admin | true | ✅ Yes |

---

## 🧪 Testing Checklist

- [ ] Create first admin user (bootstrap)
- [ ] Login as admin and get access token
- [ ] Create new admin user via API
- [ ] Promote regular user to admin
- [ ] Grant superuser status to user
- [ ] Try to demote self (should fail)
- [ ] Update multiple privileges at once
- [ ] Verify admin endpoints reject non-admin users
- [ ] Check that email/username validation works

---

## 🐛 Troubleshooting

### Error: "Not enough permissions"
**Solution:** Your user needs either:
- `role="admin"`, OR
- `is_superuser=true`

Update database:
```sql
UPDATE users SET role='admin', is_superuser=true WHERE email='your-email@example.com';
```

### Error: "Cannot demote yourself from admin role"
**Solution:** This is intentional! You cannot remove your own admin privileges. Use another admin account to demote users.

### Error: "Email already registered"
**Solution:** Email must be unique. Use a different email address.

### Error: "User not found"
**Solution:** Check that the `user_id` in the URL is correct.

---

## 📝 Database Schema

The User model supports these admin-related fields:

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")          # "user" or "admin"
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # Elevated permissions
    is_verified = Column(Boolean, default=False)
    # ... other fields
```

No migration needed - these fields already exist!

---

## 🎓 Best Practices

### 1. Use Principle of Least Privilege
- Don't make everyone a superuser
- Only grant admin role when needed
- Regular users should have `role="user"`

### 2. Create Multiple Admins
- Don't rely on a single admin account
- Create backup admin accounts
- Prevents lockout if one admin leaves

### 3. Audit Admin Actions
- Log all privilege changes
- Monitor who creates admin users
- Track role modifications

### 4. Secure Admin Credentials
- Use strong passwords for admin accounts
- Enable 2FA when available
- Rotate admin passwords regularly

### 5. Test in Development First
- Use Swagger UI to test endpoints
- Verify self-demotion protection works
- Check all error cases

---

## 📚 Related Documentation

- `docs/VERIFICATION_TOKEN_EXPLANATION.md` - Email verification flow
- `docs/EMAIL_TROUBLESHOOTING.md` - Email setup guide
- `docs/AUTH_FLOW.md` - Authentication architecture
- `README.md` - Project setup and overview

---

## ✅ Summary

**Implemented Features:**
- ✅ Create admin users via API
- ✅ Update user roles (user ↔ admin)
- ✅ Update superuser status
- ✅ Update multiple privileges at once
- ✅ Self-demotion protection
- ✅ Admin-only access control
- ✅ Input validation
- ✅ Comprehensive error handling

**Files Modified:**
- `app/repositories/user_repository.py` - Added admin management methods
- `app/api/auth_routes.py` - Added 4 new admin endpoints
- `app/core/dependencies.py` - Already had `get_current_admin_user` dependency

**API Endpoints Added:**
1. `POST /auth/admin/users` - Create admin user
2. `PATCH /auth/admin/users/{user_id}/role` - Update role
3. `PATCH /auth/admin/users/{user_id}/superuser` - Update superuser
4. `PATCH /auth/admin/users/{user_id}/privileges` - Update multiple privileges

**Status:** ✅ Fully implemented and ready to use!

---

**Next Steps:**
1. Bootstrap your first admin user
2. Test endpoints in Swagger UI
3. Create additional admin accounts
4. Integrate with your frontend

