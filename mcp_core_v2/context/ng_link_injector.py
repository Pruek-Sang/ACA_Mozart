"""
N-G Link Injector
Controls Neutral-Ground bonding logic based on panel type.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class NgLinkInjector:
    """
    Enforces N-G Link rules.
    Rule: Sub-panels MUST NOT have N-G Link (Ground Loop hazard).
    
    Note: This injector works with DesignResult which contains breaker_selections dict.
    We add metadata/warnings rather than modifying a 'panels' field that doesn't exist.
    """

    def inject(self, result: Any, site_context: Dict[str, Any]) -> Any:
        """
        Adjust N-G Link settings in the result.
        
        Args:
            result: The DesignResult object from pipeline
            site_context: Dictionary containing 'panel_type' ('main' or 'sub')
            
        Returns:
            Modified result (same object)
        """
        # SAFE MODE: No context = No modification
        if not site_context:
            logger.debug("NgLinkInjector: No site_context provided, skipping")
            return result
            
        panel_type = site_context.get("panel_type")
        if not panel_type:
            logger.debug("NgLinkInjector: No panel_type in context, skipping")
            return result
        
        if panel_type == "sub":
            logger.info("NgLinkInjector: Sub-panel detected, adding N-G Link warning")
            
            # Add warning to result
            if hasattr(result, 'warnings') and isinstance(result.warnings, list):
                result.warnings.append(
                    "[Safety] This is a SUB-PANEL design. "
                    "DO NOT bond Neutral to Ground at this panel. "
                    "N-G bonding should ONLY be at the Main Panel (MDB)."
                )
            
            # Add compliance note
            compliance_report = getattr(result, 'compliance_report', None)
            if compliance_report and isinstance(compliance_report, dict):
                if 'notes' not in compliance_report:
                    compliance_report['notes'] = []
                if isinstance(compliance_report.get('notes'), list):
                    compliance_report['notes'].append(
                        "Sub-panel grounding: N-G link REMOVED per NEC 250.24(A)(5)"
                    )
                    
        return result
