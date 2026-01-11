"""
MCP Adapter - Bridge between RAG and MCP Core

Philosophy:
- RAG produces human-friendly specs (device codes, Thai voltage names)
- MCP consumes calculation-ready specs (watts, NEC voltage types)
- This adapter is the ONLY place where conversion happens

Golden Rule: If mapping fails, use safe defaults and LOG it
"""

import logging
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.models import ProjectInputSpec, LoadSpec, RoomSpec, SiteContext

logger = logging.getLogger("Aura.McpAdapter")


# =============================================================================
# MCP Contract Types (mirrors mcp_core_v2/models/contracts.py)
# =============================================================================

class VoltageType(str, Enum):
    """MCP voltage types (NEC standard)"""
    SINGLE_PHASE_120V = "120V_1PH"
    SINGLE_PHASE_240V = "240V_1PH"
    THREE_PHASE_208V = "208V_3PH"
    THREE_PHASE_480V = "480V_3PH"


class LoadType(str, Enum):
    """MCP load types"""
    LIGHTING = "lighting"
    RECEPTACLE = "receptacle"
    HVAC = "hvac"
    MOTOR = "motor"
    APPLIANCE = "appliance"
    OTHER = "other"


@dataclass
class McpLocation:
    """Location for MCP"""
    room: str
    floor: Optional[str] = None


@dataclass
class McpElectricalLoad:
    """Electrical load for MCP Core"""
    id: str
    name: str
    load_type: LoadType
    voltage: VoltageType
    power_watts: float
    quantity: int = 1
    location: Optional[McpLocation] = field(default=None)
    is_continuous: bool = False
    notes: Optional[str] = None
    branch_distance_m: Optional[float] = None  # 🆕 VD Calculation
    power_factor: Optional[float] = None  # 🆕 PF by load type (1.0=resistive, 0.85=motor)
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "load_type": self.load_type.value,
            "voltage": self.voltage.value,
            "power_watts": self.power_watts,
            "quantity": self.quantity,
            "location": {
                "room": self.location.room if self.location else "Unknown",
                "floor": self.location.floor if self.location else None
            },
            "is_continuous": self.is_continuous,
            "notes": self.notes,
            "branch_distance_m": self.branch_distance_m,
            "power_factor": self.power_factor  # 🆕 Include PF in API request
        }


@dataclass
class McpPanelSpec:
    """Panel specification for MCP"""
    id: str
    name: str
    voltage: VoltageType
    main_breaker_rating: int
    number_of_circuits: int
    location: McpLocation
    feeds: List[str]  # Load IDs
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "voltage": self.voltage.value,
            "main_breaker_rating": self.main_breaker_rating,
            "number_of_circuits": self.number_of_circuits,
            "location": {
                "room": self.location.room,
                "floor": self.location.floor
            },
            "feeds": self.feeds
        }


