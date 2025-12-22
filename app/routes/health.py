"""
Health check API routes.
Provides endpoint to verify application status.
"""

from datetime import datetime
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API is running and responsive"
)
async def health_check() -> HealthResponse:
    """
    Verify API health status.
    
    Returns:
        HealthResponse: Current application health status
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.utcnow()
    )
