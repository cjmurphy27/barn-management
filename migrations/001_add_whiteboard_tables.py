#!/usr/bin/env python3
"""
Migration: Add Whiteboard Tables
Date: 2025-09-18
Description: Add WhiteboardPost, WhiteboardComment, and WhiteboardAttachment tables for barn communication

This migration can be run standalone or will be automatically applied via create_all()
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app.core.config import get_settings
from app.models.whiteboard import WhiteboardPost, WhiteboardComment, WhiteboardAttachment

def check_table_exists(engine, table_name):
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def run_migration():
    """Run the whiteboard tables migration"""
    try:
        # Get database URL
        settings = get_settings()
        db_url = settings.database_url
        engine = create_engine(db_url)

        print(f"Running whiteboard migration on database: {db_url[:50]}...")

        # Check which tables already exist
        existing_tables = []
        new_tables = []

        tables_to_check = [
            ("whiteboard_posts", WhiteboardPost),
            ("whiteboard_comments", WhiteboardComment),
            ("whiteboard_attachments", WhiteboardAttachment)
        ]

        for table_name, model_class in tables_to_check:
            if check_table_exists(engine, table_name):
                existing_tables.append(table_name)
                print(f"  ✓ Table {table_name} already exists")
            else:
                new_tables.append((table_name, model_class))
                print(f"  + Table {table_name} will be created")

        if not new_tables:
            print("✅ All whiteboard tables already exist. No migration needed.")
            return True

        # Create only the new tables
        print(f"\nCreating {len(new_tables)} new tables...")

        for table_name, model_class in new_tables:
            print(f"  Creating {table_name}...")
            model_class.__table__.create(engine)
            print(f"  ✅ Created {table_name}")

        # Verify tables were created
        print("\nVerifying table creation...")
        all_success = True
        for table_name, _ in new_tables:
            if check_table_exists(engine, table_name):
                print(f"  ✅ Verified {table_name}")
            else:
                print(f"  ❌ Failed to create {table_name}")
                all_success = False

        if all_success:
            print("\n🎉 Whiteboard migration completed successfully!")
            return True
        else:
            print("\n❌ Migration completed with errors")
            return False

    except SQLAlchemyError as e:
        print(f"❌ Database error during migration: {e}")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def rollback_migration():
    """Rollback the whiteboard tables migration (DROP TABLES)"""
    try:
        settings = get_settings()
        db_url = settings.database_url
        engine = create_engine(db_url)

        print(f"Rolling back whiteboard migration on database: {db_url[:50]}...")
        print("⚠️  WARNING: This will DELETE all whiteboard data!")

        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Rollback cancelled.")
            return False

        tables_to_drop = [
            "whiteboard_attachments",  # Drop in reverse order due to foreign keys
            "whiteboard_comments",
            "whiteboard_posts"
        ]

        with engine.connect() as conn:
            for table_name in tables_to_drop:
                if check_table_exists(engine, table_name):
                    print(f"  Dropping {table_name}...")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    print(f"  ✅ Dropped {table_name}")
                else:
                    print(f"  ⏭️  Table {table_name} doesn't exist, skipping")

            conn.commit()

        print("\n✅ Whiteboard migration rollback completed!")
        return True

    except SQLAlchemyError as e:
        print(f"❌ Database error during rollback: {e}")
        return False
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Whiteboard tables migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    parser.add_argument("--check", action="store_true", help="Check migration status")

    args = parser.parse_args()

    if args.rollback:
        success = rollback_migration()
    elif args.check:
        # Just check status without making changes
        try:
            settings = get_settings()
            db_url = settings.database_url
            engine = create_engine(db_url)

            tables = ["whiteboard_posts", "whiteboard_comments", "whiteboard_attachments"]
            print("Whiteboard migration status:")

            for table in tables:
                exists = check_table_exists(engine, table)
                status = "✅ EXISTS" if exists else "❌ MISSING"
                print(f"  {table}: {status}")

        except Exception as e:
            print(f"❌ Error checking migration status: {e}")
            success = False

        success = True
    else:
        success = run_migration()

    sys.exit(0 if success else 1)