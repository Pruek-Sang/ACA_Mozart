"""
MCP Core v2 Template Resolver
Resolves room templates and placement rules based on room type and area.
"""

from typing import Dict, Any, List, Tuple
from models.contracts import RoomType, RoomInput, OutletType, LightType
from models.baseline import BASELINE_OUTLET_RULES, BASELINE_LIGHTING_RULES
from dal.catalog_dal import get_catalog_dal


class TemplateResolver:
    """
    Resolves templates for room design.
    Uses catalog when available, falls back to baseline rules.
    """
    
    def __init__(self):
        self.dal = get_catalog_dal()
    
    def resolve_outlet_rules(self, room: RoomInput) -> Dict[str, Any]:
        """
        Get outlet placement rules for a room.
        
        Args:
            room: RoomInput specification
            
        Returns:
            Dictionary of outlet rules
        """
        area = room.width * room.length
        
        # Try catalog first
        template = self.dal.get_room_template(room.room_type.value, area)
        if template and template.outlet_rules:
            return template.outlet_rules
        
        # Fall back to baseline
        return BASELINE_OUTLET_RULES.get(room.room_type, {})
    
    def resolve_lighting_rules(self, room: RoomInput) -> Dict[str, Any]:
        """
        Get lighting rules for a room.
        
        Args:
            room: RoomInput specification
            
        Returns:
            Dictionary of lighting rules
        """
        area = room.width * room.length
        
        # Try catalog first
        template = self.dal.get_room_template(room.room_type.value, area)
        if template and template.lighting_rules:
            return template.lighting_rules
        
        # Fall back to baseline
        return BASELINE_LIGHTING_RULES.get(room.room_type, {})
    
    def calculate_outlet_count(self, room: RoomInput) -> int:
        """
        Calculate number of outlets needed for a room.
        
        Args:
            room: RoomInput specification
            
        Returns:
            Number of outlets
        """
        rules = self.resolve_outlet_rules(room)
        min_outlets = rules.get("min_outlets", 1)
        max_spacing = rules.get("max_spacing_m", 4.5)
        
        # Calculate perimeter-based outlets
        perimeter = 2 * (room.width + room.length)
        perimeter_outlets = int(perimeter / max_spacing) + 1
        
        return max(min_outlets, perimeter_outlets)
    
    def calculate_outlet_positions(self, room: RoomInput) -> List[Tuple[float, float]]:
        """
        Calculate outlet positions in room.
        
        Args:
            room: RoomInput specification
            
        Returns:
            List of (x, y) positions
        """
        rules = self.resolve_outlet_rules(room)
        num_outlets = self.calculate_outlet_count(room)
        max_spacing = rules.get("max_spacing_m", 4.5)
        
        positions = []
        
        # Distribute outlets around perimeter
        # Start with corners, then fill walls
        walls = [
            ("bottom", 0, room.width, 0),      # y=0
            ("right", room.width, 0, room.length),  # x=width
            ("top", room.width, 0, room.length),    # y=length
            ("left", 0, 0, room.length),       # x=0
        ]
        
        outlets_per_wall = max(1, num_outlets // 4)
        
        # Bottom wall
        for i in range(outlets_per_wall):
            x = (i + 1) * room.width / (outlets_per_wall + 1)
            positions.append((x, 0.1))
        
        # Right wall
        for i in range(outlets_per_wall):
            y = (i + 1) * room.length / (outlets_per_wall + 1)
            positions.append((room.width - 0.1, y))
        
        # Top wall
        for i in range(outlets_per_wall):
            x = (i + 1) * room.width / (outlets_per_wall + 1)
            positions.append((x, room.length - 0.1))
        
        # Left wall
        for i in range(outlets_per_wall):
            y = (i + 1) * room.length / (outlets_per_wall + 1)
            positions.append((0.1, y))
        
        return positions[:num_outlets]
    
    def calculate_light_count(self, room: RoomInput) -> int:
        """
        Calculate number of light fixtures needed.
        
        Args:
            room: RoomInput specification
            
        Returns:
            Number of light fixtures
        """
        rules = self.resolve_lighting_rules(room)
        area = room.width * room.length
        min_fixtures = rules.get("min_fixtures", 1)
        watts_per_sqm = rules.get("watts_per_sqm", 10)
        
        # Assume 10W LED per fixture point for spacing calculation
        fixture_watts = 10
        total_watts_needed = area * watts_per_sqm
        calculated_fixtures = int(total_watts_needed / fixture_watts) + 1
        
        # Limit based on room size (one fixture per ~6 sqm max)
        max_fixtures = int(area / 6) + 1
        
        return max(min_fixtures, min(calculated_fixtures, max_fixtures))
    
    def calculate_light_positions(self, room: RoomInput) -> List[Tuple[float, float]]:
        """
        Calculate light fixture positions (centered grid).
        
        Args:
            room: RoomInput specification
            
        Returns:
            List of (x, y) positions
        """
        num_lights = self.calculate_light_count(room)
        
        if num_lights == 1:
            # Center of room
            return [(room.width / 2, room.length / 2)]
        
        # Create a grid pattern
        import math
        cols = int(math.ceil(math.sqrt(num_lights * room.width / room.length)))
        rows = int(math.ceil(num_lights / cols))
        
        positions = []
        x_spacing = room.width / (cols + 1)
        y_spacing = room.length / (rows + 1)
        
        for row in range(rows):
            for col in range(cols):
                if len(positions) >= num_lights:
                    break
                x = (col + 1) * x_spacing
                y = (row + 1) * y_spacing
                positions.append((x, y))
        
        return positions
    
    def get_light_wattage(self, room: RoomInput, num_fixtures: int) -> float:
        """
        Calculate wattage per light fixture.
        
        Args:
            room: RoomInput specification
            num_fixtures: Number of fixtures
            
        Returns:
            Wattage per fixture
        """
        rules = self.resolve_lighting_rules(room)
        area = room.width * room.length
        watts_per_sqm = rules.get("watts_per_sqm", 10)
        
        total_watts = area * watts_per_sqm
        watts_per_fixture = total_watts / num_fixtures
        
        # Round to standard LED wattages
        standard_wattages = [5, 7, 9, 12, 15, 18, 24, 36]
        for w in standard_wattages:
            if w >= watts_per_fixture:
                return w
        
        return standard_wattages[-1]
    
    def get_preferred_light_type(self, room: RoomInput) -> LightType:
        """Get preferred light type for room."""
        rules = self.resolve_lighting_rules(room)
        preferred = rules.get("preferred_type", LightType.CEILING)
        
        if isinstance(preferred, str):
            return LightType(preferred)
        return preferred
    
    def get_outlet_type(self, room: RoomInput) -> OutletType:
        """Get default outlet type for room."""
        if room.room_type in [RoomType.KITCHEN, RoomType.BATHROOM]:
            return OutletType.GROUNDED
        return OutletType.STANDARD
