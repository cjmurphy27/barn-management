#!/usr/bin/env python3
"""
Simple script to check what columns exist in the horses table.
This will help us determine if we need to run migrations or if
the columns already exist.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from sqlalchemy import text, inspect
from app.database import db_manager

def check_horses_table_schema():
    """Check what columns exist in the horses table"""

    print("Checking horses table schema...")

    try:
        with db_manager.engine.connect() as conn:
            # Get table info using inspector
            inspector = inspect(db_manager.engine)

            # Check if horses table exists
            if 'horses' not in inspector.get_table_names():
                print("❌ horses table does not exist!")
                return False

            # Get column information
            columns = inspector.get_columns('horses')

            print(f"\n✅ horses table exists with {len(columns)} columns:")
            print("-" * 50)

            photo_columns = []
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  {col_name:<30} {col_type:<20} {nullable}")

                # Track photo-related columns
                if 'photo' in col_name.lower():
                    photo_columns.append(col_name)

            print("\n" + "=" * 50)
            print("PHOTO-RELATED COLUMNS:")
            if photo_columns:
                for col in photo_columns:
                    print(f"  ✅ {col}")
            else:
                print("  ❌ No photo-related columns found")

            # Check specifically for the columns our model expects
            expected_photo_columns = [
                'profile_photo_path',
                'profile_photo_data',
                'profile_photo_filename',
                'profile_photo_mime_type'
            ]

            print("\nEXPECTED PHOTO COLUMNS STATUS:")
            all_columns_exist = True
            existing_columns = [col['name'] for col in columns]

            for expected_col in expected_photo_columns:
                if expected_col in existing_columns:
                    print(f"  ✅ {expected_col} - EXISTS")
                else:
                    print(f"  ❌ {expected_col} - MISSING")
                    all_columns_exist = False

            if all_columns_exist:
                print("\n🎉 All expected photo columns exist! No migration needed.")
            else:
                print("\n⚠️  Some photo columns are missing. Migration may be needed.")

            return all_columns_exist

    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")
        return False

if __name__ == "__main__":
    # Test database connection first
    if not db_manager.test_connection():
        print("❌ Database connection failed!")
        sys.exit(1)

    # Check schema
    schema_ok = check_horses_table_schema()

    if schema_ok:
        print("\n✅ Database schema is ready!")
        sys.exit(0)
    else:
        print("\n❌ Database schema needs attention!")
        sys.exit(1)