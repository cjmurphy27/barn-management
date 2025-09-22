from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
import uuid
import shutil
import mimetypes
from datetime import datetime

from app.database import get_db
from app.models.whiteboard import WhiteboardPost, WhiteboardComment, WhiteboardAttachment, PostCategory, PostStatus
from app.schemas.whiteboard import (
    WhiteboardPostCreate, WhiteboardPostUpdate, WhiteboardPostResponse,
    WhiteboardPostListResponse, WhiteboardPostDetailResponse,
    WhiteboardCommentCreate, WhiteboardCommentUpdate, WhiteboardCommentResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["whiteboard"])

# File storage configuration
UPLOAD_DIR = "storage/whiteboard_images"
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

def save_uploaded_image(file: UploadFile, organization_id: str) -> tuple[str, str]:
    """Save uploaded image and return (filename, file_path)"""

    # Generate unique filename
    file_uuid = str(uuid.uuid4())
    original_filename = file.filename or "unknown"
    _, ext = os.path.splitext(original_filename.lower())
    filename = f"{file_uuid}{ext}"

    # Create organization subdirectory
    org_dir = os.path.join(UPLOAD_DIR, organization_id)
    os.makedirs(org_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(org_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return filename, file_path

# Custom authentication that uses JWT parsing (matching existing pattern)
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

@router.get("/whiteboard/posts", response_model=WhiteboardPostListResponse)
async def get_whiteboard_posts(
    organization_id: str = Query(..., description="Organization/barn ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[PostCategory] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    pinned_only: bool = Query(False, description="Show only pinned posts"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Get whiteboard posts for a specific barn"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Build query
        query = db.query(WhiteboardPost).filter(
            WhiteboardPost.organization_id == organization_id,
            WhiteboardPost.status == PostStatus.ACTIVE
        )

        # Apply filters
        if category:
            query = query.filter(WhiteboardPost.category == category)

        if pinned_only:
            query = query.filter(WhiteboardPost.is_pinned == True)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (WhiteboardPost.title.ilike(search_term)) |
                (WhiteboardPost.content.ilike(search_term))
            )

        # Order by: pinned first, then by creation date
        query = query.order_by(
            WhiteboardPost.is_pinned.desc(),
            WhiteboardPost.created_at.desc()
        )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        posts = query.offset(offset).limit(page_size).all()

        # Convert to response format
        post_responses = [
            WhiteboardPostResponse(**post.to_dict()) for post in posts
        ]

        return WhiteboardPostListResponse(
            posts=post_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_prev=page > 1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting whiteboard posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve posts"
        )

@router.post("/whiteboard/posts", response_model=WhiteboardPostResponse, status_code=status.HTTP_201_CREATED)
async def create_whiteboard_post(
    organization_id: str = Query(..., description="Organization/barn ID"),
    post_data: WhiteboardPostCreate = ...,
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Create a new whiteboard post"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Get user's name - use email as display name if no proper name available
        user_email = user_data.get("email", "Unknown User")
        # Extract display name from email (e.g., "chris@carril.com" -> "Chris")
        display_name = user_email.split("@")[0].title() if user_email and "@" in user_email else user_email
        # Use display name with email for full signature
        user_name = f"{display_name} ({user_email})" if user_email != "Unknown User" else display_name

        # Create post
        post_dict = post_data.dict()
        post_dict.update({
            "organization_id": organization_id,
            "author_name": user_name,
            "author_email": user_data.get("email"),
            "author_user_id": user_data.get("user_id")
        })

        db_post = WhiteboardPost(**post_dict)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        logger.info(f"Created whiteboard post '{db_post.title}' by {user_name} in organization {organization_id}")

        return WhiteboardPostResponse(**db_post.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating whiteboard post: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create post"
        )

@router.post("/whiteboard/posts/with-image", response_model=WhiteboardPostResponse, status_code=status.HTTP_201_CREATED)
async def create_whiteboard_post_with_image(
    organization_id: str = Query(..., description="Organization/barn ID"),
    title: str = Form(..., description="Post title"),
    content: str = Form(..., description="Post content"),
    category: str = Form("general", description="Post category"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    is_pinned: bool = Form(False, description="Pin this post to the top"),
    image: Optional[UploadFile] = File(None, description="Optional image attachment"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Create a new whiteboard post with optional image attachment"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Validate image if provided
        attachment_id = None
        if image and image.filename:
            is_valid, error_msg = validate_image_file(image)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)

        # Get user's name - use email as display name if no proper name available
        user_email = user_data.get("email", "Unknown User")
        display_name = user_email.split("@")[0].title() if user_email and "@" in user_email else user_email
        user_name = f"{display_name} ({user_email})" if user_email != "Unknown User" else display_name

        # Create post
        post_dict = {
            "title": title.strip(),
            "content": content.strip(),
            "category": PostCategory(category) if category else PostCategory.GENERAL,
            "tags": tags.strip() if tags and tags.strip() else None,
            "is_pinned": is_pinned,
            "organization_id": organization_id,
            "author_name": user_name,
            "author_email": user_data.get("email"),
            "author_user_id": user_data.get("user_id")
        }

        db_post = WhiteboardPost(**post_dict)
        db.add(db_post)
        db.flush()  # Get the post ID

        # Handle image upload if provided
        if image and image.filename:
            try:
                # Save the image file
                filename, file_path = save_uploaded_image(image, organization_id)

                # Create attachment record
                attachment_dict = {
                    "filename": filename,
                    "original_filename": image.filename,
                    "file_path": file_path,
                    "file_size": getattr(image, 'size', None),
                    "mime_type": image.content_type or mimetypes.guess_type(image.filename)[0],
                    "attachment_type": "image",
                    "is_primary": True,  # First image is primary
                    "post_id": db_post.id,
                    "uploaded_by_user_id": user_data.get("user_id"),
                    "uploaded_by_name": user_name,
                    "organization_id": organization_id
                }

                db_attachment = WhiteboardAttachment(**attachment_dict)
                db.add(db_attachment)

                logger.info(f"Saved image {filename} for post {db_post.id}")

            except Exception as e:
                logger.error(f"Error saving image: {str(e)}")
                # Don't fail the post creation if image save fails
                # Just log the error and continue

        db.commit()
        db.refresh(db_post)

        logger.info(f"Created whiteboard post '{db_post.title}' by {user_name} in organization {organization_id}")

        return WhiteboardPostResponse(**db_post.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating whiteboard post with image: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create post"
        )

@router.get("/whiteboard/posts/{post_id}", response_model=WhiteboardPostDetailResponse)
async def get_whiteboard_post(
    post_id: int,
    organization_id: str = Query(..., description="Organization/barn ID"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Get a specific whiteboard post with comments and attachments"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Get post
        post = db.query(WhiteboardPost).filter(
            WhiteboardPost.id == post_id,
            WhiteboardPost.organization_id == organization_id,
            WhiteboardPost.status == PostStatus.ACTIVE
        ).first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Get comments (ordered by creation date)
        comments = db.query(WhiteboardComment).filter(
            WhiteboardComment.post_id == post_id,
            WhiteboardComment.organization_id == organization_id
        ).order_by(WhiteboardComment.created_at.asc()).all()

        # Get attachments
        attachments = db.query(WhiteboardAttachment).filter(
            WhiteboardAttachment.post_id == post_id,
            WhiteboardAttachment.organization_id == organization_id
        ).order_by(WhiteboardAttachment.created_at.asc()).all()

        # Convert to response format
        post_dict = post.to_dict()
        post_dict["comments"] = [WhiteboardCommentResponse(**comment.to_dict()) for comment in comments]
        post_dict["attachments"] = [attachment.to_dict() for attachment in attachments]

        return WhiteboardPostDetailResponse(**post_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting whiteboard post {post_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve post"
        )

@router.post("/whiteboard/posts/{post_id}/comments", response_model=WhiteboardCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    organization_id: str = Query(..., description="Organization/barn ID"),
    comment_data: WhiteboardCommentCreate = ...,
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Add a comment to a whiteboard post"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Verify post exists and belongs to organization
        post = db.query(WhiteboardPost).filter(
            WhiteboardPost.id == post_id,
            WhiteboardPost.organization_id == organization_id,
            WhiteboardPost.status == PostStatus.ACTIVE
        ).first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Get user's name - use email as display name if no proper name available
        user_email = user_data.get("email", "Unknown User")
        # Extract display name from email (e.g., "chris@carril.com" -> "Chris")
        display_name = user_email.split("@")[0].title() if user_email and "@" in user_email else user_email
        # Use display name with email for full signature
        user_name = f"{display_name} ({user_email})" if user_email != "Unknown User" else display_name

        # Create comment
        comment_dict = comment_data.dict()
        comment_dict.update({
            "post_id": post_id,
            "organization_id": organization_id,
            "author_name": user_name,
            "author_email": user_data.get("email"),
            "author_user_id": user_data.get("user_id")
        })

        db_comment = WhiteboardComment(**comment_dict)
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)

        logger.info(f"Created comment on post {post_id} by {user_name} in organization {organization_id}")

        return WhiteboardCommentResponse(**db_comment.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create comment"
        )

@router.delete("/whiteboard/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_whiteboard_post(
    post_id: int,
    organization_id: str = Query(..., description="Organization/barn ID"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Delete a whiteboard post (only by author)"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Get post and verify ownership
        post = db.query(WhiteboardPost).filter(
            WhiteboardPost.id == post_id,
            WhiteboardPost.organization_id == organization_id,
            WhiteboardPost.status == PostStatus.ACTIVE
        ).first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check if user is the author
        user_email = user_data.get("email")
        if post.author_email != user_email:
            raise HTTPException(status_code=403, detail="You can only delete your own posts")

        # Mark post as deleted (soft delete)
        post.status = PostStatus.DELETED
        db.commit()

        logger.info(f"Deleted whiteboard post {post_id} by {user_email} in organization {organization_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting whiteboard post {post_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete post"
        )

@router.get("/whiteboard/images/{attachment_id}")
async def get_whiteboard_image(
    attachment_id: int,
    organization_id: str = Query(..., description="Organization/barn ID"),
    user_data: dict = Depends(get_jwt_user_required),
    db: Session = Depends(get_db)
):
    """Get a whiteboard image attachment"""
    try:
        # Verify user has access to this organization
        user_orgs = [org["barn_id"] for org in user_data.get("organizations", [])]
        if organization_id not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied to this barn")

        # Get attachment
        attachment = db.query(WhiteboardAttachment).filter(
            WhiteboardAttachment.id == attachment_id,
            WhiteboardAttachment.organization_id == organization_id,
            WhiteboardAttachment.attachment_type == "image"
        ).first()

        if not attachment:
            raise HTTPException(status_code=404, detail="Image not found")

        # Check if file exists
        if not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=404, detail="Image file not found on disk")

        # Return the file
        return FileResponse(
            path=attachment.file_path,
            media_type=attachment.mime_type or "image/jpeg",
            filename=attachment.original_filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {attachment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to serve image"
        )