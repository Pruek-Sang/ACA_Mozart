"""
Room Templates - Geometry definitions for 6 room types

Provides standard room geometries for device placement:
1. Bedroom (4x6m)
2. Living Room (6x8m)
3. Kitchen (3x4m)
4. Bathroom (2.5x3m)
5. Corridor (1.5x8m)
6. Other (generic 4x4m)

Each template includes:
- Polygon boundary
- Door/window positions
- Furniture zones (no-device areas)
- Ceiling height
- Area
"""

from typing import Dict, List, Tuple, Any

# Type aliases
Point = Tuple[float, float]
Rectangle = Tuple[float, float, float, float]  # (x1, y1, x2, y2)


# Standard room templates in mm
ROOM_TEMPLATES: Dict[str, Dict[str, Any]] = {
    'bedroom': {
        'type': 'bedroom',
        'name': 'Standard Bedroom',
        'polygon': [(0, 0), (4000, 0), (4000, 6000), (0, 6000)],  # 4x6m
        'door': {
            'position': (2000, 0),  # Center of bottom wall
            'width': 900,
            'swing_direction': 'inward',
            'swing_degrees': 90
        },
        'windows': [
            {
                'position': (4000, 3000),  # Right wall, center
                'width': 1500,
                'height': 1200,
                'sill_height': 900
            }
        ],
        'furniture': [
            {
                'type': 'bed',
                'bounds': (1000, 2000, 3000, 4500),  # Queen size bed
                'no_outlet_zone': True,
                'clearance': 200
            },
            {
                'type': 'wardrobe',
                'bounds': (0, 5000, 1500, 6000),
                'no_outlet_zone': False,
                'clearance': 100
            }
        ],
        'ceiling_height': 2800,
        'area_sqm': 24.0,
        'typical_outlets': 6,
        'typical_lights': 2,
        'typical_switches': 1
    },
    
    'living': {
        'type': 'living',
        'name': 'Standard Living Room',
        'polygon': [(0, 0), (6000, 0), (6000, 8000), (0, 8000)],  # 6x8m
        'door': {
            'position': (3000, 0),
            'width': 900,
            'swing_direction': 'inward',
            'swing_degrees': 90
        },
        'windows': [
            {
                'position': (6000, 2000),  # Right wall
                'width': 2000,
                'height': 1500,
                'sill_height': 900
            },
            {
                'position': (6000, 6000),  # Right wall
                'width': 2000,
                'height': 1500,
                'sill_height': 900
            }
        ],
        'furniture': [
            {
                'type': 'sofa',
                'bounds': (500, 3000, 2000, 5000),
                'no_outlet_zone': False,
                'clearance': 200
            },
            {
                'type': 'tv_unit',
                'bounds': (5500, 3500, 6000, 4500),
                'no_outlet_zone': True,  # Outlets needed behind TV
                'clearance': 100
            }
        ],
        'ceiling_height': 3000,
        'area_sqm': 48.0,
        'typical_outlets': 10,
        'typical_lights': 4,
        'typical_switches': 1
    },
    
    'kitchen': {
        'type': 'kitchen',
        'name': 'Standard Kitchen',
        'polygon': [(0, 0), (3000, 0), (3000, 4000), (0, 4000)],  # 3x4m
        'door': {
            'position': (1500, 0),
            'width': 800,
            'swing_direction': 'outward',
            'swing_degrees': 90
        },
        'windows': [
            {
                'position': (3000, 2000),
                'width': 1200,
                'height': 800,
                'sill_height': 1200  # Higher for kitchen
            }
        ],
        'counters': [  # Kitchen-specific
            {
                'type': 'counter',
                'bounds': (0, 500, 2500, 1100),  # L-shaped counter
                'height': 900,
                'needs_outlets': True,
                'outlet_spacing': 1200  # Every 1.2m on counter
            },
            {
                'type': 'counter',
                'bounds': (2500, 500, 3000, 3500),
                'height': 900,
                'needs_outlets': True,
                'outlet_spacing': 1200
            }
        ],
        'furniture': [],
        'ceiling_height': 2800,
        'area_sqm': 12.0,
        'typical_outlets': 8,  # Dense for appliances
        'typical_lights': 2,
        'typical_switches': 1
    },
    
    'bathroom': {
        'type': 'bathroom',
        'name': 'Standard Bathroom',
        'polygon': [(0, 0), (2500, 0), (2500, 3000), (0, 3000)],  # 2.5x3m
        'door': {
            'position': (1250, 0),
            'width': 700,
            'swing_direction': 'outward',  # Safety
            'swing_degrees': 90
        },
        'windows': [
            {
                'position': (2500, 1500),
                'width': 600,
                'height': 600,
                'sill_height': 1800  # High for privacy
            }
        ],
        'wet_zones': [  # Bathroom-specific
            {
                'type': 'shower',
                'bounds': (0, 2000, 1000, 3000),
                'clearance': 600,  # IP44 clearance
                'no_outlet_zone': True
            },
            {
                'type': 'sink',
                'bounds': (1500, 0, 2500, 700),
                'clearance': 600,
                'no_outlet_zone': False  # Can have RCBO outlet
            }
        ],
        'furniture': [
            {
                'type': 'toilet',
                'bounds': (0, 0, 600, 800),
                'no_outlet_zone': True,
                'clearance': 200
            }
        ],
        'ceiling_height': 2600,
        'area_sqm': 7.5,
        'typical_outlets': 2,  # Limited, RCBO required
        'typical_lights': 1,
        'typical_switches': 1
    },
    
    'corridor': {
        'type': 'corridor',
        'name': 'Standard Corridor',
        'polygon': [(0, 0), (1500, 0), (1500, 8000), (0, 8000)],  # 1.5x8m
        'door': {
            'position': (750, 0),
            'width': 900,
            'swing_direction': 'inward',
            'swing_degrees': 90
        },
        'windows': [],  # Typically no windows
        'furniture': [],  # Typically no furniture
        'ceiling_height': 2600,
        'area_sqm': 12.0,
        'typical_outlets': 2,  # Minimal
        'typical_lights': 3,  # Spaced along length
        'typical_switches': 2,  # 2-way at both ends
        'is_corridor': True  # Flag for special switching
    },
    
    'other': {
        'type': 'other',
        'name': 'Generic Room',
        'polygon': [(0, 0), (4000, 0), (4000, 4000), (0, 4000)],  # 4x4m
        'door': {
            'position': (2000, 0),
            'width': 900,
            'swing_direction': 'inward',
            'swing_degrees': 90
        },
        'windows': [
            {
                'position': (4000, 2000),
                'width': 1500,
                'height': 1200,
                'sill_height': 900
            }
        ],
        'furniture': [],  # Generic, no specific furniture
        'ceiling_height': 2800,
        'area_sqm': 16.0,
        'typical_outlets': 4,
        'typical_lights': 1,
        'typical_switches': 1
    }
}


