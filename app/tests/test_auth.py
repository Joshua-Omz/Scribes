"""
Test authentication endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User
from app.core.security import hash_password, create_verification_token


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "Test1234!",
            "full_name": "Test User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    """Test registration with duplicate email."""
    # Create first user
    await client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "Test1234!"
        }
    )
    
    # Try to create second user with same email
    response = await client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Test registration with duplicate username."""
    # Create first user
    await client.post(
        "/auth/register",
        json={
            "email": "user1@example.com",
            "username": "sameusername",
            "password": "Test1234!"
        }
    )
    
    # Try to create second user with same username
    response = await client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "username": "sameusername",
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Test registration with weak password."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "weak"
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # Register user first
    await client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "Test1234!"
        }
    )
    
    # Login
    response = await client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password."""
    # Register user
    await client.post(
        "/auth/register",
        json={
            "email": "wrong@example.com",
            "username": "wronguser",
            "password": "Test1234!"
        }
    )
    
    # Try login with wrong password
    response = await client.post(
        "/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "WrongPassword1!"
        }
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user."""
    response = await client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Test getting current user profile."""
    # Register and login
    await client.post(
        "/auth/register",
        json={
            "email": "current@example.com",
            "username": "currentuser",
            "password": "Test1234!"
        }
    )
    
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "current@example.com",
            "password": "Test1234!"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == "current@example.com"
    assert data["username"] == "currentuser"


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test getting current user without token."""
    response = await client.get("/auth/me")
    
    assert response.status_code == 403  # No credentials provided


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token."""
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Test refreshing access token."""
    # Register and login
    await client.post(
        "/auth/register",
        json={
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "Test1234!"
        }
    )
    
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "refresh@example.com",
            "password": "Test1234!"
        }
    )
    
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_verify_email(client: AsyncClient):
    """Test email verification."""
    # Register user
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "verify@example.com",
            "username": "verifyuser",
            "password": "Test1234!"
        }
    )
    
    # Create verification token
    verification_token = create_verification_token("verify@example.com")
    
    # Verify email
    response = await client.post(
        "/auth/verify-email",
        json={"token": verification_token}
    )
    
    assert response.status_code == 200
    assert "verified successfully" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient):
    """Test forgot password request."""
    # Register user
    await client.post(
        "/auth/register",
        json={
            "email": "forgot@example.com",
            "username": "forgotuser",
            "password": "Test1234!"
        }
    )
    
    # Request password reset
    response = await client.post(
        "/auth/forgot-password",
        json={"email": "forgot@example.com"}
    )
    
    assert response.status_code == 200
    assert "reset email sent" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client: AsyncClient):
    """Test forgot password with non-existent email."""
    # Should still return success to prevent email enumeration
    response = await client.post(
        "/auth/forgot-password",
        json={"email": "nonexistent@example.com"}
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient):
    """Test changing password."""
    # Register and login
    await client.post(
        "/auth/register",
        json={
            "email": "change@example.com",
            "username": "changeuser",
            "password": "OldPassword1!"
        }
    )
    
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "change@example.com",
            "password": "OldPassword1!"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Change password
    response = await client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "OldPassword1!",
            "new_password": "NewPassword1!"
        }
    )
    
    assert response.status_code == 200
    assert "changed successfully" in response.json()["message"].lower()
    
    # Verify new password works
    new_login_response = await client.post(
        "/auth/login",
        json={
            "email": "change@example.com",
            "password": "NewPassword1!"
        }
    )
    
    assert new_login_response.status_code == 200


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout functionality."""
    # Register and login
    await client.post(
        "/auth/register",
        json={
            "email": "logout@example.com",
            "username": "logoutuser",
            "password": "Test1234!"
        }
    )
    
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "logout@example.com",
            "password": "Test1234!"
        }
    )
    
    token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]
    
    # Logout
    response = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()
