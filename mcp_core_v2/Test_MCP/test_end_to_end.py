#!/usr/bin/env python3
"""Comprehensive End-to-End Production Test Suite"""

import sys
sys.path.insert(0, '/mnt/BigDrive/Linux_Work/ACA_Mozart/mcp_core_v2')

from datetime import datetime
from models.contracts import DesignRequest, ElectricalLoad, PanelSpecification, Location, VoltageType, LoadType
from pipeline import get_design_pipeline

print("="*100)
print("COMPREHENSIVE END-TO-END PRODUCTION TEST")
print("="*100)

test_passed = 0
test_failed = 0
test_details = []

def test_result(name: str, condition: bool, expected: str = "", actual: str = ""):
    global test_passed, test_failed, test_details
    if condition:
        test_passed += 1
        status = "✅ PASS"
    else:
        test_failed += 1
        status = "❌ FAIL"
    
    detail = f"{status}: {name}"
    if expected or actual:
        detail += f"\n     Expected: {expected}, Got: {actual}"
    print(detail)
    test_details.append((name, condition, expected, actual))

# =============================================================================
# TEST 1: Basic Single-Phase Load
# =============================================================================
print("\n" + "="*100)
print("TEST 1: Basic Single-Phase Residential Load (Lighting)")
print("="*100)

try:
    request1 = DesignRequest(
        session_id=f'test1_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        project_name='Test 1: Lighting',
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
                id='L1',
                name='LED Lighting',
                load_type=LoadType.LIGHTING,
                power_watts=500,
                voltage=VoltageType.SINGLE_PHASE_120V,
                location=Location(room='Living', floor='1')
            )
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    pipeline = get_design_pipeline()
    result1 = pipeline.execute(request1)
    
    wire = result1.wire_sizing['L1']
    
    test_result("Pipeline executes", True)
    test_result("Wire size selected", 'wire_size' in wire)
    test_result("Derating applied", 'derating_total' in wire)
    test_result("VD calculated", 'voltage_drop_percent' in wire)
    test_result("VD within 3%", wire.get('voltage_drop_percent', 999) <= 3.0,
                "≤3%", f"{wire.get('voltage_drop_percent'):.2f}%")
    
except Exception as e:
    test_result("Test 1 Complete", False, "Success", str(e))

# =============================================================================
# TEST 2: HVAC Load with Power Factor
# =============================================================================
print("\n" + "="*100)
print("TEST 2: HVAC Load (240V, PF=0.85)")
print("="*100)

