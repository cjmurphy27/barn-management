import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application Settings
    APP_NAME: str = Field(default="Barn Lady", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    SECRET_KEY: str = Field(default="your-secret-key-change-this", description="Secret key for app")
    
    # Database Settings
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_USER: str = Field(default="postgres", description="Database user")
    DB_PASSWORD: str = Field(default="postgres", description="Database password")
    DB_NAME: str = Field(default="barnlady", description="Database name")
    
    # Redis Settings (for caching and sessions)
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    
    # API Settings
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version 1 prefix")
    CORS_ORIGINS: list = Field(default=["http://localhost:8501", "http://localhost:3000"], description="CORS allowed origins")
    
    # Authentication Settings (PropelAuth integration)
    PROPELAUTH_URL: Optional[str] = Field(default=None, description="PropelAuth URL")
    PROPELAUTH_API_KEY: Optional[str] = Field(default=None, description="PropelAuth API key")
    PROPELAUTH_VERIFIER_KEY: Optional[str] = Field(default=None, description="PropelAuth verifier key")
    PROPELAUTH_AUTH_URL: Optional[str] = Field(default=None, description="PropelAuth auth URL")
    
    # AI Integration Settings
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic Claude API key")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    @property
    def database_url(self) -> str:
        """Get the complete database URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # This allows extra fields without errors
    }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
