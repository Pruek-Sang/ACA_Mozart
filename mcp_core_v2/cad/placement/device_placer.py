"""
Device Placer - Place electrical devices in rooms

Places devices according to catalog rules and electrical standards:
- Outlets (receptacles) - wall-mounted, spacing rules
- Lights - ceiling-mounted, grid or centroid
- Switches - near door, latch side

Uses PLACEMENT_RULE from catalog and standards (EIT/IEC/NEC).

Return Type: ALWAYS dict (not list) - locked per plan
"""

import logging
import math
from typing import Dict, List, Tuple, Any, Optional

from ..standards import load_standards
from ..geometry import (
    get_template,
    calculate_centroid,
    point_in_polygon,
    distance
)

logger = logging.getLogger(__name__)

Point = Tuple[float, float]


class DevicePlacer:
    """
    Place electrical devices in rooms according to standards
    
    Responsibilities (per plan):
    - Place devices at correct positions
    - Follow catalog PLACEMENT_RULE
    - Return dict (NOT list)
    - circuit = None (assign later from MCP)
    """
    
    def __init__(self, standard: str = 'EIT'):
        """
        Initialize device placer
        
        Args:
            standard: 'EIT', 'IEC', or 'NEC'
        """
        self.standard = standard
        self.rules = load_standards(standard)
        
        # Device counter for unique IDs
        self.device_count = {'outlet': 0, 'light': 0, 'switch': 0}
    
    def place_all_devices(self, room_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place all devices in room
        
        Return Type: ALWAYS dict (locked per plan)
        
        Returns:
            {
              'outlets': [...],
              'lights': [...],
              'switches': [...],
              'validation': {
                'rules_applied': [...],
                'accuracy': 0.95,
                'errors': []
              }
            }
        
        Responsibilities:
        - Place device positions
        - Set device_code from catalog
        - circuit = None (MCP will assign later)
        """
        # Reset counters
        self.device_count = {'outlet': 0, 'light': 0, 'switch': 0}
        
        # Place each device type
        outlets = self.place_receptacles(room_template)
        lights = self.place_lights(room_template)
        switches = self.place_switches(room_template, lights)
        
        # Validation
        validation = self._validate_placement(
            room_template,
            {'outlets': outlets, 'lights': lights, 'switches': switches}
        )
        
        return {
            'outlets': outlets,
            'lights': lights,
            'switches': switches,
            'validation': validation
        }
    
    def place_receptacles(self, room_template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Place outlets/receptacles along walls
        
        Algorithm - Improved for accuracy:
        1. Place outlets near corners and middle of each wall
        2. Avoid door/window areas
        3. Check furniture collision
        """
        room_type = room_template['type']
        polygon = room_template['polygon']
        door = room_template.get('door')
        windows = room_template.get('windows', [])
        furniture = room_template.get('furniture', [])
        
        _, height_mm, _ = self._get_outlet_rules(room_type)
        
        devices = []
        walls = self._get_wall_segments(polygon)
        
        # For each wall, place outlets at 25%, 50%, 75% positions
        for wall in walls:
            wall_start, wall_end = wall
            wall_length = distance(wall_start, wall_end)
            
            # Skip very short walls
            if wall_length < 1000:
                continue
            
            # Determine positions based on wall length
            if wall_length < 2000:
                positions = [0.5]  # Just middle
            elif wall_length < 4000:
                positions = [0.25, 0.75]  # Two positions
            else:
                positions = [0.25, 0.5, 0.75]  # Three positions
            
            for pos_fraction in positions:
                x = wall_start[0] + pos_fraction * (wall_end[0] - wall_start[0])
                y = wall_start[1] + pos_fraction * (wall_end[1] - wall_start[1])
                pos = (x, y)
                
                # Check distance from door/window
                if door and distance(pos, door['position']) < 700:
                    continue
                
                skip = False
                for window in windows:
                    if distance(pos, window['position']) < 700:
                        skip = True
                        break
                if skip:
                    continue
                
                # Check furniture collision
                if self._check_collision(pos, furniture, clearance=300):
                    continue
                
                # Create device
                device_id = f'OUT-{self.device_count["outlet"]:03d}'
                self.device_count['outlet'] += 1
                
                device = {
                    'id': device_id,
                    'type': 'outlet',
                    'position': pos,
                    'height': height_mm,
                    'device_code': self._get_outlet_device_code(room_type),
                    'circuit': None,
                    'room': room_type
                }
                
                devices.append(device)
        
        return devices

    
    def place_lights(self, room_template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Place ceiling lights
        
        Algorithm:
        - Small room (<15 m²): 1 light at centroid
        - Large room: Grid system (2.5m spacing)
        """
        room_type = room_template['type']
        polygon = room_template['polygon']
        area_sqm = room_template.get('area_sqm', 0)
        ceiling_height = room_template.get('ceiling_height', 2800)
        furniture = room_template.get('furniture', [])
        
        devices = []
        
        # Small room: single light at center
        if area_sqm < 15:
            centroid = calculate_centroid(polygon)
            
            device_id = f'LT-{self.device_count["light"]:03d}'
            self.device_count['light'] += 1
            
            device = {
                'id': device_id,
                'type': 'light',
                'position': centroid,
                'height': ceiling_height,
                'device_code': 'COMP-DOWNLIGHT-9W',
                'watts': 9,
                'circuit': None,
                'room': room_type
            }
            
            devices.append(device)
        
        else:
            # Large room: grid system
            grid_spacing = 2500  # 2.5m
            
            # Get bounding box
            min_x = min(p[0] for p in polygon)
            max_x = max(p[0] for p in polygon)
            min_y = min(p[1] for p in polygon)
            max_y = max(p[1] for p in polygon)
            
            # Create grid
            x = min_x + grid_spacing / 2
            while x < max_x:
                y = min_y + grid_spacing / 2
                while y < max_y:
                    pos = (x, y)
                    
                    # Check if inside polygon
                    if point_in_polygon(pos, polygon):
                        # Check furniture collision
                        if not self._check_collision(pos, furniture, clearance=300):
                            device_id = f'LT-{self.device_count["light"]:03d}'
                            self.device_count['light'] += 1
                            
                            device = {
                                'id': device_id,
                                'type': 'light',
                                'position': pos,
                                'height': ceiling_height,
                                'device_code': 'COMP-DOWNLIGHT-9W' if area_sqm < 30 else 'COMP-DOWNLIGHT-24W',
                                'watts': 9 if area_sqm < 30 else 24,
                                'circuit': None,
                                'room': room_type
                            }
                            
                            devices.append(device)
                    
                    y += grid_spacing
                x += grid_spacing
        
        return devices
    
    def place_switches(self, room_template: Dict[str, Any], 
                      lights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Place light switches near door
        
        Algorithm:
        1. Find door position
        2. Calculate latch side (opposite of swing)
        3. Place switch at 1100-1200mm height
        4. For corridors: 2-way switches at both ends
        """
        room_type = room_template['type']
        door = room_template.get('door')
        
        if not door:
            logger.warning(f"No door found in {room_type}, cannot place switches")
            return []
        
        devices = []
        
        # Standard switch position
        door_pos = door['position']
        switch_height = 1100  # mm from floor
        offset_from_jamb = 150  # mm
        
        # Calculate switch position (on latch side)
        swing = door.get('swing_direction', 'inward')
        door_width = door.get('width', 900)
        
        # For simplicity: place to the right of door
        switch_pos = (door_pos[0] + door_width + offset_from_jamb, door_pos[1] + 100)
        
        # Create main switch
        device_id = f'SW-{self.device_count["switch"]:03d}'
        self.device_count['switch'] += 1
        
        light_ids = [light['id'] for light in lights]
        
        device = {
            'id': device_id,
            'type': 'switch',
            'position': switch_pos,
            'height': switch_height,
            'device_code': 'COMP-SW-1WAY',
            'controls': light_ids,
            'circuit': None,
            'room': room_type,
            'switch_type': '1-way'
        }
        
        devices.append(device)
        
        # For corridors: add 2nd switch (2-way)
        if room_template.get('is_corridor'):
            # Place at opposite end
            polygon = room_template['polygon']
            # Get far end of corridor (opposite from door)
            far_point = max(polygon, key=lambda p: distance(p, door_pos))
            
            device_id = f'SW-{self.device_count["switch"]:03d}'
            self.device_count['switch'] += 1
            
            device2 = {
                'id': device_id,
                'type': 'switch',
                'position': (far_point[0] - offset_from_jamb, far_point[1] - 100),
                'height': switch_height,
                'device_code': 'COMP-SW-2WAY',
                'controls': light_ids,
                'circuit': None,
                'room': room_type,
                'switch_type': '2-way'
            }
            
            devices.append(device2)
            
            # Update first switch to 2-way
            devices[0]['device_code'] = 'COMP-SW-2WAY'
            devices[0]['switch_type'] = '2-way'
        
        return devices
    
    def _get_outlet_rules(self, room_type: str) -> Tuple[int, int, int]:
        """
        Get outlet placement rules from catalog or defaults
        
        Returns:
            (spacing_mm, height_mm, from_corner_mm)
        """
        # Default values (EIT/IEC compatible)
        spacing_mm = 3600  # 3.6m
        height_mm = 300    # 300mm from floor
        from_corner_mm = 200  # 200mm from corner
        
        # Kitchen has denser spacing
        if room_type == 'kitchen':
            spacing_mm = 1200  # Every 1.2m on counter
        
        # Bathroom has special clearance
        if room_type == 'bathroom':
            spacing_mm = 1500
            from_corner_mm = 600  # IP44 clearance from water
        
        return (spacing_mm, height_mm, from_corner_mm)
    
    def _get_outlet_device_code(self, room_type: str) -> str:
        """Get device code from catalog"""
        if room_type == 'bathroom':
            return 'COMP-OUTLET-16A-IP44'  # Water-resistant
        else:
            return 'COMP-OUTLET-16A'
    
    def _get_wall_segments(self, polygon: List[Point]) -> List[Tuple[Point, Point]]:
        """Get wall segments from polygon"""
        walls = []
        n = len(polygon)
        for i in range(n):
            j = (i + 1) % n
            walls.append((polygon[i], polygon[j]))
        return walls
   
    def _wall_has_opening(self, wall: Tuple[Point, Point], door: Optional[Dict], 
                         windows: List[Dict]) -> bool:
        """Check if wall has door or window"""
        if not door and not windows:
            return False
        
        wall_start, wall_end = wall
        
        # Check door
        if door:
            door_pos = door['position']
            if self._point_on_wall(door_pos, wall_start, wall_end, tolerance=500):
                return True
        
        # Check windows
        for window in windows:
            window_pos = window['position']
            if self._point_on_wall(window_pos, wall_start, wall_end, tolerance=500):
                return True
        
        return False
    
    def _point_on_wall(self, point: Point, wall_start: Point, wall_end: Point, 
                      tolerance: float = 100) -> bool:
        """Check if point is on wall segment"""
        # Distance from point to line segment
        dx = wall_end[0] - wall_start[0]
        dy = wall_end[1] - wall_start[1]
        
        if dx == 0 and dy == 0:
            return distance(point, wall_start) < tolerance
        
        t = max(0, min(1, ((point[0] - wall_start[0]) * dx + (point[1] - wall_start[1]) * dy) / (dx*dx + dy*dy)))
        
        closest_x = wall_start[0] + t * dx
        closest_y = wall_start[1] + t * dy
        
        dist = distance(point, (closest_x, closest_y))
        
        return dist < tolerance
    
    def _check_collision(self, pos: Point, furniture: List[Dict], clearance: float = 200) -> bool:
        """Check if position collides with furniture"""
        for item in furniture:
            bounds = item.get('bounds')
            if not bounds:
                continue
            
            x1, y1, x2, y2 = bounds
            
            # Expand bounds by clearance
            x1 -= clearance
            y1 -= clearance
            x2 += clearance
            y2 += clearance
            
            # Check if point inside expanded bounds
            if x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2:
                return True  # Collision
        
        return False  # No collision
    
    def _validate_placement(self, room_template: Dict, 
                           devices: Dict[str, List]) -> Dict[str, Any]:
        """
        Validate device placement
        
        Returns:
            {
              'rules_applied': ['VR001', 'RULE-ROOM-OUTLET', ...],
              'accuracy': 0.95,
              'errors': []
            }
        """
        rules_applied = []
        errors = []
        
        # Check outlet height (VR001)
        for outlet in devices['outlets']:
            if 300 <= outlet['height'] <= 1200:
                if 'VR001' not in rules_applied:
                    rules_applied.append('VR001')
            else:
                errors.append(f"Outlet {outlet['id']} height {outlet['height']}mm out of range")
        
        # Check switch height (VR002)
        for switch in devices['switches']:
            if 1100 <= switch['height'] <= 1400:
                if 'VR002' not in rules_applied:
                    rules_applied.append('VR002')
            else:
                errors.append(f"Switch {switch['id']} height {switch['height']}mm out of range")
        
        # Check device count reasonable
        expected_outlets = room_template.get('typical_outlets', 4)
        actual_outlets = len(devices['outlets'])
        
        # Allow ±30% tolerance
        if abs(actual_outlets - expected_outlets) / expected_outlets > 0.3:
            errors.append(f"Outlet count {actual_outlets} vs expected {expected_outlets}")
        
        # Calculate accuracy (will be computed against golden template in tests)
        # For now, use heuristic
        if errors:
            accuracy = max(0.0, 1.0 - len(errors) * 0.1)
        else:
            accuracy = 1.0
        
        return {
            'rules_applied': rules_applied,
            'accuracy': accuracy,
            'errors': errors
        }
