"""
MCP Core v2 Configuration
Uses pydantic-settings for environment variable management.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_key: str = ""
    
    # LangSmith Configuration (Optional)
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "mcp-core-v2"
    langsmith_tracing_v2: bool = False
    
    # Application Settings
    debug: bool = False
    default_voltage: float = 220.0  # Thailand standard voltage
    default_frequency: float = 50.0  # Hz


# Global settings instance
settings = Settings()


def get_supabase_url() -> str:
    """Get Supabase URL from settings or environment."""
    return settings.supabase_url or os.getenv("SUPABASE_URL", "")


def get_supabase_key() -> str:
    """Get Supabase key from settings or environment."""
    return settings.supabase_key or os.getenv("SUPABASE_KEY", "")
