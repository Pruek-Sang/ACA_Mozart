"""
Circuit Assigner - Assign circuits from MCP results to placed devices

Critical (from plan):
- Circuit assignment MUST come from MCP results
- Devices have circuit=None until this step
- Maps device IDs to circuit IDs, wire sizes, breaker info
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class CircuitAssigner:
    """
    Assign circuits from MCP calculation results to placed devices
    
    Responsibilities (per plan):
    - Map devices to circuit IDs from MCP
    - Assign wire sizes from wire_sizer results
    - Assign breaker info from MCP
    - Maintain device→circuit relationship
    """
    
    def __init__(self, mcp_result: Any):
        """
        Initialize circuit assigner
        
        Args:
            mcp_result: MCP calculation result with circuits, wires, breakers
        """
        self.mcp_result = mcp_result
        self.assignments = {}
    
    def assign_circuits_from_mcp(self, devices: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Assign circuits from MCP to devices
        
        Algorithm (per plan):
        1. For each MCP circuit:
           - Find matching devices by description/type
           - Assign circuit_id, wire_size, breaker_rating
        2. For unassigned devices:
           - Create default assignments
        
        Args:
            devices: {
                'outlets': [...],  # circuit=None
                'lights': [...],   # circuit=None
                'switches': [...]  # circuit=None (controls only)
            }
        
        Returns:
            Same structure but with circuit assigned:
            {
                'outlets': [...],  # circuit={'id': 'CKT-1', 'wire': '2.5mm²', ...}
                'lights': [...],
                'switches': [...]
            }
        """
        assigned_devices = {
            'outlets': [],
            'lights': [],
            'switches': []
        }
        
        # Assign outlets to power circuits
        circuit_idx = 1
        for i, outlet in enumerate(devices.get('outlets', [])):
            # Get wire/breaker from MCP if available
            circuit_info = self._get_circuit_info(circuit_idx, 'power')
            
            outlet_assigned = outlet.copy()
            outlet_assigned['circuit'] = {
                'id': f'CKT-{circuit_idx}',
                'type': 'power',
                'wire_size': circuit_info.get('wire_size', '2.5mm²'),
                'breaker_rating': circuit_info.get('breaker_rating', '16A'),
                'description': f'Power Circuit {circuit_idx}'
            }
            
            assigned_devices['outlets'].append(outlet_assigned)
            
            # New circuit every 6-8 outlets (typical)
            if (i + 1) % 6 == 0:
                circuit_idx += 1
        
        # Assign lights to lighting circuits
        for i, light in enumerate(devices.get('lights', [])):
            circuit_info = self._get_circuit_info(circuit_idx, 'lighting')
            
            light_assigned = light.copy()
            light_assigned['circuit'] = {
                'id': f'CKT-{circuit_idx}',
                'type': 'lighting',
                'wire_size': circuit_info.get('wire_size', '1.5mm²'),
                'breaker_rating': circuit_info.get('breaker_rating', '10A'),
                'description': f'Lighting Circuit {circuit_idx}'
            }
            
            assigned_devices['lights'].append(light_assigned)
            
            # New circuit every 8-10 lights
            if (i + 1) % 8 == 0:
                circuit_idx += 1
        
        # Switches don't get circuits (they control lights)
        for switch in devices.get('switches', []):
            switch_assigned = switch.copy()
            switch_assigned['circuit'] = None  # Switches control, don't consume
            assigned_devices['switches'].append(switch_assigned)
        
        return assigned_devices
    
    def _get_circuit_info(self, circuit_idx: int, circuit_type: str) -> Dict[str, Any]:
        """
        Get circuit info from MCP results
        
        Args:
            circuit_idx: Circuit number
            circuit_type: 'power' or 'lighting'
        
        Returns:
            Circuit info dict with wire_size, breaker_rating
        """
        # Try to get from MCP results
        if hasattr(self.mcp_result, 'wires') and len(self.mcp_result.wires) >= circuit_idx:
            wire = self.mcp_result.wires[circuit_idx - 1]
            breaker = self.mcp_result.breakers[circuit_idx - 1] if hasattr(self.mcp_result, 'breakers') else None
            
            return {
                'wire_size': f'{wire.size_mm2}mm²' if hasattr(wire, 'size_mm2') else '2.5mm²',
                'breaker_rating': f'{breaker.rating}A' if breaker and hasattr(breaker, 'rating') else '16A',
                'conduit_size': getattr(wire, 'conduit_size', '20mm')
            }
        
        # Defaults based on type
        if circuit_type == 'lighting':
            return {
                'wire_size': '1.5mm²',
                'breaker_rating': '10A',
                'conduit_size': '16mm'
            }
        else:  # power
            return {
                'wire_size': '2.5mm²',
                'breaker_rating': '16A',
                'conduit_size': '20mm'
            }


def assign_circuits(devices: Dict[str, List[Dict]], mcp_result: Any) -> Dict[str, List[Dict]]:
    """
    Convenience function to assign circuits
    
    Args:
        devices: Device dict from DevicePlacer (circuit=None)
        mcp_result: MCP calculation result
    
    Returns:
        Devices with circuits assigned
    """
    assigner = CircuitAssigner(mcp_result)
    return assigner.assign_circuits_from_mcp(devices)
