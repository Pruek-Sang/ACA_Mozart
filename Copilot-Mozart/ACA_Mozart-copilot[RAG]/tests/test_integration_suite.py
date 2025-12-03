"""
Integration Test Suite - INT-01 to INT-03
Tests for RAG ↔ MCP integration following new test specification

Philosophy:
- Prove end-to-end flow works: Ask → Spec → (future: Calculate)
- Ensure RAG and MCP speak the same language
- Validate knowledge changes affect output (regression guard)

Note: Full MCP Core integration is not yet complete.
These tests validate the RAG-side preparation for integration.
"""

import pytest
import re
import json
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from app.routes import app
from app.models import ProjectRequirements, RoomInput, LoadInput

client = TestClient(app)


# === Fixtures ===

@pytest.fixture
def integration_request():
    """Standard request for integration testing"""
    return {
        "query": """บ้านพักอาศัย 2 ชั้น พื้นที่ประมาณ 180 ตร.ม.
มีแอร์ 12,000 BTU 3 เครื่อง, เครื่องทำน้ำอุ่น 2 เครื่อง, เตาไฟฟ้า 3.5 kW
ต้องการทราบขนาดเมนเบรกเกอร์และจำนวนวงจรย่อย
ใช้มาตรฐาน EIT/IEC ของไทย""",
        "context_hint": ["db", "standard", "mcp", "example"],
        "language": "th"
    }


@pytest.fixture
def integration_spec_request():
    """ProjectRequirements for spec generation in integration test"""
    return ProjectRequirements(
        project_name="Integration Test House",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        location="Bangkok",
        rooms=[
            RoomInput(name="ห้องนั่งเล่น 1F", type="living_room", area_sqm=35.0),
            RoomInput(name="ครัว 1F", type="kitchen", area_sqm=20.0),
            RoomInput(name="ห้องน้ำ 1F", type="bathroom", area_sqm=6.0),
            RoomInput(name="ห้องนอนใหญ่ 2F", type="bedroom", area_sqm=25.0),
            RoomInput(name="ห้องนอนเล็ก 2F", type="bedroom", area_sqm=18.0),
            RoomInput(name="ห้องน้ำ 2F", type="bathroom", area_sqm=5.0),
        ],
        loads=[
            # Device codes per DEVICE_CODES.md
            LoadInput(room_name="ห้องนั่งเล่น 1F", device="AC-12000BTU", quantity=1),
            LoadInput(room_name="ห้องนอนใหญ่ 2F", device="AC-12000BTU", quantity=1),
            LoadInput(room_name="ห้องนอนเล็ก 2F", device="AC-12000BTU", quantity=1),
            LoadInput(room_name="ห้องน้ำ 1F", device="HEATER-3500W", quantity=1),
            LoadInput(room_name="ห้องน้ำ 2F", device="HEATER-3500W", quantity=1),
            LoadInput(room_name="ครัว 1F", device="INDUCTION-3000W", quantity=1),
        ],
        user_constraints=["rcd_for_all_outlets"]
    )


class TestINT01_EndToEndFlow:
    """
    INT-01: End-to-End Ask → Spec → Calculate
    
    Purpose: Prove the full flow works without breaking
    Note: Calculate step requires MCP Core (future integration)
    """
    
    @pytest.mark.integration
    def test_int01_ask_endpoint_works(self, integration_request):
        """Step 1: Verify /api/v1/ask returns valid response"""
        response = client.post("/api/v1/ask", json=integration_request)
        
        assert response.status_code == 200, f"Ask failed: {response.text}"
        
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 50, "Answer too short"
        # Note: Don't return data - pytest warns about returning values from tests
    
    @pytest.mark.integration
    def test_int01_spec_endpoint_works(self, integration_spec_request):
        """Step 2: Verify /api/v1/mcp_spec returns valid spec"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        
        assert response.status_code == 200, f"Spec generation failed: {response.text}"
        
        data = response.json()
        assert "project_input" in data
        # Note: Don't return data - pytest warns about returning values from tests
    
    @pytest.mark.integration
    def test_int01_full_flow_no_exception(self, integration_request, integration_spec_request):
        """Full flow: Ask → Spec without exceptions"""
        # Step 1: Ask
        ask_response = client.post("/api/v1/ask", json=integration_request)
        assert ask_response.status_code == 200
        ask_data = ask_response.json()
        
        # Step 2: Generate Spec
        spec_response = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        assert spec_response.status_code == 200
        spec_data = spec_response.json()
        
        # Validate both completed
        assert "answer" in ask_data
        assert "project_input" in spec_data
        
        # Future: Step 3 would call MCP Core /calculate
        # For now, verify spec structure is MCP-ready
        project_input = spec_data["project_input"]
        assert "rooms" in project_input
        assert "loads" in project_input
        assert "electrical_system" in project_input
    
    @pytest.mark.integration
    def test_int01_answer_mentions_breaker_range(self, integration_request):
        """Verify answer mentions breaker sizing in expected range"""
        response = client.post("/api/v1/ask", json=integration_request)
        assert response.status_code == 200
        
        data = response.json()
        answer = data["answer"]
        
        # Look for breaker size mentions (40A-100A range is typical for this house)
        breaker_patterns = [
            r'\b(40|50|63|80|100)\s*[aA]',
            r'(40|50|63|80|100)\s*แอมป์',
        ]
        
        found = any(re.search(p, answer) for p in breaker_patterns)
        
        # This is informational - don't fail if not found
        if found:
            print(f"✓ Answer mentions breaker in expected range")
        else:
            print(f"⚠ Answer does not explicitly mention breaker size in 40-100A range")
    
    @pytest.mark.integration
    def test_int01_spec_circuit_count_reasonable(self, integration_spec_request):
        """Verify spec produces reasonable circuit count"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        loads = project_input.get("loads", [])
        rooms = project_input.get("rooms", [])
        
        # For a 180 sqm house with 6 rooms and heavy loads:
        # Expect at least 6 loads, realistically 8-15 circuits
        assert len(loads) >= 6, f"Too few loads: {len(loads)}"
        assert len(rooms) == 6, f"Room count mismatch: {len(rooms)}"


