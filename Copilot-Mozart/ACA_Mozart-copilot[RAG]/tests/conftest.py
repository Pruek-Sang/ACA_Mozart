"""
Pytest Configuration for ACA Mozart RAG Tests
=============================================
Central conftest.py with shared fixtures and configuration

Key conventions:
- test_client: TestClient with mocked RagService (no FAISS/LLM needed)
- supabase_client: Real Supabase client (skips if no creds)
- TESTING=1 env var prevents health check from hitting production Supabase
"""

import pytest
import os
import sys
import time

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ═══════════════════════════════════════════════════════════════════════════
# Global TESTING mode — prevents Supabase pings in health checks, etc.
# ═══════════════════════════════════════════════════════════════════════════
os.environ.setdefault("TESTING", "1")


# ═══════════════════════════════════════════════════════════════════════════
# Register custom markers so pytest doesn't warn about unknown markers
# ═══════════════════════════════════════════════════════════════════════════
def pytest_configure(config):
    config.addinivalue_line("markers", "live: marks tests that hit real external services (Supabase, LLM, MCP Core)")


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
    FastAPI TestClient with mocked RagService.
    
    Uses the lazy-init proxy in routes.py — injects a mock RagService
    so the app starts without FAISS, Google AI, or vector DB.
    Works identically in CI and locally.
    """
    from unittest.mock import MagicMock, AsyncMock
    from starlette.testclient import TestClient
    from app.models import StandardResponse, AnswerMetadata
    
    # Inject mock RagService into the lazy proxy (avoids FAISS/LLM init)
    import app.routes as routes_mod
    mock_rag = MagicMock()
    # process_ask is awaited in route handlers — must be AsyncMock
    # Return a valid StandardResponse so endpoint serialization doesn't fail
    mock_rag.process_ask = AsyncMock(return_value=StandardResponse(
        answer="mock response for testing",
        sources=[],
        confidence="Low",
        grounding_status="mocked",
        metadata=AnswerMetadata(llm_model="mock", retrieved_docs=[]),
    ))
    routes_mod._rag_service_instance = mock_rag
    
    with TestClient(routes_mod.app) as client:
        yield client
    
    # Cleanup: reset the lazy proxy
    routes_mod._rag_service_instance = None


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

