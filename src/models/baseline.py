"""Baseline intermediate calculation objects for MCP Core v2."""

from typing import Optional

from pydantic import BaseModel, Field


class BaselineCircuit(BaseModel):
    """Intermediate calculation object for a circuit."""

    circuit_id: str = Field(..., description="Circuit identifier")
    room_id: str = Field(..., description="Associated room identifier")
    circuit_type: str = Field(..., description="Type of circuit (lighting, outlet, etc.)")
    
    # Load values
    connected_load_w: float = Field(default=0.0, description="Connected load in watts")
    demand_factor: float = Field(default=1.0, description="Demand factor (0-1)")
    demand_load_w: float = Field(default=0.0, description="Demand load in watts")
    
    # Electrical parameters
    voltage_v: float = Field(default=230.0, description="Operating voltage")
    power_factor: float = Field(default=0.85, description="Power factor")
    design_current_a: float = Field(default=0.0, description="Design current (Ib)")
    
    # Cable properties
    cable_length_m: float = Field(default=15.0, description="Cable length in meters")
    wire_size_sqmm: float = Field(default=0.0, description="Wire cross-section in sq mm")
    cable_type: str = Field(default="THW", description="Cable type")
    cable_material: str = Field(default="copper", description="Cable material")
    
    # Protection
    breaker_rating_a: float = Field(default=0.0, description="Breaker rating (In)")
    
    # Conduit
    conduit_size_mm: float = Field(default=0.0, description="Conduit size in mm")
    conduit_fill_pct: float = Field(default=0.0, description="Conduit fill percentage")
    
    # Analysis results
    voltage_drop_v: float = Field(default=0.0, description="Voltage drop in volts")
    voltage_drop_pct: float = Field(default=0.0, description="Voltage drop percentage")
    compliant: bool = Field(default=True, description="Compliance status")
    compliance_notes: list[str] = Field(
        default_factory=list, description="Compliance notes"
    )


class BaselineRoom(BaseModel):
    """Intermediate calculation object for a room."""

    room_id: str = Field(..., description="Room identifier")
    room_type: str = Field(..., description="Room type")
    area_sqm: float = Field(..., description="Room area in sq meters")
    floor_level: int = Field(default=1, description="Floor level")
    
    # Calculated totals
    total_connected_load_w: float = Field(default=0.0, description="Total connected load")
    total_demand_load_w: float = Field(default=0.0, description="Total demand load")
    
    # Circuits in this room
    circuits: list[BaselineCircuit] = Field(
        default_factory=list, description="Circuits in this room"
    )
    
    # Custom loads if any
    custom_loads: Optional[list[dict]] = Field(
        default=None, description="Custom load specifications"
    )


class BaselineContext(BaseModel):
    """Complete baseline context for the project calculation."""

    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    
    # System parameters
    voltage_system: str = Field(default="230V", description="Voltage system")
    phase_system: str = Field(default="1-phase", description="Phase system")
    nominal_voltage: float = Field(default=230.0, description="Nominal voltage in volts")
    power_factor: float = Field(default=0.85, description="Power factor")
    ambient_temp_c: float = Field(default=40.0, description="Ambient temperature")
    
    # Rooms with circuits
    rooms: list[BaselineRoom] = Field(
        default_factory=list, description="Rooms in the project"
    )
    
    # Project totals
    total_connected_load_w: float = Field(default=0.0, description="Total connected load")
    total_demand_load_w: float = Field(default=0.0, description="Total demand load")
    main_breaker_rating_a: float = Field(default=0.0, description="Main breaker rating")
    
    # Overall compliance
    overall_compliant: bool = Field(default=True, description="Overall compliance")
    compliance_notes: list[str] = Field(
        default_factory=list, description="Project-level compliance notes"
    )
    
    # Generated scripts
    autolisp_script: str = Field(default="", description="Generated AutoLISP script")
