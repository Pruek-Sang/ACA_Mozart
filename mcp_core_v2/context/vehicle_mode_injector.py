"""
Vehicle Mode Injector - EV Charger Integration

[SKELETON - NOT YET IMPLEMENTED]

Use Cases:
- Home EV chargers (Level 2: 7kW-22kW)
- Commercial EV charging stations
- Fleet charging facilities
- Destination charging (hotels, malls)

วสท. + International Standards:
- IEC 61851 (EV charging modes)
- Dedicated circuit requirement (Type 2/CCS)
- Earth leakage protection (30mA RCD minimum, 6mA DC detection)
- Load management for multiple EVs
- Dynamic load balancing with home consumption

Enable Conditions:
- User specifies EV charger OR
- Load includes "EV", "charger", "ชาร์จรถ", "ที่ชาร์จรถยนต์" keywords
"""

import logging
from typing import Dict, Any, Optional, List
from models.contracts import DesignRequest, DesignResult

logger = logging.getLogger(__name__)


class VehicleModeInjector:
    """
    Injects EV Charger calculations into design result.
    
    Features to implement:
    - Charger capacity selection (3.7kW, 7kW, 11kW, 22kW)
    - Circuit sizing for EV charger
    - Protection requirements (Type A RCD with DC detection)
    - Load management integration
    - Smart charging scheduling support
    """
    
    # Common EV charger capacities (kW)
    CHARGER_CAPACITIES = {
        "slow": 3.7,      # 1-phase 16A (overnight home charging)
        "medium": 7.0,    # 1-phase 32A (typical home charger)
        "fast": 11.0,     # 3-phase 16A (faster home/workplace)
        "rapid": 22.0,    # 3-phase 32A (destination charging)
    }
    
    # EV charger keywords
    EV_KEYWORDS = [
        'ev', 'charger', 'ชาร์จรถ', 'ที่ชาร์จรถ', 'รถยนต์ไฟฟ้า',
        'wallbox', 'วอลล์บ็อกซ์', 'type 2', 'ccs', 'chademo'
    ]
    
    def __init__(self):
        """Initialize Vehicle Mode Injector."""
        self.enabled = False
    
    def should_inject(self, request: DesignRequest) -> bool:
        """Determine if EV Charger calculations should be performed.
        
        Args:
            request: Design request with load info
            
        Returns:
            True if EV Charger calculations should be applied
        """
        # Check 1: Explicit EV flag in metadata
        metadata = getattr(request, 'metadata', None)
        if metadata and metadata.get('has_ev_charger'):
            logger.info("[EV-CHARGER] Enabled: metadata.has_ev_charger = True")
            return True
        
        # Check 2: EV keywords in load names
        for load in request.loads:
            if any(kw in load.name.lower() for kw in self.EV_KEYWORDS):
                logger.info(f"[EV-CHARGER] Enabled: found EV keyword in '{load.name}'")
                return True
        
        logger.debug("[EV-CHARGER] Skipped: No EV charger detected")
        return False
    
    def inject(self, request: DesignRequest, result: DesignResult) -> None:
        """Inject EV Charger calculations into design result.
        
        Args:
            request: Original design request
            result: Design result to modify
        """
        if not self.should_inject(request):
            return
        
        logger.info("[EV-CHARGER] 🚧 SKELETON - EV Charger calculations not yet implemented")
        
        # TODO: Implement EV Charger features
        # 1. Parse charger capacity from load or default to 7kW
        # 2. Determine if 1-phase or 3-phase based on capacity
        # 3. Size dedicated circuit (continuous load = 125% sizing)
        # 4. Specify protection requirements:
        #    - Type A RCD with DC fault detection (IEC 62955)
        #    - Or Type B RCD for DC charging capability
        # 5. Add dedicated circuit flag (no sharing with other loads)
        # 6. Calculate impact on main breaker sizing
        # 7. Add smart charging notes if applicable
        
        result.warnings.append(
            "⚡ [EV-CHARGER] ที่ชาร์จรถยนต์ไฟฟ้า ต้องใช้วงจรเฉพาะพร้อม RCD Type A หรือ B"
        )
    
    def get_charger_circuit_specs(self, capacity_kw: float, voltage: int = 230) -> Dict[str, Any]:
        """Get circuit specifications for EV charger.
        
        Args:
            capacity_kw: Charger capacity in kW
            voltage: System voltage (230 for 1-phase, 400 for 3-phase)
            
        Returns:
            Dict with breaker rating, wire size, and protection type
        """
        # Calculate current
        if voltage >= 380:  # 3-phase
            current = (capacity_kw * 1000) / (voltage * 1.732)
        else:  # 1-phase
            current = (capacity_kw * 1000) / voltage
        
        # Apply continuous load factor (125%)
        design_current = current * 1.25
        
        # TODO: Implement proper breaker and wire sizing
        return {
            "rated_current": current,
            "design_current": design_current,
            "breaker_rating": "TBD",
            "wire_size": "TBD",
            "protection": "Type A RCD 30mA with 6mA DC detection"
        }


# Global instance
_vehicle_mode_injector: Optional[VehicleModeInjector] = None


def get_vehicle_mode_injector() -> VehicleModeInjector:
    """Get the global Vehicle Mode Injector instance."""
    global _vehicle_mode_injector
    if _vehicle_mode_injector is None:
        _vehicle_mode_injector = VehicleModeInjector()
    return _vehicle_mode_injector
