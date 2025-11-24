"""
MCP Core v2 Compliance Checker
Validates electrical designs against EIT/IEC standards.
"""

from typing import List, Dict, Any, Optional
from models.contracts import (
    RoomDesign,
    ProjectDesign,
    ComplianceResult,
    CircuitSpec,
    OutletPlacement,
    LightPlacement,
)
from models.baseline import (
    BASELINE_OUTLET_RULES,
    BASELINE_LIGHTING_RULES,
    WIRE_SIZE_TABLE,
)
from dal.catalog_dal import get_catalog_dal


class ComplianceChecker:
    """
    Validates electrical designs against EIT/IEC standards.
    """
    
    def __init__(self):
        self.dal = get_catalog_dal()
        self.violations: List[str] = []
        self.warnings: List[str] = []
    
    def check_room(self, room: RoomDesign) -> ComplianceResult:
        """
        Check compliance for a single room.
        
        Args:
            room: Room design to check
            
        Returns:
            Compliance result
        """
        self.violations = []
        self.warnings = []
        
        # Run all checks
        self._check_outlet_spacing(room)
        self._check_outlet_count(room)
        self._check_lighting_level(room)
        self._check_circuit_loading(room)
        self._check_wire_sizing(room)
        
        return ComplianceResult(
            is_compliant=len(self.violations) == 0,
            violations=self.violations.copy(),
            warnings=self.warnings.copy(),
            standard="EIT/IEC",
        )
    
    def check_project(self, project: ProjectDesign) -> ComplianceResult:
        """
        Check compliance for entire project.
        
        Args:
            project: Project design to check
            
        Returns:
            Compliance result
        """
        self.violations = []
        self.warnings = []
        
        # Check each room
        for room in project.rooms:
            room_result = self.check_room(room)
            for v in room_result.violations:
                self.violations.append(f"[{room.room_id}] {v}")
            for w in room_result.warnings:
                self.warnings.append(f"[{room.room_id}] {w}")
        
        # Check main breaker sizing
        self._check_main_breaker(project)
        
        # Check total load
        self._check_total_load(project)
        
        return ComplianceResult(
            is_compliant=len(self.violations) == 0,
            violations=self.violations.copy(),
            warnings=self.warnings.copy(),
            standard="EIT/IEC",
        )
    
    def _check_outlet_spacing(self, room: RoomDesign) -> None:
        """Check outlet spacing compliance."""
        from models.contracts import RoomType
        
        rules = BASELINE_OUTLET_RULES.get(room.room_type, {})
        max_spacing = rules.get("max_spacing_m", 4.5)
        
        outlets = room.outlets
        if len(outlets) < 2:
            return
        
        # Check spacing between adjacent outlets
        positions = [(o.x, o.y) for o in outlets]
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dx = positions[i][0] - positions[j][0]
                dy = positions[i][1] - positions[j][1]
                distance = (dx**2 + dy**2) ** 0.5
                
                # This is a simplified check
                if distance > max_spacing * 1.5:
                    self.warnings.append(
                        f"Outlet spacing ({distance:.1f}m) may exceed maximum ({max_spacing}m)"
                    )
                    break
    
    def _check_outlet_count(self, room: RoomDesign) -> None:
        """Check minimum outlet count."""
        rules = BASELINE_OUTLET_RULES.get(room.room_type, {})
        min_outlets = rules.get("min_outlets", 1)
        
        if len(room.outlets) < min_outlets:
            self.violations.append(
                f"Insufficient outlets: {len(room.outlets)} < {min_outlets} required"
            )
    
    def _check_lighting_level(self, room: RoomDesign) -> None:
        """Check lighting level compliance."""
        rules = BASELINE_LIGHTING_RULES.get(room.room_type, {})
        watts_per_sqm = rules.get("watts_per_sqm", 10)
        
        total_watts = sum(l.wattage for l in room.lights)
        required_watts = room.area * watts_per_sqm
        
        if total_watts < required_watts * 0.8:  # 80% threshold
            self.warnings.append(
                f"Lighting may be insufficient: {total_watts}W < {required_watts:.0f}W recommended"
            )
    
    def _check_circuit_loading(self, room: RoomDesign) -> None:
        """Check circuit loading limits."""
        for circuit in room.circuits:
            # Max 80% loading for continuous loads
            max_watts = (circuit.breaker_size * 220) * 0.8
            
            if circuit.total_load > max_watts:
                self.violations.append(
                    f"Circuit {circuit.circuit_id} overloaded: "
                    f"{circuit.total_load}W > {max_watts:.0f}W (80% of {circuit.breaker_size}A)"
                )
    
    def _check_wire_sizing(self, room: RoomDesign) -> None:
        """Check wire sizing for circuits."""
        for circuit in room.circuits:
            # Find wire ampacity
            wire_ampacity = None
            for wire in WIRE_SIZE_TABLE:
                if wire["size_sqmm"] == circuit.wire_size:
                    wire_ampacity = wire["max_amps"]
                    break
            
            if wire_ampacity is None:
                continue
            
            # Current = W / V
            current = circuit.total_load / 220
            design_current = current * 1.25  # 125% safety factor
            
            if design_current > wire_ampacity:
                self.violations.append(
                    f"Circuit {circuit.circuit_id}: Wire undersized - "
                    f"{circuit.wire_size}mm² ({wire_ampacity}A) < {design_current:.1f}A required"
                )
            
            # Check breaker coordination
            if circuit.breaker_size > wire_ampacity:
                self.violations.append(
                    f"Circuit {circuit.circuit_id}: Breaker ({circuit.breaker_size}A) "
                    f"exceeds wire ampacity ({wire_ampacity}A)"
                )
    
    def _check_main_breaker(self, project: ProjectDesign) -> None:
        """Check main breaker sizing."""
        # Calculate required main breaker
        demand_current = project.total_demand_load / (220 * 0.9)
        min_breaker = demand_current * 1.25
        
        if project.main_breaker_size < min_breaker:
            self.violations.append(
                f"Main breaker undersized: {project.main_breaker_size}A < {min_breaker:.0f}A required"
            )
    
    def _check_total_load(self, project: ProjectDesign) -> None:
        """Check total load limits."""
        # Typical residential service limits
        service_limits = {
            32: 7040,   # 32A single phase
            40: 8800,
            50: 11000,
            63: 13860,
            80: 17600,
            100: 22000,
        }
        
        # Find appropriate service size
        for amp, max_watts in sorted(service_limits.items()):
            if max_watts >= project.total_demand_load:
                break
        else:
            self.warnings.append(
                f"Total demand ({project.total_demand_load:.0f}W) may require "
                f"service upgrade beyond 100A"
            )
    
    def quick_check(
        self,
        outlets: List[OutletPlacement],
        lights: List[LightPlacement],
        circuits: List[CircuitSpec],
        room_area: float
    ) -> Dict[str, Any]:
        """
        Quick compliance check without full room design.
        
        Args:
            outlets: Outlet placements
            lights: Light placements
            circuits: Circuit specs
            room_area: Room area in m²
            
        Returns:
            Quick check results
        """
        issues = []
        
        # Check basic counts
        if len(outlets) < 2:
            issues.append("Minimum 2 outlets recommended")
        
        if len(lights) < 1:
            issues.append("Minimum 1 light fixture required")
        
        # Check lighting level
        total_light_watts = sum(l.wattage for l in lights)
        if total_light_watts < room_area * 8:  # Minimum 8W/m²
            issues.append("Lighting may be insufficient")
        
        # Check circuits
        for circuit in circuits:
            if circuit.total_load > circuit.breaker_size * 220 * 0.8:
                issues.append(f"Circuit {circuit.circuit_id} may be overloaded")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "outlet_count": len(outlets),
            "light_count": len(lights),
            "circuit_count": len(circuits),
        }
