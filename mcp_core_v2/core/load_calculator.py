"""
MCP Core v2 Load Calculator
Calculates electrical loads for rooms and circuits.
"""

from typing import Dict, Any, List, Tuple
from models.contracts import (
    RoomInput,
    RoomType,
    OutletPlacement,
    LightPlacement,
)
from models.baseline import DEMAND_FACTORS


class LoadCalculator:
    """
    Calculates electrical loads per EIT standard.
    Applies demand factors for total load calculations.
    """
    
    # Standard load assumptions
    OUTLET_WATTS = 180  # Watts per general outlet
    DEDICATED_OUTLET_WATTS = {
        "refrigerator": 350,
        "microwave": 1200,
        "washing_machine": 500,
        "dryer": 2500,
        "dishwasher": 1500,
        "ac_unit": 1500,  # Per ton
        "water_heater": 3000,
    }
    
    def __init__(self, voltage: float = 220.0):
        self.voltage = voltage
    
    def calculate_outlet_load(
        self,
        outlets: List[OutletPlacement],
        room_type: RoomType
    ) -> float:
        """
        Calculate total outlet load in watts.
        
        Args:
            outlets: List of outlet placements
            room_type: Type of room
            
        Returns:
            Total watts
        """
        total = 0.0
        for outlet in outlets:
            if outlet.outlet_type.value == "dedicated":
                # Use higher load for dedicated outlets
                total += self.DEDICATED_OUTLET_WATTS.get("ac_unit", 1500)
            else:
                total += self.OUTLET_WATTS
        
        return total
    
    def calculate_lighting_load(self, lights: List[LightPlacement]) -> float:
        """
        Calculate total lighting load in watts.
        
        Args:
            lights: List of light placements
            
        Returns:
            Total watts
        """
        return sum(light.wattage for light in lights)
    
    def calculate_special_loads(self, special_loads: List[Dict[str, Any]]) -> float:
        """
        Calculate special equipment loads.
        
        Args:
            special_loads: List of special load specifications
            
        Returns:
            Total watts
        """
        if not special_loads:
            return 0.0
        
        total = 0.0
        for load in special_loads:
            load_type = load.get("type", "")
            quantity = load.get("quantity", 1)
            watts = load.get("watts", 0)
            
            if watts:
                total += watts * quantity
            elif load_type in self.DEDICATED_OUTLET_WATTS:
                total += self.DEDICATED_OUTLET_WATTS[load_type] * quantity
        
        return total
    
    def calculate_room_connected_load(
        self,
        outlets: List[OutletPlacement],
        lights: List[LightPlacement],
        room: RoomInput
    ) -> float:
        """
        Calculate total connected load for a room.
        
        Args:
            outlets: Outlet placements
            lights: Light placements
            room: Room input specification
            
        Returns:
            Total connected load in watts
        """
        outlet_load = self.calculate_outlet_load(outlets, room.room_type)
        lighting_load = self.calculate_lighting_load(lights)
        special_load = self.calculate_special_loads(room.special_loads or [])
        
        return outlet_load + lighting_load + special_load
    
    def apply_demand_factor(
        self,
        connected_load: float,
        load_type: str = "general"
    ) -> float:
        """
        Apply demand factor to get demand load.
        
        Args:
            connected_load: Total connected load
            load_type: Type of load for factor selection
            
        Returns:
            Demand load in watts
        """
        if load_type == "lighting":
            # First 2000W at 100%, rest at 35%
            if connected_load <= 2000:
                return connected_load
            return 2000 + (connected_load - 2000) * 0.35
        
        elif load_type == "outlet":
            # First 10kW at 100%, over at 50%
            if connected_load <= 10000:
                return connected_load
            return 10000 + (connected_load - 10000) * 0.5
        
        elif load_type == "ac":
            # 100% of largest + 75% of others
            return connected_load  # Simplified
        
        # Default: no reduction
        return connected_load
    
    def calculate_circuit_load(
        self,
        devices: List[Any],
        circuit_type: str
    ) -> float:
        """
        Calculate load for a specific circuit.
        
        Args:
            devices: List of devices on circuit
            circuit_type: Type of circuit (lighting, outlet, dedicated)
            
        Returns:
            Circuit load in watts
        """
        if circuit_type == "lighting":
            return sum(d.wattage for d in devices if hasattr(d, 'wattage'))
        elif circuit_type == "outlet":
            return len(devices) * self.OUTLET_WATTS
        elif circuit_type == "dedicated":
            return sum(
                getattr(d, 'watts', 1500) for d in devices
            )
        return 0.0
    
    def watts_to_amps(self, watts: float, power_factor: float = 0.9) -> float:
        """
        Convert watts to amps.
        
        Args:
            watts: Power in watts
            power_factor: Power factor (default 0.9)
            
        Returns:
            Current in amps
        """
        return watts / (self.voltage * power_factor)
    
    def calculate_total_demand(
        self,
        room_loads: List[Tuple[float, float, float]]
    ) -> float:
        """
        Calculate total demand load for multiple rooms.
        
        Args:
            room_loads: List of (outlet_load, lighting_load, special_load) tuples
            
        Returns:
            Total demand load in watts
        """
        total_outlet = sum(r[0] for r in room_loads)
        total_lighting = sum(r[1] for r in room_loads)
        total_special = sum(r[2] for r in room_loads)
        
        demand_outlet = self.apply_demand_factor(total_outlet, "outlet")
        demand_lighting = self.apply_demand_factor(total_lighting, "lighting")
        demand_special = total_special  # Usually 100%
        
        return demand_outlet + demand_lighting + demand_special
