#!/usr/bin/env python3
"""
Script to investigate horse photo storage state without making changes
"""
import os
import sys
sys.path.append('/Users/chris.murphy/barn-management')

from app.database import db_manager
from sqlalchemy import text
from app.config.storage import StorageConfig
from pathlib import Path

def main():
    print("=== Horse Photo Storage Investigation ===\n")

    # 1. Check storage configuration
    print("1. Storage Configuration:")
    storage_root = StorageConfig.get_storage_root()
    photos_dir = StorageConfig.get_horse_photos_dir()
    print(f"   Storage root: {storage_root}")
    print(f"   Photos directory: {photos_dir}")
    print(f"   Photos dir exists: {photos_dir.exists()}")
    print(f"   Railway volume env: {os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', 'Not set')}")

    # 2. List files in photos directory
    print(f"\n2. Files in photos directory ({photos_dir}):")
    if photos_dir.exists():
        try:
            files = list(photos_dir.glob("*"))
            if files:
                for file in files:
                    stat = file.stat()
                    print(f"   {file.name} ({stat.st_size} bytes)")
            else:
                print("   No files found")
        except Exception as e:
            print(f"   Error listing files: {e}")
    else:
        print("   Directory doesn't exist")

    # 3. Check database records
    print(f"\n3. Database records:")
    try:
        with db_manager.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, profile_photo_path
                FROM horses
                ORDER BY id
            """))

            horses = result.fetchall()
            print(f"   Found {len(horses)} horses in database:")

            for horse in horses:
                horse_id, name, photo_path = horse
                print(f"   Horse {horse_id} ({name}):")
                print(f"     Photo path: {photo_path}")

                if photo_path:
                    # Check if file exists
                    file_exists = Path(photo_path).exists() if photo_path else False
                    print(f"     File exists: {file_exists}")

                    if file_exists:
                        try:
                            stat = Path(photo_path).stat()
                            print(f"     File size: {stat.st_size} bytes")
                        except Exception as e:
                            print(f"     Error getting file stats: {e}")
                else:
                    print("     No photo path set")
                print()

    except Exception as e:
        print(f"   Error querying database: {e}")

    # 4. Environment check
    print("4. Environment Variables:")
    relevant_vars = [
        'RAILWAY_VOLUME_MOUNT_PATH',
        'DATABASE_URL',
        'ENVIRONMENT'
    ]
    for var in relevant_vars:
        value = os.environ.get(var, 'Not set')
        print(f"   {var}: {value}")

if __name__ == "__main__":
    main()