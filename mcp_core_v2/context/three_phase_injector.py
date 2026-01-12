"""
Three-Phase Injector - Load Balancing & 3-Phase Calculations

[SKELETON - NOT YET IMPLEMENTED]

Use Cases:
- Commercial buildings (สำนักงาน)
- Factories (โรงงาน)
- Large residential with 3-phase supply
- Buildings with 3-phase motors/HVAC

วสท. 2564 Standard:
- Phase imbalance should not exceed 10%
- Neutral current calculation for unbalanced loads
- 3-phase VD calculation uses different formula

Enable Conditions:
- voltage_system in ["400V_3PH", "TH_3PH_380V", "3PH"] OR
- total_load > 15kW (typical 3-phase threshold in Thailand)
"""

import logging
from typing import Dict, Any, Optional, List
from models.contracts import DesignRequest, DesignResult, ElectricalLoad

logger = logging.getLogger(__name__)


class ThreePhaseInjector:
    """
    Injects 3-phase load balancing and calculations into design result.
    
    Features to implement:
    - Phase assignment (L1, L2, L3) for balanced loading
    - Neutral current calculation
    - 3-phase VD formula (different from 1-phase)
    - Phase imbalance warning
    """
    
    # Voltage systems that indicate 3-phase
    THREE_PHASE_VOLTAGES = [
        "400V_3PH", "380V_3PH", "TH_3PH_380V",
        "415V_3PH", "208V_3PH", "480V_3PH"
    ]
    
    # Load threshold to suggest 3-phase upgrade (Watts)
    UPGRADE_THRESHOLD_W = 15000  # 15kW
    
    def __init__(self):
        """Initialize 3-Phase Injector."""
        self.enabled = False
    
    def should_inject(self, request: DesignRequest) -> bool:
        """Determine if 3-phase calculations should be performed.
        
        Args:
            request: Design request with voltage system info
            
        Returns:
            True if 3-phase calculations should be applied
        """
        # Check 1: Explicit 3-phase voltage system
        voltage_system = getattr(request, 'service_voltage', None)
        if voltage_system:
            voltage_str = voltage_system.value if hasattr(voltage_system, 'value') else str(voltage_system)
            if any(v in voltage_str.upper() for v in ['3PH', '3-PHASE', '380', '400']):
                logger.info(f"[3-PHASE] Enabled: voltage_system = {voltage_str}")
                return True
        
        # Check 2: Total load exceeds 1-phase capacity
        total_load_w = sum(load.power_watts * load.quantity for load in request.loads)
        if total_load_w > self.UPGRADE_THRESHOLD_W:
            logger.info(f"[3-PHASE] Suggested: total_load = {total_load_w/1000:.1f}kW > 15kW threshold")
            # Don't auto-enable, just suggest
            return False
        
        logger.debug("[3-PHASE] Skipped: 1-phase system")
        return False
    
    def inject(self, request: DesignRequest, result: DesignResult) -> None:
        """Inject 3-phase calculations into design result.
        
        Args:
            request: Original design request
            result: Design result to modify
        """
        if not self.should_inject(request):
            # Check if we should suggest upgrade
            total_load_w = sum(load.power_watts * load.quantity for load in request.loads)
            if total_load_w > self.UPGRADE_THRESHOLD_W:
                result.warnings.append(
                    f"ℹ️ โหลดรวม {total_load_w/1000:.1f}kW เกิน 15kW - พิจารณาใช้ไฟ 3 เฟส (ประหยัดค่าไฟ)"
                )
            return
        
        logger.info("[3-PHASE] 🚧 SKELETON - 3-Phase calculations not yet implemented")
        
        # TODO: Implement 3-phase features
        # 1. Balance loads across L1, L2, L3
        # 2. Calculate neutral current for unbalanced loads
        # 3. Use 3-phase VD formula: VD = (√3 × I × L × R) / V
        # 4. Check phase imbalance < 10%
        # 5. Update circuit grouping for 3-phase breakers
        
        result.warnings.append(
            "ℹ️ [3-PHASE] Feature pending - 3-phase load balancing will be implemented"
        )
    
    def balance_loads(self, loads: List[ElectricalLoad]) -> Dict[str, List[str]]:
        """Balance loads across three phases.
        
        Args:
            loads: List of electrical loads
            
        Returns:
            Dict mapping phase ("L1", "L2", "L3") to list of load IDs
        """
        # TODO: Implement load balancing algorithm
        # Simple approach: sort by power descending, assign to phase with lowest total
        return {"L1": [], "L2": [], "L3": []}


# Global instance
_three_phase_injector: Optional[ThreePhaseInjector] = None


def get_three_phase_injector() -> ThreePhaseInjector:
    """Get the global 3-Phase Injector instance."""
    global _three_phase_injector
    if _three_phase_injector is None:
        _three_phase_injector = ThreePhaseInjector()
    return _three_phase_injector
