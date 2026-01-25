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
    Updated: Added quantity for CRUD edit mode (2026-01-25).
    IMPORTANT: Keep all existing fields for backward compatibility!
    """
    # === EXISTING FIELDS (DO NOT REMOVE!) ===
    circuit_name: str
    circuit_id: str
    floor: str
    room: str
    quantity: int  # 🆕 For CRUD edit mode - number of devices
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
    Updated: Added 3-phase support fields (Sprint 4).
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
    # 🔧 Enhanced: Now includes distance value for better warnings
    # Format: [{"name": "circuit_name", "distance_m": 15.0}, ...]
    default_distance_circuits: List[Dict[str, Any]]
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
    
    # === 3-PHASE FIELDS (Sprint 4) ===
    is_three_phase: bool              # True if 3-phase system
    voltage_system: str               # "1PH-230V" or "3PH-400V"
    line_voltage_v: int               # 230 or 400
    phase_voltage_v: int              # 230 (1PH or 3PH line-to-neutral)
    # Phase balance info (only for 3-phase)
    phase_balance_l1_kw: Optional[float]  # L1 total kW
    phase_balance_l2_kw: Optional[float]  # L2 total kW
    phase_balance_l3_kw: Optional[float]  # L3 total kW
    phase_imbalance_percent: Optional[float]  # Imbalance %


# =============================================================================
# Helper Functions (from markdown_formatter.py)
# =============================================================================

def round_up(value: float, decimals: int = 0) -> float:
    """Round up to specified decimal places (ceiling)."""
    if decimals == 0:
        return math.ceil(value)
    multiplier = 10 ** decimals
    return math.ceil(value * multiplier) / multiplier


def _get_meter_sizing(demand_current: float, is_three_phase: bool = False, total_kw: float = 0) -> tuple:
    """
    [CP-3PH-DISPLAY] Get meter, main wire, and main breaker based on Thai MEA standards.
    
    Updated for 3-phase CT meter support (Sprint 8):
    - Single-phase: Direct meter up to 100A
    - 3-Phase >30kW: CT Meter required (per MEA regulation)
    
    Args:
        demand_current: Calculated demand current (A)
        is_three_phase: True if 3-phase system
        total_kw: Total connected load (kW) - used for CT determination
        
    Returns:
        Tuple of (meter_size, main_wire, main_breaker)
    """
    logger.info(f"[CP-3PH-DISPLAY] Meter sizing: I={demand_current:.1f}A, 3ph={is_three_phase}, kW={total_kw}")
    
    # [CP-3PH-DISPLAY] 3-Phase CT Meter threshold: >30kW requires CT
    if is_three_phase and total_kw > 30:
        # CT Meter required for 3-phase loads >30kW
        # CT ratio selection based on demand current
        if demand_current <= 100:
            ct_ratio = "100/5A"
            main_wire = "35 mm²"
            main_breaker = "100A/3P"
        elif demand_current <= 200:
            ct_ratio = "200/5A"
            main_wire = "70 mm²"
            main_breaker = "200A/3P"
        elif demand_current <= 400:
            ct_ratio = "400/5A"
            main_wire = "120 mm²"
            main_breaker = "400A/3P"
        else:
            ct_ratio = "600/5A"
            main_wire = "185 mm²"
            main_breaker = "630A/3P"
        
        logger.info(f"[CP-3PH-DISPLAY] CT Meter selected: CT={ct_ratio}")
        return f"CT Meter ({ct_ratio})", main_wire, main_breaker
    
    # 3-Phase direct meter (≤30kW)
    if is_three_phase:
        if demand_current <= 30:
            return "15(45)A 3PH", "10 mm²", "40A/3P"
        elif demand_current <= 50:
            return "30(100)A 3PH", "16 mm²", "63A/3P"
        elif demand_current <= 100:
            return "50(150)A 3PH", "25 mm²", "100A/3P"
        else:
            # Exceeds direct meter range → CT Meter
            logger.info("[CP-3PH-DISPLAY] Current exceeds 3PH direct meter, switching to CT")
            return f"CT Meter (200/5A)", "35 mm²", "125A/3P"
    
    # Single-phase meter sizing (existing logic)
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
        
        # 🆕 [VD-FIX] Extract floor_distances from metadata for accurate VD calculation
        floor_distances = mcp_result.get('floor_distances') or {}
        if floor_distances:
            logger.info(f"[CP-VD] Using floor_distances from RAG: {floor_distances}")
        else:
            logger.warning("[CP-VD] No floor_distances in mcp_result, will use defaults")
        
        # Calculate totals (logic from markdown_formatter.py lines 92-98)
        total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
        total_watts = round_up(total_watts)
        total_kw = round_up(total_watts / 1000, 2)
        
        demand_current = summary.get('demand_current')
        if demand_current is None:
            demand_current = total_watts / 230 if total_watts else 0
        demand_current = round_up(demand_current, 1)
        
        design_current = round_up(demand_current * 1.25, 1)
        
        # [3-PHASE] Extract phase system info from mcp_result (early detection for meter sizing)
        three_phase_data = mcp_result.get('three_phase_data') or mcp_result.get('calculations', {}).get('three_phase', {})
        is_three_phase = three_phase_data.get('is_three_phase', False)
        
        # [CP-3PH-DISPLAY] Get main equipment sizing with 3-phase parameters (Sprint 8)
        meter_size, main_wire, main_breaker = _get_meter_sizing(
            demand_current,
            is_three_phase=is_three_phase,
            total_kw=total_kw
        )
        
        # Process circuits
        circuits, default_distance_circuits = _process_circuits(
            grouped_circuits, wire_sizing, conduit_sizing, floor_distances
        )
        
        # Determine voltage system
        if is_three_phase:
            voltage_system = "3PH-400V"
            line_voltage = 400
            phase_voltage = 230
        else:
            voltage_system = "1PH-230V"
            line_voltage = 230
            phase_voltage = 230
        
        logger.info(f"[CP-3PH-DISPLAY] System: {voltage_system}, is_3phase={is_three_phase}")
        
        # Calculate summary fields (pass is_three_phase)
        summary_fields = _get_summary_fields(
            circuits, demand_current, main_breaker, main_wire,
            is_three_phase=is_three_phase,
            grouped_circuits=grouped_circuits
        )
        
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
            'default_distance_circuits': default_distance_circuits,
            'circuit_count': len(circuits),
            'warnings': warnings,
            'errors': errors,
            'phase_balance': None,
            
            # === NEW FIELDS (Summary Section) ===
            **summary_fields,
            
            # === 3-PHASE FIELDS (Sprint 4) ===
            'is_three_phase': is_three_phase,
            'voltage_system': voltage_system,
            'line_voltage_v': line_voltage,
            'phase_voltage_v': phase_voltage,
            'phase_balance_l1_kw': summary_fields.get('phase_balance_l1_kw'),
            'phase_balance_l2_kw': summary_fields.get('phase_balance_l2_kw'),
            'phase_balance_l3_kw': summary_fields.get('phase_balance_l3_kw'),
            'phase_imbalance_percent': summary_fields.get('phase_imbalance_percent'),
        }
        
        rcbo_count = summary_fields.get('rcbo_count', 0)
        mcb_count = summary_fields.get('mcb_count', 0)
        
        logger.info(f"[CP-COMPUTE] Computed: {total_kw}kW, {demand_current}A, {len(circuits)} circuits ({rcbo_count} RCBO, {mcb_count} MCB)")
        return display_data
        
    except Exception as e:
        logger.error(f"[CP-COMPUTE] Error computing display data: {e}")
        return _empty_display_data()


def _get_summary_fields(
    circuits: List[CircuitData], 
    demand_current: float, 
    main_breaker: str, 
    main_wire: str,
    is_three_phase: bool = False,
    grouped_circuits: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Calculate summary fields for professional load table.
    
    [CP-3PH-DISPLAY] Cloud logging checkpoint for 3-phase display integration.
    
    Args:
        circuits: Processed circuit data
        demand_current: Calculated demand current
        main_breaker: Main breaker string
        main_wire: Main wire size string
        is_three_phase: True if 3-phase system
        grouped_circuits: Original grouped circuits (for phase balance data)
    """
    # Total load by phase
    total_load_va = sum(c.get('total_va', 0) for c in circuits)
    
    # [3-PHASE] Calculate phase totals from grouped_circuits
    phase_balance_l1_kw = None
    phase_balance_l2_kw = None
    phase_balance_l3_kw = None
    phase_imbalance_percent = None
    
    if is_three_phase and grouped_circuits:
        logger.info("[CP-3PH-DISPLAY] Calculating 3-phase load distribution...")
        
        # Sum watts by assigned_phase
        l1_watts = 0.0
        l2_watts = 0.0
        l3_watts = 0.0
        
        for circuit in grouped_circuits:
            assigned_phase = circuit.get('assigned_phase')
            circuit_watts = circuit.get('total_watts', 0) or circuit.get('watts', 0)
            
            if assigned_phase == 'L1':
                l1_watts += circuit_watts
            elif assigned_phase == 'L2':
                l2_watts += circuit_watts
            elif assigned_phase == 'L3':
                l3_watts += circuit_watts
            else:
                # Unassigned - distribute equally (fallback)
                l1_watts += circuit_watts / 3
                l2_watts += circuit_watts / 3
                l3_watts += circuit_watts / 3
        
        phase_balance_l1_kw = round(l1_watts / 1000, 2)
        phase_balance_l2_kw = round(l2_watts / 1000, 2)
        phase_balance_l3_kw = round(l3_watts / 1000, 2)
        
        # Calculate imbalance
        values = [l1_watts, l2_watts, l3_watts]
        if sum(values) > 0:
            avg_watts = sum(values) / 3
            max_watts = max(values)
            min_watts = min(values)
            phase_imbalance_percent = round(((max_watts - min_watts) / avg_watts) * 100, 1) if avg_watts > 0 else 0.0
        
        logger.info(
            f"[CP-3PH-DISPLAY] Phase balance: L1={phase_balance_l1_kw}kW, "
            f"L2={phase_balance_l2_kw}kW, L3={phase_balance_l3_kw}kW, "
            f"imbalance={phase_imbalance_percent}%"
        )
        
        # Set phase totals for 3-phase
        total_load_va_l1 = round(l1_watts)
        total_load_va_l2 = round(l2_watts)
        total_load_va_l3 = round(l3_watts)
    else:
        # 1-phase: all in L1
        total_load_va_l1 = sum(c.get('load_va_l1', 0) for c in circuits)
        total_load_va_l2 = 0
        total_load_va_l3 = 0
    
    # Demand calculation
    demand_factor = 0.78  # Standard for residential
    demand_load_va = round_up(total_load_va * demand_factor)
    
    # Count breaker types
    rcbo_count = sum(1 for c in circuits if c.get('requires_rcbo', False))
    mcb_count = len(circuits) - rcbo_count
    
    # Main equipment details (adjust for 3-phase)
    if is_three_phase:
        main_cb_type = f"MCCB 3P {main_breaker}"
        main_cb_ic_ka = 10  # 10kA at 400V
    else:
        main_cb_type = f"MCCB 2P {main_breaker}"
        main_cb_ic_ka = 10  # 10kA at 230V
    
    main_feeder_size = main_wire.replace(' mm²', '')
    main_feeder_type = 'IEC01 (THW)'
    main_feeder_grd = f"G-{main_feeder_size} Sq.mm"
    main_raceway_type = 'PVC'
    main_raceway_size = '1"' if demand_current <= 45 else '2"'
    
    return {
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
        # [3-PHASE] Phase balance fields
        'phase_balance_l1_kw': phase_balance_l1_kw,
        'phase_balance_l2_kw': phase_balance_l2_kw,
        'phase_balance_l3_kw': phase_balance_l3_kw,
        'phase_imbalance_percent': phase_imbalance_percent,
    }