@dataclass
class McpDesignRequest:
    """Design request for MCP Core"""
    session_id: str
    project_name: str
    loads: List[McpElectricalLoad]
    panels: List[McpPanelSpec]
    service_voltage: VoltageType
    utility_service_size: int = 100  # Default 100A service
    project_number: Optional[str] = None
    site_context: Optional[Dict] = None  # 🆕 Site context for Injectors
    building_type: Optional[str] = None  # 🆕 For Default Distance Lookup
    service_distance_m: Optional[float] = None  # 🆕 Service VD
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization"""
        result = {
            "session_id": self.session_id,
            "project_name": self.project_name,
            "project_number": self.project_number,
            "loads": [load.to_dict() for load in self.loads],
            "panels": [panel.to_dict() for panel in self.panels],
            "service_voltage": self.service_voltage.value,
            "utility_service_size": self.utility_service_size,
            "building_type": self.building_type,
            "service_distance_m": self.service_distance_m
        }
        # 🆕 Include site_context if present
        if self.site_context:
            result["site_context"] = self.site_context
        return result


# =============================================================================
# Device Code Mapping (from DEVICE_CODES.md)
# =============================================================================

# Format: device_code -> (power_watts, load_type, is_continuous)
DEVICE_MAPPING: Dict[str, Tuple[float, LoadType, bool]] = {
    # Air Conditioners (HVAC, continuous)
    "AC-9000BTU": (900, LoadType.HVAC, True),
    "AC-12000BTU": (1200, LoadType.HVAC, True),
    "AC-18000BTU": (1800, LoadType.HVAC, True),
    "AC-24000BTU": (2400, LoadType.HVAC, True),
    
    # Outlets (Receptacle, non-continuous, NEC 180VA per outlet)
    "SOCKET-16A": (180, LoadType.RECEPTACLE, False),
    "SOCKET-20A": (180, LoadType.RECEPTACLE, False),
    "SOCKET-OUTLET": (180, LoadType.RECEPTACLE, False),  # Generic outlet
    "OUTLET-16A": (180, LoadType.RECEPTACLE, False),     # Alternative name
    
    # Kitchen Appliances (Appliance, non-continuous)
    "INDUCTION-3000W": (3000, LoadType.APPLIANCE, False),
    "IND-3000W": (3000, LoadType.APPLIANCE, False),  # 🆕 Alias for INDUCTION
    "MICROWAVE-1500W": (1500, LoadType.APPLIANCE, False),
    "RICECOOK-800W": (800, LoadType.APPLIANCE, False),
    "REFRIG-300W": (300, LoadType.APPLIANCE, True),  # Refrigerator runs continuously
    "DISHWASH-2000W": (2000, LoadType.APPLIANCE, False),
    
    # Water Heaters (Appliance, CONTINUOUS per NEC - requires 125% sizing)
    "HEATER-3500W": (3500, LoadType.APPLIANCE, True),   # Fixed: was False
    "HEATER-4500W": (4500, LoadType.APPLIANCE, True),   # Fixed: was False
    "WATER-HEATER-3500W": (3500, LoadType.APPLIANCE, True),  # Fixed: was False
    
    # Lighting (Lighting, continuous by NEC)
    "LIGHT-LED-10W": (10, LoadType.LIGHTING, True),
    "LIGHT-LED-20W": (20, LoadType.LIGHTING, True),
    "LIGHT-FLUOR-40W": (40, LoadType.LIGHTING, True),
    "LIGHTING-LED-10W": (10, LoadType.LIGHTING, True),  # Alternative format
    "LIGHTING-LED-20W": (20, LoadType.LIGHTING, True),  # Alternative format
    "LIGHTING-FLUOR-40W": (40, LoadType.LIGHTING, True),
    
    # Fans (Other, non-continuous)
    "FAN-CEILING-60W": (60, LoadType.OTHER, False),
    "FAN-STAND-50W": (50, LoadType.OTHER, False),
    
    # Switches (Other, negligible power - control devices)
    "SWITCH-1WAY": (0, LoadType.OTHER, False),
    "SWITCH-2WAY": (0, LoadType.OTHER, False),
    "SWITCH-3WAY": (0, LoadType.OTHER, False),
    "SW-1WAY": (0, LoadType.OTHER, False),
    "SW-2WAY": (0, LoadType.OTHER, False),
    "COMP-SW-1WAY": (0, LoadType.OTHER, False),  # Catalog format
    "COMP-SW-2WAY": (0, LoadType.OTHER, False),  # Catalog format
    "DIMMER": (5, LoadType.OTHER, False),        # Dimmer has small standby
    "COMP-DIMMER": (5, LoadType.OTHER, False),   # Catalog format
    
    # Miscellaneous
    "TV-200W": (200, LoadType.RECEPTACLE, False),
    "COMPUTER-300W": (300, LoadType.RECEPTACLE, False),
    "WASHER-2000W": (2000, LoadType.APPLIANCE, False),
    "DRYER-3000W": (3000, LoadType.APPLIANCE, False),
    
    # Pumps (Motor type)
    "PUMP-750W": (750, LoadType.MOTOR, False),
    "PUMP-1500W": (1500, LoadType.MOTOR, False),
    
    # EV Chargers (Appliance, continuous - requires 125% sizing)
    "EV-CHARGER-7KW": (7000, LoadType.APPLIANCE, True),   # Level 2 home charger
    "EV-CHARGER-22KW": (22000, LoadType.APPLIANCE, True), # Level 2 fast charger
    
    # Additional Kitchen Appliances
    "KETTLE-2200W": (2200, LoadType.APPLIANCE, False),    # กาต้มน้ำ
    "KETTLE-1800W": (1800, LoadType.APPLIANCE, False),
    
    # Exhaust Fans
    "FAN-EXHAUST-25W": (25, LoadType.OTHER, False),       # พัดลมดูดอากาศ
    "FAN-EXHAUST-50W": (50, LoadType.OTHER, False),
}


# Default for unknown devices
DEFAULT_DEVICE = (500, LoadType.OTHER, False)


# =============================================================================
# Voltage Mapping (Thai system -> NEC)
# =============================================================================

VOLTAGE_MAPPING: Dict[str, VoltageType] = {
    # Thai residential (230V nominal treated as 240V for NEC calculations)
    "TH_1PH_230V": VoltageType.SINGLE_PHASE_240V,
    "TH_1PH_220V": VoltageType.SINGLE_PHASE_240V,
    
    # Thai 3-phase
    "TH_3PH_380V": VoltageType.THREE_PHASE_208V,  # Closest NEC equivalent
    "TH_3PH_400V": VoltageType.THREE_PHASE_208V,
}

DEFAULT_VOLTAGE = VoltageType.SINGLE_PHASE_240V


# =============================================================================
# Main Adapter Class
# =============================================================================

class McpAdapter:
    """
    Converts RAG ProjectInputSpec to MCP DesignRequest
    
    Usage:
        adapter = McpAdapter()
        mcp_request = adapter.convert(rag_spec, site_context)
        response = mcp_client.design(mcp_request)
    """
    
    def __init__(self):
        self.unknown_devices: List[str] = []  # Track unknown devices for logging
    
    def convert(
        self, 
        spec: ProjectInputSpec, 
        site_context: Optional[SiteContext] = None,
        floor_distances: Optional[Dict[str, float]] = None
    ) -> McpDesignRequest:
        """
        Main conversion: RAG spec -> MCP request
        
        Args:
            spec: ProjectInputSpec from RAG service
            site_context: Optional site context for safety calculations
            floor_distances: Optional default distances per floor (for VD calc)
            
        Returns:
            McpDesignRequest ready for MCP Core
        """
        self.unknown_devices = []  # Reset
        
        # 1. Map voltage
        service_voltage = self._map_voltage(spec.electrical_system.voltage_system)
        
        # 2. Build room lookup (room_id -> RoomSpec)
        room_lookup = {room.room_id: room for room in spec.rooms}
        
        # 3. Convert loads (with floor defaults!)
        mcp_loads = self._convert_loads(spec.loads, room_lookup, service_voltage, floor_distances)
        
        # 4. Create default panel (MCP requires at least one)
        panel = self._create_default_panel(
            mcp_loads, 
            service_voltage,
            spec.project_info.project_name
        )
        
        # 5. Log any issues
        if self.unknown_devices:
            logger.warning(f"Unknown device codes (using defaults): {self.unknown_devices}")
        
        # 6. Convert site_context to dict (for MCP)
        site_context_dict = None
        if site_context:
            site_context_dict = site_context.model_dump()
        
        # 7. Build request
        return McpDesignRequest(
            session_id=f"rag_{uuid.uuid4().hex[:12]}",
            project_name=spec.project_info.project_name,
            project_number=None,
            loads=mcp_loads,
            panels=[panel],
            service_voltage=service_voltage,
            utility_service_size=self._estimate_service_size(mcp_loads),
            site_context=site_context_dict,  # 🆕 Pass site_context to MCP
            building_type=spec.project_info.building_type,
            service_distance_m=getattr(spec.project_info, 'service_distance_m', None) # Note: project_info might need update or pass separate
        )
    
    def _map_voltage(self, voltage_system: str) -> VoltageType:
        """Map Thai voltage system to NEC VoltageType"""
        voltage = VOLTAGE_MAPPING.get(voltage_system)
        if voltage is None:
            logger.warning(f"Unknown voltage system '{voltage_system}', using default 240V")
            return DEFAULT_VOLTAGE
        return voltage
    
    def _convert_loads(
        self, 
        loads: List[LoadSpec], 
        room_lookup: Dict[str, RoomSpec],
        service_voltage: VoltageType,
        floor_distances: Optional[Dict[str, float]] = None
    ) -> List[McpElectricalLoad]:
        """Convert RAG LoadSpecs to MCP ElectricalLoads"""
        mcp_loads = []
        floor_map = floor_distances or {}
        
        # Power Factor by load type (IEC 60364 / วสท. 2564)
        PF_BY_LOAD_TYPE = {
            LoadType.APPLIANCE: 1.0,   # Resistive (heaters, kettles, induction)
            LoadType.LIGHTING: 0.90,   # LED drivers
            LoadType.HVAC: 0.85,       # Compressor motors
            LoadType.MOTOR: 0.80,      # Motor loads
            LoadType.RECEPTACLE: 0.85, # Mixed loads
            LoadType.OTHER: 0.85,      # Default
        }
        
        for load in loads:
            # Look up device
            device_info = DEVICE_MAPPING.get(load.device_code)
            if device_info is None:
                self.unknown_devices.append(load.device_code)
                device_info = DEFAULT_DEVICE
            
            power_watts, load_type, is_continuous = device_info
            
            # Get power factor by load type
            power_factor = PF_BY_LOAD_TYPE.get(load_type, 0.85)
            
            # Get room info
            room = room_lookup.get(load.room_id)
            room_name = room.name if room else "Unknown Room"
            
            # Get floor from LoadSpec (new: floor support)
            floor = str(getattr(load, 'floor', 1)) if hasattr(load, 'floor') else "1"
            
            # Resolve Branch Distance: Specific > Floor Default > None (for tracking)
            # NOTE: Do NOT add final fallback here - let MCP Core track defaults properly
            dist = getattr(load, 'branch_distance_m', None)
            if dist is None or dist == 0:
                # Try to find from floor_map (user-specified floor distances)
                # Handle string/int key differences (JSON keys are strings)
                default_dist = floor_map.get(str(floor)) or floor_map.get(int(floor) if floor.isdigit() else floor)
                if default_dist:
                    dist = float(default_dist)
                # If still None, MCP Core will use default_table and track it
            
            # Create MCP load
            mcp_load = McpElectricalLoad(
                id=load.load_id,
                name=f"{load.device_code} in {room_name}",
                load_type=load_type,
                voltage=service_voltage,  # Inherit from service
                power_watts=power_watts,
                quantity=load.qty,
                location=McpLocation(room=room_name, floor=floor),
                is_continuous=is_continuous,
                notes=load.notes,
                branch_distance_m=dist,
                power_factor=power_factor  # 🆕 Correct PF by load type
            )
            mcp_loads.append(mcp_load)
        
        return mcp_loads
    
    def _create_default_panel(
        self, 
        loads: List[McpElectricalLoad],
        voltage: VoltageType,
        project_name: str
    ) -> McpPanelSpec:
        """Create a default main panel"""
        load_ids = [load.id for load in loads]
        
        # Estimate circuits needed (1 per load + 20% spare)
        num_circuits = max(12, int(len(loads) * 1.2))
        
        # Round up to standard panel sizes
        if num_circuits <= 12:
            num_circuits = 12
        elif num_circuits <= 20:
            num_circuits = 20
        elif num_circuits <= 30:
            num_circuits = 30
        else:
            num_circuits = 42
        
        # Estimate main breaker from total load
        total_va = sum(load.power_watts * load.quantity for load in loads)
        
        # Convert to amps based on voltage system
        # Thai standard: 230V single-phase, 400V three-phase
        if voltage in [VoltageType.THREE_PHASE_208V, VoltageType.THREE_PHASE_480V]:
            amps = total_va / (400 * 1.732)  # 3-phase (Thai 400V)
        elif voltage in [VoltageType.SINGLE_PHASE_240V]:
            amps = total_va / 240  # US 240V or Thai 230V
        else:
            amps = total_va / 230  # Thai standard 230V
        
        # Add 25% safety margin for continuous load (NEC 215.3 / วสท.)
        amps_with_margin = amps * 1.25
        
        # Round up to standard breaker sizes
        standard_sizes = [60, 100, 125, 150, 200, 400]
        main_breaker = next(
            (size for size in standard_sizes if size >= amps_with_margin),
            200  # Default to 200A
        )
        
        return McpPanelSpec(
            id="panel_main",
            name=f"Main Panel - {project_name[:20]}",
            voltage=voltage,
            main_breaker_rating=main_breaker,
            number_of_circuits=num_circuits,
            location=McpLocation(room="Electrical Room", floor="1"),
            feeds=load_ids
        )
    
    def _estimate_service_size(self, loads: List[McpElectricalLoad]) -> int:
        """Estimate utility service size based on loads"""
        # Simple calculation: sum of all loads with demand factor
        total_va = sum(load.power_watts * load.quantity for load in loads)
        
        # Apply rough demand factor (0.7 for residential)
        demand_va = total_va * 0.7
        
        # Convert to amps at 240V
        amps = demand_va / 240
        
        # Round up to standard sizes
        standard_sizes = [100, 150, 200, 400]
        return next(
            (size for size in standard_sizes if size >= amps * 1.25),
            200  # Default
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def convert_to_mcp(spec: ProjectInputSpec) -> McpDesignRequest:
    """
    Convenience function for one-off conversion
    
    Usage:
        from app.mcp_adapter import convert_to_mcp
        mcp_request = convert_to_mcp(rag_spec)
    """
    adapter = McpAdapter()
    return adapter.convert(spec)


def get_device_info(device_code: str) -> Tuple[float, str, bool]:
    """
    Get device info by code (for debugging/validation)
    
    Returns: (power_watts, load_type, is_continuous)
    """
    info = DEVICE_MAPPING.get(device_code)
    if info:
        return (info[0], info[1].value, info[2])
    return (DEFAULT_DEVICE[0], DEFAULT_DEVICE[1].value, DEFAULT_DEVICE[2])


def list_known_devices() -> List[str]:
    """List all known device codes"""
    return list(DEVICE_MAPPING.keys())
