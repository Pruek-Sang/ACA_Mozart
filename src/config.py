"""Configuration module for MCP Core v2."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    supabase_url: str = ""
    supabase_key: str = ""
    langsmith_api_key: str = ""

    class Config:
        """Pydantic config for settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
