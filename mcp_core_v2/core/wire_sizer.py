"""
MCP Core v2 Wire Sizer
Selects appropriate wire sizes based on circuit loads.
"""

from typing import Optional, List, Dict, Any
from models.contracts import CircuitSpec
from models.baseline import WIRE_SIZE_TABLE
from dal.catalog_dal import get_catalog_dal


class WireSizer:
    """
    Wire sizing calculator per EIT standard.
    Accounts for current, voltage drop, and conduit derating.
    """
    
    # Safety factor per EIT (125% for continuous loads)
    SAFETY_FACTOR = 1.25
    
    # Temperature derating factors
    TEMP_DERATING = {
        30: 1.00,
        35: 0.94,
        40: 0.87,
        45: 0.79,
        50: 0.71,
    }
    
    # Conduit fill derating (number of current-carrying conductors)
    CONDUCTOR_DERATING = {
        1: 1.00,
        2: 1.00,
        3: 0.80,
        4: 0.80,
        5: 0.80,
        6: 0.80,
        7: 0.70,
        8: 0.70,
        9: 0.70,
    }
    
    def __init__(self, voltage: float = 220.0, ambient_temp: int = 30):
        """
        Initialize wire sizer.
        
        Args:
            voltage: System voltage
            ambient_temp: Ambient temperature in Celsius
        """
        self.voltage = voltage
        self.ambient_temp = ambient_temp
        self.dal = get_catalog_dal()
    
    def calculate_required_ampacity(
        self,
        load_watts: float,
        power_factor: float = 0.9,
        num_conductors: int = 2
    ) -> float:
        """
        Calculate required wire ampacity.
        
        Args:
            load_watts: Circuit load in watts
            power_factor: Power factor
            num_conductors: Number of current-carrying conductors
            
        Returns:
            Required ampacity in amps
        """
        # Base current
        current = load_watts / (self.voltage * power_factor)
        
        # Apply safety factor
        design_current = current * self.SAFETY_FACTOR
        
        # Apply derating factors
        temp_factor = self.TEMP_DERATING.get(self.ambient_temp, 1.0)
        conductor_factor = self.CONDUCTOR_DERATING.get(
            min(num_conductors, 9), 0.70
        )
        
        # Required ampacity = design current / derating
        required = design_current / (temp_factor * conductor_factor)
        
        return required
    
    def select_wire_size(
        self,
        load_watts: float,
        power_factor: float = 0.9,
        max_voltage_drop_percent: float = 3.0,
        length_m: float = 20.0
    ) -> Dict[str, Any]:
        """
        Select appropriate wire size.
        
        Args:
            load_watts: Circuit load in watts
            power_factor: Power factor
            max_voltage_drop_percent: Maximum allowed voltage drop
            length_m: Circuit length in meters
            
        Returns:
            Wire selection result
        """
        required_ampacity = self.calculate_required_ampacity(load_watts, power_factor)
        
        # Get wire from catalog/baseline
        wire = self.dal.get_wire_for_current(required_ampacity)
        
        if wire:
            selected_size = wire.size_sqmm
            max_amps = wire.max_current_amp
        else:
            # Fallback to table lookup
            result = self._select_from_table(required_ampacity)
            selected_size = result["size_sqmm"]
            max_amps = result["max_amps"]
        
        # Check voltage drop
        vdrop = self._calculate_voltage_drop(
            load_watts, selected_size, length_m, power_factor
        )
        
        # If voltage drop too high, upsize wire
        while vdrop > max_voltage_drop_percent:
            next_size = self._get_next_size(selected_size)
            if next_size is None:
                break
            selected_size = next_size["size_sqmm"]
            max_amps = next_size["max_amps"]
            vdrop = self._calculate_voltage_drop(
                load_watts, selected_size, length_m, power_factor
            )
        
        return {
            "wire_size_sqmm": selected_size,
            "max_ampacity": max_amps,
            "required_ampacity": required_ampacity,
            "voltage_drop_percent": vdrop,
            "compliant": vdrop <= max_voltage_drop_percent,
            "length_m": length_m,
        }
    
    def _select_from_table(self, required_amps: float) -> Dict[str, Any]:
        """Select wire from baseline table."""
        for wire in WIRE_SIZE_TABLE:
            if wire["max_amps"] >= required_amps:
                return wire
        # Return largest if nothing fits
        return WIRE_SIZE_TABLE[-1]
    
    def _get_next_size(self, current_size: float) -> Optional[Dict[str, Any]]:
        """Get next larger wire size."""
        found_current = False
        for wire in WIRE_SIZE_TABLE:
            if found_current:
                return wire
            if wire["size_sqmm"] == current_size:
                found_current = True
        return None
    
    def _calculate_voltage_drop(
        self,
        load_watts: float,
        wire_size_sqmm: float,
        length_m: float,
        power_factor: float
    ) -> float:
        """
        Calculate voltage drop percentage.
        
        Args:
            load_watts: Load in watts
            wire_size_sqmm: Wire size in mm²
            length_m: One-way length in meters
            power_factor: Power factor
            
        Returns:
            Voltage drop as percentage
        """
        # Current
        current = load_watts / (self.voltage * power_factor)
        
        # Resistance (copper at 70°C): ρ ≈ 0.0225 Ω·mm²/m
        resistivity = 0.0225
        resistance = (resistivity * length_m * 2) / wire_size_sqmm  # Round trip
        
        # Voltage drop
        v_drop = current * resistance
        v_drop_percent = (v_drop / self.voltage) * 100
        
        return v_drop_percent
    
    def size_for_circuit(self, circuit: CircuitSpec, length_m: float = 20.0) -> Dict[str, Any]:
        """
        Size wire for a specific circuit.
        
        Args:
            circuit: Circuit specification
            length_m: Circuit length
            
        Returns:
            Wire sizing result
        """
        return self.select_wire_size(
            load_watts=circuit.total_load,
            length_m=length_m
        )
