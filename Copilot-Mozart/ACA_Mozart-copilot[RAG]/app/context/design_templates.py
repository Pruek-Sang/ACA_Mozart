"""
Design Templates / Presets Module

Allows customization of default values and display preferences
per team or company style.

Author: Fixia
Date: 2026-01-03
"""

import logging
from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("Aura.Templates")


class TemplateDefaults(TypedDict):
    """Default values for a template"""
    power_factor: float
    safety_factor: float
    vd_limit_branch: float
    vd_limit_service: float
    wastage_factor: float
    ambient_temp_c: float
    preferred_brand: str
    conduit_type: str  # 'PVC' or 'EMT'
    wire_type: str  # 'THW' or 'IEC01'


class DisplayPreferences(TypedDict):
    """Display preferences for a template"""
    show_assumptions: bool
    show_alternatives: bool
    boq_show_wastage: bool
    audit_group_by_category: bool
    sld_style: str  # 'compact' or 'detailed'
    language: str  # 'th' or 'en'


@dataclass
class DesignTemplate:
    """A complete design template/preset"""
    id: str
    name: str
    description: str
    is_default: bool
    is_system: bool  # System templates cannot be deleted
    created_by: Optional[str]
    defaults: TemplateDefaults
    display: DisplayPreferences
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DesignTemplate':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            is_default=data.get('is_default', False),
            is_system=data.get('is_system', False),
            created_by=data.get('created_by'),
            defaults=data.get('defaults', DEFAULT_TEMPLATE_DEFAULTS),
            display=data.get('display', DEFAULT_DISPLAY_PREFERENCES),
        )


# === Default Values ===

DEFAULT_TEMPLATE_DEFAULTS: TemplateDefaults = {
    "power_factor": 0.85,
    "safety_factor": 1.25,
    "vd_limit_branch": 3.0,
    "vd_limit_service": 2.0,
    "wastage_factor": 0.10,
    "ambient_temp_c": 30.0,
    "preferred_brand": "Schneider",
    "conduit_type": "PVC",
    "wire_type": "IEC01",
}

DEFAULT_DISPLAY_PREFERENCES: DisplayPreferences = {
    "show_assumptions": True,
    "show_alternatives": True,
    "boq_show_wastage": True,
    "audit_group_by_category": True,
    "sld_style": "detailed",
    "language": "th",
}


# === Built-in Templates ===

SYSTEM_TEMPLATES: List[DesignTemplate] = [
    DesignTemplate(
        id="standard_eit",
        name="มาตรฐาน วสท. 2564",
        description="ใช้ค่าตามมาตรฐาน วสท. และ NEC 2023",
        is_default=True,
        is_system=True,
        created_by="system",
        defaults=DEFAULT_TEMPLATE_DEFAULTS,
        display=DEFAULT_DISPLAY_PREFERENCES,
    ),
    DesignTemplate(
        id="schneider_preferred",
        name="Schneider Electric",
        description="ใช้อุปกรณ์ Schneider เป็นหลัก",
        is_default=False,
        is_system=True,
        created_by="system",
        defaults={
            **DEFAULT_TEMPLATE_DEFAULTS,
            "preferred_brand": "Schneider",
            "safety_factor": 1.3,
        },
        display=DEFAULT_DISPLAY_PREFERENCES,
    ),
    DesignTemplate(
        id="budget_saver",
        name="ประหยัดงบประมาณ",
        description="ใช้วัสดุราคาประหยัด ลดค่า wastage",
        is_default=False,
        is_system=True,
        created_by="system",
        defaults={
            **DEFAULT_TEMPLATE_DEFAULTS,
            "preferred_brand": "Local",
            "wastage_factor": 0.05,
            "conduit_type": "PVC",
        },
        display={
            **DEFAULT_DISPLAY_PREFERENCES,
            "show_alternatives": True,
        },
    ),
    DesignTemplate(
        id="premium_quality",
        name="Premium / High-End",
        description="ใช้วัสดุคุณภาพสูง safety factor สูง",
        is_default=False,
        is_system=True,
        created_by="system",
        defaults={
            **DEFAULT_TEMPLATE_DEFAULTS,
            "preferred_brand": "ABB",
            "safety_factor": 1.5,
            "wastage_factor": 0.15,
            "conduit_type": "EMT",
        },
        display={
            **DEFAULT_DISPLAY_PREFERENCES,
            "sld_style": "detailed",
        },
    ),
]


class TemplateManager:
    """Manages design templates"""
    
    def __init__(self):
        self._templates: Dict[str, DesignTemplate] = {
            t.id: t for t in SYSTEM_TEMPLATES
        }
        self._user_templates: Dict[str, DesignTemplate] = {}
    
    def get_all_templates(self) -> List[DesignTemplate]:
        """Get all available templates"""
        return list(self._templates.values()) + list(self._user_templates.values())
    
    def get_template(self, template_id: str) -> Optional[DesignTemplate]:
        """Get template by ID"""
        return self._templates.get(template_id) or self._user_templates.get(template_id)
    
    def get_default_template(self) -> DesignTemplate:
        """Get the default template"""
        for t in self._templates.values():
            if t.is_default:
                return t
        return SYSTEM_TEMPLATES[0]
    
    def create_template(
        self,
        name: str,
        description: str,
        defaults: TemplateDefaults,
        display: DisplayPreferences,
        created_by: str
    ) -> DesignTemplate:
        """Create a new user template"""
        import uuid
        
        template = DesignTemplate(
            id=f"user_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            is_default=False,
            is_system=False,
            created_by=created_by,
            defaults=defaults,
            display=display,
        )
        
        self._user_templates[template.id] = template
        logger.info(f"[TEMPLATE] Created template: {template.id} - {name}")
        
        return template
    
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> Optional[DesignTemplate]:
        """Update a user template (cannot update system templates)"""
        template = self._user_templates.get(template_id)
        if not template:
            logger.warning(f"[TEMPLATE] Cannot update: {template_id} (not found or system)")
            return None
        
        # Apply updates
        if 'name' in updates:
            template.name = updates['name']
        if 'description' in updates:
            template.description = updates['description']
        if 'defaults' in updates:
            template.defaults.update(updates['defaults'])
        if 'display' in updates:
            template.display.update(updates['display'])
        
        logger.info(f"[TEMPLATE] Updated template: {template_id}")
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a user template (cannot delete system templates)"""
        if template_id in self._user_templates:
            del self._user_templates[template_id]
            logger.info(f"[TEMPLATE] Deleted template: {template_id}")
            return True
        return False
    
    def set_default(self, template_id: str) -> bool:
        """Set a template as default"""
        template = self.get_template(template_id)
        if not template:
            return False
        
        # Unset current default
        for t in self._templates.values():
            t.is_default = False
        for t in self._user_templates.values():
            t.is_default = False
        
        template.is_default = True
        logger.info(f"[TEMPLATE] Set default: {template_id}")
        return True


# Global instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get global template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
