from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Enums for choices
class GenderType(str, Enum):
    MARE = "Mare"
    STALLION = "Stallion"
    GELDING = "Gelding"

class HealthStatus(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    CRITICAL = "Critical"

class BoardingType(str, Enum):
    FULL_CARE = "Full Care"
    PARTIAL_CARE = "Partial Care"
    SELF_CARE = "Self Care"
    PASTURE_BOARD = "Pasture Board"

class HealthRecordType(str, Enum):
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

# Base Horse Schema
class HorseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Horse's registered name")
    barn_name: Optional[str] = Field(None, max_length=100, description="Nickname or barn call name")
    breed: Optional[str] = Field(None, max_length=50, description="Horse breed")
    color: Optional[str] = Field(None, max_length=30, description="Horse color")
    markings: Optional[str] = Field(None, description="White markings, scars, distinctive features")
    
    # Age information
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    age_years: Optional[int] = Field(None, ge=0, le=50, description="Age in years")
    age_months: Optional[int] = Field(None, ge=0, le=11, description="Additional months")
    birth_location: Optional[str] = Field(None, max_length=100, description="Place of birth")
    
    # Physical characteristics
    gender: Optional[GenderType] = Field(None, description="Horse gender")
    height_hands: Optional[float] = Field(None, ge=8.0, le=22.0, description="Height in hands")
    weight_lbs: Optional[int] = Field(None, ge=200, le=3000, description="Weight in pounds")
    body_condition_score: Optional[float] = Field(None, ge=1.0, le=9.0, description="Body condition score (1-9)")
    
    # Registration information
    registration_number: Optional[str] = Field(None, max_length=50, description="Registration number")
    registration_organization: Optional[str] = Field(None, max_length=100, description="Registry organization")
    microchip_number: Optional[str] = Field(None, max_length=50, description="Microchip ID")
    passport_number: Optional[str] = Field(None, max_length=50, description="Passport number")
    
    # Ownership
    owner_name: Optional[str] = Field(None, max_length=100, description="Owner's name")
    owner_contact: Optional[str] = Field(None, max_length=200, description="Owner contact information")
    lease_information: Optional[str] = Field(None, description="Lease details if applicable")
    insurance_info: Optional[str] = Field(None, description="Insurance information")
    
    # Location and management
    current_location: Optional[str] = Field(None, max_length=200, description="Current location/facility")
    stall_number: Optional[str] = Field(None, max_length=20, description="Stall or paddock number")
    pasture_group: Optional[str] = Field(None, max_length=50, description="Pasture group or turnout")
    boarding_type: Optional[BoardingType] = Field(None, description="Type of boarding arrangement")
    
    # Training information
    training_level: Optional[str] = Field(None, max_length=50, description="Current training level")
    disciplines: Optional[str] = Field(None, max_length=200, description="Riding disciplines")
    trainer_name: Optional[str] = Field(None, max_length=100, description="Trainer's name")
    trainer_contact: Optional[str] = Field(None, max_length=200, description="Trainer contact info")
    
    # Health status
    current_health_status: Optional[HealthStatus] = Field(HealthStatus.GOOD, description="Current health status")
    special_needs: Optional[str] = Field(None, description="Special care requirements")
    allergies: Optional[str] = Field(None, description="Known allergies")
    medications: Optional[str] = Field(None, description="Current medications")
    
    # Emergency contacts
    emergency_contact_name: Optional[str] = Field(None, max_length=100, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="Emergency phone number")
    veterinarian_name: Optional[str] = Field(None, max_length=100, description="Primary veterinarian")
    veterinarian_contact: Optional[str] = Field(None, max_length=200, description="Vet contact information")
    last_vet_visit: Optional[date] = None
    last_dental: Optional[date] = None
    last_farrier: Optional[date] = None
    last_deworming: Optional[date] = None
    vet_visit_notes: Optional[str] = None
    dental_notes: Optional[str] = None
    farrier_notes: Optional[str] = None
    deworming_notes: Optional[str] = None

    # Additional information
    notes: Optional[str] = Field(None, description="General notes")
    special_instructions: Optional[str] = Field(None, description="Special care instructions")
    profile_photo_path: Optional[str] = Field(None, description="Path to profile photo")
    
    # Status flags
    is_active: bool = Field(True, description="Whether horse is currently active")
    is_retired: bool = Field(False, description="Whether horse is retired")
    is_for_sale: bool = Field(False, description="Whether horse is for sale")
    
    # Multi-tenant fields
    organization_id: Optional[str] = Field(None, description="Organization/facility ID")

    @validator('height_hands')
    def validate_height(cls, v):
        if v is not None and (v < 8.0 or v > 22.0):
            raise ValueError('Height must be between 8.0 and 22.0 hands')
        return v

    @validator('body_condition_score')
    def validate_bcs(cls, v):
        if v is not None and (v < 1.0 or v > 9.0):
            raise ValueError('Body condition score must be between 1.0 and 9.0')
        return v

# Create Horse Schema
class HorseCreate(HorseBase):
    pass

# Update Horse Schema (all fields optional)
class HorseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    barn_name: Optional[str] = Field(None, max_length=100)
    breed: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=30)
    markings: Optional[str] = None
    date_of_birth: Optional[date] = None
    age_years: Optional[int] = Field(None, ge=0, le=50)
    age_months: Optional[int] = Field(None, ge=0, le=11)
    birth_location: Optional[str] = Field(None, max_length=100)
    gender: Optional[GenderType] = None
    height_hands: Optional[float] = Field(None, ge=8.0, le=22.0)
    weight_lbs: Optional[int] = Field(None, ge=200, le=3000)
    body_condition_score: Optional[float] = Field(None, ge=1.0, le=9.0)
    registration_number: Optional[str] = Field(None, max_length=50)
    registration_organization: Optional[str] = Field(None, max_length=100)
    microchip_number: Optional[str] = Field(None, max_length=50)
    passport_number: Optional[str] = Field(None, max_length=50)
    owner_name: Optional[str] = Field(None, max_length=100)
    owner_contact: Optional[str] = Field(None, max_length=200)
    lease_information: Optional[str] = None
    insurance_info: Optional[str] = None
    current_location: Optional[str] = Field(None, max_length=200)
    stall_number: Optional[str] = Field(None, max_length=20)
    pasture_group: Optional[str] = Field(None, max_length=50)
    boarding_type: Optional[BoardingType] = None
    training_level: Optional[str] = Field(None, max_length=50)
    disciplines: Optional[str] = Field(None, max_length=200)
    trainer_name: Optional[str] = Field(None, max_length=100)
    trainer_contact: Optional[str] = Field(None, max_length=200)
    current_health_status: Optional[HealthStatus] = None
    special_needs: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    veterinarian_name: Optional[str] = Field(None, max_length=100)
    veterinarian_contact: Optional[str] = Field(None, max_length=200)
    last_vet_visit: Optional[date] = None
    last_dental: Optional[date] = None
    last_farrier: Optional[date] = None
    last_deworming: Optional[date] = None
    vet_visit_notes: Optional[str] = None
    dental_notes: Optional[str] = None
    farrier_notes: Optional[str] = None
    deworming_notes: Optional[str] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    is_active: Optional[bool] = None
    is_retired: Optional[bool] = None
    is_for_sale: Optional[bool] = None

