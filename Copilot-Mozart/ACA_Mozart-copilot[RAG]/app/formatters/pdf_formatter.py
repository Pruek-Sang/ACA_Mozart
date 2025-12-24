"""
PDF Formatter - Professional Load Schedule Table

Generates PDF-ready structured data matching Pasted image.png format.
This is SEPARATE from markdown_formatter to keep display logic isolated.

Columns: รายการ | Pole | kW | R | Y | B | N | สาย | CB | Contactor

[PDF-FMT] Checkpoint prefix for all PDF formatting logs.
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from .base_formatter import BaseFormatter

logger = logging.getLogger("Aura.PDFFormatter")


@dataclass
class PhaseBalancer:
    """Round-robin phase assignment with debug logging."""
    
    phase_totals: Dict[str, float] = field(default_factory=lambda: {'R': 0.0, 'Y': 0.0, 'B': 0.0})
    assignments: List[Dict] = field(default_factory=list)
    
    def assign(self, load_kw: float, circuit_name: str) -> str:
        """Assign load to phase with lowest total (round-robin balance)."""
        try:
            min_phase = min(self.phase_totals, key=self.phase_totals.get)
            self.phase_totals[min_phase] += load_kw
            
            # 🆕 Debug logging for phase balance tracking
            logger.debug(
                f"[PHASE-DEBUG] Assigned '{circuit_name}' ({load_kw:.2f}kW) to Phase {min_phase} | "
                f"Totals: R={self.phase_totals['R']:.2f}, Y={self.phase_totals['Y']:.2f}, B={self.phase_totals['B']:.2f}"
            )
            
            self.assignments.append({
                'circuit': circuit_name,
                'kw': load_kw,
                'phase': min_phase
            })
            
            return min_phase
        except Exception as e:
            logger.error(f"[PHASE-DEBUG] Error assigning phase: {e}")
            return 'R'  # Fallback to phase R
    
    def get_summary(self) -> Dict[str, float]:
        """Get phase balance summary for floor totals."""
        return self.phase_totals.copy()


# Circuit types that need contactor
CONTACTOR_CIRCUIT_TYPES = ['MOTOR', 'AIR_CONDITIONER', 'PUMP']
CONTACTOR_KEYWORDS = ['PUMP', 'ปั๊ม', 'แอร์', 'AC', 'MOTOR']


class PdfFormatter(BaseFormatter):
    """Formats MCP design results as PDF-ready structured data."""
    
    def get_format_type(self) -> str:
        return "pdf"
    
    def format(self, mcp_result: Dict[str, Any]) -> str:
        """Generate markdown preview of PDF table."""
        return format_pdf_markdown(mcp_result)


def format_pdf_table(mcp_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format MCP result into structured data for PDF export.
    
    Returns dict with:
    - project_info: Project metadata
    - floors: List of floor data with circuits
    - main_equipment: Main breaker/wire/meter info
    - summary: Totals and phase balance
    
    This data can be used by:
    - reportlab (PDF generation)
    - openpyxl (Excel export)
    - Frontend table renderer
    """
    logger.info("[PDF-FMT] Starting PDF format")
    
    try:
        # Extract data from mcp_result
        project_name = mcp_result.get('project_name', 'ไม่ระบุ')
        summary = mcp_result.get('summary') or {}
        grouped_circuits = mcp_result.get('grouped_circuits') or []
        wire_sizing = mcp_result.get('wire_sizing') or {}
        
        # Create phase balancer
        balancer = PhaseBalancer()
        
        # Group circuits by floor
        floors_data: Dict[str, List[Dict]] = {}
        
        for circuit in grouped_circuits:
            try:
                floor = str(circuit.get('floor', '1'))
                if floor not in floors_data:
                    floors_data[floor] = []
                
                # Get circuit info
                ckt_name = circuit.get('circuit_name', circuit.get('name', 'Unknown'))
                total_watts = circuit.get('total_watts', 0)
                total_kw = total_watts / 1000
                breaker_rating = circuit.get('breaker_rating', 15)
                breaker_poles = circuit.get('breaker_poles', 1)
                wire_size = circuit.get('wire_size', '2.5')
                circuit_type = str(circuit.get('circuit_type', ''))
                
                # Get VD% from wire_sizing
                circuit_id = circuit.get('circuit_id') or circuit.get('id') or ckt_name
                vd_data = wire_sizing.get(circuit_id, {})
                vd = vd_data.get('voltage_drop_percent', 2.0) if isinstance(vd_data, dict) else 2.0
                
                # Assign phase (round-robin)
                assigned_phase = balancer.assign(total_kw, ckt_name)
                
                # Determine contactor requirement
                needs_contactor = (
                    circuit_type.upper() in CONTACTOR_CIRCUIT_TYPES or
                    any(kw in ckt_name.upper() for kw in CONTACTOR_KEYWORDS)
                )
                contactor = 'MCP' if needs_contactor else '-'
                
                # Build row
                row = {
                    'name': ckt_name,
                    'pole': breaker_poles,
                    'kw': round(total_kw, 2),
                    'phase': assigned_phase,
                    'R': round(total_kw, 2) if assigned_phase == 'R' else '-',
                    'Y': round(total_kw, 2) if assigned_phase == 'Y' else '-',
                    'B': round(total_kw, 2) if assigned_phase == 'B' else '-',
                    'N': round(total_kw, 2),  # Neutral carries same as phase for 1-phase loads
                    'wire': f"{wire_size}mm²",
                    'cb': f"{breaker_rating}A/{breaker_poles}P",
                    'contactor': contactor,
                    'vd_percent': vd
                }
                
                floors_data[floor].append(row)
                
            except Exception as e:
                logger.error(f"[PDF-FMT] Error processing circuit: {e}")
                continue
        
        # Build floor summaries
        floors_list = []
        for floor_num in sorted(floors_data.keys(), key=lambda x: (x.isdigit(), int(x) if x.isdigit() else 999)):
            floor_circuits = floors_data[floor_num]
            floor_total_kw = sum(c['kw'] for c in floor_circuits)
            
            floor_summary = {
                'floor': floor_num,
                'display_name': f"ชั้น {floor_num}" if floor_num.isdigit() else floor_num,
                'circuits': floor_circuits,
                'total_kw': round(floor_total_kw, 2)
            }
            floors_list.append(floor_summary)
        
        # Main equipment
        total_watts = summary.get('total_watts', 0)
        demand_current = summary.get('demand_current', total_watts / 230 if total_watts else 0)
        
        main_equipment = _get_main_equipment(demand_current)
        
        # Build result
        result = {
            'project_info': {
                'name': project_name,
                'total_kw': round(total_watts / 1000, 2),
                'demand_current': round(demand_current, 1),
                'design_current': round(demand_current * 1.25, 1)
            },
            'floors': floors_list,
            'main_equipment': main_equipment,
            'phase_balance': balancer.get_summary(),
            'phase_assignments': balancer.assignments
        }
        
        logger.info(f"[PDF-FMT] Format complete: {len(grouped_circuits)} circuits, {len(floors_list)} floors")
        return result
        
    except Exception as e:
        logger.error(f"[PDF-FMT] Error formatting PDF data: {e}")
        # Return minimal fallback
        return {
            'error': str(e),
            'project_info': {'name': 'Error', 'total_kw': 0},
            'floors': [],
            'main_equipment': {},
            'phase_balance': {'R': 0, 'Y': 0, 'B': 0}
        }


