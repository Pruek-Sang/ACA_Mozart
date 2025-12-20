"""
kA Rating Injector
Enforces minimum kA ratings for main breakers based on transformer distance.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class KaRatingInjector:
    """
    Post-process validator/modifier for Breaker kA ratings.
    
    Note: This injector works with DesignResult which contains breaker_selections dict.
    We modify the breaker selections directly rather than accessing a 'panels' field.
    """
    
    # Logic: Closer to transformer = Higher Short Circuit Current (Isc)
    KA_REQUIREMENTS = {
        "less_than_50m": 10,  # < 50m -> High Isc -> Require 10kA+
        "50_100m": 6,         # 50-100m -> Medium Isc -> 6kA is usually ok (but 10kA better)
        "more_than_100m": 6   # > 100m -> Low Isc -> 6kA ok
    }

    def inject(self, result: Any, site_context: Dict[str, Any]) -> Any:
        """
        Adjust main breaker kA rating in the result.
        
        Args:
            result: The DesignResult object from pipeline
            site_context: Dictionary containing 'distance_to_transformer'
            
        Returns:
            Modified result (same object)
        """
        # SAFE MODE: No context = No modification
        if not site_context:
            logger.debug("KaRatingInjector: No site_context provided, skipping")
            return result
            
        distance = site_context.get("distance_to_transformer")
        if not distance:
            logger.debug("KaRatingInjector: No distance_to_transformer in context, skipping")
            return result
            
        min_ka = self.KA_REQUIREMENTS.get(distance, 6)
        
        # Access breaker_selections from result
        breaker_selections = getattr(result, 'breaker_selections', None)
        if not breaker_selections:
            logger.debug("KaRatingInjector: No breaker_selections found in result")
            return result
        
        # Find main breakers (keys ending with '_main')
        modified_count = 0
        for key, breaker_info in breaker_selections.items():
            if key.endswith('_main') and isinstance(breaker_info, dict):
                current_ka = breaker_info.get('ka_rating', 0)
                
                if current_ka < min_ka:
                    breaker_info['ka_rating'] = min_ka
                    breaker_info['ka_adjusted'] = True
                    breaker_info['ka_adjustment_reason'] = (
                        f"Auto-adjusted from {current_ka}kA to {min_ka}kA "
                        f"due to transformer distance ({distance})"
                    )
                    modified_count += 1
                    logger.info(f"KaRatingInjector: Upgraded {key} from {current_ka}kA to {min_ka}kA")
        
        if modified_count > 0:
            # Add warning to result
            if hasattr(result, 'warnings') and isinstance(result.warnings, list):
                result.warnings.append(
                    f"[Safety] {modified_count} main breaker(s) upgraded to {min_ka}kA "
                    f"due to proximity to transformer ({distance})"
                )
                        
        return result
