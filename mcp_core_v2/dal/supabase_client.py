"""Supabase client for MCP Core v2."""

from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper for Supabase client with common operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            logger.warning("Supabase credentials not configured")
            self._client: Optional[Client] = None
        else:
            self._client: Client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        self.schema = settings.db_schema
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        if self._client is None:
            raise ValueError("Supabase client not initialized. Check your configuration.")
        return self._client
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a record into a table."""
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error inserting into {table}: {e}")
            raise
    
    def insert_many(self, table: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert multiple records into a table."""
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error inserting multiple records into {table}: {e}")
            raise
    
    def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Select records from a table."""
        try:
            query = self.client.table(table).select(columns)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error selecting from {table}: {e}")
            raise
    
    def update(
        self, 
        table: str, 
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Update records in a table."""
        try:
            query = self.client.table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error updating {table}: {e}")
            raise
    
    def delete(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Delete records from a table."""
        try:
            query = self.client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error deleting from {table}: {e}")
            raise
    
    def upsert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert a record (insert or update)."""
        try:
            response = self.client.table(table).upsert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error upserting into {table}: {e}")
            raise


# Global instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get the global Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
