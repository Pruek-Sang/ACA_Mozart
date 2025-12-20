"""
Derating Injector
Adjusts effective load power based on environmental factors (temperature, conduit grouping).
Implements the Context Injector pattern to avoid modifying core wire sizing logic.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DeratingInjector:
    """
    Adjusts load power to compensate for environmental derating factors.
    Formula: Effective Load = Real Load / Derating Factor
    
    This injector works by modifying the load objects in-place.
    For Pydantic models, we use object.__setattr__ to bypass validation.
    """
    
    # Factors based on Thai EIT Standard / NEC
    # Ambient Temperature Correction Factors (Base 30°C or 40°C depending on cable type)
    # Here we simplify to a multiplier relative to standard condition
    TEMP_FACTORS = {
        "indoor": 1.0,      # Standard (30-40°C)
        "high_temp": 0.8,   # Under roof / Attic (>45°C)
        "outdoor": 0.9,     # Outdoor exposed to sun
        "underground": 0.7  # Underground (Heat dissipation issues)
    }
    
    # Grouping Factors (Number of circuits in same conduit)
    GROUPING_FACTORS = {
        "1": 1.0,   # 1 circuit (2-3 wires)
        "2-3": 0.8, # 2-3 circuits (4-6 wires) - EIT Table 5-8
        "4-6": 0.7  # 4-6 circuits (7-9 wires)
    }

    def inject(self, loads: List[Any], site_context: Dict[str, Any]) -> List[Any]:
        """
        Apply derating factors to loads.
        
        Args:
            loads: List of electrical loads to adjust
            site_context: Dictionary containing 'installation_area' and 'conduit_grouping'
            
        Returns:
            List of loads (same objects, potentially modified)
            
        Note:
            - If site_context is empty or None, returns loads unchanged (SAFE MODE)
            - Uses object.__setattr__ to modify Pydantic models safely
        """
        # SAFE MODE: No context = No modification
        if not site_context:
            logger.debug("DeratingInjector: No site_context provided, skipping derating")
            return loads
        
        # Check if any relevant keys exist
        if "installation_area" not in site_context and "conduit_grouping" not in site_context:
            logger.debug("DeratingInjector: No derating keys in site_context, skipping")
            return loads

        area_type = site_context.get("installation_area", "indoor")
        grouping = site_context.get("conduit_grouping", "1")
        
        temp_factor = self.TEMP_FACTORS.get(area_type, 1.0)
        group_factor = self.GROUPING_FACTORS.get(grouping, 1.0)
        
        total_factor = temp_factor * group_factor
        
        # Safety cap: Don't let factor go too low (e.g. below 0.5)
        total_factor = max(total_factor, 0.5)
        
        # If factor is 1.0, no modification needed
        if total_factor >= 1.0:
            logger.debug(f"DeratingInjector: Factor is {total_factor}, no derating applied")
            return loads
        
        logger.info(f"DeratingInjector: Applying derating factor {total_factor} "
                   f"(area={area_type}, grouping={grouping})")
        
        for load in loads:
            if hasattr(load, 'power_watts'):
                original_power = load.power_watts
                new_power = original_power / total_factor
                
                # Use object.__setattr__ to bypass Pydantic's frozen/validation
                try:
                    object.__setattr__(load, 'power_watts', new_power)
                    logger.debug(f"DeratingInjector: Load {getattr(load, 'id', 'unknown')} "
                               f"adjusted from {original_power}W to {new_power}W")
                except Exception as e:
                    logger.warning(f"DeratingInjector: Could not modify load: {e}")
                    # Continue without modification - safe fallback
                    
        return loads
