from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Enum, ARRAY, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum
from typing import Optional, List

from app.database import Base

class DocumentCategory(str, enum.Enum):
    MEDICAL_RECORD = "medical_record"
    VETERINARY_REPORT = "veterinary_report"
    VACCINATION_RECORD = "vaccination_record"
    TRAINING_NOTES = "training_notes"
    FEED_EVALUATION = "feed_evaluation"
    BEHAVIORAL_NOTES = "behavioral_notes"
    BREEDING_RECORD = "breeding_record"
    OWNERSHIP_PAPERS = "ownership_papers"
    INSURANCE_DOCUMENT = "insurance_document"
    COMPETITION_RECORD = "competition_record"
    GENERAL = "general"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"

class HorseDocument(Base):
    """Document storage for horses with AI-enhanced metadata"""
    __tablename__ = "horse_documents"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # File information
    filename = Column(String(255), nullable=False)  # Generated filename
    original_filename = Column(String(255), nullable=False)  # User's original filename
    file_path = Column(Text, nullable=False)  # Storage path
    file_type = Column(String(100), nullable=False)  # pdf, docx, txt, jpg, png
    file_size_bytes = Column(BigInteger, nullable=False)
    
    # Content & Metadata
    title = Column(String(255), nullable=True)  # User-provided or AI-generated title
    description = Column(Text, nullable=True)  # User description
    document_category = Column(Enum(DocumentCategory), nullable=False, index=True)
    extracted_text = Column(Text, nullable=True)  # For full-text search
    ai_summary = Column(Text, nullable=True)  # AI-generated summary
    ai_keywords = Column(ARRAY(String), nullable=True)  # AI-extracted keywords
    
    # Processing status
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    processing_error = Column(Text, nullable=True)  # Error details if processing failed
    
    # Timestamps
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    horse_associations = relationship("HorseDocumentAssociation", back_populates="document", cascade="all, delete-orphan")
    tags = relationship("DocumentTag", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HorseDocument(id={self.id}, filename='{self.filename}', category='{self.document_category}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "title": self.title,
            "description": self.description,
            "document_category": self.document_category.value if self.document_category else None,
            "ai_summary": self.ai_summary,
            "ai_keywords": self.ai_keywords,
            "processing_status": self.processing_status.value if self.processing_status else None,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "processed_date": self.processed_date.isoformat() if self.processed_date else None,
            "is_active": self.is_active,
            "horse_count": len(self.horse_associations) if self.horse_associations else 0
        }

class RelationshipType(str, enum.Enum):
    PRIMARY = "primary"  # Primary document for this horse
    REFERENCE = "reference"  # Referenced in relation to this horse
    COMPARISON = "comparison"  # Used for comparison with this horse

class HorseDocumentAssociation(Base):
    """Many-to-many relationship between horses and documents"""
    __tablename__ = "horse_document_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("horse_documents.id", ondelete="CASCADE"), nullable=False)
    horse_id = Column(Integer, ForeignKey("horses.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(Enum(RelationshipType), default=RelationshipType.PRIMARY, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("HorseDocument", back_populates="horse_associations")
    horse = relationship("Horse", back_populates="document_associations")
    
    def __repr__(self):
        return f"<HorseDocumentAssociation(doc_id={self.document_id}, horse_id={self.horse_id}, type='{self.relationship_type}')>"

class DocumentTag(Base):
    """Flexible tagging system for documents"""
    __tablename__ = "document_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("horse_documents.id", ondelete="CASCADE"), nullable=False)
    tag_category = Column(String(50), nullable=False, index=True)  # medical_condition, treatment, feed_type, etc.
    tag_value = Column(String(255), nullable=False, index=True)
    confidence_score = Column(Float, nullable=True)  # For AI-generated tags (0.0-1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("HorseDocument", back_populates="tags")
    
    def __repr__(self):
        return f"<DocumentTag(category='{self.tag_category}', value='{self.tag_value}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "tag_category": self.tag_category,
            "tag_value": self.tag_value,
            "confidence_score": self.confidence_score
        }