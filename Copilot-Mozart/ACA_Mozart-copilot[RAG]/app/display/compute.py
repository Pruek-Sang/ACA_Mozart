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
# NOTE: Do NOT remove existing fields! Only ADD new ones.
# =============================================================================

class CircuitData(TypedDict):
    """Single circuit data for display.
    
    Updated: Added professional load table fields.
    IMPORTANT: Keep all existing fields for backward compatibility!
    """
    # === EXISTING FIELDS (DO NOT REMOVE!) ===
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
    branch_distance_m: Optional[float]   # 🆕 Branch distance from MDB to load
    requires_rcbo: bool
    num_loads: int
    notes: List[str]
    
    # === NEW FIELDS (Professional Load Table) ===
    circuit_no: int                  # CCT No. (1, 2, 3...)
    
    # Connection Load (VA) - 3-phase ready
    load_va_l1: float                # Phase L1 (for 1-phase: all here)
    load_va_l2: float                # Phase L2 (0 for 1-phase)
    load_va_l3: float                # Phase L3 (0 for 1-phase)
    total_va: float                  # Total VA
    
    # Circuit Breaker Details
    breaker_ic_ka: int               # kA rating (6, 10, 15)
    breaker_af: int                  # Frame size (AF)
    breaker_at: int                  # Trip rating (AT) = breaker_rating
    
    # Wire/Cable Details
    wire_size_l: str                 # Line wire (copy of wire_size)
    wire_size_n: str                 # Neutral wire
    wire_size_grd: str               # Ground wire (copy of ground_size)
    wire_type: str                   # IEC01 (THW)
    
    # Raceway Details
    conduit_type: str                # PVC / EMT / IMC
    
    # Summary
    remark: str                      # Combined notes as string


class DisplayData(TypedDict):
    """Complete display data - Source of Truth for all renderers.
    
    Updated: Added summary section fields for professional load table.
    IMPORTANT: Keep all existing fields for backward compatibility!
    """
    # === EXISTING FIELDS (DO NOT REMOVE!) ===
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
    
    # === NEW FIELDS (Summary Section) ===
    # Total Load by Phase
    total_load_va: float              # Total VA
    total_load_va_l1: float           # Phase L1 total
    total_load_va_l2: float           # Phase L2 total
    total_load_va_l3: float           # Phase L3 total
    
    # Demand Calculation
    demand_factor: float              # 0.78 etc.
    demand_load_va: float             # After demand factor
    
    # Main Equipment Details
    main_cb_type: str                 # MCCB 3P 100AF/100AT
    main_cb_ic_ka: int                # 10kA at 400V
    main_feeder_size: str             # 50 Sq.mm
    main_feeder_type: str             # IEC01 (THW)
    main_feeder_grd: str              # G-16 Sq.mm
    main_raceway_type: str            # IMC / PVC / EMT
    main_raceway_size: str            # 2"
    
    # Audit Summary
    rcbo_count: int                   # Count of RCBO circuits
    mcb_count: int                    # Count of MCB circuits


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
        
        # === NEW: Calculate summary fields ===
        # Total load by phase (1-phase: all in L1)
        total_load_va = sum(c.get('total_va', 0) for c in circuits)
        total_load_va_l1 = sum(c.get('load_va_l1', 0) for c in circuits)
        total_load_va_l2 = 0  # 0 for 1-phase
        total_load_va_l3 = 0  # 0 for 1-phase
        
        # Demand calculation
        demand_factor = 0.78  # Standard for residential
        demand_load_va = round_up(total_load_va * demand_factor)
        
        # Count breaker types
        rcbo_count = sum(1 for c in circuits if c.get('requires_rcbo', False))
        mcb_count = len(circuits) - rcbo_count
        
        # Main equipment details
        main_cb_type = f"MCCB 2P {main_breaker}"
        main_cb_ic_ka = 10  # 10kA at 230V
        main_feeder_size = main_wire.replace(' mm²', '')
        main_feeder_type = 'IEC01 (THW)'
        main_feeder_grd = f"G-{main_feeder_size} Sq.mm"
        main_raceway_type = 'PVC'
        main_raceway_size = '1"' if demand_current <= 45 else '2"'
        
        display_data: DisplayData = {
            # === EXISTING FIELDS ===
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
            'phase_balance': None,
            
            # === NEW FIELDS (Summary Section) ===
            'total_load_va': total_load_va,
            'total_load_va_l1': total_load_va_l1,
            'total_load_va_l2': total_load_va_l2,
            'total_load_va_l3': total_load_va_l3,
            'demand_factor': demand_factor,
            'demand_load_va': demand_load_va,
            'main_cb_type': main_cb_type,
            'main_cb_ic_ka': main_cb_ic_ka,
            'main_feeder_size': main_feeder_size,
            'main_feeder_type': main_feeder_type,
            'main_feeder_grd': main_feeder_grd,
            'main_raceway_type': main_raceway_type,
            'main_raceway_size': main_raceway_size,
            'rcbo_count': rcbo_count,
            'mcb_count': mcb_count,
        }
        
        logger.info(f"[CP-COMPUTE] Computed: {total_kw}kW, {demand_current}A, {len(circuits)} circuits ({rcbo_count} RCBO, {mcb_count} MCB)")
        return display_data
        
    except Exception as e:
        logger.error(f"[CP-COMPUTE] Error computing display data: {e}")
        return _empty_display_data()


