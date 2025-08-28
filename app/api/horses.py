from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models.horse import Horse
from app.schemas.horse import HorseCreate, HorseUpdate, HorseResponse
from app.core.auth import get_current_user, get_current_user_optional, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["horses"])

@router.get("/horses/", response_model=List[HorseResponse])
async def get_horses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search horses by name, breed, or location"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get all horses for the current organization"""
    try:
        query = db.query(Horse)
        
        # If user is authenticated, filter by organization
        if current_user and current_user.current_org_id:
            query = query.filter(Horse.organization_id == current_user.current_org_id)
        
        # Apply search if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Horse.name.ilike(search_term)) |
                (Horse.breed.ilike(search_term)) |
                (Horse.current_location.ilike(search_term))
            )
        
        # Apply pagination
        horses = query.offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(horses)} horses")
        return horses
        
    except Exception as e:
        logger.error(f"Error retrieving horses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve horses"
        )

@router.get("/horses/{horse_id}", response_model=HorseResponse)
async def get_horse(
    horse_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get a specific horse by ID"""
    try:
        query = db.query(Horse).filter(Horse.id == horse_id)
        
        # If user is authenticated, filter by organization
        if current_user and current_user.current_org_id:
            query = query.filter(Horse.organization_id == current_user.current_org_id)
        
        horse = query.first()
        
        if not horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Horse not found"
            )
        
        return horse
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving horse {horse_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve horse"
        )

@router.post("/horses/", response_model=HorseResponse, status_code=status.HTTP_201_CREATED)
async def create_horse(
    horse_data: HorseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new horse"""
    try:
        if not current_user.current_org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No organization selected"
            )
        
        # Create horse with organization ID
        horse_dict = horse_data.dict()
        horse_dict['organization_id'] = current_user.current_org_id
        
        horse = Horse(**horse_dict)
        db.add(horse)
        db.commit()
        db.refresh(horse)
        
        logger.info(f"Created horse {horse.name} for organization {current_user.current_org_id}")
        return horse
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating horse: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create horse"
        )

@router.put("/horses/{horse_id}", response_model=HorseResponse)
async def update_horse(
    horse_id: int,
    horse_data: HorseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a horse"""
    try:
        query = db.query(Horse).filter(Horse.id == horse_id)
        
        # Filter by organization
        if current_user.current_org_id:
            query = query.filter(Horse.organization_id == current_user.current_org_id)
        
        horse = query.first()
        
        if not horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Horse not found"
            )
        
        # Update horse
        update_data = horse_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(horse, field, value)
        
        db.commit()
        db.refresh(horse)
        
        logger.info(f"Updated horse {horse.name}")
        return horse
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating horse {horse_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update horse"
        )

@router.delete("/horses/{horse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_horse(
    horse_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a horse"""
    try:
        query = db.query(Horse).filter(Horse.id == horse_id)
        
        # Filter by organization
        if current_user.current_org_id:
            query = query.filter(Horse.organization_id == current_user.current_org_id)
        
        horse = query.first()
        
        if not horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Horse not found"
            )
        
        db.delete(horse)
        db.commit()
        
        logger.info(f"Deleted horse {horse.name}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting horse {horse_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete horse"
        )
