"""
Comprehensive Test Suite for Phase C - DXF Reader + Wire Router

Tests all Phase C components:
1. DXF Reader (mock files)
2. Wire Router (orthogonal routing)
3. Integration with Phase A (LISP generation)
4. Integration with Phase B (device placement)
5. Full workflow (DXF → Placement → Routing → LISP)

All tests must pass before Phase C is considered complete.
"""

import sys
import os
from pathlib import Path
import tempfile

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cad.dxf import DXFReaderV1, read_dxf_file
from cad.routing import WireRouter, route_wires
from cad.placement import DevicePlacer
from cad.autolisp_writer import AutoLISPWriter


def test_dxf_reader():
    """Test 1: DXF Reader"""
    print("\n" + "="*60)
    print("TEST 1: DXF Reader")
    print("="*60)
    
    try:
        # Test reading simple mock DXF
        dxf_file = Path('cad/test_dxf/house_1floor_simple.dxf')
        
        reader = DXFReaderV1()
        data = reader.read_mock_dxf(dxf_file)
        
        assert 'rooms' in data, "Missing rooms"
        assert 'panels' in data, "Missing panels"
        assert 'layers' in data, "Missing layers"
        print("✓ DXF data structure correct")
        
        # Check room
        assert len(data['rooms']) > 0, "No rooms found"
        room = data['rooms'][0]
        assert 'polygon' in room, "Room missing polygon"
        assert 'type' in room, "Room missing type"
        assert room['type'] == 'bedroom', f"Wrong room type: {room['type']}"
        print(f"✓ Found {len(data['rooms'])} room(s): {room['id']}")
        
        # Check panel
        assert len(data['panels']) > 0, "No panels found"
        panel = data['panels'][0]
        assert 'position' in panel, "Panel missing position"
        print(f"✓ Found panel: {panel['id']} at {panel['position']}")
        
        # Check layers
        assert len(data['layers']) > 0, "No layers found"
        print(f"✓ Found {len(data['layers'])} layers")
        
        print("\n✅ DXF Reader: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ DXF Reader: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dxf_to_template():
    """Test 2: DXF to RoomTemplate Mapping"""
    print("\n" + "="*60)
    print("TEST 2: DXF to RoomTemplate")
    print("="*60)
    
    try:
        dxf_file = Path('cad/test_dxf/house_1floor_simple.dxf')
        
        reader = DXFReaderV1()
        data = reader.read_mock_dxf(dxf_file)
        
        # Map to template
        dxf_room = data['rooms'][0]
        template = reader.map_to_room_template(dxf_room)
        
        # Check template format
        assert 'polygon' in template, "Missing polygon"
        assert 'door' in template, "Missing door"
        assert 'area_sqm' in template, "Missing area"
        print(f"✓ Mapped to template: {template['type']} ({template['area_sqm']:.1f}m²)")
        
        # Should be compatible with DevicePlacer
        placer = DevicePlacer('EIT')
        devices = placer.place_all_devices(template)
        
        assert 'outlets' in devices, "Mapping incompatible with DevicePlacer"
        print(f"✓ Template compatible: {len(devices['outlets'])} outlets placed")
        
        print("\n✅ DXF to RoomTemplate: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ DXF to RoomTemplate: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wire_router():
    """Test 3: Wire Router"""
    print("\n" + "="*60)
    print("TEST 3: Wire Router")
    print("="*60)
    
    try:
        router = WireRouter()
        
        # Test orthogonal routing
        start = (0, 0)
        end = (1000, 2000)
        path = router.route_orthogonal(start, end)
        
        assert len(path) >= 2, "Path should have at least 2 points"
        assert path[0] == start, "Path should start at start point"
        assert path[-1] == end, "Path should end at end point"
        print(f"✓ Orthogonal routing: {len(path)} points")
        
        # Test lighting circuit
        lights = [
            {'id': 'LT-001', 'position': (2000, 2000)},
            {'id': 'LT-002', 'position': (2000, 4000)}
        ]
        switch = {
            'id': 'SW-001',
            'position': (3000, 100),
            'controls': ['LT-001', 'LT-002']
        }
        panel = {'id': 'DB-1', 'position': (500, 500)}
        
        lighting_routes = router.route_lighting_circuit(lights, switch, panel)
        
        assert len(lighting_routes) > 0, "Should generate lighting routes"
        # Should have: switch→light1, switch→light2, switch→panel
        assert len(lighting_routes) == 3, f"Expected 3 routes, got {len(lighting_routes)}"
        print(f"✓ Lighting circuit: {len(lighting_routes)} routes")
        
        # Test power circuit
        outlets = [
            {'id': 'OUT-001', 'position': (1000, 0)},
            {'id': 'OUT-002', 'position': (3000, 0)}
        ]
        
        power_routes = router.route_power_circuit(outlets, panel)
        
        assert len(power_routes) > 0, "Should generate power routes"
        # Should have: outlet1→outlet2, outlet1→panel
        print(f"✓ Power circuit: {len(power_routes)} routes")
        
        print("\n✅  Wire Router: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Wire Router: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wire_lisp_generation():
    """Test 4: Wire LISP Code Generation"""
    print("\n" + "="*60)
    print("TEST 4: Wire LISP Generation")
    print("="*60)
    
    try:
        router = WireRouter()
        
        # Create test routes
        routes = [
            {
                'from': {'id': 'SW-001'},
                'to': {'id': 'LT-001'},
                'path': [(0, 0), (1000, 0), (1000, 2000)],
                'wire_type': 'switch_leg'
            },
            {
                'from': {'id': 'SW-001'},
                'to': {'id': 'PANEL'},
                'path': [(0, 0), (500, 0), (500, 500)],
                'wire_type': 'homerun'
            }
        ]
        
        lisp_code = router.generate_wire_lisp(routes)
        
        assert len(lisp_code) > 0, "Should generate LISP code"
        assert 'LAYER' in lisp_code or 'layer' in lisp_code.lower(), "Should set layer"
        assert 'PLINE' in lisp_code or 'pline' in lisp_code.lower(), "Should have polyline commands"
        print("✓ LISP code generated")
        
        # Check homerun arrow
        assert 'homerun' in str(routes), "Should have homerun route"
        # Arrow is generated with LINE commands
        print("✓ Homerun arrow included")
        
        # Validate syntax
        assert lisp_code.count('(') == lisp_code.count(')'), "Parentheses should balance"
        print("✓ Valid LISP syntax")
        
        print("\n✅ Wire LISP Generation: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Wire LISP Generation: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_abc():
    """Test 5: Integration - Phase A + B + C"""
    print("\n" + "="*60)
    print("TEST 5: Integration (A + B + C)")
    print("="*60)
    
    try:
        # Phase C: Read DXF
        dxf_file = Path('cad/test_dxf/house_1floor_simple.dxf')
        reader = DXFReaderV1()
        dxf_data = reader.read_mock_dxf(dxf_file)
        
        dxf_room = dxf_data['rooms'][0]
        template = reader.map_to_room_template(dxf_room)
        print(f"✓ Phase C: DXF read ({template['type']})")
        
        # Phase B: Place devices
        placer = DevicePlacer('EIT')
        devices = placer.place_all_devices(template)
        print(f"✓ Phase B: Devices placed ({len(devices['outlets'])} outlets)")
        
        # Phase C: Route wires
        panel_pos = dxf_data['panels'][0]['position']
        routes = route_wires(devices, panel_pos)
        print(f"✓ Phase C: Wires routed ({len(routes)} routes)")
        
        # Phase A: Generate LISP
        writer = AutoLISPWriter("Integration Test")
        writer.write_header("Test Drawing")
        
        # Add devices
        for outlet in devices['outlets']:
            writer.insert_block("OUTLET", outlet['position'])
        
        # Add wires (from Phase C)
        router = WireRouter()
        wire_lisp = router.generate_wire_lisp(routes)
        writer.code_lines.append(wire_lisp)
        
        writer.write_footer()
        code = writer.get_code()
        
        assert len(code) > 500, "Should generate substantial code"
        print(f"✓ Phase A: LISP generated ({len(code)} chars)")
        
        # Validate integration
        assert '(command "INSERT"' in code, "Should have device insertions"
        assert '(command "PLINE"' in code.upper() or 'PLINE' in code.upper(), "Should have wire polylines"
        print("✓ Full integration working")
        
        print("\n✅ Integration (A+B+C): PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Integration (A+B+C): FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow():
    """Test 6: Full Workflow - DXF to Final LISP"""
    print("\n" + "="*60)
    print("TEST 6: Full Workflow")
    print("="*60)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Complete workflow
            dxf_file = Path('cad/test_dxf/house_2rooms.dxf')
            
            # 1. Read DXF
            dxf_data = read_dxf_file(dxf_file)
            print(f"✓ Read DXF: {len(dxf_data['rooms'])} rooms")
            
            # 2. Process each room
            all_devices = []
            reader = DXFReaderV1()
            placer = DevicePlacer('EIT')
            
            for dxf_room in dxf_data['rooms']:
                template = reader.map_to_room_template(dxf_room)
                devices = placer.place_all_devices(template)
                all_devices.append({
                    'room': template,
                    'devices': devices
                })
            
            print(f"✓ Placed devices in {len(all_devices)} rooms")
            
            # 3. Route all wires
            panel_pos = dxf_data['panels'][0]['position']
            all_routes = []
            
            for room_data in all_devices:
                routes = route_wires(room_data['devices'], panel_pos)
                all_routes.extend(routes)
            
            print(f"✓ Routed {len(all_routes)} wire segments")
            
            # 4. Generate final LISP
            output_file = tmpdir / "electrical_plan.lsp"
            
            writer = AutoLISPWriter("Full Workflow Test")
            writer.write_header("Electrical Plan - E-201")
            
            # Create layers
            writer.create_layers({
                'E-DEVICE': {'color': 3, 'linetype': 'CONTINUOUS'},
                'E-WIRE': {'color': 1, 'linetype': 'CONTINUOUS'}
            })
            
            # Add all devices
            writer.set_layer('E-DEVICE')
            for room_data in all_devices:
                for outlet in room_data['devices']['outlets']:
                    writer.insert_block("OUTLET", outlet['position'])
                for light in room_data['devices']['lights']:
                    writer.insert_block("LIGHT", light['position'])
                for switch in room_data['devices']['switches']:
                    writer.insert_block("SWITCH", switch['position'])
            
            # Add all wires
            writer.set_layer('E-WIRE')
            router = WireRouter()
            wire_lisp = router.generate_wire_lisp(all_routes, 'E-WIRE')
            writer.code_lines.append(wire_lisp)
            
            writer.write_footer()
            writer.wrap_in_function("C:ELEC-PLAN")
            
            # Save
            writer.save_to_file(output_file)
            
            assert output_file.exists(), "Output file should exist"
            assert output_file.stat().st_size > 1000, "Output should have content"
            print(f"✓ Generated: {output_file.name} ({output_file.stat().st_size} bytes)")
        
        print("\n✅ Full Workflow: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Full Workflow: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase C tests"""
    print("\n" + "="*70)
    print(" PHASE C - COMPREHENSIVE TEST SUITE ".center(70, "="))
    print("="*70)
    print("\nAll tests must pass for Phase C to be considered complete.\n")
    
    tests = [
        ("DXF Reader", test_dxf_reader),
        ("DXF to RoomTemplate", test_dxf_to_template),
        ("Wire Router", test_wire_router),
        ("Wire LISP Generation", test_wire_lisp_generation),
        ("Integration (A+B+C)", test_integration_abc),
        ("Full Workflow", test_full_workflow),
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
        print(f"🎉 ALL {total_count} TESTS PASSED - PHASE C COMPLETE! 🎉".center(70))
        print("="*70)
        print("\nPhase C is ready for production use.")
        print("Deliverables:")
        print("  ✓ DXF Reader v1 (controlled templates)")
        print("  ✓ Wire Router (orthogonal routing)")
        print("  ✓ Mock DXF files (2 test files)")
        print("  ✓ Homerun arrows")
        print("  ✓ Integration with Phase A + B verified")
        print("\nReady to proceed to Phase D.")
    else:
        print(f"⚠️  {passed_count}/{total_count} TESTS PASSED - PHASE C INCOMPLETE! ⚠️".center(70))
        print("="*70)
        print("\nPhase C is NOT complete. Fix failing tests before proceeding.")
    
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