# Response Schemas
class HorseListResponse(BaseModel):
    id: int
    uuid: str
    name: str
    barn_name: Optional[str]
    breed: Optional[str]
    color: Optional[str]
    age_display: str
    gender: Optional[str]
    current_health_status: str
    current_location: Optional[str]
    stall_number: Optional[str]
    owner_name: Optional[str]
    is_active: bool
    is_retired: bool
    is_for_sale: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class HorseResponse(HorseListResponse):
    # Include all fields from HorseBase plus computed fields
    markings: Optional[str]
    date_of_birth: Optional[date]
    age_years: Optional[int]
    age_months: Optional[int]
    birth_location: Optional[str]
    height_hands: Optional[float]
    weight_lbs: Optional[int]
    body_condition_score: Optional[float]
    registration_number: Optional[str]
    registration_organization: Optional[str]
    microchip_number: Optional[str]
    passport_number: Optional[str]
    owner_contact: Optional[str]
    lease_information: Optional[str]
    insurance_info: Optional[str]
    pasture_group: Optional[str]
    boarding_type: Optional[str]
    training_level: Optional[str]
    disciplines: Optional[str]
    trainer_name: Optional[str]
    trainer_contact: Optional[str]
    special_needs: Optional[str]
    allergies: Optional[str]
    medications: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    veterinarian_name: Optional[str]
    veterinarian_contact: Optional[str]
    farrier_name: Optional[str]
    last_vet_visit: Optional[date]
    last_dental: Optional[date]
    last_farrier: Optional[date]
    last_deworming: Optional[date]
    vet_visit_notes: Optional[str]
    dental_notes: Optional[str]
    farrier_notes: Optional[str]
    deworming_notes: Optional[str]
    notes: Optional[str]
    special_instructions: Optional[str]
    organization_id: Optional[str]

    class Config:
        from_attributes = True