def get_template(room_type: str) -> Dict[str, Any]:
    """
    Get room template by type
    
    Args:
        room_type: 'bedroom', 'living', 'kitchen', 'bathroom', 'corridor', or 'other'
    
    Returns:
        Room template dict
    
    Raises:
        KeyError if room type not found
    """
    room_type = room_type.lower()
    if room_type not in ROOM_TEMPLATES:
        raise KeyError(f"Unknown room type: {room_type}. "
                      f"Available: {list(ROOM_TEMPLATES.keys())}")
    
    return ROOM_TEMPLATES[room_type].copy()


def get_all_room_types() -> List[str]:
    """Get list of all supported room types"""
    return list(ROOM_TEMPLATES.keys())


def calculate_polygon_area(polygon: List[Point]) -> float:
    """
    Calculate area of polygon using shoelace formula
    
    Args:
        polygon: List of (x, y) points in mm
    
    Returns:
        Area in square meters
    """
    n = len(polygon)
    if n < 3:
        return 0.0
    
    area_mm2 = 0.0
    for i in range(n):
        j = (i + 1) % n
        area_mm2 += polygon[i][0] * polygon[j][1]
        area_mm2 -= polygon[j][0] * polygon[i][1]
    
    area_mm2 = abs(area_mm2) / 2.0
    area_m2 = area_mm2 / 1_000_000  # mm² to m²
    
    return area_m2


def calculate_centroid(polygon: List[Point]) -> Point:
    """
    Calculate centroid of polygon
    
    Args:
        polygon: List of (x, y) points
    
    Returns:
        (x, y) centroid point
    """
    n = len(polygon)
    if n == 0:
        return (0, 0)
    
    cx = sum(p[0] for p in polygon) / n
    cy = sum(p[1] for p in polygon) / n
    
    return (cx, cy)


def point_in_polygon(point: Point, polygon: List[Point]) -> bool:
    """
    Check if point is inside polygon (ray casting algorithm)
    
    Args:
        point: (x, y) point to check
        polygon: List of (x, y) polygon vertices
    
    Returns:
        True if point inside polygon
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def distance(p1: Point, p2: Point) -> float:
    """Calculate Euclidean distance between two points"""
    return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5
