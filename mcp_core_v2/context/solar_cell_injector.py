"""
Solar Cell Injector - Solar PV System Integration

[SKELETON - NOT YET IMPLEMENTED]

Use Cases:
- Residential rooftop solar (3-10kW typical)
- Commercial solar installations
- Net metering / on-grid systems
- Off-grid / hybrid systems

วสท. + PEA/MEA Requirements:
- Inverter sizing relative to panel capacity
- Anti-islanding protection (mandatory for grid-tie)
- DC disconnect requirements
- Grounding requirements for PV systems
- Net metering agreement handling

Enable Conditions:
- User specifies solar panel capacity OR
- Load includes "solar", "PV", "แผงโซลาร์" keywords
"""

import logging
from typing import Dict, Any, Optional, List
from models.contracts import DesignRequest, DesignResult

logger = logging.getLogger(__name__)


class SolarCellInjector:
    """
    Injects Solar PV system calculations into design result.
    
    Features to implement:
    - Inverter sizing (string vs micro-inverters)
    - DC circuit sizing (panels to inverter)
    - AC circuit sizing (inverter to panel/grid)
    - Protection requirements (DC disconnect, GFCI, anti-islanding)
    - Net metering capacity check
    """
    
    # Common residential solar sizes in Thailand (kW)
    COMMON_SIZES_KW = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0]
    
    # MEA/PEA net metering limit for residential
    NET_METERING_LIMIT_KW = 10.0  # Typical limit for residential
    
    def __init__(self):
        """Initialize Solar Cell Injector."""
        self.enabled = False
    
    def should_inject(self, request: DesignRequest) -> bool:
        """Determine if Solar PV calculations should be performed.
        
        Args:
            request: Design request with load info
            
        Returns:
            True if Solar PV calculations should be applied
        """
        # Check 1: Explicit solar in metadata
        metadata = getattr(request, 'metadata', None)
        if metadata and metadata.get('has_solar'):
            logger.info("[SOLAR] Enabled: metadata.has_solar = True")
            return True
        
        # Check 2: Solar keywords in load names
        solar_keywords = ['solar', 'pv', 'โซลาร์', 'แผงโซล่า', 'inverter', 'อินเวอร์เตอร์']
        for load in request.loads:
            if any(kw in load.name.lower() for kw in solar_keywords):
                logger.info(f"[SOLAR] Enabled: found solar keyword in '{load.name}'")
                return True
        
        logger.debug("[SOLAR] Skipped: No solar components detected")
        return False
    
    def inject(self, request: DesignRequest, result: DesignResult) -> None:
        """Inject Solar PV calculations into design result.
        
        Args:
            request: Original design request
            result: Design result to modify
        """
        if not self.should_inject(request):
            return
        
        logger.info("[SOLAR] 🚧 SKELETON - Solar PV calculations not yet implemented")
        
        # TODO: Implement Solar PV features
        # 1. Parse solar capacity from loads or metadata
        # 2. Size inverter (typically 1:1.2 ratio panel:inverter)
        # 3. Calculate DC circuit requirements (Voc × 1.25, Isc × 1.25)
        # 4. Calculate AC circuit requirements (inverter output)
        # 5. Add DC disconnect and protection requirements
        # 6. Check net metering limit compliance
        # 7. Add anti-islanding warning if grid-tie
        
        result.warnings.append(
            "ℹ️ [SOLAR] Feature pending - Solar PV sizing and protection will be calculated"
        )
    
    def calculate_inverter_size(self, panel_capacity_kw: float) -> float:
        """Calculate recommended inverter size.
        
        Args:
            panel_capacity_kw: Total DC capacity of panels in kW
            
        Returns:
            Recommended inverter size in kW
        """
        # Typical ratio: inverter slightly smaller than panel capacity
        # This allows for DC-AC conversion losses and rarely hits peak
        return panel_capacity_kw * 0.9
    
    def get_dc_wire_size(self, panel_current: float, distance_m: float) -> str:
        """Determine DC wire size for solar string.
        
        Args:
            panel_current: String current in Amps
            distance_m: Distance from panels to inverter
            
        Returns:
            Recommended wire size (mm²)
        """
        # TODO: Implement DC wire sizing
        # Consider: Isc × 1.25 safety factor, temperature derating, VD < 2%
        return "4.0"  # Placeholder


# Global instance
_solar_cell_injector: Optional[SolarCellInjector] = None


def get_solar_cell_injector() -> SolarCellInjector:
    """Get the global Solar Cell Injector instance."""
    global _solar_cell_injector
    if _solar_cell_injector is None:
        _solar_cell_injector = SolarCellInjector()
    return _solar_cell_injector
