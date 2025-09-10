from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional
from datetime import datetime, date, timedelta
import logging

from app.database import get_db
from app.models.horse import Horse
from app.models.event import Event, EventType_Config, EventType, EventStatus, RecurringPattern
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventListResponse, 
    EventFilterParams, CalendarResponse, CalendarEventSummary,
    QuickVetVisit, QuickFarrierVisit, QuickSupplyDelivery,
    EventTypeConfigCreate, EventTypeConfigResponse
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])

# Event CRUD Operations

@router.post("/events", status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    organization_id: Optional[str] = Query(None, description="Organization/barn ID"),
    db: Session = Depends(get_db)
):
    """Create a new event/appointment"""
    try:
        # Validate horse exists if horse_id provided
        if event.horse_id:
            horse = db.query(Horse).filter(Horse.id == event.horse_id).first()
            if not horse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Horse with ID {event.horse_id} not found"
                )
        
        # Calculate end_time if not provided
        end_time = None
        if event.duration_minutes:
            end_time = event.scheduled_date + timedelta(minutes=event.duration_minutes)
        
        # Create new event with organization context
        event_dict = event.dict()
        if organization_id:
            event_dict['organization_id'] = organization_id
        
        db_event = Event(
            **event_dict,
            end_time=end_time
        )
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Created event: {db_event.title} for {db_event.scheduled_date}")
        
        # Manually populate horse_name for response
        response_dict = db_event.to_dict()
        if db_event.horse_id:
            horse = db.query(Horse).filter(Horse.id == db_event.horse_id).first()
            response_dict["horse_name"] = horse.name if horse else None
        
        return response_dict
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )

