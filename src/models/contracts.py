"""API contracts for MCP Core v2 input/output specifications."""

from typing import Optional

from pydantic import BaseModel, Field


class RoomInputSpec(BaseModel):
    """Input specification for a single room."""

    room_id: str = Field(..., description="Unique identifier for the room")
    room_type: str = Field(..., description="Type of room (e.g., bedroom, kitchen)")
    area_sqm: float = Field(..., gt=0, description="Room area in square meters")
    floor_level: int = Field(default=1, description="Floor level of the room")
    custom_loads: Optional[list[dict]] = Field(
        default=None, description="Optional custom load specifications"
    )


class ProjectInputSpec(BaseModel):
    """Input specification for the entire project."""

    project_id: str = Field(..., description="Unique project identifier")
    project_name: str = Field(..., description="Project name")
    voltage_system: str = Field(
        default="230V", description="Voltage system (e.g., 230V, 400V)"
    )
    phase_system: str = Field(
        default="1-phase", description="Phase system (1-phase or 3-phase)"
    )
    rooms: list[RoomInputSpec] = Field(..., description="List of rooms in the project")
    power_factor: float = Field(default=0.85, ge=0.1, le=1.0, description="Power factor")
    ambient_temp_c: float = Field(default=40.0, description="Ambient temperature in Celsius")


class CircuitResult(BaseModel):
    """Output result for a single circuit."""

    circuit_id: str = Field(..., description="Circuit identifier")
    room_id: str = Field(..., description="Associated room identifier")
    circuit_type: str = Field(..., description="Type of circuit")
    connected_load_w: float = Field(..., description="Connected load in watts")
    demand_load_w: float = Field(..., description="Demand load in watts")
    design_current_a: float = Field(..., description="Design current (Ib) in amperes")
    wire_size_sqmm: float = Field(..., description="Selected wire size in sq mm")
    breaker_rating_a: float = Field(..., description="Breaker rating (In) in amperes")
    conduit_size_mm: float = Field(..., description="Conduit size in mm")
    voltage_drop_pct: float = Field(..., description="Voltage drop percentage")
    compliant: bool = Field(..., description="Whether circuit meets compliance")
    cable_length_m: float = Field(default=15.0, description="Cable length in meters")


class RoomResult(BaseModel):
    """Output result for a single room."""

    room_id: str = Field(..., description="Room identifier")
    room_type: str = Field(..., description="Room type")
    total_connected_load_w: float = Field(..., description="Total connected load")
    total_demand_load_w: float = Field(..., description="Total demand load")
    circuits: list[CircuitResult] = Field(..., description="Circuits in this room")


class McpRunResult(BaseModel):
    """Complete output result from MCP pipeline run."""

    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    total_connected_load_kw: float = Field(..., description="Total connected load in kW")
    total_demand_load_kw: float = Field(..., description="Total demand load in kW")
    main_breaker_rating_a: float = Field(..., description="Main breaker rating in amperes")
    rooms: list[RoomResult] = Field(..., description="Room results")
    overall_compliant: bool = Field(..., description="Overall compliance status")
    compliance_notes: list[str] = Field(
        default_factory=list, description="Compliance notes and warnings"
    )
    autolisp_script: str = Field(default="", description="Generated AutoLISP script")
