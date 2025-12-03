"""Breaker selection module."""

from typing import Dict, Any, Optional, List
from models.baseline import NECBaseline
from models.catalog_models import BreakerType, BreakerPoles, CatalogBreaker
from dal.catalog_dal import get_catalog_dal
import logging

logger = logging.getLogger(__name__)


class BreakerSelector:
    """Selects appropriate circuit breakers based on load requirements."""
    
    def __init__(self):
        """Initialize breaker selector."""
        self.nec = NECBaseline()
        self.catalog_dal = get_catalog_dal()
    
    def select_breaker(
        self,
        load_current: float,
        poles: BreakerPoles,
        breaker_type: BreakerType = BreakerType.STANDARD,
        continuous_load: bool = False
    ) -> Dict[str, Any]:
        """Select appropriate breaker for a load."""
        # Calculate required breaker rating
        required_rating = load_current
        
        # Apply continuous load factor if needed
        if continuous_load:
            required_rating *= self.nec.continuous_load_factor
        
        # Find next standard breaker rating
        selected_rating = self._get_next_standard_rating(required_rating)
        
        if not selected_rating:
            return {
                'error': f'No standard breaker rating found for {required_rating}A',
                'required_current': load_current,
                'continuous_load': continuous_load
            }
        
        # Try to get breaker from catalog
        catalog_breaker = self.catalog_dal.get_breaker_by_rating(
            ampere_rating=selected_rating,
            poles=poles,
            breaker_type=breaker_type
        )
        
        # Convert poles to integer (1, 2, or 3) for cleaner output
        poles_int = int(poles.value.replace('P', ''))
        
        result = {
            'breaker_rating': selected_rating,
            'poles': poles_int,
            'poles_str': poles.value,  # Keep string version for reference
            'breaker_type': breaker_type.value,
            'load_current': load_current,
            'continuous_load': continuous_load,
            'margin': selected_rating - load_current
        }
        
        if catalog_breaker:
            result['catalog_item'] = {
                'manufacturer': catalog_breaker.manufacturer,
                'model_number': catalog_breaker.model_number,
                'price': catalog_breaker.price,
                'interrupt_rating': catalog_breaker.interrupt_rating
            }
        else:
            logger.warning(f"No catalog item found for {selected_rating}A {poles.value} {breaker_type.value} breaker")
        
        return result
    
    def _get_next_standard_rating(self, current: float) -> Optional[int]:
        """Get the next standard breaker rating above the current."""
        for rating in self.nec.standard_breaker_ratings:
            if rating >= current:
                return rating
        return None
    
    def select_main_breaker(
        self,
        service_load: float,
        voltage: int,
        phases: int
    ) -> Dict[str, Any]:
        """Select main service breaker."""
        # Main breaker must be rated for continuous load
        required_rating = service_load * self.nec.continuous_load_factor
        
        # Determine poles based on system
        if phases == 1:
            poles = BreakerPoles.DOUBLE  # 2-pole for single phase 240V service
        else:
            poles = BreakerPoles.THREE  # 3-pole for three phase
        
        return self.select_breaker(
            load_current=service_load,
            poles=poles,
            breaker_type=BreakerType.MAIN,
            continuous_load=True
        )
    
    def select_motor_breaker(
        self,
        motor_fla: float,
        is_largest_motor: bool = False
    ) -> Dict[str, Any]:
        """Select breaker for motor load per NEC Article 430."""
        # Motor breaker must be 125% of FLA for largest motor
        # or per NEC 430.52 for motor protection
        
        if is_largest_motor:
            required_current = motor_fla * self.nec.largest_motor_factor
        else:
            required_current = motor_fla * self.nec.motor_starting_factor
        
        result = self.select_breaker(
            load_current=required_current,
            poles=BreakerPoles.THREE,  # Assuming 3-phase motor
            breaker_type=BreakerType.STANDARD,
            continuous_load=True
        )
        
        result['motor_application'] = True
        result['motor_fla'] = motor_fla
        result['is_largest_motor'] = is_largest_motor
        
        return result
    
    def select_afci_breaker(
        self,
        load_current: float,
        poles: BreakerPoles = BreakerPoles.SINGLE
    ) -> Dict[str, Any]:
        """Select AFCI breaker for dwelling unit circuits."""
        return self.select_breaker(
            load_current=load_current,
            poles=poles,
            breaker_type=BreakerType.AFCI,
            continuous_load=False
        )
    
    def select_gfci_breaker(
        self,
        load_current: float,
        poles: BreakerPoles = BreakerPoles.SINGLE
    ) -> Dict[str, Any]:
        """Select GFCI breaker for required locations."""
        return self.select_breaker(
            load_current=load_current,
            poles=poles,
            breaker_type=BreakerType.GFCI,
            continuous_load=False
        )
    
    def select_rcbo_breaker(
        self,
        load_current: float,
        poles: BreakerPoles = BreakerPoles.DOUBLE,
        trip_current_ma: int = 30
    ) -> Dict[str, Any]:
        """Select RCBO breaker for wet locations (water heater, outdoor, etc.).
        
        RCBO (Residual Current Breaker with Overcurrent) provides:
        - Overcurrent protection (like standard breaker)
        - Earth leakage protection (like RCD/ELCB)
        
        Thai Standard: ต้องใช้ RCBO 30mA สำหรับเครื่องใช้ไฟฟ้าที่มีน้ำ
        
        Args:
            load_current: Load current in Amperes
            poles: Number of poles (default 2P for water heater)
            trip_current_ma: Earth leakage trip current (30mA standard, 10mA for high sensitivity)
        
        Returns:
            Dict with breaker selection including RCBO specifics
        """
        result = self.select_breaker(
            load_current=load_current,
            poles=poles,
            breaker_type=BreakerType.RCBO,
            continuous_load=True  # Water heater is continuous load
        )
        
        result['rcbo_details'] = {
            'trip_current_ma': trip_current_ma,
            'protection_type': 'AC/A',  # Type A for all waveforms
            'application': 'wet_location',
            'note': 'ต้องติดตั้ง RCBO 30mA สำหรับอุปกรณ์ในพื้นที่เปียก (มาตรฐาน วสท.)'
        }
        
        return result
    
    def verify_breaker_coordination(
        self,
        feeder_breaker_rating: int,
        branch_breaker_rating: int
    ) -> Dict[str, Any]:
        """Verify proper breaker coordination."""
        # Feeder breaker should be larger than branch breaker
        coordinated = feeder_breaker_rating > branch_breaker_rating
        
        # Recommended minimum ratio is 1.5:1 for selective coordination
        ratio = feeder_breaker_rating / branch_breaker_rating if branch_breaker_rating > 0 else 0
        selective = ratio >= 1.5
        
        return {
            'coordinated': coordinated,
            'selective': selective,
            'feeder_rating': feeder_breaker_rating,
            'branch_rating': branch_breaker_rating,
            'ratio': round(ratio, 2),
            'recommendation': 'OK' if selective else 'Consider larger feeder breaker for selective coordination'
        }
    
    def calculate_series_rating(
        self,
        upstream_breaker_aic: int,
        downstream_breaker_aic: int,
        available_fault_current: int
    ) -> Dict[str, Any]:
        """Calculate if series rating is acceptable."""
        # Both breakers must have adequate interrupt rating
        upstream_adequate = upstream_breaker_aic >= available_fault_current
        
        # For series rating, downstream can have lower AIC if properly rated combination
        # This is simplified - actual series ratings must be tested and listed
        
        return {
            'upstream_adequate': upstream_adequate,
            'upstream_aic': upstream_breaker_aic,
            'downstream_aic': downstream_breaker_aic,
            'fault_current': available_fault_current,
            'series_rating_required': downstream_breaker_aic < available_fault_current,
            'note': 'Series ratings must be verified with tested combinations per NEC 240.86'
        }


# Global instance
_breaker_selector: Optional[BreakerSelector] = None


def get_breaker_selector() -> BreakerSelector:
    """Get the global breaker selector instance."""
    global _breaker_selector
    if _breaker_selector is None:
        _breaker_selector = BreakerSelector()
    return _breaker_selector
