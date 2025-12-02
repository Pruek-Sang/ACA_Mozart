"""Configuration module for MCP Core v2."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables
load_env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=load_env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Data Source Configuration (File-based, no external DB required)
    catalog_csv_path: str = ""  # Auto-detected if empty
    
    # Application Settings
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # NEC Standards
    nec_version: str = "2023"
    voltage_drop_limit: float = 0.03
    temperature_rating: int = 75
    
    # Calculation Settings
    safety_factor: float = 1.25
    default_power_factor: float = 0.85
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
