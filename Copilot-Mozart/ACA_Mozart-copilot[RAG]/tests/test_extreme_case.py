

# import pytest (Removed for standalone run)
from app.service import RagService
from mcp_core_v2.pipeline import DesignPipeline
from mcp_core_v2.models.contracts import DesignRequest, ElectricalLoad, LoadType, VoltageType, Location

class MockGatewayRequest:
    def __init__(self, input_text):
        self.input = input_text
        self.session_id = "test_session_extreme_001"

# @pytest.mark.asyncio (Removed)
async def test_extreme_case_output():
    """
    Test Extreme Case:
    - Distance to transformer: 10m (<50m) -> Expect 10kA
    - Installation: Outdoor -> Expect Derating Warning
    - Panel: Sub-Panel -> Expect N-G Link Warning
    """
    
    # 1. Setup Service and Pipeline
    service = RagService()
    # Mocking behaviors if necessary (omitted for integration test style)
    
    # 2. Simulate User Input with Extreme Context
    user_input = """
    ออกแบบระบบไฟฟ้าบ้าน 2 ชั้น
    มีแอร์ 3 ตัว (12000 BTU)
    เครื่องทำน้ำอุ่น 2 เครื่อง (3500W)
    เต้ารับ 10 จุด
    
    [Context]
    ระยะหม้อแปลง: 10 เมตร
    พื้นที่ติดตั้ง: กลางแดด (Outdoor)
    ประเภทตู้: ตู้ย่อย (Sub Panel)
    """
    
    # Direct pipeline execution for precise checking
    pipeline = DesignPipeline()
    req = DesignRequest(
        project_name="Extreme Case Test",
        loads=[
            ElectricalLoad(id="L1", name="AC 1", load_type=LoadType.HVAC, power_watts=1500, quantity=3, location=Location(floor="1", room="Bedroom")),
            ElectricalLoad(id="L2", name="Water Heater", load_type=LoadType.APPLIANCE, power_watts=3500, quantity=2, location=Location(floor="1", room="Bath")),
            ElectricalLoad(id="L3", name="Socket", load_type=LoadType.RECEPTACLE, power_watts=300, quantity=10, location=Location(floor="1", room="Living"))
        ],
        site_context={
            "distance_to_transformer": 10,
            "installation_area": "outdoor",
            "panel_type": "sub_panel"
        }
    )
    
    # 3. Execution
    result = pipeline.execute(req)
    result_dict = result.model_dump()
    
    # 4. Verification of Injector Results
    print("\n--- Injector Verification ---")
    
    # Check kA Rating (kA Injector)
    breakers = result_dict['breaker_selections']
    main_breaker = breakers.get('DB-1_main') or breakers.get('panel_main') or list(breakers.values())[0] # Fallback
    
    # Note: In pipeline result, ka_rating might be in metadata or modified breaker.
    # But we check the 'warnings' first as per our update
    warnings = result_dict.get('warnings', [])
    print(f"Warnings found: {warnings}")
    
    has_ng_warning = any("N-G" in str(w) and "SUB-PANEL" in str(w) for w in warnings)
    has_ka_warning = any("kA" in str(w) or "transformer" in str(w) for w in warnings) # Or check breaker rating directly
    
    # 5. Verification of Formatter (Simulating service.py logic)
    formatted_text = service._format_design_result_as_text({"design_result": result_dict, "site_context": req.site_context})
    
    print("\n--- Formatter Output Verification ---")
    print(formatted_text)
    
    # Assertions
    assert has_ng_warning, "Should have N-G Link warning for Sub-Panel"
    assert "10kA" in formatted_text, "Output should display 10kA for short distance"
    assert "Derating" in formatted_text or "กลางแดด" in formatted_text, "Output should mention Derating for Outdoor"
    assert "ห้ามต่อสาย N-G" in formatted_text, "Output should display N-G warning text"

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_extreme_case_output())
