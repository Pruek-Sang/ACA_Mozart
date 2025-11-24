"""Input and Output contracts for MCP Core v2.

Compliant with MCP DESIGN HANDOVER specification.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class RoomType(str, Enum):
    """Supported room types."""
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    KITCHEN = "kitchen"
    LIVING_ROOM = "living_room"
    DINING_ROOM = "dining_room"
    OFFICE = "office"
    GARAGE = "garage"
    STORAGE = "storage"
    HALLWAY = "hallway"
    UTILITY = "utility"


class RoomSpec(BaseModel):
    """Specification for a single room in the project."""

    name: str = Field(..., description="Room identifier/name")
    room_type: RoomType = Field(..., description="Type of room")
    width_m: float = Field(..., gt=0, description="Room width in meters")
    length_m: float = Field(..., gt=0, description="Room length in meters")
    height_m: float = Field(default=2.8, gt=0, description="Room height in meters")


class ProjectInputSpec(BaseModel):
    """Input specification for MCP pipeline.
    
    This is the primary input contract for the /mcp/v2/run endpoint.
    """

    project_id: str = Field(..., description="Unique project identifier")
    project_name: str = Field(..., description="Human-readable project name")
    rooms: List[RoomSpec] = Field(..., min_length=1, description="List of rooms to design")
    voltage: float = Field(default=220.0, description="Nominal voltage (V)")
    phases: int = Field(default=1, ge=1, le=3, description="Number of phases")
    main_breaker_amps: Optional[int] = Field(default=None, description="Main breaker rating (A)")


class WireResult(BaseModel):
    """Wire sizing result for a circuit."""

    wire_size_mm2: float = Field(..., description="Wire cross-section in mm²")
    wire_type: str = Field(..., description="Wire type (e.g., THW)")
    ampacity_a: float = Field(..., description="Wire ampacity in Amps")
    length_m: float = Field(..., description="Total wire length in meters")


class BreakerResult(BaseModel):
    """Breaker selection result for a circuit."""

    breaker_rating_a: int = Field(..., description="Breaker rating in Amps")
    breaker_type: str = Field(..., description="Breaker type (e.g., MCB)")
    breaking_capacity_ka: float = Field(..., description="Breaking capacity in kA")


class ConduitResult(BaseModel):
    """Conduit sizing result for a circuit."""

    conduit_size_mm: int = Field(..., description="Conduit inner diameter in mm")
    conduit_type: str = Field(..., description="Conduit type (e.g., EMT)")
    fill_ratio_percent: float = Field(..., description="Conduit fill ratio percentage")


class CircuitResult(BaseModel):
    """Complete result for a single circuit."""

    circuit_id: str = Field(..., description="Unique circuit identifier")
    circuit_name: str = Field(..., description="Human-readable circuit name")
    room_name: str = Field(..., description="Room this circuit serves")
    circuit_type: str = Field(..., description="Circuit type (lighting/outlet/dedicated)")
    
    # Load information
    connected_load_w: float = Field(..., description="Total connected load in Watts")
    demand_load_w: float = Field(..., description="Demand load after diversity in Watts")
    current_a: float = Field(..., description="Design current in Amps")
    
    # Sizing results
    wire: WireResult = Field(..., description="Wire sizing result")
    breaker: BreakerResult = Field(..., description="Breaker selection result")
    conduit: ConduitResult = Field(..., description="Conduit sizing result")
    
    # Compliance
    voltage_drop_percent: float = Field(..., description="Calculated voltage drop %")
    is_compliant: bool = Field(..., description="Whether circuit meets code requirements")
    compliance_notes: List[str] = Field(default_factory=list, description="Compliance notes/warnings")


class PowerFlowResult(BaseModel):
    """Power flow analysis summary."""

    total_load_kw: float = Field(..., description="Total load in kW")
    total_current_a: float = Field(..., description="Total current in Amps")
    power_factor: float = Field(..., description="Overall power factor")
    voltage_at_furthest_point_v: float = Field(..., description="Voltage at furthest load")
    max_voltage_drop_percent: float = Field(..., description="Maximum voltage drop %")
    convergence_achieved: bool = Field(..., description="Whether power flow converged")


class AutoLispScript(BaseModel):
    """AutoLISP script output."""

    script_content: str = Field(..., description="Complete AutoLISP script text")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    target_software: str = Field(default="AutoCAD", description="Target CAD software")


class McpRunResult(BaseModel):
    """Output result from MCP pipeline.
    
    This is the primary output contract for the /mcp/v2/run endpoint.
    """

    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    
    # Design results
    circuits: List[CircuitResult] = Field(..., description="All circuit results")
    power_flow: PowerFlowResult = Field(..., description="Power flow analysis results")
    
    # Generated artifacts
    autolisp_script: AutoLispScript = Field(..., description="Generated AutoLISP script")
    
    # Summary
    total_circuits: int = Field(..., description="Total number of circuits")
    compliant_circuits: int = Field(..., description="Number of compliant circuits")
    main_breaker_recommended_a: int = Field(..., description="Recommended main breaker rating")
    
    # Metadata
    run_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Run timestamp")
    warnings: List[str] = Field(default_factory=list, description="Any warnings generated")
    errors: List[str] = Field(default_factory=list, description="Any errors (non-fatal)")
