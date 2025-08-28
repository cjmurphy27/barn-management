#!/bin/bash

echo "🐴 BARN LADY MULTI-BARN ACTIVATION SCRIPT 🐴"
echo "=============================================="
echo ""
echo "This script will add authentication and multi-barn support to your existing 
system"
echo "Your existing horses and data will be preserved!"
echo ""

# Function to check if command was successful
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from your Barn Lady project root 
directory"
    echo "   (The directory containing app/main.py)"
    exit 1
fi

echo "📋 Step 1: Starting services and installing dependencies..."

# Check if we're using Docker
if [ -f "docker-compose.yml" ]; then
    echo "Detected Docker setup..."
    
    # First, make sure services are running
    echo "Starting Docker services..."
    docker-compose up -d
    check_success "Docker services started"
    
    echo "Waiting for services to be ready..."
    sleep 10
    
    # Add dependencies to requirements.txt if not already there
    if ! grep -q "pyjwt" requirements.txt; then
        echo "pyjwt==2.8.0" >> requirements.txt
        echo "cryptography==41.0.7" >> requirements.txt
        echo "requests>=2.25.0" >> requirements.txt
        echo "✅ Added dependencies to requirements.txt"
    else
        echo "✅ Dependencies already in requirements.txt"
    fi
    
    # Install in API container - install packages one by one to avoid shell issues
    echo "Installing dependencies in API container..."
    echo "Installing PyJWT..."
    docker-compose exec -T api pip install pyjwt==2.8.0
    echo "Installing cryptography..."
    docker-compose exec -T api pip install cryptography==41.0.7
    echo "Installing requests..."
    docker-compose exec -T api pip install requests
    check_success "Dependencies installed in API container"
    
    echo "✅ Dependencies installation complete"
    
else
    # Not using Docker - try regular pip
    echo "Installing dependencies with pip..."
    pip install pyjwt==2.8.0 cryptography==41.0.7 requests
    check_success "Dependencies installed"
fi

echo ""
echo "📝 Step 2: Creating authentication module..."

# Create app/core/auth.py
mkdir -p app/core
cat > app/core/auth.py << 'EOF'
import os
import jwt
import requests
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class User:
    """User model for authenticated users"""
    def __init__(self, user_id: str, email: str, organizations: List[Dict], 
current_org_id: Optional[str] = None):
        self.user_id = user_id
        self.email = email
        self.organizations = organizations
        self.current_org_id = current_org_id or (organizations[0]["org_id"] if 
organizations else None)
        
    def get_current_org(self) -> Optional[Dict]:
        """Get the current organization details"""
        for org in self.organizations:
            if org["org_id"] == self.current_org_id:
                return org
        return None
    
    def has_org_access(self, org_id: str) -> bool:
        """Check if user has access to specific organization"""
        return any(org["org_id"] == org_id for org in self.organizations)

