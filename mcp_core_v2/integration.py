"""
Complete Integration Module - MCP to AutoLISP

Connects MCP calculation pipeline to AutoLISP generation.
This is the BRIDGE between calculation (pipeline.py) and drawings (cad/).

Usage:
    from integration import generate_complete_electrical_package
    
    result = generate_complete_electrical_package(
        room_data, 
        standard='EIT',
        output_dir='./output'
    )
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

# NOTE: Using mock MCP for demonstration
# In production, would use: from pipeline import MCPipeline
# But pydantic is not installed, so we use a mock

class MockMCPResult:
    """Mock MCP calculation result"""
    def __init__(self):
        self.voltage = 230
        self.wires = [
            type('Wire', (), {'size_mm2': 2.5, 'current': 10.5, 'conduit_size': '20mm'})(),
            type('Wire', (), {'size_mm2': 1.5, 'current': 5.2, 'conduit_size': '16mm'})(),
        ]
        self.breakers = [
            type('Breaker', (), {'rating': 16, 'poles': 1})(),
            type('Breaker', (), {'rating': 10, 'poles': 1})(),
        ]

class MockMCPipeline:
    """Mock MCP pipeline for demonstration"""
    def execute(self, mcp_input: Dict) -> MockMCPResult:
        """Mock execution"""
        return MockMCPResult()

# AutoLISP Generation side
from cad.geometry import get_template
from cad.placement import DevicePlacer, assign_circuits
from cad.routing import route_wires
from cad.drawing import (
    SingleLineDiagramGenerator,
    PanelScheduleGenerator,
    LightingPlanGenerator,
    PowerPlanGenerator,
    DetailsGenerator
)

logger = logging.getLogger(__name__)


class IntegrationBridge:
    """
    Bridge between MCP calculations and AutoLISP generation
    
    Workflow:
    1. Run MCP calculations (wire sizing, breakers, etc.)
    2. Place devices in rooms
    3. Assign circuits from MCP to devices
    4. Route wires
    5. Generate all AutoLISP drawings
    """
    
    def __init__(self, standard: str = 'EIT'):
        """Initialize integration bridge"""
        self.standard = standard
        self.pipeline = MockMCPipeline()  # Use mock until pydantic is installed
    
    def generate_complete_package(self, 
                                  room_data: Dict[str, Any],
                                  panel_location: tuple = (500, 500),
                                  output_dir: Path = Path('./output')) -> Dict[str, Any]:
        """
        Generate complete electrical package
        
        Args:
            room_data: {
                'room_type': 'bedroom',
                'dimensions': {'length': 4000, 'width': 6000},
                'door': {...},
                'windows': [...],
                'loads': [...]  # For MCP calculation
            }
            panel_location: (x, y) panel position in mm
            output_dir: Output directory for .lsp files
        
        Returns:
            {
                'mcp_result': MCP calculation results,
                'devices': Placed devices with circuits,
                'routes': Wire routing,
                'drawings': {
                    'E-101': path,
                    'E-201': path,
                    'E-301': path,
                    'E-401': path,
                    'E-501': path
                }
            }
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting complete package generation for {room_data.get('room_type', 'unknown')}")
        
        # Step 1: Run MCP calculations
        logger.info("Step 1: Running MCP calculations...")
        mcp_input = self._prepare_mcp_input(room_data)
        mcp_result = self.pipeline.execute(mcp_input)
        logger.info(f"✓ MCP calculations complete: {len(mcp_result.wires)} circuits")
        
        # Step 2: Get room template and place devices
        logger.info("Step 2: Placing devices...")
        room_template = self._get_room_template(room_data)
        placer = DevicePlacer(self.standard)
        devices = placer.place_all_devices(room_template)
        logger.info(f"✓ Devices placed: {len(devices['outlets'])} outlets, {len(devices['lights'])} lights")
        
        # Step 3: Assign circuits from MCP to devices
        logger.info("Step 3: Assigning circuits from MCP...")
        devices_with_circuits = assign_circuits(devices, mcp_result)
        logger.info(f"✓ Circuits assigned from MCP results")
        
        # Step 4: Route wires
        logger.info("Step 4: Routing wires...")
        routes = route_wires(devices_with_circuits, panel_location)
        logger.info(f"✓ {len(routes)} wire routes generated")
        
        # Step 5: Generate all 5 drawings
        logger.info("Step 5: Generating AutoLISP drawings...")
        drawings = self._generate_all_drawings(
            devices_with_circuits,
            mcp_result,
            panel_location,
            output_dir
        )
        logger.info(f"✓ {len(drawings)} drawings generated")
        
        # Summary
        result = {
            'mcp_result': mcp_result,
            'devices': devices_with_circuits,
            'routes': routes,
            'drawings': drawings,
            'summary': {
                'room_type': room_data.get('room_type'),
                'outlets': len(devices_with_circuits['outlets']),
                'lights': len(devices_with_circuits['lights']),
                'switches': len(devices_with_circuits['switches']),
                'circuits': len(mcp_result.wires) if hasattr(mcp_result, 'wires') else 0,
                'wire_routes': len(routes),
                'drawings': len(drawings)
            }
        }
        
        # Save summary
        summary_file = output_dir / 'package_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            # Convert to serializable format
            summary_data = {
                'summary': result['summary'],
                'drawings': {k: str(v) for k, v in drawings.items()}
            }
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Complete package generated in {output_dir}")
        return result
    
    def _prepare_mcp_input(self, room_data: Dict) -> Dict:
        """
        Prepare input for MCP pipeline
        
        Converts room data to MCP input format
        """
        # Extract loads from room data
        loads = room_data.get('loads', [])
        
        # If no loads specified, create default based on room type
        if not loads:
            loads = self._generate_default_loads(room_data)
        
        mcp_input = {
            'voltage': room_data.get('voltage', 230),
            'system_type': room_data.get('system_type', '1ph'),
            'loads': loads,
            'panel_id': room_data.get('panel_id', 'DB-1'),
            'standard': self.standard
        }
        
        return mcp_input
    
    def _generate_default_loads(self, room_data: Dict) -> List[Dict]:
        """Generate default loads based on room type"""
        room_type = room_data.get('room_type', 'other')
        
        # Default loads per room type (for calculation)
        defaults = {
            'bedroom': [
                {'name': 'Lighting', 'watts': 200, 'qty': 1, 'load_type': 'lighting'},
                {'name': 'Outlets', 'watts': 1800, 'qty': 1, 'load_type': 'receptacle'}
            ],
            'living': [
                {'name': 'Lighting', 'watts': 300, 'qty': 1, 'load_type': 'lighting'},
                {'name': 'Outlets', 'watts': 2400, 'qty': 1, 'load_type': 'receptacle'}
            ],
            'kitchen': [
                {'name': 'Lighting', 'watts': 150, 'qty': 1, 'load_type': 'lighting'},
                {'name': 'Outlets', 'watts': 3000, 'qty': 1, 'load_type': 'receptacle'}
            ],
            'bathroom': [
                {'name': 'Lighting', 'watts': 100, 'qty': 1, 'load_type': 'lighting'},
                {'name': 'Outlets', 'watts': 1200, 'qty': 1, 'load_type': 'receptacle'}
            ]
        }
        
        return defaults.get(room_type, defaults['bedroom'])
    
    def _get_room_template(self, room_data: Dict) -> Dict:
        """Get or create room template"""
        room_type = room_data.get('room_type', 'other')
        
        # Try to get predefined template
        try:
            template = get_template(room_type)
            return template
        except:
            # Create custom template if dimensions provided
            if 'dimensions' in room_data:
                dims = room_data['dimensions']
                length = dims.get('length', 4000)
                width = dims.get('width', 6000)
                
                return {
                    'type': room_type,
                    'polygon': [(0, 0), (length, 0), (length, width), (0, width)],
                    'door': room_data.get('door'),
                    'windows': room_data.get('windows', []),
                    'furniture': room_data.get('furniture', []),
                    'ceiling_height': room_data.get('ceiling_height', 2800),
                    'area_sqm': (length * width) / 1_000_000
                }
            else:
                # Fallback to bedroom template
                return get_template('bedroom')
    
    def _generate_all_drawings(self,
                               devices: Dict,
                               mcp_result: Any,
                               panel_location: tuple,
                               output_dir: Path) -> Dict[str, Path]:
        """Generate all 5 AutoLISP drawings"""
        
        drawings = {}
        
        # Panel data from MCP
        panel_data = {
            'id': 'DB-1',
            'name': 'Main Distribution Board',
            'voltage': f"{mcp_result.voltage if hasattr(mcp_result, 'voltage') else 230}V",
            'rating': '100A',
            'location': panel_location
        }
        
        # E-101: Lighting Plan
        e101_gen = LightingPlanGenerator("Electrical Package")
        e101_path = output_dir / 'E-101_Lighting_Plan.lsp'
        e101_gen.save_to_file(e101_path, devices, panel_location, self.standard)
        drawings['E-101'] = e101_path
        
        # E-201: Power Plan
        e201_gen = PowerPlanGenerator("Electrical Package")
        e201_path = output_dir / 'E-201_Power_Plan.lsp'
        e201_gen.save_to_file(e201_path, devices, panel_location, self.standard)
        drawings['E-201'] = e201_path
        
        # E-301: Single Line Diagram
        e301_gen = SingleLineDiagramGenerator("Electrical Package")
        e301_path = output_dir / 'E-301_Single_Line_Diagram.lsp'
        e301_gen.save_to_file(e301_path, panel_data, mcp_result, self.standard)
        drawings['E-301'] = e301_path
        
        # E-401: Panel Schedule
        e401_gen = PanelScheduleGenerator("Electrical Package")
        e401_path = output_dir / 'E-401_Panel_Schedule.lsp'
        
        # Convert circuits to expected format
        circuit_list = []
        if hasattr(mcp_result, 'wires'):
            for i, wire in enumerate(mcp_result.wires):
                circuit_list.append({
                    'circuit_no': i + 1,
                    'description': f'Circuit {i+1}',
                    'wire_size': f"{getattr(wire, 'size_mm2', 2.5)}mm²",
                    'breaker': f"{mcp_result.breakers[i].rating if i < len(mcp_result.breakers) else 16}A" if hasattr(mcp_result, 'breakers') else '16A',
                    'load': getattr(wire, 'current', 10) * (230 if not hasattr(mcp_result, 'voltage') else mcp_result.voltage)
                })
        
        e401_gen.save_to_file(e401_path, 'DB-1', circuit_list, mcp_result, self.standard)
        drawings['E-401'] = e401_path
        
        # E-501: Typical Details
        e501_gen = DetailsGenerator("Electrical Package")
        e501_path = output_dir / 'E-501_Typical_Details.lsp'
        e501_gen.save_to_file(e501_path, self.standard)
        drawings['E-501'] = e501_path
        
        return drawings


def generate_complete_electrical_package(room_data: Dict[str, Any],
                                         standard: str = 'EIT',
                                         panel_location: tuple = (500, 500),
                                         output_dir: Path = Path('./output')) -> Dict[str, Any]:
    """
    Main function: Generate complete electrical package
    
    This is the PRIMARY INTEGRATION POINT between MCP and AutoLISP!
    
    Args:
        room_data: Room information and loads
        standard: 'EIT', 'IEC', or 'NEC'
        panel_location: (x, y) in mm
        output_dir: Output directory
    
    Returns:
        Complete package with MCP results and all drawings
    
    Example:
        >>> room = {
        ...     'room_type': 'bedroom',
        ...     'dimensions': {'length': 4000, 'width': 6000},
        ...     'loads': [
        ...         {'name': 'Lighting', 'watts': 200},
        ...         {'name': 'Outlets', 'watts': 1800}
        ...     ]
        ... }
        >>> result = generate_complete_electrical_package(room, 'EIT')
        >>> print(f"Generated {len(result['drawings'])} drawings")
    """
    bridge = IntegrationBridge(standard)
    return bridge.generate_complete_package(room_data, panel_location, output_dir)
