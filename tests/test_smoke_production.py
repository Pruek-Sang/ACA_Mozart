"""
Smoke Test - Test LIVE production endpoints after deploy
Catches: Deploy succeeded but app broken

This test runs AFTER deploy and verifies:
1. Frontend loads without React errors
2. RAG health shows Supabase connected (not "error")
3. RAG /api/v1/ask endpoint responds
4. Gateway is reachable
"""
import os
import pytest
import requests

# Production URLs - can be overridden by env vars
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "https://frontend-203658178245.asia-southeast1.run.app"
)
RAG_URL = os.getenv(
    "RAG_URL", 
    "https://mozart-rag-203658178245.asia-southeast1.run.app"
)
GATEWAY_URL = os.getenv(
    "GATEWAY_URL",
    "https://gateway-203658178245.asia-southeast1.run.app"
)

TIMEOUT = 30  # seconds


class TestFrontend:
    """Frontend smoke tests."""
    
    def test_frontend_loads(self):
        """Frontend returns 200 and contains HTML."""
        resp = requests.get(FRONTEND_URL, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Frontend returned {resp.status_code}"
        assert "<!DOCTYPE html>" in resp.text or "<html" in resp.text


class TestRAG:
    """RAG Service smoke tests."""
    
    def test_rag_health_alive(self):
        """RAG health endpoint returns alive status."""
        resp = requests.get(RAG_URL, timeout=TIMEOUT)
        assert resp.status_code == 200, f"RAG returned {resp.status_code}"
        
        data = resp.json()
        assert data.get("status") == "alive", f"RAG status: {data.get('status')}"
    
    def test_rag_supabase_connected(self):
        """RAG health shows Supabase connected (NOT error)."""
        resp = requests.get(RAG_URL, timeout=TIMEOUT)
        data = resp.json()
        
        supabase_status = data.get("supabase", "unknown")
        assert supabase_status == "connected", \
            f"Supabase status: {supabase_status}. Expected 'connected'!"
    
    def test_rag_api_responds(self):
        """RAG /api/v1/ask endpoint responds to ping."""
        resp = requests.post(
            f"{RAG_URL}/api/v1/ask",
            json={"query": "ping", "language": "th"},
            timeout=60  # Longer timeout for cold start
        )
        assert resp.status_code == 200, f"RAG API returned {resp.status_code}"
        
        data = resp.json()
        # Should have answer OR not have error key
        assert "answer" in data or "error" not in data, \
            f"RAG API error: {data.get('error')}"


class TestGateway:
    """Gateway smoke tests."""
    
    def test_gateway_alive(self):
        """Gateway health endpoint responds."""
        resp = requests.get(GATEWAY_URL, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Gateway returned {resp.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
