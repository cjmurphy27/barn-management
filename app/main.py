from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.config import get_settings
from app.core.auth import get_current_user_optional, get_current_user, get_user_barn_access
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db, Base, db_manager
from app.models.horse import Horse
from app.models.event import Event, EventType_Config
from app.models.supply import Supply, Supplier, Transaction, TransactionItem, StockMovement
from app.schemas.horse import HorseCreate, HorseResponse
from app.api.ai import router as ai_router
from app.api.calendar import router as calendar_router
from app.api.supplies import router as supplies_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Barn Lady API", version="1.0.0")

# Custom authentication that uses JWT parsing
security = HTTPBearer(auto_error=False)

def get_jwt_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """Get user data from JWT token (custom authentication)"""
    if not credentials:
        return None

    try:
        import jwt
        token = credentials.credentials
        # Parse JWT without verification to extract user data
        decoded_token = jwt.decode(token, options={"verify_signature": False})

        user_data = {
            "user_id": decoded_token.get("user_id"),
            "email": decoded_token.get("email"),
            "organizations": []
        }

        # Extract organization info
        org_info = decoded_token.get("org_id_to_org_member_info", {})
        for org_id, org_data in org_info.items():
            barn_info = {
                "barn_id": org_data.get("org_id"),
                "barn_name": org_data.get("org_name"),
                "user_role": org_data.get("user_role"),
                "permissions": org_data.get("user_permissions", [])
            }
            user_data["organizations"].append(barn_info)

        return user_data
    except Exception as e:
        logger.error(f"JWT parsing error in get_jwt_user: {str(e)}")
        return None

def get_jwt_user_required(user_data: Optional[dict] = Depends(get_jwt_user)) -> dict:
    """Get user data from JWT token (required)"""
    if not user_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_data

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(ai_router)
app.include_router(calendar_router)
app.include_router(supplies_router)

# Import and include horse documents router
from app.api.horse_documents import router as horse_documents_router
app.include_router(horse_documents_router, prefix="/api/v1")

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Create tables
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database tables created successfully")
        
        # Test connection
        if db_manager.test_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "version": "2.0.0"}

@app.get("/api/v1/auth/user")
async def get_user_info(user_data = Depends(get_jwt_user_required)):
    """Get current user information and barn access"""
    try:
        barns = user_data.get("organizations", [])
        user_id = user_data.get("user_id")
        email = user_data.get("email")

        return {
            "user_id": user_id,
            "email": email,
            "barns": barns
        }
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user information")

@app.get("/api/v1/auth/barns")
async def get_user_barns(user_data = Depends(get_jwt_user_required)):
    """Get all barns the current user has access to"""
    try:
        barns = user_data.get("organizations", [])
        return {"barns": barns}
    except Exception as e:
        logger.error(f"Error getting user barns: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving barn access")

@app.post("/api/v1/auth/validate-token")
async def validate_token_debug(token_data: dict):
    """Debug endpoint to test token validation"""
    try:
        token = token_data.get("token", "")
        if not token:
            return {"valid": False, "error": "No token provided"}
        
        # Test with our auth system
        from app.core.auth import auth
        user = auth.validate_access_token_and_get_user(f"Bearer {token}")
        
        if user:
            return {
                "valid": True,
                "user_id": user.user_id,
                "email": user.email,
                "organizations": len(user.org_id_to_org_info) if hasattr(user, 'org_id_to_org_info') else 0
            }
        else:
            return {"valid": False, "error": "Token validation failed"}
            
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return {"valid": False, "error": str(e)}

@app.get("/api/v1/auth/test-propelauth-connection")
async def test_propelauth_connection():
    """Test PropelAuth API connection"""
    try:
        import requests
        
        # Test with the user query endpoint
        test_url = f"{settings.PROPELAUTH_URL}/api/backend/v1/user/query"
        headers = {
            "Authorization": f"Bearer {settings.PROPELAUTH_API_KEY}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Testing PropelAuth connection to: {test_url}")
        logger.info(f"Using API key: {settings.PROPELAUTH_API_KEY[:20]}...")
        
        response = requests.get(test_url, headers=headers, params={"page_size": 1})
        
        logger.info(f"Test response status: {response.status_code}")
        logger.info(f"Test response: {response.text[:500]}...")
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response_preview": response.text[:200]
        }
        
    except Exception as e:
        logger.error(f"PropelAuth connection test error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/api/v1/auth/lookup-user")
