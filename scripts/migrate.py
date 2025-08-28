#!/usr/bin/env python3
"""
Database migration script for Barn Lady Horse Management System
Creates initial tables for horses, health records, and feeding records.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.horse import Base, Horse
from app.models.health import HealthRecord, FeedingRecord
from app.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """Create the barnlady database if it doesn't exist"""
    settings = get_settings()
    
    # Create connection to PostgreSQL server (without specifying database)
    server_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
    engine = create_engine(server_url)
    
    with engine.connect() as conn:
        # Check if database exists
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'barnlady'"))
        if not result.fetchone():
            # Create database
            conn.execute(text("COMMIT"))  # End any open transaction
            conn.execute(text("CREATE DATABASE barnlady"))
            logger.info("Created database 'barnlady'")
        else:
            logger.info("Database 'barnlady' already exists")
    
    engine.dispose()

def create_tables():
    """Create all tables defined in the models"""
    settings = get_settings()
    
    # Create engine for the barnlady database
    database_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    engine = create_engine(database_url)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully created all tables")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            logger.info(f"Created tables: {', '.join(tables)}")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise
    finally:
        engine.dispose()

def create_sample_data():
    """Create some sample horses for testing"""
    settings = get_settings()
    database_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    engine = create_engine(database_url)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db:
            # Check if we already have horses
            existing_horses = db.query(Horse).count()
            if existing_horses > 0:
                logger.info(f"Database already contains {existing_horses} horses. Skipping sample data creation.")
                return
            
            # Create sample horses
            sample_horses = [
                Horse(
                    name="Thunder Bay",
                    barn_name="Thunder",
                    breed="Thoroughbred",
                    color="Bay",
                    gender="Gelding",
                    age_years=8,
                    age_months=3,
                    height_hands=16.2,
                    weight_lbs=1200,
                    body_condition_score=6.0,
                    registration_number="TB123456789",
                    registration_organization="The Jockey Club",
                    owner_name="Sarah Johnson",
                    owner_contact="sarah.johnson@email.com | (555) 123-4567",
                    current_location="Meadowbrook Farm",
                    stall_number="B12",
                    pasture_group="Group A",
                    boarding_type="Full Care",
                    training_level="Advanced",
                    disciplines="Dressage, Show Jumping",
                    trainer_name="Amanda Wilson",
                    trainer_contact="amanda@wilsonequestrian.com",
                    current_health_status="Good",
                    veterinarian_name="Dr. Emily Parker",
                    veterinarian_contact="parker.vet@email.com | (555) 987-6543",
                    emergency_contact_name="John Johnson",
                    emergency_contact_phone="(555) 123-9999",
                    notes="Very gentle and easy to handle. Excellent with children.",
                    special_instructions="Requires daily turnout and prefers group feeding.",
                    is_active=True
                ),
                Horse(
                    name="Starlight Princess",
                    barn_name="Star",
                    breed="Quarter Horse",
                    color="Palomino",
                    gender="Mare",
                    age_years=12,
                    age_months=7,
                    height_hands=15.1,
                    weight_lbs=1100,
                    body_condition_score=7.0,
                    registration_number="QH987654321",
                    registration_organization="AQHA",
                    owner_name="Mike Rodriguez",
                    owner_contact="mike.rodriguez@email.com | (555) 234-5678",
                    current_location="Sunrise Stables",
                    stall_number="A5",
                    pasture_group="Group B",
                    boarding_type="Partial Care",
                    training_level="Intermediate",
                    disciplines="Western Pleasure, Trail",
                    trainer_name="Carlos Martinez",
                    current_health_status="Excellent",
                    veterinarian_name="Dr. Robert Chen",
                    veterinarian_contact="rchen.dvm@email.com | (555) 876-5432",
                    emergency_contact_name="Maria Rodriguez",
                    emergency_contact_phone="(555) 234-8888",
                    allergies="Sensitive to dust",
                    medications="Daily joint supplement",
                    notes="Very calm and reliable. Great for beginners.",
                    is_active=True
                ),
                Horse(
                    name="Midnight Express",
                    barn_name="Midnight",
                    breed="Arabian",
                    color="Black",
                    gender="Stallion",
                    age_years=6,
                    age_months=10,
                    height_hands=15.3,
                    weight_lbs=1050,
                    body_condition_score=6.5,
                    registration_number="AR555444333",
                    registration_organization="AHA",
                    owner_name="Jessica Thompson",
                    owner_contact="jthompson@email.com | (555) 345-6789",
                    current_location="Desert Wind Ranch",
                    stall_number="C8",
                    pasture_group="Individual",
                    boarding_type="Full Care",
                    training_level="Advanced",
                    disciplines="Endurance, Dressage",
                    trainer_name="Dr. Hassan Al-Rashid",
                    current_health_status="Good",
                    veterinarian_name="Dr. Lisa Anderson",
                    veterinarian_contact="landerson.vet@email.com | (555) 765-4321",
                    emergency_contact_name="Tom Thompson",
                    emergency_contact_phone="(555) 345-7777",
                    special_needs="Requires individual turnout due to stallion behavior",
                    notes="High energy, requires experienced handlers. Excellent bloodlines.",
                    special_instructions="Handle with caution - stallion protocols required.",
                    is_active=True
                ),
                Horse(
                    name="Gentle Ben",
                    barn_name="Ben",
                    breed="Clydesdale",
                    color="Chestnut",
                    gender="Gelding",
                    age_years=15,
                    age_months=2,
                    height_hands=17.0,
                    weight_lbs=1800,
                    body_condition_score=5.5,
                    registration_number="CD777888999",
                    registration_organization="CCGB",
                    owner_name="Green Valley Farm",
                    owner_contact="info@greenvalleyfarm.com | (555) 456-7890",
                    current_location="Green Valley Farm",
                    stall_number="Draft1",
                    pasture_group="Draft Horses",
                    boarding_type="Full Care",
                    training_level="Beginner",
                    disciplines="Driving, Therapy Work",
                    current_health_status="Fair",
                    veterinarian_name="Dr. Michael O'Brien",
                    veterinarian_contact="mobrien.vet@email.com | (555) 654-3210",
                    emergency_contact_name="Farm Manager",
                    emergency_contact_phone="(555) 456-6666",
                    medications="Arthritis supplement, fly spray as needed",
                    special_needs="Senior horse care, softer footing required",
                    notes="Retired therapy horse. Very gentle and patient with people.",
                    special_instructions="Feed senior feed twice daily. Monitor for arthritis pain.",
                    is_retired=True,
                    is_active=True
                ),
                Horse(
                    name="Lightning Bolt",
                    barn_name="Bolt",
                    breed="Paint Horse",
                    color="Pinto",
                    gender="Mare",
                    age_years=9,
                    age_months=5,
                    height_hands=15.2,
                    weight_lbs=1150,
                    body_condition_score=6.0,
                    registration_number="PH111222333",
                    registration_organization="APHA",
                    owner_name="Lightning Ridge Stables",
                    owner_contact="office@lightningridge.com | (555) 567-8901",
                    current_location="Lightning Ridge Stables",
                    stall_number="L3",
                    pasture_group="Group C",
                    boarding_type="Self Care",
                    training_level="Intermediate",
                    disciplines="Barrel Racing, Gaming",
                    trainer_name="Jenny Carter",
                    current_health_status="Good",
                    veterinarian_name="Dr. Steve Williams",
                    veterinarian_contact="swilliams.vet@email.com | (555) 543-2109",
                    emergency_contact_name="Ridge Manager",
                    emergency_contact_phone="(555) 567-5555",
                    notes="Fast and agile. Competitive barrel racer with great times.",
                    special_instructions="Warm up thoroughly before speed work.",
                    is_for_sale=True,
                    is_active=True
                )
            ]
            
            # Add horses to database
            for horse in sample_horses:
                db.add(horse)
            
            db.commit()
            logger.info(f"Successfully created {len(sample_horses)} sample horses")
            
            # Display created horses
            for horse in sample_horses:
                logger.info(f"Created horse: {horse.name} ({horse.barn_name}) - {horse.breed}")
                
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        raise
    finally:
        engine.dispose()

def check_database_connection():
    """Test database connection"""
    settings = get_settings()
    database_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"Database connection successful. PostgreSQL version: {version}")
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("Starting Barn Lady database migration...")
    
    try:
        # Step 1: Create database if it doesn't exist
        logger.info("Step 1: Creating database if needed...")
        create_database_if_not_exists()
        
        # Step 2: Check connection
        logger.info("Step 2: Testing database connection...")
        if not check_database_connection():
            logger.error("Cannot connect to database. Migration failed.")
            return False
        
        # Step 3: Create tables
        logger.info("Step 3: Creating database tables...")
        create_tables()
        
        # Step 4: Create sample data
        logger.info("Step 4: Creating sample data...")
        create_sample_data()
        
        logger.info("✅ Database migration completed successfully!")
        logger.info("You can now start adding your horses to Barn Lady!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
