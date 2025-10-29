"""
Test health check endpoint.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns expected response."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_check_structure(client: AsyncClient):
    """Test health check response structure matches schema."""
    response = await client.get("/health")
    data = response.json()
    
    required_fields = ["status", "app_name", "version", "environment", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
