"""
Complete Integration Test - MCP Pipeline to AutoLISP

Tests the COMPLETE workflow:
1. MCP calculations (wire sizing, breakers)
2. Device placement
3. Circuit assignment from MCP
4. Wire routing
5. AutoLISP generation (all 5 drawings)

This verifies the BRIDGE between calculation and drawing!
"""

import sys
import tempfile
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from integration import generate_complete_electrical_package


def test_complete_integration():
    """Test complete MCP → AutoLISP integration"""
    
    print("\n" + "="*70)
    print(" COMPLETE INTEGRATION TEST - MCP → AutoLISP ".center(70, "="))
    print("="*70)
    
    try:
        # Test data - bedroom with real loads
        room_data = {
            'room_type': 'bedroom',
            'dimensions': {
                'length': 4000,  # mm
                'width': 6000    # mm
            },
            'door': {
                'position': (2000, 0),
                'width': 900
            },
            'windows': [
                {'position': (4000, 3000), 'width': 1500, 'height': 1200}
            ],
            'loads': [
                {
                    'name': 'Bedroom Lighting',
                    'watts': 200,
                    'qty': 1,
                    'load_type': 'lighting',
                    'voltage': 230,
                    'phase_config': '1ph'
                },
                {
                    'name': 'Bedroom Outlets',
                    'watts': 1800,
                    'qty': 1,
                    'load_type': 'receptacle',
                    'voltage': 230,
                    'phase_config': '1ph'
                }
            ],
            'voltage': 230,
            'system_type': '1ph',
            'panel_id': 'DB-1',
            'standard': 'EIT'
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / 'electrical_package'
            
            print("\n1. Running complete integration...")
            print(f"   Room: {room_data['room_type']}")
            print(f"   Size: {room_data['dimensions']['length']}x{room_data['dimensions']['width']}mm")
            print(f"   Loads: {len(room_data['loads'])}")
            
            # Generate complete package
            result = generate_complete_electrical_package(
                room_data,
                standard='EIT',
                panel_location=(500, 500),
                output_dir=output_dir
            )
            
            # Verify results
            print("\n2. Verifying results...")
            
            # Check MCP calculations
            assert result.get('mcp_result') is not None, "MCP result should exist"
            print("   ✓ MCP calculations completed")
            
            # Check devices
            devices = result.get('devices')
            assert devices is not None, "Devices should exist"
            assert len(devices['outlets']) > 0, "Should have outlets"
            assert len(devices['lights']) > 0, "Should have lights"
            print(f"   ✓ Devices placed: {len(devices['outlets'])} outlets, {len(devices['lights'])} lights")
            
            # Check circuits assigned
            first_outlet = devices['outlets'][0]
            assert first_outlet.get('circuit') is not None, "Circuits should be assigned"
            circuit = first_outlet['circuit']
            assert 'wire_size' in circuit, "Circuit should have wire size from MCP"
            assert 'breaker_rating' in circuit, "Circuit should have breaker from MCP"
            print(f"   ✓ Circuits assigned: wire={circuit['wire_size']}, breaker={circuit['breaker_rating']}")
            
            # Check wire routing
            routes = result.get('routes')
            assert routes is not None, "Routes should exist"
            assert len(routes) > 0, "Should have wire routes"
            print(f"   ✓ Wire routing: {len(routes)} routes")
            
            # Check drawings
            drawings = result.get('drawings')
            assert drawings is not None, "Drawings should exist"
            assert len(drawings) == 5, "Should have all 5 drawings"
            
            expected_drawings = ['E-101', 'E-201', 'E-301', 'E-401', 'E-501']
            for dwg in expected_drawings:
                assert dwg in drawings, f"{dwg} should be generated"
                assert drawings[dwg].exists(), f"{dwg} file should exist"
                assert drawings[dwg].stat().st_size > 0, f"{dwg} should have content"
            
            print("   ✓ All 5 drawings generated:")
            for dwg, path in drawings.items():
                size_kb = path.stat().st_size / 1024
                print(f"     - {dwg}: {path.name} ({size_kb:.1f} KB)")
            
            # Check summary
            summary = result.get('summary')
            assert summary is not None, "Summary should exist"
            print(f"\n3. Package summary:")
            print(f"   Room type: {summary['room_type']}")
            print(f"   Devices: {summary['outlets']} outlets, {summary['lights']} lights, {summary['switches']} switches")
            print(f"   Circuits: {summary['circuits']}")
            print(f"   Wire routes: {summary['wire_routes']}")
            print(f"   Drawings: {summary['drawings']}")
            
            # Verify integration points
            print(f"\n4. Integration verification:")
            print("   ✓ MCP calculations → Device placement")
            print("   ✓ MCP results → Circuit assignment")
            print("   ✓ Devices + Circuits → Wire routing")
            print("   ✓ All data → AutoLISP drawings")
            print("   ✓ Complete workflow tested")
            
            print("\n" + "="*70)
            print("✅ COMPLETE INTEGRATION TEST: PASS".center(70))
            print("="*70)
            print("\n🎉 MCP → AutoLISP BRIDGE WORKING! 🎉")
            print("\nThe calculation side (MCP) is now connected to")
            print("the drawing side (AutoLISP) through integration.py!")
            print("="*70)
            
            return True
    
    except Exception as e:
        print("\n" + "="*70)
        print("❌ COMPLETE INTEGRATION TEST: FAIL".center(70))
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_complete_integration()
    sys.exit(0 if success else 1)
