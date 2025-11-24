"""Compliance checker for MCP Core v2.

Validates electrical design against code requirements and best practices.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from models.baseline import BaselineContext, BaselineCircuit, CircuitType
from core.wire_sizer import WireSizingResult
from core.breaker_selector import BreakerSelectionResult

logger = logging.getLogger(__name__)


class ComplianceStatus(str, Enum):
    """Compliance check status."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class ComplianceCheck:
    """Result of a single compliance check."""
    
    check_id: str
    check_name: str
    status: ComplianceStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    """Complete compliance report for a circuit or system."""
    
    is_compliant: bool
    checks: List[ComplianceCheck]
    warnings: List[str]
    errors: List[str]
    
    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.status == ComplianceStatus.PASS)
    
    @property
    def failed_checks(self) -> int:
        return sum(1 for c in self.checks if c.status == ComplianceStatus.FAIL)
    
    @property
    def warning_checks(self) -> int:
        return sum(1 for c in self.checks if c.status == ComplianceStatus.WARNING)


class ComplianceChecker:
    """Validates design against electrical codes and standards."""

    def __init__(
        self,
        voltage_drop_limit: float = 3.0,
        max_outlets_per_circuit: int = 10,
        max_lighting_points_per_circuit: int = 12
    ):
        """Initialize compliance checker.
        
        Args:
            voltage_drop_limit: Maximum allowed voltage drop (%)
            max_outlets_per_circuit: Maximum outlets per circuit
            max_lighting_points_per_circuit: Maximum lighting points per circuit
        """
        self._vdrop_limit = voltage_drop_limit
        self._max_outlets = max_outlets_per_circuit
        self._max_lighting = max_lighting_points_per_circuit

    def check_circuit(
        self,
        circuit: BaselineCircuit,
        wire_result: WireSizingResult,
        breaker_result: BreakerSelectionResult
    ) -> ComplianceReport:
        """Check compliance for a single circuit.
        
        Args:
            circuit: Circuit to check
            wire_result: Wire sizing result
            breaker_result: Breaker selection result
            
        Returns:
            ComplianceReport with all check results
        """
        checks = []
        warnings = []
        errors = []
        
        # Check 1: Voltage drop
        vdrop_check = self._check_voltage_drop(circuit, wire_result)
        checks.append(vdrop_check)
        if vdrop_check.status == ComplianceStatus.FAIL:
            errors.append(vdrop_check.message)
        elif vdrop_check.status == ComplianceStatus.WARNING:
            warnings.append(vdrop_check.message)
        
        # Check 2: Wire ampacity
        ampacity_check = self._check_wire_ampacity(circuit, wire_result, breaker_result)
        checks.append(ampacity_check)
        if ampacity_check.status == ComplianceStatus.FAIL:
            errors.append(ampacity_check.message)
        
        # Check 3: Breaker coordination
        coordination_check = self._check_breaker_coordination(
            circuit, wire_result, breaker_result
        )
        checks.append(coordination_check)
        if coordination_check.status == ComplianceStatus.FAIL:
            errors.append(coordination_check.message)
        
        # Check 4: Circuit loading
        loading_check = self._check_circuit_loading(circuit, breaker_result)
        checks.append(loading_check)
        if loading_check.status == ComplianceStatus.FAIL:
            errors.append(loading_check.message)
        elif loading_check.status == ComplianceStatus.WARNING:
            warnings.append(loading_check.message)
        
        # Check 5: Outlet/lighting count
        count_check = self._check_outlet_count(circuit)
        checks.append(count_check)
        if count_check.status == ComplianceStatus.FAIL:
            errors.append(count_check.message)
        elif count_check.status == ComplianceStatus.WARNING:
            warnings.append(count_check.message)
        
        is_compliant = all(c.status != ComplianceStatus.FAIL for c in checks)
        
        return ComplianceReport(
            is_compliant=is_compliant,
            checks=checks,
            warnings=warnings,
            errors=errors,
        )

    def _check_voltage_drop(
        self,
        circuit: BaselineCircuit,
        wire_result: WireSizingResult
    ) -> ComplianceCheck:
        """Check voltage drop compliance."""
        vdrop = wire_result.calculated_voltage_drop_percent
        
        if vdrop <= self._vdrop_limit:
            status = ComplianceStatus.PASS
            message = f"Voltage drop {vdrop:.2f}% within limit of {self._vdrop_limit}%"
        elif vdrop <= self._vdrop_limit * 1.2:  # 20% grace
            status = ComplianceStatus.WARNING
            message = f"Voltage drop {vdrop:.2f}% marginally exceeds limit of {self._vdrop_limit}%"
        else:
            status = ComplianceStatus.FAIL
            message = f"Voltage drop {vdrop:.2f}% exceeds limit of {self._vdrop_limit}%"
        
        return ComplianceCheck(
            check_id="vdrop",
            check_name="Voltage Drop",
            status=status,
            message=message,
            details={
                "calculated_percent": vdrop,
                "limit_percent": self._vdrop_limit,
            }
        )

    def _check_wire_ampacity(
        self,
        circuit: BaselineCircuit,
        wire_result: WireSizingResult,
        breaker_result: BreakerSelectionResult
    ) -> ComplianceCheck:
        """Check wire ampacity vs design current and breaker rating."""
        ampacity = wire_result.ampacity_a
        design_current = circuit.design_current_a
        breaker_rating = breaker_result.breaker_rating_a
        
        # Wire ampacity must be >= breaker rating for proper protection
        if ampacity >= breaker_rating:
            status = ComplianceStatus.PASS
            message = f"Wire ampacity {ampacity}A >= breaker rating {breaker_rating}A"
        else:
            status = ComplianceStatus.FAIL
            message = f"Wire ampacity {ampacity}A < breaker rating {breaker_rating}A - inadequate protection"
        
        return ComplianceCheck(
            check_id="ampacity",
            check_name="Wire Ampacity",
            status=status,
            message=message,
            details={
                "wire_ampacity_a": ampacity,
                "breaker_rating_a": breaker_rating,
                "design_current_a": design_current,
            }
        )

    def _check_breaker_coordination(
        self,
        circuit: BaselineCircuit,
        wire_result: WireSizingResult,
        breaker_result: BreakerSelectionResult
    ) -> ComplianceCheck:
        """Check breaker/wire coordination."""
        wire_size = wire_result.wire_size_mm2
        min_size = breaker_result.min_wire_size_mm2
        max_size = breaker_result.max_wire_size_mm2
        
        if min_size <= wire_size <= max_size:
            status = ComplianceStatus.PASS
            message = f"Wire {wire_size}mm² compatible with {breaker_result.breaker_rating_a}A breaker"
        else:
            status = ComplianceStatus.FAIL
            message = f"Wire {wire_size}mm² outside range {min_size}-{max_size}mm² for breaker"
        
        return ComplianceCheck(
            check_id="coordination",
            check_name="Breaker Coordination",
            status=status,
            message=message,
            details={
                "wire_size_mm2": wire_size,
                "min_size_mm2": min_size,
                "max_size_mm2": max_size,
            }
        )

    def _check_circuit_loading(
        self,
        circuit: BaselineCircuit,
        breaker_result: BreakerSelectionResult
    ) -> ComplianceCheck:
        """Check circuit loading percentage."""
        breaker_rating = breaker_result.breaker_rating_a
        design_current = circuit.design_current_a
        
        loading_percent = (design_current / breaker_rating) * 100 if breaker_rating > 0 else 0
        
        if loading_percent <= 80:
            status = ComplianceStatus.PASS
            message = f"Circuit loading {loading_percent:.1f}% (recommended ≤80%)"
        elif loading_percent <= 100:
            status = ComplianceStatus.WARNING
            message = f"Circuit loading {loading_percent:.1f}% is high (recommended ≤80%)"
        else:
            status = ComplianceStatus.FAIL
            message = f"Circuit loading {loading_percent:.1f}% exceeds breaker rating"
        
        return ComplianceCheck(
            check_id="loading",
            check_name="Circuit Loading",
            status=status,
            message=message,
            details={
                "loading_percent": loading_percent,
                "design_current_a": design_current,
                "breaker_rating_a": breaker_rating,
            }
        )

    def _check_outlet_count(self, circuit: BaselineCircuit) -> ComplianceCheck:
        """Check number of outlets/points on circuit."""
        num_loads = len(circuit.loads)
        circuit_type = circuit.circuit_type
        
        if circuit_type == CircuitType.LIGHTING:
            max_count = self._max_lighting
            load_type = "lighting points"
        elif circuit_type == CircuitType.OUTLET:
            max_count = self._max_outlets
            load_type = "outlets"
        else:
            # Dedicated circuits typically have 1 load
            max_count = 1
            load_type = "dedicated loads"
        
        if num_loads <= max_count:
            status = ComplianceStatus.PASS
            message = f"{num_loads} {load_type} within limit of {max_count}"
        elif num_loads <= max_count * 1.2:
            status = ComplianceStatus.WARNING
            message = f"{num_loads} {load_type} slightly exceeds recommended {max_count}"
        else:
            status = ComplianceStatus.FAIL
            message = f"{num_loads} {load_type} exceeds maximum of {max_count}"
        
        return ComplianceCheck(
            check_id="outlet_count",
            check_name="Outlet/Point Count",
            status=status,
            message=message,
            details={
                "count": num_loads,
                "max_count": max_count,
                "circuit_type": circuit_type.value,
            }
        )

    def check_system(self, context: BaselineContext) -> ComplianceReport:
        """Check system-level compliance.
        
        Args:
            context: Complete baseline context
            
        Returns:
            System-level compliance report
        """
        checks = []
        warnings = []
        errors = []
        
        # Check total connected load
        total_load = context.total_connected_load_w
        if total_load > 50000:  # 50kW threshold
            warnings.append(f"High total load ({total_load/1000:.1f}kW) - verify utility capacity")
        
        # Check circuit count
        if context.total_circuits > 30:
            warnings.append(f"Large number of circuits ({context.total_circuits}) - consider subpanel")
        
        is_compliant = len(errors) == 0
        
        return ComplianceReport(
            is_compliant=is_compliant,
            checks=checks,
            warnings=warnings,
            errors=errors,
        )
