"""
Audit Validator - Compare User-specified values vs Auto-calculated values

[CP-AUDIT] Checkpoint prefix for all audit-related logs.

This module is SEPARATE from the main formatter to keep concerns isolated.
Frontend will consume audit_results separately from load_schedule.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("Aura.Audit")


def validate_user_specs(
    grouped_circuits: List[Dict[str, Any]],
    extracted_loads: List[Dict[str, Any]],
    default_distance_circuits: List[Any] = None  # 🔧 Changed: now accepts List[Dict] or List[str]
) -> List[Dict[str, Any]]:
    """
    [CP-AUDIT] Compare user-specified values with auto-calculated values.
    Also validates system warnings like default distances.
    
    Args:
        grouped_circuits: Auto-calculated circuits from MCP Core
        extracted_loads: Loads with user_breaker/user_wire_size from LLM extraction
        default_distance_circuits: List of circuit info using default distance
            - New format: [{"name": str, "distance_m": float}, ...]
            - Old format: [str, ...] (backward compatible)
    
    Returns:
        List of audit results with PASS/FAIL status for each check
    """
    logger.info(f"[CP-AUDIT] Starting audit validation")
    logger.info(f"[CP-AUDIT] Circuits: {len(grouped_circuits)}, Loads with user specs: {sum(1 for l in extracted_loads if l.get('user_breaker') or l.get('user_wire_size'))}")
    
    audit_results = []
    
    # 🆕 1. Check Default Distances (System Audit)
    # Checks consistency with Chat Markdown Report
    if default_distance_circuits:
        logger.info(f"[CP-AUDIT] Found {len(default_distance_circuits)} circuits with default distance")
        for ckt_info in default_distance_circuits:
            # 🔧 Handle both new dict format and old string format
            if isinstance(ckt_info, dict):
                ckt_name = ckt_info.get("name", "Unknown")
                distance_m = ckt_info.get("distance_m", 15.0)
            else:
                # Backward compatibility: if it's just a string
                ckt_name = str(ckt_info)
                distance_m = 15.0  # Default
            
            audit_results.append({
                'check': f"ระยะสาย ({ckt_name})",
                'user_value': "ไม่ระบุ (Default)",
                'recommended_value': "วัดหน้างาน",
                'auto_value': f"Default {distance_m:.0f}m",
                'status': 'WARN',
                'circuit_name': ckt_name,
                'device': 'Walking Distance',
                'room': '-',
                'checks': [{
                    'item': 'Distance',
                    'user_value': f'Default {distance_m:.0f}m',
                    'auto_value': 'ควรวัดจริง',
                    'status': 'WARN',
                    'reason': f'ใช้ระยะ Default {distance_m:.0f}m (ค่าประมาณการ) อาจมีผลต่อ Voltage Drop'
                }],
                'overall_status': 'WARN'
            })

    # Build a map of device -> user specs for quick lookup
    user_specs_map = {}
    for load in extracted_loads:
        device = load.get('device', '')
        room = load.get('room_name', '')
        key = f"{room}:{device}"
        if load.get('user_breaker') or load.get('user_wire_size'):
            user_specs_map[key] = {
                'user_breaker': load.get('user_breaker'),
                'user_wire_size': load.get('user_wire_size'),
                'device': device,
                'room': room
            }
    
    if not user_specs_map:
        logger.info("[CP-AUDIT] No user-specified values found, only system audits")
        return audit_results
    
    logger.info(f"[CP-AUDIT] Found {len(user_specs_map)} loads with user specs")
    
    # Compare each circuit with user specs
    for circuit in grouped_circuits:
        circuit_name = circuit.get('circuit_name', circuit.get('name', 'Unknown'))
        auto_breaker = circuit.get('breaker_rating', 0)
        auto_wire = circuit.get('wire_size', '0')
        
        # Find matching user specs (by device type in circuit loads)
        circuit_loads = circuit.get('loads', [])
        # 🆕 FIX: Handle case where 'loads' is an integer (count) instead of a list
        if not isinstance(circuit_loads, list):
            logger.warning(f"[CP-AUDIT] Skipping circuit {circuit_name} - loads is {type(circuit_loads).__name__}, not list")
            continue
        
        for load in circuit_loads:
            device = load.get('device', load.get('name', ''))
            room = load.get('room', load.get('room_name', ''))
            key = f"{room}:{device}"
            
            if key not in user_specs_map:
                # Try matching by device only
                for spec_key, spec in user_specs_map.items():
                    if spec['device'].upper() in device.upper() or device.upper() in spec['device'].upper():
                        key = spec_key
                        break
            
            if key in user_specs_map:
                user_spec = user_specs_map[key]
                checks = []
                
                # Check breaker
                if user_spec.get('user_breaker'):
                    user_breaker = user_spec['user_breaker']
                    if user_breaker < auto_breaker:
                        checks.append({
                            'item': 'breaker',
                            'user_value': f"{user_breaker}A",
                            'auto_value': f"{auto_breaker}A",
                            'status': 'FAIL',
                            'reason': f"Breaker {user_breaker}A เล็กกว่าที่แนะนำ {auto_breaker}A"
                        })
                        logger.warning(f"[CP-AUDIT] FAIL: {circuit_name} breaker {user_breaker}A < {auto_breaker}A")
                    elif user_breaker > auto_breaker * 1.5:
                        checks.append({
                            'item': 'breaker',
                            'user_value': f"{user_breaker}A",
                            'auto_value': f"{auto_breaker}A",
                            'status': 'WARN',
                            'reason': f"Breaker {user_breaker}A ใหญ่เกินไป (แนะนำ {auto_breaker}A)"
                        })
                        logger.warning(f"[CP-AUDIT] WARN: {circuit_name} breaker {user_breaker}A >> {auto_breaker}A")
                    else:
                        checks.append({
                            'item': 'breaker',
                            'user_value': f"{user_breaker}A",
                            'auto_value': f"{auto_breaker}A",
                            'status': 'PASS',
                            'reason': 'OK'
                        })
                        logger.info(f"[CP-AUDIT] PASS: {circuit_name} breaker {user_breaker}A >= {auto_breaker}A")
                
                # Check wire size
                if user_spec.get('user_wire_size'):
                    user_wire = user_spec['user_wire_size']
                    try:
                        user_wire_float = float(user_wire.replace('mm²', '').replace('mm', '').strip())
                        auto_wire_float = float(str(auto_wire).replace('mm²', '').replace('mm', '').strip())
                        
                        if user_wire_float < auto_wire_float:
                            checks.append({
                                'item': 'wire_size',
                                'user_value': f"{user_wire}mm²",
                                'auto_value': f"{auto_wire}mm²",
                                'status': 'FAIL',
                                'reason': f"สาย {user_wire}mm² เล็กกว่าที่แนะนำ {auto_wire}mm²"
                            })
                            logger.warning(f"[CP-AUDIT] FAIL: {circuit_name} wire {user_wire} < {auto_wire}")
                        else:
                            checks.append({
                                'item': 'wire_size',
                                'user_value': f"{user_wire}mm²",
                                'auto_value': f"{auto_wire}mm²",
                                'status': 'PASS',
                                'reason': 'OK'
                            })
                            logger.info(f"[CP-AUDIT] PASS: {circuit_name} wire {user_wire} >= {auto_wire}")
                    except ValueError:
                        logger.error(f"[CP-AUDIT] Cannot parse wire sizes: user={user_wire}, auto={auto_wire}")
                
                # 🆕 Check VD% if user specified distance
                if user_spec.get('user_vd_percent'):
                    try:
                        user_vd = float(user_spec['user_vd_percent'])
                        # VD should not exceed 3% for branch circuits (วสท. 2564)
                        if user_vd > 3.0:
                            checks.append({
                                'item': 'VD%',
                                'user_value': f"{user_vd:.1f}%",
                                'auto_value': '≤3.0%',
                                'status': 'FAIL',
                                'reason': f"VD {user_vd:.1f}% เกินมาตรฐาน 3%"
                            })
                            logger.warning(f"[CP-AUDIT] FAIL: {circuit_name} VD {user_vd}% > 3%")
                        else:
                            checks.append({
                                'item': 'VD%',
                                'user_value': f"{user_vd:.1f}%",
                                'auto_value': '≤3.0%',
                                'status': 'PASS',
                                'reason': 'OK'
                            })
                            logger.info(f"[CP-AUDIT] PASS: {circuit_name} VD {user_vd}% <= 3%")
                    except (ValueError, TypeError) as e:
                        logger.error(f"[CP-AUDIT] Cannot parse VD%: {e}")
                
                if checks:
                    overall_status = 'FAIL' if any(c['status'] == 'FAIL' for c in checks) else \
                                    ('WARN' if any(c['status'] == 'WARN' for c in checks) else 'PASS')
                    audit_results.append({
                        'circuit_name': circuit_name,
                        'device': device,
                        'room': room,
                        'checks': checks,
                        'overall_status': overall_status
                    })
    
    logger.info(f"[CP-AUDIT] Audit complete: {len(audit_results)} items checked")
    fail_count = sum(1 for r in audit_results if r['overall_status'] == 'FAIL')
    warn_count = sum(1 for r in audit_results if r['overall_status'] == 'WARN')
    pass_count = sum(1 for r in audit_results if r['overall_status'] == 'PASS')
    logger.info(f"[CP-AUDIT] Results: {pass_count} PASS, {warn_count} WARN, {fail_count} FAIL")
    
    return audit_results
