from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os
import uuid
import shutil
import mimetypes
from datetime import datetime

from app.database import get_db
from app.models.horse import Horse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["horse-photos"])

# File storage configuration
UPLOAD_DIR = "storage/horse_photos"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_image_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded image file"""
    # Check file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False, f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"

    # Check file extension
    if file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return False, f"File type '{ext}' not allowed. Supported: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"

    return True, "Valid"

def save_uploaded_horse_photo(file: UploadFile, organization_id: str, horse_id: int) -> tuple[str, str]:
    """Save uploaded horse photo and return (filename, file_path)"""
    # Generate unique filename
    file_uuid = str(uuid.uuid4())
    original_filename = file.filename or "unknown"
    _, ext = os.path.splitext(original_filename.lower())
    filename = f"horse_{horse_id}_{file_uuid}{ext}"

    # Create organization subdirectory
    org_dir = os.path.join(UPLOAD_DIR, organization_id)
    os.makedirs(org_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(org_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return filename, file_path

# JWT Authentication (matching Message Board pattern)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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

@router.post("/horses/{horse_id}/photo", status_code=status.HTTP_201_CREATED)
async def upload_horse_photo(
    horse_id: int,
    organization_id: str = Query(..., description="Organization/barn ID"),
    photo: UploadFile = File(..., description="Horse profile photo"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Upload a profile photo for a horse"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Validate image
        is_valid, error_msg = validate_image_file(photo)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Verify horse exists and belongs to organization
        horse = db.query(Horse).filter(
            Horse.id == horse_id,
            Horse.organization_id == organization_id
        ).first()

        if not horse:
            raise HTTPException(status_code=404, detail="Horse not found")

        # Remove old photo if it exists
        if horse.profile_photo_path and os.path.exists(horse.profile_photo_path):
            try:
                os.remove(horse.profile_photo_path)
                logger.info(f"Removed old photo: {horse.profile_photo_path}")
            except Exception as e:
                logger.warning(f"Could not remove old photo: {str(e)}")

        # Save new photo
        filename, file_path = save_uploaded_horse_photo(photo, organization_id, horse_id)

        # Update horse record
        horse.profile_photo_path = file_path
        db.commit()

        logger.info(f"Updated photo for horse {horse_id}: {filename}")

        return {
            "message": "Photo uploaded successfully",
            "filename": filename,
            "horse_id": horse_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading horse photo: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to upload photo"
        )

@router.get("/horses/{horse_id}/photo")
async def get_horse_photo(
    horse_id: int,
    organization_id: str = Query(..., description="Organization/barn ID"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Get a horse's profile photo"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Get horse
        horse = db.query(Horse).filter(
            Horse.id == horse_id,
            Horse.organization_id == organization_id
        ).first()

        if not horse:
            raise HTTPException(status_code=404, detail="Horse not found")

        if not horse.profile_photo_path:
            raise HTTPException(status_code=404, detail="No photo found for this horse")

        # Check if file exists
        if not os.path.exists(horse.profile_photo_path):
            raise HTTPException(status_code=404, detail="Photo file not found on disk")

        # Determine mime type
        mime_type = mimetypes.guess_type(horse.profile_photo_path)[0] or "image/jpeg"

        # Return the file
        return FileResponse(
            path=horse.profile_photo_path,
            media_type=mime_type,
            filename=f"{horse.name}_profile.jpg"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving horse photo {horse_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to serve photo"
        )

@router.delete("/horses/{horse_id}/photo", status_code=status.HTTP_204_NO_CONTENT)
async def delete_horse_photo(
    horse_id: int,
    organization_id: str = Query(..., description="Organization/barn ID"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Delete a horse's profile photo"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Get horse
        horse = db.query(Horse).filter(
            Horse.id == horse_id,
            Horse.organization_id == organization_id
        ).first()

        if not horse:
            raise HTTPException(status_code=404, detail="Horse not found")

        if not horse.profile_photo_path:
            raise HTTPException(status_code=404, detail="No photo found for this horse")

        # Remove file if it exists
        if os.path.exists(horse.profile_photo_path):
            try:
                os.remove(horse.profile_photo_path)
                logger.info(f"Deleted photo file: {horse.profile_photo_path}")
            except Exception as e:
                logger.warning(f"Could not delete photo file: {str(e)}")

        # Clear photo path from database
        horse.profile_photo_path = None
        db.commit()

        logger.info(f"Deleted photo for horse {horse_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting horse photo {horse_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete photo"
        )