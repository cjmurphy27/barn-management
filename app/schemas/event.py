from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Import enums from the model
from app.models.event import EventType, EventStatus, RecurringPattern

# Event Base Schema
class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    event_type: EventType = Field(..., description="Type of event")
    
    # Scheduling
    scheduled_date: datetime = Field(..., description="Scheduled date and time")
    duration_minutes: Optional[int] = Field(60, ge=1, le=1440, description="Duration in minutes")
    
    # Location & Provider
    location: Optional[str] = Field(None, max_length=200, description="Event location")
    provider_name: Optional[str] = Field(None, max_length=100, description="Service provider name")
    provider_contact: Optional[str] = Field(None, max_length=200, description="Provider contact info")
    
    # Management
    status: Optional[EventStatus] = Field(EventStatus.SCHEDULED, description="Event status")
    priority: Optional[str] = Field("medium", description="Priority level")
    
    # Cost Information
    estimated_cost: Optional[float] = Field(None, ge=0, description="Estimated cost")
    actual_cost: Optional[float] = Field(None, ge=0, description="Actual cost")
    cost_notes: Optional[str] = Field(None, description="Cost-related notes")
    
    # Recurring Events
    recurring_pattern: Optional[RecurringPattern] = Field(RecurringPattern.NONE, description="Recurring pattern")
    recurring_interval: Optional[int] = Field(1, ge=1, description="Interval for recurring events")
    recurring_end_date: Optional[date] = Field(None, description="End date for recurring events")
    
    # Horse Association
    horse_id: Optional[int] = Field(None, description="Associated horse ID")
    
    # Additional Information
    notes: Optional[str] = Field(None, description="General notes")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    
    # Weather Considerations
    weather_dependent: Optional[bool] = Field(False, description="Whether event depends on weather")
    indoor_alternative: Optional[bool] = Field(False, description="Whether indoor alternative exists")

    @validator('scheduled_date')
    def validate_scheduled_date(cls, v):
        if v and v < datetime.now():
            # Allow past dates for completed events, but warn
            pass
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v and v not in ['low', 'medium', 'high', 'urgent']:
            raise ValueError('Priority must be one of: low, medium, high, urgent')
        return v

# Create Event Schema
class EventCreate(EventBase):
    pass

# Update Event Schema (all fields optional except ID)
class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    location: Optional[str] = Field(None, max_length=200)
    provider_name: Optional[str] = Field(None, max_length=100)
    provider_contact: Optional[str] = Field(None, max_length=200)
    status: Optional[EventStatus] = None
    priority: Optional[str] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    cost_notes: Optional[str] = None
    recurring_pattern: Optional[RecurringPattern] = None
    recurring_interval: Optional[int] = Field(None, ge=1)
    recurring_end_date: Optional[date] = None
    horse_id: Optional[int] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    completion_notes: Optional[str] = None
    weather_dependent: Optional[bool] = None
    indoor_alternative: Optional[bool] = None

# Response Schemas
class EventListResponse(BaseModel):
    id: int
    uuid: str
    title: str
    event_type: str
    scheduled_date: datetime
    duration_display: str
    status: str
    priority: str
    horse_id: Optional[int]
    horse_name: Optional[str]
    provider_name: Optional[str]
    location: Optional[str]
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    cost_status: str
    is_overdue: bool
    weather_dependent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class EventResponse(EventListResponse):
    # Include all fields from EventBase plus computed fields
    description: Optional[str]
    duration_minutes: Optional[int]
    end_time: Optional[datetime]
    provider_contact: Optional[str]
    cost_notes: Optional[str]
    recurring_pattern: str
    recurring_interval: Optional[int]
    recurring_end_date: Optional[date]
    notes: Optional[str]
    special_instructions: Optional[str]
    completion_notes: Optional[str]
    before_photo_path: Optional[str]
    after_photo_path: Optional[str]
    indoor_alternative: bool
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Event Type Configuration Schemas
class EventTypeConfigBase(BaseModel):
    event_type: EventType = Field(..., description="Event type")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    default_duration_minutes: Optional[int] = Field(60, ge=1, description="Default duration")
    typical_cost_range_min: Optional[float] = Field(None, ge=0, description="Typical minimum cost")
    typical_cost_range_max: Optional[float] = Field(None, ge=0, description="Typical maximum cost")
    recommended_frequency_days: Optional[int] = Field(None, ge=1, description="Recommended frequency in days")
    requires_horse: Optional[bool] = Field(True, description="Whether event requires a horse")
    color_hex: Optional[str] = Field(None, max_length=7, description="Color for calendar display")
    icon: Optional[str] = Field(None, max_length=50, description="Icon identifier")
    description: Optional[str] = Field(None, description="Event type description")

class EventTypeConfigCreate(EventTypeConfigBase):
    pass

class EventTypeConfigResponse(EventTypeConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Filtering and Query Schemas
class EventFilterParams(BaseModel):
    start_date: Optional[date] = Field(None, description="Filter events from this date")
    end_date: Optional[date] = Field(None, description="Filter events until this date")
    event_type: Optional[EventType] = Field(None, description="Filter by event type")
    status: Optional[EventStatus] = Field(None, description="Filter by status")
    horse_id: Optional[int] = Field(None, description="Filter by horse")
    provider_name: Optional[str] = Field(None, description="Filter by provider")
    priority: Optional[str] = Field(None, description="Filter by priority")
    weather_dependent: Optional[bool] = Field(None, description="Filter weather-dependent events")
    overdue_only: Optional[bool] = Field(False, description="Show only overdue events")

# Calendar View Schemas
class CalendarEventSummary(BaseModel):
    """Simplified event data for calendar display"""
    id: int
    title: str
    event_type: str
    scheduled_date: datetime
    duration_minutes: int
    status: str
    horse_name: Optional[str]
    color_hex: Optional[str] = "#3498db"  # Default blue
    is_overdue: bool

class CalendarResponse(BaseModel):
    """Calendar view response with events grouped by date"""
    events: List[CalendarEventSummary]
    date_range: dict  # {"start": "2024-01-01", "end": "2024-01-31"}
    total_events: int
    event_types_summary: dict  # {"veterinary": 5, "farrier": 3, etc.}

# Quick Event Creation Schemas (for common event types)
class QuickVetVisit(BaseModel):
    horse_id: int
    scheduled_date: datetime
    reason: Optional[str] = "Routine checkup"
    veterinarian_name: Optional[str] = None

class QuickFarrierVisit(BaseModel):
    horse_id: int
    scheduled_date: datetime
    service_type: Optional[str] = "Trim"  # Trim, Shoes, Reset
    farrier_name: Optional[str] = None

class QuickSupplyDelivery(BaseModel):
    scheduled_date: datetime
    supplier: str
    items: str
    estimated_cost: Optional[float] = None