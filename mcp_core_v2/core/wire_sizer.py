"""Wire sizing module based on NEC requirements."""

from typing import Dict, Any, Optional, List
from models.baseline import WireBaseline, NECBaseline
from models.catalog_models import ConductorMaterial
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class WireSizer:
    """Sizes conductors according to NEC requirements."""
    
    def __init__(self):
        """Initialize wire sizer."""
        self.wire_baseline = WireBaseline()
        self.nec_baseline = NECBaseline()
        self.settings = get_settings()
    
    def size_wire_by_ampacity(
        self,
        current: float,
        material: ConductorMaterial = ConductorMaterial.COPPER,
        temperature_rating: int = 75
    ) -> Dict[str, Any]:
        """Size wire based on required ampacity."""
        # Get ampacity table for material and temperature
        if material == ConductorMaterial.COPPER and temperature_rating == 75:
            ampacity_table = self.wire_baseline.copper_ampacity_75C
        elif material == ConductorMaterial.ALUMINUM and temperature_rating == 75:
            ampacity_table = self.wire_baseline.aluminum_ampacity_75C
        else:
            logger.error(f"Unsupported material/temperature: {material}/{temperature_rating}")
            return {}
        
        # Find smallest wire that meets ampacity requirement
        selected_size = None
        selected_ampacity = None
        
        for size, ampacity in ampacity_table.items():
            if ampacity >= current:
                selected_size = size
                selected_ampacity = ampacity
                break
        
        if not selected_size:
            logger.error(f"No wire size found for {current}A")
            return {
                'error': f'Current {current}A exceeds maximum wire ampacity',
                'required_current': current
            }
        
        return {
            'wire_size': selected_size,
            'ampacity': selected_ampacity,
            'material': material.value,
            'temperature_rating': temperature_rating,
            'required_current': current,
            'margin': selected_ampacity - current
        }
    
    def size_wire_with_voltage_drop(
        self,
        current: float,
        distance_feet: float,
        voltage: float,
        max_voltage_drop_percent: float = 3.0,
        material: ConductorMaterial = ConductorMaterial.COPPER,
        temperature_rating: int = 75
    ) -> Dict[str, Any]:
        """Size wire considering both ampacity and voltage drop."""
        # First, size by ampacity
        ampacity_result = self.size_wire_by_ampacity(current, material, temperature_rating)
        
        if 'error' in ampacity_result:
            return ampacity_result
        
        # Check voltage drop for ampacity-sized wire
        wire_size = ampacity_result['wire_size']
        vd, vd_pct = self._calculate_voltage_drop(
            current, distance_feet, wire_size, voltage
        )
        
        # If voltage drop is acceptable, return
        if vd_pct <= max_voltage_drop_percent:
            return {
                **ampacity_result,
                'voltage_drop': vd,
                'voltage_drop_percent': vd_pct,
                'sized_for': 'ampacity'
            }
        
        # Need to upsize for voltage drop
        if material == ConductorMaterial.COPPER:
            ampacity_table = self.wire_baseline.copper_ampacity_75C
        else:
            ampacity_table = self.wire_baseline.aluminum_ampacity_75C
        
        # Try larger wire sizes
        wire_sizes = list(ampacity_table.keys())
        current_index = wire_sizes.index(wire_size)
        
        for i in range(current_index + 1, len(wire_sizes)):
            test_size = wire_sizes[i]
            vd, vd_pct = self._calculate_voltage_drop(
                current, distance_feet, test_size, voltage
            )
            
            if vd_pct <= max_voltage_drop_percent:
                return {
                    'wire_size': test_size,
                    'ampacity': ampacity_table[test_size],
                    'material': material.value,
                    'temperature_rating': temperature_rating,
                    'required_current': current,
                    'voltage_drop': vd,
                    'voltage_drop_percent': vd_pct,
                    'sized_for': 'voltage_drop',
                    'upsized_from': wire_size
                }
        
        # Could not meet voltage drop requirement
        return {
            'error': 'Cannot meet voltage drop requirement with available wire sizes',
            'required_current': current,
            'distance_feet': distance_feet,
            'max_voltage_drop_percent': max_voltage_drop_percent
        }
    
    def _calculate_voltage_drop(
        self,
        current: float,
        distance_feet: float,
        wire_size: str,
        voltage: float
    ) -> tuple:
        """Calculate voltage drop for a wire size."""
        # Get wire resistance
        resistance_per_1000 = self.wire_baseline.copper_resistance.get(wire_size, 0)
        
        if resistance_per_1000 == 0:
            logger.warning(f"No resistance data for wire size {wire_size}")
            return 0, 0
        
        # Calculate total resistance (round trip)
        total_resistance = (resistance_per_1000 * distance_feet * 2) / 1000
        
        # Calculate voltage drop
        voltage_drop = current * total_resistance
        voltage_drop_percent = (voltage_drop / voltage) * 100
        
        return voltage_drop, voltage_drop_percent
    
    def get_wire_properties(self, wire_size: str) -> Dict[str, Any]:
        """Get properties of a wire size."""
        return {
            'size': wire_size,
            'copper_ampacity_75C': self.wire_baseline.copper_ampacity_75C.get(wire_size),
            'aluminum_ampacity_75C': self.wire_baseline.aluminum_ampacity_75C.get(wire_size),
            'copper_resistance': self.wire_baseline.copper_resistance.get(wire_size),
            'area_sq_in': self._get_wire_area(wire_size)
        }
    
    def _get_wire_area(self, wire_size: str) -> Optional[float]:
        """Get wire cross-sectional area."""
        from models.baseline import ConduitBaseline
        conduit_baseline = ConduitBaseline()
        return conduit_baseline.wire_areas.get(wire_size)
    
    def size_ground_wire(self, circuit_breaker_rating: int) -> str:
        """Size equipment grounding conductor based on NEC Table 250.122."""
        # Simplified NEC Table 250.122
        grounding_table = {
            15: "14",
            20: "12",
            30: "10",
            40: "10",
            60: "10",
            100: "8",
            200: "6",
            300: "4",
            400: "3",
            500: "2",
            600: "1",
            800: "1/0",
            1000: "2/0",
            1200: "3/0",
            1600: "4/0",
            2000: "250",
            2500: "350",
            3000: "400"
        }
        
        for rating, wire_size in grounding_table.items():
            if circuit_breaker_rating <= rating:
                return wire_size
        
        return "500"  # Maximum size in table
    
    def calculate_neutral_size(
        self,
        phase_wire_size: str,
        unbalanced_load_percent: float = 100.0
    ) -> str:
        """Calculate neutral conductor size."""
        # For most circuits, neutral is same size as phase
        # Can be reduced for certain conditions per NEC 220.61
        
        if unbalanced_load_percent >= 70:
            # Full size neutral required
            return phase_wire_size
        else:
            # Could potentially reduce neutral size
            # For safety, return same size
            logger.info("Neutral could potentially be reduced, but using full size for safety")
            return phase_wire_size


# Global instance
_wire_sizer: Optional[WireSizer] = None


def get_wire_sizer() -> WireSizer:
    """Get the global wire sizer instance."""
    global _wire_sizer
    if _wire_sizer is None:
        _wire_sizer = WireSizer()
    return _wire_sizer
