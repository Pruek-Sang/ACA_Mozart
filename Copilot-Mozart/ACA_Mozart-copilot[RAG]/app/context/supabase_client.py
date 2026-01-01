"""
Supabase Client - Backend Connection to Mozart Database

Philosophy:
- Single connection instance (singleton pattern)
- Environment-based configuration
- Graceful fallback if connection fails

Usage:
    from app.context import supabase_client
    
    # Query sessions
    result = supabase_client.table("mozart.sessions").select("*").execute()
"""

import os
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger("Aura.Supabase")

# Lazy import to avoid startup failures
_supabase_instance = None


def get_supabase_client():
    """
    Get Supabase client instance (lazy initialization).
    
    Returns:
        Supabase client or None if configuration missing
    """
    global _supabase_instance
    
    if _supabase_instance is not None:
        return _supabase_instance
    
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning(
                "⚠️ Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. "
                "Stateful features will be disabled."
            )
            return None
        
        _supabase_instance = create_client(url, key)
        logger.info("✅ Supabase client initialized successfully")
        return _supabase_instance
        
    except ImportError:
        logger.warning("⚠️ supabase-py not installed. Run: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase: {e}")
        return None


# Convenience alias
supabase_client = get_supabase_client


class SupabaseHealthCheck:
    """
    Health check utility for Supabase connection.
    """
    
    @staticmethod
    def is_available() -> bool:
        """Check if Supabase is available and connected."""
        client = get_supabase_client()
        if not client:
            return False
        
        try:
            # Simple query to check connection
            client.schema("mozart").table("sessions").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase health check failed: {e}")
            return False
    
    @staticmethod
    def get_status() -> dict:
        """Get detailed status of Supabase connection."""
        client = get_supabase_client()
        
        if not client:
            return {
                "available": False,
                "reason": "Client not initialized",
                "config": {
                    "url_set": bool(os.getenv("SUPABASE_URL")),
                    "key_set": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")),
                }
            }
        
        try:
            result = client.schema("mozart").table("sessions").select("id").limit(1).execute()
            return {
                "available": True,
                "tables_accessible": True,
            }
        except Exception as e:
            return {
                "available": False,
                "reason": str(e),
            }
