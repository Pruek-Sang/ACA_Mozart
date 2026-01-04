
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.display.compute import compute_display_data

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_vd_priority():
    print("Testing VD Priority Logic...")
    
    # Mock Data
    mock_mcp_result = {
        'project_name': 'Test Project',
        'summary': {'total_watts': 5000},
        'grouped_circuits': [
            # Case 1: Wire Sizing has distance (Highest Priority)
            {
                'circuit_id': 'c1', 'name': 'C1-WireSizing', 'floor': '1', 'total_watts': 1000
            },
            # Case 2: RAG Extraction has branch_distance_m (Second Priority)
            {
                'circuit_id': 'c2', 'name': 'C2-RAGCircuit', 'floor': '1', 'total_watts': 1000,
                'branch_distance_m': 42.0
            },
            # Case 3: RAG Floor Map (Third Priority)
            {
                'circuit_id': 'c3', 'name': 'C3-RAGFloor', 'floor': '2', 'total_watts': 1000
            },
            # Case 4: Default Fallback
            {
                'circuit_id': 'c4', 'name': 'C4-Default', 'floor': '3', 'total_watts': 1000
            },
            # Case 5: Outdoor Special Mapping (Should use Floor 1 default/map)
            {
                'circuit_id': 'c5', 'name': 'C5-Outdoor', 'floor': '1', 'room': 'Outdoor Area', 'total_watts': 1000
            }
        ],
        'wire_sizing': {
            'c1': {'distance_m': 12.5, 'voltage_drop_percent': 1.5, 'ground_size': '2.5', 'wire_size': '4'},
            'c2': {'voltage_drop_percent': 2.0}, # No distance here
            'c3': {'voltage_drop_percent': 2.1},
            'c4': {'voltage_drop_percent': 2.2},
            'c5': {'voltage_drop_percent': 2.3}
        },
        'conduit_sizing': {},
        'floor_distances': {
            '2': 88.0 # Floor 2 map
        }
    }
    
    result = compute_display_data(mock_mcp_result)
    
    circuits = {c['circuit_id']: c for c in result['circuits']}
    defaults = result['default_distance_circuits']
    
    # Check C1: Should be 12.5 (Wire Sizing)
    assert circuits['c1']['branch_distance_m'] == 12.5, f"C1 Failed: {circuits['c1']['branch_distance_m']}"
    print("✅ C1 (Wire Sizing Priority): Pass")
    
    # Check C2: Should be 42.0 (Circuit RAG)
    assert circuits['c2']['branch_distance_m'] == 42.0, f"C2 Failed: {circuits['c2']['branch_distance_m']}"
    print("✅ C2 (Circuit RAG Priority): Pass")
    
    # Check C3: Should be 88.0 (Floor Map RAG)
    assert circuits['c3']['branch_distance_m'] == 88.0, f"C3 Failed: {circuits['c3']['branch_distance_m']}"
    print("✅ C3 (Floor Map Priority): Pass")
    
    # Check C4: Should be 35.0 (Floor 3 Default)
    assert circuits['c4']['branch_distance_m'] == 35.0, f"C4 Failed: {circuits['c4']['branch_distance_m']}"
    assert 'C4-Default' in defaults, "C4 should be in default list"
    print("✅ C4 (Default Fallback): Pass")
    
    # Check C5: Outdoor -> Floor 1 Default (15.0) since no Floor 1 map
    assert circuits['c5']['branch_distance_m'] == 15.0, f"C5 Failed: {circuits['c5']['branch_distance_m']}"
    assert 'C5-Outdoor' in defaults, "C5 should be in default list"
    print("✅ C5 (Outdoor Mapping): Pass")
    
    # Check Summary Fields
    assert result['total_load_va'] == 5000, f"Total Load VA Failed: {result['total_load_va']}"
    assert result['circuit_count'] == 5, "Circuit Count Failed"
    print("✅ Summary Fields: Pass")

if __name__ == "__main__":
    test_vd_priority()
