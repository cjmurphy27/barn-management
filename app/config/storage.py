import os
from pathlib import Path

class StorageConfig:
    """Configuration for file storage paths"""

    @staticmethod
    def get_storage_root() -> Path:
        """
        Get the root storage directory.

        In Railway with volumes:
        - Volume will be mounted to /app/storage
        - RAILWAY_VOLUME_MOUNT_PATH environment variable will be set

        For local development:
        - Uses ./storage directory
        """
        # Check if running on Railway with volume
        railway_volume_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if railway_volume_path:
            return Path(railway_volume_path)

        # Fallback to local storage directory
        app_root = Path(__file__).parent.parent.parent
        return app_root / "storage"

    @staticmethod
    def get_horse_photos_dir() -> Path:
        """Get the horse photos storage directory"""
        storage_root = StorageConfig.get_storage_root()
        horse_photos_dir = storage_root / "horse_photos"

        # Ensure directory exists
        try:
            horse_photos_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # If we can't create the directory, try to use a writable location
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "barn_management" / "horse_photos"
            temp_dir.mkdir(parents=True, exist_ok=True)
            return temp_dir

        return horse_photos_dir

    @staticmethod
    def get_documents_dir() -> Path:
        """Get the documents storage directory"""
        storage_root = StorageConfig.get_storage_root()
        documents_dir = storage_root / "documents"

        # Ensure directory exists
        documents_dir.mkdir(parents=True, exist_ok=True)

        return documents_dir

    @staticmethod
    def ensure_storage_structure():
        """Ensure all required storage directories exist"""
        try:
            StorageConfig.get_horse_photos_dir()
            StorageConfig.get_documents_dir()

            # Create any other subdirectories as needed
            storage_root = StorageConfig.get_storage_root()

            # Additional directories for future use
            (storage_root / "temp").mkdir(parents=True, exist_ok=True)
            (storage_root / "backups").mkdir(parents=True, exist_ok=True)

            return True
        except Exception as e:
            # Log the error but don't fail startup
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not initialize storage structure: {str(e)}")
            logger.warning("Storage will be created on-demand when needed")
            return False