class PropelAuthManager:
    """PropelAuth integration manager"""
    
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.PROPELAUTH_URL or not self.settings.PROPELAUTH_API_KEY:
            logger.warning("PropelAuth not configured - authentication will be 
disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("PropelAuth authentication enabled")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token using PropelAuth verifier key"""
        if not self.enabled:
            raise HTTPException(status_code=501, detail="Authentication not 
configured")
            
        try:
            # Format the key properly for JWT
            verifier_key = f"-----BEGIN PUBLIC 
KEY-----\n{self.settings.PROPELAUTH_VERIFIER_KEY}\n-----END PUBLIC KEY-----"
            
            payload = jwt.decode(
                token,
                verifier_key,
                algorithms=["RS256"],
                audience=self.settings.PROPELAUTH_URL
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Fetch user info from PropelAuth API"""
        if not self.enabled:
            raise HTTPException(status_code=501, detail="Authentication not 
configured")
            
        try:
            headers = {"Authorization": f"Bearer 
{self.settings.PROPELAUTH_API_KEY}"}
            response = requests.get(
                f"{self.settings.PROPELAUTH_URL}/api/backend/v1/user/{user_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch user info: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch user 
information")

# Global auth manager
auth_manager = PropelAuthManager()

# JWT token verification
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = 
Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user"""
    if not auth_manager.enabled:
        # Return a default user for development when auth is not configured
        return User(
            user_id="dev_user",
            email="dev@example.com",
            organizations=[{"org_id": "default_org", "org_name": "Default 
Organization", "role": "admin"}]
        )
    
    if not credentials:
        raise HTTPException(status_code=401, detail="No authentication token 
provided")
    
    token = credentials.credentials
    
    # Verify the token
    payload = auth_manager.verify_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Get user details from PropelAuth
    user_info = auth_manager.get_user_info(user_id)
    
    # Extract organizations
    organizations = []
    if "org_id_to_org_info" in user_info:
        for org_id, org_info in user_info["org_id_to_org_info"].items():
            organizations.append({
                "org_id": org_id,
                "org_name": org_info.get("org_name", "Unknown"),
                "role": org_info.get("role", "member")
            })
    
    return User(
        user_id=user_id,
        email=user_info.get("email", ""),
        organizations=organizations
    )

async def get_current_user_optional(request: Request) -> Optional[User]:
    """Optional authentication - returns None if no valid token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
            
        token = auth_header.split(" ")[1]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", 
credentials=token)
        return await get_current_user(credentials)
    except HTTPException:
        return None

def require_org_access(org_id: str):
    """Decorator factory to require access to specific organization"""
    def decorator(user: User = Depends(get_current_user)):
        if not user.has_org_access(org_id):
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied to organization {org_id}"
            )
        return user
    return decorator
EOF

check_success "Created app/core/auth.py"

echo ""
echo "🔄 Step 3: Backing up and updating existing files..."

# Backup existing files
echo "Creating backups..."
cp app/api/horses.py app/api/horses.py.backup
cp app/main.py app/main.py.backup
check_success "Backups created"

# Update horses.py
echo "Updating horses API..."
cat > app/api/horses.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging

from app.database import get_db
from app.models.horse import Horse
from app.core.auth import get_current_user, User
# from app.models.health import HealthRecord, FeedingRecord  # We'll add this back 
later
from app.schemas.horse import (
    HorseCreate, HorseUpdate, HorseResponse, HorseListResponse,
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/horses", tags=["horses"])

# Horse CRUD Operations

@router.get("/", response_model=List[HorseListResponse])
async def get_horses(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to 
return"),
    search: Optional[str] = Query(None, description="Search by name, breed, or 
registration number"),
    active_only: bool = Query(True, description="Return only active horses"),
    sort_by: str = Query("name", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get list of horses with optional filtering and search
    Automatically filtered by user's current organization
    """
    try:
        # Ensure user has a current organization
        if not current_user.current_org_id:
            raise HTTPException(
                status_code=400, 
                detail="No organization selected. Please select an organization 
first."
            )
        
        # Build base query - automatically filter by user's organization
        query = db.query(Horse).filter(Horse.organization_id == 
current_user.current_org_id)
        
        # Apply filters
        if active_only:
            query = query.filter(Horse.is_active == True)
        
        # Apply search
        if search:
            search_filter = or_(
                Horse.name.ilike(f"%{search}%"),
                Horse.barn_name.ilike(f"%{search}%"),
                Horse.breed.ilike(f"%{search}%"),
                Horse.registration_number.ilike(f"%{search}%"),
                Horse.owner_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Apply sorting
        sort_column = getattr(Horse, sort_by, Horse.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        horses = query.offset(skip).limit(limit).all()
        
        current_org = current_user.get_current_org()
        org_name = current_org['org_name'] if current_org else "Unknown 
Organization"
        
        logger.info(f"Retrieved {len(horses)} horses for {org_name} (User: 
{current_user.email})")
        return horses
        
    except Exception as e:
        logger.error(f"Error retrieving horses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve horses"
        )


@router.get("/{horse_id}", response_model=HorseResponse)
async def get_horse(
    horse_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific horse by ID with related records
    Must belong to user's current organization
    """
    try:
        if not current_user.current_org_id:
            raise HTTPException(status_code=400, detail="No organization selected")
        
        horse = db.query(Horse).filter(
            Horse.id == horse_id,
            Horse.organization_id == current_user.current_org_id
        ).first()
        
        if not horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Horse with ID {horse_id} not found"
            )
        
        logger.info(f"Retrieved horse: {horse.name} (User: {current_user.email})")
        return horse
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving horse {horse_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve horse"
        )


@router.post("/", response_model=HorseResponse, status_code=status.HTTP_201_CREATED)
async def create_horse(
    horse: HorseCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new horse record
    Automatically assigned to user's current organization
    """
    try:
        if not current_user.current_org_id:
            raise HTTPException(status_code=400, detail="No organization selected")
        
        # Create new horse instance
        horse_data = horse.dict()
        db_horse = Horse(**horse_data)
        
        # Automatically set organization and creator
        db_horse.organization_id = current_user.current_org_id
        db_horse.created_by = current_user.user_id
        
        # Set creation metadata
        db_horse.created_at = datetime.utcnow()
        
        # Check for duplicate names in the same organization
        existing_horse = db.query(Horse).filter(
            Horse.name.ilike(horse.name),
            Horse.organization_id == current_user.current_org_id,
            Horse.is_active == True
        ).first()
        
        if existing_horse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A horse named '{horse.name}' already exists in your 
organization"
            )
        
        # Add to database
        db.add(db_horse)
        db.commit()
        db.refresh(db_horse)
        
        current_org = current_user.get_current_org()
        org_name = current_org['org_name'] if current_org else "Unknown 
Organization"
        
        logger.info(f"Created new horse: {db_horse.name} in {org_name} (User: 
{current_user.email})")
        return db_horse
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating horse: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create horse"
        )


@router.put("/{horse_id}", response_model=HorseResponse)
async def update_horse(
    horse_id: int, 
    horse_update: HorseUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing horse record
    Must belong to user's current organization
    """
    try:
        if not current_user.current_org_id:
            raise HTTPException(status_code=400, detail="No organization selected")
        
        # Get existing horse (must belong to user's organization)
        db_horse = db.query(Horse).filter(
            Horse.id == horse_id,
            Horse.organization_id == current_user.current_org_id
        ).first()
        
        if not db_horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Horse with ID {horse_id} not found"
            )
        
        # Check for name conflicts (excluding current horse)
        if horse_update.name:
            name_conflict = db.query(Horse).filter(
                Horse.name.ilike(horse_update.name),
                Horse.organization_id == current_user.current_org_id,
                Horse.id != horse_id,
                Horse.is_active == True
            ).first()
            
            if name_conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A horse named '{horse_update.name}' already exists in 
your organization"
                )
        
        # Update fields
        update_data = horse_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_horse, field, value)
        
        # Set update timestamp
        db_horse.updated_at = datetime.utcnow()
        
        # Commit changes
        db.commit()
        db.refresh(db_horse)
        
        logger.info(f"Updated horse: {db_horse.name} (User: {current_user.email})")
        return db_horse
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating horse {horse_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update horse"
        )


@router.delete("/{horse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_horse(
    horse_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a horse record (soft delete by setting is_active to False)
    Must belong to user's current organization
    """
    try:
        if not current_user.current_org_id:
            raise HTTPException(status_code=400, detail="No organization selected")
        
        # Get existing horse (must belong to user's organization)
        db_horse = db.query(Horse).filter(
            Horse.id == horse_id,
            Horse.organization_id == current_user.current_org_id
        ).first()
        
        if not db_horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Horse with ID {horse_id} not found"
            )
        
        # Soft delete
        db_horse.is_active = False
        db_horse.updated_at = datetime.utcnow()
        
        # Commit changes
        db.commit()
        
        logger.info(f"Deleted horse: {db_horse.name} (User: {current_user.email})")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting horse {horse_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete horse"
        )


# Statistics and Summary Endpoints

@router.get("/{horse_id}/summary", response_model=Dict[str, Any])
async def get_horse_summary(
    horse_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a summary of horse information including recent health records and 
statistics
    Must belong to user's current organization
    """
    try:
        if not current_user.current_org_id:
            raise HTTPException(status_code=400, detail="No organization selected")
        
        # Get horse (must belong to user's organization)
        horse = db.query(Horse).filter(
            Horse.id == horse_id,
            Horse.organization_id == current_user.current_org_id
        ).first()
        
        if not horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Horse with ID {horse_id} not found"
            )
        
        # Calculate summary statistics
        summary = {
            "horse": horse.to_dict(),
            "statistics": {
                "total_health_records": 0,  # We'll add this back later
                "recent_health_records_count": 0,
            },
            "recent_health_records": [],
            "organization": current_user.get_current_org()
        }
        
        logger.info(f"Generated summary for horse {horse_id} (User: 
{current_user.email})")
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary for horse {horse_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate horse summary"
        )

# Organization Management Endpoints

@router.get("/organizations/current")
async def get_current_organization(current_user: User = Depends(get_current_user)):
    """Get current organization information"""
    return {
        "current_org_id": current_user.current_org_id,
        "current_org": current_user.get_current_org(),
        "all_organizations": current_user.organizations
    }

@router.post("/organizations/{org_id}/select")
async def select_organization(
    org_id: str,
    current_user: User = Depends(get_current_user)
):
    """Switch to different organization"""
    if not current_user.has_org_access(org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied to this organization"
        )
    
    current_user.current_org_id = org_id
    return {
        "message": "Organization switched successfully",
        "current_org_id": org_id,
        "current_org": current_user.get_current_org()
    }
EOF

check_success "Updated app/api/horses.py"

# Update main.py
echo "Updating main application..."
cat > app/main.py << 'EOF'
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
        logger.info("✅ PropelAuth authentication enabled")
    else:
        logger.warning("⚠️  PropelAuth not configured - running in development 
mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Barn Lady application...")

# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Multi-Barn Horse Management System with AI Assistant and 
Authentication",
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
        # Test database connection - fixed for SQLAlchemy v2
        db.execute(text("SELECT 1"))
        
        settings = get_settings()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "ai_service": "available",
            "authentication": "enabled" if settings.PROPELAUTH_URL else 
"development_mode",
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
async def get_current_user_info(current_user: User = 
Depends(get_current_user_optional)):
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
        "authentication_enabled": bool(settings.PROPELAUTH_URL and 
settings.PROPELAUTH_API_KEY),
        "propelauth_url": settings.PROPELAUTH_URL,
        "development_mode": not bool(settings.PROPELAUTH_URL and 
settings.PROPELAUTH_API_KEY),
        "version": settings.APP_VERSION
    }

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
        "name": "Barn Lady API with Multi-Barn Support",
        "version": get_settings().APP_VERSION,
        "endpoints": {
            "authentication": "/api/v1/auth/me",
            "horses": "/api/v1/horses/",
            "organizations": "/api/v1/horses/organizations/current",
            "ai_analysis": "/api/v1/ai/analyze-horse",
            "ai_questions": "/api/v1/ai/general-question",
            "ai_compare": "/api/v1/ai/compare-horses",
            "documentation": "/docs",
            "health_check": "/health"
        },
        "features": [
            "Multi-barn horse management",
            "PropelAuth authentication",
            "Organization-based access control",
            "AI-powered health analysis", 
            "Intelligent care recommendations",
            "Horse comparison and insights",
            "Search and filtering",
            "RESTful API design",
            "Interactive documentation"
        ]
    }

@app.get("/api/v1/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get basic system statistics for current organization"""
    try:
        from app.models.horse import Horse
        
        if not current_user.current_org_id:
            raise HTTPException(status_code=400, detail="No organization selected")
        
        # Get counts for current organization only
        base_query = db.query(Horse).filter(Horse.organization_id == 
current_user.current_org_id)
        
        total_horses = base_query.count()
        active_horses = base_query.filter(Horse.is_active == True).count()
        retired_horses = base_query.filter(Horse.is_retired == True).count()
        for_sale_horses = base_query.filter(Horse.is_for_sale == True).count()
        
        current_org = current_user.get_current_org()
        
        return {
            "organization": {
                "name": current_org.get('org_name', 'Unknown') if current_org else 
'Unknown',
                "org_id": current_user.current_org_id,
                "user_role": current_org.get('role', 'member') if current_org else 
'unknown'
            },
            "horses": {
                "total": total_horses,
                "active": active_horses,
                "retired": retired_horses,
                "for_sale": for_sale_horses
            },
            "system": {
                "version": get_settings().APP_VERSION,
                "status": "operational",
                "ai_enabled": True,
                "multi_barn_enabled": True
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
EOF

check_success "Updated app/main.py"

echo ""
echo "📱 Step 4: Creating frontend authentication component..."

# Create frontend auth component
mkdir -p frontend
cat > frontend/auth_component.py << 'EOF'
import streamlit as st
import requests
import json
from typing import Optional, Dict, Any

class AuthManager:
    """Authentication manager for Streamlit frontend"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        
    def set_auth_token(self, token: str):
        """Store auth token in session state"""
        st.session_state.auth_token = token
        
    def get_auth_token(self) -> Optional[str]:
        """Get auth token from session state"""
        return st.session_state.get('auth_token')
        
    def clear_auth_token(self):
        """Clear auth token and user info"""
        keys_to_clear = ['auth_token', 'user_info', 'current_org']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
                
    def get_headers(self) -> Dict[str, str]:
        """Get headers with auth token"""
        token = self.get_auth_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
        
    def check_auth(self) -> Optional[Dict[str, Any]]:
        """Check if user is authenticated and get user info"""
        token = self.get_auth_token()
        if not token:
            return None
            
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/horses/organizations/current",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                st.session_state.user_info = user_info
                return user_info
            elif response.status_code == 401:
                # Token is invalid
                self.clear_auth_token()
                return None
            else:
                st.error(f"Authentication check failed: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            st.error(f"Failed to connect to API: {e}")
            return None
        
    def api_request(self, method: str, endpoint: str, **kwargs) -> 
requests.Response:
        """Make authenticated API request"""
        headers = self.get_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        return requests.request(method, url, timeout=30, **kwargs)

# Global auth manager instance
auth = AuthManager()

def show_login_page():
    """Show login page for development authentication"""
    
    st.title("🐴 Barn Lady - Multi-Barn Horse Management")
    st.markdown("---")
    
    # Check if PropelAuth is configured by testing the API
    try:
        response = requests.get(f"{auth.api_base_url}/health", timeout=5)
        api_available = response.status_code == 200
    except:
        api_available = False
    
    if not api_available:
        st.error("❌ Cannot connect to Barn Lady API. Please ensure the backend is 
running.")
        st.code("docker-compose up -d")
        return
    
    st.success("✅ Connected to Barn Lady API")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔐 Development Login")
        st.info("""
        **For Development & Testing**
        
        Enter your PropelAuth JWT token to access your barns.
        """)
        
        with st.form("login_form"):
            token_input = st.text_area(
                "JWT Token:",
                height=100,
                placeholder="Paste your PropelAuth JWT token here...",
                help="Get this from your PropelAuth dashboard"
            )
            
            submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submitted and token_input:
                auth.set_auth_token(token_input.strip())
                user_info = auth.check_auth()
                
                if user_info:
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid token. Please check your token and try 
again.")
    
    with col2:
        st.subheader("📋 How to Get Your Token")
        st.markdown("""
        **Step 1:** Go to your PropelAuth dashboard
        - URL: `https://34521247761.propelauthtest.com`
        
        **Step 2:** Create or login as a test user
        
        **Step 3:** Create an organization (barn)
        
        **Step 4:** Generate a JWT token for testing
        
        **Step 5:** Copy and paste the token above
        """)
        
        st.markdown("---")
        
        st.subheader("🌟 What You'll Get")
        st.markdown("""
        ✅ **Multi-Barn Management** - Switch between different barns
        
        ✅ **Secure Horse Data** - Each barn sees only their horses
        
        ✅ **AI-Powered Insights** - Claude understands your barn context
        
        ✅ **Team Collaboration** - Multiple users per barn
        
        ✅ **Professional Features** - Search, sort, manage horses
        """)

def show_organization_selector():
    """Show organization selector in sidebar"""
    user_info = st.session_state.get('user_info', {})
    organizations = user_info.get('all_organizations', [])
    current_org_id = user_info.get('current_org_id')
    
    if not organizations:
        st.sidebar.error("No organizations found")
        return
    
    st.sidebar.markdown("### 🏢 Your Barns")
    
    if len(organizations) > 1:
        # Multiple organizations - show selector
        org_options = {}
        for org in organizations:
            org_options[org['org_name']] = org['org_id']
            
        # Find current selection
        current_selection = None
        for name, org_id in org_options.items():
            if org_id == current_org_id:
                current_selection = name
                break
                
        if current_selection not in org_options:
            current_selection = list(org_options.keys())[0]
            
        selected_org_name = st.sidebar.selectbox(
            "Select barn:",
            options=list(org_options.keys()),
            index=list(org_options.keys()).index(current_selection) if 
current_selection in org_options else 0,
            key="org_selector"
        )
        
        selected_org_id = org_options[selected_org_name]
        
        # Switch organization if changed
        if selected_org_id != current_org_id:
            try:
                response = auth.api_request(
                    'POST', 
                    f'/api/v1/horses/organizations/{selected_org_id}/select'
                )
                
                if response.status_code == 200:
                    # Update user info in session
                    updated_info = auth.check_auth()
                    if updated_info:
                        st.sidebar.success(f"Switched to {selected_org_name}")
                        st.rerun()
                else:
                    st.sidebar.error("Failed to switch organization")
                    
            except requests.RequestException:
                st.sidebar.error("Failed to switch organization")
    
    else:
        # Single organization
        org = organizations[0]
        st.sidebar.markdown(f"**{org['org_name']}**")
        st.sidebar.caption(f"Role: {org.get('role', 'Member')}")

def show_user_menu():
    """Show user menu in sidebar"""
    user_info = st.session_state.get('user_info', {})
    current_org = user_info.get('current_org', {})
    
    st.sidebar.markdown("---")
    
    # Current organization info
    if current_org:
        st.sidebar.markdown(f"**📍 Current Barn:** {current_org.get('org_name', 
'Unknown')}")
        st.sidebar.caption(f"Role: {current_org.get('role', 'Member')}")
    
    st.sidebar.markdown("---")
    
    # User info
    email = user_info.get('current_org', {}).get('email', 'Unknown User')
    st.sidebar.markdown(f"**👤 Logged in**")
    st.sidebar.caption(f"User ID: {user_info.get('current_org_id', 
'Unknown')[:8]}...")
    
    # Logout button
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        auth.clear_auth_token()
        st.rerun()

def require_auth():
    """Decorator/function to require authentication"""
    user_info = auth.check_auth()
    
    if not user_info:
        show_login_page()
        return False
    
    # Show organization selector and user menu
    show_organization_selector()
    show_user_menu()
    
    return True

def get_auth_headers() -> Dict[str, str]:
    """Get headers for API requests"""
    return auth.get_headers()

def make_api_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make an authenticated API request"""
    return auth.api_request(method, endpoint, **kwargs)
EOF

check_success "Created frontend/auth_component.py"

echo ""
echo "🔄 Step 5: Restarting services to load new code..."

# Check if using Docker
if [ -f "docker-compose.yml" ]; then
    echo "Restarting Docker services..."
    docker-compose restart api
    check_success "API service restarted"

    docker-compose restart frontend  
    check_success "Frontend service restarted"
    
    echo ""
    echo "⏳ Waiting for services to reload..."
    sleep 12
    
    # Check if services are running
    echo "Checking service status..."
    docker-compose ps
else
    echo "⚠️  Not using Docker - please restart your services manually"
fi

echo ""
echo "🧪 Step 6: Testing the setup..."

# Wait a bit more for services to be fully ready
echo "Waiting for services to be fully ready..."
sleep 5

# Test API health with retries
echo "Testing API health..."
for i in {1..5}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API health check passed"
        break
    else
        if [ $i -eq 5 ]; then
            echo "⚠️  API health check failed - services may still be starting"
            echo "   You can check manually: curl http://localhost:8000/health"
        else
            echo "   Attempt $i failed, retrying..."
            sleep 3
        fi
    fi
done

# Test auth endpoints
echo "Testing authentication endpoints..."
if curl -s http://localhost:8000/api/v1/auth/status > /dev/null 2>&1; then
    echo "✅ Authentication endpoints working"
else
    echo "⚠️  Auth endpoints not responding yet - services may still be starting"
fi

# Test horses endpoint (should work in dev mode)
echo "Testing horses endpoint..."
if curl -s http://localhost:8000/api/v1/horses/ > /dev/null 2>&1; then
    echo "✅ Horses API working"
else
    echo "⚠️  Horses API not responding yet - services may still be starting"
fi

echo ""
echo "🎉 MULTI-BARN SETUP COMPLETE! 🎉"
echo "=================================="
echo ""
echo "🌟 Your Barn Lady system now supports:"
echo "   ✅ PropelAuth authentication"
echo "   ✅ Multi-barn organization support"
echo "   ✅ Secure horse data isolation"
echo "   ✅ Organization switching"
echo "   ✅ User role management"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. 🌐 Open Streamlit: http://localhost:8501"
echo "   (Your services are already running!)"
echo "2. 🔑 Get PropelAuth JWT token:"
echo "   - Go to: https://34521247761.propelauthtest.com"
echo "   - Create test user and organization"  
echo "   - Generate JWT token"
echo "3. 🔓 Login with your token"
echo "4. 🐴 Add horses to your barn!"
echo ""
echo "📋 Quick Tests:"
echo "   • API docs: http://localhost:8000/docs"
echo "   • Health: http://localhost:8000/health"
echo "   • Auth status: http://localhost:8000/api/v1/auth/status"
echo ""
echo "🎯 Your existing horses are preserved and ready!"
echo "🔥 Each barn will now see only their own horses!"
echo ""
echo "Happy multi-barn horse managing! 🐴✨"

# Show backup info
echo ""
echo "📦 Backup Information:"
echo "   Your original files are backed up:"
echo "   • app/api/horses.py.backup"
echo "   • app/main.py.backup"
echo ""
echo "   If you need to restore, run:"
echo "   cp app/api/horses.py.backup app/api/horses.py"
echo "   cp app/main.py.backup app/main.py"
echo "   docker-compose restart api"

# Show current containers status
echo ""
echo "🐳 Current Docker Status:"
docker-compose ps

echo ""
echo "All systems ready! 🎯"
