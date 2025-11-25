"""Wire sizer for selecting appropriate wire sizes based on current and voltage drop."""

from typing import Optional

from src.dal.catalog_dal import DEFAULT_CABLE_SPECS, CatalogDAL
from src.models.baseline import BaselineContext
from src.models.catalog_models import CableSpec


class WireSizer:
    """Selects wire sizes based on design current and voltage drop limits."""

    # Maximum voltage drop limits (NEC/EIT standards)
    MAX_BRANCH_VD_PCT = 3.0  # 3% for branch circuits
    MAX_TOTAL_VD_PCT = 5.0  # 5% total
    
    # Safety factor for continuous loads (NEC 210.19(A)(1))
    AMPACITY_SAFETY_FACTOR = 1.25

    def __init__(self, dal: Optional[CatalogDAL] = None):
        """Initialize wire sizer.
        
        Args:
            dal: Optional CatalogDAL for fetching cable specs.
        """
        self.dal = dal
        self._cable_specs: Optional[list[CableSpec]] = None

    def _get_cable_specs(self) -> list[CableSpec]:
        """Get cable specifications from DAL or defaults."""
        if self._cable_specs is not None:
            return self._cable_specs

        if self.dal is not None:
            specs = self.dal.get_cable_specs(material="copper")
            if specs:
                self._cable_specs = specs
                return specs

        self._cable_specs = DEFAULT_CABLE_SPECS
        return self._cable_specs

    def _get_ampacity(self, spec: CableSpec, ambient_temp: float) -> float:
        """Get cable ampacity adjusted for ambient temperature.
        
        Args:
            spec: Cable specification.
            ambient_temp: Ambient temperature in Celsius.
            
        Returns:
            Adjusted ampacity in amperes.
        """
        if ambient_temp <= 30:
            return spec.ampacity_30c
        elif ambient_temp <= 40:
            return spec.ampacity_40c
        elif spec.ampacity_45c > 0 and ambient_temp <= 45:
            return spec.ampacity_45c
        else:
            # Apply derating factor for higher temperatures
            # Approximately 2% per degree above 30°C
            derating = max(0.5, 1 - (ambient_temp - 30) * 0.02)
            return spec.ampacity_30c * derating

    def _calculate_voltage_drop_pct(
        self,
        current_a: float,
        length_m: float,
        spec: CableSpec,
        voltage_v: float,
    ) -> float:
        """Calculate voltage drop percentage for a cable.
        
        Args:
            current_a: Current in amperes.
            length_m: Cable length in meters.
            spec: Cable specification.
            voltage_v: Operating voltage.
            
        Returns:
            Voltage drop percentage.
        """
        if voltage_v <= 0 or length_m <= 0:
            return 0.0

        # VD = 2 * I * L * R / 1000 (for single phase)
        # where R is in ohm/km and L is in meters
        vd_v = 2 * current_a * (length_m / 1000) * spec.resistance_ohm_km
        vd_pct = (vd_v / voltage_v) * 100

        return vd_pct

    def select_wire_size(
        self,
        design_current_a: float,
        cable_length_m: float,
        voltage_v: float,
        ambient_temp: float = 40.0,
        max_vd_pct: float = 3.0,
    ) -> tuple[float, CableSpec]:
        """Select minimum wire size meeting current and voltage drop requirements.
        
        Selection criteria (NEC/EIT):
        1. Ampacity >= 1.25 * Ib (design current) for continuous loads
        2. Voltage drop <= max_vd_pct (typically 3% for branch)
        
        Args:
            design_current_a: Design current (Ib) in amperes.
            cable_length_m: Cable length in meters.
            voltage_v: Operating voltage.
            ambient_temp: Ambient temperature for derating.
            max_vd_pct: Maximum allowed voltage drop percentage.
            
        Returns:
            Tuple of (wire_size_sqmm, CableSpec).
        """
        specs = self._get_cable_specs()
        required_ampacity = design_current_a * self.AMPACITY_SAFETY_FACTOR

        for spec in sorted(specs, key=lambda s: s.size_sqmm):
            ampacity = self._get_ampacity(spec, ambient_temp)

            # Check ampacity requirement
            if ampacity < required_ampacity:
                continue

            # Check voltage drop requirement
            vd_pct = self._calculate_voltage_drop_pct(
                design_current_a, cable_length_m, spec, voltage_v
            )
            if vd_pct <= max_vd_pct:
                return spec.size_sqmm, spec

        # If no cable meets VD requirement, select by ampacity only
        for spec in sorted(specs, key=lambda s: s.size_sqmm):
            ampacity = self._get_ampacity(spec, ambient_temp)
            if ampacity >= required_ampacity:
                return spec.size_sqmm, spec

        # Fallback to largest available
        largest = max(specs, key=lambda s: s.size_sqmm)
        return largest.size_sqmm, largest

    def size_wires(self, context: BaselineContext) -> BaselineContext:
        """Size wires for all circuits in the context.
        
        Args:
            context: BaselineContext with circuits to size.
            
        Returns:
            Updated BaselineContext with wire sizes.
        """
        for room in context.rooms:
            for circuit in room.circuits:
                wire_size, spec = self.select_wire_size(
                    design_current_a=circuit.design_current_a,
                    cable_length_m=circuit.cable_length_m,
                    voltage_v=circuit.voltage_v,
                    ambient_temp=context.ambient_temp_c,
                    max_vd_pct=self.MAX_BRANCH_VD_PCT,
                )

                circuit.wire_size_sqmm = wire_size
                circuit.cable_type = spec.insulation_type
                circuit.cable_material = spec.material

        return context
