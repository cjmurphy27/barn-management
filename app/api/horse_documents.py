from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_
from typing import List, Optional, Dict, Any
import logging
import os
import uuid
import shutil
import mimetypes
from datetime import datetime

from app.database import get_db
from app.models.horse import Horse
from app.models.horse_document import HorseDocument, HorseDocumentAssociation, DocumentTag, DocumentCategory, ProcessingStatus, RelationshipType
from app.schemas.horse_document import (
    DocumentUpload, DocumentResponse, DocumentDetailResponse, 
    DocumentSearchRequest, DocumentUpdateRequest, HorseDocumentSummary,
    DocumentTagCreate, DocumentTagResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/horses", tags=["Horse Documents"])

# File storage configuration
UPLOAD_DIR = "storage/horse_documents"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".jpg", ".jpeg", ".png", ".tiff"}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file"""
    
    # Check file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False, f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
    
    # Check file extension
    if file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"File type '{ext}' not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, "Valid"

def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
    """Save uploaded file and return (filename, file_path)"""
    
    # Generate unique filename
    file_uuid = str(uuid.uuid4())
    _, ext = os.path.splitext(file.filename) if file.filename else ("", "")
    filename = f"{file_uuid}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return filename, file_path

@router.post("/{horse_id}/documents", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def upload_horse_document(
    horse_id: int,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    document_category: DocumentCategory = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a document for a horse"""
    
    try:
        # Verify horse exists
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if not horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Horse with ID {horse_id} not found"
            )
        
        # Validate file
        is_valid, message = validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Save file
        filename, file_path = save_uploaded_file(file)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file.filename or "")
        file_type = mime_type or "application/octet-stream"
        
        # Create document record
        document = HorseDocument(
            filename=filename,
            original_filename=file.filename or filename,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size,
            title=title or file.filename,
            description=description,
            document_category=document_category,
            processing_status=ProcessingStatus.PENDING
        )
        
        db.add(document)
        db.flush()  # Get the ID
        
        # Create horse-document association
        association = HorseDocumentAssociation(
            document_id=document.id,
            horse_id=horse_id,
            relationship_type=RelationshipType.PRIMARY
        )
        
        db.add(association)
        db.commit()
        db.refresh(document)
        
        logger.info(f"Uploaded document '{filename}' for horse {horse_id}")
        
        return document.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals() and os.path.exists(file_path):
            os.unlink(file_path)
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )

@router.get("/{horse_id}/documents", response_model=List[DocumentResponse])
async def get_horse_documents(
    horse_id: int,
    category: Optional[DocumentCategory] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get documents for a specific horse"""
    
    # Verify horse exists
    horse = db.query(Horse).filter(Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Horse with ID {horse_id} not found"
        )
    
    # Build query
    query = db.query(HorseDocument).join(
        HorseDocumentAssociation, 
        HorseDocument.id == HorseDocumentAssociation.document_id
    ).filter(
        HorseDocumentAssociation.horse_id == horse_id,
        HorseDocument.is_active == True
    )
    
    # Apply category filter
    if category:
        query = query.filter(HorseDocument.document_category == category)
    
    # Order by upload date (newest first)
    documents = query.order_by(desc(HorseDocument.upload_date)).offset(offset).limit(limit).all()
    
    return [doc.to_dict() for doc in documents]

@router.get("/{horse_id}/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_horse_document_detail(
    horse_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific document"""
    
    # Get document with associations and tags
    document = db.query(HorseDocument).options(
        joinedload(HorseDocument.horse_associations),
        joinedload(HorseDocument.tags)
    ).filter(
        HorseDocument.id == document_id,
        HorseDocument.is_active == True
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Verify document is associated with this horse
    horse_association = next(
        (assoc for assoc in document.horse_associations if assoc.horse_id == horse_id), 
        None
    )
    
    if not horse_association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found for horse {horse_id}"
        )
    
    # Get associated horses info
    associated_horses = []
    for assoc in document.horse_associations:
        horse = db.query(Horse).filter(Horse.id == assoc.horse_id).first()
        if horse:
            associated_horses.append({
                "id": horse.id,
                "name": horse.name,
                "relationship_type": assoc.relationship_type.value
            })
    
    # Build response
    result = document.to_dict()
    result["tags"] = [tag.to_dict() for tag in document.tags]
    result["associated_horses"] = associated_horses
    
    return result

@router.get("/{horse_id}/documents/{document_id}/download")
async def download_horse_document(
    horse_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Download a document file"""
    
    # Get document
    document = db.query(HorseDocument).join(
        HorseDocumentAssociation,
        HorseDocument.id == HorseDocumentAssociation.document_id
    ).filter(
        HorseDocument.id == document_id,
        HorseDocumentAssociation.horse_id == horse_id,
        HorseDocument.is_active == True
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk"
        )
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type=document.file_type
    )

@router.put("/{horse_id}/documents/{document_id}", response_model=DocumentResponse)
async def update_horse_document(
    horse_id: int,
    document_id: int,
    update_data: DocumentUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update document metadata"""
    
    # Get document
    document = db.query(HorseDocument).join(
        HorseDocumentAssociation,
        HorseDocument.id == HorseDocumentAssociation.document_id
    ).filter(
        HorseDocument.id == document_id,
        HorseDocumentAssociation.horse_id == horse_id,
        HorseDocument.is_active == True
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update fields
    if update_data.title is not None:
        document.title = update_data.title
    if update_data.description is not None:
        document.description = update_data.description
    if update_data.document_category is not None:
        document.document_category = update_data.document_category
    
    db.commit()
    db.refresh(document)
    
    logger.info(f"Updated document {document_id} for horse {horse_id}")
    
    return document.to_dict()

@router.delete("/{horse_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_horse_document(
    horse_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document (soft delete)"""
    
    # Get document
    document = db.query(HorseDocument).join(
        HorseDocumentAssociation,
        HorseDocument.id == HorseDocumentAssociation.document_id
    ).filter(
        HorseDocument.id == document_id,
        HorseDocumentAssociation.horse_id == horse_id,
        HorseDocument.is_active == True
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Soft delete
    document.is_active = False
    db.commit()
    
    logger.info(f"Deleted document {document_id} for horse {horse_id}")

@router.get("/{horse_id}/documents/summary", response_model=HorseDocumentSummary)
async def get_horse_document_summary(
    horse_id: int,
    db: Session = Depends(get_db)
):
    """Get document summary for a horse"""
    
    # Verify horse exists
    horse = db.query(Horse).filter(Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Horse with ID {horse_id} not found"
        )
    
    # Get all documents for this horse
    documents = db.query(HorseDocument).join(
        HorseDocumentAssociation,
        HorseDocument.id == HorseDocumentAssociation.document_id
    ).filter(
        HorseDocumentAssociation.horse_id == horse_id,
        HorseDocument.is_active == True
    ).all()
    
    # Count by category
    documents_by_category = {}
    for doc in documents:
        category = doc.document_category.value
        documents_by_category[category] = documents_by_category.get(category, 0) + 1
    
    # Get recent documents (last 5)
    recent_documents = sorted(documents, key=lambda x: x.upload_date, reverse=True)[:5]
    
    return {
        "horse_id": horse_id,
        "horse_name": horse.name,
        "total_documents": len(documents),
        "documents_by_category": documents_by_category,
        "recent_documents": [doc.to_dict() for doc in recent_documents]
    }