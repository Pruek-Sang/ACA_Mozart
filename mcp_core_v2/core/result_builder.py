"""Result builder for aggregating design results."""

from typing import Dict, Any
from models.contracts import DesignRequest, DesignResult
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResultBuilder:
    """Builds comprehensive design result from individual calculation results."""
    
    def __init__(self):
        """Initialize result builder."""
        pass
    
    def build_result(
        self,
        request: DesignRequest,
        calculations: Dict[str, Any],
        wire_sizing: Dict[str, Any],
        breaker_selections: Dict[str, Any],
        conduit_sizing: Dict[str, Any],
        compliance_report: Dict[str, Any],
        autolisp_code: str = None
    ) -> DesignResult:
        """Build complete design result."""
        errors = []
        warnings = []
        
        # Collect errors from each section
        errors.extend(self._extract_errors(calculations))
        errors.extend(self._extract_errors(wire_sizing))
        errors.extend(self._extract_errors(breaker_selections))
        errors.extend(self._extract_errors(conduit_sizing))
        
        # Collect compliance issues
        if not compliance_report.get('compliant', True):
            errors.extend([
                issue['message'] 
                for issue in compliance_report.get('issues', [])
            ])
        
        warnings.extend([
            warning['message'] 
            for warning in compliance_report.get('warnings', [])
        ])
        
        result = DesignResult(
            session_id=request.session_id,
            request=request,
            calculations=calculations,
            wire_sizing=wire_sizing,
            breaker_selections=breaker_selections,
            conduit_sizing=conduit_sizing,
            compliance_report=compliance_report,
            autolisp_code=autolisp_code,
            completed_at=datetime.utcnow(),
            errors=errors,
            warnings=warnings
        )
        
        return result
    
    def _extract_errors(self, data: Dict[str, Any]) -> list:
        """Extract error messages from result data."""
        errors = []
        
        if isinstance(data, dict):
            if 'error' in data:
                errors.append(data['error'])
            
            # Recursively check nested dictionaries
            for key, value in data.items():
                if isinstance(value, dict):
                    errors.extend(self._extract_errors(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            errors.extend(self._extract_errors(item))
        
        return errors
    
    def create_summary(self, result: DesignResult) -> Dict[str, Any]:
        """Create a summary of the design result."""
        # Count components
        num_panels = len(result.request.panels)
        num_loads = len(result.request.loads)
        num_circuits = sum(len(panel.feeds) for panel in result.request.panels)
        
        # Gather statistics
        total_load_va = sum(
            load.power_watts * load.quantity 
            for load in result.request.loads
        )
        
        summary = {
            'session_id': result.session_id,
            'project_name': result.request.project_name,
            'project_number': result.request.project_number,
            'completed_at': result.completed_at,
            'component_count': {
                'panels': num_panels,
                'loads': num_loads,
                'circuits': num_circuits
            },
            'total_load_va': total_load_va,
            'service_voltage': result.request.service_voltage.value,
            'utility_service_size': result.request.utility_service_size,
            'status': {
                'compliant': result.compliance_report.get('compliant', False),
                'errors': len(result.errors),
                'warnings': len(result.warnings)
            }
        }
        
        return summary
    
    def create_load_summary(self, result: DesignResult) -> Dict[str, Any]:
        """Create a summary of loads by type."""
        from collections import defaultdict
        
        load_by_type = defaultdict(lambda: {'count': 0, 'total_watts': 0})
        
        for load in result.request.loads:
            load_type = load.load_type.value
            load_by_type[load_type]['count'] += load.quantity
            load_by_type[load_type]['total_watts'] += load.power_watts * load.quantity
        
        return dict(load_by_type)
    
    def create_panel_summary(self, result: DesignResult) -> Dict[str, Any]:
        """Create a summary for each panel."""
        panel_summaries = {}
        
        for panel in result.request.panels:
            calc_data = result.calculations.get(panel.id, {})
            
            panel_summaries[panel.id] = {
                'name': panel.name,
                'location': panel.location.room,
                'main_breaker': panel.main_breaker_rating,
                'voltage': panel.voltage.value,
                'circuit_count': len(panel.feeds),
                'total_load_va': calc_data.get('total_va', 0),
                'demand_current': calc_data.get('demand_current', 0),
                'utilization': calc_data.get('utilization', 0)
            }
        
        return panel_summaries
    
    def export_to_dict(self, result: DesignResult) -> Dict[str, Any]:
        """Export result to dictionary for storage/serialization."""
        return {
            'session_id': result.session_id,
            'project_name': result.request.project_name,
            'project_number': result.request.project_number,
            'created_at': result.request.created_at.isoformat(),
            'completed_at': result.completed_at.isoformat(),
            'request': result.request.model_dump(),
            'calculations': result.calculations,
            'wire_sizing': result.wire_sizing,
            'breaker_selections': result.breaker_selections,
            'conduit_sizing': result.conduit_sizing,
            'compliance_report': result.compliance_report,
            'autolisp_code_length': len(result.autolisp_code) if result.autolisp_code else 0,
            'errors': result.errors,
            'warnings': result.warnings,
            'summary': self.create_summary(result),
            'load_summary': self.create_load_summary(result),
            'panel_summary': self.create_panel_summary(result)
        }


# Global instance
_result_builder: Optional[ResultBuilder] = None


def get_result_builder() -> ResultBuilder:
    """Get the global result builder instance."""
    global _result_builder
    if _result_builder is None:
        _result_builder = ResultBuilder()
    return _result_builder
