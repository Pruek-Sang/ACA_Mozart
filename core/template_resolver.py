"""Template resolver for MCP Core v2.

Resolves high-level room specifications into detailed baseline contexts
using catalog data from the DAL.
"""

import logging
import uuid
from typing import List

from models.contracts import ProjectInputSpec, RoomSpec
from models.baseline import (
    BaselineContext,
    BaselineRoom,
    BaselineCircuit,
    BaselineLoad,
    CircuitType,
    LoadType,
)
from dal.catalog_dal import CatalogDAL

logger = logging.getLogger(__name__)


class TemplateResolver:
    """Resolves project inputs into detailed baseline contexts."""

    def __init__(self, catalog_dal: CatalogDAL):
        """Initialize resolver with catalog data access.
        
        Args:
            catalog_dal: Data access object for catalog data
        """
        self._catalog = catalog_dal

    def resolve(self, input_spec: ProjectInputSpec) -> BaselineContext:
        """Resolve project input specification to baseline context.
        
        Args:
            input_spec: High-level project specification
            
        Returns:
            Detailed baseline context with circuits and loads
        """
        logger.info(f"Resolving project {input_spec.project_id} with {len(input_spec.rooms)} rooms")
        
        rooms = []
        total_area = 0.0
        total_connected_load = 0.0
        total_circuits = 0
        
        for room_spec in input_spec.rooms:
            baseline_room = self._resolve_room(room_spec, input_spec.voltage)
            rooms.append(baseline_room)
            total_area += baseline_room.area_m2
            
            for circuit in baseline_room.circuits:
                total_connected_load += circuit.total_connected_load_w
                total_circuits += 1
        
        context = BaselineContext(
            project_id=input_spec.project_id,
            project_name=input_spec.project_name,
            voltage=input_spec.voltage,
            frequency=50.0,
            phases=input_spec.phases,
            rooms=rooms,
            total_area_m2=total_area,
            total_connected_load_w=total_connected_load,
            total_circuits=total_circuits,
        )
        
        logger.info(
            f"Resolved {total_circuits} circuits, "
            f"{total_area:.1f}m² area, "
            f"{total_connected_load:.0f}W connected load"
        )
        
        return context

    def _resolve_room(self, room_spec: RoomSpec, voltage: float) -> BaselineRoom:
        """Resolve a single room specification.
        
        Args:
            room_spec: Room specification
            voltage: System voltage
            
        Returns:
            BaselineRoom with circuits and loads
        """
        area = room_spec.width_m * room_spec.length_m
        room_type = room_spec.room_type.value
        
        # Get room template from catalog
        template = self._catalog.get_room_template(room_type)
        
        if not template:
            logger.warning(f"No template for room type {room_type}, using defaults")
            template = self._catalog.get_room_template("bedroom")
        
        circuits = []
        
        # Create lighting circuit
        lighting_circuit = self._create_lighting_circuit(
            room_spec, area, template, voltage
        )
        circuits.append(lighting_circuit)
        
        # Create outlet circuit
        outlet_circuit = self._create_outlet_circuit(
            room_spec, area, template, voltage
        )
        circuits.append(outlet_circuit)
        
        # Create dedicated circuit if required
        if template.requires_dedicated_circuit:
            dedicated_circuit = self._create_dedicated_circuit(
                room_spec, template, voltage
            )
            circuits.append(dedicated_circuit)
        
        # Calculate distance from panel (simple estimate based on room position)
        distance_from_panel = self._estimate_distance_from_panel(room_spec)
        
        return BaselineRoom(
            room_id=f"room-{uuid.uuid4().hex[:8]}",
            name=room_spec.name,
            room_type=room_type,
            width_m=room_spec.width_m,
            length_m=room_spec.length_m,
            height_m=room_spec.height_m,
            area_m2=area,
            circuits=circuits,
            distance_from_panel_m=distance_from_panel,
        )

    def _create_lighting_circuit(
        self,
        room_spec: RoomSpec,
        area: float,
        template,
        voltage: float
    ) -> BaselineCircuit:
        """Create lighting circuit for a room."""
        circuit_template = self._catalog.get_circuit_template("lighting")
        
        # Calculate lighting load based on template
        lighting_watts = area * template.lighting_watts_per_m2
        num_points = max(template.min_lighting_points, int(area / 8))  # 1 point per 8m²
        watts_per_point = lighting_watts / num_points
        
        loads = []
        for i in range(num_points):
            load = BaselineLoad(
                load_id=f"light-{uuid.uuid4().hex[:6]}",
                name=f"Lighting Point {i+1}",
                watts=watts_per_point,
                load_type=LoadType.RESISTIVE,
                power_factor=1.0,
                quantity=1,
                demand_factor=template.diversity_factor,
                x_position_m=room_spec.width_m / 2,
                y_position_m=room_spec.length_m * (i + 1) / (num_points + 1),
            )
            loads.append(load)
        
        total_connected = sum(l.watts * l.quantity for l in loads)
        total_demand = sum(l.watts * l.quantity * l.demand_factor for l in loads)
        
        return BaselineCircuit(
            circuit_id=f"ckt-{uuid.uuid4().hex[:8]}",
            name=f"{room_spec.name}_lighting",
            circuit_type=CircuitType.LIGHTING,
            loads=loads,
            distance_from_panel_m=self._estimate_distance_from_panel(room_spec),
            voltage=voltage,
            total_connected_load_w=total_connected,
            total_demand_load_w=total_demand,
        )

    def _create_outlet_circuit(
        self,
        room_spec: RoomSpec,
        area: float,
        template,
        voltage: float
    ) -> BaselineCircuit:
        """Create outlet circuit for a room."""
        circuit_template = self._catalog.get_circuit_template("outlet")
        
        # Calculate number of outlets
        num_outlets = max(
            template.min_outlets,
            int(area * template.outlets_per_m2)
        )
        
        loads = []
        for i in range(num_outlets):
            load = BaselineLoad(
                load_id=f"outlet-{uuid.uuid4().hex[:6]}",
                name=f"Outlet {i+1}",
                watts=template.outlet_watts_each,
                load_type=LoadType.MIXED,
                power_factor=0.85,
                quantity=1,
                demand_factor=template.diversity_factor,
                x_position_m=(i % 2) * room_spec.width_m + 0.3,
                y_position_m=(i // 2 + 1) * room_spec.length_m / (num_outlets // 2 + 1),
            )
            loads.append(load)
        
        total_connected = sum(l.watts * l.quantity for l in loads)
        total_demand = sum(l.watts * l.quantity * l.demand_factor for l in loads)
        
        return BaselineCircuit(
            circuit_id=f"ckt-{uuid.uuid4().hex[:8]}",
            name=f"{room_spec.name}_outlets",
            circuit_type=CircuitType.OUTLET,
            loads=loads,
            distance_from_panel_m=self._estimate_distance_from_panel(room_spec),
            voltage=voltage,
            total_connected_load_w=total_connected,
            total_demand_load_w=total_demand,
        )

    def _create_dedicated_circuit(
        self,
        room_spec: RoomSpec,
        template,
        voltage: float
    ) -> BaselineCircuit:
        """Create dedicated circuit for a room (e.g., water heater, AC)."""
        load = BaselineLoad(
            load_id=f"dedicated-{uuid.uuid4().hex[:6]}",
            name=template.dedicated_circuit_name or "Dedicated Load",
            watts=template.dedicated_circuit_load_w or 2000.0,
            load_type=LoadType.RESISTIVE,
            power_factor=0.95,
            quantity=1,
            demand_factor=1.0,  # Full demand for dedicated circuits
            x_position_m=room_spec.width_m / 2,
            y_position_m=room_spec.length_m / 2,
        )
        
        return BaselineCircuit(
            circuit_id=f"ckt-{uuid.uuid4().hex[:8]}",
            name=f"{room_spec.name}_{(template.dedicated_circuit_name or 'dedicated').lower().replace(' ', '_')}",
            circuit_type=CircuitType.DEDICATED,
            loads=[load],
            distance_from_panel_m=self._estimate_distance_from_panel(room_spec),
            voltage=voltage,
            total_connected_load_w=load.watts,
            total_demand_load_w=load.watts * load.demand_factor,
        )

    def _estimate_distance_from_panel(self, room_spec: RoomSpec) -> float:
        """Estimate wire run distance from panel to room center.
        
        Simple heuristic: assumes panel is near entry, adds room diagonal.
        """
        # Base distance (panel location assumption)
        base_distance = 5.0
        
        # Add half the room diagonal
        room_diagonal = ((room_spec.width_m ** 2 + room_spec.length_m ** 2) ** 0.5) / 2
        
        return base_distance + room_diagonal
