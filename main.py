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
    
    yield
    
    # Shutdown
    logger.info("Shutting down Barn Lady application...")

# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Horse Management System for Barn Operations with AI Assistant",
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
    app.include_router(ai_router)  # Add AI router
    
    return app

# Create app instance
app = create_app()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    settings = get_settings()
    return {
        "message": f"Welcome to {settings.APP_NAME} with AI Assistant",
        "version": settings.APP_VERSION,
        "features": ["Horse Management", "AI Analysis", "Care Recommendations"],
        "docs": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check(db = Depends(get_db)):
    """Health check endpoint to verify API and database connectivity"""
    try:
        # Test database connection - fixed for SQLAlchemy v2
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "ai_service": "available",
            "version": get_settings().APP_VERSION
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

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )

# API Information endpoints
@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "name": "Barn Lady API with AI",
        "version": get_settings().APP_VERSION,
        "endpoints": {
            "horses": "/api/v1/horses/",
            "ai_analysis": "/api/v1/ai/analyze-horse",
            "ai_questions": "/api/v1/ai/general-question",
            "ai_compare": "/api/v1/ai/compare-horses",
            "documentation": "/docs",
            "health_check": "/health"
        },
        "features": [
            "Horse management",
            "AI-powered health analysis", 
            "Intelligent care recommendations",
            "Horse comparison and insights",
            "Search and filtering",
            "RESTful API design",
            "Interactive documentation"
        ]
    }

@app.get("/api/v1/stats")
async def get_system_stats(db = Depends(get_db)):
    """Get basic system statistics"""
    try:
        from app.models.horse import Horse
        
        # Get basic counts
        total_horses = db.query(Horse).count()
        active_horses = db.query(Horse).filter(Horse.is_active == True).count()
        retired_horses = db.query(Horse).filter(Horse.is_retired == True).count()
        for_sale_horses = db.query(Horse).filter(Horse.is_for_sale == True).count()
        
        return {
            "horses": {
                "total": total_horses,
                "active": active_horses,
                "retired": retired_horses,
                "for_sale": for_sale_horses
            },
            "system": {
                "version": get_settings().APP_VERSION,
                "status": "operational",
                "ai_enabled": True
            }
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve system statistics"
        )

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
