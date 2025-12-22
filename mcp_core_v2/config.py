"""Configuration module for MCP Core v2."""

import os
from typing import Optional, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables
load_env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=load_env_path)


# ============================================================
# Default Branch Distance Table (by building type, per floor)
# Unit: meters from distribution board (MDB/SDB)
# Based on typical Thai residential/commercial buildings
# ============================================================
DEFAULT_BRANCH_DISTANCE_M: Dict[str, Dict[str, float]] = {
    "บ้านเดี่ยว_1ชั้น": {"floor_1": 15.0, "default": 15.0},
    "บ้านเดี่ยว_2ชั้น": {"floor_1": 15.0, "floor_2": 25.0, "default": 20.0},
    "บ้านเดี่ยว_3ชั้น": {"floor_1": 15.0, "floor_2": 25.0, "floor_3": 35.0, "default": 25.0},
    "ทาวน์เฮ้าส์": {"floor_1": 10.0, "floor_2": 18.0, "default": 14.0},
    "ทาวน์โฮม": {"floor_1": 10.0, "floor_2": 18.0, "floor_3": 26.0, "default": 18.0},
    "คอนโด": {"default": 10.0},
    "อพาร์ทเมนต์": {"default": 12.0},
    "สำนักงาน": {"default": 20.0},
    "โรงงาน": {"default": 30.0},
    "default": {"default": 15.0}  # Fallback for unknown types
}

# Meters to Feet conversion factor
METERS_TO_FEET: float = 3.28084


# ============================================================
# VD Compliance Configuration (วสท. 2564 / NEC 2023)
# Future Enhancements Tracking
# ============================================================
from dataclasses import dataclass, field
from typing import List


@dataclass
class VDComplianceConfig:
    """Voltage Drop compliance configuration per วสท. 2564 standard.
    
    This dataclass tracks VD calculation requirements and future enhancements.
    """
    # Current limits (implemented)
    branch_limit_percent: float = 3.0      # ✅ Implemented in wire_sizer.py
    
    # Future enhancements (TODO)
    service_limit_percent: float = 2.0     # ❌ TODO: Calculate Service VD (meter→MDB)
    total_limit_percent: float = 5.0       # ❌ TODO: Calculate Total VD (Service + Branch)
    
    # Default assumptions
    default_ambient_temp_c: float = 30.0   # ⚠️ Thai outdoor may be 35-40°C
    default_service_distance_m: float = 30.0
    
    # Implementation status (for tracking)
    implemented_features: List[str] = field(default_factory=lambda: [
        "branch_vd_calculation",
        "branch_vd_limit_check", 
        "auto_wire_upsize_for_vd",
        "default_distance_by_building_type",
        "distance_warning_in_report"
    ])
    
    pending_features: List[str] = field(default_factory=lambda: [
        # Priority 1 - Medium importance
        "service_vd_calculation",       # มิเตอร์→MDB using service_distance_m
        "total_vd_check",               # Service + Branch ≤ 5%
        # Priority 2 - Medium importance  
        "conduit_fill_check",           # NEC 40% fill limit
        # Priority 3 - Low importance
        "outdoor_ambient_temp_warning", # Thai 35-40°C vs default 30°C
    ])


# Global VD compliance config instance
VD_COMPLIANCE = VDComplianceConfig()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Data Source Configuration (File-based, no external DB required)
    catalog_csv_path: str = ""  # Auto-detected if empty
    
    # Application Settings
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 5001
    
    # Google API (optional)
    google_api_key: str = ""
    
    # Thai Standard Settings
    default_voltage: str = "230V_1PH"
    default_frequency: str = "50Hz"
    
    # NEC Standards
    nec_version: str = "2023"
    voltage_drop_limit: float = 0.03
    temperature_rating: int = 75
    
    # Calculation Settings
    safety_factor: float = 1.25
    default_power_factor: float = 0.85
    
    # ============================================================
    # Voltage Drop Distance Settings (วสท. 2564 Compliant)
    # ============================================================
    # Default service entrance distance (transformer → MDB) in meters
    # Used when user doesn't specify distance
    default_service_distance_m: float = 30.0
    
    # VD Limits per วสท. 2564 Standard
    vd_limit_service_percent: float = 2.0   # Service entrance ≤ 2%
    vd_limit_branch_percent: float = 3.0    # Branch circuit ≤ 3%
    vd_limit_total_percent: float = 5.0     # Total ≤ 5%
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def get_branch_distance_m(
    building_type: Optional[str] = None,
    floor_level: Optional[str] = None
) -> float:
    """Get default branch circuit distance in meters based on building type and floor.
    
    Args:
        building_type: Building type (e.g., "บ้านเดี่ยว_2ชั้น", "คอนโด")
        floor_level: Floor level (e.g., "1", "2", "floor_1", "floor_2")
        
    Returns:
        Distance in meters (float)
    """
    # Normalize building type
    if not building_type:
        building_type = "default"
    
    # Get building config or fallback to default
    building_config = DEFAULT_BRANCH_DISTANCE_M.get(
        building_type,
        DEFAULT_BRANCH_DISTANCE_M.get("default", {"default": 15.0})
    )
    
    # Normalize floor level
    if floor_level:
        # Handle various floor formats: "1", "floor_1", "ชั้น 1", etc.
        floor_key = floor_level.lower().strip()
        if not floor_key.startswith("floor_"):
            # Extract number from string
            import re
            match = re.search(r'(\d+)', floor_key)
            if match:
                floor_key = f"floor_{match.group(1)}"
            else:
                floor_key = "default"
    else:
        floor_key = "default"
    
    # Get distance for floor or fallback to building default
    distance = building_config.get(
        floor_key,
        building_config.get("default", 15.0)
    )
    
    return float(distance)


def get_branch_distance_feet(
    building_type: Optional[str] = None,
    floor_level: Optional[str] = None
) -> float:
    """Get default branch circuit distance in feet.
    
    Convenience wrapper that converts meters to feet.
    """
    distance_m = get_branch_distance_m(building_type, floor_level)
    return distance_m * METERS_TO_FEET
