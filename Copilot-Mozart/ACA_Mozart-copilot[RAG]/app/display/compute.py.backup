"""
Compute Module - Single Source of Truth for Display Data

This module centralizes all display-related calculations.
Other renderers (markdown, audit, sld, boq) should READ from DisplayData, NOT calculate.

[CP-COMPUTE] Checkpoint prefix for all compute-related logs.

Design Pattern:
- Single Source of Truth: All calculations happen HERE
- Compute Once, Render Many: DisplayData is computed once, used by all renderers
- Type Safety: DisplayData is a TypedDict for clear contract

Input: mcp_result from mcp_response.to_dict()
Output: DisplayData dict for all renderers
"""

import math
import logging
from typing import Dict, Any, List, Optional, TypedDict

logger = logging.getLogger("Aura.Display.Compute")


# =============================================================================
# Type Definitions (Contract)
# =============================================================================

class CircuitData(TypedDict):
    """Single circuit data for display."""
    circuit_name: str
    circuit_id: str
    floor: str
    room: str
    total_watts: float
    total_kw: float
    total_current: float
    breaker_rating: int
    breaker_poles: int
    breaker_type: str
    wire_size: str
    ground_size: str
    conduit_size: str
    vd_percent: float
    requires_rcbo: bool
    num_loads: int
    notes: List[str]


class DisplayData(TypedDict):
    """Complete display data - Source of Truth for all renderers."""
    # Project Info
    project_name: str
    
    # Totals (calculated once)
    total_watts: float
    total_kw: float
    demand_current: float
    design_current: float  # demand_current × 1.25
    
    # Main Equipment (calculated once)
    meter_size: str
    main_wire: str
    main_breaker: str
    
    # Circuits
    circuits: List[CircuitData]
    circuit_count: int
    
    # Warnings & Errors
    warnings: List[str]
    errors: List[str]
    
    # Phase Balance (optional)
    phase_balance: Optional[Dict[str, float]]


# =============================================================================
# Helper Functions (from markdown_formatter.py)
# =============================================================================

def round_up(value: float, decimals: int = 0) -> float:
    """Round up to specified decimal places (ceiling)."""
    if decimals == 0:
        return math.ceil(value)
    multiplier = 10 ** decimals
    return math.ceil(value * multiplier) / multiplier


def _get_meter_sizing(demand_current: float) -> tuple:
    """
    Get meter, main wire, and main breaker based on Thai MEA standards.
    
    Logic moved from markdown_formatter.py lines 129-145.
    """
    if demand_current <= 15:
        return "5(15)A", "4 mm²", "16A/1P"
    elif demand_current <= 45:
        return "15(45)A", "10 mm²", "50A/2P"
    elif demand_current <= 100:
        return "30(100)A", "25 mm²", "100A/2P"
    else:
        return "CT Meter", "50 mm²", "125A/2P"


# =============================================================================
# Main Compute Function
# =============================================================================

def compute_display_data(mcp_result: Dict[str, Any]) -> DisplayData:
    """
    [CP-COMPUTE] Compute all display data from MCP result.
    
    This is the SINGLE SOURCE OF TRUTH for all display calculations.
    All renderers (markdown, audit, sld, boq) should use this output.
    
    Args:
        mcp_result: Dict from mcp_response.to_dict() - contains:
            - project_name
            - summary (total_watts, demand_current)
            - grouped_circuits (list of circuits)
            - wire_sizing
            - conduit_sizing
            - warnings, errors
    
    Returns:
        DisplayData: Complete structured data for all renderers
    """
    logger.info("[CP-COMPUTE] Computing display data...")
    
    # Handle None input
    if mcp_result is None:
        logger.error("[CP-COMPUTE] mcp_result is None!")
        return _empty_display_data()
    
    try:
        # Extract base data
        project_name = mcp_result.get('project_name', 'ไม่ระบุ')
        summary = mcp_result.get('summary') or {}
        grouped_circuits = mcp_result.get('grouped_circuits') or []
        wire_sizing = mcp_result.get('wire_sizing') or {}
        conduit_sizing = mcp_result.get('conduit_sizing') or {}
        warnings = mcp_result.get('warnings') or []
        errors = mcp_result.get('errors') or []
        
        # Calculate totals (logic from markdown_formatter.py lines 92-98)
        total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
        total_watts = round_up(total_watts)
        total_kw = round_up(total_watts / 1000, 2)
        
        demand_current = summary.get('demand_current')
        if demand_current is None:
            demand_current = total_watts / 230 if total_watts else 0
        demand_current = round_up(demand_current, 1)
        
        design_current = round_up(demand_current * 1.25, 1)
        
        # Get main equipment sizing
        meter_size, main_wire, main_breaker = _get_meter_sizing(demand_current)
        
        # Process circuits
        circuits = _process_circuits(grouped_circuits, wire_sizing, conduit_sizing)
        
        display_data: DisplayData = {
            'project_name': project_name,
            'total_watts': total_watts,
            'total_kw': total_kw,
            'demand_current': demand_current,
            'design_current': design_current,
            'meter_size': meter_size,
            'main_wire': main_wire,
            'main_breaker': main_breaker,
            'circuits': circuits,
            'circuit_count': len(circuits),
            'warnings': warnings,
            'errors': errors,
            'phase_balance': None,  # TODO: Add phase balance calculation
        }
        
        logger.info(f"[CP-COMPUTE] Computed: {total_kw}kW, {demand_current}A, {len(circuits)} circuits")
        return display_data
        
    except Exception as e:
        logger.error(f"[CP-COMPUTE] Error computing display data: {e}")
        return _empty_display_data()


