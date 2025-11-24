"""Supabase client with LangSmith tracing integration.

Provides connection to Supabase for accessing catalog data and
storing design session state.
"""

import os
from functools import lru_cache
from typing import Optional, Any, Dict, List
import logging

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper around Supabase client with tracing support."""

    def __init__(self, url: str, key: str, enable_tracing: bool = False):
        """Initialize Supabase client.
        
        Args:
            url: Supabase project URL
            key: Supabase anon/service key
            enable_tracing: Whether to enable LangSmith tracing
        """
        self._client: Client = create_client(url, key)
        self._enable_tracing = enable_tracing
        self._trace_callback: Optional[callable] = None
        
        if enable_tracing:
            self._setup_tracing()

    def _setup_tracing(self) -> None:
        """Setup LangSmith tracing if configured."""
        try:
            langsmith_api_key = os.getenv("LANGCHAIN_API_KEY")
            if langsmith_api_key:
                from langsmith import Client as LangSmithClient
                self._langsmith_client = LangSmithClient()
                logger.info("LangSmith tracing enabled for Supabase operations")
            else:
                logger.warning("LANGCHAIN_API_KEY not set, tracing disabled")
        except ImportError:
            logger.warning("langsmith not installed, tracing disabled")
        except Exception as e:
            logger.warning(f"Failed to setup LangSmith tracing: {e}")

    def _trace_operation(self, operation: str, table: str, params: Dict[str, Any]) -> None:
        """Log operation for tracing purposes."""
        if self._enable_tracing:
            logger.debug(f"Supabase operation: {operation} on {table} with {params}")

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        schema: str = "public"
    ) -> List[Dict[str, Any]]:
        """Execute a SELECT query on a table.
        
        Args:
            table: Table name
            columns: Columns to select (default "*")
            filters: Dictionary of filter conditions
            limit: Maximum rows to return
            schema: Database schema (default "public")
            
        Returns:
            List of matching records
        """
        self._trace_operation("SELECT", table, {"columns": columns, "filters": filters})
        
        try:
            query = self._client.schema(schema).table(table).select(columns)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Supabase SELECT error on {table}: {e}")
            raise

    def insert(
        self,
        table: str,
        data: Dict[str, Any],
        schema: str = "public"
    ) -> Dict[str, Any]:
        """Insert a record into a table.
        
        Args:
            table: Table name
            data: Record data
            schema: Database schema
            
        Returns:
            Inserted record
        """
        self._trace_operation("INSERT", table, {"data": data})
        
        try:
            response = self._client.schema(schema).table(table).insert(data).execute()
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Supabase INSERT error on {table}: {e}")
            raise

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        schema: str = "public"
    ) -> List[Dict[str, Any]]:
        """Update records in a table.
        
        Args:
            table: Table name
            data: Updated field values
            filters: Filter conditions to identify records
            schema: Database schema
            
        Returns:
            Updated records
        """
        self._trace_operation("UPDATE", table, {"data": data, "filters": filters})
        
        try:
            query = self._client.schema(schema).table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Supabase UPDATE error on {table}: {e}")
            raise

    def rpc(
        self,
        function_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call a Supabase RPC function.
        
        Args:
            function_name: Name of the function
            params: Function parameters
            
        Returns:
            Function result
        """
        self._trace_operation("RPC", function_name, {"params": params})
        
        try:
            response = self._client.rpc(function_name, params or {}).execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Supabase RPC error on {function_name}: {e}")
            raise

    @property
    def client(self) -> Client:
        """Access underlying Supabase client."""
        return self._client


@lru_cache()
def get_supabase_client() -> Optional[SupabaseClient]:
    """Get cached Supabase client instance.
    
    Returns None if Supabase is not configured.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        logger.warning("Supabase not configured (SUPABASE_URL or SUPABASE_KEY missing)")
        return None
    
    enable_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    
    return SupabaseClient(url, key, enable_tracing)