def _get_branch_distance(
    circuit: Dict,
    vd_data: Dict,
    floor_distances: Dict[str, float],
    floor_int: int,
    ckt_name: str,
    room: str
) -> tuple[float, bool]:
    """
    Determine the branch distance for a circuit.
    
    Priority:
    1. Wire sizing distance (from MCP Core calculation)
    2. Grouped circuit distance (from RAG extraction)
    3. Floor-based distance (from RAG floor map)
    4. Hardcoded defaults (15m, 25m, 35m)
    
    Returns:
        (distance_m, is_default)
    """
    # 1. Source: wire_sizing (from MCP Core)
    if isinstance(vd_data, dict) and vd_data.get('distance_m'):
        # Respect the flag from Core pipeline
        is_default = vd_data.get('used_default_distance', False)
        dist_val = float(vd_data['distance_m'])

        # 🛡️ FIX: Double check if this "default" matches User Floor Distance
        # If it matches, it is NOT a system default, it's a User Floor Default (valid)
        if is_default:
            # Check string key and int key
            user_floor_dist = floor_distances.get(str(floor_int)) or floor_distances.get(floor_int)
            if user_floor_dist and abs(dist_val - float(user_floor_dist)) < 0.1:
                logger.info(f"[CP-VD] Override default flag: {dist_val}m matches user floor {floor_int} spec")
                is_default = False
        
        return dist_val, is_default
    
    # 2. Source: grouped_circuits (from RAG service)
    dist = circuit.get('branch_distance_m') or circuit.get('distance_m')
    if dist is not None:
        return float(dist), False
    
    # 3. Source: floor_distances from RAG extraction
    # Handle known rooms that should map to Floor 1 distance defaults
    room_lower = room.lower()
    if any(k in room_lower for k in ['outdoor', 'garage', 'common', 'garden', 'ภายนอก', 'โรงรถ', 'ส่วนกลาง', 'สวน']):
        # If no explicit floor distance, use Floor 1 default logic
        # We don't return here, we let it fall through to RAG check or default
        pass

    # Try string key "1", "2" then int key 1, 2
    if str(floor_int) in floor_distances:
        d = floor_distances[str(floor_int)]
        logger.info(f"[CP-VD] Using RAG floor_distances for '{ckt_name}': {d}m (floor {floor_int})")
        return float(d), False
    elif floor_int in floor_distances:
        d = floor_distances[floor_int]
        logger.info(f"[CP-VD] Using RAG floor_distances for '{ckt_name}': {d}m (floor {floor_int})")
        return float(d), False

    # 4. Fallback: Hardcoded defaults
    floor_defaults = {1: 15.0, 2: 25.0, 3: 35.0}
    # For floors > 3, add 10m per floor
    default_dist = floor_defaults.get(floor_int, 15.0 + (floor_int - 1) * 10.0)
    
    logger.warning(f"[VD-FIX] Using floor default for '{ckt_name}': {default_dist}m (floor {floor_int})")
    return float(default_dist), True


