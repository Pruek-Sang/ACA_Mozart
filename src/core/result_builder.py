"""Result builder for converting BaselineContext to McpRunResult."""

from src.models.baseline import BaselineContext
from src.models.contracts import CircuitResult, McpRunResult, RoomResult


class ResultBuilder:
    """Converts processed BaselineContext to McpRunResult output format."""

    def build(self, context: BaselineContext) -> McpRunResult:
        """Convert BaselineContext to McpRunResult.
        
        Args:
            context: Processed BaselineContext with all calculations.
            
        Returns:
            McpRunResult ready for API response.
        """
        room_results: list[RoomResult] = []

        for room in context.rooms:
            circuit_results: list[CircuitResult] = []

            for circuit in room.circuits:
                circuit_result = CircuitResult(
                    circuit_id=circuit.circuit_id,
                    room_id=circuit.room_id,
                    circuit_type=circuit.circuit_type,
                    connected_load_w=circuit.connected_load_w,
                    demand_load_w=circuit.demand_load_w,
                    design_current_a=round(circuit.design_current_a, 2),
                    wire_size_sqmm=circuit.wire_size_sqmm,
                    breaker_rating_a=circuit.breaker_rating_a,
                    conduit_size_mm=circuit.conduit_size_mm,
                    voltage_drop_pct=round(circuit.voltage_drop_pct, 2),
                    compliant=circuit.compliant,
                    cable_length_m=circuit.cable_length_m,
                )
                circuit_results.append(circuit_result)

            room_result = RoomResult(
                room_id=room.room_id,
                room_type=room.room_type,
                total_connected_load_w=room.total_connected_load_w,
                total_demand_load_w=room.total_demand_load_w,
                circuits=circuit_results,
            )
            room_results.append(room_result)

        result = McpRunResult(
            project_id=context.project_id,
            project_name=context.project_name,
            total_connected_load_kw=round(context.total_connected_load_w / 1000, 2),
            total_demand_load_kw=round(context.total_demand_load_w / 1000, 2),
            main_breaker_rating_a=context.main_breaker_rating_a,
            rooms=room_results,
            overall_compliant=context.overall_compliant,
            compliance_notes=context.compliance_notes,
            autolisp_script=context.autolisp_script,
        )

        return result
