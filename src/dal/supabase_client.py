"""Singleton Supabase client for MCP Core v2."""

from typing import Optional

from supabase import Client, create_client

from src.config import settings


class SupabaseClientSingleton:
    """Singleton pattern for Supabase client."""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create the Supabase client instance."""
        if cls._instance is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in environment"
                )
            cls._instance = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the client instance (useful for testing)."""
        cls._instance = None


def get_supabase_client() -> Client:
    """Convenience function to get Supabase client."""
    return SupabaseClientSingleton.get_client()