def _process_circuits(
    grouped_circuits: List[Dict],
    wire_sizing: Dict[str, Any],
    conduit_sizing: Dict[str, Any]
) -> List[CircuitData]:
    """Process grouped_circuits into CircuitData list.
    
    Updated: Now includes professional load table fields.
    """
    circuits: List[CircuitData] = []
    
    for idx, circuit in enumerate(grouped_circuits, start=1):
        try:
            ckt_name = circuit.get('circuit_name', circuit.get('name', 'Unknown'))
            circuit_id = circuit.get('circuit_id') or circuit.get('id') or ckt_name
            
            total_watts = circuit.get('total_watts', 0)
            total_current = circuit.get('total_current', 0)
            breaker_rating = circuit.get('breaker_rating', 15)
            breaker_poles = circuit.get('breaker_poles', 1)
            wire_size = str(circuit.get('wire_size', '2.5'))
            requires_rcbo = circuit.get('requires_rcbo', False)
            floor_str = str(circuit.get('floor', '1'))
            room = circuit.get('room', '')
            
            # Room fallback: if empty, use floor + circuit type
            if not room:
                room = f"ชั้น {floor_str}"
            
            # Get VD% and distance from wire_sizing
            vd_data = wire_sizing.get(circuit_id, {})
            vd_percent = vd_data.get('voltage_drop_percent', 2.0) if isinstance(vd_data, dict) else 2.0
            ground_size = vd_data.get('ground_size', '2.5') if isinstance(vd_data, dict) else '2.5'
            # 🆕 Extract branch_distance_m from MCP Core wire_result
            branch_distance_m = vd_data.get('distance_m') if isinstance(vd_data, dict) else None
            
            # Get conduit from conduit_sizing
            conduit_data = conduit_sizing.get(circuit_id, {})
            conduit_size = conduit_data.get('trade_size', '1/2"') if isinstance(conduit_data, dict) else '1/2"'
            
            # Handle loads count
            num_loads = circuit.get('loads', 0)
            if isinstance(num_loads, list):
                num_loads = len(num_loads)
            
            # Notes handling
            notes = circuit.get('notes', [])
            remark = '; '.join(notes) if notes else ''
            
            circuit_data: CircuitData = {
                # === EXISTING FIELDS (unchanged) ===
                'circuit_name': ckt_name,
                'circuit_id': circuit_id,
                'floor': floor_str,
                'room': room,
                'total_watts': round_up(total_watts),
                'total_kw': round_up(total_watts / 1000, 2),
                'total_current': round_up(total_current, 1),
                'breaker_rating': breaker_rating,
                'breaker_poles': breaker_poles,
                'breaker_type': 'RCBO' if requires_rcbo else 'MCB',
                'wire_size': wire_size,
                'ground_size': ground_size,
                'conduit_size': conduit_size,
                'vd_percent': round_up(vd_percent, 1),
                'branch_distance_m': branch_distance_m,  # 🆕 From MCP Core wire_result
                'requires_rcbo': requires_rcbo,
                'num_loads': num_loads,
                'notes': notes,
                
                # === NEW FIELDS (Professional Load Table) ===
                'circuit_no': idx,  # CCT No. from enumerate
                
                # Connection Load (VA) - 1-phase: all in L1
                'load_va_l1': round_up(total_watts),  # All in L1 for 1-phase
                'load_va_l2': 0,  # 0 for 1-phase
                'load_va_l3': 0,  # 0 for 1-phase
                'total_va': round_up(total_watts),
                
                # Circuit Breaker Details
                'breaker_ic_ka': 6,  # Default 6kA for residential
                'breaker_af': breaker_rating,  # AF = AT for residential MCB
                'breaker_at': breaker_rating,  # AT = rating
                
                # Wire/Cable Details (copy from existing for compatibility)
                'wire_size_l': wire_size,  # Same as wire_size
                'wire_size_n': wire_size,  # Same for 1-phase
                'wire_size_grd': ground_size,  # Same as ground_size
                'wire_type': 'IEC01 (THW)',  # Standard for Thai
                
                # Raceway Details
                'conduit_type': 'PVC',  # Default for residential
                
                # Summary
                'remark': remark,
            }
            
            circuits.append(circuit_data)
            
        except Exception as e:
            logger.warning(f"[CP-COMPUTE] Error processing circuit: {e}")
            continue
    
    return circuits


def _empty_display_data() -> DisplayData:
    """Return empty DisplayData for fallback.
    
    IMPORTANT: Include all fields (existing + new) to prevent KeyError.
    """
    return {
        # === EXISTING FIELDS ===
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
        
        # === NEW FIELDS (with fallback defaults) ===
        'total_load_va': 0,
        'total_load_va_l1': 0,
        'total_load_va_l2': 0,
        'total_load_va_l3': 0,
        'demand_factor': 0.78,
        'demand_load_va': 0,
        'main_cb_type': '-',
        'main_cb_ic_ka': 0,
        'main_feeder_size': '-',
        'main_feeder_type': '-',
        'main_feeder_grd': '-',
        'main_raceway_type': '-',
        'main_raceway_size': '-',
        'rcbo_count': 0,
        'mcb_count': 0,
    }
