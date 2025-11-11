"""
FastAPI Application Entry Point
Main application factory and configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import close_db
from app.api.health import router as health_router
from app.api.auth_routes import router as auth_router
from app.api.note_routes import router as note_router
from app.api.cross_ref_routes import router as cross_ref_router
# Version 2 of semantic routes with ORM-native queries and automatic embeddings
from app.api.semantic_routes_v2 import router as semantic_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📍 Environment: {settings.app_env}")
    print(f"🔧 Debug mode: {settings.debug}")
    
    # Register event listeners for automatic embedding generation
    from app.models.events import register_note_events
    register_note_events()
    print("✅ Registered automatic embedding generation listeners")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    await close_db()
    print("✅ Database connections closed")


def create_application() -> FastAPI:
    """
    Application factory function.
    Creates and configures FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A spiritual knowledge and note organization system powered by AI",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(note_router)
    app.include_router(cross_ref_router)
    app.include_router(semantic_router)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Handle uncaught exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error" if settings.is_production else str(exc),
                "error_code": "INTERNAL_ERROR"
            }
        )
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
