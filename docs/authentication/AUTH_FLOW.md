## Authentication — architecture, data flow & troubleshooting

This document describes how authentication is implemented in the backend (models, services, routes, and token lifecycle). It also includes concrete troubleshooting steps for the SQLAlchemy
InvalidRequestError that occurs when a model relationship (for example `User -> UserProfile`) cannot be resolved during mapper initialization.

Files referenced
- `app/core/security.py` — password hashing and JWT helpers
- `app/services/auth_service.py` — business logic for register/login/refresh/reset/verify/logout
- `app/api/auth_routes.py` — FastAPI endpoints
- `app/repositories/user_repository.py` — data access for `User`
- `app/models/user_model.py` and `app/models/refresh_model.py` — DB models
- `README.md` — project-level setup and usage
- `docs/` — other documentation

If you need the quick project README, see `README.md` at the repository root or the `docs/` folder for additional guides.

---

## High-level overview

- Clients (web/mobile) register and login using the REST API exposed by FastAPI.
- Passwords are hashed with bcrypt. Tokens are JWTs signed with the app secret.
- There are 3 token types used by the system: `access`, `refresh`, and short-lived `verification` / `reset` tokens for email verification and password reset flows.
- Refresh tokens are persisted in the database (refresh_tokens table) so they can be revoked or rotated.

Core responsibilities by layer:

- Models: database structure (User, RefreshToken, etc.)
- Repositories: db queries and persistence logic
- Services: business rules (checking duplicates, hashing, token creation, email sends)
- API routes: request/response wiring, dependency injection for auth
- Security utilities: token encode/decode, hashing

---

## Data shapes (important fields)

- User (table `users`)
  - id: int
  - email: str (unique)
  - username: str (unique)
  - hashed_password: str
  - full_name: Optional[str]
  - role: str ("user"|"admin")
  - is_active: bool
  - is_verified: bool
  - created_at / updated_at

- RefreshToken (table `refresh_tokens`)
  - id: int
  - token: str (JWT string) - unique
  - user_id: int (FK -> users.id)
  - expires_at: datetime
  - revoked: bool

---

## Typical request flows

1) Register
   - Endpoint: POST `/auth/register` with `UserCreate` (email, username, password, optional full_name)
   - Service: `AuthService.register()`
     - Check duplicate email/username via `UserRepository`
     - Hash password (bcrypt)
     - Create user record
     - Create verification token (JWT with type `verification`)
     - Trigger verification email send (non-blocking)
   - Response: `UserResponse` (user data without password)

2) Login
   - Endpoint: POST `/auth/login` with `LoginRequest` (email, password)
   - Service: `AuthService.login()`
     - Fetch user by email
     - Verify password with `verify_password()`
     - Ensure `is_active` true
     - Create access token (JWT, type `access`) and refresh token (JWT, type `refresh`)
     - Persist refresh token in `refresh_tokens` table (expires_at + revoked False)
   - Response: `TokenResponse` (access_token, refresh_token, token_type, expires_in)

3) Accessing protected endpoints
   - FastAPI dependency: `get_current_user` uses `HTTPBearer` to get token
   - Decodes JWT via `decode_token()` and verifies `type == "access"`
   - Extracts `sub` (user id) from token and loads User from DB
   - Additional dependencies: `get_current_active_user`, `get_current_verified_user`, `get_current_admin_user`

4) Refreshing access token
   - Endpoint: POST `/auth/refresh` with the `refresh_token` in body
   - Service: `AuthService.refresh_access_token()`
     - Decode JWT and verify `type == "refresh"`
     - Look up refresh token record in DB and ensure not revoked
     - Issue a new access token

5) Password reset & verification
   - Forgot password: `AuthService.forgot_password()` creates reset token and sends email; response is always success to prevent enumeration
   - Reset password: `AuthService.reset_password(token, new_password)` decodes token (`type == "reset"`), updates hashed password and revokes existing refresh tokens for that user
   - Verify email: `AuthService.verify_email(token)` decodes token (`type == "verification"`) and sets `is_verified = True`

6) Logout
   - Endpoint: POST `/auth/logout` with body containing refresh_token
   - Service: `AuthService.revoke_refresh_token()` marks refresh token record as `revoked = True`

---

## Token lifecycle and security notes

- Access token
  - Short lived (configurable, default ~30 minutes)
  - Stored client-side (e.g., in memory or secure cookie)
  - Contains `sub` (user id), `email`, `role`, `type: access`, and `exp`

