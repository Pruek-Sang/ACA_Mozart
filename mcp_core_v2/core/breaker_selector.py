"""
MCP Core v2 Breaker Selector
Selects appropriate circuit breakers based on circuit loads and wire sizes.
"""

from typing import Optional, List, Dict, Any
from models.contracts import CircuitSpec
from models.baseline import STANDARD_BREAKER_SIZES
from dal.catalog_dal import get_catalog_dal


class BreakerSelector:
    """
    Circuit breaker selector per EIT standard.
    Ensures proper coordination between breaker and wire ampacity.
    """
    
    def __init__(self, voltage: float = 220.0):
        """
        Initialize breaker selector.
        
        Args:
            voltage: System voltage
        """
        self.voltage = voltage
        self.dal = get_catalog_dal()
    
    def calculate_minimum_rating(
        self,
        load_watts: float,
        power_factor: float = 0.9
    ) -> float:
        """
        Calculate minimum breaker rating for load.
        
        Args:
            load_watts: Circuit load in watts
            power_factor: Power factor
            
        Returns:
            Minimum breaker rating in amps
        """
        # I = P / (V × PF) × 1.25 safety factor
        current = load_watts / (self.voltage * power_factor)
        return current * 1.25
    
    def select_breaker(
        self,
        load_watts: float,
        wire_ampacity: float,
        circuit_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Select appropriate breaker size.
        
        Args:
            load_watts: Circuit load in watts
            wire_ampacity: Wire ampacity in amps
            circuit_type: Type of circuit
            
        Returns:
            Breaker selection result
        """
        min_rating = self.calculate_minimum_rating(load_watts)
        
        # Breaker must be <= wire ampacity for coordination
        max_allowed = wire_ampacity
        
        # Find standard size
        selected_size = None
        for size in STANDARD_BREAKER_SIZES:
            if size >= min_rating and size <= max_allowed:
                selected_size = size
                break
        
        # If no size fits, pick smallest that handles load
        if selected_size is None:
            for size in STANDARD_BREAKER_SIZES:
                if size >= min_rating:
                    selected_size = size
                    break
        
        # Still none? Use largest
        if selected_size is None:
            selected_size = STANDARD_BREAKER_SIZES[-1]
        
        # Get breaker spec from catalog
        breaker = self.dal.get_breaker_by_rating(selected_size)
        
        return {
            "breaker_size": selected_size,
            "min_required": min_rating,
            "wire_ampacity": wire_ampacity,
            "coordinated": selected_size <= wire_ampacity,
            "breaker_spec": breaker,
            "curve_type": "C" if circuit_type == "general" else "B",
        }
    
    def select_main_breaker(
        self,
        total_demand_load: float,
        phases: int = 1
    ) -> Dict[str, Any]:
        """
        Select main breaker for panel.
        
        Args:
            total_demand_load: Total demand load in watts
            phases: Number of phases
            
        Returns:
            Main breaker selection
        """
        if phases == 1:
            current = total_demand_load / (self.voltage * 0.9)
        else:
            # Three-phase: P = √3 × V × I × PF
            current = total_demand_load / (1.732 * self.voltage * 0.9)
        
        min_rating = current * 1.25
        
        # Select from standard sizes
        selected_size = None
        for size in STANDARD_BREAKER_SIZES:
            if size >= min_rating:
                selected_size = size
                break
        
        if selected_size is None:
            selected_size = STANDARD_BREAKER_SIZES[-1]
        
        return {
            "main_breaker_size": selected_size,
            "calculated_current": current,
            "min_required": min_rating,
            "poles": phases,
        }
    
    def check_breaker_coordination(
        self,
        breaker_size: int,
        wire_ampacity: float
    ) -> Dict[str, Any]:
        """
        Check if breaker and wire are properly coordinated.
        
        Args:
            breaker_size: Breaker rating in amps
            wire_ampacity: Wire ampacity in amps
            
        Returns:
            Coordination check result
        """
        # Per EIT: breaker rating ≤ wire ampacity
        is_coordinated = breaker_size <= wire_ampacity
        
        return {
            "coordinated": is_coordinated,
            "breaker_size": breaker_size,
            "wire_ampacity": wire_ampacity,
            "margin_amps": wire_ampacity - breaker_size,
            "message": (
                "Properly coordinated" if is_coordinated
                else "WARNING: Breaker exceeds wire ampacity"
            ),
        }
    
    def recommend_breaker_panel(
        self,
        circuits: List[CircuitSpec],
        total_demand: float
    ) -> Dict[str, Any]:
        """
        Recommend breaker panel configuration.
        
        Args:
            circuits: List of circuit specifications
            total_demand: Total demand load
            
        Returns:
            Panel recommendation
        """
        main = self.select_main_breaker(total_demand)
        
        # Count circuit types
        lighting_circuits = sum(1 for c in circuits if c.circuit_type == "lighting")
        outlet_circuits = sum(1 for c in circuits if c.circuit_type == "outlet")
        dedicated_circuits = sum(1 for c in circuits if c.circuit_type == "dedicated")
        
        total_spaces = len(circuits) + 2  # +2 for spares
        
        # Recommend panel size (round up to standard sizes)
        panel_sizes = [8, 12, 18, 24, 36, 42]
        recommended_size = next(
            (s for s in panel_sizes if s >= total_spaces),
            panel_sizes[-1]
        )
        
        return {
            "main_breaker": main,
            "total_circuits": len(circuits),
            "lighting_circuits": lighting_circuits,
            "outlet_circuits": outlet_circuits,
            "dedicated_circuits": dedicated_circuits,
            "recommended_panel_spaces": recommended_size,
            "spare_spaces": recommended_size - len(circuits),
        }
