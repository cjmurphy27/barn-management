#!/usr/bin/env python3
"""
Migration script to add care notes and last_deworming columns to the horses table.

Usage:
    python scripts/add_care_notes_migration.py
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MIGRATIONS = [
    "ALTER TABLE horses ADD COLUMN IF NOT EXISTS last_deworming DATE;",
    "ALTER TABLE horses ADD COLUMN IF NOT EXISTS vet_visit_notes TEXT;",
    "ALTER TABLE horses ADD COLUMN IF NOT EXISTS dental_notes TEXT;",
    "ALTER TABLE horses ADD COLUMN IF NOT EXISTS farrier_notes TEXT;",
    "ALTER TABLE horses ADD COLUMN IF NOT EXISTS deworming_notes TEXT;",
]

def run_migration():
    settings = get_settings()
    db_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    engine = create_engine(db_url)

    with engine.connect() as conn:
        for sql in MIGRATIONS:
            logger.info(f"Running: {sql}")
            conn.execute(text(sql))
        conn.commit()

    logger.info("Migration complete.")

if __name__ == "__main__":
    run_migration()
