"""Catalog models for electrical components."""

from typing import Optional, Dict, List
from pydantic import BaseModel
from enum import Enum


class BreakerType(str, Enum):
    """Circuit breaker types."""
    STANDARD = "standard"
    GFCI = "gfci"
    AFCI = "afci"
    DUAL_FUNCTION = "dual_function"  # AFCI+GFCI
    RCBO = "rcbo"  # Residual Current Breaker with Overcurrent (Thai: เซอร์กิตเบรกเกอร์ป้องกันไฟรั่ว)
    MAIN = "main"


class BreakerPoles(str, Enum):
    """Number of poles for breakers."""
    SINGLE = "1P"
    DOUBLE = "2P"
    THREE = "3P"


class CatalogBreaker(BaseModel):
    """Circuit breaker catalog item."""
    id: str
    manufacturer: str
    model_number: str
    breaker_type: BreakerType
    poles: BreakerPoles
    ampere_rating: int
    voltage_rating: int
    interrupt_rating: int  # AIC
    price: Optional[float] = None
    availability: bool = True
    catalog_page: Optional[str] = None
    notes: Optional[str] = None


class WireInsulation(str, Enum):
    """Wire insulation types."""
    THHN = "THHN"
    THWN = "THWN"
    THWN2 = "THWN-2"
    XHHW = "XHHW"
    XHHW2 = "XHHW-2"
    USE2 = "USE-2"


class ConductorMaterial(str, Enum):
    """Conductor material types."""
    COPPER = "copper"
    ALUMINUM = "aluminum"


class CatalogWire(BaseModel):
    """Wire/conductor catalog item."""
    id: str
    manufacturer: str
    awg_size: str
    material: ConductorMaterial
    insulation_type: WireInsulation
    voltage_rating: int
    temperature_rating: int  # Celsius
    stranding: str  # e.g., "7-strand", "19-strand", "solid"
    price_per_foot: Optional[float] = None
    availability: bool = True
    color_available: List[str] = []
    notes: Optional[str] = None


class ConduitMaterial(str, Enum):
    """Conduit material types."""
    EMT = "EMT"  # Electrical Metallic Tubing
    IMC = "IMC"  # Intermediate Metal Conduit
    RMC = "RMC"  # Rigid Metal Conduit
    PVC = "PVC"  # Polyvinyl Chloride
    LFNC = "LFNC"  # Liquidtight Flexible Nonmetallic Conduit


class CatalogConduit(BaseModel):
    """Conduit catalog item."""
    id: str
    manufacturer: str
    material: ConduitMaterial
    trade_size: str  # e.g., "1/2", "3/4", "1"
    length_feet: int = 10  # Standard length
    price_per_length: Optional[float] = None
    availability: bool = True
    indoor_rated: bool = True
    outdoor_rated: bool = True
    notes: Optional[str] = None


class PanelType(str, Enum):
    """Electrical panel types."""
    LOADCENTER = "loadcenter"
    PANELBOARD = "panelboard"
    SWITCHBOARD = "switchboard"
    MCC = "mcc"  # Motor Control Center


class CatalogPanel(BaseModel):
    """Electrical panel catalog item."""
    id: str
    manufacturer: str
    model_number: str
    panel_type: PanelType
    main_breaker_rating: int
    bus_rating: int
    voltage: int
    phases: int
    number_of_spaces: int
    max_circuits: int
    enclosure_type: str  # e.g., "NEMA 1", "NEMA 3R"
    price: Optional[float] = None
    availability: bool = True
    dimensions: Optional[Dict[str, float]] = None  # height, width, depth in inches
    weight_lbs: Optional[float] = None
    notes: Optional[str] = None


class CatalogDatabase(BaseModel):
    """Complete catalog database."""
    breakers: List[CatalogBreaker] = []
    wires: List[CatalogWire] = []
    conduits: List[CatalogConduit] = []
    panels: List[CatalogPanel] = []
    version: str = "1.0.0"
    last_updated: Optional[str] = None
