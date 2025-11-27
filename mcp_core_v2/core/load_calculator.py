"""Load calculation module for electrical design."""

from typing import Dict, List, Any, Tuple, Optional
from models.contracts import ElectricalLoad, PanelSpecification, VoltageType
from models.baseline import NECBaseline
from config import get_settings
import logging
import math

logger = logging.getLogger(__name__)


class LoadCalculator:
    """Calculates electrical loads according to NEC standards."""
    
    def __init__(self):
        """Initialize load calculator."""
        self.nec = NECBaseline()
        self.settings = get_settings()
    
    def calculate_load_current(
        self, 
        load: ElectricalLoad,
        power_factor: Optional[float] = None
    ) -> float:
        """Calculate current for a single load."""
        pf = power_factor or load.power_factor or self.settings.default_power_factor
        power_watts = load.power_watts * load.quantity
        
        # Extract voltage value from enum
        voltage_map = {
            VoltageType.SINGLE_PHASE_120V: 120,
            VoltageType.SINGLE_PHASE_240V: 240,
            VoltageType.THREE_PHASE_208V: 208,
            VoltageType.THREE_PHASE_480V: 480
        }
        voltage = voltage_map.get(load.voltage, 120)
        
        # Calculate current based on voltage type
        if load.voltage in [VoltageType.SINGLE_PHASE_120V, VoltageType.SINGLE_PHASE_240V]:
            # Single phase: I = P / (V × PF)
            current = power_watts / (voltage * pf)
        else:
            # Three phase: I = P / (√3 × V × PF)
            current = power_watts / (math.sqrt(3) * voltage * pf)
        
        # Apply continuous load factor if applicable
        if load.is_continuous:
            current *= self.nec.continuous_load_factor
        
        return current
    
    def calculate_panel_load(
        self, 
        panel: PanelSpecification,
        loads: List[ElectricalLoad]
    ) -> Dict[str, Any]:
        """Calculate total load for a panel."""
        panel_loads = [load for load in loads if load.id in panel.feeds]
        
        total_va = 0
        total_current = 0
        load_breakdown = {}
        
        for load in panel_loads:
            current = self.calculate_load_current(load)
            va = load.power_watts * load.quantity
            
            total_current += current
            total_va += va
            
            load_breakdown[load.id] = {
                'name': load.name,
                'current': round(current, 2),
                'va': va,
                'is_continuous': load.is_continuous
            }
        
        # Apply demand factors
        demand_current = self._apply_demand_factors(panel_loads, total_current)
        
        return {
            'panel_id': panel.id,
            'total_va': round(total_va, 2),
            'total_current': round(total_current, 2),
            'demand_current': round(demand_current, 2),
            'load_breakdown': load_breakdown,
            'utilization': round((demand_current / panel.main_breaker_rating) * 100, 2)
        }
    
    def _apply_demand_factors(
        self, 
        loads: List[ElectricalLoad],
        total_current: float
    ) -> float:
        """Apply NEC demand factors to loads."""
        # Group loads by type
        lighting_va = sum(
            load.power_watts * load.quantity 
            for load in loads 
            if load.load_type.value == 'lighting'
        )
        receptacle_va = sum(
            load.power_watts * load.quantity 
            for load in loads 
            if load.load_type.value == 'receptacle'
        )
        
        demand_va = 0
        
        # Apply lighting demand factors (simplified residential calculation)
        if lighting_va > 0:
            if lighting_va <= 3000:
                demand_va += lighting_va
            elif lighting_va <= 120000:
                demand_va += 3000 + (lighting_va - 3000) * 0.35
            else:
                demand_va += 3000 + (117000 * 0.35) + (lighting_va - 120000) * 0.25
        
        # Apply receptacle demand factors
        if receptacle_va > 0:
            if receptacle_va <= 10000:
                demand_va += receptacle_va
            else:
                demand_va += 10000 + (receptacle_va - 10000) * 0.5
        
        # For other loads, use full demand
        other_va = sum(
            load.power_watts * load.quantity 
            for load in loads 
            if load.load_type.value not in ['lighting', 'receptacle']
        )
        demand_va += other_va
        
        # Convert back to current (simplified - assumes average voltage)
        demand_current = demand_va / 120  # Simplified
        
        return demand_current
    
    def calculate_voltage_drop(
        self,
        current: float,
        distance_feet: float,
        wire_size: str,
        voltage: float
    ) -> Tuple[float, float]:
        """Calculate voltage drop for a circuit."""
        from models.baseline import WireBaseline
        
        wire_baseline = WireBaseline()
        
        # Get wire resistance (ohms per 1000 feet)
        resistance_per_1000 = wire_baseline.copper_resistance.get(wire_size, 0)
        
        # Calculate total resistance (round trip)
        total_resistance = (resistance_per_1000 * distance_feet * 2) / 1000
        
        # Calculate voltage drop
        voltage_drop = current * total_resistance
        
        # Calculate percentage drop
        voltage_drop_percent = (voltage_drop / voltage) * 100
        
        return voltage_drop, voltage_drop_percent
    
    def verify_voltage_drop(
        self,
        voltage_drop_percent: float,
        is_feeder: bool = False
    ) -> Dict[str, Any]:
        """Verify voltage drop is within NEC limits."""
        limit = (
            self.nec.voltage_drop_feeder 
            if is_feeder 
            else self.nec.voltage_drop_branch
        )
        
        compliant = voltage_drop_percent <= (limit * 100)
        
        return {
            'compliant': compliant,
            'voltage_drop_percent': round(voltage_drop_percent, 2),
            'limit_percent': limit * 100,
            'margin': round((limit * 100) - voltage_drop_percent, 2)
        }


# Global instance
_load_calculator: Optional[LoadCalculator] = None


def get_load_calculator() -> LoadCalculator:
    """Get the global load calculator instance."""
    global _load_calculator
    if _load_calculator is None:
        _load_calculator = LoadCalculator()
    return _load_calculator
