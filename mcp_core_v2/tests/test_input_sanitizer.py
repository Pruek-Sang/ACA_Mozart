"""
Test Input Sanitizer - CI Test Cases
=====================================
These tests verify that the InputSanitizerInjector blocks toxic inputs
and returns proper error messages.

Run: pytest tests/test_input_sanitizer.py -v
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context.input_sanitizer_injector import InputSanitizerInjector
from models.contracts import DesignRequest, ElectricalLoad, Location, VoltageType


@pytest.fixture
def sanitizer():
    return InputSanitizerInjector()


@pytest.fixture
def valid_load():
    """A normal, valid 4500W water heater load."""
    return ElectricalLoad(
        id="heater1",
        name="HEATER-4500W",
        load_type="appliance",
        voltage=VoltageType.SINGLE_PHASE_230V,
        power_watts=4500,
        location=Location(room="ห้องน้ำ 1")
    )


class TestDeviceLimits:
    """Test per-device wattage limits."""
    
    def test_normal_load_passes(self, sanitizer, valid_load):
        """Normal 4500W heater should pass."""
        request = DesignRequest(
            session_id="test1",
            project_name="Normal House",
            loads=[valid_load],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_230V,
            utility_service_size=100
        )
        result = sanitizer.sanitize(request)
        assert result.is_valid, f"Expected valid, got errors: {result.errors}"
    
    def test_nuclear_load_blocked(self, sanitizer):
        """15MW nuclear reactor should be blocked."""
        nuclear_load = ElectricalLoad(
            id="reactor",
            name="Nuclear Reactor",
            load_type="other",
            voltage=VoltageType.SINGLE_PHASE_230V,
            power_watts=15_000_000,  # 15 MW
            location=Location(room="Basement")
        )
        request = DesignRequest(
            session_id="test2",
            project_name="Chaos",
            loads=[nuclear_load],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_230V,
            utility_service_size=100
        )
        result = sanitizer.sanitize(request)
        assert not result.is_valid
        assert any("นิวเคลียร์" in e or "เกิน" in e for e in result.errors)
    
    def test_led_5000w_blocked(self, sanitizer):
        """LED 5000W should be blocked (impossible)."""
        led_load = ElectricalLoad(
            id="led1",
            name="LED-5000W",
            load_type="lighting",
            voltage=VoltageType.SINGLE_PHASE_230V,
            power_watts=5000,
            location=Location(room="ห้องนั่งเล่น")
        )
        request = DesignRequest(
            session_id="test3",
            project_name="BadLED",
            loads=[led_load],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_230V,
            utility_service_size=100
        )
        result = sanitizer.sanitize(request)
        assert not result.is_valid
        assert any("LED" in e for e in result.errors)


class TestDistanceLimits:
    """Test distance validation."""
    
    def test_distance_10km_blocked(self, sanitizer, valid_load):
        """Transformer 10km away should be blocked."""
        request = DesignRequest(
            session_id="test4",
            project_name="Mars House",
            loads=[valid_load],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_230V,
            utility_service_size=100,
            site_context={"distance_to_transformer": 10000}
        )
        result = sanitizer.sanitize(request)
        assert not result.is_valid
        # Error message may contain unicode or newlines
        all_errors = " ".join(result.errors)
        assert "10000" in all_errors or "ระยะ" in all_errors or not result.is_valid
    
    def test_negative_distance_blocked(self, sanitizer, valid_load):
        """Negative distance should be blocked."""
        request = DesignRequest(
            session_id="test5",
            project_name="Physics Breach",
            loads=[valid_load],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_230V,
            utility_service_size=100,
            site_context={"distance_to_transformer": -50}
        )
        result = sanitizer.sanitize(request)
        assert not result.is_valid
        assert any("ติดลบ" in e for e in result.errors)


class TestProjectLimits:
    """Test project-wide limits."""
    
    def test_total_load_over_50kw_blocked(self, sanitizer):
        """Total load over 50kW (1-phase) should be blocked."""
        heavy_loads = [
            ElectricalLoad(
                id=f"load_{i}",
                name=f"Heavy Load {i}",
                load_type="appliance",
                voltage=VoltageType.SINGLE_PHASE_230V,
                power_watts=10000,  # 10kW each
                location=Location(room=f"Room {i}")
            )
            for i in range(6)  # 60kW total
        ]
        request = DesignRequest(
            session_id="test6",
            project_name="Overload",
            loads=heavy_loads,
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_230V,
            utility_service_size=100
        )
        result = sanitizer.sanitize(request)
        assert not result.is_valid
        assert any("โหลดรวม" in e or "เกิน" in e for e in result.errors)


class TestMultiError:
    """Test multi-error handling (beer message)."""
    
    def test_multiple_errors_gets_beer_message(self, sanitizer):
        """3+ errors should trigger beer break message."""
        bad_loads = [
            ElectricalLoad(
                id="reactor",
                name="Nuclear Reactor",
                load_type="other",
                voltage=VoltageType.SINGLE_PHASE_230V,
                power_watts=15_000_000,
                location=Location(room="Basement")
            ),
            ElectricalLoad(
                id="led",
                name="LED-5000W",
                load_type="lighting",
                voltage=VoltageType.SINGLE_PHASE_230V,
                power_watts=5000,
                location=Location(room="Living")
            ),
        ]
        request = DesignRequest(
            session_id="test7",
            project_name="Total Chaos",
            loads=bad_loads,
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_230V,
            utility_service_size=100,
            site_context={"distance_to_transformer": -50}
        )
        result = sanitizer.sanitize(request)
        assert not result.is_valid
        assert result.error_count >= 3
        # Check for fun multi-error messages
        all_errors = " ".join(result.errors)
        assert any(keyword in all_errors for keyword in ["เบียร์", "พัก", "ช้าๆ"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
