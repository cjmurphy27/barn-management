#!/bin/bash

echo "🔧 Comprehensive Fix - Fixing ALL syntax errors..."

# Fix the auth.py file (this is the current error)
echo "Fixing app/core/auth.py..."
cat > app/core/auth.py << 'AUTHPY'
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, List, Any
import logging
import jwt
import requests
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

class User(BaseModel):
    user_id: str
    email: str
    organizations: List[Dict[str, Any]]
    current_org_id: Optional[str] = None
    
    def get_current_org(self) -> Optional[Dict[str, Any]]:
        if not self.current_org_id:
            return None
        
        for org in self.organizations:
            if org.get('org_id') == self.current_org_id:
                return org
        return None

def decode_propelauth_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        settings = get_settings()
        
        if not settings.PROPELAUTH_VERIFIER_KEY:
            logger.warning("PropelAuth not configured - authentication will be disabled")
            return None
            
        # Decode the JWT token
        payload = jwt.decode(
            token,
            settings.PROPELAUTH_VERIFIER_KEY,
            algorithms=["RS256"],
            audience=settings.PROPELAUTH_URL,
            issuer=settings.PROPELAUTH_URL
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return None

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    if not credentials:
        return None
    
    token_data = decode_propelauth_token(credentials.credentials)
    if not token_data:
        return None
    
    try:
        user = User(
            user_id=token_data.get('sub'),
            email=token_data.get('email'),
            organizations=token_data.get('org_member_info', []),
            current_org_id=token_data.get('org_id')
        )
        return user
    except Exception as e:
        logger.error(f"Error creating user from token: {str(e)}")
        return None

def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def require_organization(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.current_org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected"
        )
    return current_user
AUTHPY

echo "✅ Fixed auth.py"

# Also ensure main.py is completely clean
echo "Double-checking main.py..."
cat > app/main.py << 'MAINPY'
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging
import time

from app.core.config import get_settings
from app.core.auth import get_current_user, get_current_user_optional, User
from app.api.horses import router as horses_router
from app.api.ai import router as ai_router
from app.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Barn Lady application...")
    settings = get_settings()
    logger.info(f"Application: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    if settings.PROPELAUTH_URL and settings.PROPELAUTH_API_KEY:
        logger.info("PropelAuth authentication enabled")
    else:
        logger.warning("PropelAuth not configured - running in development mode")
    
    yield
    logger.info("Shutting down Barn Lady application...")

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Multi-Barn Horse Management System with AI Assistant and Authentication",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
        )
    
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    app.include_router(horses_router)
    app.include_router(ai_router)
    
    return app

app = create_app()

@app.get("/")
async def root():
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

@app.get("/health")
async def health_check(db = Depends(get_db)):
    try:
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

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user_optional)):
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

echo "🔄 Rebuilding and starting containers..."
docker-compose build --no-cache api
docker-compose up -d

echo "⏱️ Waiting for services to start..."
sleep 15

echo "🧪 Testing API health..."
curl -s http://localhost:8000/health

echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "🎉 Fix complete! Try http://localhost:8501"