def _process_circuits(
    grouped_circuits: List[Dict],
    wire_sizing: Dict[str, Any],
    conduit_sizing: Dict[str, Any],
    floor_distances: Optional[Dict[str, float]] = None
) -> tuple[List[CircuitData], List[Dict[str, Any]]]:
    """Process grouped_circuits into CircuitData list.
    
    Returns:
        (circuits_list, default_distance_info_list)
        default_distance_info_list: [{"name": str, "distance_m": float}, ...]
    """
    if floor_distances is None:
        floor_distances = {}
    circuits: List[CircuitData] = []
    default_circuits: List[Dict[str, Any]] = []  # Enhanced: now stores dict with distance
    
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
            
            # Room fallback
            if not room:
                room = f"ชั้น {floor_str}"
            
            # 🆕 [VD-FIX] Read VD from circuit (injected by service.py)
            # This fixes the key mismatch where wire_sizing uses load.id but we have circuit_id
            vd_percent = circuit.get('voltage_drop_percent', 2.0)
            if abs(vd_percent - 2.0) < 0.001:  # Check if using default
                logger.warning(f"[VD-WARN] Circuit '{ckt_name}' has default VD 2.0 - check injection!")
            
            # 🆕 [VD-FIX] Look up wire sizing data from constituent loads to get correct Default flag
            vd_data = {}
            # Fallback to circuit_id (legacy)
            vd_data = wire_sizing.get(circuit_id, {})
            
            # Try to match via loads (since wire_sizing is keyed by load_id)
            loads_in_circuit = circuit.get('loads', [])
            if isinstance(loads_in_circuit, list):
                for load in loads_in_circuit:
                    # If this load has wire sizing data, use it!
                    load_id = load.get('id')
                    if load_id and load_id in wire_sizing:
                        vd_data = wire_sizing[load_id]
                        break
            
            ground_size = vd_data.get('ground_size', '2.5') if isinstance(vd_data, dict) else '2.5'

            
            conduit_data = conduit_sizing.get(circuit_id, {})
            conduit_size = conduit_data.get('trade_size', '1/2"') if isinstance(conduit_data, dict) else '1/2"'
            
            # Calculate Distance
            floor_int = int(floor_str) if floor_str.isdigit() else 1
            branch_distance_m, used_default = _get_branch_distance(
                circuit, vd_data, floor_distances, floor_int, ckt_name, room
            )
            
            if used_default:
                # 🔧 Enhanced: Store both name and distance for better warnings
                default_circuits.append({
                    "name": ckt_name,
                    "distance_m": branch_distance_m
                })

            # Loads count
            num_loads = circuit.get('loads', 0)
            total_quantity = 1  # 🆕 FIX: Track total quantity for CRUD
            if isinstance(num_loads, list):
                # 🆕 FIX 2026-01-25: Sum up quantity from all loads
                total_quantity = sum(load.get('quantity', 1) for load in num_loads)
                num_loads = len(num_loads)
            
            # Notes
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
                'quantity': total_quantity,  # 🆕 FIX 2026-01-25: For CRUD edit mode
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
            
    return circuits, default_circuits

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
