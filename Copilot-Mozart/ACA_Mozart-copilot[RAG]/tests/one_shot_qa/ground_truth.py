"""
Ground Truth Data for Engineering Correctness Validation
ข้อมูล Ground Truth จากมาตรฐาน วสท. และ Catalog สำหรับตรวจสอบความถูกต้อง

เจ้าค่ะนายท่าน นี่คือ "ความจริง" ที่ Layer 1 ใช้เทียบกับคำตอบ LLM
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class CableInsulation(str, Enum):
    """ประเภทฉนวนสายไฟ"""
    THW = "THW"  # PVC 70°C
    XLPE = "XLPE"  # 90°C
    THHN = "THHN"  # Nylon-coated 90°C
    VAF = "VAF"  # Flat cable


@dataclass
class CableSpec:
    """Specification for a cable type"""
    cable_id: str
    size_mm2: float
    insulation: CableInsulation
    ampacity_in_conduit_a: float
    ampacity_free_air_a: float
    resistance_ohm_per_km_20c: float
    temp_rating_c: int


@dataclass
class BreakerSpec:
    """Specification for circuit breaker selection"""
    rating_a: int
    min_load_a: float  # Minimum load current for this breaker
    max_load_a: float  # Maximum load current for this breaker (80% rule)
    

@dataclass
class DeratingFactor:
    """Derating factor specification"""
    factor_id: str
    factor_name: str
    derating_type: str
    table: List[Dict[str, Any]]
    standard_reference: str


# =============================================================================
# CABLE AMPACITY TABLE (วสท. 2564 ตาราง 5-20)
# Source: มาตรฐานทางวิศวกรรมไฟฟ้า Thai standard.md + catalog_rows.csv
# =============================================================================

THW_CABLES: Dict[float, CableSpec] = {
    1.5: CableSpec(
        cable_id="CS001",
        size_mm2=1.5,
        insulation=CableInsulation.THW,
        ampacity_in_conduit_a=18,
        ampacity_free_air_a=20,
        resistance_ohm_per_km_20c=12.1,
        temp_rating_c=70
    ),
    2.5: CableSpec(
        cable_id="CS002",
        size_mm2=2.5,
        insulation=CableInsulation.THW,
        ampacity_in_conduit_a=24,
        ampacity_free_air_a=27,
        resistance_ohm_per_km_20c=7.41,
        temp_rating_c=70
    ),
    4.0: CableSpec(
        cable_id="CS004",
        size_mm2=4.0,
        insulation=CableInsulation.THW,
        ampacity_in_conduit_a=32,
        ampacity_free_air_a=36,
        resistance_ohm_per_km_20c=4.61,
        temp_rating_c=70
    ),
    6.0: CableSpec(
        cable_id="CS006",
        size_mm2=6.0,
        insulation=CableInsulation.THW,
        ampacity_in_conduit_a=41,
        ampacity_free_air_a=48,
        resistance_ohm_per_km_20c=3.08,
        temp_rating_c=70
    ),
    10.0: CableSpec(
        cable_id="CS010",
        size_mm2=10.0,
        insulation=CableInsulation.THW,
        ampacity_in_conduit_a=57,
        ampacity_free_air_a=66,
        resistance_ohm_per_km_20c=1.83,
        temp_rating_c=70
    ),
}

XLPE_CABLES: Dict[float, CableSpec] = {
    10.0: CableSpec(
        cable_id="CS005",
        size_mm2=10.0,
        insulation=CableInsulation.XLPE,
        ampacity_in_conduit_a=64,
        ampacity_free_air_a=75,
        resistance_ohm_per_km_20c=1.83,
        temp_rating_c=90
    ),
}


# =============================================================================
# BREAKER SELECTION TABLE (80% rule)
# =============================================================================

STANDARD_BREAKERS: Dict[int, BreakerSpec] = {
    6: BreakerSpec(rating_a=6, min_load_a=0, max_load_a=4.8),
    10: BreakerSpec(rating_a=10, min_load_a=4.8, max_load_a=8.0),
    16: BreakerSpec(rating_a=16, min_load_a=8.0, max_load_a=12.8),
    20: BreakerSpec(rating_a=20, min_load_a=12.8, max_load_a=16.0),
    25: BreakerSpec(rating_a=25, min_load_a=16.0, max_load_a=20.0),
    32: BreakerSpec(rating_a=32, min_load_a=20.0, max_load_a=25.6),
    40: BreakerSpec(rating_a=40, min_load_a=25.6, max_load_a=32.0),
    50: BreakerSpec(rating_a=50, min_load_a=32.0, max_load_a=40.0),
    63: BreakerSpec(rating_a=63, min_load_a=40.0, max_load_a=50.4),
}


def get_correct_breaker(load_current_a: float) -> int:
    """
    Get the correct breaker rating for a given load current.
    Rule: Breaker must be >= load current, but load should be <= 80% of breaker
    
    Args:
        load_current_a: Load current in Amperes
        
    Returns:
        Correct breaker rating in Amperes
    """
    for rating, spec in sorted(STANDARD_BREAKERS.items()):
        if load_current_a <= spec.max_load_a:
            return rating
    return 100  # Default to 100A for very high loads


# =============================================================================
# DERATING FACTORS (IEC 60364-5-52 / วสท.)
# =============================================================================

DERATING_FACTORS: Dict[str, DeratingFactor] = {
    "DF001": DeratingFactor(
        factor_id="DF001",
        factor_name="Conductor grouping in conduit / tray",
        derating_type="conductor_grouping",
        table=[
            {"min_conductors": 1, "max_conductors": 3, "factor": 1.0},
            {"min_conductors": 4, "max_conductors": 6, "factor": 0.8},
            {"min_conductors": 7, "max_conductors": 9, "factor": 0.7},
            {"min_conductors": 10, "max_conductors": 20, "factor": 0.5},
            {"min_conductors": 21, "max_conductors": 30, "factor": 0.4},
        ],
        standard_reference="IEC 60364-5-52 / EIT"
    ),
    "DF002": DeratingFactor(
        factor_id="DF002",
        factor_name="Ambient temperature correction",
        derating_type="ambient_temperature",
        table=[
            {"min_temp_c": 30, "max_temp_c": 40, "factor": 1.0},
            {"min_temp_c": 41, "max_temp_c": 45, "factor": 0.94},
            {"min_temp_c": 46, "max_temp_c": 50, "factor": 0.88},
            {"min_temp_c": 51, "max_temp_c": 55, "factor": 0.82},
            {"min_temp_c": 56, "max_temp_c": 60, "factor": 0.76},
            {"min_temp_c": 61, "max_temp_c": 70, "factor": 0.61},
        ],
        standard_reference="IEC 60364-5-52 Table B.52.x"
    ),
    "DF004": DeratingFactor(
        factor_id="DF004",
        factor_name="Thermal Insulation Derating",
        derating_type="thermal_insulation",
        table=[
            {"insulation_thickness_mm": 0, "derating_factor": 1.0},
            {"insulation_thickness_mm": 50, "derating_factor": 0.85},
            {"insulation_thickness_mm": 100, "derating_factor": 0.75},
            {"insulation_thickness_mm": 200, "derating_factor": 0.6},
        ],
        standard_reference="IEC 60364-5-52"
    ),
}


def get_derating_factor(
    factor_type: str, 
    num_conductors: Optional[int] = None,
    ambient_temp_c: Optional[int] = None,
    insulation_thickness_mm: Optional[int] = None
) -> float:
    """
    Get derating factor based on conditions.
    
    Args:
        factor_type: Type of derating ("conductor_grouping", "ambient_temperature", "thermal_insulation")
        num_conductors: Number of conductors (for grouping derating)
        ambient_temp_c: Ambient temperature in Celsius
        insulation_thickness_mm: Thermal insulation thickness in mm
        
    Returns:
        Derating factor (0.0 to 1.0)
    """
    if factor_type == "conductor_grouping" and num_conductors is not None:
        df = DERATING_FACTORS["DF001"]
        for row in df.table:
            if row["min_conductors"] <= num_conductors <= row["max_conductors"]:
                return row["factor"]
        return 0.4  # Default for very high count
        
    elif factor_type == "ambient_temperature" and ambient_temp_c is not None:
        df = DERATING_FACTORS["DF002"]
        for row in df.table:
            if row["min_temp_c"] <= ambient_temp_c <= row["max_temp_c"]:
                return row["factor"]
        return 0.61  # Default for very high temp
        
    elif factor_type == "thermal_insulation" and insulation_thickness_mm is not None:
        df = DERATING_FACTORS["DF004"]
        # Find the closest thickness
        for i, row in enumerate(df.table):
            if insulation_thickness_mm <= row["insulation_thickness_mm"]:
                return row["derating_factor"]
        return 0.6  # Default for very thick insulation
        
    return 1.0


# =============================================================================
# VOLTAGE DROP CALCULATION
# =============================================================================

def calculate_voltage_drop_1ph(
    current_a: float,
    length_m: float,
    resistance_ohm_per_km: float,
    voltage_v: float = 230
) -> float:
    """
    Calculate voltage drop percentage for single-phase circuit.
    
    Formula: VD% = (2 × I × L × R) / (V × 1000) × 100
    
    Args:
        current_a: Load current in Amperes
        length_m: Cable length (one way) in meters
        resistance_ohm_per_km: Cable resistance in Ohm/km at 20°C
        voltage_v: System voltage (default 230V)
        
    Returns:
        Voltage drop as percentage
    """
    vd_percent = (2 * current_a * length_m * resistance_ohm_per_km) / (voltage_v * 1000) * 100
    return round(vd_percent, 2)


def is_voltage_drop_acceptable(vd_percent: float, max_vd_percent: float = 3.0) -> bool:
    """Check if voltage drop is within acceptable limit."""
    return vd_percent <= max_vd_percent


# =============================================================================
# DEVICE CODES (From DEVICE_CODES.md)
# =============================================================================

VALID_DEVICE_CODES: Dict[str, Dict[str, Any]] = {
    # Air Conditioners
    "AC-9000BTU": {"name": "Air Conditioner 9000 BTU", "power_w": 800},
    "AC-12000BTU": {"name": "Air Conditioner 12000 BTU", "power_w": 1100},
    "AC-18000BTU": {"name": "Air Conditioner 18000 BTU", "power_w": 1600},
    "AC-24000BTU": {"name": "Air Conditioner 24000 BTU", "power_w": 2200},
    
    # Outlets
    "SOCKET-16A": {"name": "Socket Outlet 16A", "current_a": 16},
    "SOCKET-20A": {"name": "Socket Outlet 20A", "current_a": 20},
    
    # Kitchen Appliances
    "INDUCTION-3000W": {"name": "Induction Cooker 3000W", "power_w": 3000},
    "MICROWAVE-1500W": {"name": "Microwave Oven 1500W", "power_w": 1500},
    "RICECOOK-800W": {"name": "Rice Cooker 800W", "power_w": 800},
    "REFRIG-300W": {"name": "Refrigerator 300W", "power_w": 300},
    "DISHWASH-2000W": {"name": "Dishwasher 2000W", "power_w": 2000},
    
    # Water Heaters
    "HEATER-3500W": {"name": "Water Heater 3500W", "power_w": 3500},
    "HEATER-4500W": {"name": "Water Heater 4500W (heavy duty)", "power_w": 4500},
    
    # Lighting
    "LIGHT-LED-10W": {"name": "LED Light 10W", "power_w": 10},
    "LIGHT-LED-20W": {"name": "LED Light 20W", "power_w": 20},
    "LIGHT-FLUOR-40W": {"name": "Fluorescent Light 40W", "power_w": 40},
    
    # Fans
    "FAN-CEILING-60W": {"name": "Ceiling Fan 60W", "power_w": 60},
    "FAN-STAND-50W": {"name": "Stand Fan 50W", "power_w": 50},
    
    # Miscellaneous
    "TV-200W": {"name": "Television 200W", "power_w": 200},
    "COMPUTER-300W": {"name": "Desktop Computer 300W", "power_w": 300},
    "WASHER-2000W": {"name": "Washing Machine 2000W", "power_w": 2000},
    "DRYER-3000W": {"name": "Clothes Dryer 3000W", "power_w": 3000},
}


def is_valid_device_code(code: str) -> bool:
    """Check if device code exists in catalog."""
    return code in VALID_DEVICE_CODES


# =============================================================================
# ROOM TEMPLATES (From ROOM_TEMPLATES.md)
# =============================================================================

VALID_ROOM_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "ROOMT-LIVING-STD": {"name": "Standard living room", "max_area_sqm": 25},
    "ROOMT-LIVING-LARGE": {"name": "Large living room", "min_area_sqm": 25},
    "ROOMT-BEDROOM-STD": {"name": "Standard bedroom"},
    "ROOMT-BEDROOM-MASTER": {"name": "Master bedroom with ensuite"},
    "ROOMT-KITCHEN-STD": {"name": "Standard kitchen"},
    "ROOMT-KITCHEN-HEAVY": {"name": "Heavy load kitchen", "notes": ">5kW appliances"},
    "ROOMT-BATHROOM-STD": {"name": "Standard bathroom"},
    "ROOMT-BATHROOM-MASTER": {"name": "Master bathroom with water heater"},
    "ROOMT-DINING-STD": {"name": "Standard dining room"},
    "ROOMT-STORAGE-STD": {"name": "Storage room"},
    "ROOMT-LAUNDRY-STD": {"name": "Laundry room"},
    "ROOMT-GARAGE-STD": {"name": "Garage"},
    "ROOMT-OFFICE-STD": {"name": "Home office"},
    "ROOMT-BALCONY-STD": {"name": "Balcony"},
}


def is_valid_room_template(template_code: str) -> bool:
    """Check if room template exists."""
    return template_code in VALID_ROOM_TEMPLATES


# =============================================================================
# PLACEMENT RULES (From catalog_rows.csv)
# =============================================================================

PLACEMENT_RULES: Dict[str, Dict[str, Any]] = {
    "outlet_max_spacing_m": 3.6,  # Maximum spacing between outlets
    "outlet_min_height_mm": 300,
    "outlet_max_height_mm": 1200,
    "switch_min_height_mm": 1100,
    "switch_max_height_mm": 1400,
    "min_distance_from_water_mm": 600,  # Bathroom outlets
}


# =============================================================================
# RCD/RCBO REQUIREMENTS
# =============================================================================

RCD_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "bathroom": {
        "required": True,
        "sensitivity_ma": 30,
        "type": "RCBO"
    },
    "wet_area": {
        "required": True,
        "sensitivity_ma": 30,
        "type": "RCD/RCBO"
    },
    "outdoor": {
        "required": True,
        "sensitivity_ma": 30,
        "type": "RCD"
    },
    "general": {
        "required": False,
        "sensitivity_ma": None,
        "type": None
    }
}


def get_rcd_requirement(location_type: str) -> Dict[str, Any]:
    """Get RCD requirement for a location type."""
    return RCD_REQUIREMENTS.get(location_type, RCD_REQUIREMENTS["general"])


# =============================================================================
# STANDARD LIMITS (วสท. 2564)
# =============================================================================

STANDARD_LIMITS = {
    "max_voltage_drop_branch_pct": 3.0,
    "max_voltage_drop_feeder_pct": 5.0,
    "max_voltage_drop_total_pct": 8.0,
    "min_ground_rod_length_m": 2.4,
    "max_ground_resistance_ohm": 5.0,
    "main_cb_min_ic_ka": 10,  # Minimum short circuit rating
    "sub_cb_min_ic_ka": 6,
    "max_outlets_per_circuit": 10,
    "max_circuit_load_percent": 80,
    "outlet_shutter_required": True,  # มอก.166-2549
    "clamp_max_spacing_m": 1.2,
}


# =============================================================================
# TEST UTILITIES
# =============================================================================

def validate_ampacity_claim(
    wire_size_mm2: float,
    claimed_ampacity_a: float,
    insulation: CableInsulation = CableInsulation.THW,
    in_conduit: bool = True,
    tolerance_percent: float = 5.0
) -> tuple[bool, str]:
    """
    Validate if a claimed ampacity is correct for a given wire size.
    
    Args:
        wire_size_mm2: Wire size in square millimeters
        claimed_ampacity_a: The claimed ampacity value to validate
        insulation: Cable insulation type
        in_conduit: Whether cable is in conduit (True) or free air (False)
        tolerance_percent: Acceptable tolerance in percent
        
    Returns:
        Tuple of (is_valid, message)
    """
    if insulation == CableInsulation.THW:
        cables = THW_CABLES
    elif insulation == CableInsulation.XLPE:
        cables = XLPE_CABLES
    else:
        return False, f"Unknown insulation type: {insulation}"
    
    if wire_size_mm2 not in cables:
        return False, f"Wire size {wire_size_mm2}mm² not in catalog"
    
    spec = cables[wire_size_mm2]
    actual_ampacity = spec.ampacity_in_conduit_a if in_conduit else spec.ampacity_free_air_a
    
    lower_bound = actual_ampacity * (1 - tolerance_percent / 100)
    upper_bound = actual_ampacity * (1 + tolerance_percent / 100)
    
    if lower_bound <= claimed_ampacity_a <= upper_bound:
        return True, f"Correct: {wire_size_mm2}mm² THW = {actual_ampacity}A"
    else:
        return False, f"Wrong: {wire_size_mm2}mm² THW = {actual_ampacity}A, not {claimed_ampacity_a}A"
