"""
MCP Core v2 Conduit Sizer
Selects appropriate conduit sizes based on wire fill requirements.
"""

from typing import List, Dict, Any
from math import pi, ceil
from models.baseline import WIRE_SIZE_TABLE, CONDUIT_FILL_RULES


class ConduitSizer:
    """
    Conduit sizing calculator per EIT standard.
    Accounts for fill percentage and wire count.
    """
    
    # Standard conduit sizes (internal diameter in mm)
    CONDUIT_SIZES = [16, 20, 25, 32, 40, 50, 63]
    
    # Wire outer diameter (approximate, including insulation)
    # For PVC insulated copper
    WIRE_OD = {
        1.0: 3.0,
        1.5: 3.4,
        2.5: 4.0,
        4.0: 4.8,
        6.0: 5.4,
        10.0: 7.0,
        16.0: 8.2,
        25.0: 10.0,
        35.0: 11.5,
        50.0: 13.5,
        70.0: 16.0,
        95.0: 18.5,
        120.0: 21.0,
    }
    
    def __init__(self):
        pass
    
    def calculate_wire_area(self, wire_size_sqmm: float) -> float:
        """
        Calculate wire cross-sectional area including insulation.
        
        Args:
            wire_size_sqmm: Wire conductor size in mm²
            
        Returns:
            Total wire area in mm² (including insulation)
        """
        # Get outer diameter
        od = self.WIRE_OD.get(wire_size_sqmm)
        if od is None:
            # Estimate for non-standard sizes
            od = 2 * (wire_size_sqmm ** 0.5) + 2
        
        return pi * (od / 2) ** 2
    
    def calculate_conduit_area(self, conduit_id_mm: float) -> float:
        """
        Calculate conduit internal area.
        
        Args:
            conduit_id_mm: Conduit internal diameter in mm
            
        Returns:
            Internal area in mm²
        """
        return pi * (conduit_id_mm / 2) ** 2
    
    def get_max_fill_percent(self, num_conductors: int) -> float:
        """
        Get maximum fill percentage based on conductor count.
        
        Args:
            num_conductors: Number of conductors
            
        Returns:
            Maximum fill percentage (0-1)
        """
        if num_conductors == 1:
            return CONDUIT_FILL_RULES.get(1, 0.53)
        elif num_conductors == 2:
            return CONDUIT_FILL_RULES.get(2, 0.31)
        else:
            return CONDUIT_FILL_RULES.get(3, 0.40)
    
    def select_conduit(
        self,
        wire_sizes: List[float],
        conduit_type: str = "PVC"
    ) -> Dict[str, Any]:
        """
        Select appropriate conduit size.
        
        Args:
            wire_sizes: List of wire sizes in mm² (one per conductor)
            conduit_type: Type of conduit
            
        Returns:
            Conduit selection result
        """
        num_conductors = len(wire_sizes)
        max_fill = self.get_max_fill_percent(num_conductors)
        
        # Calculate total wire area
        total_wire_area = sum(
            self.calculate_wire_area(ws) for ws in wire_sizes
        )
        
        # Required conduit area
        required_area = total_wire_area / max_fill
        
        # Select smallest conduit that fits
        selected_size = None
        actual_fill = 0
        
        for size in self.CONDUIT_SIZES:
            conduit_area = self.calculate_conduit_area(size)
            fill = total_wire_area / conduit_area
            
            if fill <= max_fill:
                selected_size = size
                actual_fill = fill
                break
        
        # If nothing fits, use largest
        if selected_size is None:
            selected_size = self.CONDUIT_SIZES[-1]
            actual_fill = total_wire_area / self.calculate_conduit_area(selected_size)
        
        return {
            "conduit_size_mm": selected_size,
            "conduit_type": conduit_type,
            "num_conductors": num_conductors,
            "total_wire_area_sqmm": total_wire_area,
            "max_fill_percent": max_fill * 100,
            "actual_fill_percent": actual_fill * 100,
            "compliant": actual_fill <= max_fill,
        }
    
    def select_for_circuit(
        self,
        wire_size_sqmm: float,
        with_ground: bool = True,
        with_neutral: bool = True
    ) -> Dict[str, Any]:
        """
        Select conduit for a typical circuit.
        
        Args:
            wire_size_sqmm: Main wire size
            with_ground: Include ground conductor
            with_neutral: Include neutral conductor
            
        Returns:
            Conduit selection result
        """
        wire_sizes = [wire_size_sqmm]  # Hot
        
        if with_neutral:
            wire_sizes.append(wire_size_sqmm)  # Neutral same as hot
        
        if with_ground:
            # Ground can be smaller (typically one size down, min 2.5mm²)
            ground_size = max(2.5, wire_size_sqmm / 2)
            wire_sizes.append(ground_size)
        
        return self.select_conduit(wire_sizes)
    
    def select_from_baseline(self, wire_size_sqmm: float) -> float:
        """
        Get conduit size from baseline table.
        
        Args:
            wire_size_sqmm: Wire size
            
        Returns:
            Conduit size in mm
        """
        for wire in WIRE_SIZE_TABLE:
            if wire["size_sqmm"] == wire_size_sqmm:
                return wire["conduit_mm"]
        
        # Estimate for non-standard sizes
        return self.select_for_circuit(wire_size_sqmm)["conduit_size_mm"]
    
    def calculate_raceway_fill(
        self,
        circuits: List[Dict[str, Any]],
        raceway_size_mm: float
    ) -> Dict[str, Any]:
        """
        Calculate fill for a shared raceway.
        
        Args:
            circuits: List of circuit wire specs
            raceway_size_mm: Raceway internal diameter
            
        Returns:
            Raceway fill analysis
        """
        all_wires = []
        for circuit in circuits:
            wire_size = circuit.get("wire_size", 2.5)
            # Assume 3 conductors per circuit (hot, neutral, ground)
            all_wires.extend([wire_size, wire_size, wire_size])
        
        total_area = sum(self.calculate_wire_area(w) for w in all_wires)
        raceway_area = self.calculate_conduit_area(raceway_size_mm)
        
        num_conductors = len(all_wires)
        max_fill = self.get_max_fill_percent(num_conductors)
        actual_fill = total_area / raceway_area
        
        return {
            "raceway_size_mm": raceway_size_mm,
            "num_conductors": num_conductors,
            "total_wire_area": total_area,
            "max_fill_percent": max_fill * 100,
            "actual_fill_percent": actual_fill * 100,
            "compliant": actual_fill <= max_fill,
            "available_area": raceway_area * max_fill - total_area,
        }
