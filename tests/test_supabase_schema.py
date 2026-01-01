"""
Supabase Schema Test - Test REAL Supabase connection
Catches: Error #310 (wrong table name/schema syntax)

This test verifies:
1. mozart schema exists
2. sessions table is accessible with correct syntax
3. projects table is accessible with correct syntax
"""
import os
import pytest


def test_supabase_env_configured():
    """Verify Supabase environment variables are set."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    assert url is not None, "SUPABASE_URL not set"
    assert key is not None, "SUPABASE_SERVICE_ROLE_KEY not set"
    assert url.startswith("https://"), f"Invalid SUPABASE_URL: {url}"


def test_mozart_sessions_table():
    """Test mozart.sessions table is accessible with correct syntax."""
    from supabase import create_client
    
    client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    # CRITICAL: Use schema().table() NOT table("schema.table")
    # This is the exact syntax that caused Error #310
    result = client.schema("mozart").table("sessions").select("id").limit(1).execute()
    
    assert result is not None, "Query returned None"
    assert hasattr(result, 'data'), "Result has no 'data' attribute"


def test_mozart_projects_table():
    """Test mozart.projects table is accessible with correct syntax."""
    from supabase import create_client
    
    client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    result = client.schema("mozart").table("projects").select("id").limit(1).execute()
    
    assert result is not None, "Query returned None"
    assert hasattr(result, 'data'), "Result has no 'data' attribute"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