async def lookup_real_user(user_data: dict):
    """Look up real user data from PropelAuth using email"""
    try:
        email = user_data.get("email", "")
        
        if not email:
            return {"success": False, "error": "No email provided"}
        
        # Use PropelAuth's User Management API to get real user data
        import requests
        
        # PropelAuth User API endpoint
        user_api_url = f"{settings.PROPELAUTH_URL}/api/backend/v1/user/email"
        
        # API authentication using our PropelAuth API key
        headers = {
            "Authorization": f"Bearer {settings.PROPELAUTH_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Query parameters
        params = {
            "email": email,
            "include_orgs": "true"  # Include organization data
        }
        
        # Debug logging
        logger.info(f"Making request to: {user_api_url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Params: {params}")
        
        response = requests.get(user_api_url, params=params, headers=headers)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response content: {response.text}")  # Show full response
        
        if response.status_code == 200:
            user_response = response.json()
            
            # Extract real user data
            real_user = {
                "user_id": user_response.get("user_id"),
                "email": user_response.get("email"),
                "first_name": user_response.get("first_name"),
                "last_name": user_response.get("last_name"),
                "username": user_response.get("username"),
                "organizations": []
            }
            
            # Process organization data (this is our barn data!)
            org_id_to_org_info = user_response.get("org_id_to_org_info", {})
            for org_id, org_info in org_id_to_org_info.items():
                barn = {
                    "barn_id": org_id,
                    "barn_name": org_info.get("org_name", "Unknown Barn"),
                    "user_role": org_info.get("user_role", "Member"),
                    "permissions": org_info.get("user_permissions", [])
                }
                real_user["organizations"].append(barn)
            
            return {
                "success": True,
                "user": real_user,
                "total_organizations": len(real_user["organizations"])
            }
            
        elif response.status_code == 404:
            return {"success": False, "error": "User not found in PropelAuth"}
        else:
            logger.error(f"PropelAuth user lookup failed: {response.status_code} - {response.text}")
            return {"success": False, "error": f"User lookup failed: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"User lookup error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/api/v1/auth/exchange-code")
async def exchange_code_for_token(request_data: dict):
    """Exchange OAuth authorization code for access token"""
    try:
        auth_code = request_data.get("code", "")
        redirect_uri = request_data.get("redirect_uri", "")
        
        if not auth_code:
            return {"success": False, "error": "No authorization code provided"}
        
        # Exchange code for token using PropelAuth's OAuth flow
        import requests
        
        # PropelAuth token endpoint
        token_url = f"{settings.PROPELAUTH_URL}/propelauth/oauth/token"

        # OAuth token exchange parameters
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri
        }

        # Use Basic Auth for client authentication (OAuth2 standard)
        import base64
        client_credentials = f"{settings.PROPELAUTH_CLIENT_ID}:{settings.PROPELAUTH_CLIENT_SECRET}"
        client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {client_credentials_b64}"
        }
        
        logger.info(f"Exchanging code for token at: {token_url}")
        logger.info(f"Token data: {token_data}")
        
        response = requests.post(token_url, data=token_data, headers=headers)
        
        logger.info(f"Token exchange response status: {response.status_code}")
        logger.info(f"Token exchange response: {response.text}")
        
        if response.status_code == 200:
            token_response = response.json()
            access_token = token_response.get("access_token")
            
            if access_token:
                # Parse JWT to get user info directly (temporary workaround)
                import jwt
                import json

                try:
                    # Decode JWT without verification for now (since we got it directly from PropelAuth)
                    decoded_token = jwt.decode(access_token, options={"verify_signature": False})
                    logger.info(f"Decoded JWT: {json.dumps(decoded_token, indent=2)}")

                    # Extract user information from JWT
                    user_data = {
                        "user_id": decoded_token.get("user_id"),
                        "email": decoded_token.get("email"),
                        "organizations": []
                    }

                    # Extract organization info
                    org_info = decoded_token.get("org_id_to_org_member_info", {})
                    for org_id, org_data in org_info.items():
                        barn_info = {
                            "barn_id": org_data.get("org_id"),
                            "barn_name": org_data.get("org_name"),
                            "user_role": org_data.get("user_role"),
                            "permissions": org_data.get("user_permissions", [])
                        }
                        user_data["organizations"].append(barn_info)

                    logger.info(f"User {user_data['user_id']} has access to {len(user_data['organizations'])} barns")

                    return {
                        "success": True,
                        "access_token": access_token,
                        "user": user_data
                    }

                except Exception as jwt_error:
                    logger.error(f"JWT parsing error: {str(jwt_error)}")
                    return {"success": False, "error": f"JWT parsing failed: {str(jwt_error)}"}
            else:
                return {"success": False, "error": "No access token in response"}
        else:
            logger.error(f"PropelAuth token exchange failed: {response.status_code} - {response.text}")
            return {"success": False, "error": f"Token exchange failed: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Token exchange error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/api/v1/auth/validate-propelauth-token")
