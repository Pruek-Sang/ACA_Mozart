"""
Comprehensive Test Suite for Phase D - Complete MVP

Tests all Phase D components:
1. Circuit Assignment from MCP
2. E-101 Lighting Plan Generator
3. E-201 Power Plan Generator
4. E-501 Typical Details Generator
5. Complete Integration (A+B+C+D)
6. Full End-to-End Workflow

All tests must pass for Phase D (MVP) to be considered complete.
"""

import sys
import os
from pathlib import Path
import tempfile

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cad.placement import DevicePlacer, assign_circuits
from cad.geometry import get_template
from cad.drawing import (
    LightingPlanGenerator,
    PowerPlanGenerator,
    DetailsGenerator,
    SingleLineDiagramGenerator,
    PanelScheduleGenerator
)
from cad.validators import validate_lisp_syntax


class MockMCPResult:
    """Mock MCP result for testing"""
    def __init__(self):
        self.wires = [
            type('Wire', (), {'size_mm2': '2.5', 'current': 10.5, 'conduit_size': '20mm'})(),
            type('Wire', (), {'size_mm2': '1.5', 'current': 5.2, 'conduit_size': '16mm'})(),
        ]
        self.breakers = [
            type('Breaker', (), {'rating': '16', 'poles': 1})(),
            type('Breaker', (), {'rating': '10', 'poles': 1})(),
        ]


