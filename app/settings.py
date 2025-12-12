"""Application settings module using pydantic-settings.

This module provides centralized configuration management with validation,
defaults, and type safety for environment variables.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All settings have type validation and optional defaults.
    Pydantic-settings automatically loads values from environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',  # Ignore extra environment variables
    )
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, description="Server port")
    
    # Database settings
    database_url: str = Field(
        ...,  # Required field
        description="PostgreSQL database connection URL"
    )
    database_scale_0: bool = Field(
        default=False,
        description="Set true if database scales to 0 when idle (disables LISTEN/NOTIFY, enables pool_pre_ping)"
    )
    
    # JWT authentication
    jwt_secret: str = Field(
        ...,  # Required field
        description="Secret key for JWT token signing and verification"
    )
    
    # LLM/AI settings
    llm_sp_ak: str = Field(
        default="",
        description="LLM service provider API key"
    )
    llm_sp_base_url: str = Field(
        default="",
        description="LLM service provider base URL"
    )
    
    # Logging settings (Better Stack / Logtail)
    logtail_source_token: Optional[str] = Field(
        default=None,
        description="Better Stack (Logtail) source token for remote logging"
    )
    logtail_host: Optional[str] = Field(
        default=None,
        description="Better Stack (Logtail) host URL"
    )
    
    @field_validator('database_url')
    @classmethod
    def convert_postgres_scheme(cls, v: str) -> str:
        """Convert postgres:// to postgresql:// for SQLAlchemy 2.0+ compatibility.
        
        Heroku provides DATABASE_URL with 'postgres://' scheme, but SQLAlchemy 2.0+
        requires 'postgresql://' scheme. This validator handles the conversion.
        
        Args:
            v: The database URL value
            
        Returns:
            Database URL with postgresql:// scheme
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v


# Global settings instance
# This should be imported and used throughout the application
settings = Settings()
