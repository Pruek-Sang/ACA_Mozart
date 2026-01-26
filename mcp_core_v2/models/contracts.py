"""Contract models for MCP Core v2."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum


def _utc_now() -> datetime:
    """Return current UTC time with timezone info (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class VoltageType(str, Enum):
    """Voltage type enumeration.
    
    Thai Standard (EIT/TIS): 230V single-phase, 400V three-phase
    US Standard (NEC): 120V/240V single-phase, 208V/480V three-phase
    """
    # Thai/IEC Standard
    SINGLE_PHASE_230V = "230V_1PH"    # Thai residential standard
    THREE_PHASE_400V = "400V_3PH"     # Thai commercial standard
    
    # US Standard (for compatibility)
    SINGLE_PHASE_120V = "120V_1PH"
    SINGLE_PHASE_240V = "240V_1PH"
    THREE_PHASE_208V = "208V_3PH"
    THREE_PHASE_480V = "480V_3PH"


class LoadType(str, Enum):
    """Load type enumeration."""
    LIGHTING = "lighting"
    RECEPTACLE = "receptacle"
    HVAC = "hvac"
    MOTOR = "motor"
    APPLIANCE = "appliance"
    SOLAR = "solar"  # [CP-SOLAR] Solar PV system (Generation, not consumption)
    OTHER = "other"


class Location(BaseModel):
    """Location information for equipment."""
    room: str
    floor: Optional[str] = None
    building: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None


class ElectricalLoad(BaseModel):
    """Electrical load specification."""
    id: str
    name: str
    load_type: LoadType
    voltage: VoltageType
    power_watts: float
    quantity: int = 1
    power_factor: Optional[float] = None
    location: Location
    is_continuous: bool = False
    notes: Optional[str] = None
    # ============================================================
    # Voltage Drop Distance Fields (วสท. 2564 Compliant)
    # ============================================================
    branch_distance_m: Optional[float] = Field(
        None,
        description="Distance from distribution board to load in meters. If None, uses default based on building type and floor."
    )
    # ============================================================
    # 3-Phase Support Fields (Sprint 2)
    # ============================================================
    assigned_phase: Optional[str] = Field(
        None,
        description="Assigned phase for 3-phase systems: 'L1', 'L2', or 'L3'. None for 1-phase."
    )


class PanelSpecification(BaseModel):
    """Electrical panel specification."""
    id: str
    name: str
    voltage: VoltageType
    main_breaker_rating: int
    number_of_circuits: int
    location: Location
    feeds: List[str] = Field(default_factory=list)  # Load IDs


class DesignRequest(BaseModel):
    """Design request contract."""
    session_id: str
    project_name: str
    project_number: Optional[str] = None
    loads: List[ElectricalLoad]
    panels: List[PanelSpecification]
    service_voltage: VoltageType
    utility_service_size: int
    created_at: datetime = Field(default_factory=_utc_now)
    metadata: Optional[Dict[str, Any]] = None
    # 🆕 Site context for safety calculations (Derating, kA, N-G Link)
    site_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Site & installation context: distance_to_transformer, installation_area, panel_type, conduit_grouping"
    )
    # ============================================================
    # Voltage Drop Distance Fields (วสท. 2564 Compliant)
    # ============================================================
    building_type: Optional[str] = Field(
        None,
        description="Building type for default distance lookup: บ้านเดี่ยว_1ชั้น, บ้านเดี่ยว_2ชั้น, ทาวน์เฮ้าส์, คอนโด, etc."
    )
    service_distance_m: Optional[float] = Field(
        None,
        description="Distance from transformer to MDB in meters. If None, uses default (30m) with warning."
    )


class DesignResult(BaseModel):
    """Design result contract."""
    session_id: str
    request: DesignRequest
    calculations: Dict[str, Any]  # Includes 'three_phase' key with phase balance data
    wire_sizing: Dict[str, Any]
    breaker_selections: Dict[str, Any]
    conduit_sizing: Dict[str, Any]
    compliance_report: Dict[str, Any]
    grouped_circuits: List[Dict[str, Any]] = Field(default_factory=list)  # Circuit grouping data
    three_phase_data: Optional[Dict[str, Any]] = None  # Sprint 4: 3-phase balance & system info
    autolisp_code: Optional[str] = None
    completed_at: datetime = Field(default_factory=_utc_now)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
