"""Contract models for MCP Core v2."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class VoltageType(str, Enum):
    """Voltage type enumeration."""
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class DesignResult(BaseModel):
    """Design result contract."""
    session_id: str
    request: DesignRequest
    calculations: Dict[str, Any]
    wire_sizing: Dict[str, Any]
    breaker_selections: Dict[str, Any]
    conduit_sizing: Dict[str, Any]
    compliance_report: Dict[str, Any]
    autolisp_code: Optional[str] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
