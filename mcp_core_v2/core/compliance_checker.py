"""Compliance checker for NEC and electrical codes."""

from typing import Dict, Any, List
from models.contracts import DesignRequest, ElectricalLoad, LoadType
from models.baseline import NECBaseline
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Checks electrical design for NEC compliance."""
    
    def __init__(self):
        """Initialize compliance checker."""
        self.nec = NECBaseline()
        self.settings = get_settings()
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def check_design(self, request: DesignRequest) -> Dict[str, Any]:
        """Perform complete compliance check on design."""
        self.issues = []
        self.warnings = []
        
        # Check various compliance aspects
        self._check_circuit_requirements(request.loads)
        self._check_panel_requirements(request.panels, request.loads)
        self._check_load_calculations(request.loads)
        self._check_special_requirements(request.loads)
        
        # Determine overall compliance
        compliant = len(self.issues) == 0
        
        return {
            'compliant': compliant,
            'nec_version': self.settings.nec_version,
            'issues': self.issues,
            'warnings': self.warnings,
            'checks_performed': [
                'circuit_requirements',
                'panel_requirements',
                'load_calculations',
                'special_requirements'
            ]
        }
    
    def _check_circuit_requirements(self, loads: List[ElectricalLoad]):
        """Check circuit-specific requirements."""
        for load in loads:
            # Check AFCI requirements (NEC 210.12)
            if load.load_type == LoadType.RECEPTACLE:
                if not self._has_afci_protection(load):
                    self.warnings.append({
                        'code': 'NEC_210.12',
                        'severity': 'warning',
                        'load_id': load.id,
                        'message': f'Load {load.name} may require AFCI protection in dwelling units'
                    })
            
            # Check GFCI requirements (NEC 210.8)
            if self._requires_gfci(load):
                self.warnings.append({
                    'code': 'NEC_210.8',
                    'severity': 'warning',
                    'load_id': load.id,
                    'message': f'Load {load.name} may require GFCI protection based on location'
                })
            
            # Check dedicated circuit requirements
            if load.load_type == LoadType.HVAC:
                self.warnings.append({
                    'code': 'NEC_210.23',
                    'severity': 'info',
                    'load_id': load.id,
                    'message': f'HVAC load {load.name} typically requires dedicated circuit'
                })
    
    def _check_panel_requirements(self, panels, loads):
        """Check panel-specific requirements."""
        for panel in panels:
            # Check panel rating vs loads
            panel_loads = [load for load in loads if load.id in panel.feeds]
            
            if not panel_loads:
                self.warnings.append({
                    'code': 'DESIGN',
                    'severity': 'warning',
                    'panel_id': panel.id,
                    'message': f'Panel {panel.name} has no loads assigned'
                })
                continue
            
            # Check number of circuits vs panel capacity
            if len(panel_loads) > panel.number_of_circuits:
                self.issues.append({
                    'code': 'PANEL_CAPACITY',
                    'severity': 'error',
                    'panel_id': panel.id,
                    'message': f'Panel {panel.name} has {len(panel_loads)} loads but only {panel.number_of_circuits} circuits'
                })
    
    def _check_load_calculations(self, loads: List[ElectricalLoad]):
        """Check load calculation requirements."""
        # Group loads by type
        load_groups = {}
        for load in loads:
            load_type = load.load_type.value
            if load_type not in load_groups:
                load_groups[load_type] = []
            load_groups[load_type].append(load)
        
        # Check minimum requirements
        # Kitchen small appliance circuits (NEC 210.11(C)(1))
        if 'receptacle' in load_groups:
            kitchen_receptacles = [
                load for load in load_groups['receptacle']
                if 'kitchen' in load.location.room.lower()
            ]
            if kitchen_receptacles and len(kitchen_receptacles) < 2:
                self.warnings.append({
                    'code': 'NEC_210.11_C_1',
                    'severity': 'warning',
                    'message': 'Dwelling unit kitchens require at least two 20A small appliance circuits'
                })
        
        # Check for continuous loads
        continuous_loads = [load for load in loads if load.is_continuous]
        if continuous_loads:
            self.warnings.append({
                'code': 'NEC_210.19_A_1',
                'severity': 'info',
                'message': f'{len(continuous_loads)} continuous loads require 125% sizing factor'
            })
    
    def _check_special_requirements(self, loads: List[ElectricalLoad]):
        """Check special location and equipment requirements."""
        for load in loads:
            location = load.location
            
            # Check bathroom requirements
            if 'bathroom' in location.room.lower():
                if load.load_type == LoadType.RECEPTACLE:
                    self.warnings.append({
                        'code': 'NEC_210.11_C_3',
                        'severity': 'info',
                        'load_id': load.id,
                        'message': f'Bathroom receptacle {load.name} requires 20A circuit and GFCI protection'
                    })
            
            # Check outdoor requirements
            if location.building and 'outdoor' in location.building.lower():
                self.warnings.append({
                    'code': 'NEC_210.8_A',
                    'severity': 'warning',
                    'load_id': load.id,
                    'message': f'Outdoor load {load.name} requires GFCI protection and weather-resistant equipment'
                })
            
            # Check motor requirements
            if load.load_type == LoadType.MOTOR:
                self.warnings.append({
                    'code': 'NEC_430',
                    'severity': 'info',
                    'load_id': load.id,
                    'message': f'Motor load {load.name} requires overload protection per NEC Article 430'
                })
    
    def _has_afci_protection(self, load: ElectricalLoad) -> bool:
        """Check if load has AFCI protection (simplified check)."""
        # In actual implementation, this would check the breaker specification
        # For now, return False to generate warning
        return False
    
    def _requires_gfci(self, load: ElectricalLoad) -> bool:
        """Check if load requires GFCI protection."""
        location = load.location.room.lower()
        
        # NEC 210.8 GFCI requirements
        gfci_locations = [
            'bathroom', 'garage', 'outdoor', 'crawl space',
            'basement', 'kitchen', 'laundry', 'sink'
        ]
        
        return any(loc in location for loc in gfci_locations)
    
    def check_voltage_drop(
        self,
        voltage_drop_percent: float,
        is_feeder: bool = False
    ) -> Dict[str, Any]:
        """Check voltage drop compliance."""
        limit = (
            self.nec.voltage_drop_feeder 
            if is_feeder 
            else self.nec.voltage_drop_branch
        ) * 100
        
        compliant = voltage_drop_percent <= limit
        
        result = {
            'compliant': compliant,
            'voltage_drop_percent': voltage_drop_percent,
            'limit_percent': limit,
            'code_reference': 'NEC 210.19(A) FPN 4' if not is_feeder else 'NEC 215.2(A) FPN 2'
        }
        
        if not compliant:
            result['issue'] = f'Voltage drop {voltage_drop_percent:.2f}% exceeds {limit}% limit'
        
        return result
    
    def check_wire_ampacity(
        self,
        wire_ampacity: int,
        circuit_current: float,
        is_continuous: bool = False
    ) -> Dict[str, Any]:
        """Check wire ampacity compliance."""
        required_ampacity = circuit_current
        if is_continuous:
            required_ampacity *= self.nec.continuous_load_factor
        
        compliant = wire_ampacity >= required_ampacity
        
        result = {
            'compliant': compliant,
            'wire_ampacity': wire_ampacity,
            'required_ampacity': required_ampacity,
            'circuit_current': circuit_current,
            'code_reference': 'NEC 210.19(A)'
        }
        
        if not compliant:
            result['issue'] = f'Wire ampacity {wire_ampacity}A insufficient for {required_ampacity:.2f}A'
        
        return result
    
    def generate_report(self) -> str:
        """Generate a compliance report."""
        report = []
        report.append(f"NEC Compliance Report - Version {self.settings.nec_version}")
        report.append("=" * 60)
        
        if self.issues:
            report.append(f"\nISSUES ({len(self.issues)}):")
            for issue in self.issues:
                report.append(f"  [{issue['code']}] {issue['message']}")
        else:
            report.append("\nNo critical issues found.")
        
        if self.warnings:
            report.append(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                report.append(f"  [{warning['code']}] {warning['message']}")
        
        return "\n".join(report)


# Global instance
_compliance_checker: Optional[ComplianceChecker] = None


def get_compliance_checker() -> ComplianceChecker:
    """Get the global compliance checker instance."""
    global _compliance_checker
    if _compliance_checker is None:
        _compliance_checker = ComplianceChecker()
    return _compliance_checker
