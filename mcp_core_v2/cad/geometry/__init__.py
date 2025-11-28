"""Geometry package"""

from .room_templates import (
    ROOM_TEMPLATES,
    get_template,
    get_all_room_types,
    calculate_polygon_area,
    calculate_centroid,
    point_in_polygon,
    distance
)

__all__ = [
    'ROOM_TEMPLATES',
    'get_template',
    'get_all_room_types',
    'calculate_polygon_area',
    'calculate_centroid',
    'point_in_polygon',
    'distance'
]