async def validate_propelauth_token(request_data: dict):
    """Validate a real PropelAuth JWT token"""
    try:
        token = request_data.get("token", "")
        
        if not token:
            return {"success": False, "error": "No token provided"}
        
        # Validate PropelAuth JWT token using their API
        import requests
        
        # Use PropelAuth's token validation endpoint
        validate_url = f"{settings.PROPELAUTH_URL}/api/backend/v1/validate_access_token"
        
        headers = {
            "Authorization": f"Bearer {settings.PROPELAUTH_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "access_token": token
        }
        
        logger.info(f"Validating PropelAuth token with: {validate_url}")
        
        response = requests.post(validate_url, json=data, headers=headers)
        
        logger.info(f"PropelAuth validation response: {response.status_code}")
        logger.info(f"PropelAuth validation content: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Extract user information from validated token
            user_info = {
                "user_id": token_data.get("user_id"),
                "email": token_data.get("email"), 
                "first_name": token_data.get("first_name"),
                "last_name": token_data.get("last_name"),
                "organizations": []
            }
            
            # Convert organizations to our barn format
            org_id_to_org_info = token_data.get("org_id_to_org_info", {})
            for org_id, org_info in org_id_to_org_info.items():
                barn = {
                    "barn_id": org_id,
                    "barn_name": org_info.get("org_name", "Unknown Barn"),
                    "user_role": org_info.get("user_role", "Member"), 
                    "permissions": org_info.get("user_permissions", [])
                }
                user_info["organizations"].append(barn)
            
            logger.info(f"Successfully validated token for user: {user_info['email']}")
            
            return {
                "success": True,
                "user": user_info,
                "token_valid": True
            }
        else:
            logger.error(f"PropelAuth token validation failed: {response.status_code} - {response.text}")
            return {"success": False, "error": f"PropelAuth validation failed: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"PropelAuth token validation error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/v1/auth/login")
async def initiate_login():
    """Initiate PropelAuth OAuth login flow through backend"""
    from fastapi.responses import RedirectResponse
    import urllib.parse
    
    # Use PropelAuth's hosted login page (same as working frontend)
    # TODO: For production, configure proper OAuth with backend callback
    redirect_uri = "http://localhost:8501/?auth=callback"  # Point back to frontend
    
    # Build PropelAuth OAuth URL 
    login_url = f"{settings.PROPELAUTH_URL}/login"
    params = {
        "redirect_uri": redirect_uri
    }
    
    full_login_url = f"{login_url}?{urllib.parse.urlencode(params)}"
    logger.info(f"Redirecting to PropelAuth OAuth login: {full_login_url}")
    
    return RedirectResponse(url=full_login_url)

@app.get("/api/v1/auth/callback")
async def handle_auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle PropelAuth OAuth callback"""
    from fastapi.responses import RedirectResponse
    import requests
    import secrets
    import json
    
    if error:
        logger.error(f"PropelAuth OAuth error: {error}")
        return RedirectResponse(url="http://localhost:8501/?auth_error=" + error)
    
    if not code:
        logger.error("No authorization code received from PropelAuth")
        return RedirectResponse(url="http://localhost:8501/?auth_error=no_code")
    
    try:
        # Exchange authorization code for access token
        token_url = f"{settings.PROPELAUTH_URL}/propelauth/oidc/token"
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:8002/api/v1/auth/callback",
            "client_id": settings.PROPELAUTH_API_KEY
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {settings.PROPELAUTH_API_KEY}"
        }
        
        logger.info(f"Exchanging code for token at: {token_url}")
        
        response = requests.post(token_url, data=token_data, headers=headers)
        
        logger.info(f"Token exchange response: {response.status_code}")
        logger.info(f"Token exchange content: {response.text}")
        
        if response.status_code == 200:
            token_response = response.json()
            access_token = token_response.get("access_token")
            
            if access_token:
                # Validate the token and get user info
                from app.core.auth import auth
                user = auth.validate_access_token_and_get_user(f"Bearer {access_token}")
                
                if user:
                    # Create a simple session token for the frontend
                    session_token = secrets.token_urlsafe(32)
                    
                    # Store session in a simple way (in production, use Redis or database)
                    # For now, we'll create a temporary token that contains user info
                    session_data = {
                        "user_id": user.user_id,
                        "email": user.email,
                        "access_token": access_token
                    }
                    
                    # Encode session data (in production, store securely)
                    import base64
                    encoded_session = base64.b64encode(json.dumps(session_data).encode()).decode()
                    
                    # Redirect back to frontend with session token
                    frontend_url = f"http://localhost:8501/?session_token={encoded_session}"
                    logger.info(f"Redirecting to frontend with session: {frontend_url}")
                    
                    return RedirectResponse(url=frontend_url)
                else:
                    logger.error("Failed to validate access token")
                    return RedirectResponse(url="http://localhost:8501/?auth_error=token_validation_failed")
            else:
                logger.error("No access token received")
                return RedirectResponse(url="http://localhost:8501/?auth_error=no_access_token")
        else:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return RedirectResponse(url="http://localhost:8501/?auth_error=token_exchange_failed")
            
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(url="http://localhost:8501/?auth_error=callback_exception")

@app.post("/api/v1/auth/validate-session")
async def validate_session(request_data: dict):
    """Validate a frontend session token"""
    try:
        session_token = request_data.get("session_token", "")
        
        if not session_token:
            return {"success": False, "error": "No session token provided"}
        
        # Decode session data
        import base64
        import json
        
        try:
            decoded_data = base64.b64decode(session_token.encode()).decode()
            session_data = json.loads(decoded_data)
        except:
            return {"success": False, "error": "Invalid session token"}
        
        # Validate the access token with PropelAuth
        access_token = session_data.get("access_token")
        if access_token:
            from app.core.auth import auth
            user = auth.validate_access_token_and_get_user(f"Bearer {access_token}")
            
            if user:
                # Get user barn access
                barns = get_user_barn_access(user)
                
                return {
                    "success": True,
                    "user": {
                        "user_id": user.user_id,
                        "email": user.email,
                        "barns": barns
                    }
                }
            else:
                return {"success": False, "error": "Invalid access token"}
        else:
            return {"success": False, "error": "No access token in session"}
            
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/v1/horses/")
async def get_horses(
    search: Optional[str] = None,
    active_only: bool = True,
    sort_by: str = "name",
    sort_order: str = "asc",
    limit: int = 100,
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get horses from database with search, filter, and sorting"""
    from sqlalchemy import or_, asc, desc
    
    query = db.query(Horse)
    
    # Filter by organization (barn) if provided
    if organization_id:
        query = query.filter(Horse.organization_id == organization_id)
    
    # Filter by active status
    if active_only:
        query = query.filter(Horse.is_active == True)
    
    # Search functionality
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Horse.name.ilike(search_term),
                Horse.barn_name.ilike(search_term),
                Horse.breed.ilike(search_term),
                Horse.color.ilike(search_term),
                Horse.owner_name.ilike(search_term),
                Horse.current_location.ilike(search_term)
            )
        )
    
    # Sorting
    sort_column = getattr(Horse, sort_by, Horse.name)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Limit results
    horses = query.limit(limit).all()
    
    return [horse.to_dict() for horse in horses]

