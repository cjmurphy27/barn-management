from propelauth_py import init_base_auth
from propelauth_py.user import User
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, List, Any
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize PropelAuth
auth = init_base_auth(
    auth_url=settings.PROPELAUTH_URL,
    integration_api_key=settings.PROPELAUTH_API_KEY,
    token_verification_metadata={
        "verifier_key": settings.PROPELAUTH_VERIFIER_KEY,
        "issuer": settings.PROPELAUTH_URL,
    }
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
        user = auth.validate_access_token(token)
        
        if user:
            logger.info(f"Optional auth - authenticated user: {user.user_id}")
        return user
        
    except Exception as e:
        logger.warning(f"Optional authentication failed: {str(e)}")
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

def get_user_organizations(user: User) -> list:
    """
    Get all organizations (barns) the user belongs to
    """
    return [org for org in user.org_id_to_org_info.values()]

def get_user_barn_access(user: User) -> list:
    """
    Get all barns (organizations) the user has access to
    This will be our main function for multi-barn access control
    """
    organizations = get_user_organizations(user)
    
    # Convert organizations to barn access info
    barns = []
    for org in organizations:
        barn_info = {
            "barn_id": org.org_id,
            "barn_name": org.org_name,
            "user_role": org.user_role,
            "permissions": org.user_permissions
        }
        barns.append(barn_info)
    
    logger.info(f"User {user.user_id} has access to {len(barns)} barns")
    return barns
