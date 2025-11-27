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
        temperature_rating: int = 75,
        ambient_temp_c: float = 30.0,
        num_conductors: int = 3,
        power_factor: float = 1.0,
        insulation_thickness_mm: float = 0.0,
        soil_resistivity: float = 0.0
    ) -> Dict[str, Any]:
        """Size wire considering ampacity, voltage drop, and derating factors.
        
        Args:
            current: Load current (A)
            distance_feet: One-way distance (feet)
            voltage: Nominal voltage (V)
            max_voltage_drop_percent: Maximum allowed VD (%)
            material: Conductor material
            temperature_rating: Conductor temp rating (60, 75, or 90°C)
            ambient_temp_c: Ambient temperature (°C)
            num_conductors: Number of current-carrying conductors
            power_factor: Power factor (0-1)
            insulation_thickness_mm: Thermal insulation thickness (mm)
            soil_resistivity: Soil thermal resistivity (K·m/W, 0 if not buried)
            
        Returns:
            Dict with wire size, ampacity, voltage drop, and derating info
        """
        from models.baseline import DeratingFactors
        
        # Calculate derating factors
        derating_total, derating_breakdown = DeratingFactors.calculate_total_derating(
            ambient_temp_c=ambient_temp_c,
            num_conductors=num_conductors,
            conductor_temp_rating=temperature_rating,
            soil_resistivity=soil_resistivity,
            insulation_thickness_mm=insulation_thickness_mm
        )
        
        # Calculate required ampacity (before derating)
        required_ampacity = current / derating_total if derating_total > 0 else current
        
        # First, size by derated ampacity
        ampacity_result = self.size_wire_by_ampacity(
            required_ampacity, material, temperature_rating
        )
        
        if 'error' in ampacity_result:
            return ampacity_result
        
        # Check voltage drop for ampacity-sized wire
        wire_size = ampacity_result['wire_size']
        vd, vd_pct = self._calculate_voltage_drop(
            current, distance_feet, wire_size, voltage,
            operating_temp_c=temperature_rating,
            power_factor=power_factor,
            material=material
        )
        
        # If voltage drop is acceptable, return
        if vd_pct <= max_voltage_drop_percent:
            return {
                **ampacity_result,
                'voltage_drop': vd,
                'voltage_drop_percent': vd_pct,
                'sized_for': 'ampacity',
                'derating_factors': derating_breakdown,
                'derating_total': derating_total,
                'current_before_derating': current,
                'current_after_derating': required_ampacity
            }
        
        # Need to upsize for voltage drop
        if material == ConductorMaterial.COPPER:
            ampacity_table = self.wire_baseline.copper_ampacity_75C
        else:
            ampacity_table = self.wire_baseline.aluminum_ampacity_75C
        
        # Try larger wire sizes
        for size, ampacity in ampacity_table.items():
            if ampacity < required_ampacity:
                continue
            
            vd, vd_pct = self._calculate_voltage_drop(
                current, distance_feet, size, voltage,
                operating_temp_c=temperature_rating,
                power_factor=power_factor,
                material=material
            )
            
            if vd_pct <= max_voltage_drop_percent:
                return {
                    'wire_size': size,
                    'ampacity': ampacity,
                    'material': material.value,
                    'temperature_rating': temperature_rating,
                    'required_current': current,
                    'required_ampacity': required_ampacity,
                    'margin': ampacity - required_ampacity,
                    'voltage_drop': vd,
                    'voltage_drop_percent': vd_pct,
                    'sized_for': 'voltage_drop',
                    'derating_factors': derating_breakdown,
                    'derating_total': derating_total,
                    'current_before_derating': current,
                    'current_after_derating': required_ampacity
                }
        
        # Could not meet voltage drop requirement
        return {
            'error': 'Cannot meet voltage drop requirement with available wire sizes',
            'required_current': current,
            'required_ampacity': required_ampacity,
            'distance_feet': distance_feet,
            'max_voltage_drop_percent': max_voltage_drop_percent,
            'derating_total': derating_total
        }
    
    def _calculate_voltage_drop(
        self,
        current: float,
        distance_feet: float,
        wire_size: str,
        voltage: float,
        operating_temp_c: float = 75.0,
        power_factor: float = 1.0,
        material: ConductorMaterial = ConductorMaterial.COPPER
    ) -> tuple:
        """Calculate voltage drop with temperature correction and reactance.
        
        Args:
            current: Load current (A)
            distance_feet: One-way distance (feet)
            wire_size: Wire size (AWG or kcmil)
            voltage: Nominal voltage (V)
            operating_temp_c: Operating temperature (°C)
            power_factor: Power factor (0-1)
            material: Conductor material
            
        Returns:
            Tuple of (voltage_drop_volts, voltage_drop_percent)
        """
        # Get wire resistance at 20°C
        if material == ConductorMaterial.COPPER:
            r_20c = self.wire_baseline.copper_resistance.get(wire_size, 0)
        else:
            r_20c = self.wire_baseline.aluminum_resistance.get(wire_size, 0)
        
        if r_20c == 0:
            logger.warning(f"No resistance data for wire size {wire_size}")
            return 0, 0
        
        # Apply temperature correction
        r_operating = self.calculate_resistance_at_temp(r_20c, operating_temp_c, material)
        
        # Typical reactance for copper wire (Ω/1000ft)
        # Simplified: X ≈ 0.05 Ω/1000ft for most sizes in conduit
        x_per_1000ft = 0.054  # Conservative estimate
        
        # Calculate VD with reactance
        # Assuming single-phase (most common for branch circuits)
        import math
        
        cos_theta = power_factor
        sin_theta = math.sqrt(1 - cos_theta**2) if cos_theta < 1.0 else 0.0
        
        # Effective impedance
        z_eff = r_operating * cos_theta + x_per_1000ft * sin_theta
        
        # Voltage drop (round trip for single-phase)
        vd_volt = 2.0 * distance_feet * current * z_eff / 1000.0
        vd_pct = (vd_volt / voltage) * 100.0
        
        return vd_volt, vd_pct
    
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
    
    def calculate_resistance_at_temp(
        self,
        r_20c: float,
        operating_temp_c: float,
        material: ConductorMaterial = ConductorMaterial.COPPER
    ) -> float:
        """Calculate resistance at operating temperature.
        
        Formula: R_t = R_20 × (1 + α × ΔT)
        
        Args:
            r_20c: Resistance at 20°C (Ω/1000ft)
            operating_temp_c: Operating temperature (°C)
            material: Conductor material
            
        Returns:
            Resistance at operating temperature
        """
        import math
        
        # Temperature coefficient (per °C)
        alpha = 0.00393 if material == ConductorMaterial.COPPER else 0.00403
        
        delta_t = operating_temp_c - 20.0
        r_operating = r_20c * (1.0 + alpha * delta_t)
        
        return r_operating
    
    def calculate_vd_with_reactance(
        self,
        current: float,
        distance_feet: float,
        r_ohm_per_1000ft: float,
        x_ohm_per_1000ft: float,
        voltage: float,
        power_factor: float,
        phase_type: str = 'single'
    ) -> tuple[float, float]:
        """Calculate voltage drop with reactance (R + jX).
        
        Formula (Single Phase): VD = 2 × L × I × (R×cosθ + X×sinθ) / 1000
        Formula (Three Phase):  VD = √3 × L × I × (R×cosθ + X×sinθ) / 1000
        
        Args:
            current: Load current (A)
            distance_feet: One-way distance (feet)
            r_ohm_per_1000ft: Resistance (Ω/1000ft)
            x_ohm_per_1000ft: Reactance (Ω/1000ft)
            voltage: Nominal voltage (V)
            power_factor: Power factor (0-1)
            phase_type: 'single' or 'three'
            
        Returns:
            Tuple of (voltage_drop_volts, voltage_drop_percent)
        """
        import math
        
        cos_theta = power_factor
        sin_theta = math.sqrt(1 - cos_theta**2) if cos_theta < 1.0 else 0.0
        
        # Effective impedance: Z = R×cosθ + X×sinθ
        z_eff = r_ohm_per_1000ft * cos_theta + x_ohm_per_1000ft * sin_theta
        
        # Calculate voltage drop
        if phase_type.lower() == 'three':
            # Three-phase: VD = √3 × L × I × Z / 1000
            vd_volt = math.sqrt(3) * distance_feet * current * z_eff / 1000.0
        else:
            # Single-phase: VD = 2 × L × I × Z / 1000 (round trip)
            vd_volt = 2.0 * distance_feet * current * z_eff / 1000.0
        
        vd_pct = (vd_volt / voltage) * 100.0
        
        return vd_volt, vd_pct
    
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
