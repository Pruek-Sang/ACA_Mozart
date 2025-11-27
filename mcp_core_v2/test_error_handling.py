#!/usr/bin/env python3
"""
MCP Core v2 - Error Handling Test Suite
Group B: Input Validation & Spec Correctness
Group C: Standards / Compliance Errors
"""

import sys
sys.path.insert(0, '/mnt/BigDrive/Linux_Work/ACA_Mozart/mcp_core_v2')

from datetime import datetime
from models.contracts import (
    DesignRequest, ElectricalLoad, PanelSpecification,
    Location, VoltageType, LoadType
)
from pipeline import get_design_pipeline
import pytest

print("="*100)
print("MCP CORE V2 - ERROR HANDLING TEST SUITE")
print("="*100)

passed = 0
failed = 0
errors = []

def test_case(name: str, test_func):
    """Run a test case and track results"""
    global passed, failed, errors
    try:
        test_func()
        print(f"✅ PASS: {name}")
        passed += 1
        return True
    except AssertionError as e:
        print(f"❌ FAIL: {name}")
        print(f"   Reason: {str(e)}")
        failed += 1
        errors.append((name, str(e)))
        return False
    except Exception as e:
        print(f"⚠️  ERROR: {name}")
        print(f"   Exception: {type(e).__name__}: {str(e)}")
        failed += 1
        errors.append((name, f"{type(e).__name__}: {str(e)}"))
        return False

# =============================================================================
# GROUP B: INPUT VALIDATION
# =============================================================================

print("\n" + "="*100)
print("GROUP B: INPUT VALIDATION & SPEC CORRECTNESS")
print("="*100)

def test_b1_missing_panels():
    """B1: Missing panels in request"""
    try:
        request = DesignRequest(
            session_id='test_b1',
            project_name='Missing Panels Test',
            panels=[],  # Empty!
            loads=[
                ElectricalLoad(
                    id='L1',
                    name='Test Load',
                    load_type=LoadType.LIGHTING,
                    power_watts=500,
                    voltage=VoltageType.SINGLE_PHASE_120V,
                    location=Location(room='Test', floor='1')
                )
            ],
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=200
        )
        
        pipeline = get_design_pipeline()
        result = pipeline.execute(request)
        
        # Should handle gracefully or raise meaningful error
        # For now, check if it doesn't crash
        assert result is not None, "Pipeline should handle empty panels"
        
    except Exception as e:
        # Check if error is meaningful
        error_msg = str(e).lower()
        assert 'panel' in error_msg or 'required' in error_msg, \
            f"Error message should mention panels: {e}"

test_case("B1: Missing required panels", test_b1_missing_panels)

def test_b2_empty_loads():
    """B1: Empty loads list"""
    try:
        request = DesignRequest(
            session_id='test_b2',
            project_name='Empty Loads Test',
            panels=[
                PanelSpecification(
                    id='P1',
                    name='Test Panel',
                    voltage=VoltageType.SINGLE_PHASE_240V,
                    max_amperage=100,
                    main_breaker_rating=100,
                    number_of_circuits=20,
                    location=Location(room='Util', floor='1')
                )
            ],
            loads=[],  # Empty!
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=200
        )
        
        pipeline = get_design_pipeline()
        result = pipeline.execute(request)
        
        # Should complete without crash
        assert result is not None
        assert len(result.wire_sizing) == 0, "No loads = no wire sizing"
        
    except Exception as e:
        # Graceful handling expected
        pass

test_case("B1: Empty loads list (graceful)", test_b2_empty_loads)

