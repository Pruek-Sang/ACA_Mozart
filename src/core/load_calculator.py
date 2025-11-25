"""Load calculator for computing connected, demand loads and design currents."""

from src.models.baseline import BaselineContext


class LoadCalculator:
    """Calculates electrical loads and design currents for circuits."""

    def calculate(self, context: BaselineContext) -> BaselineContext:
        """Calculate loads and design currents for all circuits.
        
        Computes:
        - connected_load_w (already set from template)
        - demand_load_w = connected_load_w * demand_factor
        - design_current_a (Ib) = demand_load_w / (voltage * power_factor)
        
        Args:
            context: BaselineContext with circuits to calculate.
            
        Returns:
            Updated BaselineContext with calculated values.
        """
        total_connected = 0.0
        total_demand = 0.0

        for room in context.rooms:
            room_connected = 0.0
            room_demand = 0.0

            for circuit in room.circuits:
                # Calculate demand load
                circuit.demand_load_w = circuit.connected_load_w * circuit.demand_factor

                # Calculate design current (Ib)
                # I = P / (V * PF) for single phase
                if circuit.voltage_v > 0 and circuit.power_factor > 0:
                    if context.phase_system == "3-phase":
                        # For 3-phase: I = P / (sqrt(3) * V * PF)
                        import math
                        circuit.design_current_a = circuit.demand_load_w / (
                            math.sqrt(3) * circuit.voltage_v * circuit.power_factor
                        )
                    else:
                        # Single phase: I = P / (V * PF)
                        circuit.design_current_a = circuit.demand_load_w / (
                            circuit.voltage_v * circuit.power_factor
                        )
                else:
                    circuit.design_current_a = 0.0

                # Accumulate room totals
                room_connected += circuit.connected_load_w
                room_demand += circuit.demand_load_w

            # Update room totals
            room.total_connected_load_w = room_connected
            room.total_demand_load_w = room_demand

            # Accumulate project totals
            total_connected += room_connected
            total_demand += room_demand

        # Update project totals
        context.total_connected_load_w = total_connected
        context.total_demand_load_w = total_demand

        return context
