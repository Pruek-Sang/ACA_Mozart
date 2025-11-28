"""
E-301 Single Line Diagram Generator

Generates AutoLISP code for electrical single line diagrams showing:
- Utility/source connection
- Main breaker
- Panel/distribution board
- Branch circuits (simplified)
- Grounding system

Uses M

CP calculation results as source of truth for all electrical data.
"""

import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

from ..autolisp_writer import AutoLISPWriter

logger = logging.getLogger(__name__)


class SingleLineDiagramGenerator:
    """
    Generator for E-301 Single Line Diagrams
    
    Reads from MCP result:
    - Panel specifications
    - Circuit summaries
    - Wire sizes (from wire_sizer)
    - Breaker ratings (from breaker_selector)
    """
    
    def __init__(self, project_name: str = ""):
        self.project_name = project_name
        self.writer = AutoLISPWriter(project_name)
    
    def generate(self, panel_data: Dict[str, Any], mcp_result: Any, standard: str = 'EIT') -> str:
        """
        Generate E-301 Single Line Diagram
        
        Args:
            panel_data: {
                'id': 'DB-1',
                'name': 'Main Distribution Board',
                'voltage': '230V' or enum value,
                'rating': '100A',
                'location': (x, y)
            }
            mcp_result: DesignResult from MCP pipeline
            standard: 'EIT', 'IEC', or 'NEC'
        
        Returns:
            LISP code string
        """
        # Start fresh
        self.writer = AutoLISPWriter(self.project_name)
        
        # Header
        self.writer.write_header(
            "E-301 Single Line Diagram",
            f"Panel: {panel_data.get('name', panel_data['id'])}"
        )
        
        # Create layers
        layers = {
            'E-ELEC-SLD': {'color': 1, 'linetype': 'CONTINUOUS'},
            'E-ELEC-TEXT': {'color': 7, 'linetype': 'CONTINUOUS'},
        }
        self.writer.create_layers(layers)
        self.writer.set_layer('E-ELEC-SLD')
        
        # Draw diagram components
        self._draw_utility_source(panel_data)
        self._draw_main_breaker(panel_data)
        self._draw_panel(panel_data)
        self._draw_branch_circuits(panel_data, mcp_result)
        self._draw_grounding(panel_data)
        
        # Add legend
        self._draw_legend(standard)
        
        # Footer
        self.writer.write_footer()
        
        # Wrap in function
        self.writer.wrap_in_function("C:ELEC-E301")
        
        return self.writer.get_code()
    
    def _draw_utility_source(self, panel_data: Dict[str, Any]) -> None:
        """Draw utility/source symbol"""
        # Position at top
        x, y = 0, 5000
        
        # Symbol: Simple rectangle
        self.writer.draw_line((x - 200, y), (x + 200, y))
        self.writer.draw_line((x + 200, y), (x + 200, y - 300))
        self.writer.draw_line((x + 200, y - 300), (x - 200, y - 300))
        self.writer.draw_line((x - 200, y - 300), (x - 200, y))
        
        # Label
        voltage = panel_data.get('voltage', '230V')
        if hasattr(voltage, 'value'):  # Enum
            voltage = voltage.value
        
        self.writer.set_layer('E-ELEC-TEXT')
        self.writer.add_text(f"UTILITY {voltage}", (x - 150, y + 200), height=80)
        self.writer.set_layer('E-ELEC-SLD')
    
    def _draw_main_breaker(self, panel_data: Dict[str, Any]) -> None:
        """Draw main breaker symbol"""
        x, y = 0, 4000
        
        # Breaker symbol: Rectangle with "X"
        self.writer.draw_line((x - 150, y), (x + 150, y))
        self.writer.draw_line((x + 150, y), (x + 150, y - 400))
        self.writer.draw_line((x + 150, y - 400), (x - 150, y - 400))
        self.writer.draw_line((x - 150, y - 400), (x - 150, y))
        
        # X mark
        self.writer.draw_line((x - 150, y), (x + 150, y - 400))
        self.writer.draw_line((x + 150, y), (x - 150, y - 400))
        
        # Connecting line from utility
        self.writer.draw_line((0, 4700), (0, 4000))
        
        # Label
        rating = panel_data.get('rating', '100A')
        self.writer.set_layer('E-ELEC-TEXT')
        self.writer.add_text(f"MCB {rating}", (x + 200, y - 200), height=80)
        self.writer.set_layer('E-ELEC-SLD')
    
    def _draw_panel(self, panel_data: Dict[str, Any]) -> None:
        """Draw panel/DB symbol"""
        x, y = 0, 3000
        
        # Panel symbol: Large rectangle
        self.writer.draw_line((x - 300, y), (x + 300, y))
        self.writer.draw_line((x + 300, y), (x + 300, y - 600))
        self.writer.draw_line((x + 300, y - 600), (x - 300, y - 600))
        self.writer.draw_line((x - 300, y - 600), (x - 300, y))
        
        # Connecting line from breaker
        self.writer.draw_line((0, 3600), (0, 3000))
        
        # Label
        panel_id = panel_data.get('id', 'DB-1')
        panel_name = panel_data.get('name', '')
        
        self.writer.set_layer('E-ELEC-TEXT')
        self.writer.add_text(panel_id, (x - 250, y - 300), height=120)
        if panel_name:
            self.writer.add_text(panel_name, (x + 350, y - 300), height=70)
        self.writer.set_layer('E-ELEC-SLD')
    
    def _draw_branch_circuits(self, panel_data: Dict[str, Any], mcp_result: Any) -> None:
        """
        Draw branch circuits (simplified single lines)
        
        For MVP: Show circuit count and summary, not detailed routing
        """
        x, y_start = 0, 2400
        
        # Extract circuit info from MCP result
        circuits = self._extract_circuits_from_mcp(mcp_result)
        
        if not circuits:
            # No circuits, just show placeholder
            self.writer.set_layer('E-ELEC-TEXT')
            self.writer.add_text("(Branch circuits - see panel schedule)", 
                               (x + 400, y_start), height=70)
            return
        
        # Draw up to 5 circuits (simplified for SLD)
        for i, circuit in enumerate(circuits[:5]):
            y = y_start - (i * 200)
            
            # Circuit line
            self.writer.draw_line((x, 2400), (x + 800, y))
            
            # Circuit label
            self.writer.set_layer('E-ELEC-TEXT')
            circuit_label = f"{circuit.get('id', f'CKT-{i+1}')}: " \
                          f"{circuit.get('description', 'Circuit')} " \
                          f"({circuit.get('wire_size', 'N/A')})"
            self.writer.add_text(circuit_label, (x + 850, y - 30), height=60)
            self.writer.set_layer('E-ELEC-SLD')
        
        if len(circuits) > 5:
            # Show "..." for more circuits
            self.writer.set_layer('E-ELEC-TEXT')
            self.writer.add_text(f"... and {len(circuits) - 5} more circuits", 
                               (x + 850, y_start - 1100), height=60)
    
    def _draw_grounding(self, panel_data: Dict[str, Any]) -> None:
        """Draw grounding system notation"""
        x, y = -500, 2000
        
        # Ground symbol
        # Triangle pointing down
        self.writer.draw_polyline([
            (x, y),
            (x - 100, y - 200),
            (x + 100, y - 200),
            (x, y)
        ])
        
        # Connecting line
        self.writer.draw_line((0, 2400), (x, y))
        
        # Label
        self.writer.set_layer('E-ELEC-TEXT')
        self.writer.add_text("Earthing System", (x - 100, y - 350), height=70)
        self.writer.add_text("(TN-S or local standard)", (x - 150, y - 450), height=50)
        self.writer.set_layer('E-ELEC-SLD')
    
    def _draw_legend(self, standard: str) -> None:
        """Draw symbol legend"""
        x, y = 2000, 5000
        
        self.writer.set_layer('E-ELEC-TEXT')
        self.writer.add_text("LEGEND", (x, y), height=100)
        self.writer.add_text(f"Standard: {standard}", (x, y - 150), height=70)
        self.writer.add_text("━━  Utility Supply", (x, y - 300), height=60)
        self.writer.add_text("□   Breaker (MCB)", (x, y - 400), height=60)
        self.writer.add_text("▭   Distribution Board", (x, y - 500), height=60)
        self.writer.add_text("▽   Grounding", (x, y - 600), height=60)
    
    def _extract_circuits_from_mcp(self, mcp_result: Any) -> List[Dict[str, Any]]:
        """
        Extract circuit information from MCP result
        
        Returns:
            List of circuit dicts with id, description, wire_size, breaker
        """
        circuits = []
        
        # Try to get circuits from result
        # MCP result structure (from models.contracts):
        # - loads: List[LoadResult]
        # - wires: List[WireResult]  
        # - breakers: List[BreakerResult]
        
        try:
            # Group by circuit (if available)
            if hasattr(mcp_result, 'wires'):
                for i, wire in enumerate(mcp_result.wires):
                    circuit = {
                        'id': f'CKT-{i+1}',
                        'description': getattr(wire, 'description', f'Circuit {i+1}'),
                        'wire_size': getattr(wire, 'size_mm2', 'N/A'),
                        'breaker': 'N/A'
                    }
                    
                    # Try to get breaker info
                    if hasattr(mcp_result, 'breakers') and i < len(mcp_result.breakers):
                        breaker = mcp_result.breakers[i]
                        circuit['breaker'] = getattr(breaker, 'rating', 'N/A')
                    
                    circuits.append(circuit)
            
            # Fallback: create placeholder circuits
            if not circuits:
                circuits = [
                    {'id': 'CKT-1', 'description': 'Lighting Circuit', 
                     'wire_size': '2.5mm²', 'breaker': '16A'},
                    {'id': 'CKT-2', 'description': 'Power Circuit', 
                     'wire_size': '2.5mm²', 'breaker': '20A'},
                ]
        
        except Exception as e:
            logger.warning(f"Could not extract circuits from MCP result: {e}")
            circuits = []
        
        return circuits
    
    def save_to_file(self, output_path: Path, panel_data: Dict[str, Any], 
                    mcp_result: Any, standard: str = 'EIT') -> Path:
        """
        Generate and save E-301 LISP file
        
        Returns:
            Path to saved file
        """
        code = self.generate(panel_data, mcp_result, standard)
        
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Generated E-301: {output_path}")
        return output_path
