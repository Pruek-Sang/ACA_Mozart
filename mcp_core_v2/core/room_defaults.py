"""Room Defaults Module - Default configurations for residential rooms.

Provides default values for:
- Room sizes (default 5x5m for bedroom)
- Minimum outlets per room
- Minimum lighting requirements
- Smart home provisions

Standards Reference:
- Thai EIT Standard (วสท.)
- Common residential practices
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class RoomCategory(str, Enum):
    """Room category for defaults."""
    BEDROOM = "bedroom"
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    DINING_ROOM = "dining_room"
    STUDY = "study"
    CORRIDOR = "corridor"
    GARAGE = "garage"
    OUTDOOR = "outdoor"
    LAUNDRY = "laundry"
    STORAGE = "storage"
    PUMP_ROOM = "pump_room"


@dataclass
class RoomDefaults:
    """Default configuration for a room type."""
    room_type: RoomCategory
    default_area_sqm: float           # Default area if not specified
    min_area_sqm: float              # Minimum allowed area
    max_area_sqm: float              # Maximum typical area
    min_outlets: int                 # Minimum outlets required
    outlets_per_10sqm: float         # Outlets per 10 m²
    needs_dedicated_lighting: bool   # Does room need dedicated light circuit?
    needs_receptacles: bool          # Does room need receptacles?
    needs_ac: bool                   # Does room typically have AC?
    suggested_ac_btu: int            # Suggested AC size (BTU)
    smart_home_ready: bool           # Should prepare for smart home?
    notes: List[str] = field(default_factory=list)


# Default configurations for all room types
ROOM_DEFAULTS: Dict[RoomCategory, RoomDefaults] = {
    RoomCategory.BEDROOM: RoomDefaults(
        room_type=RoomCategory.BEDROOM,
        default_area_sqm=25.0,        # 5x5m
        min_area_sqm=9.0,             # 3x3m minimum
        max_area_sqm=50.0,
        min_outlets=2,                # At least 2 outlets
        outlets_per_10sqm=1.5,
        needs_dedicated_lighting=False,  # Group with other bedrooms
        needs_receptacles=True,
        needs_ac=True,
        suggested_ac_btu=12000,       # 12,000 BTU standard
        smart_home_ready=True,
        notes=["ควรมีเต้ารับข้างเตียงอย่างน้อย 2 จุด"]
    ),
    RoomCategory.LIVING_ROOM: RoomDefaults(
        room_type=RoomCategory.LIVING_ROOM,
        default_area_sqm=35.0,
        min_area_sqm=16.0,
        max_area_sqm=80.0,
        min_outlets=4,
        outlets_per_10sqm=1.5,
        needs_dedicated_lighting=False,
        needs_receptacles=True,
        needs_ac=True,
        suggested_ac_btu=18000,       # 18,000 BTU for larger room
        smart_home_ready=True,
        notes=["ควรมีเต้ารับสำหรับ TV และ อุปกรณ์ entertainment"]
    ),
    RoomCategory.KITCHEN: RoomDefaults(
        room_type=RoomCategory.KITCHEN,
        default_area_sqm=15.0,
        min_area_sqm=6.0,
        max_area_sqm=30.0,
        min_outlets=4,
        outlets_per_10sqm=3.0,        # Kitchen needs more outlets
        needs_dedicated_lighting=False,
        needs_receptacles=True,
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=[
            "เตา Induction ต้องวงจรเฉพาะ",
            "ไมโครเวฟ/กาต้มน้ำ ควรใช้เต้ารับเฉพาะ",
            "ควรมีพัดลมดูดอากาศ"
        ]
    ),
    RoomCategory.BATHROOM: RoomDefaults(
        room_type=RoomCategory.BATHROOM,
        default_area_sqm=6.0,
        min_area_sqm=3.0,
        max_area_sqm=15.0,
        min_outlets=0,                # NO receptacles in bathroom (wet location)
        outlets_per_10sqm=0.0,
        needs_dedicated_lighting=False,
        needs_receptacles=False,      # Important: No receptacles
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=[
            "ไม่ควรมีเต้ารับในห้องน้ำ (พื้นที่เปียก)",
            "เครื่องทำน้ำอุ่นต้องใช้ RCBO",
            "สวิตช์ไฟควรอยู่นอกห้องน้ำ"
        ]
    ),
    RoomCategory.DINING_ROOM: RoomDefaults(
        room_type=RoomCategory.DINING_ROOM,
        default_area_sqm=16.0,
        min_area_sqm=9.0,
        max_area_sqm=30.0,
        min_outlets=2,
        outlets_per_10sqm=1.0,
        needs_dedicated_lighting=False,
        needs_receptacles=True,
        needs_ac=False,              # Usually connected to living room
        suggested_ac_btu=0,
        smart_home_ready=True,
        notes=["ควรมีไฟ pendant เหนือโต๊ะอาหาร"]
    ),
    RoomCategory.STUDY: RoomDefaults(
        room_type=RoomCategory.STUDY,
        default_area_sqm=12.0,
        min_area_sqm=6.0,
        max_area_sqm=25.0,
        min_outlets=4,
        outlets_per_10sqm=3.0,       # Needs outlets for computer etc.
        needs_dedicated_lighting=False,
        needs_receptacles=True,
        needs_ac=True,
        suggested_ac_btu=9000,
        smart_home_ready=True,
        notes=[
            "ควรมีเต้ารับสำหรับคอมพิวเตอร์",
            "ควรมี LAN outlet",
            "ควรเตรียม UPS outlet"
        ]
    ),
    RoomCategory.CORRIDOR: RoomDefaults(
        room_type=RoomCategory.CORRIDOR,
        default_area_sqm=6.0,
        min_area_sqm=2.0,
        max_area_sqm=20.0,
        min_outlets=0,
        outlets_per_10sqm=0.5,
        needs_dedicated_lighting=False,
        needs_receptacles=False,
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=["ควรใช้ไฟ sensor ประหยัดพลังงาน"]
    ),
    RoomCategory.GARAGE: RoomDefaults(
        room_type=RoomCategory.GARAGE,
        default_area_sqm=20.0,
        min_area_sqm=12.0,
        max_area_sqm=50.0,
        min_outlets=2,
        outlets_per_10sqm=1.0,
        needs_dedicated_lighting=False,
        needs_receptacles=True,
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=[
            "ควรมีเต้ารับสำหรับอุปกรณ์",
            "อาจต้องเตรียมสำหรับ EV charger"
        ]
    ),
    RoomCategory.OUTDOOR: RoomDefaults(
        room_type=RoomCategory.OUTDOOR,
        default_area_sqm=30.0,
        min_area_sqm=5.0,
        max_area_sqm=200.0,
        min_outlets=1,
        outlets_per_10sqm=0.3,
        needs_dedicated_lighting=False,
        needs_receptacles=True,
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=[
            "ต้องใช้เต้ารับกันน้ำ (IP44+)",
            "ควรมี timer สำหรับไฟสวน"
        ]
    ),
    RoomCategory.LAUNDRY: RoomDefaults(
        room_type=RoomCategory.LAUNDRY,
        default_area_sqm=6.0,
        min_area_sqm=3.0,
        max_area_sqm=15.0,
        min_outlets=2,
        outlets_per_10sqm=2.0,
        needs_dedicated_lighting=False,
        needs_receptacles=True,
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=[
            "เครื่องซักผ้าต้องวงจรเฉพาะ",
            "เครื่องอบผ้าต้องวงจรเฉพาะ"
        ]
    ),
    RoomCategory.STORAGE: RoomDefaults(
        room_type=RoomCategory.STORAGE,
        default_area_sqm=4.0,
        min_area_sqm=2.0,
        max_area_sqm=20.0,
        min_outlets=1,
        outlets_per_10sqm=0.5,
        needs_dedicated_lighting=False,
        needs_receptacles=False,
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=[]
    ),
    RoomCategory.PUMP_ROOM: RoomDefaults(
        room_type=RoomCategory.PUMP_ROOM,
        default_area_sqm=4.0,
        min_area_sqm=2.0,
        max_area_sqm=10.0,
        min_outlets=1,
        outlets_per_10sqm=1.0,
        needs_dedicated_lighting=True,  # Need light to service pump
        needs_receptacles=True,
        needs_ac=False,
        suggested_ac_btu=0,
        smart_home_ready=False,
        notes=["ปั๊มน้ำต้องใช้ Motor Starter"]
    ),
}


class RoomDefaultsManager:
    """Manages room default configurations."""
    
    # Default project area if not specified
    DEFAULT_PROJECT_AREA_SQM = 150.0
    
    # Default room size for bedrooms
    DEFAULT_BEDROOM_SIZE_M = 5.0  # 5x5m = 25 m²
    
    # Threshold for "large room" (needs more outlets)
    LARGE_ROOM_THRESHOLD_SQM = 100.0  # 10x10m
    
    def __init__(self):
        """Initialize room defaults manager."""
        self.room_defaults = ROOM_DEFAULTS
    
    def get_defaults(self, room_type: str) -> RoomDefaults:
        """Get defaults for a room type."""
        category = self._parse_room_category(room_type)
        return self.room_defaults.get(category, self.room_defaults[RoomCategory.BEDROOM])
    
    def calculate_required_outlets(
        self,
        room_type: str,
        area_sqm: float = None
    ) -> Dict[str, Any]:
        """Calculate required outlets for a room.
        
        Rules:
        - Small room (≤25m²): minimum outlets
        - Large room (>100m²): at least 4 outlets
        - Per-area calculation for medium rooms
        """
        defaults = self.get_defaults(room_type)
        
        # Use default area if not specified
        if area_sqm is None or area_sqm <= 0:
            area_sqm = defaults.default_area_sqm
        
        # Check if room needs receptacles
        if not defaults.needs_receptacles:
            return {
                "room_type": room_type,
                "area_sqm": area_sqm,
                "required_outlets": 0,
                "message": "ห้องนี้ไม่ควรมีเต้ารับ (ตามมาตรฐาน)",
                "notes": defaults.notes
            }
        
        # Calculate based on area
        outlets_by_area = math.ceil(area_sqm * defaults.outlets_per_10sqm / 10)
        
        # Apply minimum
        required = max(defaults.min_outlets, outlets_by_area)
        
        # Large room rule
        if area_sqm >= self.LARGE_ROOM_THRESHOLD_SQM:
            required = max(4, required)
        
        return {
            "room_type": room_type,
            "area_sqm": area_sqm,
            "required_outlets": required,
            "minimum_outlets": defaults.min_outlets,
            "is_large_room": area_sqm >= self.LARGE_ROOM_THRESHOLD_SQM,
            "notes": defaults.notes
        }
    
    def calculate_suggested_ac(
        self,
        room_type: str,
        area_sqm: float = None
    ) -> Dict[str, Any]:
        """Calculate suggested AC size for a room.
        
        Rule of thumb: ~600-800 BTU per m² (depends on insulation, sun exposure)
        Using 700 BTU/m² as default
        """
        defaults = self.get_defaults(room_type)
        
        if area_sqm is None or area_sqm <= 0:
            area_sqm = defaults.default_area_sqm
        
        if not defaults.needs_ac:
            return {
                "room_type": room_type,
                "area_sqm": area_sqm,
                "needs_ac": False,
                "suggested_btu": 0,
                "message": "ห้องนี้ไม่จำเป็นต้องมีแอร์"
            }
        
        # Calculate BTU: 700 BTU per m²
        BTU_PER_SQM = 700
        calculated_btu = area_sqm * BTU_PER_SQM
        
        # Round to standard sizes
        standard_sizes = [9000, 12000, 18000, 24000, 30000, 36000]
        
        suggested_btu = standard_sizes[0]
        for size in standard_sizes:
            if size >= calculated_btu:
                suggested_btu = size
                break
        else:
            suggested_btu = standard_sizes[-1]
        
        # Estimate power (kW) - roughly BTU / 3.4
        power_kw = suggested_btu / 3412
        
        return {
            "room_type": room_type,
            "area_sqm": area_sqm,
            "needs_ac": True,
            "calculated_btu": round(calculated_btu, 0),
            "suggested_btu": suggested_btu,
            "estimated_power_kw": round(power_kw, 2),
            "breaker_poles": 2,
            "note": "แอร์ต้องใช้ breaker แยกแต่ละตัว"
        }
    
    def get_room_defaults_summary(
        self,
        room_type: str,
        area_sqm: float = None
    ) -> Dict[str, Any]:
        """Get complete defaults summary for a room."""
        defaults = self.get_defaults(room_type)
        
        if area_sqm is None or area_sqm <= 0:
            area_sqm = defaults.default_area_sqm
        
        outlets = self.calculate_required_outlets(room_type, area_sqm)
        ac = self.calculate_suggested_ac(room_type, area_sqm)
        
        return {
            "room_type": room_type,
            "area_sqm": area_sqm,
            "default_area_sqm": defaults.default_area_sqm,
            "outlets": outlets,
            "ac": ac,
            "needs_dedicated_lighting": defaults.needs_dedicated_lighting,
            "needs_receptacles": defaults.needs_receptacles,
            "smart_home_ready": defaults.smart_home_ready,
            "notes": defaults.notes
        }
    
    def validate_room_design(
        self,
        room_type: str,
        area_sqm: float,
        num_outlets: int,
        has_ac: bool,
        ac_btu: int = 0
    ) -> Dict[str, Any]:
        """Validate room design against defaults."""
        defaults = self.get_defaults(room_type)
        outlet_calc = self.calculate_required_outlets(room_type, area_sqm)
        ac_calc = self.calculate_suggested_ac(room_type, area_sqm)
        
        issues = []
        warnings = []
        
        # Check outlets
        if defaults.needs_receptacles:
            if num_outlets < outlet_calc["required_outlets"]:
                issues.append(
                    f"เต้ารับไม่พอ: มี {num_outlets} ต้องการ {outlet_calc['required_outlets']}"
                )
        else:
            if num_outlets > 0:
                warnings.append(
                    f"ห้องนี้ไม่ควรมีเต้ารับ (มี {num_outlets})"
                )
        
        # Check AC
        if defaults.needs_ac:
            if not has_ac:
                warnings.append("ห้องนี้ควรมีแอร์")
            elif ac_btu > 0 and ac_btu < ac_calc["calculated_btu"] * 0.8:
                warnings.append(
                    f"แอร์อาจเล็กเกินไป: {ac_btu} BTU (แนะนำ {ac_calc['suggested_btu']} BTU)"
                )
        
        return {
            "valid": len(issues) == 0,
            "room_type": room_type,
            "area_sqm": area_sqm,
            "issues": issues,
            "warnings": warnings,
            "recommendations": defaults.notes
        }
    
    def _parse_room_category(self, room_type: str) -> RoomCategory:
        """Parse room type string to category."""
        room_lower = room_type.lower()
        
        mappings = {
            "bedroom": RoomCategory.BEDROOM,
            "ห้องนอน": RoomCategory.BEDROOM,
            "living": RoomCategory.LIVING_ROOM,
            "ห้องนั่งเล่น": RoomCategory.LIVING_ROOM,
            "kitchen": RoomCategory.KITCHEN,
            "ครัว": RoomCategory.KITCHEN,
            "bathroom": RoomCategory.BATHROOM,
            "ห้องน้ำ": RoomCategory.BATHROOM,
            "dining": RoomCategory.DINING_ROOM,
            "ห้องอาหาร": RoomCategory.DINING_ROOM,
            "study": RoomCategory.STUDY,
            "ห้องทำงาน": RoomCategory.STUDY,
            "corridor": RoomCategory.CORRIDOR,
            "ทางเดิน": RoomCategory.CORRIDOR,
            "garage": RoomCategory.GARAGE,
            "โรงรถ": RoomCategory.GARAGE,
            "outdoor": RoomCategory.OUTDOOR,
            "ภายนอก": RoomCategory.OUTDOOR,
            "สวน": RoomCategory.OUTDOOR,
            "laundry": RoomCategory.LAUNDRY,
            "ซักล้าง": RoomCategory.LAUNDRY,
            "storage": RoomCategory.STORAGE,
            "เก็บของ": RoomCategory.STORAGE,
            "pump": RoomCategory.PUMP_ROOM,
            "ปั๊ม": RoomCategory.PUMP_ROOM,
        }
        
        for key, value in mappings.items():
            if key in room_lower:
                return value
        
        return RoomCategory.BEDROOM  # Default


# Global instance
_room_defaults_manager: Optional[RoomDefaultsManager] = None


def get_room_defaults_manager() -> RoomDefaultsManager:
    """Get the global room defaults manager instance."""
    global _room_defaults_manager
    if _room_defaults_manager is None:
        _room_defaults_manager = RoomDefaultsManager()
    return _room_defaults_manager