def _process_circuits(
    grouped_circuits: List[Dict],
    wire_sizing: Dict[str, Any],
    conduit_sizing: Dict[str, Any]
) -> List[CircuitData]:
    """Process grouped_circuits into CircuitData list."""
    circuits: List[CircuitData] = []
    
    for circuit in grouped_circuits:
        try:
            ckt_name = circuit.get('circuit_name', circuit.get('name', 'Unknown'))
            circuit_id = circuit.get('circuit_id') or circuit.get('id') or ckt_name
            
            total_watts = circuit.get('total_watts', 0)
            total_current = circuit.get('total_current', 0)
            
            # Get VD% from wire_sizing
            vd_data = wire_sizing.get(circuit_id, {})
            vd_percent = vd_data.get('voltage_drop_percent', 2.0) if isinstance(vd_data, dict) else 2.0
            ground_size = vd_data.get('ground_size', '2.5') if isinstance(vd_data, dict) else '2.5'
            
            # Get conduit from conduit_sizing
            conduit_data = conduit_sizing.get(circuit_id, {})
            conduit_size = conduit_data.get('trade_size', '1/2"') if isinstance(conduit_data, dict) else '1/2"'
            
            # Handle loads count
            num_loads = circuit.get('loads', 0)
            if isinstance(num_loads, list):
                num_loads = len(num_loads)
            
            circuit_data: CircuitData = {
                'circuit_name': ckt_name,
                'circuit_id': circuit_id,
                'floor': str(circuit.get('floor', '1')),
                'room': circuit.get('room', ''),
                'total_watts': round_up(total_watts),
                'total_kw': round_up(total_watts / 1000, 2),
                'total_current': round_up(total_current, 1),
                'breaker_rating': circuit.get('breaker_rating', 15),
                'breaker_poles': circuit.get('breaker_poles', 1),
                'breaker_type': 'RCBO' if circuit.get('requires_rcbo') else 'MCB',
                'wire_size': str(circuit.get('wire_size', '2.5')),
                'ground_size': ground_size,
                'conduit_size': conduit_size,
                'vd_percent': round_up(vd_percent, 1),
                'requires_rcbo': circuit.get('requires_rcbo', False),
                'num_loads': num_loads,
                'notes': circuit.get('notes', []),
            }
            
            circuits.append(circuit_data)
            
        except Exception as e:
            logger.warning(f"[CP-COMPUTE] Error processing circuit: {e}")
            continue
    
    return circuits


def _empty_display_data() -> DisplayData:
    """Return empty DisplayData for fallback."""
    return {
        'project_name': 'ไม่ระบุ',
        'total_watts': 0,
        'total_kw': 0,
        'demand_current': 0,
        'design_current': 0,
        'meter_size': '-',
        'main_wire': '-',
        'main_breaker': '-',
        'circuits': [],
        'circuit_count': 0,
        'warnings': [],
        'errors': ['No data available'],
        'phase_balance': None,
    }
