#!/usr/bin/env python3
"""
Database migration script that runs on Railway startup to add missing fields
"""

import sys
import logging
import os
from sqlalchemy import create_engine, text, inspect

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment"""
    # Railway provides DATABASE_URL directly
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("Using Railway DATABASE_URL")
        return database_url
    
    # Fallback for local development
    from app.core.config import get_settings
    settings = get_settings()
    return settings.database_url

def migrate_horse_fields():
    """Add missing fields to horses table if they don't exist"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if horses table exists
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                
                if 'horses' not in tables:
                    logger.info("Horses table doesn't exist yet - will be created by SQLAlchemy")
                    trans.commit()
                    return True
                
                # Get existing columns
                columns = inspector.get_columns('horses')
                existing_column_names = [col['name'] for col in columns]
                
                # List of new columns to add
                new_columns = [
                    ("farrier_name", "VARCHAR(100)"),
                    ("feeding_schedule", "TEXT"),
                    ("exercise_schedule", "TEXT"),
                    ("last_vet_visit", "DATE"),
                    ("last_dental", "DATE"),
                    ("last_farrier", "DATE")
                ]
                
                # Add each new column if it doesn't exist
                columns_added = 0
                for column_name, column_type in new_columns:
                    if column_name not in existing_column_names:
                        logger.info(f"Adding column: {column_name}")
                        conn.execute(text(f"""
                            ALTER TABLE horses 
                            ADD COLUMN {column_name} {column_type}
                        """))
                        columns_added += 1
                    else:
                        logger.info(f"Column {column_name} already exists")
                
                # Commit the transaction
                trans.commit()
                
                if columns_added > 0:
                    logger.info(f"Successfully added {columns_added} new horse fields")
                else:
                    logger.info("All horse fields already exist")
                
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error during migration: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

def migrate_horse_documents():
    """Create horse document tables if they don't exist"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if horse_documents table exists
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'horse_documents' in tables:
                logger.info("Horse documents tables already exist")
                return True
            
            logger.info("Horse documents tables don't exist yet - will be created by SQLAlchemy")
            return True
                
    except Exception as e:
        logger.error(f"Database connection error during document table check: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Railway database migration...")
    
    # Run horse fields migration
    horse_fields_success = migrate_horse_fields()
    
    # Check document tables
    document_tables_success = migrate_horse_documents()
    
    if horse_fields_success and document_tables_success:
        logger.info("All migrations completed successfully!")
        sys.exit(0)
    else:
        logger.error("Some migrations failed!")
        sys.exit(1)