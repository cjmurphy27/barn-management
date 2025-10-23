#!/usr/bin/env python3
"""
Database migration script to add new photo fields to horses table.
This script adds the missing columns needed for the volume storage implementation.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from sqlalchemy import text
from app.database import db_manager

def migrate_horse_photos():
    """Add new photo columns to horses table"""

    # SQL to add new columns
    migrations = [
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS profile_photo_data TEXT;",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS profile_photo_filename VARCHAR(200);",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS profile_photo_mime_type VARCHAR(50);"
    ]

    print("Starting horse photos migration...")

    try:
        with db_manager.engine.connect() as conn:
            # Start transaction
            trans = conn.begin()

            for migration_sql in migrations:
                print(f"Executing: {migration_sql}")
                conn.execute(text(migration_sql))

            # Commit transaction
            trans.commit()
            print("✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    # Test database connection first
    if not db_manager.test_connection():
        print("❌ Database connection failed!")
        sys.exit(1)

    # Run migration
    if migrate_horse_photos():
        print("🎉 Horse photos migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)