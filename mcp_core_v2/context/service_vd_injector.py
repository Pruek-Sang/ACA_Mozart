"""
Service VD Injector - Voltage Drop for Service Entrance (หม้อแปลง → MDB)

[SKELETON - NOT YET IMPLEMENTED]

Use Cases:
- Commercial buildings (สำนักงาน)
- Factories (โรงงาน)
- Large residential (บ้านไกลหม้อแปลง >100m)
- Condos with long service runs

วสท. 2564 Standard:
- Service VD ≤ 2%
- Total VD (Service + Branch) ≤ 5%

Enable Conditions:
- service_distance_m > 50m OR
- building_type in ["commercial", "factory", "โรงงาน", "สำนักงาน"] OR
- request.site_context.distance_to_transformer != "less_than_50m"
"""

import logging
from typing import Dict, Any, Optional
from models.contracts import DesignRequest, DesignResult

logger = logging.getLogger(__name__)


class ServiceVDInjector:
    """
    Injects Service Entrance Voltage Drop calculations into design result.
    
    This is separate from branch VD calculation which is always performed.
    Service VD is only relevant for:
    - Long distance from transformer (>50m)
    - Commercial/Industrial buildings
    - 3-Phase systems with significant feeder length
    """
    
    # Building types that require Service VD calculation
    APPLICABLE_BUILDING_TYPES = [
        "commercial", "factory", "สำนักงาน", "โรงงาน",
        "warehouse", "คลังสินค้า", "hospital", "โรงพยาบาล"
    ]
    
    def __init__(self):
        """Initialize Service VD Injector."""
        self.enabled = False  # Disabled by default for residential
    
    def should_inject(self, request: DesignRequest) -> bool:
        """Determine if Service VD calculation should be performed.
        
        Args:
            request: Design request with building info and site context
            
        Returns:
            True if Service VD should be calculated
        """
        # Check 1: Explicit service distance specified
        if hasattr(request, 'service_distance_m') and request.service_distance_m:
            if request.service_distance_m > 50:
                logger.info(f"[SERVICE-VD] Enabled: service_distance_m = {request.service_distance_m}m")
                return True
        
        # Check 2: Building type requires it
        building_type = getattr(request, 'building_type', None)
        if building_type and building_type.lower() in self.APPLICABLE_BUILDING_TYPES:
            logger.info(f"[SERVICE-VD] Enabled: building_type = {building_type}")
            return True
        
        # Check 3: Site context indicates far from transformer
        site_context = getattr(request, 'site_context', None)
        if site_context:
            distance_to_transformer = site_context.get('distance_to_transformer', '')
            if distance_to_transformer in ['50_100m', 'more_than_100m']:
                logger.info(f"[SERVICE-VD] Enabled: distance_to_transformer = {distance_to_transformer}")
                return True
        
        logger.debug("[SERVICE-VD] Skipped: Not applicable for this project")
        return False
    
    def inject(self, request: DesignRequest, result: DesignResult) -> None:
        """Inject Service VD calculation into design result.
        
        Args:
            request: Original design request
            result: Design result to modify
        """
        if not self.should_inject(request):
            return
        
        logger.info("[SERVICE-VD] 🚧 SKELETON - Service VD calculation not yet implemented")
        
        # TODO: Implement Service VD calculation
        # 1. Get service_distance_m from request or default (30m)
        # 2. Get main feeder wire size from result
        # 3. Calculate VD using wire_sizer._calculate_voltage_drop
        # 4. Add to result.warnings if VD > 2%
        # 5. Calculate Total VD (Service + max Branch VD)
        # 6. Add to result.warnings if Total VD > 5%
        
        # Placeholder warning
        result.warnings.append(
            "ℹ️ [SERVICE-VD] Feature pending - Service VD calculation will be added for commercial/industrial projects"
        )


# Global instance
_service_vd_injector: Optional[ServiceVDInjector] = None


def get_service_vd_injector() -> ServiceVDInjector:
    """Get the global Service VD Injector instance."""
    global _service_vd_injector
    if _service_vd_injector is None:
        _service_vd_injector = ServiceVDInjector()
    return _service_vd_injector
