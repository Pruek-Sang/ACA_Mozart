"""Breaker selector for choosing appropriate circuit protection."""

from typing import Optional

from src.dal.catalog_dal import DEFAULT_BREAKER_SPECS, CatalogDAL
from src.models.baseline import BaselineContext
from src.models.catalog_models import BreakerSpec


class BreakerSelector:
    """Selects breaker ratings based on design current."""

    def __init__(self, dal: Optional[CatalogDAL] = None):
        """Initialize breaker selector.
        
        Args:
            dal: Optional CatalogDAL for fetching breaker specs.
        """
        self.dal = dal
        self._breaker_specs: Optional[list[BreakerSpec]] = None

    def _get_breaker_specs(self) -> list[BreakerSpec]:
        """Get breaker specifications from DAL or defaults."""
        if self._breaker_specs is not None:
            return self._breaker_specs

        if self.dal is not None:
            specs = self.dal.get_breaker_specs()
            if specs:
                self._breaker_specs = specs
                return specs

        self._breaker_specs = DEFAULT_BREAKER_SPECS
        return self._breaker_specs

    def select_breaker(
        self,
        design_current_a: float,
        cable_ampacity: float = 0.0,
        poles: int = 1,
    ) -> BreakerSpec:
        """Select breaker rating for a circuit.
        
        Selection criteria (NEC/EIT):
        - In >= Ib (breaker rating >= design current)
        - In <= Iz (breaker rating <= cable ampacity) when Iz provided
        
        Args:
            design_current_a: Design current (Ib) in amperes.
            cable_ampacity: Cable ampacity (Iz) in amperes. If 0, only Ib is used.
            poles: Number of poles required.
            
        Returns:
            Selected BreakerSpec.
        """
        specs = self._get_breaker_specs()

        # Filter by poles
        matching_poles = [s for s in specs if s.poles == poles]
        if not matching_poles:
            matching_poles = specs

        # Sort by rating
        sorted_specs = sorted(matching_poles, key=lambda s: s.rating_a)

        for spec in sorted_specs:
            # Breaker rating must be >= design current
            if spec.rating_a >= design_current_a:
                # If cable ampacity is specified, check In <= Iz
                if cable_ampacity > 0 and spec.rating_a > cable_ampacity:
                    continue
                return spec

        # If no breaker fits in range, select next available above Ib
        for spec in sorted_specs:
            if spec.rating_a >= design_current_a:
                return spec

        # Fallback to largest available
        return max(sorted_specs, key=lambda s: s.rating_a)

    def select_main_breaker(
        self,
        total_demand_load_w: float,
        voltage_v: float,
        power_factor: float,
        phase_system: str = "1-phase",
    ) -> float:
        """Select main breaker rating for the project.
        
        Args:
            total_demand_load_w: Total demand load in watts.
            voltage_v: System voltage.
            power_factor: System power factor.
            phase_system: Phase system type.
            
        Returns:
            Main breaker rating in amperes.
        """
        import math

        # Calculate total current
        if voltage_v <= 0 or power_factor <= 0:
            return 100.0  # Default

        if phase_system == "3-phase":
            total_current = total_demand_load_w / (
                math.sqrt(3) * voltage_v * power_factor
            )
        else:
            total_current = total_demand_load_w / (voltage_v * power_factor)

        # Apply diversity factor (typical 0.7-0.8 for residential)
        diversified_current = total_current * 0.8

        # Select main breaker
        specs = self._get_breaker_specs()
        sorted_specs = sorted(specs, key=lambda s: s.rating_a)

        for spec in sorted_specs:
            if spec.rating_a >= diversified_current:
                return spec.rating_a

        return max(specs, key=lambda s: s.rating_a).rating_a

    def select_breakers(self, context: BaselineContext) -> BaselineContext:
        """Select breakers for all circuits in the context.
        
        Args:
            context: BaselineContext with circuits needing breakers.
            
        Returns:
            Updated BaselineContext with breaker selections.
        """
        for room in context.rooms:
            for circuit in room.circuits:
                breaker = self.select_breaker(
                    design_current_a=circuit.design_current_a,
                    poles=1,  # Assuming single phase circuits
                )
                circuit.breaker_rating_a = breaker.rating_a

        # Select main breaker
        context.main_breaker_rating_a = self.select_main_breaker(
            total_demand_load_w=context.total_demand_load_w,
            voltage_v=context.nominal_voltage,
            power_factor=context.power_factor,
            phase_system=context.phase_system,
        )

        return context