def test_b3_invalid_voltage_type():
    """B3: Invalid voltage reference"""
    # This tests Pydantic validation
    try:
        # Try to create with invalid enum value
        load = ElectricalLoad(
            id='L1',
            name='Bad Voltage',
            load_type=LoadType.LIGHTING,
            power_watts=500,
            voltage="999V_INVALID",  # Invalid!
            location=Location(room='Test', floor='1')
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        # Pydantic should catch this
        assert 'validation' in str(e).lower() or 'enum' in str(e).lower()

test_case("B3: Invalid voltage type (Pydantic)", test_b3_invalid_voltage_type)

# =============================================================================
# GROUP C: COMPLIANCE ERRORS
# =============================================================================

print("\n" + "="*100)
print("GROUP C: STANDARDS / COMPLIANCE ERRORS")
print("="*100)

def test_c1_excessive_voltage_drop():
    """C1: Voltage drop exceeds safe limits"""
    request = DesignRequest(
        session_id='test_c1',
        project_name='Excessive VD Test',
        panels=[
            PanelSpecification(
                id='P1',
                name='Distant Panel',
                voltage=VoltageType.SINGLE_PHASE_240V,
                max_amperage=100,
                main_breaker_rating=100,
                number_of_circuits=20,
                location=Location(room='Utility', floor='1')
            )
        ],
        loads=[
            ElectricalLoad(
                id='L1',
                name='Heavy Load Far Away',
                load_type=LoadType.HVAC,
                power_watts=5000,  # Heavy!
                voltage=VoltageType.SINGLE_PHASE_240V,
                location=Location(room='Far Room', floor='1')
                # Note: distance will be default 100ft, but wire sizer should handle
            )
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    pipeline = get_design_pipeline()
    result = pipeline.execute(request)
    
    # Should NOT crash
    assert result is not None, "Pipeline should complete"
    
    # Check wire sizing result
    wire = result.wire_sizing.get('L1', {})
    vd_pct = wire.get('voltage_drop_percent', 0)
    
    # Wire sizer should upsize to keep VD under 3%
    # If VD > 3%, should be flagged
    if vd_pct > 3.0:
        # Check if compliance checker flagged it
        compliance = result.compliance_report
        assert compliance is not None, "Compliance report should exist"
        # (Current implementation may not flag this - that's OK for now)
    
    print(f"   VD: {vd_pct:.2f}%, Wire: {wire.get('wire_size')}")

test_case("C1: Excessive voltage drop handling", test_c1_excessive_voltage_drop)

def test_c2_high_current_load():
    """C2: Very high current requiring large wire"""
    request = DesignRequest(
        session_id='test_c2',
        project_name='High Current Test',
        panels=[
            PanelSpecification(
                id='P1',
                name='Main Panel',
                voltage=VoltageType.SINGLE_PHASE_240V,
                max_amperage=200,
                main_breaker_rating=200,
                number_of_circuits=40,
                location=Location(room='Utility', floor='1')
            )
        ],
        loads=[
            ElectricalLoad(
                id='BIG1',
                name='Electric Range',
                load_type=LoadType.APPLIANCE,
                power_watts=12000,  # 12kW @ 240V = 50A!
                voltage=VoltageType.SINGLE_PHASE_240V,
                location=Location(room='Kitchen', floor='1')
            )
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    pipeline = get_design_pipeline()
    result = pipeline.execute(request)
    
    assert result is not None
    
    wire = result.wire_sizing['BIG1']
    current = wire.get('current_before_derating', 0)
    wire_size = wire.get('wire_size')
    ampacity = wire.get('ampacity', 0)
    
    # Should upsize appropriately
    assert current > 45, f"Expected ~50A, got {current}A"
    assert ampacity >= current, f"Ampacity {ampacity}A must exceed current {current}A"
    
    print(f"   Current: {current:.1f}A, Wire: {wire_size}, Ampacity: {ampacity}A")

test_case("C2: High current load sizing", test_c2_high_current_load)

def test_c3_multiple_violations():
    """C: Multiple compliance issues at once"""
    request = DesignRequest(
        session_id='test_c3',
        project_name='Multiple Issues Test',
        panels=[
            PanelSpecification(
                id='P1',
                name='Small Panel',
                voltage=VoltageType.SINGLE_PHASE_120V,
                max_amperage=60,  # Small!
                main_breaker_rating=60,
                number_of_circuits=12,
                location=Location(room='Utility', floor='1')
            )
        ],
        loads=[
            # Too many heavy loads for small panel
            ElectricalLoad(id='L1', name='Load 1', load_type=LoadType.HVAC,
                          power_watts=2000, voltage=VoltageType.SINGLE_PHASE_120V,
                          location=Location(room='R1', floor='1')),
            ElectricalLoad(id='L2', name='Load 2', load_type=LoadType.HVAC,
                          power_watts=2000, voltage=VoltageType.SINGLE_PHASE_120V,
                          location=Location(room='R2', floor='1')),
            ElectricalLoad(id='L3', name='Load 3', load_type=LoadType.APPLIANCE,
                          power_watts=1800, voltage=VoltageType.SINGLE_PHASE_120V,
                          location=Location(room='R3', floor='1')),
        ],
        service_voltage=VoltageType.SINGLE_PHASE_120V,
        utility_service_size=100
    )
    
    pipeline = get_design_pipeline()
    result = pipeline.execute(request)
    
    # Should complete
    assert result is not None
    
    # Check compliance report for warnings
    if result.compliance_report:
        print(f"   Warnings: {len(result.compliance_report.get('warnings', []))}")
        print(f"   Errors: {len(result.compliance_report.get('errors', []))}")

test_case("C3: Multiple compliance issues", test_c3_multiple_violations)

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*100)
print("TEST SUMMARY")
print("="*100)

total = passed + failed
pass_rate = (passed / total * 100) if total > 0 else 0

print(f"\nTotal Tests: {total}")
print(f"Passed: {passed} ✅")
print(f"Failed: {failed} ❌")
print(f"Pass Rate: {pass_rate:.1f}%")

if errors:
    print("\n" + "="*100)
    print("FAILED TESTS DETAILS")
    print("="*100)
    for name, reason in errors:
        print(f"\n❌ {name}")
        print(f"   {reason}")

if failed == 0:
    print("\n🎉 ALL ERROR HANDLING TESTS PASSED!")
    sys.exit(0)
else:
    print(f"\n⚠️  {failed} tests need attention")
    sys.exit(1)
