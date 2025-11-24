"""Result builder for MCP Core v2.

Aggregates all calculation results into the final McpRunResult.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

from models.contracts import (
    McpRunResult,
    CircuitResult,
    WireResult,
    BreakerResult,
    ConduitResult,
    PowerFlowResult,
    AutoLispScript,
)
from models.baseline import BaselineContext, BaselineCircuit
from core.wire_sizer import WireSizingResult
from core.breaker_selector import BreakerSelectionResult
from core.conduit_sizer import ConduitSizingResult
from core.pandapower_adapter import PowerFlowResults
from core.compliance_checker import ComplianceReport

logger = logging.getLogger(__name__)


class ResultBuilder:
    """Builds final McpRunResult from all component results."""

    def __init__(self):
        """Initialize result builder."""
        self._warnings: List[str] = []
        self._errors: List[str] = []

    def build(
        self,
        context: BaselineContext,
        circuit_results: Dict[str, Tuple[
            WireSizingResult,
            BreakerSelectionResult,
            ConduitSizingResult,
            ComplianceReport
        ]],
        power_flow_results: PowerFlowResults,
        autolisp_script: AutoLispScript,
        main_breaker_a: int
    ) -> McpRunResult:
        """Build complete McpRunResult.
        
        Args:
            context: Baseline context with all rooms and circuits
            circuit_results: Dictionary mapping circuit_id to result tuple
            power_flow_results: Results from power flow analysis
            autolisp_script: Generated AutoLISP script
            main_breaker_a: Recommended main breaker rating
            
        Returns:
            Complete McpRunResult
        """
        logger.info("Building final result")
        
        # Build circuit results
        circuits = []
        compliant_count = 0
        
        for room in context.rooms:
            for circuit in room.circuits:
                if circuit.circuit_id in circuit_results:
                    wire, breaker, conduit, compliance = circuit_results[circuit.circuit_id]
                    
                    circuit_result = self._build_circuit_result(
                        circuit=circuit,
                        room_name=room.name,
                        wire_result=wire,
                        breaker_result=breaker,
                        conduit_result=conduit,
                        compliance=compliance,
                    )
                    circuits.append(circuit_result)
                    
                    if circuit_result.is_compliant:
                        compliant_count += 1
                    
                    # Collect warnings and errors
                    self._warnings.extend(compliance.warnings)
                    self._errors.extend(compliance.errors)
        
        # Build power flow result
        power_flow = self._build_power_flow_result(power_flow_results)
        
        # Build final result
        result = McpRunResult(
            project_id=context.project_id,
            project_name=context.project_name,
            circuits=circuits,
            power_flow=power_flow,
            autolisp_script=autolisp_script,
            total_circuits=len(circuits),
            compliant_circuits=compliant_count,
            main_breaker_recommended_a=main_breaker_a,
            run_timestamp=datetime.utcnow(),
            warnings=list(set(self._warnings)),  # Deduplicate
            errors=list(set(self._errors)),
        )
        
        logger.info(
            f"Result built: {result.total_circuits} circuits, "
            f"{result.compliant_circuits} compliant, "
            f"{len(result.warnings)} warnings"
        )
        
        return result

    def _build_circuit_result(
        self,
        circuit: BaselineCircuit,
        room_name: str,
        wire_result: WireSizingResult,
        breaker_result: BreakerSelectionResult,
        conduit_result: ConduitSizingResult,
        compliance: ComplianceReport
    ) -> CircuitResult:
        """Build CircuitResult from component results."""
        # Wire result
        wire = WireResult(
            wire_size_mm2=wire_result.wire_size_mm2,
            wire_type=wire_result.wire_type,
            ampacity_a=wire_result.ampacity_a,
            length_m=wire_result.total_length_m,
        )
        
        # Breaker result
        breaker = BreakerResult(
            breaker_rating_a=breaker_result.breaker_rating_a,
            breaker_type=breaker_result.breaker_type,
            breaking_capacity_ka=breaker_result.breaking_capacity_ka,
        )
        
        # Conduit result
        conduit = ConduitResult(
            conduit_size_mm=conduit_result.conduit_size_mm,
            conduit_type=conduit_result.conduit_type,
            fill_ratio_percent=conduit_result.fill_ratio_percent,
        )
        
        # Compliance notes
        compliance_notes = []
        for check in compliance.checks:
            if check.status.value != "pass":
                compliance_notes.append(f"{check.check_name}: {check.message}")
        
        return CircuitResult(
            circuit_id=circuit.circuit_id,
            circuit_name=circuit.name,
            room_name=room_name,
            circuit_type=circuit.circuit_type.value,
            connected_load_w=circuit.total_connected_load_w,
            demand_load_w=circuit.total_demand_load_w,
            current_a=circuit.design_current_a,
            wire=wire,
            breaker=breaker,
            conduit=conduit,
            voltage_drop_percent=wire_result.calculated_voltage_drop_percent,
            is_compliant=compliance.is_compliant,
            compliance_notes=compliance_notes,
        )

    def _build_power_flow_result(
        self,
        pf_results: PowerFlowResults
    ) -> PowerFlowResult:
        """Build PowerFlowResult from pandapower results."""
        return PowerFlowResult(
            total_load_kw=pf_results.total_load_kw,
            total_current_a=pf_results.total_current_a,
            power_factor=pf_results.power_factor,
            voltage_at_furthest_point_v=pf_results.voltage_at_furthest_point_v,
            max_voltage_drop_percent=pf_results.max_voltage_drop_percent,
            convergence_achieved=pf_results.convergence_achieved,
        )

    def add_warning(self, message: str) -> None:
        """Add a warning message to the result."""
        self._warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add an error message to the result."""
        self._errors.append(message)

    def reset(self) -> None:
        """Reset warnings and errors for new build."""
        self._warnings = []
        self._errors = []
