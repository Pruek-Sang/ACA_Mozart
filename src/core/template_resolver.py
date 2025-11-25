"""Template resolver for transforming ProjectInputSpec to BaselineContext."""

import math
from typing import Optional

from src.dal.catalog_dal import (
    CatalogDAL,
    DEFAULT_ROOM_TEMPLATES,
)
from src.models.baseline import BaselineCircuit, BaselineContext, BaselineRoom
from src.models.catalog_models import RoomTemplate
from src.models.contracts import ProjectInputSpec, RoomInputSpec


class TemplateResolver:
    """Resolves project input specs into baseline calculation context."""

    def __init__(self, dal: Optional[CatalogDAL] = None):
        """Initialize with optional DAL instance.
        
        Args:
            dal: CatalogDAL instance. If None, will use defaults.
        """
        self.dal = dal
        self._templates_cache: Optional[dict[str, RoomTemplate]] = None

    def _get_template(self, room_type: str) -> RoomTemplate:
        """Get room template by type, falling back to defaults.
        
        Args:
            room_type: The type of room.
            
        Returns:
            RoomTemplate for the room type.
        """
        room_type_lower = room_type.lower()

        # Try database first if DAL is available
        if self.dal is not None:
            template = self.dal.get_room_template(room_type_lower)
            if template is not None:
                return template

        # Fall back to defaults
        if room_type_lower in DEFAULT_ROOM_TEMPLATES:
            return DEFAULT_ROOM_TEMPLATES[room_type_lower]

        # Generic fallback template
        return RoomTemplate(
            room_type=room_type_lower,
            description=f"Generic {room_type}",
            lighting_load_w_sqm=15.0,
            outlet_load_w=180.0,
            outlet_count_per_sqm=0.1,
            lighting_demand_factor=1.0,
            outlet_demand_factor=0.5,
        )

    def _create_circuits_for_room(
        self,
        room: RoomInputSpec,
        template: RoomTemplate,
        voltage: float,
        power_factor: float,
    ) -> list[BaselineCircuit]:
        """Create baseline circuits for a room based on template.
        
        Args:
            room: Room input specification.
            template: Room template with load definitions.
            voltage: Nominal voltage.
            power_factor: Power factor.
            
        Returns:
            List of BaselineCircuit for the room.
        """
        circuits: list[BaselineCircuit] = []
        circuit_counter = 1

        # Lighting circuit
        lighting_load = template.lighting_load_w_sqm * room.area_sqm
        if lighting_load > 0:
            circuits.append(
                BaselineCircuit(
                    circuit_id=f"{room.room_id}_C{circuit_counter:02d}",
                    room_id=room.room_id,
                    circuit_type="lighting",
                    connected_load_w=lighting_load,
                    demand_factor=template.lighting_demand_factor,
                    voltage_v=voltage,
                    power_factor=power_factor,
                    cable_length_m=10.0 + room.floor_level * 3.0,
                )
            )
            circuit_counter += 1

        # Outlet circuit(s)
        num_outlets = max(1, math.ceil(template.outlet_count_per_sqm * room.area_sqm))
        outlet_load = template.outlet_load_w * num_outlets
        if outlet_load > 0:
            circuits.append(
                BaselineCircuit(
                    circuit_id=f"{room.room_id}_C{circuit_counter:02d}",
                    room_id=room.room_id,
                    circuit_type="outlet",
                    connected_load_w=outlet_load,
                    demand_factor=template.outlet_demand_factor,
                    voltage_v=voltage,
                    power_factor=power_factor,
                    cable_length_m=12.0 + room.floor_level * 3.0,
                )
            )
            circuit_counter += 1

        # AC circuit if applicable
        if template.has_ac_circuit and template.ac_load_w > 0:
            circuits.append(
                BaselineCircuit(
                    circuit_id=f"{room.room_id}_C{circuit_counter:02d}",
                    room_id=room.room_id,
                    circuit_type="ac",
                    connected_load_w=template.ac_load_w,
                    demand_factor=template.ac_demand_factor,
                    voltage_v=voltage,
                    power_factor=0.85,  # AC typically has different PF
                    cable_length_m=8.0 + room.floor_level * 3.0,
                )
            )
            circuit_counter += 1

        # Special outlet circuit if applicable
        if template.has_special_outlet and template.special_outlet_load_w > 0:
            circuits.append(
                BaselineCircuit(
                    circuit_id=f"{room.room_id}_C{circuit_counter:02d}",
                    room_id=room.room_id,
                    circuit_type="special_outlet",
                    connected_load_w=template.special_outlet_load_w,
                    demand_factor=1.0,  # Special outlets at full demand
                    voltage_v=voltage,
                    power_factor=power_factor,
                    cable_length_m=10.0 + room.floor_level * 3.0,
                )
            )
            circuit_counter += 1

        # Custom loads if specified
        if room.custom_loads:
            for custom_load in room.custom_loads:
                load_type = custom_load.get("type", "custom")
                load_w = custom_load.get("load_w", 0.0)
                demand_factor = custom_load.get("demand_factor", 1.0)
                if load_w > 0:
                    circuits.append(
                        BaselineCircuit(
                            circuit_id=f"{room.room_id}_C{circuit_counter:02d}",
                            room_id=room.room_id,
                            circuit_type=load_type,
                            connected_load_w=load_w,
                            demand_factor=demand_factor,
                            voltage_v=voltage,
                            power_factor=power_factor,
                            cable_length_m=custom_load.get("cable_length_m", 15.0),
                        )
                    )
                    circuit_counter += 1

        return circuits

    def resolve(self, project_input: ProjectInputSpec) -> BaselineContext:
        """Transform ProjectInputSpec into BaselineContext.
        
        Args:
            project_input: Input specification for the project.
            
        Returns:
            BaselineContext ready for calculations.
        """
        # Parse voltage from system string
        voltage_str = project_input.voltage_system.replace("V", "").replace("v", "")
        try:
            nominal_voltage = float(voltage_str)
        except ValueError:
            nominal_voltage = 230.0

        # Create baseline context
        context = BaselineContext(
            project_id=project_input.project_id,
            project_name=project_input.project_name,
            voltage_system=project_input.voltage_system,
            phase_system=project_input.phase_system,
            nominal_voltage=nominal_voltage,
            power_factor=project_input.power_factor,
            ambient_temp_c=project_input.ambient_temp_c,
        )

        # Process each room
        baseline_rooms: list[BaselineRoom] = []
        for room_input in project_input.rooms:
            template = self._get_template(room_input.room_type)

            # Create circuits for this room
            circuits = self._create_circuits_for_room(
                room=room_input,
                template=template,
                voltage=nominal_voltage,
                power_factor=project_input.power_factor,
            )

            # Create baseline room
            baseline_room = BaselineRoom(
                room_id=room_input.room_id,
                room_type=room_input.room_type,
                area_sqm=room_input.area_sqm,
                floor_level=room_input.floor_level,
                circuits=circuits,
                custom_loads=room_input.custom_loads,
            )

            baseline_rooms.append(baseline_room)

        context.rooms = baseline_rooms
        return context
