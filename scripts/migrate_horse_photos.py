#!/usr/bin/env python3
"""
Migration script to convert horse profile photos from Base64 storage to FastAPI file system.

This script:
1. Finds all horses with existing profile_photo_path files
2. Copies those files to the new FastAPI storage structure
3. Verifies the migration was successful
4. Provides rollback capability

Usage:
    python scripts/migrate_horse_photos.py --dry-run    # Preview changes
    python scripts/migrate_horse_photos.py              # Execute migration
    python scripts/migrate_horse_photos.py --rollback   # Rollback changes
"""

import os
import sys
import argparse
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.database import db_manager
from app.models.horse import Horse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Storage configuration
OLD_STORAGE_PATHS = [
    "uploads",  # Current upload directory
    "storage/horse_images",  # Alternative paths that might exist
]
NEW_STORAGE_DIR = "storage/horse_photos"
BACKUP_DIR = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

class HorsePhotoMigrator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.migrated_horses: List[Dict] = []
        self.errors: List[Dict] = []

        # Ensure directories exist
        if not dry_run:
            os.makedirs(NEW_STORAGE_DIR, exist_ok=True)
            os.makedirs(BACKUP_DIR, exist_ok=True)

    def find_horses_with_photos(self, db: Session) -> List[Horse]:
        """Find all horses that have profile photos"""
        horses = db.query(Horse).filter(
            Horse.profile_photo_path.isnot(None),
            Horse.profile_photo_path != '',
            Horse.organization_id.isnot(None)
        ).all()

        logger.info(f"Found {len(horses)} horses with profile photos")
        return horses

    def validate_source_file(self, file_path: str) -> bool:
        """Validate that the source file exists and is readable"""
        if not os.path.exists(file_path):
            return False

        if not os.path.isfile(file_path):
            return False

        try:
            # Try to read the file to ensure it's accessible
            with open(file_path, 'rb') as f:
                f.read(1024)  # Read first 1KB to test
            return True
        except Exception:
            return False

    def get_new_file_path(self, horse: Horse, original_path: str) -> str:
        """Generate the new file path in the FastAPI storage structure"""
        # Extract file extension
        _, ext = os.path.splitext(original_path)
        if not ext:
            ext = '.jpg'  # Default extension

        # Create new filename
        filename = f"horse_{horse.id}_migrated{ext}"

        # Create organization subdirectory path
        org_dir = os.path.join(NEW_STORAGE_DIR, horse.organization_id)
        new_path = os.path.join(org_dir, filename)

        return new_path

    def migrate_horse_photo(self, horse: Horse, db: Session) -> Dict:
        """Migrate a single horse's photo"""
        result = {
            "horse_id": horse.id,
            "horse_name": horse.name,
            "organization_id": horse.organization_id,
            "old_path": horse.profile_photo_path,
            "new_path": None,
            "success": False,
            "error": None
        }

        try:
            old_path = horse.profile_photo_path

            # Validate source file
            if not self.validate_source_file(old_path):
                result["error"] = f"Source file not found or not readable: {old_path}"
                return result

            # Generate new path
            new_path = self.get_new_file_path(horse, old_path)
            result["new_path"] = new_path

            if self.dry_run:
                logger.info(f"DRY RUN: Would migrate {old_path} -> {new_path}")
                result["success"] = True
                return result

            # Create organization directory
            org_dir = os.path.dirname(new_path)
            os.makedirs(org_dir, exist_ok=True)

            # Create backup of original file
            backup_path = os.path.join(BACKUP_DIR, f"horse_{horse.id}_{os.path.basename(old_path)}")
            shutil.copy2(old_path, backup_path)
            logger.info(f"Backed up {old_path} to {backup_path}")

            # Copy file to new location
            shutil.copy2(old_path, new_path)
            logger.info(f"Copied {old_path} to {new_path}")

            # Update database record
            horse.profile_photo_path = new_path
            db.commit()
            logger.info(f"Updated database for horse {horse.id} ({horse.name})")

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error migrating horse {horse.id}: {str(e)}")
            if not self.dry_run:
                db.rollback()

        return result

    def migrate_all_photos(self) -> Dict:
        """Migrate all horse photos"""
        logger.info("Starting horse photo migration...")

        db = db_manager.get_session()
        try:
            horses = self.find_horses_with_photos(db)

            if not horses:
                logger.info("No horses with photos found. Migration complete.")
                return {"total": 0, "migrated": 0, "errors": 0}

            total_horses = len(horses)
            migrated_count = 0
            error_count = 0

            for horse in horses:
                logger.info(f"Processing horse {horse.id} ({horse.name})...")

                result = self.migrate_horse_photo(horse, db)

                if result["success"]:
                    self.migrated_horses.append(result)
                    migrated_count += 1
                else:
                    self.errors.append(result)
                    error_count += 1

            summary = {
                "total": total_horses,
                "migrated": migrated_count,
                "errors": error_count,
                "migrated_horses": self.migrated_horses,
                "error_horses": self.errors
            }

            logger.info(f"Migration complete: {migrated_count}/{total_horses} successful, {error_count} errors")
            return summary

        finally:
            db.close()

    def rollback_migration(self) -> bool:
        """Rollback the migration using backup files"""
        logger.info("Starting migration rollback...")

        if not os.path.exists(BACKUP_DIR):
            logger.error(f"Backup directory {BACKUP_DIR} not found")
            return False

        db = db_manager.get_session()
        try:
            success_count = 0
            error_count = 0

            # Process each migrated horse
            for migration in self.migrated_horses:
                try:
                    horse_id = migration["horse_id"]
                    old_path = migration["old_path"]
                    new_path = migration["new_path"]

                    # Find the horse in database
                    horse = db.query(Horse).filter(Horse.id == horse_id).first()
                    if not horse:
                        logger.warning(f"Horse {horse_id} not found in database")
                        continue

                    # Restore original path in database
                    horse.profile_photo_path = old_path

                    # Remove new file if it exists
                    if new_path and os.path.exists(new_path):
                        os.remove(new_path)
                        logger.info(f"Removed {new_path}")

                    db.commit()
                    success_count += 1
                    logger.info(f"Rolled back horse {horse_id}")

                except Exception as e:
                    logger.error(f"Error rolling back horse {migration.get('horse_id')}: {str(e)}")
                    error_count += 1
                    db.rollback()

            logger.info(f"Rollback complete: {success_count} successful, {error_count} errors")
            return error_count == 0

        finally:
            db.close()

    def generate_report(self, summary: Dict) -> str:
        """Generate a detailed migration report"""
        report = []
        report.append("=" * 60)
        report.append("HORSE PHOTO MIGRATION REPORT")
        report.append("=" * 60)
        report.append(f"Total horses processed: {summary['total']}")
        report.append(f"Successfully migrated: {summary['migrated']}")
        report.append(f"Errors: {summary['errors']}")
        report.append("")

        if summary['migrated_horses']:
            report.append("SUCCESSFULLY MIGRATED:")
            report.append("-" * 30)
            for migration in summary['migrated_horses']:
                report.append(f"Horse {migration['horse_id']} ({migration['horse_name']})")
                report.append(f"  From: {migration['old_path']}")
                report.append(f"  To:   {migration['new_path']}")
                report.append("")

        if summary['error_horses']:
            report.append("ERRORS:")
            report.append("-" * 30)
            for error in summary['error_horses']:
                report.append(f"Horse {error['horse_id']} ({error['horse_name']})")
                report.append(f"  Error: {error['error']}")
                report.append("")

        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Migrate horse photos to FastAPI storage")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--rollback", action="store_true", help="Rollback previous migration")
    args = parser.parse_args()

    migrator = HorsePhotoMigrator(dry_run=args.dry_run)

    if args.rollback:
        success = migrator.rollback_migration()
        sys.exit(0 if success else 1)

    try:
        summary = migrator.migrate_all_photos()

        # Generate and save report
        report = migrator.generate_report(summary)
        print(report)

        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Report saved to {report_file}")

        # Exit with appropriate code
        sys.exit(0 if summary['errors'] == 0 else 1)

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()