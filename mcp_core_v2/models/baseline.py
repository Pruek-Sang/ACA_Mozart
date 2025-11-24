"""
MCP Core v2 Baseline Data
Default values for electrical design when catalog is unavailable.
"""

from typing import Dict, List, Any
from .contracts import RoomType, LightType


# --- Baseline Outlet Rules ---
# Outlets per room type (minimum requirements per EIT standard)
BASELINE_OUTLET_RULES: Dict[RoomType, Dict[str, Any]] = {
    RoomType.BEDROOM: {
        "min_outlets": 3,
        "outlets_per_wall": 1,
        "max_spacing_m": 4.5,
        "height_m": 0.3,
        "recommended_circuits": 1,
    },
    RoomType.LIVING_ROOM: {
        "min_outlets": 4,
        "outlets_per_wall": 1,
        "max_spacing_m": 4.5,
        "height_m": 0.3,
        "recommended_circuits": 2,
    },
    RoomType.KITCHEN: {
        "min_outlets": 4,
        "outlets_per_wall": 2,
        "max_spacing_m": 1.2,  # Counter spacing
        "height_m": 1.1,  # Counter height
        "recommended_circuits": 2,
        "dedicated_circuits": ["refrigerator", "microwave"],
    },
    RoomType.BATHROOM: {
        "min_outlets": 1,
        "outlets_per_wall": 1,
        "max_spacing_m": 4.5,
        "height_m": 1.2,
        "recommended_circuits": 1,
        "gfci_required": True,
    },
    RoomType.OFFICE: {
        "min_outlets": 4,
        "outlets_per_wall": 2,
        "max_spacing_m": 3.0,
        "height_m": 0.3,
        "recommended_circuits": 2,
    },
    RoomType.STORAGE: {
        "min_outlets": 1,
        "outlets_per_wall": 1,
        "max_spacing_m": 6.0,
        "height_m": 0.3,
        "recommended_circuits": 1,
    },
    RoomType.HALLWAY: {
        "min_outlets": 1,
        "outlets_per_wall": 1,
        "max_spacing_m": 6.0,
        "height_m": 0.3,
        "recommended_circuits": 1,
    },
}


# --- Baseline Lighting Rules ---
# Watts per square meter by room type
BASELINE_LIGHTING_RULES: Dict[RoomType, Dict[str, Any]] = {
    RoomType.BEDROOM: {
        "watts_per_sqm": 10,
        "lux_target": 150,
        "preferred_type": LightType.CEILING,
        "min_fixtures": 1,
    },
    RoomType.LIVING_ROOM: {
        "watts_per_sqm": 15,
        "lux_target": 200,
        "preferred_type": LightType.CEILING,
        "min_fixtures": 2,
    },
    RoomType.KITCHEN: {
        "watts_per_sqm": 20,
        "lux_target": 300,
        "preferred_type": LightType.DOWNLIGHT,
        "min_fixtures": 2,
    },
    RoomType.BATHROOM: {
        "watts_per_sqm": 15,
        "lux_target": 200,
        "preferred_type": LightType.DOWNLIGHT,
        "min_fixtures": 1,
    },
    RoomType.OFFICE: {
        "watts_per_sqm": 20,
        "lux_target": 500,
        "preferred_type": LightType.CEILING,
        "min_fixtures": 2,
    },
    RoomType.STORAGE: {
        "watts_per_sqm": 8,
        "lux_target": 100,
        "preferred_type": LightType.CEILING,
        "min_fixtures": 1,
    },
    RoomType.HALLWAY: {
        "watts_per_sqm": 10,
        "lux_target": 100,
        "preferred_type": LightType.DOWNLIGHT,
        "min_fixtures": 1,
    },
}


# --- Wire Sizing Table (Copper, PVC insulation) ---
# Based on EIT standard for installation method B2 (enclosed in conduit)
WIRE_SIZE_TABLE: List[Dict[str, Any]] = [
    {"size_sqmm": 1.0, "max_amps": 11, "conduit_mm": 16},
    {"size_sqmm": 1.5, "max_amps": 14, "conduit_mm": 16},
    {"size_sqmm": 2.5, "max_amps": 18, "conduit_mm": 16},
    {"size_sqmm": 4.0, "max_amps": 24, "conduit_mm": 20},
    {"size_sqmm": 6.0, "max_amps": 31, "conduit_mm": 20},
    {"size_sqmm": 10.0, "max_amps": 42, "conduit_mm": 25},
    {"size_sqmm": 16.0, "max_amps": 56, "conduit_mm": 32},
    {"size_sqmm": 25.0, "max_amps": 73, "conduit_mm": 32},
    {"size_sqmm": 35.0, "max_amps": 89, "conduit_mm": 40},
    {"size_sqmm": 50.0, "max_amps": 108, "conduit_mm": 50},
    {"size_sqmm": 70.0, "max_amps": 136, "conduit_mm": 50},
    {"size_sqmm": 95.0, "max_amps": 164, "conduit_mm": 63},
    {"size_sqmm": 120.0, "max_amps": 188, "conduit_mm": 63},
]


# --- Standard Breaker Sizes ---
STANDARD_BREAKER_SIZES: List[int] = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125]


# --- Conduit Fill Rules ---
# Maximum fill percentage by number of conductors
CONDUIT_FILL_RULES: Dict[int, float] = {
    1: 0.53,  # 53% for 1 conductor
    2: 0.31,  # 31% for 2 conductors
    3: 0.40,  # 40% for 3+ conductors
}


# --- Demo Room Data ---
# 4x3m bedroom for testing
DEMO_BEDROOM: Dict[str, Any] = {
    "room_id": "demo-bedroom-001",
    "room_type": "bedroom",
    "width": 4.0,
    "length": 3.0,
    "height": 2.8,
    "special_loads": None,
}


# --- Demand Factors ---
# Diversity factors for load calculation
DEMAND_FACTORS: Dict[str, float] = {
    "lighting": 1.0,  # 100% for first 2000W, 35% thereafter
    "outlet_first_10kw": 1.0,
    "outlet_over_10kw": 0.5,
    "ac": 1.0,
    "kitchen": 0.8,
}
