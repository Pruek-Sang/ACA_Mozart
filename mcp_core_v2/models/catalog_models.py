"""
MCP Core v2 Catalog Models
Pydantic models matching the amadeus.catalog schema structure.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class WireSpec(BaseModel):
    """Wire specification from catalog."""
    id: UUID
    size_sqmm: float = Field(..., description="Wire size in mm²")
    material: str = "copper"  # copper, aluminum
    insulation: str = "PVC"  # PVC, XLPE, etc.
    max_current_amp: float = Field(..., description="Maximum current rating")
    voltage_rating: int = 450  # Volts
    temperature_rating: int = 70  # Celsius
    price_per_meter: Optional[float] = None
    brand: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class BreakerSpec(BaseModel):
    """Circuit breaker specification from catalog."""
    id: UUID
    rated_current: int = Field(..., description="Rated current in Amperes")
    poles: int = Field(default=1, ge=1, le=4)
    breaking_capacity_ka: float = Field(default=6.0, description="kA rating")
    curve_type: str = "C"  # B, C, D
    brand: Optional[str] = None
    model: Optional[str] = None
    price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ConduitSpec(BaseModel):
    """Conduit specification from catalog."""
    id: UUID
    internal_diameter_mm: float
    external_diameter_mm: float
    material: str = "PVC"  # PVC, EMT, rigid
    color: str = "white"
    price_per_meter: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class OutletSpec(BaseModel):
    """Outlet/receptacle specification from catalog."""
    id: UUID
    outlet_type: str  # standard, grounded, usb, dedicated
    rated_current: int = 16  # Amperes
    rated_voltage: int = 250  # Volts
    num_sockets: int = 1
    grounding: bool = True
    brand: Optional[str] = None
    model: Optional[str] = None
    price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class LightFixtureSpec(BaseModel):
    """Light fixture specification from catalog."""
    id: UUID
    fixture_type: str  # ceiling, downlight, wall, pendant, spot
    wattage: float
    lumens: float
    color_temp_k: int = 4000  # Kelvin
    led: bool = True
    dimmable: bool = False
    ip_rating: str = "IP20"
    brand: Optional[str] = None
    model: Optional[str] = None
    price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class RoomTemplate(BaseModel):
    """Room design template from catalog."""
    id: UUID
    room_type: str
    min_area_sqm: float
    max_area_sqm: float
    outlet_rules: dict  # JSON rules for outlet placement
    lighting_rules: dict  # JSON rules for lighting
    circuit_rules: dict  # JSON rules for circuits
    compliance_standard: str = "EIT"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ComplianceRule(BaseModel):
    """Compliance rule from catalog."""
    id: UUID
    rule_code: str  # e.g., "EIT-4.2.1"
    rule_type: str  # outlet_spacing, wire_sizing, etc.
    description: str
    check_function: str  # Name of check function
    parameters: dict  # Rule parameters
    severity: str = "error"  # error, warning, info
    standard: str = "EIT"
    created_at: datetime = Field(default_factory=datetime.now)


# --- Query Response Models ---

class CatalogQueryResult(BaseModel):
    """Generic query result from catalog."""
    success: bool
    data: Optional[List[dict]] = None
    error: Optional[str] = None
    count: int = 0


class WireQueryResult(BaseModel):
    """Wire query result."""
    success: bool
    wires: List[WireSpec] = []
    error: Optional[str] = None


class BreakerQueryResult(BaseModel):
    """Breaker query result."""
    success: bool
    breakers: List[BreakerSpec] = []
    error: Optional[str] = None


class TemplateQueryResult(BaseModel):
    """Template query result."""
    success: bool
    templates: List[RoomTemplate] = []
    error: Optional[str] = None
