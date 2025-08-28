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
