"""
SLD Generator - Single Line Diagram Data Generator
Generates JSON data structure for frontend to render SLD.
Also supports SVG generation if schemdraw is available.

Professional Features:
- RCD/RCBO Sensitivity (30mA, 100mA, 300mA) based on room type
- Protection Coordination check (Ib ≤ In ≤ Iz)
- Voltage Drop display
- Cable type and installation method
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import schemdraw for optional SVG generation
try:
    import schemdraw
    import schemdraw.elements as elm
    HAS_SCHEMDRAW = True
except ImportError:
    HAS_SCHEMDRAW = False
    logger.info("schemdraw not installed. Using JSON-only mode for SLD.")


# ============================================================
# RCD/RCBO SENSITIVITY RULES (EIT/IEC 60364)
# ============================================================
class RcdSensitivity(Enum):
    """RCD sensitivity ratings per IEC 60364-4-41"""
    HIGH_30MA = 30      # Personal protection (socket, bathroom)
    MEDIUM_100MA = 100  # Additional protection
    LOW_300MA = 300     # Fire protection

# Room types that REQUIRE 30mA RCD (EIT + IEC 60364-7)
RCD_30MA_REQUIRED = {
    'bathroom', 'toilet', 'shower', 'wet_room', 'laundry',
    'outdoor', 'garage', 'carport', 'swimming_pool', 'sauna',
    'kitchen_socket',  # Socket outlets in kitchen
}

# Room types that REQUIRE RCD (any sensitivity)
RCD_REQUIRED = {
    'socket', 'receptacle', 'outlet',  # All socket circuits
    *RCD_30MA_REQUIRED
}

def get_rcd_sensitivity(room_type: str, load_type: str = None) -> Optional[int]:
    """
    Determine RCD sensitivity based on room type and load type.
    Returns mA value or None if RCD not required.
    
    EIT Standard (วสท.):
    - 30mA: ห้องน้ำ, ห้องครัว (socket), outdoor, swimming pool
    - 100mA: Additional protection for other sockets
    - 300mA: Fire protection for sub-distribution
    """
    room_lower = room_type.lower() if room_type else ''
    load_lower = load_type.lower() if load_type else ''
    
    # 30mA required zones
    if any(zone in room_lower for zone in RCD_30MA_REQUIRED):
        return 30
    
    # Socket circuits always need RCD
    if 'socket' in load_lower or 'outlet' in load_lower or 'receptacle' in load_lower:
        return 30  # EIT recommends 30mA for all sockets
    
    # Water heater
    if 'water' in load_lower and 'heater' in load_lower:
        return 30
    
    # General circuits - 100mA or no RCD
    return None


# ============================================================
# PROTECTION COORDINATION (Ib ≤ In ≤ Iz)
# ============================================================
@dataclass
class ProtectionCoordination:
    """Protection coordination check result"""
    Ib: float  # Design current (load)
    In: float  # Nominal current (breaker rating)
    Iz: float  # Cable ampacity
    is_valid: bool
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def check_protection_coordination(
    Ib: float,  # Design current
    In: float,  # Breaker rating
    Iz: float   # Cable ampacity
) -> ProtectionCoordination:
    """
    Check protection coordination per IEC 60364-4-43.
    
    Rule: Ib ≤ In ≤ Iz
    - Ib: Design current (what the load draws)
    - In: Breaker rating (what the breaker is rated for)
    - Iz: Cable ampacity (what the cable can carry)
    
    If violated: Cable overheats before breaker trips = FIRE HAZARD
    """
    is_valid = (Ib <= In) and (In <= Iz)
    
    if is_valid:
        message = f"✓ Ib({Ib:.1f}A) ≤ In({In}A) ≤ Iz({Iz:.1f}A)"
    else:
        violations = []
        if Ib > In:
            violations.append(f"Ib({Ib:.1f}A) > In({In}A) - Load exceeds breaker!")
        if In > Iz:
            violations.append(f"In({In}A) > Iz({Iz:.1f}A) - Breaker too large for cable!")
        message = "✗ " + " | ".join(violations)
    
    return ProtectionCoordination(
        Ib=Ib, In=In, Iz=Iz,
        is_valid=is_valid,
        message=message
    )


@dataclass
class SldNode:
    """Represents a node in SLD (breaker, load, etc.)"""
    id: str
    node_type: str  # 'main_breaker', 'branch_breaker', 'load', 'bus'
    label: str
    rating: str  # e.g., "32A", "16A"
    x: float  # Relative position
    y: float


@dataclass  
class SldEdge:
    """Represents a connection between nodes"""
    from_node: str
    to_node: str
    wire_size: str  # e.g., "2.5mm²"
    length_m: Optional[float] = None


@dataclass
class SldData:
    """Complete SLD data structure for frontend"""
    project_name: str
    voltage_system: str
    main_breaker: str
    total_load_kw: float
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    panels: List[Dict[str, Any]]


class SldGenerator:
    """Generate Single Line Diagram data from design calculations."""
    
    def __init__(self):
        """Initialize SLD Generator. Supports both JSON and SVG output."""
        pass

    def generate_sld_data(
        self,
        breaker_selections: Dict[str, Any],
        wire_sizing: Dict[str, Any],
        calculations: Dict[str, Any],
        project_name: str = "Residential House"
    ) -> Dict[str, Any]:
        """
        Generate SLD data structure from calculation results.
        
        Returns JSON-serializable dict that frontend can use to render SLD.
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        
        # Calculate total load
        total_load_w = 0
        for calc in calculations.values():
            if isinstance(calc, dict):
                total_load_w += calc.get('total_load_va', 0) or calc.get('power_watts', 0)
        total_load_kw = total_load_w / 1000
        
        # Determine main breaker size based on total load (EIT standard)
        if total_load_kw <= 5:
            main_breaker = "32A"
        elif total_load_kw <= 10:
            main_breaker = "50A"
        elif total_load_kw <= 15:
            main_breaker = "63A"
        else:
            main_breaker = "100A"
        
        # Create main bus node
        nodes.append({
            "id": "MAIN_BUS",
            "node_type": "bus",
            "label": "Main Bus 230V",
            "rating": "",
            "x": 0,
            "y": 0
        })
        
        # Create main breaker node
        nodes.append({
            "id": "MAIN_CB",
            "node_type": "main_breaker",
            "label": f"Main CB {main_breaker}",
            "rating": main_breaker,
            "x": 0,
            "y": 1
        })
        
        edges.append({
            "from_node": "MAIN_BUS",
            "to_node": "MAIN_CB",
            "wire_size": "10mm²",
            "length_m": 5
        })
        
        # Create branch circuits from breaker_selections
        x_offset = 0
        protection_issues = []  # Collect any Ib≤In≤Iz violations
        
        for circuit_id, breaker_data in breaker_selections.items():
            breaker_rating = breaker_data.get('rating_a', 16)
            if not isinstance(breaker_rating, (int, float)):
                breaker_rating = 16
            
            # Get wire data for this circuit
            wire_data = wire_sizing.get(circuit_id, {})
            wire_size = wire_data.get('size_mm2', 2.5)
            cable_length = wire_data.get('cable_length_m', 15)
            cable_ampacity = wire_data.get('ampacity', 0) or breaker_data.get('cable_ampacity_a', 0)
            voltage_drop_pct = wire_data.get('voltage_drop_percent', 0)
            
            # Get design current (Ib)
            design_current = breaker_data.get('design_current_a', 0) or breaker_data.get('load_current', 0)
            
            # Determine RCD sensitivity based on room/load type
            room_type = breaker_data.get('room_type', circuit_id)
            load_type = breaker_data.get('load_type', '')
            rcd_ma = get_rcd_sensitivity(room_type, load_type)
            
            # Check protection coordination (Ib ≤ In ≤ Iz)
            coord_check = None
            if design_current > 0 and cable_ampacity > 0:
                coord_check = check_protection_coordination(
                    Ib=design_current,
                    In=breaker_rating,
                    Iz=cable_ampacity
                )
                if not coord_check.is_valid:
                    protection_issues.append({
                        "circuit": circuit_id,
                        "issue": coord_check.message
                    })
            
            # Determine breaker type (MCB vs RCBO)
            breaker_type = breaker_data.get('breaker_type', 'MCB')
            if rcd_ma and 'rcbo' not in breaker_type.lower():
                breaker_type = 'RCBO'  # Upgrade to RCBO if RCD required
            
            # Branch breaker node - with RCD info
            branch_id = f"CB_{circuit_id}"
            breaker_label = f"{circuit_id} {breaker_rating}A"
            if rcd_ma:
                breaker_label += f" {rcd_ma}mA"
            
            nodes.append({
                "id": branch_id,
                "node_type": "branch_breaker",
                "label": breaker_label,
                "rating": f"{breaker_rating}A",
                "breaker_type": breaker_type,
                "rcd_sensitivity_ma": rcd_ma,
                "x": x_offset,
                "y": 2
            })
            
            # Edge with voltage drop info
            edges.append({
                "from_node": "MAIN_CB",
                "to_node": branch_id,
                "wire_size": f"{wire_size}mm²",
                "voltage_drop_pct": round(voltage_drop_pct, 2) if voltage_drop_pct else None,
                "length_m": None
            })
            
            # Load node
            load_id = f"LOAD_{circuit_id}"
            load_name = breaker_data.get('load_name', circuit_id)
            nodes.append({
                "id": load_id,
                "node_type": "load",
                "label": load_name,
                "rating": "",
                "x": x_offset,
                "y": 3
            })
            
            edges.append({
                "from_node": branch_id,
                "to_node": load_id,
                "wire_size": f"{wire_size}mm²",
                "voltage_drop_pct": round(voltage_drop_pct, 2) if voltage_drop_pct else None,
                "length_m": cable_length
            })
            
            x_offset += 1
        
        # Build panel summary for Load Schedule (Professional format)
        circuits_summary = []
        for cid, data in breaker_selections.items():
            rating = data.get('rating_a', 16)
            wire_data = wire_sizing.get(cid, {})
            
            # Get values for coordination check
            Ib = data.get('design_current_a', 0) or data.get('load_current', 0)
            Iz = wire_data.get('ampacity', 0) or data.get('cable_ampacity_a', 0)
            vd = wire_data.get('voltage_drop_percent', 0)
            
            # RCD info
            room_type = data.get('room_type', cid)
            load_type = data.get('load_type', '')
            rcd_ma = get_rcd_sensitivity(room_type, load_type)
            
            # Coordination check
            coord_ok = True
            coord_msg = ""
            if Ib > 0 and Iz > 0:
                coord = check_protection_coordination(Ib, rating, Iz)
                coord_ok = coord.is_valid
                coord_msg = coord.message
            
            circuits_summary.append({
                "id": cid,
                "breaker": f"{rating}A",
                "type": 'RCBO' if rcd_ma else data.get('breaker_type', 'MCB'),
                "rcd_ma": rcd_ma,
                "load_name": data.get('load_name', cid),
                "Ib": round(Ib, 1),  # Design current
                "In": rating,         # Nominal current (breaker)
                "Iz": round(Iz, 1),   # Cable ampacity
                "Vd%": round(vd, 2),  # Voltage drop
                "coordination_ok": coord_ok,
                "coordination_check": coord_msg,
                "wire_size": wire_data.get('size_mm2', wire_data.get('wire_size', '2.5'))
            })
        
        panels = [{
            "id": "DB-1",
            "name": "Main Distribution Board",
            "main_breaker": main_breaker,
            "voltage": "230V 1Ph",
            "total_circuits": len(breaker_selections),
            "total_load_kw": round(total_load_kw, 2),
            "circuits": circuits_summary,
            "protection_issues": protection_issues
        }]
        
        # Count RCDs and check overall coordination
        rcd_count = sum(1 for c in circuits_summary if c.get('rcd_ma'))
        all_coordinated = all(c.get('coordination_ok', True) for c in circuits_summary)
        
        return {
            "project_name": project_name,
            "voltage_system": "230V 1-Phase",
            "main_breaker": main_breaker,
            "total_load_kw": round(total_load_kw, 2),
            "nodes": nodes,
            "edges": edges,
            "panels": panels,
            # Professional summary
            "summary": {
                "total_circuits": len(breaker_selections),
                "rcd_protected_circuits": rcd_count,
                "all_coordinated": all_coordinated,
                "protection_issues_count": len(protection_issues)
            },
            "protection_issues": protection_issues,
            "format": "json",
            "svg_available": HAS_SCHEMDRAW
        }

    def generate_sld(self, panel_data: Dict[str, Any]) -> str:
        """
        Generate SLD - returns SVG if schemdraw available, else JSON string.
        
        This method is for backward compatibility with result_builder.
        """
        # If panel_data has 'circuits' key (old interface)
        if 'circuits' in panel_data:
            result = {
                "format": "json",
                "message": "SLD data for frontend rendering",
                "panel": {
                    "main_breaker": panel_data.get('main_breaker', 'Unknown'),
                    "circuits": panel_data.get('circuits', [])
                },
                "svg_available": HAS_SCHEMDRAW
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        # If schemdraw available and user wants SVG
        if HAS_SCHEMDRAW and panel_data.get('output_format') == 'svg':
            return self._generate_svg(panel_data)
        
        # Default: return JSON for frontend
        return json.dumps(panel_data, ensure_ascii=False, indent=2)
    
    def _generate_svg(self, panel_data: Dict[str, Any]) -> str:
        """Generate SVG using schemdraw library."""
        if not HAS_SCHEMDRAW:
            return '<!-- schemdraw not available -->'
            
        try:
            d = schemdraw.Drawing()
            d.config(fontsize=12)

            # Draw Main Bus
            d += elm.Line().right().length(2).label('Main Bus')
            bus_start = d.here

            # Draw Main Breaker
            main_rating = panel_data.get('main_breaker', '50A')
            d += elm.Breaker().up().label(f"Main\n{main_rating}")
            
            # Draw Branch Circuits
            circuits = panel_data.get('circuits', [])
            
            for i, circuit in enumerate(circuits):
                d.move_from(bus_start, dx=i*2, dy=0)
                d += elm.Line().down().length(1)
                d += elm.Breaker().down().label(
                    f"{circuit.get('id', f'C{i+1}')}\n{circuit.get('breaker', '16A')}"
                )
                d += elm.Line().down().length(1)
                d += elm.Dot()
                d += elm.Label().label(circuit.get('load_name', 'Load'), loc='right')

            return d.get_imagedata('svg').decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to generate SVG: {str(e)}")
            return f"<!-- Error generating SLD SVG: {str(e)} -->"
