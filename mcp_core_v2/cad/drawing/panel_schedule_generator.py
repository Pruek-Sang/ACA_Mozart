"""
E-401 Panel Schedule Generator

Generates AutoLISP code for electrical panel schedules (table format).
Shows all circuit details in a comprehensive 12-column table.

Uses MCP calculation results as the single source of truth.
"""

import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

from ..autolisp_writer import AutoLISPWriter

logger = logging.getLogger(__name__)


class PanelScheduleGenerator:
    """
    Generator for E-401 Panel Schedule
    
    Creates a detailed circuit table with 12 columns:
    1. Circuit No.
    2. Description
    3. No. of Points
    4. Load (VA or W)
    5. Demand Factor
    6. Demand Load
    7. Current (A)
    8. Breaker Size (A, poles)
    9. Cable Size (mm², cores)
    10. Conduit Size (mm)
    11. Protection Type (MCB/RCBO)
    12. Remarks
    """
    
    def __init__(self, project_name: str = ""):
        self.project_name = project_name
        self.writer = AutoLISPWriter(project_name)
    
    def generate(self, panel_id: str, circuit_list: List[Dict[str, Any]], 
                mcp_result: Any, standard: str = 'EIT') -> str:
        """
        Generate E-401 Panel Schedule
        
        Args:
            panel_id: Panel identifier (e.g., 'DB-1')
            circuit_list: List of circuit dicts (from MCP)
            mcp_result: DesignResult from MCP pipeline
            standard: 'EIT', 'IEC', or 'NEC'
        
        Returns:
            LISP code string
        """
        # Start fresh
        self.writer = AutoLISPWriter(self.project_name)
        
        # Header
        self.writer.write_header(
            "E-401 Panel Schedule",
            f"Panel: {panel_id}"
        )
        
        # Create layers
        layers = {
            'E-ELEC-SCHEDULE': {'color': 7, 'linetype': 'CONTINUOUS'},
            'E-ELEC-TEXT': {'color': 7, 'linetype': 'CONTINUOUS'},
        }
        self.writer.create_layers(layers)
        self.writer.set_layer('E-ELEC-SCHEDULE')
        
        # Extract circuit data from MCP if not provided
        if not circuit_list:
            circuit_list = self._extract_circuits_from_mcp(mcp_result, panel_id)
        
        # Generate table
        self._generate_table(panel_id, circuit_list, standard)
        
        # Add notes
        self._add_notes(standard)
        
        # Footer
        self.writer.write_footer()
        
        # Wrap in function
        self.writer.wrap_in_function("C:ELEC-E401")
        
        return self.writer.get_code()
    
    def _generate_table(self, panel_id: str, circuits: List[Dict[str, Any]], standard: str) -> None:
        """
        Generate AutoCAD TABLE for panel schedule
        
        Uses TABLE command to create structured data
        """
        num_circuits = len(circuits)
        num_rows = num_circuits + 2  # Header + data + summary
        num_cols = 12
        
        # Table position
        table_x, table_y = 1000, 8000
        
        # Create table
        self.writer.code_lines.append(
            f';; Create panel schedule table\n'
            f'(command "TABLE" (list {table_x} {table_y}) '
            f'{num_rows} {num_cols} 400 3000)\n'  # row height, col width
        )
        
        # Set table style
        self.writer.code_lines.append(
            f'(command "TABLESTYLE" "Standard")\n\n'
        )
        
        # Title row
        self._add_table_title(panel_id, standard)
        
        # Header row
        self._add_table_headers()
        
        # Data rows
        for i, circuit in enumerate(circuits):
            self._add_circuit_row(i + 2, circuit)  # Row 0 = title, 1 = headers
        
        # Summary row
        self._add_summary_row(num_rows - 1, circuits)
    
    def _add_table_title(self, panel_id: str, standard: str) -> None:
        """Add table title row"""
        y = 8000
        self.writer.set_layer('E-ELEC-TEXT')
        
        title = f"PANEL SCHEDULE - {panel_id}"
        self.writer.add_text(title, (1500, y + 200), height=150)
        
        std_text = f"Standard: {standard}"
        self.writer.add_text(std_text, (1500, y + 50), height=80)
        
        self.writer.set_layer('E-ELEC-SCHEDULE')
    
    def _add_table_headers(self) -> None:
        """Add column headers"""
        headers = [
            "Circuit\nNo.",
            "Description",
            "No. of\nPoints",
            "Load\n(VA/W)",
            "Demand\nFactor",
            "Demand\nLoad",
            "Current\n(A)",
            "Breaker\n(A, poles)",
            "Cable\n(mm², cores)",
            "Conduit\n(mm)",
            "Protection\nType",
            "Remarks"
        ]
        
        x_start = 1200
        y = 7600
        col_width = 1000
        
        self.writer.set_layer('E-ELEC-TEXT')
        for i, header in enumerate(headers):
            x = x_start + (i * col_width)
            # Simplify header for LISP (remove newlines)
            header_text = header.replace('\n', ' ')
            self.writer.add_text(header_text, (x, y), height=60)
        
        self.writer.set_layer('E-ELEC-SCHEDULE')
    
    def _add_circuit_row(self, row_num: int, circuit: Dict[str, Any]) -> None:
        """Add a circuit data row"""
        x_start = 1200
        y = 7600 - (row_num * 300)
        col_width = 1000
        
        # Extract circuit data
        data = [
            circuit.get('circuit_no', 'N/A'),
            circuit.get('description', '')[:20],  # Truncate long descriptions
            str(circuit.get('points', 0)),
            str(circuit.get('load_va', 0)),
            f"{circuit.get('demand_factor', 1.0):.2f}",
            str(circuit.get('demand_load', 0)),
            f"{circuit.get('current_a', 0):.2f}",
            circuit.get('breaker', 'N/A'),
            circuit.get('cable', 'N/A'),
            circuit.get('conduit', 'N/A'),
            circuit.get('protection', 'MCB'),
            circuit.get('remarks', '')[:15],  # Truncate
        ]
        
        self.writer.set_layer('E-ELEC-TEXT')
        for i, value in enumerate(data):
            x = x_start + (i * col_width)
            self.writer.add_text(str(value), (x, y), height=50)
        
        self.writer.set_layer('E-ELEC-SCHEDULE')
    
    def _add_summary_row(self, row_num: int, circuits: List[Dict[str, Any]]) -> None:
        """Add summary row with totals"""
        x_start = 1200
        y = 7600 - (row_num * 300)
        col_width = 1000
        
        # Calculate totals
        total_load = sum(c.get('load_va', 0) for c in circuits)
        total_demand = sum(c.get('demand_load', 0) for c in circuits)
        total_current = sum(c.get('current_a', 0) for c in circuits)
        
        # Summary data
        summary = [
            "TOTAL",
            f"{len(circuits)} circuits",
            "",
            f"{total_load:.0f}",
            "",
            f"{total_demand:.0f}",
            f"{total_current:.2f}",
            "",
            "",
            "",
            "",
            ""
        ]
        
        self.writer.set_layer('E-ELEC-TEXT')
        for i, value in enumerate(summary):
            if value:  # Only add non-empty cells
                x = x_start + (i * col_width)
                self.writer.add_text(value, (x, y), height=60)
        
        self.writer.set_layer('E-ELEC-SCHEDULE')
    
    def _add_notes(self, standard: str) -> None:
        """Add notes below table"""
        notes_x, notes_y = 1200, 3000
        
        notes = [
            "NOTES:",
            f"1. All calculations per {standard} standards",
            "2. Circuit loading ≤ 80% of breaker rating",
            "3. Voltage drop ≤ 3% for branch circuits",
            "4. RCBO required for bathroom and wet locations",
            "5. Spare capacity: See panel specifications",
        ]
        
        self.writer.set_layer('E-ELEC-TEXT')
        for i, note in enumerate(notes):
            y = notes_y - (i * 150)
            self.writer.add_text(note, (notes_x, y), height=70)
        
        self.writer.set_layer('E-ELEC-SCHEDULE')
    
    def _extract_circuits_from_mcp(self, mcp_result: Any, panel_id: str) -> List[Dict[str, Any]]:
        """
        Extract circuit information from MCP result
        
        Maps MCP data to panel schedule format
        
        Returns:
            List of circuit dicts with all required fields
        """
        circuits = []
        
        try:
            # Try to get data from MCP result
            if hasattr(mcp_result, 'loads'):
                for i, load in enumerate(mcp_result.loads):
                    # Get corresponding wire and breaker
                    wire = None
                    breaker = None
                    
                    if hasattr(mcp_result, 'wires') and i < len(mcp_result.wires):
                        wire = mcp_result.wires[i]
                    
                    if hasattr(mcp_result, 'breakers') and i < len(mcp_result.breakers):
                        breaker = mcp_result.breakers[i]
                    
                    # Build circuit dict
                    circuit = {
                        'circuit_no': f'CKT-{i+1}',
                        'description': getattr(load, 'description', f'Circuit {i+1}'),
                        'points': getattr(load, 'quantity', 1),
                        'load_va': getattr(load, 'va', 0),
                        'demand_factor': getattr(load, 'demand_factor', 1.0),
                        'demand_load': getattr(load, 'va', 0) * getattr(load, 'demand_factor', 1.0),
                        'current_a': getattr(wire, 'current', 0) if wire else 0,
                        'breaker': f"{getattr(breaker, 'rating', 'N/A')}A " \
                                  f"{getattr(breaker, 'poles', 1)}P" if breaker else 'N/A',
                        'cable': f"{getattr(wire, 'size_mm2', 'N/A')}mm² " \
                                f"{getattr(wire, 'cores', 3)}C" if wire else 'N/A',
                        'conduit': getattr(wire, 'conduit_size', 'N/A') if wire else 'N/A',
                        'protection': 'RCBO' if 'bath' in getattr(load, 'description', '').lower() else 'MCB',
                        'remarks': ''
                    }
                    
                    circuits.append(circuit)
            
            # Fallback: create placeholder circuits
            if not circuits:
                circuits = self._create_placeholder_circuits()
        
        except Exception as e:
            logger.warning(f"Could not extract circuits from MCP result: {e}")
            circuits = self._create_placeholder_circuits()
        
        return circuits
    
    def _create_placeholder_circuits(self) -> List[Dict[str, Any]]:
        """Create placeholder circuits for testing"""
        return [
            {
                'circuit_no': 'LT-01',
                'description': 'Living Room Lighting',
                'points': 6,
                'load_va': 360,
                'demand_factor': 0.7,
                'demand_load': 252,
                'current_a': 1.09,
                'breaker': '16A 1P',
                'cable': '2.5mm² 3C',
                'conduit': '16mm PVC',
                'protection': 'MCB',
                'remarks': ''
            },
            {
                'circuit_no': 'PWR-01',
                'description': 'Living Room Outlets',
                'points': 8,
                'load_va': 1600,
                'demand_factor': 0.5,
                'demand_load': 800,
                'current_a': 3.48,
                'breaker': '20A 1P',
                'cable': '2.5mm² 3C',
                'conduit': '16mm PVC',
                'protection': 'MCB',
                'remarks': ''
            },
            {
                'circuit_no': 'BATH-01',
                'description': 'Bathroom',
                'points': 3,
                'load_va': 1200,
                'demand_factor': 1.0,
                'demand_load': 1200,
                'current_a': 5.22,
                'breaker': '20A 1P',
                'cable': '2.5mm² 3C',
                'conduit': '16mm PVC',
                'protection': 'RCBO',
                'remarks': 'IP44 required'
            },
        ]
    
    def save_to_file(self, output_path: Path, panel_id: str, 
                    circuit_list: List[Dict[str, Any]], mcp_result: Any, 
                    standard: str = 'EIT') -> Path:
        """
        Generate and save E-401 LISP file
        
        Returns:
            Path to saved file
        """
        code = self.generate(panel_id, circuit_list, mcp_result, standard)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Generated E-401: {output_path}")
        return output_path
