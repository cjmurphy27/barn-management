from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid
import enum

from app.database import Base

class PostCategory(str, enum.Enum):
    GENERAL = "general"
    ANNOUNCEMENT = "announcement"
    MAINTENANCE = "maintenance"
    HEALTH_ALERT = "health_alert"
    TRAINING = "training"
    SUPPLIES = "supplies"
    WEATHER = "weather"
    EMERGENCY = "emergency"
    OTHER = "other"

class PostStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    PINNED = "pinned"
    DELETED = "deleted"

class WhiteboardPost(Base):
    """Whiteboard posts for barn communication"""
    __tablename__ = "whiteboard_posts"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)

    # Post Content
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(Enum(PostCategory), default=PostCategory.GENERAL, index=True)
    status = Column(Enum(PostStatus), default=PostStatus.ACTIVE, index=True)

    # Post Metadata
    is_pinned = Column(Boolean, default=False)
    tags = Column(String(500), nullable=True)  # Comma-separated tags

    # Author Information
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(200), nullable=True)
    author_user_id = Column(String(100), nullable=True, index=True)  # PropelAuth user ID

    # Multi-tenant support (barn isolation)
    organization_id = Column(String(100), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    comments = relationship("WhiteboardComment", back_populates="post", cascade="all, delete-orphan")
    attachments = relationship("WhiteboardAttachment", back_populates="post", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "title": self.title,
            "content": self.content,
            "category": self.category.value if self.category else None,
            "status": self.status.value if self.status else None,
            "is_pinned": self.is_pinned,
            "tags": self.tags.split(",") if self.tags else [],
            "author_name": self.author_name,
            "author_email": self.author_email,
            "author_user_id": self.author_user_id,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "comment_count": len(self.comments) if self.comments else 0,
            "attachment_count": len(self.attachments) if self.attachments else 0
        }

class WhiteboardComment(Base):
    """Comments on whiteboard posts"""
    __tablename__ = "whiteboard_comments"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)

    # Comment Content
    content = Column(Text, nullable=False)

    # Relationships
    post_id = Column(Integer, ForeignKey("whiteboard_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_comment_id = Column(Integer, ForeignKey("whiteboard_comments.id", ondelete="CASCADE"), nullable=True)  # For replies

    # Author Information
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(200), nullable=True)
    author_user_id = Column(String(100), nullable=True, index=True)  # PropelAuth user ID

    # Multi-tenant support (inherit from post but explicit for queries)
    organization_id = Column(String(100), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    post = relationship("WhiteboardPost", back_populates="comments")
    parent_comment = relationship("WhiteboardComment", remote_side=[id])
    replies = relationship("WhiteboardComment", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "content": self.content,
            "post_id": self.post_id,
            "parent_comment_id": self.parent_comment_id,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "author_user_id": self.author_user_id,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "reply_count": len(self.replies) if self.replies else 0
        }

class WhiteboardAttachment(Base):
    """File attachments for whiteboard posts"""
    __tablename__ = "whiteboard_attachments"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)

    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)

    # Attachment Metadata
    attachment_type = Column(String(50), default="image")  # image, document, video, etc.
    is_primary = Column(Boolean, default=False)  # Primary image for post preview

    # Relationships
    post_id = Column(Integer, ForeignKey("whiteboard_posts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Author Information (who uploaded)
    uploaded_by_user_id = Column(String(100), nullable=True, index=True)
    uploaded_by_name = Column(String(100), nullable=True)

    # Multi-tenant support
    organization_id = Column(String(100), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    post = relationship("WhiteboardPost", back_populates="attachments")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "attachment_type": self.attachment_type,
            "is_primary": self.is_primary,
            "post_id": self.post_id,
            "uploaded_by_user_id": self.uploaded_by_user_id,
            "uploaded_by_name": self.uploaded_by_name,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }