"""Catalog models matching database views from Supabase amadeus schema."""

from typing import Optional

from pydantic import BaseModel, Field


class RoomTemplate(BaseModel):
    """Room template from database defining standard loads for room types."""

    id: Optional[int] = Field(default=None, description="Template ID")
    room_type: str = Field(..., description="Room type identifier")
    description: Optional[str] = Field(default=None, description="Template description")
    
    # Standard load definitions per sq meter
    lighting_load_w_sqm: float = Field(
        default=20.0, description="Lighting load watts per sq meter"
    )
    outlet_load_w: float = Field(
        default=180.0, description="Standard outlet load in watts"
    )
    outlet_count_per_sqm: float = Field(
        default=0.1, description="Number of outlets per sq meter"
    )
    
    # Special loads
    has_ac_circuit: bool = Field(default=False, description="Whether room needs AC circuit")
    ac_load_w: float = Field(default=0.0, description="AC load in watts if applicable")
    
    has_special_outlet: bool = Field(
        default=False, description="Whether room has special outlets"
    )
    special_outlet_load_w: float = Field(
        default=0.0, description="Special outlet load in watts"
    )
    
    # Demand factors
    lighting_demand_factor: float = Field(
        default=1.0, description="Demand factor for lighting"
    )
    outlet_demand_factor: float = Field(
        default=0.5, description="Demand factor for outlets"
    )
    ac_demand_factor: float = Field(default=1.0, description="Demand factor for AC")


class CableSpec(BaseModel):
    """Cable specification from database."""

    id: Optional[int] = Field(default=None, description="Cable spec ID")
    size_sqmm: float = Field(..., description="Cross-sectional area in sq mm")
    material: str = Field(default="copper", description="Cable material")
    insulation_type: str = Field(default="THW", description="Insulation type")
    
    # Current carrying capacity at different temperatures
    ampacity_30c: float = Field(..., description="Ampacity at 30°C ambient")
    ampacity_40c: float = Field(..., description="Ampacity at 40°C ambient")
    ampacity_45c: float = Field(default=0.0, description="Ampacity at 45°C ambient")
    
    # Resistance values
    resistance_ohm_km: float = Field(..., description="Resistance in ohm per km")
    reactance_ohm_km: float = Field(default=0.08, description="Reactance in ohm per km")
    
    # Physical properties
    outer_diameter_mm: float = Field(..., description="Outer diameter in mm")
    weight_kg_km: float = Field(default=0.0, description="Weight in kg per km")
    
    # Voltage rating
    voltage_rating_v: int = Field(default=750, description="Voltage rating in volts")


class BreakerSpec(BaseModel):
    """Breaker specification from database."""

    id: Optional[int] = Field(default=None, description="Breaker spec ID")
    rating_a: float = Field(..., description="Current rating in amperes")
    poles: int = Field(default=1, description="Number of poles")
    type: str = Field(default="MCB", description="Breaker type (MCB, MCCB, etc.)")
    
    # Breaking capacity
    breaking_capacity_ka: float = Field(
        default=10.0, description="Breaking capacity in kA"
    )
    
    # Trip characteristics
    trip_curve: str = Field(default="C", description="Trip curve type (B, C, D)")
    
    # Frame size
    frame_size: Optional[str] = Field(default=None, description="Frame size designation")
    
    # Manufacturer info
    manufacturer: Optional[str] = Field(default=None, description="Manufacturer name")
    model: Optional[str] = Field(default=None, description="Model number")


class ConduitSpec(BaseModel):
    """Conduit specification from database."""

    id: Optional[int] = Field(default=None, description="Conduit spec ID")
    size_mm: float = Field(..., description="Trade size in mm")
    material: str = Field(default="PVC", description="Conduit material")
    
    # Cross-sectional area
    internal_area_sqmm: float = Field(..., description="Internal cross-sectional area")
    
    # Fill percentages allowed per NEC
    max_fill_1_wire_pct: float = Field(
        default=53.0, description="Max fill for 1 wire (%)"
    )
    max_fill_2_wire_pct: float = Field(
        default=31.0, description="Max fill for 2 wires (%)"
    )
    max_fill_3plus_wire_pct: float = Field(
        default=40.0, description="Max fill for 3+ wires (%)"
    )
