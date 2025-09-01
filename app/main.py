from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.config import get_settings
from app.database import get_db, Base, db_manager
from app.models.horse import Horse
from app.models.event import Event, EventType_Config
from app.models.supply import Supply, Supplier, Transaction, TransactionItem, StockMovement
from app.schemas.horse import HorseCreate, HorseResponse
from app.api.ai import router as ai_router
from app.api.calendar import router as calendar_router
from app.api.supplies import router as supplies_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Barn Lady API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(ai_router)
app.include_router(calendar_router)
app.include_router(supplies_router)

# Import and include horse documents router
from app.api.horse_documents import router as horse_documents_router
app.include_router(horse_documents_router, prefix="/api/v1")

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Create tables
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database tables created successfully")
        
        # Test connection
        if db_manager.test_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "version": "2.0.0"}

@app.get("/api/v1/horses/")
async def get_horses(
    search: Optional[str] = None,
    active_only: bool = True,
    sort_by: str = "name",
    sort_order: str = "asc",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get horses from database with search, filter, and sorting"""
    from sqlalchemy import or_, asc, desc
    
    query = db.query(Horse)
    
    # Filter by active status
    if active_only:
        query = query.filter(Horse.is_active == True)
    
    # Search functionality
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Horse.name.ilike(search_term),
                Horse.barn_name.ilike(search_term),
                Horse.breed.ilike(search_term),
                Horse.color.ilike(search_term),
                Horse.owner_name.ilike(search_term),
                Horse.current_location.ilike(search_term)
            )
        )
    
    # Sorting
    sort_column = getattr(Horse, sort_by, Horse.name)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Limit results
    horses = query.limit(limit).all()
    
    return [horse.to_dict() for horse in horses]

@app.get("/api/v1/horses/{horse_id}")
async def get_horse(horse_id: int, db: Session = Depends(get_db)):
    """Get a specific horse by ID"""
    horse = db.query(Horse).filter(Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    return horse.to_dict()

@app.post("/api/v1/horses/")
async def create_horse(horse_data: HorseCreate, db: Session = Depends(get_db)):
    """Create a new horse"""
    db_horse = Horse(**horse_data.dict())
    db.add(db_horse)
    db.commit()
    db.refresh(db_horse)
    logger.info(f"Created new horse: {db_horse.name}")
    return db_horse.to_dict()

@app.put("/api/v1/horses/{horse_id}")
async def update_horse(horse_id: int, horse_data: HorseCreate, db: Session = Depends(get_db)):
    """Update an existing horse"""
    db_horse = db.query(Horse).filter(Horse.id == horse_id).first()
    if not db_horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    
    # Update horse fields
    for field, value in horse_data.dict(exclude_unset=True).items():
        setattr(db_horse, field, value)
    
    db.commit()
    db.refresh(db_horse)
    logger.info(f"Updated horse: {db_horse.name}")
    return db_horse.to_dict()

@app.delete("/api/v1/horses/{horse_id}")
async def delete_horse(horse_id: int, db: Session = Depends(get_db)):
    """Delete a horse (soft delete by setting is_active=False)"""
    db_horse = db.query(Horse).filter(Horse.id == horse_id).first()
    if not db_horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    
    # Soft delete - just mark as inactive
    db_horse.is_active = False
    db.commit()
    logger.info(f"Deleted horse: {db_horse.name}")
    return {"message": f"Horse {db_horse.name} deleted successfully"}

