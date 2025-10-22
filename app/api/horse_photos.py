from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from typing import Optional
import logging
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path

from app.database import get_db
from app.models.horse import Horse
from app.config.storage import StorageConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["horse-photos"])

# File storage configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

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

    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        return False, f"MIME type '{file.content_type}' not allowed. Supported: {', '.join(ALLOWED_MIME_TYPES)}"

    return True, "Valid"

def save_image_to_storage(file: UploadFile) -> tuple[str, str]:
    """Save uploaded image to volume storage and return (file_path, original_filename)"""
    # Ensure storage directory exists
    storage_dir = StorageConfig.get_horse_photos_dir()

    # Generate unique filename
    file_extension = ""
    if file.filename:
        _, file_extension = os.path.splitext(file.filename.lower())

    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = storage_dir / unique_filename

    # Save file to storage
    file_content = file.file.read()

    with open(file_path, "wb") as f:
        f.write(file_content)

    return str(file_path), file.filename or unique_filename

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

        # Save image to volume storage
        file_path, original_filename = save_image_to_storage(photo)

        # Update horse record with file path
        horse.profile_photo_path = file_path

        db.commit()

        logger.info(f"Updated photo for horse {horse_id}: {photo.filename} saved to {file_path}")

        return {
            "message": "Photo uploaded successfully",
            "filename": photo.filename,
            "horse_id": horse_id,
            "mime_type": photo.content_type or "image/jpeg"
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

        # Check for file-based photo storage
        if horse.profile_photo_path and os.path.exists(horse.profile_photo_path):
            mime_type = mimetypes.guess_type(horse.profile_photo_path)[0] or "image/jpeg"
            return FileResponse(
                path=horse.profile_photo_path,
                media_type=mime_type,
                filename=f"{horse.name}_profile.jpg"
            )

        # No photo found
        raise HTTPException(status_code=404, detail="No photo found for this horse")

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

        # Check if any photo exists
        if not horse.profile_photo_path:
            raise HTTPException(status_code=404, detail="No photo found for this horse")

        # Remove file-based photo if it exists
        if horse.profile_photo_path and os.path.exists(horse.profile_photo_path):
            try:
                os.remove(horse.profile_photo_path)
                logger.info(f"Deleted photo file: {horse.profile_photo_path}")
            except Exception as e:
                logger.warning(f"Could not delete photo file: {str(e)}")

        # Clear photo field from database
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