import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # PropelAuth Configuration
    PROPELAUTH_URL: str = os.getenv("PROPELAUTH_URL", "")
    PROPELAUTH_API_KEY: str = os.getenv("PROPELAUTH_API_KEY", "")
    PROPELAUTH_VERIFIER_KEY: str = os.getenv("PROPELAUTH_VERIFIER_KEY", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/barnlady")
    
    # Claude AI Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Application Configuration
    APP_NAME: str = "Barn Lady"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8501"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Validation helper
def validate_required_settings():
    """Validate that all required settings are present"""
    missing = []
    
    if not settings.PROPELAUTH_URL:
        missing.append("PROPELAUTH_URL")
    if not settings.PROPELAUTH_API_KEY:
        missing.append("PROPELAUTH_API_KEY")
    if not settings.ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True
