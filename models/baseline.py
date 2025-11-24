"""Intermediate baseline representations for MCP Core v2.

These models represent the resolved, enriched state of a project
after template resolution but before electrical calculations.
"""

from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class CircuitType(str, Enum):
    """Types of electrical circuits."""
    LIGHTING = "lighting"
    OUTLET = "outlet"
    DEDICATED = "dedicated"  # For specific appliances like AC, water heater


class LoadType(str, Enum):
    """Types of electrical loads."""
    RESISTIVE = "resistive"
    INDUCTIVE = "inductive"
    CAPACITIVE = "capacitive"
    MIXED = "mixed"


class BaselineLoad(BaseModel):
    """A single electrical load within a circuit."""

    load_id: str = Field(..., description="Unique load identifier")
    name: str = Field(..., description="Load name")
    watts: float = Field(..., ge=0, description="Load power in Watts")
    load_type: LoadType = Field(default=LoadType.RESISTIVE, description="Type of load")
    power_factor: float = Field(default=1.0, ge=0, le=1, description="Load power factor")
    quantity: int = Field(default=1, ge=1, description="Number of identical loads")
    demand_factor: float = Field(default=1.0, ge=0, le=1, description="Demand factor for diversity")
    
    # Position for AutoLISP (optional)
    x_position_m: Optional[float] = Field(default=None, description="X position in room")
    y_position_m: Optional[float] = Field(default=None, description="Y position in room")


class BaselineCircuit(BaseModel):
    """A complete circuit with all its loads."""

    circuit_id: str = Field(..., description="Unique circuit identifier")
    name: str = Field(..., description="Circuit name")
    circuit_type: CircuitType = Field(..., description="Type of circuit")
    loads: List[BaselineLoad] = Field(default_factory=list, description="Loads on this circuit")
    
    # Circuit properties
    distance_from_panel_m: float = Field(default=10.0, ge=0, description="Distance from panel in meters")
    voltage: float = Field(default=220.0, description="Circuit voltage")
    
    # Calculated fields (populated during processing)
    total_connected_load_w: float = Field(default=0.0, description="Sum of all loads")
    total_demand_load_w: float = Field(default=0.0, description="Load after demand factors")
    design_current_a: float = Field(default=0.0, description="Design current in Amps")


class BaselineRoom(BaseModel):
    """A room with its resolved circuits and loads."""

    room_id: str = Field(..., description="Unique room identifier")
    name: str = Field(..., description="Room name")
    room_type: str = Field(..., description="Type of room")
    
    # Dimensions
    width_m: float = Field(..., gt=0, description="Room width in meters")
    length_m: float = Field(..., gt=0, description="Room length in meters")
    height_m: float = Field(default=2.8, gt=0, description="Room height in meters")
    area_m2: float = Field(default=0.0, ge=0, description="Room area in m²")
    
    # Circuits
    circuits: List[BaselineCircuit] = Field(default_factory=list, description="Circuits serving this room")
    
    # Panel distance (for voltage drop calculations)
    distance_from_panel_m: float = Field(default=10.0, ge=0, description="Distance from main panel")


class BaselineContext(BaseModel):
    """Complete baseline context for a project.
    
    This is the intermediate representation after template resolution
    and before electrical calculations.
    """

    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    
    # Electrical system parameters
    voltage: float = Field(default=220.0, description="System voltage")
    frequency: float = Field(default=50.0, description="System frequency (Hz)")
    phases: int = Field(default=1, description="Number of phases")
    
    # Rooms with resolved circuits
    rooms: List[BaselineRoom] = Field(default_factory=list, description="All rooms")
    
    # Summary fields (calculated)
    total_area_m2: float = Field(default=0.0, description="Total floor area")
    total_connected_load_w: float = Field(default=0.0, description="Total connected load")
    total_circuits: int = Field(default=0, description="Total number of circuits")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
