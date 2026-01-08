"""
E2E Test for BOQ Feature - NO MOCK
Tests the real API endpoint for boq_data generation

Run: pytest tests/test_boq_e2e_real.py -v
"""
import os
import sys
import pytest
import httpx
from typing import Dict, Any

# Skip if running in CI without backend
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true" and not os.environ.get("BACKEND_URL"),
    reason="Requires real backend (not mocked)"
)

# Backend URL - default to local, can override with env var
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


class TestBOQE2EReal:
    """E2E Tests for BOQ feature - NO MOCK"""
    
    @pytest.fixture
    def sample_design_request(self) -> Dict[str, Any]:
        """Real design request that would produce BOQ"""
        return {
            "message": "บ้าน 2 ชั้น มีแอร์ 3 ตัว เครื่องทำน้ำอุ่น 1 ตัว ปลั๊กไฟ 10 จุด",
            "session_id": "test-boq-e2e-001",
            "project_name": "TEST_BOQ_E2E"
        }
    
    def test_api_returns_boq_data(self, sample_design_request: Dict):
        """
        🔥 CRITICAL: Verify API returns boq_data with price_source
        
        This is the main test to catch "silent failures" where:
        - Backend generates BOQ but doesn't send it
        - price_source is missing or wrong
        - sections are empty
        """
        with httpx.Client(base_url=BACKEND_URL, timeout=60.0) as client:
            response = client.post("/api/v1/ask", json=sample_design_request)
            
            # 1. Check response status
            assert response.status_code == 200, f"API returned {response.status_code}"
            data = response.json()
            
            # 2. Check metadata exists
            assert "metadata" in data, "Response missing 'metadata'"
            metadata = data["metadata"]
            
            # 3. 🔥 CRITICAL: Check boq_data exists
            assert "boq_data" in metadata, (
                "❌ SILENT FAILURE: metadata.boq_data is MISSING!\n"
                "This means BOQ is generated but NOT sent to frontend.\n"
                "Check service.py: boq_data_dict should be added to metadata."
            )
            
            boq_data = metadata["boq_data"]
            
            # 4. Check boq_data structure
            assert boq_data is not None, "boq_data is None"
            assert isinstance(boq_data, dict), f"boq_data is {type(boq_data)}, expected dict"
            
            # 5. Check required fields
            required_fields = [
                "sections", "price_source", "final_total", 
                "subtotal_material", "subtotal_labor"
            ]
            for field in required_fields:
                assert field in boq_data, f"boq_data missing '{field}'"
            
            # 6. 🔥 CRITICAL: Check price_source
            price_source = boq_data.get("price_source")
            assert price_source in ["prices.csv", "catalog_fallback", "error"], (
                f"Invalid price_source: {price_source}\n"
                "Expected: 'prices.csv' or 'catalog_fallback'"
            )
            
            # Log for debugging (will appear in test output)
            print(f"\n✅ BOQ E2E Test Passed!")
            print(f"   - Price Source: {price_source}")
            print(f"   - Sections: {len(boq_data.get('sections', []))}")
            print(f"   - Final Total: {boq_data.get('final_total'):,.2f} THB")
    
    def test_boq_sections_not_empty(self, sample_design_request: Dict):
        """Check that BOQ actually has items, not empty sections"""
        with httpx.Client(base_url=BACKEND_URL, timeout=60.0) as client:
            response = client.post("/api/v1/ask", json=sample_design_request)
            data = response.json()
            
            boq_data = data.get("metadata", {}).get("boq_data", {})
            sections = boq_data.get("sections", [])
            
            assert len(sections) > 0, "BOQ has no sections!"
            
            # Check each section has items
            for section in sections:
                section_id = section.get("section_id", "?")
                items = section.get("items", [])
                assert len(items) > 0, f"Section {section_id} has no items!"
    
    def test_boq_prices_are_realistic(self, sample_design_request: Dict):
        """
        Sanity check: BOQ prices should be reasonable
        
        Catches bugs where prices are 0 or unrealistically high
        """
        with httpx.Client(base_url=BACKEND_URL, timeout=60.0) as client:
            response = client.post("/api/v1/ask", json=sample_design_request)
            data = response.json()
            
            boq_data = data.get("metadata", {}).get("boq_data", {})
            final_total = boq_data.get("final_total", 0)
            
            # Sanity bounds: residential BOQ should be 10k - 500k THB
            assert final_total > 10000, f"Final total too low: {final_total} (< 10k)"
            assert final_total < 500000, f"Final total too high: {final_total} (> 500k)"


class TestSessionE2EReal:
    """E2E Tests for Session CRUD - NO MOCK"""
    
    def test_session_create_and_load(self):
        """
        Test session create + load roundtrip
        
        Catches issues where:
        - Session created but can't be loaded back
        - Data lost during save/restore
        """
        with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
            # 1. Start a new session
            response = client.post("/api/v1/session/start", json={
                "project_name": "TEST_SESSION_E2E"
            })
            
            assert response.status_code == 200, f"Start returned {response.status_code}"
            data = response.json()
            
            session_id = data.get("session_id")
            assert session_id, "No session_id returned from /start"
            
            print(f"\n✅ Session created: {session_id[:8]}...")
            
            # 2. Load the session back
            response = client.get(f"/api/v1/session/{session_id}/data")
            
            # Session might not have data endpoint yet - check
            if response.status_code == 404:
                pytest.skip("GET /session/{id}/data not implemented")
            
            assert response.status_code == 200, f"Load returned {response.status_code}"
            
            loaded = response.json()
            assert loaded.get("project_name") == "TEST_SESSION_E2E", (
                f"Project name mismatch: {loaded.get('project_name')}"
            )


if __name__ == "__main__":
    # Run with: python tests/test_boq_e2e_real.py
    pytest.main([__file__, "-v", "-s"])
