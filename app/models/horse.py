from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional
import uuid

# Import Base from database.py instead of creating a new one
from app.database import Base

class Horse(Base):
    __tablename__ = "horses"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic Information
    name = Column(String(100), nullable=False, index=True)
    barn_name = Column(String(100), nullable=True)  # Nickname/barn call name
    breed = Column(String(50), nullable=True)
    color = Column(String(30), nullable=True)
    markings = Column(Text, nullable=True)  # White markings, scars, etc.
    
    # Age & Birth Information
    date_of_birth = Column(Date, nullable=True)
    age_years = Column(Integer, nullable=True)
    age_months = Column(Integer, nullable=True)
    birth_location = Column(String(100), nullable=True)
    
    # Physical Characteristics
    gender = Column(String(10), nullable=True)  # Mare, Stallion, Gelding
    height_hands = Column(Float, nullable=True)  # Height in hands
    weight_lbs = Column(Integer, nullable=True)  # Weight in pounds
    body_condition_score = Column(Float, nullable=True)  # 1-9 scale
    
    # Registration & Identification
    registration_number = Column(String(50), nullable=True)
    registration_organization = Column(String(100), nullable=True)
    microchip_number = Column(String(50), nullable=True)
    passport_number = Column(String(50), nullable=True)
    
    # Ownership Information
    owner_name = Column(String(100), nullable=True)
    owner_contact = Column(String(200), nullable=True)
    lease_information = Column(Text, nullable=True)
    insurance_info = Column(Text, nullable=True)
    
    # Location & Management
    current_location = Column(String(200), nullable=True)
    stall_number = Column(String(20), nullable=True)
    pasture_group = Column(String(50), nullable=True)
    boarding_type = Column(String(50), nullable=True)  # Full, Partial, Self-care
    
    # Training & Discipline
    training_level = Column(String(50), nullable=True)
    disciplines = Column(String(200), nullable=True)  # Dressage, Jumping, Western, etc.
    trainer_name = Column(String(100), nullable=True)
    trainer_contact = Column(String(200), nullable=True)
    
    # Health Status
    current_health_status = Column(String(20), default="Good")  # Good, Fair, Poor, Critical
    special_needs = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    
    # Emergency Information
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    veterinarian_name = Column(String(100), nullable=True)
    veterinarian_contact = Column(String(200), nullable=True)
    farrier_name = Column(String(100), nullable=True)
    
    # Care Schedules
    feeding_schedule = Column(Text, nullable=True)
    exercise_schedule = Column(Text, nullable=True)
    
    # Health History Dates
    last_vet_visit = Column(Date, nullable=True)
    last_dental = Column(Date, nullable=True)
    last_farrier = Column(Date, nullable=True)
    last_deworming = Column(Date, nullable=True)

    # Care Visit Notes
    vet_visit_notes = Column(Text, nullable=True)
    dental_notes = Column(Text, nullable=True)
    farrier_notes = Column(Text, nullable=True)
    deworming_notes = Column(Text, nullable=True)

    # Additional Notes
    notes = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    
    # Profile Photo
    profile_photo_path = Column(String(500), nullable=True)  # File path for photo storage
    
    # Status & Flags
    is_active = Column(Boolean, default=True)
    is_retired = Column(Boolean, default=False)
    is_for_sale = Column(Boolean, default=False)
    
    # Multi-tenant support (for future PropelAuth integration)
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - temporarily disabled due to circular import
    # events = relationship("Event", back_populates="horse", cascade="all, delete-orphan")
    # health_records = relationship("HealthRecord", back_populates="horse", cascade="all, delete-orphan")
    # feeding_records = relationship("FeedingRecord", back_populates="horse", cascade="all, delete-orphan")
    
    # Document relationships
    document_associations = relationship("HorseDocumentAssociation", back_populates="horse", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Horse(name='{self.name}', breed='{self.breed}')>"
    
    @property
    def age_display(self) -> str:
        """Return a human-readable age string"""
        if self.date_of_birth:
            today = date.today()
            age = today - self.date_of_birth
            years = age.days // 365
            months = (age.days % 365) // 30
            return f"{years} years, {months} months"
        elif self.age_years:
            months_str = f", {self.age_months} months" if self.age_months else ""
            return f"{self.age_years} years{months_str}"
        return "Age unknown"
    
    @property
    def display_name(self) -> str:
        """Return the preferred display name"""
        if self.barn_name and self.barn_name != self.name:
            return f"{self.name} ({self.barn_name})"
        return self.name
    
    def to_dict(self) -> dict:
        """Convert horse object to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "barn_name": self.barn_name,
            "breed": self.breed,
            "color": self.color,
            "markings": self.markings,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age_display": self.age_display,
            "gender": self.gender,
            "height_hands": self.height_hands,
            "weight_lbs": self.weight_lbs,
            "body_condition_score": self.body_condition_score,
            "registration_number": self.registration_number,
            "registration_organization": self.registration_organization,
            "microchip_number": self.microchip_number,
            "owner_name": self.owner_name,
            "owner_contact": self.owner_contact,
            "current_location": self.current_location,
            "stall_number": self.stall_number,
            "pasture_group": self.pasture_group,
            "boarding_type": self.boarding_type,
            "training_level": self.training_level,
            "disciplines": self.disciplines,
            "trainer_name": self.trainer_name,
            "trainer_contact": self.trainer_contact,
            "feeding_schedule": self.feeding_schedule,
            "exercise_schedule": self.exercise_schedule,
            "current_health_status": self.current_health_status,
            "special_needs": self.special_needs,
            "allergies": self.allergies,
            "medications": self.medications,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "veterinarian_name": self.veterinarian_name,
            "veterinarian_contact": self.veterinarian_contact,
            "farrier_name": self.farrier_name,
            "last_vet_visit": self.last_vet_visit.isoformat() if self.last_vet_visit else None,
            "last_dental": self.last_dental.isoformat() if self.last_dental else None,
            "last_farrier": self.last_farrier.isoformat() if self.last_farrier else None,
            "last_deworming": self.last_deworming.isoformat() if self.last_deworming else None,
            "vet_visit_notes": self.vet_visit_notes,
            "dental_notes": self.dental_notes,
            "farrier_notes": self.farrier_notes,
            "deworming_notes": self.deworming_notes,
            "notes": self.notes,
            "profile_photo_path": self.profile_photo_path,
            "is_active": self.is_active,
            "is_retired": self.is_retired,
            "is_for_sale": self.is_for_sale,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
