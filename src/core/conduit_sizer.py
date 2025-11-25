"""Conduit sizer for calculating conduit fill and selecting sizes."""

import math
from typing import Optional

from src.dal.catalog_dal import DEFAULT_CABLE_SPECS, DEFAULT_CONDUIT_SPECS, CatalogDAL
from src.models.baseline import BaselineContext
from src.models.catalog_models import CableSpec, ConduitSpec


class ConduitSizer:
    """Calculates conduit fill and selects appropriate conduit sizes."""

    def __init__(self, dal: Optional[CatalogDAL] = None):
        """Initialize conduit sizer.
        
        Args:
            dal: Optional CatalogDAL for fetching specs.
        """
        self.dal = dal
        self._cable_specs: Optional[list[CableSpec]] = None
        self._conduit_specs: Optional[list[ConduitSpec]] = None

    def _get_cable_specs(self) -> list[CableSpec]:
        """Get cable specifications."""
        if self._cable_specs is not None:
            return self._cable_specs

        if self.dal is not None:
            specs = self.dal.get_all_cable_specs()
            if specs:
                self._cable_specs = specs
                return specs

        self._cable_specs = DEFAULT_CABLE_SPECS
        return self._cable_specs

    def _get_conduit_specs(self) -> list[ConduitSpec]:
        """Get conduit specifications."""
        if self._conduit_specs is not None:
            return self._conduit_specs

        if self.dal is not None:
            specs = self.dal.get_conduit_specs()
            if specs:
                self._conduit_specs = specs
                return specs

        self._conduit_specs = DEFAULT_CONDUIT_SPECS
        return self._conduit_specs

    def _get_wire_area(self, wire_size_sqmm: float) -> float:
        """Get wire outer area based on wire size.
        
        Args:
            wire_size_sqmm: Wire cross-sectional area.
            
        Returns:
            Wire outer cross-sectional area in sq mm.
        """
        specs = self._get_cable_specs()

        for spec in specs:
            if spec.size_sqmm == wire_size_sqmm:
                # Calculate area from outer diameter
                return math.pi * (spec.outer_diameter_mm / 2) ** 2

        # Estimate based on wire size with typical insulation
        # Outer diameter ≈ sqrt(size) * 2.5 for THW cables
        estimated_od = math.sqrt(wire_size_sqmm) * 2.5
        return math.pi * (estimated_od / 2) ** 2

    def _get_max_fill_pct(self, num_wires: int) -> float:
        """Get maximum conduit fill percentage based on number of wires.
        
        Args:
            num_wires: Number of conductors.
            
        Returns:
            Maximum fill percentage (NEC Table 1).
        """
        if num_wires == 1:
            return 53.0
        elif num_wires == 2:
            return 31.0
        else:
            return 40.0

    def select_conduit(
        self,
        wire_sizes_sqmm: list[float],
        num_conductors_per_wire: int = 3,  # L, N, PE
    ) -> tuple[float, float, ConduitSpec]:
        """Select conduit size based on wire fill requirements.
        
        Args:
            wire_sizes_sqmm: List of wire sizes in the conduit.
            num_conductors_per_wire: Number of conductors per wire (default: 3 for L+N+PE).
            
        Returns:
            Tuple of (conduit_size_mm, fill_percentage, ConduitSpec).
        """
        conduit_specs = self._get_conduit_specs()

        # Calculate total wire area
        total_wire_area = 0.0
        total_conductors = 0
        for wire_size in wire_sizes_sqmm:
            wire_area = self._get_wire_area(wire_size)
            total_wire_area += wire_area * num_conductors_per_wire
            total_conductors += num_conductors_per_wire

        # Get max fill percentage
        max_fill_pct = self._get_max_fill_pct(total_conductors)

        # Find smallest conduit that fits
        for spec in sorted(conduit_specs, key=lambda s: s.size_mm):
            available_area = spec.internal_area_sqmm * (max_fill_pct / 100)
            if available_area >= total_wire_area:
                fill_pct = (total_wire_area / spec.internal_area_sqmm) * 100
                return spec.size_mm, fill_pct, spec

        # Use largest available if none fits
        largest = max(conduit_specs, key=lambda s: s.size_mm)
        fill_pct = (total_wire_area / largest.internal_area_sqmm) * 100
        return largest.size_mm, fill_pct, largest

    def size_conduits(self, context: BaselineContext) -> BaselineContext:
        """Size conduits for all circuits in the context.
        
        Each circuit gets its own conduit (conservative approach).
        
        Args:
            context: BaselineContext with circuits needing conduit sizing.
            
        Returns:
            Updated BaselineContext with conduit sizes.
        """
        for room in context.rooms:
            for circuit in room.circuits:
                conduit_size, fill_pct, _ = self.select_conduit(
                    wire_sizes_sqmm=[circuit.wire_size_sqmm],
                    num_conductors_per_wire=3,  # L, N, PE
                )

                circuit.conduit_size_mm = conduit_size
                circuit.conduit_fill_pct = fill_pct

        return context