@app.get("/api/v1/horses/{horse_id}")
async def get_horse(horse_id: int, organization_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get a specific horse by ID"""
    query = db.query(Horse).filter(Horse.id == horse_id)
    
    # Filter by organization if provided
    if organization_id:
        query = query.filter(Horse.organization_id == organization_id)
    
    horse = query.first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    return horse.to_dict()

@app.post("/api/v1/horses/")
async def create_horse(horse_data: HorseCreate, organization_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Create a new horse"""
    horse_dict = horse_data.dict()
    
    # Set organization_id if provided
    if organization_id:
        horse_dict['organization_id'] = organization_id
    
    db_horse = Horse(**horse_dict)
    db.add(db_horse)
    db.commit()
    db.refresh(db_horse)
    logger.info(f"Created new horse: {db_horse.name} for organization: {organization_id}")
    return db_horse.to_dict()

@app.put("/api/v1/horses/{horse_id}")
async def update_horse(horse_id: int, horse_data: HorseCreate, organization_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Update an existing horse"""
    query = db.query(Horse).filter(Horse.id == horse_id)
    
    # Filter by organization if provided
    if organization_id:
        query = query.filter(Horse.organization_id == organization_id)
    
    db_horse = query.first()
    if not db_horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    
    # Update horse fields
    for field, value in horse_data.dict(exclude_unset=True).items():
        setattr(db_horse, field, value)
    
    db.commit()
    db.refresh(db_horse)
    logger.info(f"Updated horse: {db_horse.name}")
    return db_horse.to_dict()

@app.delete("/api/v1/horses/{horse_id}")
async def delete_horse(horse_id: int, organization_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Delete a horse (soft delete by setting is_active=False)"""
    query = db.query(Horse).filter(Horse.id == horse_id)
    
    # Filter by organization if provided
    if organization_id:
        query = query.filter(Horse.organization_id == organization_id)
    
    db_horse = query.first()
    if not db_horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    
    # Soft delete - just mark as inactive
    db_horse.is_active = False
    db.commit()
    logger.info(f"Deleted horse: {db_horse.name}")
    return {"message": f"Horse {db_horse.name} deleted successfully"}

