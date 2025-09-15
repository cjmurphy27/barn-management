from propelauth_py import init_base_auth, TokenVerificationMetadata, UnauthorizedException
from propelauth_py.user import User
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, List, Any
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize PropelAuth - let it auto-configure token verification metadata
auth = init_base_auth(
    auth_url=settings.PROPELAUTH_URL,
    integration_api_key=settings.PROPELAUTH_API_KEY
)

security = HTTPBearer(auto_error=False)

# User class is now imported from propelauth_py.user

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Optional authentication dependency - returns None if no valid token provided
    """
    if not credentials:
        return None
    
    try:
        # Extract the token from the Authorization header
        token = credentials.credentials
        
        # Validate the token and get user info using PropelAuth SDK
        user = auth.validate_access_token_and_get_user(f"Bearer {token}")
        
        if user:
            logger.info(f"Optional auth - authenticated user: {user.user_id}")
        return user
        
    except UnauthorizedException as e:
        logger.warning(f"Invalid access token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return None

def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """
    Required authentication dependency - raises 401 if no valid token provided
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def require_org_member(org_id: str):
    """
    Dependency factory that requires user to be a member of a specific organization (barn)
    """
    def _require_org_member(user: User = Depends(get_current_user)) -> User:
        if not user.is_member_of_org(org_id):
            logger.warning(f"User {user.user_id} attempted to access barn {org_id} without membership")
            raise HTTPException(
                status_code=403,
                detail="Access denied - not a member of this barn"
            )
        return user
    return _require_org_member

def require_org_role(org_id: str, required_role: str):
    """
    Dependency factory that requires user to have a specific role in an organization (barn)
    """
    def _require_org_role(user: User = Depends(get_current_user)) -> User:
        if not user.is_member_of_org(org_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied - not a member of this barn"
            )
        
        org_info = user.get_org(org_id)
        if not org_info or required_role not in org_info.user_role:
            logger.warning(f"User {user.user_id} lacks required role {required_role} in barn {org_id}")
            raise HTTPException(
                status_code=403,
                detail=f"Access denied - requires {required_role} role"
            )
        return user
    return _require_org_role

def get_user_organizations(user) -> list:
    """
    Get all organizations (barns) the user belongs to
    """
    # Handle custom user data dictionary (from JWT parsing)
    if isinstance(user, dict) and "organizations" in user:
        return user["organizations"]

    # Handle PropelAuth User object
    if hasattr(user, 'org_id_to_org_info'):
        return [org for org in user.org_id_to_org_info.values()]
    elif hasattr(user, 'org_id_to_org_member_info'):
        return [org for org in user.org_id_to_org_member_info.values()]

    # Fallback
    return []

def get_user_barn_access(user) -> list:
    """
    Get all barns (organizations) the user has access to
    This will be our main function for multi-barn access control
    """
    organizations = get_user_organizations(user)

    # If organizations is already in the proper format (from JWT parsing), return it
    if organizations and isinstance(organizations[0], dict) and "barn_id" in organizations[0]:
        user_id = user.get("user_id") if isinstance(user, dict) else getattr(user, "user_id", "unknown")
        logger.info(f"User {user_id} has access to {len(organizations)} barns")
        return organizations

    # Convert PropelAuth organization objects to barn access info
    barns = []
    for org in organizations:
        # Handle both dict and object formats
        if isinstance(org, dict):
            barn_info = {
                "barn_id": org.get("org_id"),
                "barn_name": org.get("org_name"),
                "user_role": org.get("user_role"),
                "permissions": org.get("user_permissions", [])
            }
        else:
            barn_info = {
                "barn_id": org.org_id,
                "barn_name": org.org_name,
                "user_role": org.user_role,
                "permissions": org.user_permissions
            }
        barns.append(barn_info)

    user_id = user.get("user_id") if isinstance(user, dict) else getattr(user, "user_id", "unknown")
    logger.info(f"User {user_id} has access to {len(barns)} barns")
    return barns
