"""
E-501 Typical Details Generator

Generates standard electrical details:
- Outlet mounting details
- Switch mounting details
- Wire routing details
- Symbol legend
"""

import logging
from typing import Dict, List, Any
from pathlib import Path

from ..autolisp_writer import AutoLISPWriter

logger = logging.getLogger(__name__)


class DetailsGenerator:
    """
    Generate E-501 Typical Details
    
    Standard details for electrical installation:
    - Device mounting heights
    - Wire types and sizes
    - Symbol legend
    - Notes and specifications
    """
    
    def __init__(self, project_name: str = "Typical Details"):
        """Initialize details generator"""
        self.project_name = project_name
    
    def generate(self, standard: str = 'EIT') -> str:
        """
        Generate E-501 typical details
        
        Args:
            standard: 'EIT', 'IEC', or 'NEC'
        
        Returns:
            AutoLISP code string
        """
        writer = AutoLISPWriter(self.project_name)
        
        # Header
        writer.write_header("E-501", "Typical Details")
        
        # Create layers
        writer.create_layers({
            'E-DETAIL': {'color': 7, 'linetype': 'CONTINUOUS'},
            'E-TEXT': {'color': 1, 'linetype': 'CONTINUOUS'},
            'E-DIM': {'color': 3, 'linetype': 'CONTINUOUS'}
        })
        
        writer.set_layer('E-DETAIL')
        
        # Draw details
        self._draw_outlet_detail(writer, (1000, 8000), standard)
        self._draw_switch_detail(writer, (6000, 8000), standard)
        self._draw_wire_legend(writer, (1000, 4000), standard)
        self._draw_symbol_legend(writer, (6000, 4000), standard)
        
        # Add general notes
        self._add_general_notes(writer, (1000, 1000), standard)
        
        # Footer
        writer.write_footer()
        writer.wrap_in_function("C:E501")
        
        return writer.get_code()
    
    def _draw_outlet_detail(self, writer: AutoLISPWriter, origin: tuple, standard: str):
        """Draw outlet mounting detail"""
        x, y = origin
        
        # Title
        writer.add_text("OUTLET MOUNTING DETAIL", (x, y + 500), height=180)
        
        # Wall representation
        writer.draw_line((x, y), (x, y - 2000))
        writer.draw_line((x + 100, y), (x + 100, y - 2000))
        
        # Outlet box
        box_y = y - 300
        box_points = [
            (x + 100, box_y),
            (x + 250, box_y),
            (x + 250, box_y - 80),
            (x + 100, box_y - 80),
            (x + 100, box_y)
        ]
        writer.draw_polyline(box_points)
        
        # Dimension
        writer.add_text("300mm AFF", (x + 300, box_y), height=100)
        
        # Notes
        writer.add_text("- Height: 300mm above finished floor", (x, y - 1500), height=80)
        writer.add_text("- Type: 16A 250V", (x, y - 1650), height=80)
        if standard == 'EIT':
            writer.add_text("- Standard: TIS 166", (x, y - 1800), height=80)
    
    def _draw_switch_detail(self, writer: AutoLISPWriter, origin: tuple, standard: str):
        """Draw switch mounting detail"""
        x, y = origin
        
        # Title
        writer.add_text("SWITCH MOUNTING DETAIL", (x, y + 500), height=180)
        
        # Wall
        writer.draw_line((x, y), (x, y - 2000))
        writer.draw_line((x + 100, y), (x + 100, y - 2000))
        
        # Switch box
        box_y = y - 1100
        box_points = [
            (x + 100, box_y),
            (x + 250, box_y),
            (x + 250, box_y - 80),
            (x + 100, box_y - 80),
            (x + 100, box_y)
        ]
        writer.draw_polyline(box_points)
        
        # Dimension
        writer.add_text("1100mm AFF", (x + 300, box_y), height=100)
        
        # Notes
        writer.add_text("- Height: 1100mm above finished floor", (x, y - 1500), height=80)
        writer.add_text("- Type: 1-way or 2-way", (x, y - 1650), height=80)
        writer.add_text("- Near door latch side", (x, y - 1800), height=80)
    
    def _draw_wire_legend(self, writer: AutoLISPWriter, origin: tuple, standard: str):
        """Draw wire type legend"""
        x, y = origin
        
        # Title
        writer.add_text("WIRE SPECIFICATIONS", (x, y + 300), height=180)
        
        y_offset = y
        
        # Wire types
        wires = [
            ("Power Circuits", "2.5mm² THW/THHN", "20A max"),
            ("Lighting Circuits", "1.5mm² THW/THHN", "10A max"),
            ("Dedicated Circuits", "4.0mm² THW/THHN", "32A max")
        ]
        
        for desc, wire_type, rating in wires:
            writer.add_text(f"- {desc}:", (x, y_offset), height=100)
            y_offset -= 150
            writer.add_text(f"  {wire_type} ({rating})", (x + 100, y_offset), height=90)
            y_offset -= 200
    
    def _draw_symbol_legend(self, writer: AutoLISPWriter, origin: tuple, standard: str):
        """Draw symbol legend"""
        x, y = origin
        
        # Title
        writer.add_text("SYMBOL LEGEND", (x, y + 300), height=180)
        
        y_offset = y
        
        symbols = [
            ("○", "Ceiling Light"),
            ("S", "Switch"),
            ("⊗", "Outlet/Receptacle"),
            ("⊗ IP44", "Waterproof Outlet"),
            ("───→", "Homerun to Panel"),
            ("DB", "Distribution Board")
        ]
        
        for symbol, desc in symbols:
            writer.add_text(f"{symbol}  =  {desc}", (x, y_offset), height=100)
            y_offset -= 200
    
    def _add_general_notes(self, writer: AutoLISPWriter, origin: tuple, standard: str):
        """Add general notes"""
        x, y = origin
        
        writer.set_layer('E-TEXT')
        writer.add_text("GENERAL NOTES:", (x, y), height=150)
        
        notes = [
            "1. All dimensions in millimeters unless noted",
            "2. Wire sizes per circuit calculations",
            "3. All outlets GFCI/RCBO in wet areas",
            "4. Follow local electrical code",
            f"5. Installation per {standard} standard"
        ]
        
        y_offset = y - 300
        for note in notes:
            writer.add_text(note, (x, y_offset), height=100)
            y_offset -= 200
    
    def save_to_file(self, output_path: Path, standard: str = 'EIT') -> Path:
        """Generate and save to file"""
        code = self.generate(standard)
        output_path = Path(output_path)
        output_path.write_text(code, encoding='utf-8')
        return output_path