- Refresh token
  - Longer lived (configurable, default ~7 days)
  - Persisted in DB so it can be revoked
  - Contains `sub` (user id) and `type: refresh`

- Verification / Reset tokens
  - Short lived (verification default 24 hours, reset default 1 hour)
  - Contain `sub` set to email and `type` field set accordingly

Security best-practices implemented
- BCrypt for password hashing (via `passlib`)
- JWT token signing using `settings.jwt_secret_key` and algorithm `HS256`
- Refresh tokens persisted and revocation supported
- Password reset endpoints avoid email enumeration

---

## Troubleshooting: SQLAlchemy InvalidRequestError for relationships

Problem you reported (example message):

"sqlalchemy.exc.InvalidRequestError: Could not resolve relationship property reference 'UserProfile' on mapper 'User'. This indicates that `UserProfile` was not present / not imported when the User mapper was configured."

Root causes
- The referenced related model class (e.g. `UserProfile`) is not defined anywhere in `app.models`.
- The class exists but the module defining it wasn't imported before SQLAlchemy configured/mapped the `User` model. SQLAlchemy maps classes when they are imported/defined; if `User` is mapped before `UserProfile` exists, a non-string reference or eager-resolution can fail.

Fixes (concrete, apply one or more):

1) Use string form for relationships (safe for import order)

   Example (already used in `app/models/user_model.py`):

   profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete")

   - Using the class name as a string defers resolution until mappers are configured. If you already have a string and still see the error, check steps 2 and 3.

2) Ensure the referenced model file exists and defines the class

   - Create `app/models/user_profile.py` with a `UserProfile` class (if it doesn't exist). Example skeleton:

     ```py
     from sqlalchemy import Column, Integer, String, ForeignKey
     from sqlalchemy.orm import relationship
     from app.core.database import Base

     class UserProfile(Base):
         __tablename__ = "user_profiles"
         id = Column(Integer, primary_key=True)
         user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
         bio = Column(String, nullable=True)
         # backref/back_populates for User
         user = relationship("User", back_populates="profile")
     ```

3) Ensure model modules are imported before mapper configuration / app startup that uses models

   - The simplest robust approach: import all model modules from `app/models/__init__.py` so that when `app.models` is imported all models are registered with SQLAlchemy declarative base.

   Example `app/models/__init__.py`:

   ```py
   # Import models so SQLAlchemy registers them when the package is imported
   from .user_model import User
   from .refresh_model import RefreshToken
   from .user_profile import UserProfile
   # ... import other models referenced across the project

   __all__ = [
       "User",
       "RefreshToken",
       "UserProfile",
       # ...
   ]
   ```

   - Make sure nothing in your code imports models with circular import patterns. Importing the `app.models` package early in `app/main.py` (or before you run migrations or create metadata) ensures all classes are mapped.

4) Avoid early use of mapped classes before all modules are imported

   - If you call `Base.metadata.create_all()` or any code that triggers mapper configuration before importing related model modules, move that call after model imports.

5) As final safeguard — use deferred configuration

   - If you have a complex import graph, keep relationship targets as strings and centralize model imports (as above). Avoid importing repository/service modules at module import time in models.

Example checklist to resolve the issue now

1. Confirm `app/models/user_profile.py` exists and defines `UserProfile`.
2. Add the import to `app/models/__init__.py` as shown above.
3. In `app/main.py` ensure you import `app.models` (or `from app import models`) once at startup so mapping is done before routes/services use models.
4. Re-run tests / start the app. The InvalidRequestError should be resolved.

If you prefer a minimal patch, create `app/models/__init__.py` and import the existing model modules. This is low-risk and usually fixes mapping issues.

---

## Diagnostics commands & quick checks

- To find which models are present, inspect the `app/models` folder and confirm each referenced name exists.
- To run tests locally (PowerShell):

```powershell
# from repository root
pytest -q
```

- If using Alembic and you changed models, create a migration:

```powershell
alembic revision --autogenerate -m "register user_profile and other missing models"
alembic upgrade head
```

---

## Summary & next steps

- Authentication is implemented across models, services, and routes as described in this document.
- If you see the mapper `InvalidRequestError` for `UserProfile`:
  - prefer adding a `user_profile.py` model if it is missing,
  - or centralize imports in `app/models/__init__.py` and import `app.models` early in `app/main.py`.
- This document links to `README.md` and other `docs/` files in this repository for setup and run instructions.

If you want, I can:
- create a minimal `app/models/__init__.py` that imports all existing models, or
- add the missing `UserProfile` model skeleton and a unit test demonstrating mapping.

---

End of document.
