"""Catalog models mapping to amadeus.catalog views.

These models represent the reference data from the catalog database
that informs electrical design decisions.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RoomTemplate(BaseModel):
    """Template for standard room electrical requirements.
    
    Maps to amadeus.catalog.room_templates view.
    """

    template_id: str = Field(..., description="Unique template identifier")
    room_type: str = Field(..., description="Type of room")
    
    # Default lighting requirements
    lighting_watts_per_m2: float = Field(..., description="Lighting load per m²")
    min_lighting_points: int = Field(..., description="Minimum number of lighting points")
    
    # Default outlet requirements
    outlets_per_m2: float = Field(..., description="Outlet count per m²")
    min_outlets: int = Field(..., description="Minimum outlets")
    outlet_watts_each: float = Field(default=180.0, description="Assumed load per outlet")
    
    # Special requirements
    requires_dedicated_circuit: bool = Field(default=False, description="Needs dedicated circuit")
    dedicated_circuit_load_w: Optional[float] = Field(default=None, description="Dedicated circuit load")
    dedicated_circuit_name: Optional[str] = Field(default=None, description="Dedicated circuit name")
    
    # Safety margins
    diversity_factor: float = Field(default=0.8, description="Diversity/demand factor")


class CircuitTemplate(BaseModel):
    """Template for standard circuit configurations.
    
    Maps to amadeus.catalog.circuit_templates view.
    """

    template_id: str = Field(..., description="Unique template identifier")
    circuit_type: str = Field(..., description="Type of circuit (lighting/outlet/dedicated)")
    name_pattern: str = Field(..., description="Naming pattern for circuit")
    
    # Default ratings
    default_breaker_a: int = Field(..., description="Default breaker rating in Amps")
    max_load_w: float = Field(..., description="Maximum load for this circuit type")
    max_outlets: int = Field(..., description="Maximum outlets per circuit")
    
    # Wire defaults
    default_wire_size_mm2: float = Field(..., description="Default wire size in mm²")
    wire_type: str = Field(default="THW", description="Wire insulation type")


class CableSpec(BaseModel):
    """Cable specification from catalog.
    
    Maps to amadeus.catalog.cable_specs view.
    """

    spec_id: str = Field(..., description="Unique specification identifier")
    size_mm2: float = Field(..., description="Cross-sectional area in mm²")
    
    # Ampacity ratings
    ampacity_in_conduit_a: float = Field(..., description="Ampacity when in conduit")
    ampacity_free_air_a: float = Field(..., description="Ampacity in free air")
    
    # Electrical properties
    resistance_ohm_per_km: float = Field(..., description="DC resistance in Ω/km")
    reactance_ohm_per_km: float = Field(default=0.08, description="AC reactance in Ω/km")
    
    # Physical properties
    insulation_type: str = Field(default="THW", description="Insulation type")
    outer_diameter_mm: float = Field(..., description="Overall diameter in mm")
    max_temperature_c: int = Field(default=75, description="Max operating temperature")
    
    # Standards
    standard_reference: str = Field(default="IEC 60227", description="Standard reference")


class BreakerSpec(BaseModel):
    """Circuit breaker specification from catalog.
    
    Maps to amadeus.catalog.breaker_specs view.
    """

    spec_id: str = Field(..., description="Unique specification identifier")
    rating_a: int = Field(..., description="Current rating in Amps")
    
    # Breaking capacity
    breaking_capacity_ka: float = Field(..., description="Breaking capacity in kA")
    
    # Type and characteristics
    breaker_type: str = Field(default="MCB", description="Breaker type")
    trip_curve: str = Field(default="C", description="Trip curve characteristic")
    poles: int = Field(default=1, description="Number of poles")
    
    # Physical
    width_modules: int = Field(default=1, description="DIN rail width in modules")
    
    # Coordination
    min_wire_size_mm2: float = Field(..., description="Minimum wire size")
    max_wire_size_mm2: float = Field(..., description="Maximum wire size")


class ConduitSpec(BaseModel):
    """Conduit specification from catalog.
    
    Maps to amadeus.catalog.conduit_specs view.
    """

    spec_id: str = Field(..., description="Unique specification identifier")
    nominal_size_mm: int = Field(..., description="Nominal size in mm")
    
    # Internal dimensions
    inner_diameter_mm: float = Field(..., description="Inner diameter in mm")
    
    # Capacity
    max_fill_percent: float = Field(default=40.0, description="Max fill percentage")
    usable_area_mm2: float = Field(..., description="Usable cross-sectional area")
    
    # Type
    conduit_type: str = Field(default="EMT", description="Conduit type")
    material: str = Field(default="steel", description="Material")
    
    # Standards
    standard_reference: str = Field(default="ANSI C80.3", description="Standard reference")


class ApplianceSpec(BaseModel):
    """Standard appliance specification from catalog.
    
    Maps to amadeus.catalog.appliance_specs view.
    """

    spec_id: str = Field(..., description="Unique specification identifier")
    name: str = Field(..., description="Appliance name")
    category: str = Field(..., description="Appliance category")
    
    # Electrical
    typical_watts: float = Field(..., description="Typical power consumption")
    max_watts: float = Field(..., description="Maximum power consumption")
    power_factor: float = Field(default=0.85, description="Typical power factor")
    
    # Requirements
    requires_dedicated_circuit: bool = Field(default=False, description="Needs dedicated circuit")
    recommended_breaker_a: Optional[int] = Field(default=None, description="Recommended breaker")
    
    # Common rooms
    typical_rooms: List[str] = Field(default_factory=list, description="Rooms where typically found")
