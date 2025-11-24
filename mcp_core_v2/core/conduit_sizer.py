"""Conduit sizing module based on NEC requirements."""

from typing import Dict, Any, List, Optional
from models.baseline import ConduitBaseline
import logging
import math

logger = logging.getLogger(__name__)


class ConduitSizer:
    """Sizes conduit based on NEC fill requirements."""
    
    def __init__(self):
        """Initialize conduit sizer."""
        self.baseline = ConduitBaseline()
    
    def size_conduit(
        self,
        wire_sizes: List[str],
        wire_counts: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Size conduit for a set of wires."""
        if not wire_sizes:
            return {'error': 'No wires provided'}
        
        # Default to one of each wire if counts not provided
        if not wire_counts:
            wire_counts = [1] * len(wire_sizes)
        
        if len(wire_sizes) != len(wire_counts):
            return {'error': 'Wire sizes and counts must have same length'}
        
        # Calculate total wire area
        total_wire_area = 0
        wire_details = []
        
        for wire_size, count in zip(wire_sizes, wire_counts):
            wire_area = self.baseline.wire_areas.get(wire_size)
            if not wire_area:
                logger.warning(f"No area data for wire size {wire_size}")
                continue
            
            area_for_this_wire = wire_area * count
            total_wire_area += area_for_this_wire
            
            wire_details.append({
                'size': wire_size,
                'count': count,
                'area_each': wire_area,
                'total_area': area_for_this_wire
            })
        
        # Determine number of conductors for fill calculation
        total_conductors = sum(wire_counts)
        
        # Get fill percentage based on number of conductors
        fill_percent = self._get_fill_percentage(total_conductors)
        
        # Find smallest conduit that meets fill requirement
        selected_conduit = self._select_conduit_size(total_wire_area, fill_percent)
        
        if not selected_conduit:
            return {
                'error': 'No conduit size found for wire configuration',
                'total_wire_area': total_wire_area,
                'wire_details': wire_details
            }
        
        return {
            'conduit_size': selected_conduit['size'],
            'conduit_area': selected_conduit['area'],
            'total_wire_area': round(total_wire_area, 4),
            'fill_percentage': round((total_wire_area / selected_conduit['area']) * 100, 2),
            'max_fill_percentage': fill_percent * 100,
            'wire_details': wire_details,
            'total_conductors': total_conductors
        }
    
    def _get_fill_percentage(self, num_conductors: int) -> float:
        """Get maximum fill percentage based on number of conductors."""
        if num_conductors == 1:
            return self.baseline.max_fill_percentage[1]
        elif num_conductors == 2:
            return self.baseline.max_fill_percentage[2]
        else:
            return self.baseline.max_fill_percentage[3]
    
    def _select_conduit_size(
        self,
        wire_area: float,
        fill_percent: float
    ) -> Optional[Dict[str, Any]]:
        """Select conduit size based on wire area and fill percentage."""
        for size, diameter in self.baseline.conduit_sizes.items():
            # Calculate conduit internal area
            radius = diameter / 2
            conduit_area = math.pi * radius * radius
            
            # Calculate maximum allowed fill area
            max_fill_area = conduit_area * fill_percent
            
            if wire_area <= max_fill_area:
                return {
                    'size': size,
                    'diameter': diameter,
                    'area': conduit_area
                }
        
        return None
    
    def size_conduit_for_circuit(
        self,
        phase_wire_size: str,
        num_phases: int,
        neutral_wire_size: Optional[str] = None,
        ground_wire_size: Optional[str] = None
    ) -> Dict[str, Any]:
        """Size conduit for a complete circuit."""
        wire_sizes = []
        wire_counts = []
        
        # Add phase conductors
        wire_sizes.append(phase_wire_size)
        wire_counts.append(num_phases)
        
        # Add neutral if present
        if neutral_wire_size:
            wire_sizes.append(neutral_wire_size)
            wire_counts.append(1)
        
        # Add ground if present
        if ground_wire_size:
            wire_sizes.append(ground_wire_size)
            wire_counts.append(1)
        
        result = self.size_conduit(wire_sizes, wire_counts)
        
        # Add circuit details
        if 'error' not in result:
            result['circuit_configuration'] = {
                'phase_conductors': num_phases,
                'phase_wire_size': phase_wire_size,
                'neutral_wire_size': neutral_wire_size,
                'ground_wire_size': ground_wire_size
            }
        
        return result
    
    def verify_conduit_fill(
        self,
        conduit_size: str,
        wire_sizes: List[str],
        wire_counts: List[int]
    ) -> Dict[str, Any]:
        """Verify that a specific conduit size is adequate."""
        # Get conduit properties
        conduit_diameter = self.baseline.conduit_sizes.get(conduit_size)
        if not conduit_diameter:
            return {'error': f'Unknown conduit size: {conduit_size}'}
        
        # Calculate conduit area
        radius = conduit_diameter / 2
        conduit_area = math.pi * radius * radius
        
        # Calculate wire area
        total_wire_area = 0
        for wire_size, count in zip(wire_sizes, wire_counts):
            wire_area = self.baseline.wire_areas.get(wire_size, 0)
            total_wire_area += wire_area * count
        
        # Get required fill percentage
        total_conductors = sum(wire_counts)
        max_fill_percent = self._get_fill_percentage(total_conductors)
        max_fill_area = conduit_area * max_fill_percent
        
        # Check if adequate
        actual_fill_percent = (total_wire_area / conduit_area) * 100
        adequate = total_wire_area <= max_fill_area
        
        return {
            'adequate': adequate,
            'conduit_size': conduit_size,
            'conduit_area': round(conduit_area, 4),
            'wire_area': round(total_wire_area, 4),
            'fill_percentage': round(actual_fill_percent, 2),
            'max_fill_percentage': max_fill_percent * 100,
            'margin': round(max_fill_area - total_wire_area, 4)
        }
    
    def get_conduit_properties(self, conduit_size: str) -> Dict[str, Any]:
        """Get properties of a conduit size."""
        diameter = self.baseline.conduit_sizes.get(conduit_size)
        if not diameter:
            return {'error': f'Unknown conduit size: {conduit_size}'}
        
        radius = diameter / 2
        area = math.pi * radius * radius
        
        return {
            'size': conduit_size,
            'diameter_inches': diameter,
            'area_sq_inches': round(area, 4),
            'fill_1_conductor': self.baseline.max_fill_percentage[1] * 100,
            'fill_2_conductors': self.baseline.max_fill_percentage[2] * 100,
            'fill_3plus_conductors': self.baseline.max_fill_percentage[3] * 100
        }


# Global instance
_conduit_sizer: Optional[ConduitSizer] = None


def get_conduit_sizer() -> ConduitSizer:
    """Get the global conduit sizer instance."""
    global _conduit_sizer
    if _conduit_sizer is None:
        _conduit_sizer = ConduitSizer()
    return _conduit_sizer
