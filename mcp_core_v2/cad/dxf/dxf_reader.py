"""
DXF Reader v1 - Read controlled DXF templates

Reads DXF files with predefined layer naming patterns:
- A-ROOM-* : Room boundaries (polygons)
- E-PANEL-* : Panel locations
- A-DOOR-* : Door positions
- A-WINDOW-* : Window positions

For MVP: Works with controlled/test DXF files only.
NOT designed for arbitrary external architect DXF files.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

Point = Tuple[float, float]


class DXFReaderV1:
    """
    DXF Reader v1 - Controlled templates only
    
    Reads test/mock DXF files with known layer structure.
    Extracts:
    - Room polygons
    - Panel locations
    - Door/window positions
    
    Maps to RoomTemplate format for device placement.
    """
    
    def __init__(self):
        """Initialize DXF reader"""
        self.rooms = []
        self.panels = []
        self.layers_found = []
    
    def read_mock_dxf(self, file_path: Path) -> Dict[str, Any]:
        """
        Read mock DXF file (simplified parser for testing)
        
        For MVP: Parse simple text-based mock DXF format
        
        Args:
            file_path: Path to mock DXF file
        
        Returns:
            {
                'rooms': [
                    {
                        'id': 'BEDROOM-01',
                        'type': 'bedroom',
                        'polygon': [(x,y), ...],
                        'door': {'position': (x,y), 'width': w},
                        'windows': [...]
                    }
                ],
                'panels': [
                    {'id': 'DB-1', 'position': (x,y)}
                ],
                'layers': ['A-ROOM-BEDROOM', ...]
            }
        """
        if not file_path.exists():
            raise FileNotFoundError(f"DXF file not found: {file_path}")
        
        # Read mock DXF (simple text format for MVP)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse mock format
        data = self._parse_mock_dxf(content)
        
        return data
    
    def _parse_mock_dxf(self, content: str) -> Dict[str, Any]:
        """
        Parse mock DXF text format
        
        Format:
        LAYER: A-ROOM-BEDROOM
        POLYGON: (0,0) (4000,0) (4000,6000) (0,6000)
        
        LAYER: A-DOOR
        POINT: (2000,0) WIDTH:900
        
        LAYER: E-PANEL-MAIN
        POINT: (500,500)
        """
        rooms = []
        panels = []
        layers_found = []
        
        current_layer = None
        lines = content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('LAYER:'):
                current_layer = line.split(':', 1)[1].strip()
                layers_found.append(current_layer)
            
            elif line.startswith('POLYGON:') and current_layer:
                # Parse polygon points
                points_str = line.split(':', 1)[1].strip()
                points = self._parse_points(points_str)
                
                # Determine room type from layer
                room_type = self._extract_room_type(current_layer)
                room_id = current_layer.replace('A-ROOM-', '').replace('_', '-')
                
                room = {
                    'id': room_id,
                    'type': room_type,
                    'polygon': points,
                    'door': None,
                    'windows': [],
                    'layer': current_layer
                }
                rooms.append(room)
            
            elif line.startswith('POINT:') and current_layer:
                point_data = line.split(':', 1)[1].strip()
                parts = point_data.split()
                point = self._parse_points(parts[0])[0]
                
                # Check layer type
                if 'PANEL' in current_layer:
                    panel_id = current_layer.replace('E-PANEL-', '').upper()
                    if not panel_id:
                        panel_id = 'DB-1'
                    
                    panels.append({
                        'id': panel_id,
                        'position': point,
                        'layer': current_layer
                    })
                
                elif 'DOOR' in current_layer:
                    # Parse door width if present
                    width = 900  # default
                    for part in parts[1:]:
                        if 'WIDTH:' in part:
                            width = int(part.split(':')[1])
                    
                    # Assign to last room
                    if rooms:
                        rooms[-1]['door'] = {
                            'position': point,
                            'width': width,
                            'swing_direction': 'inward',
                            'swing_degrees': 90
                        }
                
                elif 'WINDOW' in current_layer:
                    # Parse window dimensions
                    width = 1500
                    height = 1200
                    for part in parts[1:]:
                        if 'WIDTH:' in part:
                            width = int(part.split(':')[1])
                        if 'HEIGHT:' in part:
                            height = int(part.split(':')[1])
                    
                    # Assign to last room
                    if rooms:
                        rooms[-1]['windows'].append({
                            'position': point,
                            'width': width,
                            'height': height,
                            'sill_height': 900
                        })
            
            i += 1
        
        return {
            'rooms': rooms,
            'panels': panels,
            'layers': layers_found
        }
    
    def _parse_points(self, points_str: str) -> List[Point]:
        """
        Parse point string: "(0,0) (100,100)" → [(0,0), (100,100)]
        """
        points = []
        # Find all (x,y) patterns
        import re
        pattern = r'\(([0-9.]+),([0-9.]+)\)'
        matches = re.findall(pattern, points_str)
        
        for match in matches:
            x = float(match[0])
            y = float(match[1])
            points.append((x, y))
        
        return points
    
    def _extract_room_type(self, layer_name: str) -> str:
        """
        Extract room type from layer name
        
        A-ROOM-BEDROOM → bedroom
        A-ROOM-LIVING_ROOM → living
        """
        layer_upper = layer_name.upper()
        
        if 'BEDROOM' in layer_upper:
            return 'bedroom'
        elif 'LIVING' in layer_upper:
            return 'living'
        elif 'KITCHEN' in layer_upper:
            return 'kitchen'
        elif 'BATHROOM' in layer_upper or 'BATH' in layer_upper:
            return 'bathroom'
        elif 'CORRIDOR' in layer_upper or 'HALLWAY' in layer_upper:
            return 'corridor'
        else:
            return 'other'
    
    def map_to_room_template(self, dxf_room: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map DXF room data to RoomTemplate format
        
        Args:
            dxf_room: Room dict from read_mock_dxf()
        
        Returns:
            RoomTemplate-compatible dict
        """
        from ..geometry import calculate_polygon_area, calculate_centroid
        
        polygon = dxf_room['polygon']
        area_sqm = calculate_polygon_area(polygon)
        centroid = calculate_centroid(polygon)
        
        # Build template
        template = {
            'type': dxf_room['type'],
            'name': dxf_room['id'],
            'polygon': polygon,
            'door': dxf_room.get('door'),
            'windows': dxf_room.get('windows', []),
            'furniture': [],  # Would parse from DXF in full version
            'ceiling_height': 2800,  # Default
            'area_sqm': area_sqm,
            'typical_outlets': max(4, int(area_sqm / 4)),
            'typical_lights': max(1, int(area_sqm / 15)),
            'typical_switches': 1,
            'source': 'dxf',
            'dxf_layer': dxf_room.get('layer')
        }
        
        return template


def read_dxf_file(file_path: Path) -> Dict[str, Any]:
    """
    Convenience function to read DXF file
    
    Args:
        file_path: Path to mock DXF file
    
    Returns:
        Parsed DXF data
    """
    reader = DXFReaderV1()
    return reader.read_mock_dxf(file_path)
