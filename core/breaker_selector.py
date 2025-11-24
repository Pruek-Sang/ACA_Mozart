"""Breaker selector for MCP Core v2.

Selects appropriate protection devices (circuit breakers) based on
circuit current and coordination requirements.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

from models.baseline import BaselineCircuit, CircuitType
from models.catalog_models import BreakerSpec
from dal.catalog_dal import CatalogDAL

logger = logging.getLogger(__name__)


@dataclass
class BreakerSelectionResult:
    """Result of breaker selection."""
    
    breaker_rating_a: int
    breaker_type: str
    breaking_capacity_ka: float
    trip_curve: str
    poles: int
    min_wire_size_mm2: float
    max_wire_size_mm2: float
    selection_reason: str


class BreakerSelector:
    """Selects circuit breakers based on load and protection requirements."""

    # Standard breaker ratings (Amps)
    STANDARD_RATINGS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100]

    def __init__(self, catalog_dal: CatalogDAL):
        """Initialize breaker selector.
        
        Args:
            catalog_dal: Catalog data access object
        """
        self._catalog = catalog_dal
        self._breaker_specs: List[BreakerSpec] = []

    def _get_breaker_specs(self) -> List[BreakerSpec]:
        """Get and cache breaker specifications."""
        if not self._breaker_specs:
            self._breaker_specs = self._catalog.get_breaker_specs()
        return self._breaker_specs

    def select_breaker(
        self,
        circuit: BaselineCircuit,
        wire_ampacity: float,
        actual_current: Optional[float] = None
    ) -> BreakerSelectionResult:
        """Select breaker for a circuit.
        
        Selection criteria:
        1. Breaker rating >= 1.25 × design current (startup allowance)
        2. Breaker rating <= wire ampacity (cable protection)
        3. Breaker rating should be a standard size
        
        Args:
            circuit: Circuit to select breaker for
            wire_ampacity: Ampacity of selected wire
            actual_current: Actual current if different from design current
            
        Returns:
            BreakerSelectionResult with selected breaker
        """
        current = actual_current if actual_current is not None else circuit.design_current_a
        
        logger.debug(f"Selecting breaker for {circuit.name}: {current:.2f}A")
        
        # Calculate minimum required rating
        min_rating = self._calculate_min_rating(current, circuit.circuit_type)
        
        # Maximum rating cannot exceed wire ampacity
        max_rating = int(wire_ampacity)
        
        # Find suitable breaker
        specs = self._get_breaker_specs()
        
        # Filter to standard ratings in valid range
        valid_ratings = [
            r for r in self.STANDARD_RATINGS
            if r >= min_rating and r <= max_rating
        ]
        
        if not valid_ratings:
            # If no valid rating, use minimum that protects the wire
            valid_ratings = [
                r for r in self.STANDARD_RATINGS
                if r <= max_rating
            ]
            if not valid_ratings:
                # Last resort: use maximum standard that's reasonable
                valid_ratings = [max(r for r in self.STANDARD_RATINGS if r <= 63)]
        
        selected_rating = min(valid_ratings) if valid_ratings else 16
        
        # Find matching spec or use defaults
        spec = self._find_spec_by_rating(selected_rating, specs)
        
        reason = self._get_selection_reason(
            current, min_rating, max_rating, selected_rating, circuit.circuit_type
        )
        
        logger.debug(f"Selected {selected_rating}A breaker: {reason}")
        
        return BreakerSelectionResult(
            breaker_rating_a=selected_rating,
            breaker_type=spec.breaker_type if spec else "MCB",
            breaking_capacity_ka=spec.breaking_capacity_ka if spec else 6.0,
            trip_curve=spec.trip_curve if spec else "C",
            poles=spec.poles if spec else 1,
            min_wire_size_mm2=spec.min_wire_size_mm2 if spec else 1.5,
            max_wire_size_mm2=spec.max_wire_size_mm2 if spec else 16.0,
            selection_reason=reason,
        )

    def _calculate_min_rating(self, current: float, circuit_type: CircuitType) -> int:
        """Calculate minimum breaker rating for a given current.
        
        Args:
            current: Design current in Amps
            circuit_type: Type of circuit
            
        Returns:
            Minimum breaker rating in Amps
        """
        # Apply multiplier based on circuit type
        multipliers = {
            CircuitType.LIGHTING: 1.0,  # No startup surge
            CircuitType.OUTLET: 1.25,   # General startup allowance
            CircuitType.DEDICATED: 1.25, # Motor starting, etc.
        }
        
        multiplier = multipliers.get(circuit_type, 1.25)
        min_rating = int(current * multiplier)
        
        # Round up to nearest standard rating
        for rating in self.STANDARD_RATINGS:
            if rating >= min_rating:
                return rating
        
        return self.STANDARD_RATINGS[-1]

    def _find_spec_by_rating(
        self,
        rating: int,
        specs: List[BreakerSpec]
    ) -> Optional[BreakerSpec]:
        """Find breaker spec matching the rating."""
        for spec in specs:
            if spec.rating_a == rating:
                return spec
        return None

    def _get_selection_reason(
        self,
        current: float,
        min_rating: int,
        max_rating: int,
        selected: int,
        circuit_type: CircuitType
    ) -> str:
        """Generate human-readable selection reason."""
        reasons = []
        
        reasons.append(f"Design current: {current:.1f}A")
        reasons.append(f"Min rating required: {min_rating}A")
        reasons.append(f"Max rating (wire protection): {max_rating}A")
        
        if circuit_type == CircuitType.DEDICATED:
            reasons.append("Dedicated circuit - 125% startup allowance")
        
        return "; ".join(reasons)

    def select_main_breaker(
        self,
        total_demand_load_w: float,
        voltage: float = 220.0,
        power_factor: float = 0.85,
        diversity_factor: float = 0.7
    ) -> int:
        """Select main breaker rating for entire installation.
        
        Args:
            total_demand_load_w: Total demand load in Watts
            voltage: System voltage
            power_factor: Average power factor
            diversity_factor: Diversity factor for multiple circuits
            
        Returns:
            Main breaker rating in Amps
        """
        # Apply diversity factor
        diversified_load = total_demand_load_w * diversity_factor
        
        # Calculate current
        total_current = diversified_load / (voltage * power_factor)
        
        # Add 25% margin and round up to standard rating
        required_rating = total_current * 1.25
        
        # Find suitable main breaker rating
        main_ratings = [32, 40, 50, 63, 80, 100, 125, 160, 200]
        
        for rating in main_ratings:
            if rating >= required_rating:
                return rating
        
        return main_ratings[-1]
