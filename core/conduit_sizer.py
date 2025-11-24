"""Conduit sizer for MCP Core v2.

Estimates conduit sizes based on wire quantities and fill ratio
requirements.
"""

import logging
import math
from typing import List, Optional
from dataclasses import dataclass

from models.catalog_models import CableSpec, ConduitSpec
from dal.catalog_dal import CatalogDAL

logger = logging.getLogger(__name__)


@dataclass
class ConduitSizingResult:
    """Result of conduit sizing calculation."""
    
    conduit_size_mm: int
    conduit_type: str
    inner_diameter_mm: float
    required_area_mm2: float
    available_area_mm2: float
    fill_ratio_percent: float
    num_conductors: int
    meets_fill_limit: bool


class ConduitSizer:
    """Estimates conduit sizes based on conductor fill requirements."""

    # Maximum fill percentages per NEC/local codes
    MAX_FILL_ONE_WIRE = 53.0  # 1 conductor
    MAX_FILL_TWO_WIRES = 31.0  # 2 conductors
    MAX_FILL_THREE_PLUS = 40.0  # 3+ conductors

    def __init__(self, catalog_dal: CatalogDAL):
        """Initialize conduit sizer.
        
        Args:
            catalog_dal: Catalog data access object
        """
        self._catalog = catalog_dal
        self._conduit_specs: List[ConduitSpec] = []
        self._cable_specs: List[CableSpec] = []

    def _get_conduit_specs(self) -> List[ConduitSpec]:
        """Get and cache conduit specifications."""
        if not self._conduit_specs:
            self._conduit_specs = self._catalog.get_conduit_specs()
        return self._conduit_specs

    def _get_cable_specs(self) -> List[CableSpec]:
        """Get and cache cable specifications."""
        if not self._cable_specs:
            self._cable_specs = self._catalog.get_cable_specs()
        return self._cable_specs

    def size_conduit(
        self,
        wire_size_mm2: float,
        num_conductors: int = 2,  # Default: live + neutral
        include_ground: bool = True
    ) -> ConduitSizingResult:
        """Size conduit for given wire configuration.
        
        Args:
            wire_size_mm2: Wire cross-sectional area in mm²
            num_conductors: Number of insulated conductors
            include_ground: Whether to include ground wire
            
        Returns:
            ConduitSizingResult with selected conduit
        """
        total_conductors = num_conductors
        if include_ground:
            total_conductors += 1
        
        logger.debug(
            f"Sizing conduit for {total_conductors} × {wire_size_mm2}mm² conductors"
        )
        
        # Get wire outer diameter
        cable_spec = self._find_cable_spec(wire_size_mm2)
        if cable_spec:
            wire_od = cable_spec.outer_diameter_mm
        else:
            # Estimate outer diameter from cross-section
            # Approximate: OD ≈ 1.6 × √(area) for THW
            wire_od = 1.6 * math.sqrt(wire_size_mm2)
        
        # Calculate total wire area
        wire_area = math.pi * (wire_od / 2) ** 2
        total_wire_area = wire_area * total_conductors
        
        # Get maximum fill percentage
        max_fill = self._get_max_fill_percent(total_conductors)
        
        # Required conduit area
        required_conduit_area = total_wire_area / (max_fill / 100)
        
        # Find suitable conduit
        conduits = self._get_conduit_specs()
        selected_conduit: Optional[ConduitSpec] = None
        
        for conduit in conduits:
            conduit_area = math.pi * (conduit.inner_diameter_mm / 2) ** 2
            if conduit_area >= required_conduit_area:
                selected_conduit = conduit
                break
        
        if selected_conduit is None:
            # Use largest available
            selected_conduit = conduits[-1] if conduits else None
        
        if selected_conduit:
            conduit_area = math.pi * (selected_conduit.inner_diameter_mm / 2) ** 2
            actual_fill = (total_wire_area / conduit_area) * 100
            
            return ConduitSizingResult(
                conduit_size_mm=selected_conduit.nominal_size_mm,
                conduit_type=selected_conduit.conduit_type,
                inner_diameter_mm=selected_conduit.inner_diameter_mm,
                required_area_mm2=total_wire_area,
                available_area_mm2=conduit_area,
                fill_ratio_percent=actual_fill,
                num_conductors=total_conductors,
                meets_fill_limit=actual_fill <= max_fill,
            )
        
        # Fallback
        return ConduitSizingResult(
            conduit_size_mm=20,
            conduit_type="EMT",
            inner_diameter_mm=20.9,
            required_area_mm2=total_wire_area,
            available_area_mm2=137.2,
            fill_ratio_percent=total_wire_area / 137.2 * 100,
            num_conductors=total_conductors,
            meets_fill_limit=True,
        )

    def _find_cable_spec(self, size_mm2: float) -> Optional[CableSpec]:
        """Find cable specification by size."""
        specs = self._get_cable_specs()
        for spec in specs:
            if abs(spec.size_mm2 - size_mm2) < 0.1:
                return spec
        return None

    def _get_max_fill_percent(self, num_conductors: int) -> float:
        """Get maximum fill percentage based on conductor count."""
        if num_conductors == 1:
            return self.MAX_FILL_ONE_WIRE
        elif num_conductors == 2:
            return self.MAX_FILL_TWO_WIRES
        else:
            return self.MAX_FILL_THREE_PLUS

    def estimate_total_conduit_length(
        self,
        wire_run_length_m: float,
        num_bends: int = 2,
        pullbox_spacing_m: float = 30.0
    ) -> float:
        """Estimate total conduit length including fittings.
        
        Args:
            wire_run_length_m: Straight-line wire run length
            num_bends: Number of bends in the run
            pullbox_spacing_m: Maximum distance between pull boxes
            
        Returns:
            Estimated total conduit length in meters
        """
        # Add allowance for bends (approx 0.3m per bend)
        bend_allowance = num_bends * 0.3
        
        # Calculate number of pull boxes needed
        num_pullboxes = max(0, int(wire_run_length_m / pullbox_spacing_m))
        
        # Add allowance for each pull box (0.2m)
        pullbox_allowance = num_pullboxes * 0.2
        
        # Total including 10% contingency
        total = (wire_run_length_m + bend_allowance + pullbox_allowance) * 1.1
        
        return total