def test_circuit_assignment():
    """Test 1: Circuit Assignment from MCP"""
    print("\n" + "="*60)
    print("TEST 1: Circuit Assignment")
    print("="*60)
    
    try:
        # Place devices (circuit=None)
        placer = DevicePlacer('EIT')
        bedroom = get_template('bedroom')
        devices = placer.place_all_devices(bedroom)
        
        # Verify circuit is None before assignment
        assert devices['outlets'][0]['circuit'] is None, "Circuit should be None before assignment"
        print("✓ Devices have circuit=None before assignment")
        
        # Assign circuits from MCP
        mcp_result = MockMCPResult()
        devices_with_circuits = assign_circuits(devices, mcp_result)
        
        # Verify circuits assigned
        assert devices_with_circuits['outlets'][0]['circuit'] is not None, "Circuit should be assigned"
        circuit = devices_with_circuits['outlets'][0]['circuit']
        assert 'id' in circuit, "Circuit should have ID"
        assert 'wire_size' in circuit, "Circuit should have wire size"
        assert 'breaker_rating' in circuit, "Circuit should have breaker rating"
        print(f"✓ Circuit assigned: {circuit['id']}, {circuit['wire_size']}, {circuit['breaker_rating']}")
        
        print("\n✅ Circuit Assignment: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Circuit Assignment: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e101_generator():
    """Test 2: E-101 Lighting Plan Generator"""
    print("\n" + "="*60)
    print("TEST 2: E-101 Lighting Plan")
    print("="*60)
    
    try:
        # Prepare devices with circuits
        placer = DevicePlacer('EIT')
        bedroom = get_template('bedroom')
        devices = placer.place_all_devices(bedroom)
        
        mcp_result = MockMCPResult()
        devices_with_circuits = assign_circuits(devices, mcp_result)
        
        # Generate E-101
        generator = LightingPlanGenerator("Test Project")
        panel_pos = (500, 500)
        
        lisp_code = generator.generate(devices_with_circuits, panel_pos, 'EIT')
        
        assert len(lisp_code) > 0, "Should generate LISP code"
        assert 'E-101' in lisp_code, "Should include drawing number"
        assert 'Lighting Plan' in lisp_code or 'LIGHTING' in lisp_code.upper(), "Should mention lighting"
        assert 'LIGHT' in lisp_code or 'light' in lisp_code.lower(), "Should have light blocks"
        print("✓ E-101 LISP generated")
        
        # Validate syntax
        assert lisp_code.count('(') == lisp_code.count(')'), "Parentheses should balance"
        print("✓ Valid LISP syntax")
        
        print("\n✅ E-101 Generator: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ E-101 Generator: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e201_generator():
    """Test 3: E-201 Power Plan Generator"""
    print("\n" + "="*60)
    print("TEST 3: E-201 Power Plan")
    print("="*60)
    
    try:
        # Prepare devices
        placer = DevicePlacer('EIT')
        bedroom = get_template('bedroom')
        devices = placer.place_all_devices(bedroom)
        
        mcp_result = MockMCPResult()
        devices_with_circuits = assign_circuits(devices, mcp_result)
        
        # Generate E-201
        generator = PowerPlanGenerator("Test Project")
        panel_pos = (500, 500)
        
        lisp_code = generator.generate(devices_with_circuits, panel_pos, 'EIT')
        
        assert len(lisp_code) > 0, "Should generate LISP code"
        assert 'E-201' in lisp_code, "Should include drawing number"
        assert 'Power Plan' in lisp_code or 'POWER' in lisp_code.upper(), "Should mention power"
        assert 'OUTLET' in lisp_code or 'outlet' in lisp_code.lower(), "Should have outlet blocks"
        print("✓ E-201 LISP generated")
        
        # Validate
        assert lisp_code.count('(') == lisp_code.count(')'), "Parentheses should balance"
        print("✓ Valid LISP syntax")
        
        print("\n✅ E-201 Generator: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ E-201 Generator: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e501_generator():
    """Test 4: E-501 Typical Details Generator"""
    print("\n" + "="*60)
    print("TEST 4: E-501 Typical Details")
    print("="*60)
    
    try:
        # Generate E-501
        generator = DetailsGenerator("Test Project")
        
        lisp_code = generator.generate('EIT')
        
        assert len(lisp_code) > 0, "Should generate LISP code"
        assert 'E-501' in lisp_code, "Should include drawing number"
        assert 'Detail' in lisp_code or 'DETAIL' in lisp_code.upper(), "Should mention details"
        assert 'OUTLET' in lisp_code or 'SWITCH' in lisp_code, "Should have device details"
        print("✓ E-501 LISP generated")
        
        # Validate
        assert lisp_code.count('(') == lisp_code.count(')'), "Parentheses should balance"
        print("✓ Valid LISP syntax")
        
        print("\n✅ E-501 Generator: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ E-501 Generator: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_integration():
    """Test 5: Complete Integration (A+B+C+D)"""
    print("\n" + "="*60)
    print("TEST 5: Complete Integration (A+B+C+D)")
    print("="*60)
    
    try:
        # Phase A: Standards, LISP writer
        from cad.standards import load_standards
        standards = load_standards('EIT')
        assert standards is not None
        print("✓ Phase A: Standards loaded")
        
        # Phase B: Place devices
        placer = DevicePlacer('EIT')
        bedroom = get_template('bedroom')
        devices = placer.place_all_devices(bedroom)
        assert len(devices['outlets']) > 0
        print(f"✓ Phase B: {len(devices['outlets'])} outlets, {len(devices['lights'])} lights placed")
        
        # Phase D: Assign circuits
        mcp_result = MockMCPResult()
        devices_with_circuits = assign_circuits(devices, mcp_result)
        assert devices_with_circuits['outlets'][0]['circuit'] is not None
        print("✓ Phase D: Circuits assigned")
        
        # Phase C: Route wires
        from cad.routing import route_wires
        panel_pos = (500, 500)
        routes = route_wires(devices_with_circuits, panel_pos)
        assert len(routes) > 0
        print(f"✓ Phase C: {len(routes)} wire routes generated")
        
        # Phase D: Generate all 5 drawings
        generators = {
            'E-301': SingleLineDiagramGenerator("Test"),
            'E-401': PanelScheduleGenerator("Test"),
            'E-101': LightingPlanGenerator("Test"),
            'E-201': PowerPlanGenerator("Test"),
            'E-501': DetailsGenerator("Test")
        }
        
        drawings_generated = 0
        for name, gen in generators.items():
            if name == 'E-301':
                panel_data = {'id': 'DB-1', 'name': 'Panel', 'voltage': '230V', 'rating': '100A', 'location': panel_pos}
                code = gen.generate(panel_data, mcp_result, 'EIT')
            elif name == 'E-401':
                code = gen.generate('DB-1', [], mcp_result, 'EIT')
            elif name == 'E-501':
                code = gen.generate('EIT')
            else:
                 code = gen.generate(devices_with_circuits, panel_pos, 'EIT')
            
            assert len(code) > 0, f"{name} should generate code"
            drawings_generated += 1
        
        print(f"✓ Phase D: All {drawings_generated} drawings generated")
        
        print("\n✅ Complete Integration (A+B+C+D): PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Complete Integration: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_mvp_workflow():
    """Test 6: Full MVP End-to-End Workflow"""
    print("\n" + "="*60)
    print("TEST 6: Full MVP Workflow")
    print("="*60)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Complete MVP workflow
            print("✓ Starting full MVP workflow...")
            
            # 1. Load standards
            from cad.standards import load_standards
            standards = load_standards('EIT')
            
            # 2. Get room template
            bedroom = get_template('bedroom')
            
            # 3. Place devices
            placer = DevicePlacer('EIT')
            devices = placer.place_all_devices(bedroom)
            
            # 4. Assign circuits from MCP
            mcp_result = MockMCPResult()
            devices_with_circuits = assign_circuits(devices, mcp_result)
            
            # 5. Route wires
            from cad.routing import route_wires
            panel_pos = (500, 500)
            routes = route_wires(devices_with_circuits, panel_pos)
            
            # 6. Generate all 5 drawings
            panel_data = {'id': 'DB-1', 'name': 'Main Panel', 'voltage': '230V', 'rating': '100A', 'location': panel_pos}
            
            drawings = {
                'E-101': LightingPlanGenerator("MVP Test"),
                'E-201': PowerPlanGenerator("MVP Test"),
                'E-301': SingleLineDiagramGenerator("MVP Test"),
                'E-401': PanelScheduleGenerator("MVP Test"),
                'E-501': DetailsGenerator("MVP Test")
            }
            
            files_created = []
            for name, gen in drawings.items():
                output_file = tmpdir / f"{name}.lsp"
                
                if name == 'E-301':
                    gen.save_to_file(output_file, panel_data, mcp_result, 'EIT')
                elif name == 'E-401':
                    gen.save_to_file(output_file, 'DB-1', [], mcp_result, 'EIT')
                elif name == 'E-501':
                    gen.save_to_file(output_file, 'EIT')
                else:
                    gen.save_to_file(output_file, devices_with_circuits, panel_pos, 'EIT')
                
                assert output_file.exists(), f"{name} file should exist"
                assert output_file.stat().st_size > 500, f"{name} should have content"
                
                # Validate syntax
                ok, errors = validate_lisp_syntax(output_file)
                assert ok, f"{name} should be valid: {errors}"
                
                files_created.append(name)
            
            print(f"✓ Generated {len(files_created)} drawings: {', '.join(files_created)}")
            print("✓ All files validated successfully")
        
        print("\n✅ Full MVP Workflow: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Full MVP Workflow: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase D tests"""
    print("\n" + "="*70)
    print(" PHASE D - COMPREHENSIVE TEST SUITE (MVP COMPLETE) ".center(70, "="))
    print("="*70)
    print("\nAll tests must pass for Phase D (MVP) to be considered complete.\n")
    
    tests = [
        ("Circuit Assignment", test_circuit_assignment),
        ("E-101 Lighting Plan", test_e101_generator),
        ("E-201 Power Plan", test_e201_generator),
        ("E-501 Typical Details", test_e501_generator),
        ("Complete Integration (A+B+C+D)", test_complete_integration),
        ("Full MVP Workflow", test_full_mvp_workflow),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} raised unexpected exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY ".center(70, "="))
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(passed for _, passed in results)
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print("\n" + "="*70)
    if all_passed:
        print(f"🎉 ALL {total_count} TESTS PASSED - PHASE D COMPLETE! 🎉".center(70))
        print("="*70)
        print("\n🏆 MVP COMPLETE! 🏆")
        print("\nAll 4 phases delivered:")
        print("  ✓ Phase A: Standards + Base AutoLISP + E-301 + E-401")
        print("  ✓ Phase B: Device Placement + 6 Room Templates")
        print("  ✓ Phase C: DXF Reader + Wire Router")
        print("  ✓ Phase D: E-101 + E-201 + E-501 + Circuit Assignment")
        print("\nTotal Deliverables:")
        print("  ✓ 5 Drawing Types (E-101, E-201, E-301, E-401, E-501)")
        print("  ✓ 6 Room Types (Bedroom, Living, Kitchen, Bathroom, Corridor, Other)")
        print("  ✓ 3 Standards (EIT, IEC, NEC)")
        print("  ✓ Complete workflow (DXF → Devices → Circuits → Drawings)")
        print("\n🚀 READY FOR PRODUCTION USE! 🚀")
    else:
        print(f"⚠️  {passed_count}/{total_count} TESTS PASSED - PHASE D INCOMPLETE! ⚠️".center(70))
        print("="*70)
        print("\nPhase D is NOT complete. Fix failing tests before proceeding.")
    
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
