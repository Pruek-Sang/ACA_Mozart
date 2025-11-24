"""
MCP Core v2 Contracts
Defines the data contracts (Pydantic models) for the pipeline.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class RoomType(str, Enum):
    """Standard room types."""
    BEDROOM = "bedroom"
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    OFFICE = "office"
    STORAGE = "storage"
    HALLWAY = "hallway"


class OutletType(str, Enum):
    """Outlet types."""
    STANDARD = "standard"
    GROUNDED = "grounded"
    USB = "usb"
    DEDICATED = "dedicated"


class LightType(str, Enum):
    """Light fixture types."""
    CEILING = "ceiling"
    DOWNLIGHT = "downlight"
    WALL = "wall"
    PENDANT = "pendant"
    SPOT = "spot"


# --- Input Contracts ---

class RoomInput(BaseModel):
    """Input specification for a single room."""
    room_id: str = Field(..., description="Unique identifier for the room")
    room_type: RoomType = Field(..., description="Type of room")
    width: float = Field(..., gt=0, description="Room width in meters")
    length: float = Field(..., gt=0, description="Room length in meters")
    height: float = Field(default=2.8, gt=0, description="Room height in meters")
    special_loads: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Special equipment loads (e.g., AC units)"
    )


class ProjectInput(BaseModel):
    """Input specification for a project."""
    project_id: str = Field(..., description="Unique project identifier")
    project_name: str = Field(..., description="Project name")
    rooms: List[RoomInput] = Field(..., min_length=1, description="List of rooms")
    voltage: float = Field(default=220.0, description="System voltage")
    phases: int = Field(default=1, ge=1, le=3, description="Number of phases")


# --- Output Contracts ---

class OutletPlacement(BaseModel):
    """Outlet placement specification."""
    outlet_id: str
    outlet_type: OutletType
    x: float  # X coordinate in room
    y: float  # Y coordinate in room
    height: float = 0.3  # Height from floor in meters
    circuit_id: str


class LightPlacement(BaseModel):
    """Light fixture placement specification."""
    light_id: str
    light_type: LightType
    x: float
    y: float
    wattage: float
    circuit_id: str


class SwitchPlacement(BaseModel):
    """Switch placement specification."""
    switch_id: str
    x: float
    y: float
    height: float = 1.2  # Standard switch height
    controls: List[str]  # Light IDs controlled


class CircuitSpec(BaseModel):
    """Circuit specification."""
    circuit_id: str
    circuit_type: str  # "lighting", "outlet", "dedicated"
    breaker_size: int  # Amperes
    wire_size: float  # mm²
    conduit_size: float  # mm
    total_load: float  # Watts
    connected_devices: List[str]


class RoomDesign(BaseModel):
    """Complete design for a single room."""
    room_id: str
    room_type: RoomType
    area: float  # m²
    outlets: List[OutletPlacement]
    lights: List[LightPlacement]
    switches: List[SwitchPlacement]
    circuits: List[CircuitSpec]
    total_load_watts: float
    compliance_notes: List[str] = []


class ComplianceResult(BaseModel):
    """Compliance check result."""
    is_compliant: bool
    violations: List[str] = []
    warnings: List[str] = []
    standard: str = "EIT/IEC"


class ProjectDesign(BaseModel):
    """Complete project design output."""
    project_id: str
    project_name: str
    rooms: List[RoomDesign]
    main_breaker_size: int
    total_connected_load: float  # Watts
    total_demand_load: float  # Watts after diversity
    compliance: ComplianceResult
    autolisp_script: str = ""
    metadata: Dict[str, Any] = {}
