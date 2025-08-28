from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional
import uuid
import enum

from app.database import Base

class EventType(str, enum.Enum):
    VETERINARY = "veterinary"
    FARRIER = "farrier"
    DENTAL = "dental"
    SUPPLY_DELIVERY = "supply_delivery"
    TRAINING = "training"
    BREEDING = "breeding"
    HEALTH_TREATMENT = "health_treatment"
    OTHER = "other"

class EventStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class RecurringPattern(str, enum.Enum):
    NONE = "none"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    CUSTOM = "custom"

class Event(Base):
    __tablename__ = "events"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic Event Information
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    
    # Scheduling
    scheduled_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)
    end_time = Column(DateTime, nullable=True)  # Calculated or manual
    
    # Location & Provider
    location = Column(String(200), nullable=True)
    provider_name = Column(String(100), nullable=True)
    provider_contact = Column(String(200), nullable=True)
    
    # Status & Management
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED, index=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Cost Information
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    cost_notes = Column(Text, nullable=True)
    
    # Recurring Events
    recurring_pattern = Column(Enum(RecurringPattern), default=RecurringPattern.NONE)
    recurring_interval = Column(Integer, default=1)  # Every N weeks/months/etc
    recurring_end_date = Column(Date, nullable=True)
    parent_event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    
    # Horse Association (nullable for facility-wide events)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=True, index=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    
    # Photos/Documentation
    before_photo_path = Column(String(500), nullable=True)
    after_photo_path = Column(String(500), nullable=True)
    documents_path = Column(Text, nullable=True)  # JSON array of document paths
    
    # Reminders & Notifications
    reminder_sent = Column(Boolean, default=False)
    reminder_date = Column(DateTime, nullable=True)
    notification_contacts = Column(Text, nullable=True)  # JSON array of contacts
    
    # Weather Considerations
    weather_dependent = Column(Boolean, default=False)
    indoor_alternative = Column(Boolean, default=False)
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships will be configured after both models are loaded
    # horse = relationship("Horse", back_populates="events")
    child_events = relationship("Event", backref="parent_event", remote_side=[id])
    
    def __repr__(self):
        return f"<Event(title='{self.title}', date='{self.scheduled_date}', type='{self.event_type}')>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if event is overdue"""
        if self.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
            return False
        return datetime.now() > self.scheduled_date
    
    @property
    def duration_display(self) -> str:
        """Return human-readable duration"""
        if not self.duration_minutes:
            return "Duration not set"
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours and minutes:
            return f"{hours}h {minutes}m"
        elif hours:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    @property
    def cost_status(self) -> str:
        """Return cost status indicator"""
        if self.actual_cost is not None:
            return "actual"
        elif self.estimated_cost is not None:
            return "estimated"
        else:
            return "unknown"
    
    def to_dict(self) -> dict:
        """Convert event object to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type.value if self.event_type else None,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "duration_minutes": self.duration_minutes,
            "duration_display": self.duration_display,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "provider_name": self.provider_name,
            "provider_contact": self.provider_contact,
            "status": self.status.value if self.status else None,
            "priority": self.priority,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "cost_status": self.cost_status,
            "cost_notes": self.cost_notes,
            "recurring_pattern": self.recurring_pattern.value if self.recurring_pattern else None,
            "recurring_interval": self.recurring_interval,
            "recurring_end_date": self.recurring_end_date.isoformat() if self.recurring_end_date else None,
            "horse_id": self.horse_id,
            "horse_name": None,  # Will be populated by API layer
            "notes": self.notes,
            "special_instructions": self.special_instructions,
            "completion_notes": self.completion_notes,
            "before_photo_path": self.before_photo_path,
            "after_photo_path": self.after_photo_path,
            "is_overdue": self.is_overdue,
            "weather_dependent": self.weather_dependent,
            "indoor_alternative": self.indoor_alternative,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class EventType_Config(Base):
    """Configuration for different event types with defaults"""
    __tablename__ = "event_type_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(EventType), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    default_duration_minutes = Column(Integer, default=60)
    typical_cost_range_min = Column(Float, nullable=True)
    typical_cost_range_max = Column(Float, nullable=True)
    recommended_frequency_days = Column(Integer, nullable=True)
    requires_horse = Column(Boolean, default=True)
    color_hex = Column(String(7), nullable=True)  # For calendar display
    icon = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<EventTypeConfig(type='{self.event_type}', name='{self.display_name}')>"