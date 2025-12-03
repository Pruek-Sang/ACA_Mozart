"""Lighting Calculator Module - Lux Calculation and Fixture Selection.

Calculates required lighting based on:
- Room area (m²)
- Room type (bedroom, kitchen, bathroom, etc.)
- Lux requirements (Thai/IEC standards)

Standards Reference:
- Thai EIT Standard (วสท.)
- IEC 60364
- Illuminating Engineering Society (IES) Guidelines

Formulas:
    Required Lumens = Area × Lux × Maintenance Factor / Utilization Factor
    Number of Fixtures = Required Lumens / Lumens per Fixture
    Power = Number of Fixtures × Watts per Fixture
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class RoomType(str, Enum):
    """Room types for lighting calculation."""
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


@dataclass
class LightFixture:
    """Light fixture specification."""
    name: str
    model: str
    watts: float
    lumens: float
    color_temp_k: int  # Color temperature (2700K warm, 4000K neutral, 6500K cool)
    type: str  # LED, fluorescent, incandescent
    dimmable: bool = False
    smart_ready: bool = False
    price_thb: float = 0.0
    
    @property
    def efficacy(self) -> float:
        """Luminous efficacy (lumens/watt)."""
        return self.lumens / self.watts if self.watts > 0 else 0


# Standard LED fixtures (Thai market common products)
STANDARD_FIXTURES: Dict[str, LightFixture] = {
    "LED_9W_DOWNLIGHT": LightFixture(
        name="ดาวน์ไลท์ LED 9W",
        model="Philips DN020B LED9/CW",
        watts=9,
        lumens=810,
        color_temp_k=4000,
        type="LED",
        dimmable=False,
        smart_ready=False,
        price_thb=195
    ),
    "LED_12W_DOWNLIGHT": LightFixture(
        name="ดาวน์ไลท์ LED 12W",
        model="Philips DN020B LED12/CW",
        watts=12,
        lumens=1080,
        color_temp_k=4000,
        type="LED",
        dimmable=False,
        smart_ready=False,
        price_thb=245
    ),
    "LED_18W_DOWNLIGHT": LightFixture(
        name="ดาวน์ไลท์ LED 18W",
        model="Philips DN020B LED18/CW",
        watts=18,
        lumens=1620,
        color_temp_k=4000,
        type="LED",
        dimmable=False,
        smart_ready=False,
        price_thb=345
    ),
    "LED_24W_CEILING": LightFixture(
        name="โคมเพดาน LED 24W",
        model="Philips CL200 24W",
        watts=24,
        lumens=2160,
        color_temp_k=4000,
        type="LED",
        dimmable=True,
        smart_ready=False,
        price_thb=595
    ),
    "LED_36W_CEILING": LightFixture(
        name="โคมเพดาน LED 36W",
        model="Philips CL200 36W",
        watts=36,
        lumens=3240,
        color_temp_k=4000,
        type="LED",
        dimmable=True,
        smart_ready=False,
        price_thb=895
    ),
    "LED_9W_BULB": LightFixture(
        name="หลอด LED 9W",
        model="Philips LEDBulb 9W E27",
        watts=9,
        lumens=806,
        color_temp_k=3000,
        type="LED",
        dimmable=False,
        smart_ready=False,
        price_thb=79
    ),
    "LED_12W_BULB": LightFixture(
        name="หลอด LED 12W",
        model="Philips LEDBulb 12W E27",
        watts=12,
        lumens=1055,
        color_temp_k=3000,
        type="LED",
        dimmable=False,
        smart_ready=False,
        price_thb=99
    ),
    "LED_SMART_9W": LightFixture(
        name="หลอด Smart LED 9W",
        model="Philips Wiz 9W E27",
        watts=9,
        lumens=806,
        color_temp_k=4000,  # Tunable
        type="LED",
        dimmable=True,
        smart_ready=True,
        price_thb=399
    ),
    "LED_T8_18W": LightFixture(
        name="หลอด LED T8 18W",
        model="Philips Ecofit T8 18W",
        watts=18,
        lumens=1800,
        color_temp_k=4000,
        type="LED",
        dimmable=False,
        smart_ready=False,
        price_thb=159
    ),
    "LED_STRIP_5M": LightFixture(
        name="ไฟ LED Strip 5m",
        model="Philips LED Strip 5m",
        watts=24,  # Total for 5m
        lumens=1200,
        color_temp_k=3000,
        type="LED",
        dimmable=True,
        smart_ready=False,
        price_thb=490
    ),
}


class LightingCalculator:
    """Calculates lighting requirements based on room specifications.
    
    Key Formulas:
    
    1. Required Lumens:
       Φ = E × A × MF / UF
       Where:
       - Φ = Required lumens (lm)
       - E = Required illuminance (lux)
       - A = Room area (m²)
       - MF = Maintenance factor (0.7-0.8 typical)
       - UF = Utilization factor (0.4-0.6 typical)
    
    2. Number of Fixtures:
       N = Φ / Φ_fixture
       Where:
       - N = Number of fixtures
       - Φ_fixture = Lumens per fixture
    
    3. Spacing (for uniform distribution):
       S = √(A / N)
       Maximum spacing ≈ 1.5 × mounting height
    """
    
    # Recommended Lux levels by room type (Thai EIT / IES)
    LUX_REQUIREMENTS: Dict[RoomType, Tuple[int, int, int]] = {
        # (minimum, recommended, maximum)
        RoomType.BEDROOM: (100, 150, 200),
        RoomType.LIVING_ROOM: (150, 200, 300),
        RoomType.KITCHEN: (300, 400, 500),      # Task lighting important
        RoomType.BATHROOM: (150, 200, 300),
        RoomType.DINING_ROOM: (150, 200, 300),
        RoomType.STUDY: (300, 400, 500),        # Reading/work needs high lux
        RoomType.CORRIDOR: (50, 100, 150),
        RoomType.GARAGE: (100, 150, 200),
        RoomType.OUTDOOR: (50, 75, 100),
        RoomType.LAUNDRY: (150, 200, 300),
        RoomType.STORAGE: (50, 100, 150),
    }
    
    # Default factors
    MAINTENANCE_FACTOR = 0.8     # 80% (clean room, good maintenance)
    UTILIZATION_FACTOR = 0.5    # 50% (typical residential)
    
    def __init__(self):
        """Initialize lighting calculator."""
        self.fixtures = STANDARD_FIXTURES
    
    def calculate_lux(
        self,
        room_type: str,
        area_sqm: float,
        fixture: LightFixture = None,
        num_fixtures: int = None
    ) -> Dict[str, Any]:
        """Calculate achieved lux level for given fixtures.
        
        Formula: E = (N × Φ_fixture × UF) / (A × MF)
        
        Args:
            room_type: Type of room
            area_sqm: Room area in square meters
            fixture: Light fixture specification
            num_fixtures: Number of fixtures
            
        Returns:
            Dict with lux level and compliance status
        """
        if fixture is None:
            fixture = self.fixtures["LED_12W_DOWNLIGHT"]
        
        if num_fixtures is None or num_fixtures <= 0:
            num_fixtures = 1
        
        # Calculate achieved lux
        # E = (N × Φ × UF) / (A × MF)
        total_lumens = num_fixtures * fixture.lumens
        lux = (total_lumens * self.UTILIZATION_FACTOR) / \
              (area_sqm * self.MAINTENANCE_FACTOR)
        
        # Get required lux
        room_type_enum = self._parse_room_type(room_type)
        lux_min, lux_rec, lux_max = self.LUX_REQUIREMENTS.get(
            room_type_enum, (100, 150, 200)
        )
        
        # Check compliance
        if lux < lux_min:
            status = "INSUFFICIENT"
            message = f"⚠️ ต่ำกว่าเกณฑ์ ({lux:.0f} < {lux_min} lux)"
        elif lux > lux_max:
            status = "EXCESSIVE"
            message = f"⚠️ เกินจำเป็น ({lux:.0f} > {lux_max} lux) สิ้นเปลือง"
        else:
            status = "OK"
            message = f"✅ เหมาะสม ({lux:.0f} lux)"
        
        return {
            "achieved_lux": round(lux, 1),
            "required_lux": {
                "min": lux_min,
                "recommended": lux_rec,
                "max": lux_max
            },
            "status": status,
            "message": message,
            "fixture": {
                "name": fixture.name,
                "model": fixture.model,
                "watts": fixture.watts,
                "lumens": fixture.lumens
            },
            "num_fixtures": num_fixtures,
            "total_watts": num_fixtures * fixture.watts,
            "total_lumens": total_lumens
        }
    
    def calculate_required_fixtures(
        self,
        room_type: str,
        area_sqm: float,
        fixture_key: str = None,
        target_lux: str = "recommended"
    ) -> Dict[str, Any]:
        """Calculate number of fixtures needed for target lux.
        
        Formula:
        1. Φ_required = E × A × MF / UF
        2. N = Φ_required / Φ_fixture
        
        Args:
            room_type: Type of room
            area_sqm: Room area in square meters
            fixture_key: Key to STANDARD_FIXTURES (e.g., "LED_12W_DOWNLIGHT")
            target_lux: "min", "recommended", or "max"
            
        Returns:
            Dict with fixture count and specifications
        """
        # Get fixture
        if fixture_key and fixture_key in self.fixtures:
            fixture = self.fixtures[fixture_key]
        else:
            # Select appropriate fixture based on room
            fixture = self._select_fixture_for_room(room_type, area_sqm)
        
        # Get target lux
        room_type_enum = self._parse_room_type(room_type)
        lux_min, lux_rec, lux_max = self.LUX_REQUIREMENTS.get(
            room_type_enum, (100, 150, 200)
        )
        
        if target_lux == "min":
            target = lux_min
        elif target_lux == "max":
            target = lux_max
        else:
            target = lux_rec
        
        # Calculate required lumens
        # Φ = E × A × MF / UF
        required_lumens = (target * area_sqm * self.MAINTENANCE_FACTOR) / \
                         self.UTILIZATION_FACTOR
        
        # Calculate number of fixtures (round up)
        num_fixtures = math.ceil(required_lumens / fixture.lumens)
        
        # Minimum 1 fixture
        num_fixtures = max(1, num_fixtures)
        
        # Calculate achieved lux with this count
        lux_result = self.calculate_lux(room_type, area_sqm, fixture, num_fixtures)
        
        # Calculate spacing
        spacing = self._calculate_spacing(area_sqm, num_fixtures)
        
        # Total cost
        total_cost = num_fixtures * fixture.price_thb
        
        return {
            "room_type": room_type,
            "area_sqm": area_sqm,
            "target_lux": target,
            "required_lumens": round(required_lumens, 0),
            "fixture": {
                "key": fixture_key or self._get_fixture_key(fixture),
                "name": fixture.name,
                "model": fixture.model,
                "watts": fixture.watts,
                "lumens": fixture.lumens,
                "efficacy_lm_w": round(fixture.efficacy, 1),
                "color_temp_k": fixture.color_temp_k,
                "dimmable": fixture.dimmable,
                "smart_ready": fixture.smart_ready,
                "unit_price_thb": fixture.price_thb
            },
            "num_fixtures": num_fixtures,
            "total_watts": num_fixtures * fixture.watts,
            "total_lumens": num_fixtures * fixture.lumens,
            "achieved_lux": lux_result["achieved_lux"],
            "lux_status": lux_result["status"],
            "spacing_m": spacing,
            "total_cost_thb": total_cost,
            "energy_saving_note": self._get_energy_note(fixture, num_fixtures)
        }
    
    def _select_fixture_for_room(
        self,
        room_type: str,
        area_sqm: float
    ) -> LightFixture:
        """Select appropriate fixture based on room type and size."""
        room_type_enum = self._parse_room_type(room_type)
        
        # Small rooms: use smaller fixtures
        if area_sqm <= 10:
            if room_type_enum == RoomType.BATHROOM:
                return self.fixtures["LED_9W_DOWNLIGHT"]
            return self.fixtures["LED_12W_DOWNLIGHT"]
        
        # Medium rooms
        elif area_sqm <= 20:
            if room_type_enum in [RoomType.KITCHEN, RoomType.STUDY]:
                return self.fixtures["LED_18W_DOWNLIGHT"]
            return self.fixtures["LED_12W_DOWNLIGHT"]
        
        # Large rooms
        else:
            if room_type_enum == RoomType.LIVING_ROOM:
                return self.fixtures["LED_24W_CEILING"]
            return self.fixtures["LED_18W_DOWNLIGHT"]
    
    def _calculate_spacing(self, area_sqm: float, num_fixtures: int) -> float:
        """Calculate uniform spacing between fixtures.
        
        Formula: S = √(A / N)
        """
        if num_fixtures <= 0:
            return 0
        
        return round(math.sqrt(area_sqm / num_fixtures), 2)
    
    def _parse_room_type(self, room_type: str) -> RoomType:
        """Parse room type string to enum."""
        room_type_lower = room_type.lower()
        
        mappings = {
            "bedroom": RoomType.BEDROOM,
            "ห้องนอน": RoomType.BEDROOM,
            "living": RoomType.LIVING_ROOM,
            "living_room": RoomType.LIVING_ROOM,
            "ห้องนั่งเล่น": RoomType.LIVING_ROOM,
            "kitchen": RoomType.KITCHEN,
            "ครัว": RoomType.KITCHEN,
            "bathroom": RoomType.BATHROOM,
            "ห้องน้ำ": RoomType.BATHROOM,
            "dining": RoomType.DINING_ROOM,
            "dining_room": RoomType.DINING_ROOM,
            "ห้องอาหาร": RoomType.DINING_ROOM,
            "study": RoomType.STUDY,
            "ห้องทำงาน": RoomType.STUDY,
            "corridor": RoomType.CORRIDOR,
            "ทางเดิน": RoomType.CORRIDOR,
            "garage": RoomType.GARAGE,
            "โรงรถ": RoomType.GARAGE,
            "outdoor": RoomType.OUTDOOR,
            "ภายนอก": RoomType.OUTDOOR,
            "สวน": RoomType.OUTDOOR,
            "laundry": RoomType.LAUNDRY,
            "ซักล้าง": RoomType.LAUNDRY,
            "storage": RoomType.STORAGE,
            "เก็บของ": RoomType.STORAGE,
        }
        
        for key, value in mappings.items():
            if key in room_type_lower:
                return value
        
        return RoomType.BEDROOM  # Default
    
    def _get_fixture_key(self, fixture: LightFixture) -> str:
        """Get fixture key from fixture object."""
        for key, f in self.fixtures.items():
            if f.model == fixture.model:
                return key
        return "UNKNOWN"
    
    def _get_energy_note(self, fixture: LightFixture, num_fixtures: int) -> str:
        """Generate energy saving note."""
        total_watts = fixture.watts * num_fixtures
        
        # Compare with incandescent equivalent
        # LED ~90 lm/W, Incandescent ~15 lm/W
        incandescent_equiv = (fixture.lumens * num_fixtures) / 15
        savings_percent = ((incandescent_equiv - total_watts) / incandescent_equiv) * 100
        
        return f"ประหยัดไฟ ~{savings_percent:.0f}% เทียบหลอดไส้"
    
    def get_all_fixtures(self) -> Dict[str, Dict[str, Any]]:
        """Get all available fixtures."""
        return {
            key: {
                "name": f.name,
                "model": f.model,
                "watts": f.watts,
                "lumens": f.lumens,
                "efficacy": round(f.efficacy, 1),
                "color_temp_k": f.color_temp_k,
                "dimmable": f.dimmable,
                "smart_ready": f.smart_ready,
                "price_thb": f.price_thb
            }
            for key, f in self.fixtures.items()
        }


# Global instance
_lighting_calculator: Optional[LightingCalculator] = None


def get_lighting_calculator() -> LightingCalculator:
    """Get the global lighting calculator instance."""
    global _lighting_calculator
    if _lighting_calculator is None:
        _lighting_calculator = LightingCalculator()
    return _lighting_calculator