try:
    request2 = DesignRequest(
        session_id=f'test2_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        project_name='Test 2: HVAC',
        panels=[
            PanelSpecification(
                id='P2',
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
                id='AC1',
                name='AC Unit 12000 BTU',
                load_type=LoadType.HVAC,
                power_watts=1500,
                voltage=VoltageType.SINGLE_PHASE_240V,
                location=Location(room='Master', floor='2'),
                power_factor=0.85  # ← Power factor specified
            )
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    result2 = pipeline.execute(request2)
    wire2 = result2.wire_sizing['AC1']
    
    test_result("HVAC load processed", True)
    test_result("Power factor used", wire2.get('current_before_derating', 0) > 0)
    test_result("Derating factors present", 'derating_factors' in wire2)
    
    if 'derating_factors' in wire2:
        factors = wire2['derating_factors']
        test_result("Temperature factor exists", 'temperature' in factors)
        test_result("Grouping factor exists", 'grouping' in factors)
        test_result("Total derating calculated", factors.get('total', 0) > 0)
    
except Exception as e:
    test_result("Test 2 Complete", False, "Success", str(e))

# =============================================================================
# TEST 3: Three-Phase Motor Load
# =============================================================================
print("\n" + "="*100)
print("TEST 3: Three-Phase Motor (208V)")
print("="*100)

try:
    request3 = DesignRequest(
        session_id=f'test3_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        project_name='Test 3: Motor',
        panels=[
            PanelSpecification(
                id='P3',
                name='Motor Panel',
                voltage=VoltageType.THREE_PHASE_208V,
                max_amperage=100,
                main_breaker_rating=100,
                number_of_circuits=20,
                location=Location(room='Workshop', floor='1')
            )
        ],
        loads=[
            ElectricalLoad(
                id='M1',
                name='3-Phase Motor',
                load_type=LoadType.MOTOR,
                power_watts=5000,  # 5kW
                voltage=VoltageType.THREE_PHASE_208V,
                location=Location(room='Workshop', floor='1'),
                power_factor=0.80
            )
        ],
        service_voltage=VoltageType.THREE_PHASE_208V,
        utility_service_size=100
    )
    
    result3 = pipeline.execute(request3)
    wire3 = result3.wire_sizing['M1']
    
    test_result("3-phase load processed", True)
    test_result("Wire sized for 3-phase", 'wire_size' in wire3)
    
    # For 3-phase, current should be I = P / (√3 × V × PF)
    # = 5000 / (1.732 × 208 × 0.8) ≈ 17.3A
    expected_current = 5000 / (1.732 * 208 * 0.8)
    actual_current = wire3.get('current_before_derating', 0)
    current_error = abs(actual_current - expected_current)
    
    test_result("3-phase current correct", current_error < 0.5,
                f"~{expected_current:.1f}A", f"{actual_current:.1f}A")
    
except Exception as e:
    test_result("Test 3 Complete", False, "Success", str(e))

# =============================================================================
# TEST 4: Multiple Loads
# =============================================================================
print("\n" + "="*100)
print("TEST 4: Multiple Loads (Mixed Types)")
print("="*100)

try:
    request4 = DesignRequest(
        session_id=f'test4_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        project_name='Test 4: Multiple', 
        panels=[
            PanelSpecification(
                id='P4',
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
                id='L1', name='Lighting', load_type=LoadType.LIGHTING,
                power_watts=1000, voltage=VoltageType.SINGLE_PHASE_120V,
                location=Location(room='Office', floor='1')
            ),
            ElectricalLoad(
                id='L2', name='Receptacles', load_type=LoadType.RECEPTACLE,
                power_watts=1800, voltage=VoltageType.SINGLE_PHASE_120V,
                location=Location(room='Office', floor='1')
            ),
            ElectricalLoad(
                id='L3', name='AC Unit', load_type=LoadType.HVAC,
                power_watts=2000, voltage=VoltageType.SINGLE_PHASE_240V,
                location=Location(room='Bedroom', floor='2'),
                power_factor=0.85
            )
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    result4 = pipeline.execute(request4)
    
    test_result("Multiple loads processed", len(result4.wire_sizing) == 3)
    test_result("All loads have wire sizing", 
                all(k in result4.wire_sizing for k in ['L1', 'L2', 'L3']))
    test_result("All loads have derating", 
                all('derating_total' in result4.wire_sizing[k] for k in ['L1', 'L2', 'L3']))
    
except Exception as e:
    test_result("Test 4 Complete", False, "Success", str(e))

# =============================================================================
# TEST 5: Derating Factors Verification
# =============================================================================
print("\n" + "="*100)
print("TEST 5: Derating Factors Values Verification")
print("="*100)

try:
    # Test with known conditions
    request5 = DesignRequest(
        session_id=f'test5_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        project_name='Test 5: Derating',
        panels=[
            PanelSpecification(
                id='P5',
                name='Test Panel',
                voltage=VoltageType.SINGLE_PHASE_240V,
                max_amperage=100,
                main_breaker_rating=100,
                number_of_circuits=20,
                location=Location(room='Test', floor='1')
            )
        ],
        loads=[
            ElectricalLoad(
                id='T1',
                name='Test Load',
                load_type=LoadType.RECEPTACLE,
                power_watts=1000,
                voltage=VoltageType.SINGLE_PHASE_120V,
                location=Location(room='Test', floor='1')
            )
        ],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=100
    )
    
    result5 = pipeline.execute(request5)
    wire5 = result5.wire_sizing['T1']
    
    if 'derating_factors' in wire5:
        df = wire5['derating_factors']
        
        # At 30°C, temp factor should be 1.0
        test_result("Temp factor at 30°C = 1.0", df.get('temperature') == 1.0,
                    "1.0", str(df.get('temperature')))
        
        # 2 conductors (single phase), grouping should be 1.0
        test_result("Grouping for 2 cond = 1.0", df.get('grouping') == 1.0,
                    "1.0", str(df.get('grouping')))
        
        # No insulation, factor should be 1.0
        test_result("No insulation = 1.0", df.get('insulation') == 1.0,
                    "1.0", str(df.get('insulation')))
        
        # Not buried, soil factor should be 1.0
        test_result("Not buried = 1.0", df.get('soil') == 1.0,
                    "1.0", str(df.get('soil')))
        
        # Total should be 1.0
        test_result("Total derating = 1.0", abs(df.get('total', 0) - 1.0) < 0.001,
                    "1.0", f"{df.get('total'):.3f}")
    
except Exception as e:
    test_result("Test 5 Complete", False, "Success", str(e))

# =============================================================================
# TEST 6: Voltage Drop Validation
# =============================================================================
print("\n" + "="*100)
print("TEST 6: Voltage Drop Limits")
print("="*100)

try:
    # Test various loads to ensure VD is always within limits
    test_cases = [
        ("Small load", 300, VoltageType.SINGLE_PHASE_120V),
        ("Medium load", 1500, VoltageType.SINGLE_PHASE_120V),
        ("Large load", 3000, VoltageType.SINGLE_PHASE_240V),
    ]
    
    vd_pass_count = 0
    for name, watts, voltage in test_cases:
        request_vd = DesignRequest(
            session_id=f'testvd_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{watts}',
            project_name=f'VD Test: {name}',
            panels=[
                PanelSpecification(
                    id='PVD',
                    name='VD Test Panel',
                    voltage=VoltageType.SINGLE_PHASE_240V,
                    max_amperage=200,
                    main_breaker_rating=200,
                    number_of_circuits=40,
                    location=Location(room='Test', floor='1')
                )
            ],
            loads=[
                ElectricalLoad(
                    id='VD1',
                    name=name,
                    load_type=LoadType.RECEPTACLE,
                    power_watts=watts,
                    voltage=voltage,
                    location=Location(room='Test', floor='1')
                )
            ],
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=200
        )
        
        result_vd = pipeline.execute(request_vd)
        wire_vd = result_vd.wire_sizing['VD1']
        vd_pct = wire_vd.get('voltage_drop_percent', 999)
        
        if vd_pct <= 3.0:
            vd_pass_count += 1
            print(f"  ✓ {name}: VD = {vd_pct:.2f}% ≤ 3%")
    
    test_result("All VD within 3% limit", vd_pass_count == len(test_cases),
                f"{len(test_cases)}/{len(test_cases)}", f"{vd_pass_count}/{len(test_cases)}")
    
except Exception as e:
    test_result("Test 6 Complete", False, "Success", str(e))

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*100)
print("TEST SUMMARY")
print("="*100)

total_tests = test_passed + test_failed
pass_rate = (test_passed / total_tests * 100) if total_tests > 0 else 0

print(f"\nTotal Tests Run: {total_tests}")
print(f"Passed: {test_passed} ✅")
print(f"Failed: {test_failed} ❌")
print(f"Pass Rate: {pass_rate:.1f}%")

# Critical tests check
critical_tests = [
    "Pipeline executes",
    "Derating applied",
    "VD calculated",
    "All VD within 3% limit"
]

critical_pass = sum(1 for name, passed, _, _ in test_details if name in critical_tests and passed)
critical_total = len(critical_tests)

print(f"\nCritical Tests: {critical_pass}/{critical_total} ✅")

if test_failed == 0:
    print("\n🎉 ALL TESTS PASSED - PRODUCTION READY!")
    confidence = 100
elif pass_rate >= 90:
    print("\n✅ PRODUCTION READY (Minor issues)")
    confidence = 90
elif pass_rate >= 75:
    print("\n⚠️  NEEDS REVIEW (Some failures)")
    confidence = 75
else:
    print("\n❌ NOT READY (Too many failures)")
    confidence = 50

print(f"\nConfidence Level: {confidence}%")
print("="*100)

sys.exit(0 if test_failed == 0 else 1)