def _get_main_equipment(demand_current: float) -> Dict[str, str]:
    """Get main equipment sizing based on demand current (Thai MEA standards)."""
    try:
        if demand_current <= 15:
            return {'meter': '5(15)A', 'main_wire': 'THW 4mm²', 'main_breaker': '16A 2P'}
        elif demand_current <= 45:
            return {'meter': '15(45)A', 'main_wire': 'THW 6mm²', 'main_breaker': '32A 2P'}
        elif demand_current <= 100:
            return {'meter': '30(100)A', 'main_wire': 'THW 16mm²', 'main_breaker': '63A 2P'}
        else:
            return {'meter': 'CT Meter', 'main_wire': 'THW 35mm²', 'main_breaker': '100A 2P'}
    except Exception as e:
        logger.error(f"[PDF-FMT] Error getting main equipment: {e}")
        return {'meter': 'Error', 'main_wire': 'Error', 'main_breaker': 'Error'}


def format_pdf_markdown(mcp_result: Dict[str, Any]) -> str:
    """
    Generate Markdown representation of the PDF table.
    
    This is for preview in chat - actual PDF uses format_pdf_table().
    """
    logger.info("[PDF-FMT] Generating PDF preview markdown")
    
    try:
        data = format_pdf_table(mcp_result)
        
        if 'error' in data:
            return f"❌ Error generating PDF: {data['error']}"
        
        lines = [
            "## 📄 PDF Preview (ตารางอุปกรณ์ไฟฟ้า)",
            "",
            "| รายการ | Pole | kW | R | Y | B | N | สาย | CB | Contactor |",
            "|--------|:----:|---:|--:|--:|--:|--:|-----|----:|-----------|",
        ]
        
        for floor in data.get('floors', []):
            # Floor header
            lines.append(f"| **{floor['display_name']}** | | | | | | | | | |")
            
            for circuit in floor.get('circuits', []):
                name = circuit['name'][:20] + "..." if len(circuit['name']) > 23 else circuit['name']
                lines.append(
                    f"| {name} | {circuit['pole']} | {circuit['kw']:.2f} | "
                    f"{circuit['R']} | {circuit['Y']} | {circuit['B']} | {circuit['N']} | "
                    f"{circuit['wire']} | {circuit['cb']} | {circuit['contactor']} |"
                )
            
            # Floor summary
            lines.append(f"| **รวม {floor['display_name']}** | | **{floor['total_kw']:.2f}** | | | | | | | |")
        
        # Phase balance summary
        pb = data.get('phase_balance', {})
        lines.extend([
            "",
            "### Phase Balance",
            f"- R: {pb.get('R', 0):.2f} kW",
            f"- Y: {pb.get('Y', 0):.2f} kW",
            f"- B: {pb.get('B', 0):.2f} kW",
        ])
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"[PDF-FMT] Error generating markdown: {e}")
        return f"❌ Error generating PDF preview: {e}"


# Export function for API endpoint
def export_to_pdf(mcp_result: Dict[str, Any], output_path: str = None) -> Dict[str, Any]:
    """
    Export MCP result to PDF-ready data.
    
    Args:
        mcp_result: Dictionary from MCP Core
        output_path: Optional path for future PDF file generation
        
    Returns:
        Structured data for PDF generation
    """
    return format_pdf_table(mcp_result)