@router.get("/events")
async def get_events(
    db: Session = Depends(get_db),
    organization_id: Optional[str] = Query(None, description="Filter by organization/barn"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    status: Optional[EventStatus] = Query(None, description="Filter by status"),
    horse_id: Optional[int] = Query(None, description="Filter by horse"),
    provider_name: Optional[str] = Query(None, description="Filter by provider"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    overdue_only: Optional[bool] = Query(False, description="Show only overdue events"),
    limit: Optional[int] = Query(100, le=1000, description="Limit results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    """Get events with optional filtering"""
    try:
        query = db.query(Event)
        
        # Apply filters
        if organization_id:
            query = query.filter(Event.organization_id == organization_id)
        if start_date:
            query = query.filter(Event.scheduled_date >= start_date)
        if end_date:
            # Add one day to include events on the end_date
            query = query.filter(Event.scheduled_date <= datetime.combine(end_date, datetime.max.time()))
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if status:
            query = query.filter(Event.status == status)
        if horse_id:
            query = query.filter(Event.horse_id == horse_id)
        if provider_name:
            query = query.filter(Event.provider_name.ilike(f"%{provider_name}%"))
        if priority:
            query = query.filter(Event.priority == priority)
        
        # Special filter for overdue events
        if overdue_only:
            query = query.filter(
                and_(
                    Event.scheduled_date < datetime.now(),
                    Event.status.notin_([EventStatus.COMPLETED, EventStatus.CANCELLED])
                )
            )
        
        # Order by scheduled date (soonest first)
        query = query.order_by(asc(Event.scheduled_date))
        
        # Apply pagination
        events = query.offset(offset).limit(limit).all()
        
        # Manually populate horse_name for each event
        result = []
        for event in events:
            event_dict = event.to_dict()
            if event.horse_id:
                horse = db.query(Horse).filter(Horse.id == event.horse_id).first()
                event_dict["horse_name"] = horse.name if horse else None
            result.append(event_dict)
        
        logger.info(f"Retrieved {len(events)} events with filters applied")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events"
        )

@router.get("/events/{event_id}")
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )
    
    # Manually populate horse_name for response
    event_dict = event.to_dict()
    if event.horse_id:
        horse = db.query(Horse).filter(Horse.id == event.horse_id).first()
        event_dict["horse_name"] = horse.name if horse else None
    
    return event_dict

@router.put("/events/{event_id}")
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing event"""
    try:
        # Get existing event
        db_event = db.query(Event).filter(Event.id == event_id).first()
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
        
        # Validate horse exists if horse_id being updated
        if event_update.horse_id is not None:
            if event_update.horse_id:  # If not None and not 0
                horse = db.query(Horse).filter(Horse.id == event_update.horse_id).first()
                if not horse:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Horse with ID {event_update.horse_id} not found"
                    )
        
        # Update fields
        update_data = event_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_event, field, value)
        
        # Recalculate end_time if scheduled_date or duration changed
        if 'scheduled_date' in update_data or 'duration_minutes' in update_data:
            if db_event.duration_minutes:
                db_event.end_time = db_event.scheduled_date + timedelta(minutes=db_event.duration_minutes)
        
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Updated event: {db_event.title}")
        
        # Manually populate horse_name for response
        event_dict = db_event.to_dict()
        if db_event.horse_id:
            horse = db.query(Horse).filter(Horse.id == db_event.horse_id).first()
            event_dict["horse_name"] = horse.name if horse else None
        
        return event_dict
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event"
        )

@router.delete("/events/{event_id}")
async def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event"""
    try:
        db_event = db.query(Event).filter(Event.id == event_id).first()
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
        
        db.delete(db_event)
        db.commit()
        
        logger.info(f"Deleted event: {db_event.title}")
        return {"message": f"Event '{db_event.title}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event"
        )

# Calendar View Endpoints

@router.get("/view/month", response_model=CalendarResponse)
async def get_monthly_calendar(
    year: int = Query(..., description="Year for calendar view"),
    month: int = Query(..., ge=1, le=12, description="Month for calendar view"),
    organization_id: Optional[str] = Query(None, description="Filter by organization/barn"),
    db: Session = Depends(get_db)
):
    """Get calendar view for a specific month"""
    try:
        # Calculate month boundaries
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Get events for the month
        query = db.query(Event).filter(
            and_(
                Event.scheduled_date >= start_date,
                Event.scheduled_date <= datetime.combine(end_date.date(), datetime.max.time())
            )
        )
        
        # Add organization filter
        if organization_id:
            query = query.filter(Event.organization_id == organization_id)
        
        events = query.order_by(asc(Event.scheduled_date)).all()
        
        # Get event type configs for colors
        type_configs = db.query(EventType_Config).all()
        color_map = {config.event_type: config.color_hex for config in type_configs if config.color_hex}
        
        # Format events for calendar
        calendar_events = []
        event_type_counts = {}
        
        for event in events:
            # Get horse name manually since relationship is disabled
            horse_name = None
            if event.horse_id:
                horse = db.query(Horse).filter(Horse.id == event.horse_id).first()
                horse_name = horse.name if horse else None
                
            calendar_events.append(CalendarEventSummary(
                id=event.id,
                title=event.title,
                event_type=event.event_type.value,
                scheduled_date=event.scheduled_date,
                duration_minutes=event.duration_minutes or 60,
                status=event.status.value,
                horse_name=horse_name,
                color_hex=color_map.get(event.event_type, "#3498db"),
                is_overdue=event.is_overdue
            ))
            
            # Count event types
            event_type_str = event.event_type.value
            event_type_counts[event_type_str] = event_type_counts.get(event_type_str, 0) + 1
        
        return CalendarResponse(
            events=calendar_events,
            date_range={
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat()
            },
            total_events=len(calendar_events),
            event_types_summary=event_type_counts
        )
        
    except Exception as e:
        logger.error(f"Error retrieving monthly calendar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar view"
        )

@router.get("/view/week", response_model=CalendarResponse)
async def get_weekly_calendar(
    start_date: date = Query(..., description="Start date for week view"),
    organization_id: Optional[str] = Query(None, description="Filter by organization/barn"),
    db: Session = Depends(get_db)
):
    """Get calendar view for a specific week"""
    try:
        end_date = start_date + timedelta(days=6)
        
        query = db.query(Event).filter(
            and_(
                Event.scheduled_date >= start_date,
                Event.scheduled_date <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        # Add organization filter
        if organization_id:
            query = query.filter(Event.organization_id == organization_id)
            
        events = query.order_by(asc(Event.scheduled_date)).all()
        
        # Format similar to monthly view
        type_configs = db.query(EventType_Config).all()
        color_map = {config.event_type: config.color_hex for config in type_configs if config.color_hex}
        
        calendar_events = []
        event_type_counts = {}
        
        for event in events:
            # Get horse name manually since relationship is disabled
            horse_name = None
            if event.horse_id:
                horse = db.query(Horse).filter(Horse.id == event.horse_id).first()
                horse_name = horse.name if horse else None
                
            calendar_events.append(CalendarEventSummary(
                id=event.id,
                title=event.title,
                event_type=event.event_type.value,
                scheduled_date=event.scheduled_date,
                duration_minutes=event.duration_minutes or 60,
                status=event.status.value,
                horse_name=horse_name,
                color_hex=color_map.get(event.event_type, "#3498db"),
                is_overdue=event.is_overdue
            ))
            
            event_type_str = event.event_type.value
            event_type_counts[event_type_str] = event_type_counts.get(event_type_str, 0) + 1
        
        return CalendarResponse(
            events=calendar_events,
            date_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            total_events=len(calendar_events),
            event_types_summary=event_type_counts
        )
        
    except Exception as e:
        logger.error(f"Error retrieving weekly calendar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weekly calendar view"
        )

# Quick Event Creation

@router.post("/events/quick/vet-visit", response_model=EventResponse)
async def create_quick_vet_visit(
    visit: QuickVetVisit,
    organization_id: Optional[str] = Query(None, description="Organization/barn ID"),
    db: Session = Depends(get_db)
):
    """Quickly create a veterinary visit"""
    event_create = EventCreate(
        title=f"Vet Visit - {visit.reason}" if visit.reason else "Veterinary Appointment",
        description=visit.reason,
        event_type=EventType.VETERINARY,
        scheduled_date=visit.scheduled_date,
        duration_minutes=60,
        provider_name=visit.veterinarian_name,
        horse_id=visit.horse_id,
        status=EventStatus.SCHEDULED,
        priority="medium"
    )
    
    return await create_event(event_create, organization_id, db)

@router.post("/events/quick/farrier-visit", response_model=EventResponse)
async def create_quick_farrier_visit(
    visit: QuickFarrierVisit,
    organization_id: Optional[str] = Query(None, description="Organization/barn ID"),
    db: Session = Depends(get_db)
):
    """Quickly create a farrier visit"""
    event_create = EventCreate(
        title=f"Farrier - {visit.service_type}",
        description=f"Farrier service: {visit.service_type}",
        event_type=EventType.FARRIER,
        scheduled_date=visit.scheduled_date,
        duration_minutes=45,
        provider_name=visit.farrier_name,
        horse_id=visit.horse_id,
        status=EventStatus.SCHEDULED,
        priority="medium"
    )
    
    return await create_event(event_create, organization_id, db)

@router.post("/events/quick/supply-delivery", response_model=EventResponse)
async def create_quick_supply_delivery(
    delivery: QuickSupplyDelivery,
    organization_id: Optional[str] = Query(None, description="Organization/barn ID"),
    db: Session = Depends(get_db)
):
    """Quickly create a supply delivery event"""
    event_create = EventCreate(
        title=f"Delivery - {delivery.supplier}",
        description=f"Items: {delivery.items}",
        event_type=EventType.SUPPLY_DELIVERY,
        scheduled_date=delivery.scheduled_date,
        duration_minutes=30,
        provider_name=delivery.supplier,
        estimated_cost=delivery.estimated_cost,
        status=EventStatus.SCHEDULED,
        priority="low"
    )
    
    return await create_event(event_create, organization_id, db)

# Dashboard & Summary Endpoints

@router.get("/upcoming")
async def get_upcoming_events(
    days_ahead: int = Query(7, ge=1, le=30, description="Days to look ahead"),
    limit: int = Query(10, le=50, description="Maximum events to return"),
    organization_id: Optional[str] = Query(None, description="Filter by organization/barn"),
    db: Session = Depends(get_db)
):
    """Get upcoming events for dashboard"""
    try:
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        query = db.query(Event).filter(
            and_(
                Event.scheduled_date >= datetime.now(),
                Event.scheduled_date <= end_date,
                Event.status.notin_([EventStatus.COMPLETED, EventStatus.CANCELLED])
            )
        )
        
        if organization_id:
            query = query.filter(Event.organization_id == organization_id)
            
        events = query.order_by(asc(Event.scheduled_date)).limit(limit).all()
        
        return {
            "upcoming_events": [event.to_dict() for event in events],
            "count": len(events),
            "date_range": {
                "start": datetime.now().date().isoformat(),
                "end": end_date.date().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving upcoming events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upcoming events"
        )

@router.get("/overdue")
async def get_overdue_events(
    organization_id: Optional[str] = Query(None, description="Filter by organization/barn"),
    db: Session = Depends(get_db)
):
    """Get overdue events that need attention"""
    try:
        query = db.query(Event).filter(
            and_(
                Event.scheduled_date < datetime.now(),
                Event.status.notin_([EventStatus.COMPLETED, EventStatus.CANCELLED])
            )
        )
        
        if organization_id:
            query = query.filter(Event.organization_id == organization_id)
            
        events = query.order_by(desc(Event.scheduled_date)).all()
        
        return {
            "overdue_events": [event.to_dict() for event in events],
            "count": len(events)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving overdue events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overdue events"
        )