"""
E-101 Lighting Plan Generator

Generates complete lighting plan drawing with:
- Ceiling lights
- Switches
- Wiring (switch legs)
- Homerun to panel
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..autolisp_writer import AutoLISPWriter
from ..routing import WireRouter

logger = logging.getLogger(__name__)


class LightingPlanGenerator:
    """
    Generate E-101 Lighting Plan
    
    Includes:
    - Light fixtures (ceiling-mounted)
    - Switches (wall-mounted)
    - Switch legs (wiring)
    - Homerun arrows to panel
    - Legend and notes
    """
    
    def __init__(self, project_name: str = "Lighting Plan"):
        """Initialize lighting plan generator"""
        self.project_name = project_name
        self.writer = AutoLISPWriter(project_name)
    
    def generate(self, devices: Dict[str, List[Dict]], 
                panel_position: tuple, standard: str = 'EIT') -> str:
        """
        Generate E-101 lighting plan
        
        Args:
            devices: Devices with circuits assigned
            panel_position: (x, y) panel location
            standard: 'EIT', 'IEC', or 'NEC'
        
        Returns:
            AutoLISP code string
        """
        writer = AutoLISPWriter(self.project_name)
        
        # Header
        writer.write_header("E-101", "Lighting Plan")
        
        # Create layers
        writer.create_layers({
            'E-LIGHT': {'color': 3, 'linetype': 'CONTINUOUS'},
            'E-SWITCH': {'color': 5, 'linetype': 'CONTINUOUS'},
            'E-WIRE-LIGHTING': {'color': 2, 'linetype': 'CONTINUOUS'},
            'E-ANNOTATION': {'color': 8, 'linetype': 'CONTINUOUS'}
        })
        
        # Place lights
        writer.set_layer('E-LIGHT')
        for light in devices.get('lights', []):
            writer.insert_block("LIGHT", light['position'])
            
            # Add label
            circuit = light.get('circuit', {})
            if circuit:
                label_pos = (light['position'][0] + 200, light['position'][1] - 200)
                writer.add_text(circuit.get('id', 'L'), label_pos, height=120)
        
        # Place switches
        writer.set_layer('E-SWITCH')
        for switch in devices.get('switches', []):
            writer.insert_block("SWITCH", switch['position'], rotation=0)
            
            # Add label
            label_pos = (switch['position'][0] + 200, switch['position'][1] + 200)
            writer.add_text(switch.get('id', 'SW'), label_pos, height=120)
        
        # Route wiring
        panel = {'position': panel_position, 'id': 'PANEL'}
        router = WireRouter()
        
        # Only route lighting circuits
        lighting_devices = {
            'lights': devices.get('lights', []),
            'switches': devices.get('switches', []),
            'outlets': []  # No outlets in lighting plan
        }
        
        routes = router.route_all_circuits(lighting_devices, panel)
        
        # Generate wire LISP
        writer.set_layer('E-WIRE-LIGHTING')
        wire_code = router.generate_wire_lisp(routes, 'E-WIRE-LIGHTING')
        writer.code_lines.append(wire_code)
        
        # Add legend
        self._add_legend(writer, devices, standard)
        
        # Footer
        writer.write_footer()
        writer.wrap_in_function("C:E101")
        
        return writer.get_code()
    
    def _add_legend(self, writer: AutoLISPWriter, devices: Dict, standard: str):
        """Add drawing legend"""
        writer.set_layer('E-ANNOTATION')
        
        # Legend box position
        legend_x, legend_y = (100, -2000)
        
        # Title
        writer.add_text("LIGHTING PLAN LEGEND", (legend_x, legend_y), height=200)
        
        # Symbols
        y_offset = legend_y - 400
        writer.add_text("○ = Ceiling Light", (legend_x, y_offset), height=120)
        
        y_offset -= 300
        writer.add_text("S = Switch", (legend_x, y_offset), height=120)
        
        y_offset -= 300
        writer.add_text("─── = Wiring", (legend_x, y_offset), height=120)
        
        y_offset -= 300
        writer.add_text(f"Standard: {standard}", (legend_x, y_offset), height=120)
    
    def save_to_file(self, output_path: Path, devices: Dict, 
                    panel_position: tuple, standard: str = 'EIT') -> Path:
        """Generate and save to file"""
        code = self.generate(devices, panel_position, standard)
        output_path = Path(output_path)
        output_path.write_text(code, encoding='utf-8')
        return output_path
