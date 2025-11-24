"""
MCP Core v2 Result Builder
Assembles final design output from pipeline components.
"""

from typing import List, Dict, Any, Optional
from models.contracts import (
    RoomInput,
    RoomDesign,
    ProjectInput,
    ProjectDesign,
    OutletPlacement,
    LightPlacement,
    SwitchPlacement,
    CircuitSpec,
    ComplianceResult,
    OutletType,
    LightType,
)


class ResultBuilder:
    """
    Builds final design results from component outputs.
    Assembles room and project designs with all specifications.
    """
    
    def __init__(self):
        self.circuit_counter = 0
        self.outlet_counter = 0
        self.light_counter = 0
        self.switch_counter = 0
    
    def _next_circuit_id(self, room_id: str, circuit_type: str) -> str:
        """Generate next circuit ID."""
        self.circuit_counter += 1
        prefix = {"lighting": "L", "outlet": "O", "dedicated": "D"}.get(circuit_type, "C")
        return f"{room_id}-{prefix}{self.circuit_counter}"
    
    def _next_outlet_id(self, room_id: str) -> str:
        """Generate next outlet ID."""
        self.outlet_counter += 1
        return f"{room_id}-OUT{self.outlet_counter}"
    
    def _next_light_id(self, room_id: str) -> str:
        """Generate next light ID."""
        self.light_counter += 1
        return f"{room_id}-LT{self.light_counter}"
    
    def _next_switch_id(self, room_id: str) -> str:
        """Generate next switch ID."""
        self.switch_counter += 1
        return f"{room_id}-SW{self.switch_counter}"
    
    def build_outlet(
        self,
        room_id: str,
        x: float,
        y: float,
        outlet_type: OutletType,
        circuit_id: str,
        height: float = 0.3
    ) -> OutletPlacement:
        """Build outlet placement."""
        return OutletPlacement(
            outlet_id=self._next_outlet_id(room_id),
            outlet_type=outlet_type,
            x=x,
            y=y,
            height=height,
            circuit_id=circuit_id,
        )
    
    def build_light(
        self,
        room_id: str,
        x: float,
        y: float,
        wattage: float,
        light_type: LightType,
        circuit_id: str
    ) -> LightPlacement:
        """Build light placement."""
        return LightPlacement(
            light_id=self._next_light_id(room_id),
            light_type=light_type,
            x=x,
            y=y,
            wattage=wattage,
            circuit_id=circuit_id,
        )
    
    def build_switch(
        self,
        room_id: str,
        x: float,
        y: float,
        controls: List[str],
        height: float = 1.2
    ) -> SwitchPlacement:
        """Build switch placement."""
        return SwitchPlacement(
            switch_id=self._next_switch_id(room_id),
            x=x,
            y=y,
            height=height,
            controls=controls,
        )
    
    def build_circuit(
        self,
        room_id: str,
        circuit_type: str,
        breaker_size: int,
        wire_size: float,
        conduit_size: float,
        total_load: float,
        connected_devices: List[str]
    ) -> CircuitSpec:
        """Build circuit specification."""
        return CircuitSpec(
            circuit_id=self._next_circuit_id(room_id, circuit_type),
            circuit_type=circuit_type,
            breaker_size=breaker_size,
            wire_size=wire_size,
            conduit_size=conduit_size,
            total_load=total_load,
            connected_devices=connected_devices,
        )
    
    def build_room_design(
        self,
        room: RoomInput,
        outlets: List[OutletPlacement],
        lights: List[LightPlacement],
        switches: List[SwitchPlacement],
        circuits: List[CircuitSpec],
        compliance_notes: List[str] = None
    ) -> RoomDesign:
        """
        Build complete room design.
        
        Args:
            room: Room input specification
            outlets: Outlet placements
            lights: Light placements
            switches: Switch placements
            circuits: Circuit specifications
            compliance_notes: Any compliance notes
            
        Returns:
            Complete room design
        """
        total_load = sum(c.total_load for c in circuits)
        
        return RoomDesign(
            room_id=room.room_id,
            room_type=room.room_type,
            area=room.width * room.length,
            outlets=outlets,
            lights=lights,
            switches=switches,
            circuits=circuits,
            total_load_watts=total_load,
            compliance_notes=compliance_notes or [],
        )
    
    def build_project_design(
        self,
        project: ProjectInput,
        rooms: List[RoomDesign],
        main_breaker_size: int,
        total_connected_load: float,
        total_demand_load: float,
        compliance: ComplianceResult,
        autolisp_script: str = "",
        metadata: Dict[str, Any] = None
    ) -> ProjectDesign:
        """
        Build complete project design.
        
        Args:
            project: Project input
            rooms: Room designs
            main_breaker_size: Main breaker size
            total_connected_load: Total connected load
            total_demand_load: Total demand load
            compliance: Compliance result
            autolisp_script: Generated AutoLISP script
            metadata: Additional metadata
            
        Returns:
            Complete project design
        """
        return ProjectDesign(
            project_id=project.project_id,
            project_name=project.project_name,
            rooms=rooms,
            main_breaker_size=main_breaker_size,
            total_connected_load=total_connected_load,
            total_demand_load=total_demand_load,
            compliance=compliance,
            autolisp_script=autolisp_script,
            metadata=metadata or {},
        )
    
    def reset_counters(self) -> None:
        """Reset all ID counters."""
        self.circuit_counter = 0
        self.outlet_counter = 0
        self.light_counter = 0
        self.switch_counter = 0
    
    def build_from_template_output(
        self,
        room: RoomInput,
        outlet_positions: List[tuple],
        light_positions: List[tuple],
        outlet_type: OutletType,
        light_type: LightType,
        light_wattage: float,
        wire_size: float,
        conduit_size: float,
        breaker_size: int,
    ) -> RoomDesign:
        """
        Build room design from template resolver output.
        
        Args:
            room: Room input
            outlet_positions: List of (x, y) outlet positions
            light_positions: List of (x, y) light positions
            outlet_type: Type of outlets
            light_type: Type of lights
            light_wattage: Wattage per light
            wire_size: Wire size in mm²
            conduit_size: Conduit size in mm
            breaker_size: Breaker size in amps
            
        Returns:
            Complete room design
        """
        # Reset counters for new room
        self.reset_counters()
        
        # Create circuits first
        outlet_circuit = self.build_circuit(
            room.room_id,
            "outlet",
            breaker_size,
            wire_size,
            conduit_size,
            len(outlet_positions) * 180,  # 180W per outlet
            [],  # Will be filled below
        )
        
        lighting_circuit = self.build_circuit(
            room.room_id,
            "lighting",
            16,  # Standard lighting circuit
            1.5,  # Standard lighting wire
            16,   # Standard conduit
            len(light_positions) * light_wattage,
            [],
        )
        
        # Create outlets
        outlets = []
        for x, y in outlet_positions:
            outlet = self.build_outlet(
                room.room_id, x, y, outlet_type, outlet_circuit.circuit_id
            )
            outlets.append(outlet)
            outlet_circuit.connected_devices.append(outlet.outlet_id)
        
        # Create lights
        lights = []
        for x, y in light_positions:
            light = self.build_light(
                room.room_id, x, y, light_wattage, light_type, lighting_circuit.circuit_id
            )
            lights.append(light)
            lighting_circuit.connected_devices.append(light.light_id)
        
        # Create switch near door (assumed at 0,0)
        light_ids = [l.light_id for l in lights]
        switch = self.build_switch(room.room_id, 0.15, 0.5, light_ids)
        switches = [switch]
        
        return self.build_room_design(
            room,
            outlets,
            lights,
            switches,
            [outlet_circuit, lighting_circuit],
        )
