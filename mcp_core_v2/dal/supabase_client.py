"""
MCP Core v2 Supabase Client
Handles connection to Supabase for the amadeus.catalog schema.
"""

import logging
from typing import Optional
from supabase import create_client, Client

from config import get_supabase_url, get_supabase_key

logger = logging.getLogger(__name__)


class SupabaseClientWrapper:
    """Wrapper for Supabase client with connection management."""
    
    _instance: Optional[Client] = None
    _url: str = ""
    _key: str = ""
    
    @classmethod
    def get_client(cls) -> Optional[Client]:
        """
        Get or create Supabase client instance.
        Returns None if credentials are not configured.
        """
        if cls._instance is not None:
            return cls._instance
        
        url = get_supabase_url()
        key = get_supabase_key()
        
        if not url or not key:
            return None
        
        try:
            cls._instance = create_client(url, key)
            cls._url = url
            cls._key = key
            return cls._instance
        except Exception as e:
            logger.error("Failed to create Supabase client: %s", e)
            return None
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if client is connected."""
        return cls._instance is not None
    
    @classmethod
    def reset(cls) -> None:
        """Reset the client instance."""
        cls._instance = None
        cls._url = ""
        cls._key = ""


def get_supabase() -> Optional[Client]:
    """
    Convenience function to get Supabase client.
    Returns None if not configured (allows offline/demo mode).
    """
    return SupabaseClientWrapper.get_client()
