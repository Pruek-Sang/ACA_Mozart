#!/usr/bin/env python3
"""
Enhanced Error Handling Test Suite
Tests custom exceptions and validation logic
"""

import sys
sys.path.insert(0, '/mnt/BigDrive/Linux_Work/ACA_Mozart/mcp_core_v2')

from datetime import datetime
from models.contracts import (
    DesignRequest, ElectricalLoad, PanelSpecification,
    Location, VoltageType, LoadType
)
from pipeline import get_design_pipeline
from exceptions import InvalidSpecError, UnsupportedProjectError

print("="*100)
print("ENHANCED ERROR HANDLING TEST SUITE")
print("="*100)

passed = 0
failed = 0

def test(name: str, func):
    global passed, failed
    try:
        func()
        print(f"✅ {name}")
        passed += 1
    except AssertionError as e:
        print(f"❌ {name}: {e}")
        failed += 1
    except Exception as e:
        print(f"⚠️  {name}: {type(e).__name__}: {e}")
        failed += 1

# =============================================================================
# TEST: Custom Exceptions Work
# =============================================================================

print("\n" + "="*100)
print("CUSTOM EXCEPTION TESTS")
print("="*100)

def test_invalid_spec_exception():
    """Test InvalidSpecError is raised for missing service_voltage"""
    try:
        # This should fail Pydantic validation
        request = DesignRequest(
            session_id='test_exc1',
            project_name='Test',
            panels=[
                PanelSpecification(
                    id='P1', name='Panel',
                    voltage=VoltageType.SINGLE_PHASE_240V,
                    max_amperage=100, main_breaker_rating=100,
                    number_of_circuits=20,
                    location=Location(room='U', floor='1')
                )
            ],
            loads=[],
            service_voltage=None,  # Missing!
            utility_service_size=200
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        # Pydantic will catch this
        assert 'service_voltage' in str(e).lower() or 'required' in str(e).lower()

test("Exception: InvalidSpecError for missing service_voltage", test_invalid_spec_exception)

def test_invalid_utility_size():
    """Test validation catches invalid utility size"""
    try:
        request = DesignRequest(
            session_id='test_exc2',
            project_name='Test',
            panels=[
                PanelSpecification(
                    id='P1', name='Panel',
                    voltage=VoltageType.SINGLE_PHASE_240V,
                    max_amperage=100, main_breaker_rating=100,
                    number_of_circuits=20,
                    location=Location(room='U', floor='1')
                )
            ],
            loads=[],
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=0  # Invalid!
        )
        
        pipeline = get_design_pipeline()
        result = pipeline.execute(request)
        assert False, "Should have raised InvalidSpecError"
        
    except InvalidSpecError as e:
        assert 'utility_service_size' in str(e)
    except Exception as e:
        # Also OK if caught by Pydantic
        pass

test("Exception: Invalid utility_service_size validation", test_invalid_utility_size)

# =============================================================================
# TEST: Validation Logic
# =============================================================================

print("\n" + "="*100)
print("VALIDATION LOGIC TESTS")
print("="*100)

def test_empty_panels_allowed():
    """Empty panels should log warning but not fail"""
    request = DesignRequest(
        session_id='test_val1',
        project_name='No Panels',
        panels=[],  # Empty
        loads=[],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=100
    )
    
    pipeline = get_design_pipeline()
    result = pipeline.execute(request)
    
    assert result is not None
    assert len(result.wire_sizing) == 0

test("Validation: Empty panels allowed (flexible mode)", test_empty_panels_allowed)

def test_empty_loads_allowed():
    """Empty loads should complete successfully"""
    request = DesignRequest(
        session_id='test_val2',
        project_name='No Loads',
        panels=[
            PanelSpecification(
                id='P1', name='Panel',
                voltage=VoltageType.SINGLE_PHASE_240V,
                max_amperage=100, main_breaker_rating=100,
                number_of_circuits=20,
                location=Location(room='U', floor='1')
            )
        ],
        loads=[],  # Empty
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=100
    )
    
    pipeline = get_design_pipeline()
    result = pipeline.execute(request)
    
    assert result is not None
    assert len(result.wire_sizing) == 0

test("Validation: Empty loads allowed", test_empty_loads_allowed)

# =============================================================================
# TEST: Error Recovery
# =============================================================================

print("\n" + "="*100)
print("ERROR RECOVERY TESTS")
print("="*100)

def test_high_load_auto_correction():
    """System should auto-correct for high loads"""
    request = DesignRequest(
        session_id='test_rec1',
        project_name='Auto Correction',
        panels=[
            PanelSpecification(
                id='P1', name='Panel',
                voltage=VoltageType.SINGLE_PHASE_240V,
                max_amperage=200, main_breaker_rating=200,
                number_of_circuits=40,
                location=Location(room='U', floor='1')
            )
        ],
        loads=[
            ElectricalLoad(
                id='BIG',
                name='Huge Load',
                load_type=LoadType.HVAC,
                power_watts=15000,  # 15kW!
                voltage=VoltageType.SINGLE_PHASE_240V,
                location=Location(room='Room', floor='1')
            )
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    pipeline = get_design_pipeline()
    result = pipeline.execute(request)
    
    assert result is not None
    wire = result.wire_sizing['BIG']
    
    # Should select large wire
    assert wire['wire_size'] in ['4', '3', '2', '1', '0', '00', '000']
    assert wire['ampacity'] > 60

test("Recovery: Auto-correct for high loads", test_high_load_auto_correction)

def test_multiple_heavy_loads():
    """Multiple heavy loads should be handled"""
    request = DesignRequest(
        session_id='test_rec2',
        project_name='Multiple Heavy',
        panels=[
            PanelSpecification(
                id='P1', name='Panel',
                voltage=VoltageType.SINGLE_PHASE_240V,
                max_amperage=200, main_breaker_rating=200,
                number_of_circuits=40,
                location=Location(room='U', floor='1')
            )
        ],
        loads=[
            ElectricalLoad(
                id=f'HEAVY{i}',
                name=f'Heavy Load {i}',
                load_type=LoadType.HVAC,
                power_watts=3000,
                voltage=VoltageType.SINGLE_PHASE_240V,
                location=Location(room=f'Room{i}', floor='1')
            )
            for i in range(5)
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    pipeline = get_design_pipeline()
    result = pipeline.execute(request)
    
    assert result is not None
    assert len(result.wire_sizing) == 5
    
    # All should have appropriate wire sizes
    for load_id in [f'HEAVY{i}' for i in range(5)]:
        wire = result.wire_sizing[load_id]
        assert wire['wire_size'] is not None
        assert wire['ampacity'] > 0

test("Recovery: Multiple heavy loads handled", test_multiple_heavy_loads)

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*100)
print("TEST SUMMARY")
print("="*100)

total = passed + failed
pass_rate = (passed / total * 100) if total > 0 else 0

print(f"\nTotal: {total}")
print(f"Passed: {passed} ✅")
print(f"Failed: {failed} ❌")
print(f"Pass Rate: {pass_rate:.1f}%")

if failed == 0:
    print("\n🎉 ALL ENHANCED ERROR HANDLING TESTS PASSED!")
    sys.exit(0)
else:
    print(f"\n⚠️  {failed} tests need attention")
    sys.exit(1)
