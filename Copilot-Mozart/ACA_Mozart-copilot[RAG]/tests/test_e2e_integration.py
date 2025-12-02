"""
End-to-End Integration Tests

Tests the full flow: RAG → Adapter → MCP Client → MCP Core API

These tests require MCP Core API to be running on port 5001.
Run `pytest tests/test_e2e_integration.py -v -m integration`
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_project_input_spec():
    """Sample ProjectInputSpec from RAG service"""
    from app.models import ProjectInputSpec, ProjectInfo, ElectricalSystem, RoomSpec, LoadSpec, Constraints
    
    return ProjectInputSpec(
        project_info=ProjectInfo(
            project_name="บ้านทดสอบ Integration",
            building_type="residential"
        ),
        electrical_system=ElectricalSystem(
            voltage_system="TH_1PH_230V",
            earthing="TN-S"
        ),
        rooms=[
            RoomSpec(
                room_id="R1",
                name="ห้องนั่งเล่น",
                room_type="LIVING",
                template_code="ROOMT-LIVING-STD",
                area_sqm=30.0
            ),
            RoomSpec(
                room_id="R2",
                name="ห้องนอน",
                room_type="BEDROOM",
                template_code="ROOMT-BEDROOM-STD",
                area_sqm=20.0
            )
        ],
        loads=[
            LoadSpec(
                load_id="L1",
                device_code="LIGHTING-LED-20W",
                room_id="R1",
                qty=4,
                notes="ไฟเพดาน"
            ),
            LoadSpec(
                load_id="L2",
                device_code="SOCKET-OUTLET",
                room_id="R1",
                qty=4,
                notes=None
            ),
            LoadSpec(
                load_id="L3",
                device_code="AC-12000BTU",
                room_id="R1",
                qty=1,
                notes=None
            ),
            LoadSpec(
                load_id="L4",
                device_code="LIGHTING-LED-20W",
                room_id="R2",
                qty=2,
                notes=None
            ),
            LoadSpec(
                load_id="L5",
                device_code="SOCKET-OUTLET",
                room_id="R2",
                qty=2,
                notes=None
            )
        ],
        constraints=Constraints(rule_profile_id="TH_RESIDENTIAL_LV")
    )


@pytest.fixture
def sample_mcp_response_data():
    """Mock response from MCP Core API"""
    return {
        "session_id": "test-session-123",
        "calculations": {
            "total_load_watts": 1680,
            "total_load_amps": 7.0,
            "demand_factor": 0.7,
            "calculated_demand_amps": 4.9
        },
        "wire_sizing": {
            "L1": {"wire_size": "2.5 mm²", "current_amps": 0.33},
            "L2": {"wire_size": "2.5 mm²", "current_amps": 1.5},
            "L3": {"wire_size": "4.0 mm²", "current_amps": 5.0}
        },
        "breaker_selections": {
            "L1": {"breaker_rating": 15, "poles": 1},
            "L2": {"breaker_rating": 15, "poles": 1},
            "L3": {"breaker_rating": 20, "poles": 1}
        },
        "conduit_sizing": {"main_conduit": "25mm EMT"},
        "compliance_report": {"nec_compliant": True, "version": "NEC 2020"},
        "autolisp_code": "; AutoLISP code here",
        "errors": [],
        "warnings": []
    }


# =============================================================================
# Unit Tests (No external dependencies)
# =============================================================================

class TestAdapterConversion:
    """Test RAG → MCP conversion"""
    
    def test_convert_spec_to_mcp_request(self, sample_project_input_spec):
        """ProjectInputSpec → McpDesignRequest"""
        from app.mcp_adapter import McpAdapter
        
        adapter = McpAdapter()
        mcp_request = adapter.convert(sample_project_input_spec)
        
        # Check basic fields
        assert mcp_request.project_name == "บ้านทดสอบ Integration"
        assert mcp_request.service_voltage.value == "240V_1PH"  # Thai → NEC
        
        # Check loads converted
        assert len(mcp_request.loads) == 5
        
        # Check specific load conversion
        lighting_load = next(l for l in mcp_request.loads if l.id == "L1")
        assert lighting_load.power_watts == 20  # LED
        assert lighting_load.quantity == 4
        assert lighting_load.load_type.value == "lighting"
        
        ac_load = next(l for l in mcp_request.loads if l.id == "L3")
        assert ac_load.power_watts == 1200  # 12000 BTU
        assert ac_load.load_type.value == "hvac"
        
        # Check panel created
        assert len(mcp_request.panels) == 1
    
    def test_voltage_mapping(self):
        """Thai voltage → NEC voltage"""
        from app.mcp_adapter import VoltageType, VOLTAGE_MAPPING, DEFAULT_VOLTAGE
        
        assert VOLTAGE_MAPPING.get("TH_1PH_230V") == VoltageType.SINGLE_PHASE_240V
        assert VOLTAGE_MAPPING.get("TH_3PH_380V") == VoltageType.THREE_PHASE_208V
        assert DEFAULT_VOLTAGE == VoltageType.SINGLE_PHASE_240V  # Default
    
    def test_device_mapping_uses_catalog(self):
        """Device codes are mapped using DEVICE_MAPPING"""
        from app.mcp_adapter import DEVICE_MAPPING, LoadType
        
        # Check expected devices exist
        assert "LIGHTING-LED-20W" in DEVICE_MAPPING
        assert "AC-12000BTU" in DEVICE_MAPPING
        assert "SOCKET-OUTLET" in DEVICE_MAPPING
        
        # Check values (tuple format: power_watts, load_type, is_continuous)
        led = DEVICE_MAPPING["LIGHTING-LED-20W"]
        assert led[0] == 20  # power_watts
        assert led[1] == LoadType.LIGHTING
        
        ac = DEVICE_MAPPING["AC-12000BTU"]
        assert ac[0] == 1200  # power_watts
        assert ac[1] == LoadType.HVAC


class TestMcpClientWithMock:
    """Test MCP Client with mocked HTTP"""
    
    @pytest.mark.asyncio
    async def test_design_success(self, sample_mcp_response_data):
        """Successful MCP call"""
        from app.mcp_client import McpClient
        from app.mcp_adapter import McpDesignRequest, McpElectricalLoad, McpPanelSpec, McpLocation, VoltageType, LoadType
        from unittest.mock import MagicMock
        
        # Create mock request
        request = McpDesignRequest(
            session_id="test-123",
            project_name="Test Project",
            loads=[
                McpElectricalLoad(
                    id="L1",
                    name="Test Light",
                    load_type=LoadType.LIGHTING,
                    voltage=VoltageType.SINGLE_PHASE_240V,
                    power_watts=100,
                    quantity=1,
                    location=McpLocation(room="Living Room")
                )
            ],
            panels=[
                McpPanelSpec(
                    id="P1",
                    name="Main Panel",
                    voltage=VoltageType.SINGLE_PHASE_240V,
                    main_breaker_rating=100,
                    number_of_circuits=20,
                    location=McpLocation(room="Garage"),
                    feeds=["L1"]
                )
            ],
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=100
        )
        
        # Mock httpx response - json() returns sync, not coroutine
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_mcp_response_data
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            client = McpClient(base_url="http://test:5001")
            response = await client.design(request)
        
        assert response.success is True
        assert response.session_id == "test-session-123"
        assert response.calculations is not None
        assert response.calculations["total_load_watts"] == 1680
        assert response.wire_sizing is not None
        assert "L1" in response.wire_sizing
    
    @pytest.mark.asyncio
    async def test_design_timeout(self):
        """Handle MCP timeout gracefully"""
        from app.mcp_client import McpClient
        from app.mcp_adapter import McpDesignRequest, VoltageType
        import httpx
        
        request = McpDesignRequest(
            session_id="test-timeout",
            project_name="Timeout Test",
            loads=[],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=100
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timed out")
            )
            
            client = McpClient(base_url="http://test:5001", timeout=5.0)
            response = await client.design(request)
        
        assert response.success is False
        assert response.error_message is not None
        assert "timeout" in response.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_design_connection_error(self):
        """Handle connection error gracefully"""
        from app.mcp_client import McpClient
        from app.mcp_adapter import McpDesignRequest, VoltageType
        import httpx
        
        request = McpDesignRequest(
            session_id="test-conn-error",
            project_name="Connection Error Test",
            loads=[],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=100
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            
            client = McpClient(base_url="http://localhost:5001")
            response = await client.design(request)
        
        assert response.success is False
        assert response.error_message is not None
        assert "cannot connect" in response.error_message.lower()


class TestFullE2EFlow:
    """Test complete RAG → MCP flow"""
    
    @pytest.mark.asyncio
    async def test_full_flow_mock(self, sample_project_input_spec, sample_mcp_response_data):
        """Full flow with mocked MCP Core"""
        from app.mcp_adapter import McpAdapter
        from app.mcp_client import McpClient
        from unittest.mock import MagicMock
        
        # Step 1: Convert spec
        adapter = McpAdapter()
        mcp_request = adapter.convert(sample_project_input_spec)
        
        # Verify conversion
        assert len(mcp_request.loads) == 5
        assert mcp_request.service_voltage.value == "240V_1PH"
        
        # Step 2: Call MCP (mocked) - json() is sync method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_mcp_response_data
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            client = McpClient(base_url="http://test:5001")
            mcp_result = await client.design(mcp_request)
        
        # Step 3: Verify result
        assert mcp_result.success is True
        assert mcp_result.wire_sizing is not None
        assert mcp_result.breaker_selections is not None
        assert mcp_result.autolisp_code is not None


# =============================================================================
# Live Integration Tests (requires running services)
# =============================================================================

@pytest.mark.skipif(True, reason="Requires running MCP Core API on port 5001")
class TestLiveIntegration:
    """Tests that require actual MCP Core running"""
    
    @pytest.mark.asyncio
    async def test_health_check_live(self):
        """Test actual MCP Core health check"""
        from app.mcp_client import McpClient
        
        client = McpClient()
        is_healthy = await client.health_check()
        assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_design_live(self, sample_project_input_spec):
        """Test actual MCP Core design call"""
        from app.mcp_adapter import McpAdapter
        from app.mcp_client import McpClient
        
        adapter = McpAdapter()
        mcp_request = adapter.convert(sample_project_input_spec)
        
        client = McpClient()
        response = await client.design(mcp_request)
        
        assert response.success is True
        assert response.calculations is not None
        assert response.wire_sizing is not None


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
