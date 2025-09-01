from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Import enums from the model
from app.models.horse_document import DocumentCategory, ProcessingStatus, RelationshipType

# Document Schemas

class DocumentUpload(BaseModel):
    """Schema for document upload request"""
    title: Optional[str] = Field(None, max_length=255, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    document_category: DocumentCategory = Field(..., description="Document category")
    horse_ids: List[int] = Field(..., min_items=1, description="Horse IDs to associate with this document")

class DocumentTagCreate(BaseModel):
    """Schema for creating document tags"""
    tag_category: str = Field(..., min_length=1, max_length=50, description="Tag category")
    tag_value: str = Field(..., min_length=1, max_length=255, description="Tag value")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")

class DocumentTagResponse(DocumentTagCreate):
    """Schema for document tag response"""
    id: int
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    uuid: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    title: Optional[str]
    description: Optional[str]
    document_category: DocumentCategory
    ai_summary: Optional[str]
    ai_keywords: Optional[List[str]]
    processing_status: ProcessingStatus
    upload_date: datetime
    processed_date: Optional[datetime]
    is_active: bool
    horse_count: int
    
    class Config:
        from_attributes = True

class DocumentDetailResponse(DocumentResponse):
    """Extended document response with tags and horses"""
    tags: List[DocumentTagResponse] = []
    associated_horses: List[dict] = []  # Will contain horse basic info
    
    class Config:
        from_attributes = True

class HorseDocumentAssociationResponse(BaseModel):
    """Schema for horse-document association response"""
    id: int
    document_id: int
    horse_id: int
    relationship_type: RelationshipType
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentSearchRequest(BaseModel):
    """Schema for document search request"""
    query: Optional[str] = Field(None, description="Search query")
    horse_id: Optional[int] = Field(None, description="Filter by horse ID")
    document_category: Optional[DocumentCategory] = Field(None, description="Filter by category")
    tag_category: Optional[str] = Field(None, description="Filter by tag category")
    tag_value: Optional[str] = Field(None, description="Filter by tag value")
    limit: Optional[int] = Field(50, ge=1, le=100, description="Maximum results")
    offset: Optional[int] = Field(0, ge=0, description="Results offset")

class DocumentProcessingRequest(BaseModel):
    """Schema for requesting document processing"""
    document_id: int = Field(..., description="Document ID to process")
    force_reprocess: Optional[bool] = Field(False, description="Force reprocessing even if already processed")

class DocumentUpdateRequest(BaseModel):
    """Schema for updating document metadata"""
    title: Optional[str] = Field(None, max_length=255, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    document_category: Optional[DocumentCategory] = Field(None, description="Document category")
    
class HorseDocumentSummary(BaseModel):
    """Schema for horse document summary"""
    horse_id: int
    horse_name: str
    total_documents: int
    documents_by_category: dict  # category -> count
    recent_documents: List[DocumentResponse]
    
    class Config:
        from_attributes = True