"""Wire sizer for MCP Core v2.

Selects appropriate wire sizes based on ampacity requirements and
voltage drop constraints.
"""

import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

from models.baseline import BaselineCircuit
from models.catalog_models import CableSpec
from dal.catalog_dal import CatalogDAL

logger = logging.getLogger(__name__)


@dataclass
class WireSizingResult:
    """Result of wire sizing calculation."""
    
    wire_size_mm2: float
    wire_type: str
    ampacity_a: float
    resistance_ohm_per_km: float
    calculated_voltage_drop_percent: float
    total_length_m: float
    meets_ampacity: bool
    meets_voltage_drop: bool


class WireSizer:
    """Selects wire sizes based on ampacity and voltage drop."""

    def __init__(
        self,
        catalog_dal: CatalogDAL,
        voltage: float = 220.0,
        voltage_drop_limit: float = 3.0
    ):
        """Initialize wire sizer.
        
        Args:
            catalog_dal: Catalog data access object
            voltage: Nominal system voltage
            voltage_drop_limit: Maximum allowed voltage drop percentage
        """
        self._catalog = catalog_dal
        self._voltage = voltage
        self._vdrop_limit = voltage_drop_limit
        self._cable_specs: List[CableSpec] = []

    def _get_cable_specs(self) -> List[CableSpec]:
        """Get and cache cable specifications."""
        if not self._cable_specs:
            self._cable_specs = self._catalog.get_cable_specs()
        return self._cable_specs

    def size_wire(
        self,
        circuit: BaselineCircuit,
        actual_current: Optional[float] = None
    ) -> WireSizingResult:
        """Size wire for a circuit.
        
        Args:
            circuit: Circuit to size wire for
            actual_current: Actual measured/calculated current (uses design current if not provided)
            
        Returns:
            WireSizingResult with selected wire and calculations
        """
        current = actual_current if actual_current is not None else circuit.design_current_a
        distance_m = circuit.distance_from_panel_m
        
        logger.debug(f"Sizing wire for {circuit.name}: {current:.2f}A, {distance_m:.1f}m")
        
        # Get available cable specs
        cables = self._get_cable_specs()
        
        # Find minimum wire size that meets ampacity
        suitable_cables = [
            cable for cable in cables
            if cable.ampacity_in_conduit_a >= current * 1.25  # 125% margin
        ]
        
        if not suitable_cables:
            # Use largest available
            logger.warning(f"No cable with sufficient ampacity for {current:.2f}A, using largest")
            suitable_cables = [cables[-1]] if cables else []
        
        # Check voltage drop for each suitable cable
        best_cable: Optional[CableSpec] = None
        best_result: Optional[WireSizingResult] = None
        
        for cable in suitable_cables:
            vdrop = self._calculate_voltage_drop(
                current=current,
                length_m=distance_m,
                r_ohm_per_km=cable.resistance_ohm_per_km,
                x_ohm_per_km=cable.reactance_ohm_per_km,
                power_factor=self._get_circuit_pf(circuit)
            )
            
            meets_vdrop = vdrop <= self._vdrop_limit
            meets_ampacity = cable.ampacity_in_conduit_a >= current
            
            result = WireSizingResult(
                wire_size_mm2=cable.size_mm2,
                wire_type=cable.insulation_type,
                ampacity_a=cable.ampacity_in_conduit_a,
                resistance_ohm_per_km=cable.resistance_ohm_per_km,
                calculated_voltage_drop_percent=vdrop,
                total_length_m=distance_m * 2,  # Round trip
                meets_ampacity=meets_ampacity,
                meets_voltage_drop=meets_vdrop,
            )
            
            if meets_vdrop and meets_ampacity:
                best_cable = cable
                best_result = result
                break
            elif best_result is None or vdrop < best_result.calculated_voltage_drop_percent:
                best_cable = cable
                best_result = result
        
        if best_result is None:
            # Fallback to minimum size
            best_result = WireSizingResult(
                wire_size_mm2=1.5,
                wire_type="THW",
                ampacity_a=14,
                resistance_ohm_per_km=12.1,
                calculated_voltage_drop_percent=0.0,
                total_length_m=distance_m * 2,
                meets_ampacity=False,
                meets_voltage_drop=False,
            )
        
        logger.debug(
            f"Selected {best_result.wire_size_mm2}mm² for {circuit.name}: "
            f"vdrop={best_result.calculated_voltage_drop_percent:.2f}%"
        )
        
        return best_result

    def _calculate_voltage_drop(
        self,
        current: float,
        length_m: float,
        r_ohm_per_km: float,
        x_ohm_per_km: float,
        power_factor: float = 0.85
    ) -> float:
        """Calculate voltage drop percentage.
        
        Uses the formula:
        Vdrop% = (2 * I * L * (R*cos(θ) + X*sin(θ))) / V * 100
        
        For single-phase circuits.
        
        Args:
            current: Current in Amps
            length_m: One-way length in meters
            r_ohm_per_km: Resistance in Ω/km
            x_ohm_per_km: Reactance in Ω/km
            power_factor: Circuit power factor
            
        Returns:
            Voltage drop as percentage
        """
        import math
        
        # Convert length to km
        length_km = length_m / 1000
        
        # Calculate sin(θ) from power factor
        cos_theta = power_factor
        sin_theta = math.sqrt(1 - cos_theta**2)
        
        # Impedance drop per unit length
        z_drop = r_ohm_per_km * cos_theta + x_ohm_per_km * sin_theta
        
        # Total voltage drop (2x for round trip in single phase)
        v_drop = 2 * current * length_km * z_drop
        
        # Percentage of nominal voltage
        vdrop_percent = (v_drop / self._voltage) * 100
        
        return vdrop_percent

    def _get_circuit_pf(self, circuit: BaselineCircuit) -> float:
        """Get weighted average power factor for circuit."""
        if not circuit.loads or circuit.total_connected_load_w == 0:
            return 0.85
        
        weighted_pf = sum(
            load.watts * load.quantity * load.power_factor
            for load in circuit.loads
        ) / circuit.total_connected_load_w
        
        return min(max(weighted_pf, 0.5), 1.0)

    def get_minimum_wire_for_breaker(self, breaker_rating_a: int) -> float:
        """Get minimum wire size for a given breaker rating.
        
        Args:
            breaker_rating_a: Breaker current rating
            
        Returns:
            Minimum wire size in mm²
        """
        # Standard minimum wire sizes for breaker ratings
        breaker_wire_map = {
            6: 1.5,
            10: 1.5,
            16: 2.5,
            20: 2.5,
            25: 4.0,
            32: 6.0,
            40: 10.0,
            50: 16.0,
            63: 16.0,
        }
        
        return breaker_wire_map.get(breaker_rating_a, 2.5)
