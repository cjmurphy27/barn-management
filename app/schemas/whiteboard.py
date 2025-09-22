from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.whiteboard import PostCategory, PostStatus

# Base schemas
class WhiteboardPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, description="Post content")
    category: PostCategory = Field(default=PostCategory.GENERAL, description="Post category")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")

class WhiteboardCommentBase(BaseModel):
    content: str = Field(..., min_length=1, description="Comment content")
    parent_comment_id: Optional[int] = Field(None, description="Parent comment ID for replies")

# Create schemas
class WhiteboardPostCreate(WhiteboardPostBase):
    is_pinned: Optional[bool] = Field(default=False, description="Pin this post to the top")

class WhiteboardCommentCreate(WhiteboardCommentBase):
    post_id: int = Field(..., description="Post ID this comment belongs to")

# Update schemas
class WhiteboardPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[PostCategory] = None
    status: Optional[PostStatus] = None
    is_pinned: Optional[bool] = None
    tags: Optional[str] = Field(None, max_length=500)

class WhiteboardCommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)

# Response schemas
class WhiteboardAttachmentResponse(BaseModel):
    id: int
    uuid: str
    filename: str
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    attachment_type: str
    is_primary: bool
    uploaded_by_name: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class WhiteboardCommentResponse(BaseModel):
    id: int
    uuid: str
    content: str
    post_id: int
    parent_comment_id: Optional[int]
    author_name: str
    author_email: Optional[str]
    author_user_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    reply_count: int

    class Config:
        from_attributes = True

class WhiteboardPostResponse(BaseModel):
    id: int
    uuid: str
    title: str
    content: str
    category: str
    status: str
    is_pinned: bool
    tags: List[str]
    author_name: str
    author_email: Optional[str]
    author_user_id: Optional[str]
    organization_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    comment_count: int
    attachment_count: int

    class Config:
        from_attributes = True

# List response with pagination info
class WhiteboardPostListResponse(BaseModel):
    posts: List[WhiteboardPostResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

# Detailed response with comments and attachments
class WhiteboardPostDetailResponse(WhiteboardPostResponse):
    comments: List[WhiteboardCommentResponse]
    attachments: List[WhiteboardAttachmentResponse]

    class Config:
        from_attributes = True