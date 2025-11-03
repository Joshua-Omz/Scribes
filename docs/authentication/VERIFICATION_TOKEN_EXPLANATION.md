# Email Verification Token vs Access Token - Understanding the Difference

## 🔴 The Issue: "Invalid Token Type"

You're getting this error because you're using the **access token** (JWT authentication token) instead of the **verification token**.

### Two Different Token Types:

| Token Type | Purpose | Where to Get It | Format |
|------------|---------|-----------------|--------|
| **Access Token** | API authentication | Login response | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (type: "access") |
| **Verification Token** | Email verification | Registration email | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (type: "verification") |

## ✅ Correct Flow

### 1. Register a New User

**POST** `/auth/register`

```json
{
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "role": "user",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,  // ← Not verified yet
  "created_at": "2025-11-01T12:00:00",
  "updated_at": null
}
```

### 2. Check Your Email

After registration, a **verification email** is sent to your inbox with a link like:

```
http://localhost:3000/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzMwNTU4NDAwLCJ0eXBlIjoidmVyaWZpY2F0aW9uIn0.xxx
```

The token in the URL is the **verification token**.

### 3. Verify Email

**POST** `/auth/verify-email`

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzMwNTU4NDAwLCJ0eXBlIjoidmVyaWZpY2F0aW9uIn0.xxx"
}
```

**Response:**
```json
{
  "message": "Email verified successfully",
  "detail": "You can now access all features"
}
```

## 🔍 Token Comparison

### Access Token Payload:
```json
{
  "sub": "1",              // User ID
  "email": "test@example.com",
  "role": "user",
  "exp": 1730558400,
  "type": "access"         // ← Type is "access"
}
```

### Verification Token Payload:
```json
{
  "sub": "test@example.com",  // Email (not ID)
  "exp": 1730558400,
  "type": "verification"      // ← Type is "verification"
}
```

## ❌ What You're Doing Wrong

You're trying to use the **access token** (from login) for email verification:

```json
{
  "token": "eyJ...access_token..."  // ← This has type: "access"
}
```

The backend checks:
```python
if payload.get("type") != "verification":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token type"  // ← This error!
    )
```

## 🎯 Solution Options

### Option 1: Check Your Email (Production Flow)

1. Register a new user
2. Check the email inbox for verification email
3. Copy the token from the email link
4. Use that token for verification

### Option 2: For Testing - Return Token in Registration Response

Since you're in development and need to test without checking email, we can modify the registration endpoint to return the verification token.

**I can add a development-only endpoint that returns the verification token for testing purposes.**

Would you like me to:
1. Add a debug endpoint to retrieve verification tokens?
2. Modify the registration response to include the token (dev mode only)?
3. Show you how to extract the token from the verification email?

## 🧪 Testing Without Email

If you want to test verification without checking email, here's a workaround:

### Current Behavior:
When you register, the verification token is created but only sent via email.

### Development Solution:
Add debug logging to see the token in the console:

**In `app/services/auth_service.py`, line 77:**
```python
# Generate verification token
verification_token = create_verification_token(user.email)

# DEBUG: Print token for testing (remove in production!)
if settings.debug:
    print(f"\n{'='*60}")
    print(f"🔑 VERIFICATION TOKEN (DEV ONLY)")
    print(f"{'='*60}")
    print(f"Email: {user.email}")
    print(f"Token: {verification_token}")
    print(f"{'='*60}\n")

# Send verification email (async, non-blocking)
```

Then when you register, you'll see the token in the console output!

## 📝 Quick Test Commands

### 1. Register User:
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "SecurePass123"
  }'
```

### 2. Check Console for Verification Token

Look for output like:
```
============================================================
🔑 VERIFICATION TOKEN (DEV ONLY)
============================================================
Email: test@example.com
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
============================================================
```

### 3. Verify Email with Token:
```bash
curl -X POST "http://localhost:8000/auth/verify-email" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

## 🔐 Security Note

**Never return sensitive tokens in API responses in production!**

The verification token should only be:
- Sent via email (production)
- Logged to console (development only)
- Never included in API responses

---

**Next Steps:**
1. Check your email for the verification link
2. OR add debug logging to see the token in the console
3. OR I can create a development-only endpoint to retrieve tokens for testing

Which approach would you prefer?
