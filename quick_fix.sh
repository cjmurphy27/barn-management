#!/bin/bash
echo "🔧 Fixing syntax error..."

# Completely rewrite main.py to fix the broken string
cat > app/main.py << 'MAINPY'
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging
import time
from typing import Dict, Any

# Import your modules
from app.core.config import get_settings
from app.core.auth import get_current_user, get_current_user_optional, User
from app.api.horses import router as horses_router
from app.api.ai import router as ai_router
from app.database import get_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    # Startup
    logger.info("Starting Barn Lady application...")
    settings = get_settings()
    logger.info(f"Application: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Check PropelAuth configuration
    if settings.PROPELAUTH_URL and settings.PROPELAUTH_API_KEY:
        logger.info("PropelAuth authentication enabled")
    else:
        logger.warning("PropelAuth not configured - running in development mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Barn Lady application...")

# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Multi-Barn Horse Management System with AI Assistant and Authentication",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for production
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
        )
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Include routers
    app.include_router(horses_router)
    app.include_router(ai_router)
    
    return app

# Create app instance
app = create_app()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    settings = get_settings()
    return {
        "message": f"Welcome to {settings.APP_NAME} with Multi-Barn Support",
        "version": settings.APP_VERSION,
        "features": [
            "Multi-Barn Horse Management", 
            "AI Analysis", 
            "Care Recommendations",
            "PropelAuth Authentication",
            "Organization-based Access Control"
        ],
        "docs": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check(db = Depends(get_db)):
    """Health check endpoint to verify API and database connectivity"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        settings = get_settings()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "ai_service": "available",
            "authentication": "enabled" if settings.PROPELAUTH_URL else "development_mode",
            "version": settings.APP_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "timestamp": time.time(),
                "database": "disconnected",
                "error": str(e)
            }
        )

# Authentication endpoints  
@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user_optional)):
    """Get current user information"""
    if not current_user:
        return {
            "authenticated": False, 
            "message": "No authentication token provided",
            "auth_required": True
        }
    
    return {
        "authenticated": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "organizations": current_user.organizations,
        "current_org_id": current_user.current_org_id,
        "current_org": current_user.get_current_org()
    }

@app.get("/api/v1/auth/status")
async def get_auth_status():
    """Get authentication system status"""
    settings = get_settings()
    
    return {
        "authentication_enabled": bool(settings.PROPELAUTH_URL and settings.PROPELAUTH_API_KEY),
        "propelauth_url": settings.PROPELAUTH_URL,
        "development_mode": not bool(settings.PROPELAUTH_URL and settings.PROPELAUTH_API_KEY),
        "version": settings.APP_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
MAINPY

echo "✅ Fixed main.py"
echo "🔄 Restarting API..."
docker-compose restart api

sleep 5
echo "🧪 Testing..."
curl -s http://localhost:8000/health
echo ""
echo "🎉 Should be working now!"
