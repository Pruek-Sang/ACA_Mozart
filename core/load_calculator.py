"""Load calculator for MCP Core v2.

Calculates electrical loads and currents for circuits based on
connected loads and demand factors.
"""

import logging
from typing import Dict, Any

from models.baseline import BaselineContext, BaselineCircuit

logger = logging.getLogger(__name__)


class LoadCalculator:
    """Calculates electrical loads and design currents."""

    def __init__(self, voltage: float = 220.0, power_factor: float = 0.85):
        """Initialize load calculator.
        
        Args:
            voltage: System nominal voltage (V)
            power_factor: Default power factor for mixed loads
        """
        self._voltage = voltage
        self._power_factor = power_factor

    def calculate(self, context: BaselineContext) -> BaselineContext:
        """Calculate loads and currents for all circuits.
        
        Args:
            context: Baseline context with circuits
            
        Returns:
            Updated context with calculated values
        """
        logger.info(f"Calculating loads for {context.total_circuits} circuits")
        
        total_connected = 0.0
        total_demand = 0.0
        
        for room in context.rooms:
            for circuit in room.circuits:
                self._calculate_circuit_load(circuit)
                total_connected += circuit.total_connected_load_w
                total_demand += circuit.total_demand_load_w
        
        context.total_connected_load_w = total_connected
        
        logger.info(
            f"Total connected load: {total_connected:.0f}W, "
            f"Total demand load: {total_demand:.0f}W"
        )
        
        return context

    def _calculate_circuit_load(self, circuit: BaselineCircuit) -> None:
        """Calculate load values for a single circuit.
        
        Updates the circuit object in-place with calculated values.
        """
        # Sum connected loads
        connected_load = sum(
            load.watts * load.quantity
            for load in circuit.loads
        )
        
        # Apply demand factors
        demand_load = sum(
            load.watts * load.quantity * load.demand_factor
            for load in circuit.loads
        )
        
        # Calculate weighted average power factor
        if connected_load > 0:
            weighted_pf = sum(
                load.watts * load.quantity * load.power_factor
                for load in circuit.loads
            ) / connected_load
        else:
            weighted_pf = self._power_factor
        
        # Calculate design current (single phase)
        # I = P / (V * PF)
        voltage = circuit.voltage or self._voltage
        design_current = demand_load / (voltage * weighted_pf) if voltage > 0 else 0
        
        # Update circuit
        circuit.total_connected_load_w = connected_load
        circuit.total_demand_load_w = demand_load
        circuit.design_current_a = design_current
        
        logger.debug(
            f"Circuit {circuit.name}: "
            f"connected={connected_load:.0f}W, "
            f"demand={demand_load:.0f}W, "
            f"current={design_current:.2f}A"
        )

    def get_circuit_summary(self, circuit: BaselineCircuit) -> Dict[str, Any]:
        """Get summary of circuit load calculations.
        
        Args:
            circuit: Circuit to summarize
            
        Returns:
            Dictionary with load calculation summary
        """
        return {
            "circuit_id": circuit.circuit_id,
            "circuit_name": circuit.name,
            "circuit_type": circuit.circuit_type.value,
            "num_loads": len(circuit.loads),
            "connected_load_w": circuit.total_connected_load_w,
            "demand_load_w": circuit.total_demand_load_w,
            "design_current_a": circuit.design_current_a,
            "voltage": circuit.voltage,
        }

    def calculate_total_demand(self, context: BaselineContext) -> float:
        """Calculate total demand load for the project.
        
        Args:
            context: Baseline context with calculated circuit loads
            
        Returns:
            Total demand load in Watts
        """
        return sum(
            circuit.total_demand_load_w
            for room in context.rooms
            for circuit in room.circuits
        )

    def calculate_total_current(
        self,
        context: BaselineContext,
        voltage: float = None,
        power_factor: float = None
    ) -> float:
        """Calculate total design current for the project.
        
        Args:
            context: Baseline context with calculated circuit loads
            voltage: System voltage (uses default if not specified)
            power_factor: Power factor (uses default if not specified)
            
        Returns:
            Total design current in Amps
        """
        voltage = voltage or self._voltage
        pf = power_factor or self._power_factor
        
        total_demand = self.calculate_total_demand(context)
        
        return total_demand / (voltage * pf) if voltage > 0 else 0
