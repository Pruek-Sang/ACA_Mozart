"""Template resolver for electrical design patterns."""

from typing import Dict, Any, List, Optional
from models.contracts import ElectricalLoad, LoadType, VoltageType
import logging

logger = logging.getLogger(__name__)


class DesignTemplate:
    """Design template for common electrical configurations."""
    
    def __init__(self, name: str, pattern: Dict[str, Any]):
        """Initialize a design template."""
        self.name = name
        self.pattern = pattern
    
    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply template to context."""
        return {**self.pattern, **context}


class TemplateResolver:
    """Resolves and applies design templates."""
    
    def __init__(self):
        """Initialize template resolver with common templates."""
        self.templates: Dict[str, DesignTemplate] = {}
        self._load_standard_templates()
    
    def _load_standard_templates(self):
        """Load standard electrical design templates."""
        
        # Residential lighting circuit template
        self.templates['residential_lighting'] = DesignTemplate(
            'residential_lighting',
            {
                'circuit_type': 'lighting',
                'voltage': VoltageType.SINGLE_PHASE_120V,
                'wire_size': '14',
                'breaker_rating': 15,
                'max_fixtures': 12,
                'derating_factor': 0.8
            }
        )
        
        # Commercial receptacle circuit template
        self.templates['commercial_receptacle'] = DesignTemplate(
            'commercial_receptacle',
            {
                'circuit_type': 'receptacle',
                'voltage': VoltageType.SINGLE_PHASE_120V,
                'wire_size': '12',
                'breaker_rating': 20,
                'max_receptacles': 10,
                'derating_factor': 0.8
            }
        )
        
        # HVAC dedicated circuit template
        self.templates['hvac_dedicated'] = DesignTemplate(
            'hvac_dedicated',
            {
                'circuit_type': 'hvac',
                'voltage': VoltageType.SINGLE_PHASE_240V,
                'is_dedicated': True,
                'requires_disconnect': True,
                'derating_factor': 1.0
            }
        )
        
        # Motor circuit template
        self.templates['motor_circuit'] = DesignTemplate(
            'motor_circuit',
            {
                'circuit_type': 'motor',
                'overload_protection': True,
                'disconnect_required': True,
                'starting_factor': 1.25,
                'derating_factor': 1.0
            }
        )
        
        # Residential appliance template (water heaters, ranges, dryers, etc.)
        self.templates['residential_appliance'] = DesignTemplate(
            'residential_appliance',
            {
                'circuit_type': 'appliance',
                'wire_type': 'THHN',
                'conduit_type': 'EMT',
                'is_dedicated': True,  # Most appliances need dedicated circuits
                'derating_factor': 1.0
            }
        )
        
        # Three-phase equipment template
        self.templates['three_phase_equipment'] = DesignTemplate(
            'three_phase_equipment',
            {
                'circuit_type': 'equipment',
                'voltage': VoltageType.THREE_PHASE_208V,
                'is_dedicated': True,
                'derating_factor': 1.0
            }
        )
    
    def get_template(self, template_name: str) -> Optional[DesignTemplate]:
        """Get a template by name."""
        return self.templates.get(template_name)
    
    def resolve_load_template(self, load: ElectricalLoad) -> Dict[str, Any]:
        """Resolve appropriate template for a load."""
        template_map = {
            LoadType.LIGHTING: 'residential_lighting',
            LoadType.RECEPTACLE: 'commercial_receptacle',
            LoadType.HVAC: 'hvac_dedicated',
            LoadType.MOTOR: 'motor_circuit',
            LoadType.APPLIANCE: 'residential_appliance',  # Added for appliances
        }
        
        template_name = template_map.get(load.load_type)
        if not template_name:
            # Use default template for unknown types instead of warning
            logger.debug(f"Using default template for load type {load.load_type}")
            return {
                'wire_type': 'THHN',
                'conduit_type': 'EMT',
                'is_dedicated': False,
                'derating_factor': 1.0
            }
        
        template = self.get_template(template_name)
        if not template:
            # Return sensible defaults if template not found
            return {
                'wire_type': 'THHN',
                'conduit_type': 'EMT',
                'is_dedicated': load.power_watts > 1500,  # Dedicated if >1500W
                'derating_factor': 1.0
            }
        
        context = {
            'load_id': load.id,
            'load_name': load.name,
            'power_watts': load.power_watts,
            'voltage': load.voltage,
            'is_continuous': load.is_continuous
        }
        
        return template.apply(context)
    
    def resolve_circuit_requirements(
        self, 
        loads: List[ElectricalLoad]
    ) -> Dict[str, Dict[str, Any]]:
        """Resolve circuit requirements for multiple loads."""
        circuit_requirements = {}
        
        for load in loads:
            template_data = self.resolve_load_template(load)
            circuit_requirements[load.id] = template_data
        
        return circuit_requirements
    
    def add_custom_template(self, name: str, pattern: Dict[str, Any]):
        """Add a custom template."""
        self.templates[name] = DesignTemplate(name, pattern)
        logger.info(f"Added custom template: {name}")
    
    def list_templates(self) -> List[str]:
        """List all available templates."""
        return list(self.templates.keys())


# Global instance
_template_resolver: Optional[TemplateResolver] = None


def get_template_resolver() -> TemplateResolver:
    """Get the global template resolver instance."""
    global _template_resolver
    if _template_resolver is None:
        _template_resolver = TemplateResolver()
    return _template_resolver
