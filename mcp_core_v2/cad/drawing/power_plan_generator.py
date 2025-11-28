"""
E-201 Power Plan Generator

Generates complete power plan drawing with:
- Outlets/receptacles
- Power wiring
- Homerun to panel
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..autolisp_writer import AutoLISPWriter
from ..routing import WireRouter

logger = logging.getLogger(__name__)


class PowerPlanGenerator:
    """
    Generate E-201 Power Plan
    
    Includes:
    - Outlets/receptacles
    - Power circuit wiring
    - Homerun arrows to panel
    - Circuit labels
    - Legend
    """
    
    def __init__(self, project_name: str = "Power Plan"):
        """Initialize power plan generator"""
        self.project_name = project_name
    
    def generate(self, devices: Dict[str, List[Dict]], 
                panel_position: tuple, standard: str = 'EIT') -> str:
        """
        Generate E-201 power plan
        
        Args:
            devices: Devices with circuits assigned
            panel_position: (x, y) panel location  
            standard: 'EIT', 'IEC', or 'NEC'
        
        Returns:
            AutoLISP code string
        """
        writer = AutoLISPWriter(self.project_name)
        
        # Header
        writer.write_header("E-201", "Power Plan")
        
        # Create layers
        writer.create_layers({
            'E-OUTLET': {'color': 7, 'linetype': 'CONTINUOUS'},
            'E-WIRE-POWER': {'color': 1, 'linetype': 'CONTINUOUS'},
            'E-ANNOTATION': {'color': 8, 'linetype': 'CONTINUOUS'}
        })
        
        # Place outlets
        writer.set_layer('E-OUTLET')
        for outlet in devices.get('outlets', []):
            # Determine symbol based on outlet type
            symbol = "OUTLET"
            device_code = outlet.get('device_code', '')
            if 'IP44' in device_code:
                symbol = "OUTLET_IP44"
            
            writer.insert_block(symbol, outlet['position'])
            
            # Add circuit label
            circuit = outlet.get('circuit', {})
            if circuit:
                label_pos = (outlet['position'][0], outlet['position'][1] - 300)
                circuit_text = circuit.get('id', 'O')
                writer.add_text(circuit_text, label_pos, height=100)
        
        # Route power wiring
        panel = {'position': panel_position, 'id': 'PANEL'}
        router = WireRouter()
        
        # Only route power circuits
        power_devices = {
            'outlets': devices.get('outlets', []),
            'lights': [],
            'switches': []
        }
        
        routes = router.route_all_circuits(power_devices, panel)
        
        # Generate wire LISP
        writer.set_layer('E-WIRE-POWER')
        wire_code = router.generate_wire_lisp(routes, 'E-WIRE-POWER')
        writer.code_lines.append(wire_code)
        
        # Add legend
        self._add_legend(writer, devices, standard)
        
        # Footer
        writer.write_footer()
        writer.wrap_in_function("C:E201")
        
        return writer.get_code()
    
    def _add_legend(self, writer: AutoLISPWriter, devices: Dict, standard: str):
        """Add drawing legend"""
        writer.set_layer('E-ANNOTATION')
        
        legend_x, legend_y = (100, -2500)
        
        # Title
        writer.add_text("POWER PLAN LEGEND", (legend_x, legend_y), height=200)
        
        # Symbols
        y_offset = legend_y - 400
        writer.add_text("⊗ = Outlet (16A)", (legend_x, y_offset), height=120)
        
        y_offset -= 300
        writer.add_text("⊗ IP44 = Waterproof Outlet", (legend_x, y_offset), height=120)
        
        y_offset -= 300
        writer.add_text("─── = Power Wiring", (legend_x, y_offset), height=120)
        
        # Circuit info
        y_offset -= 400
        circuits_used = set()
        for outlet in devices.get('outlets', []):
            circuit = outlet.get(' circuit', {})
            if circuit:
                circuits_used.add(circuit.get('id', 'CKT-X'))
        
        writer.add_text(f"Circuits: {len(circuits_used)}", (legend_x, y_offset), height=120)
        
        y_offset -= 300
        writer.add_text(f"Standard: {standard}", (legend_x, y_offset), height=120)
    
    def save_to_file(self, output_path: Path, devices: Dict,
                    panel_position: tuple, standard: str = 'EIT') -> Path:
        """Generate and save to file"""
        code = self.generate(devices, panel_position, standard)
        output_path = Path(output_path)
        output_path.write_text(code, encoding='utf-8')
        return output_path
