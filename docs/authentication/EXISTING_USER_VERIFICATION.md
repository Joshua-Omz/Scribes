# Getting Verification Tokens for Existing Users

**Date:** November 3, 2025  
**Issue:** How to get verification tokens for users who already registered

## 🎯 Problem

You have existing users in your database who:
- Already registered (account exists)
- Haven't verified their email yet
- Need a verification token

## ✅ Solutions

### **Option 1: Resend Verification Email (Recommended)** 📧

**NEW ENDPOINT:** `POST /auth/resend-verification`

This endpoint generates a **new** verification token and sends it via email.

#### How to Use:

**In Swagger UI** (http://localhost:8000/docs):

```json
{
  "email": "existing-user@example.com"
}
```

**Response:**
```json
{
  "message": "If the email exists and is unverified, a verification email has been sent",
  "detail": "Check your inbox and spam folder"
}
```

#### What Happens:
1. ✅ Generates new verification token
2. ✅ Sends email to user
3. ✅ Prints token to console (development mode)
4. ✅ Prevents email enumeration (always returns success)

#### Get Token from Console:

In **development mode** (`DEBUG=True`), the token is printed to your server console:

```
======================================================================
🔑 RESENT VERIFICATION TOKEN (DEVELOPMENT MODE ONLY)
======================================================================
📧 Email: existing-user@example.com
🎫 Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
======================================================================
Use this token in POST /auth/verify-email
======================================================================
```

**Copy that token and use it!**

---

### **Option 2: Admin Manual Verification** 👑

**NEW ENDPOINT:** `POST /admin/verify-user/{user_id}`

Admin can manually verify any user without requiring a token.

#### Requirements:
- Must be logged in as admin
- Must have admin or superuser privileges

#### How to Use:

**In Swagger UI:**

1. Login as admin
2. Click "Authorize" and paste access token
3. Go to `POST /admin/verify-user/{user_id}`
4. Enter the user's ID
5. Execute

**Response:**
```json
{
  "id": 3,
  "email": "user@example.com",
  "username": "username",
  "is_verified": true,
  ...
}
```

#### What Happens:
- ✅ Immediately verifies the user
- ✅ No token needed
- ✅ No email sent
- ✅ Admin only

---

### **Option 3: Direct Database Update (Quick & Dirty)** 🔧

If you just need to verify a user quickly during development:

**SQL Command:**
```sql
UPDATE users 
SET is_verified = true 
WHERE email = 'user@example.com';
```

**Or using Python script:**

Create `verify_user.py`:
```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.core.config import settings
from app.models.user_model import User

async def verify_user(email: str):
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(
            update(User)
            .where(User.email == email.lower())
            .values(is_verified=True)
        )
        await session.commit()
        
        if result.rowcount > 0:
            print(f"✅ Verified user: {email}")
        else:
            print(f"❌ User not found: {email}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python verify_user.py user@example.com")
        sys.exit(1)
    
    asyncio.run(verify_user(sys.argv[1]))
```

Run it:
```powershell
python verify_user.py user@example.com
```

---

## 🧪 Testing Guide

### Test 1: Resend Verification Email

1. **Start server:**
   ```powershell
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Go to Swagger UI:** http://localhost:8000/docs

3. **Use POST `/auth/resend-verification`:**
   ```json
   {
     "email": "joshuaomisanya41@gmail.com"
   }
   ```

4. **Check console for token:**
   ```
   🔑 RESENT VERIFICATION TOKEN (DEVELOPMENT MODE ONLY)
   🎫 Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

5. **Copy token and verify:**
   ```json
   {
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }
   ```

### Test 2: Admin Manual Verification

1. **Login as admin** (you already bootstrapped yourself as admin!)

2. **Get your access token** from login response

3. **Click "Authorize"** in Swagger UI

4. **Find the user ID:**
   - Use `GET /auth/users` to list all users
   - Find the user you want to verify
   - Note their ID

5. **Use POST `/admin/verify-user/{user_id}`:**
   - Enter the user ID
   - Execute
   - User is now verified!

---

## 📊 Comparison Table

| Method | Token Required | Admin Only | Sends Email | Best For |
|--------|---------------|------------|-------------|----------|
| **Resend Verification** | ✅ Yes (new one) | ❌ No | ✅ Yes | Normal users |
| **Admin Manual Verify** | ❌ No | ✅ Yes | ❌ No | Quick admin fixes |
| **Database Update** | ❌ No | 🔧 Dev only | ❌ No | Development/testing |

---

## 🔄 Complete Flow Examples

### Example 1: User Lost Verification Email

**User:** "I never got my verification email!"

**Solution:**
1. User goes to app
2. User clicks "Resend verification email"
3. Frontend calls `POST /auth/resend-verification`
4. User receives new email with fresh token
5. User clicks link in email
6. Frontend extracts token from URL
7. Frontend calls `POST /auth/verify-email` with token
8. ✅ User verified!

### Example 2: Admin Helping User

**User:** "I can't find the verification email!"

**Solution:**
1. Admin logs into admin panel
2. Admin searches for user
3. Admin clicks "Verify User" button
4. Frontend calls `POST /admin/verify-user/{user_id}`
5. ✅ User verified immediately!

### Example 3: Development Testing

**Developer:** "I need to test with verified users"

**Solution:**
1. Register test user
2. Check console for token OR
3. Use resend endpoint OR
4. Run `python verify_user.py test@example.com`
5. ✅ User verified!

---

## 🔐 Security Notes

### Resend Verification Endpoint

**Good:**
- ✅ Always returns same message (prevents email enumeration)
- ✅ Generates fresh token each time
- ✅ Tokens expire after 24 hours
- ✅ Only works for unverified users

**Be Aware:**
- ⚠️ No rate limiting (add in production)
- ⚠️ Tokens printed to console in dev mode

### Admin Verify Endpoint

**Good:**
- ✅ Requires admin authentication
- ✅ Prevents self-demotion
- ✅ Validates user exists

**Be Aware:**
- ⚠️ Bypasses email verification
- ⚠️ Should be logged/audited

---

## 📝 API Reference

### POST `/auth/resend-verification`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "If the email exists and is unverified, a verification email has been sent",
  "detail": "Check your inbox and spam folder"
}
```

**Errors:**
- None (always returns 200 to prevent email enumeration)

---

### POST `/admin/verify-user/{user_id}`

**Authentication:** Required (Admin only)

**Path Parameters:**
- `user_id` (integer) - ID of user to verify

**Response:** `200 OK`
```json
{
  "id": 3,
  "email": "user@example.com",
  "username": "username",
  "is_verified": true,
  ...
}
```

**Errors:**
- `401` - Not authenticated
- `403` - Not admin
- `404` - User not found
- `400` - User already verified

---

## 🎯 Quick Commands

### Resend Verification (cURL)
```bash
curl -X POST "http://localhost:8000/auth/resend-verification" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Admin Verify User (cURL)
```bash
curl -X POST "http://localhost:8000/auth/admin/verify-user/3" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Check User Status (cURL)
```bash
curl -X GET "http://localhost:8000/auth/users" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🐛 Troubleshooting

### "User not found"
- Check email is spelled correctly
- Email is case-insensitive (stored as lowercase)
- User must exist in database

### "User email is already verified"
- User is already verified
- No action needed
- User can login normally

### Token not appearing in console
- Make sure `DEBUG=True` in `.env`
- Restart server after changing `.env`
- Check you're looking at correct terminal

### Email not received
- Check spam folder
- Email might take 1-2 minutes
- Verify SMTP settings are correct
- Check server console for email errors

---

## ✅ Summary

**For Existing Users, you have 3 ways to get verification tokens:**

1. **Best Method:** Use `POST /auth/resend-verification`
   - Sends new token via email
   - Prints token to console (dev mode)
   - User can verify normally

2. **Admin Method:** Use `POST /admin/verify-user/{user_id}`
   - Instant verification
   - No token needed
   - Admin only

3. **Dev Method:** Direct database update
   - Quick and simple
   - Development only
   - Not recommended for production

**All methods are now implemented and ready to use!** 🎉
