from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional
import enum
import uuid

Base = declarative_base()

class HealthRecordType(enum.Enum):
    VACCINATION = "vaccination"
    MEDICAL_TREATMENT = "medical_treatment"
    VET_VISIT = "vet_visit"
    DENTAL_WORK = "dental_work"
    FARRIER_VISIT = "farrier_visit"
    INJURY = "injury"
    ILLNESS = "illness"
    ROUTINE_CHECKUP = "routine_checkup"
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    BLOODWORK = "bloodwork"
    OTHER = "other"

class HealthRecord(Base):
    __tablename__ = "health_records"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key to horse
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False, index=True)
    
    # Record details
    record_type = Column(Enum(HealthRecordType), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Date information
    date_performed = Column(Date, nullable=False, index=True)
    date_due = Column(Date, nullable=True, index=True)  # For follow-ups or next due date
    
    # Provider information
    veterinarian_name = Column(String(100), nullable=True)
    veterinarian_practice = Column(String(100), nullable=True)
    veterinarian_contact = Column(String(200), nullable=True)
    provider_license = Column(String(50), nullable=True)
    
    # Treatment/Procedure details
    procedure_name = Column(String(200), nullable=True)
    medications_given = Column(Text, nullable=True)
    dosage_instructions = Column(Text, nullable=True)
    treatment_duration = Column(String(100), nullable=True)
    
    # Vaccination specific fields
    vaccine_name = Column(String(100), nullable=True)
    vaccine_manufacturer = Column(String(100), nullable=True)
    vaccine_batch_lot = Column(String(50), nullable=True)
    vaccine_expiration = Column(Date, nullable=True)
    
    # Results and findings
    findings = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    test_results = Column(Text, nullable=True)
    temperature = Column(Float, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    weight = Column(Float, nullable=True)
    
    # Cost information
    cost = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    invoice_number = Column(String(50), nullable=True)
    
    # Follow-up and status
    follow_up_required = Column(Boolean, default=False)
    follow_up_instructions = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    status = Column(String(20), default="completed")  # completed, pending, scheduled, cancelled
    
    # Severity and priority
    severity = Column(String(10), nullable=True)  # low, medium, high, critical
    priority = Column(String(10), nullable=True)  # routine, urgent, emergency
    
    # Files and documentation
    file_attachments = Column(Text, nullable=True)  # JSON list of file paths
    photos = Column(Text, nullable=True)  # JSON list of photo paths
    documents = Column(Text, nullable=True)  # JSON list of document paths
    
    # Administrative
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Private notes not shared
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    horse = relationship("Horse", back_populates="health_records")
    
    def __repr__(self):
        return f"<HealthRecord(horse_id={self.horse_id}, type='{self.record_type}', date='{self.date_performed}')>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if a follow-up or recurring item is overdue"""
        if self.date_due and self.status in ["pending", "scheduled"]:
            return date.today() > self.date_due
        return False
    
    @property
    def is_due_soon(self, days_ahead: int = 30) -> bool:
        """Check if item is due within specified days"""
        if self.date_due and self.status in ["pending", "scheduled"]:
            days_until_due = (self.date_due - date.today()).days
            return 0 <= days_until_due <= days_ahead
        return False


class FeedingRecord(Base):
    __tablename__ = "feeding_records"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key to horse
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False, index=True)
    
    # Feed details
    feed_type = Column(String(100), nullable=False)  # Hay, Grain, Supplement, etc.
    feed_brand = Column(String(100), nullable=True)
    feed_description = Column(Text, nullable=True)
    
    # Quantities
    amount = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # lbs, cups, scoops, flakes
    
    # Timing
    feeding_time = Column(DateTime, nullable=False)
    feeding_schedule = Column(String(50), nullable=True)  # AM, PM, MID, etc.
    
    # Cost tracking
    cost_per_unit = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    fed_by = Column(String(100), nullable=True)
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    horse = relationship("Horse", back_populates="feeding_records")
    
    def __repr__(self):
        return f"<FeedingRecord(horse_id={self.horse_id}, feed_type='{self.feed_type}', amount={self.amount})>"