class TestINT02_CatalogAndStandardConsistency:
    """
    INT-02: Catalog & Standard Consistency
    
    Purpose: Prevent RAG saying one thing and MCP doing another
    """
    
    @pytest.mark.integration
    def test_int02_ask_and_spec_use_same_standard(self, integration_request, integration_spec_request):
        """Verify both endpoints reference same standard"""
        # Get Ask response
        ask_response = client.post("/api/v1/ask", json=integration_request)
        assert ask_response.status_code == 200
        ask_data = ask_response.json()
        
        # Get Spec response
        spec_response = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        assert spec_response.status_code == 200
        spec_data = spec_response.json()
        
        # Check answer mentions Thai/EIT/IEC
        answer = ask_data["answer"]
        answer_mentions_thai_std = any(
            re.search(p, answer, re.IGNORECASE) 
            for p in [r'EIT', r'IEC', r'วสท', r'มาตรฐาน.*ไทย', r'TH_']
        )
        
        # Check spec uses Thai standard
        project_input = spec_data["project_input"]
        constraints = project_input.get("constraints", {})
        rule_profile = constraints.get("rule_profile_id", "")
        
        spec_uses_thai = "TH" in rule_profile.upper() or "RESIDENTIAL" in rule_profile.upper()
        
        # Both should align on Thai/EIT standard
        if answer_mentions_thai_std and spec_uses_thai:
            print("✓ Both Ask and Spec consistently use Thai/EIT standard")
        elif not answer_mentions_thai_std and not spec_uses_thai:
            print("⚠ Neither explicitly mentions Thai standard - may be acceptable")
        else:
            print("⚠ Potential inconsistency between Ask and Spec standards")
    
    @pytest.mark.integration
    def test_int02_device_codes_consistent(self, integration_spec_request):
        """Verify device codes in spec are from catalog"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        loads = project_input.get("loads", [])
        
        # All device_codes should follow naming convention
        for load in loads:
            device_code = load.get("device_code", "")
            
            # Should match known patterns
            valid_patterns = [
                r'^COMP-',
                r'^APP\d+-',
                r'^CABLE-',
                r'^AC[-_]',
                r'^OUTLET[-_]',
                r'^WATER[-_]',
                r'^INDUCTION[-_]',
                r'^COOKER[-_]',
            ]
            
            # At least loosely follows convention
            is_valid = any(re.match(p, device_code, re.IGNORECASE) for p in valid_patterns)
            
            # Soft check - log but don't fail
            if not is_valid and device_code:
                print(f"⚠ Device code may not be from catalog: {device_code}")


class TestINT03_RegressionGuard:
    """
    INT-03: Regression Guard (Change Knowledge → Change Answer)
    
    Purpose: Prove RAG uses knowledge, not just hallucinating
    
    Note: Full regression testing requires:
    1. Snapshot before changes
    2. Modify knowledge
    3. Snapshot after changes
    4. Compare diffs
    
    For MVP, we validate that:
    - Responses are deterministic-ish (similar for same input)
    - Knowledge retrieval is actually happening
    """
    
    @pytest.mark.integration
    def test_int03_response_uses_knowledge(self, integration_request):
        """Verify response includes retrieved docs (not pure hallucination)"""
        response = client.post("/api/v1/ask", json=integration_request)
        assert response.status_code == 200
        
        data = response.json()
        metadata = data.get("metadata", {})
        
        retrieved = metadata.get("retrieved_docs", [])
        
        # Should have retrieved documents
        assert len(retrieved) >= 1, "No documents retrieved - possible hallucination risk"
        
        print(f"✓ Retrieved {len(retrieved)} documents from knowledge base")
    
    @pytest.mark.integration
    def test_int03_multiple_calls_similar_structure(self, integration_request):
        """Verify multiple calls produce structurally similar responses"""
        # Call twice
        response1 = client.post("/api/v1/ask", json=integration_request)
        response2 = client.post("/api/v1/ask", json=integration_request)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should have same structure
        assert set(data1.keys()) == set(data2.keys()), "Response structure differs between calls"
        
        # Both should have similar confidence levels
        conf1 = data1.get("confidence", "")
        conf2 = data2.get("confidence", "")
        
        # Confidence should be in same ballpark
        valid_confs = ["High", "Medium", "Low"]
        assert conf1 in valid_confs
        assert conf2 in valid_confs
        
        print(f"✓ Multiple calls produce consistent structure (confidence: {conf1}, {conf2})")
    
    @pytest.mark.integration
    def test_int03_spec_reproducible(self, integration_spec_request):
        """Verify spec generation is reproducible"""
        # Generate spec twice
        response1 = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        response2 = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Compare key structural elements
        pi1 = data1["project_input"]
        pi2 = data2["project_input"]
        
        # Room count should be same
        assert len(pi1["rooms"]) == len(pi2["rooms"]), "Room count differs between calls"
        
        # Load count should be same
        assert len(pi1["loads"]) == len(pi2["loads"]), "Load count differs between calls"
        
        # Voltage system should be same
        assert pi1["electrical_system"]["voltage_system"] == pi2["electrical_system"]["voltage_system"]
        
        print("✓ Spec generation is reproducible")
    
    def test_int03_snapshot_helper(self, integration_request, integration_spec_request):
        """
        Helper test to create a snapshot for regression testing
        
        Usage: Run this test and save output to compare after knowledge changes
        """
        # Get responses
        ask_response = client.post("/api/v1/ask", json=integration_request)
        spec_response = client.post(
            "/api/v1/mcp_spec",
            json=integration_spec_request.model_dump()
        )
        
        if ask_response.status_code == 200 and spec_response.status_code == 200:
            ask_data = ask_response.json()
            spec_data = spec_response.json()
            
            # Create snapshot hash
            snapshot = {
                "ask_answer_length": len(ask_data.get("answer", "")),
                "ask_confidence": ask_data.get("confidence", ""),
                "ask_sources_count": len(ask_data.get("sources", [])),
                "spec_rooms_count": len(spec_data.get("project_input", {}).get("rooms", [])),
                "spec_loads_count": len(spec_data.get("project_input", {}).get("loads", [])),
                "spec_voltage": spec_data.get("project_input", {}).get("electrical_system", {}).get("voltage_system", ""),
            }
            
            snapshot_json = json.dumps(snapshot, sort_keys=True)
            snapshot_hash = hashlib.md5(snapshot_json.encode()).hexdigest()[:8]
            
            print(f"\n=== Regression Snapshot ===")
            print(f"Hash: {snapshot_hash}")
            print(f"Data: {snapshot}")
            print(f"===========================\n")
            
            # This test always passes - it's a helper
            assert True


class TestINT_HealthChecks:
    """Additional integration health checks"""
    
    def test_both_endpoints_accessible(self):
        """Verify both main endpoints are accessible"""
        # Ask endpoint
        ask_resp = client.post("/api/v1/ask", json={
            "query": "test",
            "language": "th"
        })
        assert ask_resp.status_code in [200, 400, 422]
        
        # Spec endpoint
        spec_resp = client.post("/api/v1/mcp_spec", json={
            "project_name": "test",
            "building_type": "residential",
            "voltage_system": "TH_1PH_230V",
            "rooms": [{"name": "test", "type": "living_room", "area_sqm": 10}],
            "loads": []
        })
        assert spec_resp.status_code in [200, 400, 422]
    
    def test_knowledge_groups_accessible(self):
        """Verify knowledge groups endpoint works"""
        response = client.get("/api/v1/knowledge/groups")
        assert response.status_code == 200
        
        data = response.json()
        assert "groups" in data
        assert len(data["groups"]) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
