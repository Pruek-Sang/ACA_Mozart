"""
Placement Validator - Validate device placement accuracy

Calculates accuracy by comparing placed devices against golden templates.
Target: ≥90% accuracy (within ±100mm tolerance)
"""

import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)

Point = Tuple[float, float]


# Golden layout templates for accuracy validation
GOLDEN_LAYOUTS = {
    'bedroom_4x6': {
        'room_type': 'bedroom',
        'polygon': [(0, 0), (4000, 0), (4000, 6000), (0, 6000)],
        'outlets': [
            {'position': (1000, 0), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (3000, 0), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (4000, 2000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (4000, 4000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (2000, 6000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (0, 3000), 'tolerance_mm': 100, 'type': 'outlet'},
        ],
        'lights': [
            {'position': (2000, 2000), 'tolerance_mm': 200, 'type': 'light'},
            {'position': (2000, 4000), 'tolerance_mm': 200, 'type': 'light'},
        ],
        'switches': [
            {'position': (3050, 100), 'tolerance_mm': 150, 'type': 'switch'},
        ]
    },
    
    'living_6x8': {
        'room_type': 'living',
        'polygon': [(0, 0), (6000, 0), (6000, 8000), (0, 8000)],
        'outlets': [
            {'position': (1500, 0), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (4500, 0), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (6000, 2000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (6000, 4000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (6000, 6000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (4500, 8000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (1500, 8000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (0, 6000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (0, 4000), 'tolerance_mm': 100, 'type': 'outlet'},
            {'position': (0, 2000), 'tolerance_mm': 100, 'type': 'outlet'},
        ],
        'lights': [
            {'position': (2000, 2667), 'tolerance_mm': 300, 'type': 'light'},
            {'position': (4000, 2667), 'tolerance_mm': 300, 'type': 'light'},
            {'position': (2000, 5333), 'tolerance_mm': 300, 'type': 'light'},
            {'position': (4000, 5333), 'tolerance_mm': 300, 'type': 'light'},
        ],
        'switches': [
            {'position': (3950, 100), 'tolerance_mm': 150, 'type': 'switch'},
        ]
    },
    
    'kitchen_3x4': {
        'room_type': 'kitchen',
        'polygon': [(0, 0), (3000, 0), (3000, 4000), (0, 4000)],
        'outlets': [
            # Kitchen has dense outlets on counters
            {'position': (400, 800), 'tolerance_mm': 150, 'type': 'outlet'},
            {'position': (1200, 800), 'tolerance_mm': 150, 'type': 'outlet'},
            {'position': (2000, 800), 'tolerance_mm': 150, 'type': 'outlet'},
            {'position': (2700, 1500), 'tolerance_mm': 150, 'type': 'outlet'},
            {'position': (2700, 2500), 'tolerance_mm': 150, 'type': 'outlet'},
            {'position': (1500, 4000), 'tolerance_mm': 150, 'type': 'outlet'},
        ],
        'lights': [
            {'position': (1500, 2000), 'tolerance_mm': 200, 'type': 'light'},
        ],
        'switches': [
            {'position': (2050, 100), 'tolerance_mm': 150, 'type': 'switch'},
        ]
    },
}


def calculate_accuracy(placed_devices: Dict[str, List[Dict]], 
                      golden_template_name: str) -> float:
    """
    Calculate placement accuracy against golden template
    
    Algorithm (from plan):
    1. For each expected device in golden:
       - Find nearest placed device of same type
       - Calculate distance
       - If distance <= tolerance: matched++
    
    2. Calculate:
       accuracy = matched_devices / total_expected_devices
    
    Args:
        placed_devices: {'outlets': [...], 'lights': [...], 'switches': [...]}
        golden_template_name: Template key (e.g., 'bedroom_4x6')
    
    Returns:
        Accuracy as float (0.0 - 1.0)
    
    Example:
        accuracy = calculate_accuracy(devices, 'bedroom_4x6')
        assert accuracy >= 0.90, f"Accuracy {accuracy} < 90%"
    """
    if golden_template_name not in GOLDEN_LAYOUTS:
        logger.warning(f"Golden template {golden_template_name} not found")
        return 0.0
    
    golden = GOLDEN_LAYOUTS[golden_template_name]
    
    matched = 0
    total = 0
    
    # Check each device type
    for device_type in ['outlets', 'lights', 'switches']:
        golden_devices = golden.get(device_type, [])
        placed = placed_devices.get(device_type, [])
        
        for expected in golden_devices:
            total += 1
            expected_pos = expected['position']
            tolerance = expected['tolerance_mm']
            
            # Find nearest placed device of same type
            nearest_dist = float('inf')
            for device in placed:
                device_pos = device['position']
                dist = _distance(expected_pos, device_pos)
                
                if dist < nearest_dist:
                    nearest_dist = dist
            
            # Check if within tolerance
            if nearest_dist <= tolerance:
                matched += 1
    
    if total == 0:
        return 0.0
    
    accuracy = matched / total
    return accuracy


def _distance(p1: Point, p2: Point) -> float:
    """Calculate Euclidean distance"""
    return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5


def validate_placement_rules(placed_devices: Dict[str, List[Dict]], 
                            room_type: str, standard: str = 'EIT') -> Dict[str, Any]:
    """
    Validate that all placement rules were applied correctly
    
    Returns:
        {
          'all_rules_applied': True/False,
          'violations': [],
          'rules_checked': ['VR001', 'VR002', ...]
        }
    """
    violations = []
    rules_checked = []
    
    # VR001: Outlet height (300-1200mm)
    for outlet in placed_devices.get('outlets', []):
        height = outlet.get('height', 0)
        if not (300 <= height <= 1200):
            violations.append(f"VR001: Outlet {outlet['id']} height {height}mm out of range")
        rules_checked.append('VR001')
    
    # VR002: Switch height (1100-1400mm)
    for switch in placed_devices.get('switches', []):
        height = switch.get('height', 0)
        if not (1100 <= height <= 1400):
            violations.append(f"VR002: Switch {switch['id']} height {height}mm out of range")
        rules_checked.append('VR002')
    
    # VR003: Bathroom clearance (600mm from water) - if applicable
    if room_type == 'bathroom':
        for outlet in placed_devices.get('outlets', []):
            # Would need wet_zones data to validate properly
            # For MVP, just check device code
            device_code = outlet.get('device_code', '')
            if 'IP44' not in device_code:
                violations.append(f"VR003: Bathroom outlet {outlet['id']} should be IP44")
        rules_checked.append('VR003')
    
    # Unique rules
    rules_checked = list(set(rules_checked))
    
    return {
        'all_rules_applied': len(violations) == 0,
        'violations': violations,
        'rules_checked': rules_checked
    }
