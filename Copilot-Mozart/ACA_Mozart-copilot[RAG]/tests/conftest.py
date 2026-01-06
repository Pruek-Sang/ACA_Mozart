"""
Pytest Configuration for ACA Mozart RAG Tests
=============================================
Central conftest.py with shared fixtures and configuration
"""

import pytest
import os
import sys

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--api-url",
        action="store",
        default="http://localhost:8080/api/v1/ask",
        help="URL of the /api/v1/ask endpoint"
    )
    parser.addoption(
        "--use-mock-l2",
        action="store_true",
        default=False,
        help="Use mock evaluation for Layer 2"
    )
    parser.addoption(
        "--project-id",
        action="store",
        default=os.environ.get("PROJECT_ID"),
        help="GCP Project ID for Gemini"
    )


@pytest.fixture(scope="session")
def api_url(request):
    """Get API URL from command line or default"""
    return request.config.getoption("--api-url")


@pytest.fixture(scope="session")
def use_mock_l2(request):
    """Get mock L2 flag from command line"""
    return request.config.getoption("--use-mock-l2")


@pytest.fixture(scope="session")
def project_id(request):
    """Get GCP project ID from command line or env"""
    return request.config.getoption("--project-id")


# =============================================================================
# 🆕 Phase 1: Real Integration Test Fixtures (No Mocks!)
# =============================================================================

@pytest.fixture(scope="module")
def test_client():
    """
    FastAPI TestClient for real API testing.
    Uses the actual app from routes.py.
    """
    from fastapi.testclient import TestClient
    from app.routes import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def supabase_client():
    """
    Real Supabase client for integration tests.
    Uses test tables (mozart.test_sessions) to avoid production data.
    
    Requires environment variables:
    - SUPABASE_URL
    - SUPABASE_SERVICE_ROLE_KEY
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        pytest.skip("Supabase credentials not configured")
    
    from supabase import create_client
    client = create_client(url, key)
    yield client


@pytest.fixture
def test_session_id():
    """Generate unique test session ID for each test."""
    import uuid
    return f"test_{uuid.uuid4()}"


@pytest.fixture
def cleanup_session(supabase_client, test_session_id):
    """
    Cleanup fixture - deletes test session after test completes.
    Use as: def test_something(cleanup_session): ...
    """
    yield test_session_id
    
    # Cleanup after test
    try:
        supabase_client.schema("mozart").table("sessions").delete().eq(
            "session_id", test_session_id
        ).execute()
    except Exception:
        pass  # Ignore cleanup errors

