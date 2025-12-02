"""
Tests for MCP Adapter

Tests conversion from RAG ProjectInputSpec to MCP DesignRequest
"""

import pytest
from app.mcp_adapter import (
    McpAdapter,
    convert_to_mcp,
    get_device_info,
    list_known_devices,
    VoltageType,
    LoadType,
    DEVICE_MAPPING,
    VOLTAGE_MAPPING
)
from app.models import (
    ProjectInputSpec,
    ProjectInfo,
    ElectricalSystem,
    RoomSpec,
    LoadSpec,
    Constraints
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def basic_spec():
    """Create a basic ProjectInputSpec for testing"""
    return ProjectInputSpec(
        project_info=ProjectInfo(
            project_name="Test House",
            building_type="RESIDENTIAL"
        ),
        electrical_system=ElectricalSystem(
            voltage_system="TH_1PH_230V",
            earthing="TT"
        ),
        rooms=[
            RoomSpec(
                room_id="R1",
                name="Living Room",
                room_type="LIVING",
                template_code="ROOMT-LIVING-STD"
            ),
            RoomSpec(
                room_id="R2",
                name="Bedroom",
                room_type="BEDROOM",
                template_code="ROOMT-BEDROOM-STD",
                area_sqm=15.0
            )
        ],
        loads=[
            LoadSpec(load_id="L1", room_id="R1", device_code="AC-12000BTU", qty=1),
            LoadSpec(load_id="L2", room_id="R1", device_code="SOCKET-16A", qty=4),
            LoadSpec(load_id="L3", room_id="R2", device_code="AC-9000BTU", qty=1),
        ],
        constraints=Constraints(
            rule_profile_id="TH_RESIDENTIAL_LV",
            user_constraints=[]
        )
    )


@pytest.fixture
def adapter():
    """Create a fresh adapter instance"""
    return McpAdapter()


# =============================================================================
# Device Mapping Tests
# =============================================================================

class TestDeviceMapping:
    """Tests for device code to watts/type mapping"""
    
    def test_ac_12000btu_mapping(self):
        """AC-12000BTU should map to 1200W HVAC continuous"""
        watts, load_type, continuous = get_device_info("AC-12000BTU")
        assert watts == 1200
        assert load_type == "hvac"
        assert continuous is True
    
    def test_socket_16a_mapping(self):
        """SOCKET-16A should map to 180W receptacle non-continuous"""
        watts, load_type, continuous = get_device_info("SOCKET-16A")
        assert watts == 180
        assert load_type == "receptacle"
        assert continuous is False
    
    def test_heater_3500w_mapping(self):
        """HEATER-3500W should map correctly"""
        watts, load_type, continuous = get_device_info("HEATER-3500W")
        assert watts == 3500
        assert load_type == "appliance"
        assert continuous is False
    
    def test_unknown_device_returns_default(self):
        """Unknown device code should return safe defaults"""
        watts, load_type, continuous = get_device_info("UNKNOWN-DEVICE")
        assert watts == 500  # Default power
        assert load_type == "other"
        assert continuous is False
    
    def test_all_documented_devices_exist(self):
        """All devices in DEVICE_CODES.md should be in mapping"""
        known = list_known_devices()
        
        # Key devices that must exist
        required = [
            "AC-9000BTU", "AC-12000BTU", "AC-18000BTU", "AC-24000BTU",
            "SOCKET-16A", "SOCKET-20A",
            "HEATER-3500W", "HEATER-4500W",
            "INDUCTION-3000W"
        ]
        
        for device in required:
            assert device in known, f"Missing required device: {device}"


# =============================================================================
# Voltage Mapping Tests
# =============================================================================

class TestVoltageMapping:
    """Tests for voltage system mapping"""
    
    def test_thai_1ph_230v_maps_to_240v(self):
        """TH_1PH_230V should map to SINGLE_PHASE_240V for NEC"""
        adapter = McpAdapter()
        spec = ProjectInputSpec(
            project_info=ProjectInfo(project_name="Test", building_type="RESIDENTIAL"),
            electrical_system=ElectricalSystem(voltage_system="TH_1PH_230V"),
            rooms=[],
            loads=[],
            constraints=Constraints(rule_profile_id="TH_RESIDENTIAL_LV")
        )
        
        result = adapter.convert(spec)
        assert result.service_voltage == VoltageType.SINGLE_PHASE_240V
    
    def test_thai_3ph_380v_maps_to_208v(self):
        """TH_3PH_380V should map to THREE_PHASE_208V"""
        adapter = McpAdapter()
        voltage = adapter._map_voltage("TH_3PH_380V")
        assert voltage == VoltageType.THREE_PHASE_208V
    
    def test_unknown_voltage_uses_default(self):
        """Unknown voltage should use 240V default"""
        adapter = McpAdapter()
        voltage = adapter._map_voltage("UNKNOWN_VOLTAGE")
        assert voltage == VoltageType.SINGLE_PHASE_240V


# =============================================================================
# Full Conversion Tests
# =============================================================================

class TestFullConversion:
    """Tests for complete spec conversion"""
    
    def test_basic_conversion(self, adapter, basic_spec):
        """Test basic conversion works end-to-end"""
        result = adapter.convert(basic_spec)
        
        # Check project name preserved
        assert result.project_name == "Test House"
        
        # Check loads converted
        assert len(result.loads) == 3
        
        # Check panel created
        assert len(result.panels) == 1
        
        # Check session ID generated
        assert result.session_id.startswith("rag_")
    
    def test_loads_have_correct_power(self, adapter, basic_spec):
        """Loads should have correct power values"""
        result = adapter.convert(basic_spec)
        
        # Find AC-12000BTU load
        ac_load = next(l for l in result.loads if "AC-12000BTU" in l.name)
        assert ac_load.power_watts == 1200
        assert ac_load.load_type == LoadType.HVAC
    
    def test_room_names_in_load_locations(self, adapter, basic_spec):
        """Load locations should include room names"""
        result = adapter.convert(basic_spec)
        
        # First load is in Living Room
        assert result.loads[0].location.room == "Living Room"
    
    def test_panel_has_all_load_ids(self, adapter, basic_spec):
        """Panel should feed all loads"""
        result = adapter.convert(basic_spec)
        
        panel = result.panels[0]
        assert "L1" in panel.feeds
        assert "L2" in panel.feeds
        assert "L3" in panel.feeds
    
    def test_to_dict_serializable(self, adapter, basic_spec):
        """to_dict() should produce JSON-serializable output"""
        import json
        
        result = adapter.convert(basic_spec)
        data = result.to_dict()
        
        # Should not raise
        json_str = json.dumps(data)
        assert len(json_str) > 0
    
    def test_unknown_device_tracked(self, adapter):
        """Unknown devices should be tracked"""
        spec = ProjectInputSpec(
            project_info=ProjectInfo(project_name="Test", building_type="RESIDENTIAL"),
            electrical_system=ElectricalSystem(voltage_system="TH_1PH_230V"),
            rooms=[RoomSpec(room_id="R1", name="Room", room_type="OTHER", template_code="ROOMT-OTHER")],
            loads=[LoadSpec(load_id="L1", room_id="R1", device_code="MYSTERY-DEVICE", qty=1)],
            constraints=Constraints(rule_profile_id="TH_RESIDENTIAL_LV")
        )
        
        result = adapter.convert(spec)
        
        # Unknown device should be tracked
        assert "MYSTERY-DEVICE" in adapter.unknown_devices
        
        # But conversion should still work
        assert len(result.loads) == 1


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_loads(self, adapter):
        """Should handle empty loads gracefully"""
        spec = ProjectInputSpec(
            project_info=ProjectInfo(project_name="Empty", building_type="RESIDENTIAL"),
            electrical_system=ElectricalSystem(voltage_system="TH_1PH_230V"),
            rooms=[],
            loads=[],
            constraints=Constraints(rule_profile_id="TH_RESIDENTIAL_LV")
        )
        
        result = adapter.convert(spec)
        
        assert len(result.loads) == 0
        assert len(result.panels) == 1  # Still need a panel
        assert result.panels[0].number_of_circuits == 12  # Minimum size
    
    def test_missing_room_reference(self, adapter):
        """Should handle loads referencing non-existent rooms"""
        spec = ProjectInputSpec(
            project_info=ProjectInfo(project_name="Test", building_type="RESIDENTIAL"),
            electrical_system=ElectricalSystem(voltage_system="TH_1PH_230V"),
            rooms=[RoomSpec(room_id="R1", name="Room1", room_type="BEDROOM", template_code="ROOMT-BEDROOM-STD")],
            loads=[LoadSpec(load_id="L1", room_id="R99", device_code="AC-12000BTU", qty=1)],  # R99 doesn't exist
            constraints=Constraints(rule_profile_id="TH_RESIDENTIAL_LV")
        )
        
        result = adapter.convert(spec)
        
        # Should still convert, with "Unknown Room"
        assert result.loads[0].location.room == "Unknown Room"
    
    def test_high_load_increases_panel_size(self, adapter):
        """Many loads should result in larger panel"""
        rooms = [RoomSpec(room_id=f"R{i}", name=f"Room{i}", room_type="BEDROOM", template_code="ROOMT-BEDROOM-STD") 
                 for i in range(1, 6)]
        
        # 25 loads (5 per room)
        loads = []
        for i in range(1, 26):
            room_id = f"R{((i-1) % 5) + 1}"
            loads.append(LoadSpec(load_id=f"L{i}", room_id=room_id, device_code="SOCKET-16A", qty=1))
        
        spec = ProjectInputSpec(
            project_info=ProjectInfo(project_name="Big House", building_type="RESIDENTIAL"),
            electrical_system=ElectricalSystem(voltage_system="TH_1PH_230V"),
            rooms=rooms,
            loads=loads,
            constraints=Constraints(rule_profile_id="TH_RESIDENTIAL_LV")
        )
        
        result = adapter.convert(spec)
        
        # Should have at least 30 circuits (25 * 1.2 rounded up)
        assert result.panels[0].number_of_circuits >= 30


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""
    
    def test_convert_to_mcp_function(self, basic_spec):
        """convert_to_mcp() should work like adapter.convert()"""
        result = convert_to_mcp(basic_spec)
        
        assert result.project_name == "Test House"
        assert len(result.loads) == 3
    
    def test_list_known_devices(self):
        """list_known_devices() should return all device codes"""
        devices = list_known_devices()
        
        assert len(devices) > 10  # We have at least 10 devices
        assert "AC-12000BTU" in devices
        assert "SOCKET-16A" in devices
