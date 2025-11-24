"""
MCP Core v2 AutoLISP Generator
Generates AutoLISP scripts for AutoCAD electrical drawing automation.
"""

from typing import List, Dict, Any
from models.contracts import (
    RoomDesign,
    ProjectDesign,
    OutletPlacement,
    LightPlacement,
    SwitchPlacement,
    CircuitSpec,
)


class AutoLISPGenerator:
    """
    Generates AutoLISP scripts for AutoCAD.
    Produces scripts that can be loaded and executed in AutoCAD.
    """
    
    # Block names (should match CAD library)
    OUTLET_BLOCK = "ELEC_OUTLET"
    LIGHT_BLOCK = "ELEC_LIGHT"
    SWITCH_BLOCK = "ELEC_SWITCH"
    PANEL_BLOCK = "ELEC_PANEL"
    
    # Layer names
    LAYER_OUTLETS = "E-POWER"
    LAYER_LIGHTING = "E-LITE"
    LAYER_SWITCH = "E-LITE-SW"
    LAYER_CIRCUIT = "E-CIRC"
    LAYER_ANNOTATION = "E-ANNO"
    
    def __init__(self, scale: float = 1.0):
        """
        Initialize generator.
        
        Args:
            scale: Drawing scale factor
        """
        self.scale = scale
        self.script_lines: List[str] = []
    
    def _add_line(self, line: str) -> None:
        """Add a line to the script."""
        self.script_lines.append(line)
    
    def _add_comment(self, comment: str) -> None:
        """Add a comment to the script."""
        self._add_line(f"; {comment}")
    
    def _setup_layers(self) -> None:
        """Generate layer setup commands."""
        self._add_comment("===== Layer Setup =====")
        
        layers = [
            (self.LAYER_OUTLETS, 1),   # Red
            (self.LAYER_LIGHTING, 2),  # Yellow
            (self.LAYER_SWITCH, 3),    # Green
            (self.LAYER_CIRCUIT, 4),   # Cyan
            (self.LAYER_ANNOTATION, 7), # White
        ]
        
        self._add_line("(defun setup-elec-layers ()")
        for layer, color in layers:
            self._add_line(
                f'  (command "LAYER" "N" "{layer}" "C" {color} "{layer}" "")'
            )
        self._add_line(")")
    
    def _insert_block(
        self,
        block_name: str,
        x: float,
        y: float,
        layer: str,
        rotation: float = 0,
        attributes: Dict[str, str] = None
    ) -> None:
        """Generate block insertion command."""
        x_scaled = x * self.scale
        y_scaled = y * self.scale
        
        self._add_line(
            f'  (command "LAYER" "S" "{layer}" "")'
        )
        self._add_line(
            f'  (command "INSERT" "{block_name}" '
            f'(list {x_scaled:.3f} {y_scaled:.3f} 0) '
            f'1 1 {rotation})'
        )
        
        if attributes:
            for attr, value in attributes.items():
                self._add_line(f'  "{value}"')  # Attribute values in order
    
    def _draw_wire(
        self,
        from_point: tuple,
        to_point: tuple,
        layer: str
    ) -> None:
        """Generate wire drawing command."""
        x1, y1 = from_point[0] * self.scale, from_point[1] * self.scale
        x2, y2 = to_point[0] * self.scale, to_point[1] * self.scale
        
        self._add_line(f'  (command "LAYER" "S" "{layer}" "")')
        self._add_line(
            f'  (command "LINE" (list {x1:.3f} {y1:.3f} 0) '
            f'(list {x2:.3f} {y2:.3f} 0) "")'
        )
    
    def _add_text(
        self,
        text: str,
        x: float,
        y: float,
        height: float = 0.1,
        layer: str = None
    ) -> None:
        """Generate text command."""
        x_scaled = x * self.scale
        y_scaled = y * self.scale
        h_scaled = height * self.scale
        
        if layer:
            self._add_line(f'  (command "LAYER" "S" "{layer}" "")')
        
        self._add_line(
            f'  (command "TEXT" (list {x_scaled:.3f} {y_scaled:.3f} 0) '
            f'{h_scaled:.3f} 0 "{text}")'
        )
    
    def generate_room(self, room: RoomDesign) -> str:
        """
        Generate AutoLISP for a single room.
        
        Args:
            room: Room design
            
        Returns:
            AutoLISP script string
        """
        self.script_lines = []
        
        self._add_comment(f"Room: {room.room_id}")
        self._add_comment(f"Type: {room.room_type.value}")
        self._add_comment(f"Area: {room.area:.2f} m²")
        self._add_line("")
        
        # Function definition
        func_name = f"draw-{room.room_id.replace('-', '_')}"
        self._add_line(f"(defun {func_name} (base-x base-y)")
        
        # Draw outlets
        self._add_comment("Outlets")
        for outlet in room.outlets:
            self._insert_block(
                self.OUTLET_BLOCK,
                outlet.x,
                outlet.y,
                self.LAYER_OUTLETS,
                attributes={"ID": outlet.outlet_id, "CIRCUIT": outlet.circuit_id}
            )
        
        # Draw lights
        self._add_comment("Light fixtures")
        for light in room.lights:
            self._insert_block(
                self.LIGHT_BLOCK,
                light.x,
                light.y,
                self.LAYER_LIGHTING,
                attributes={"ID": light.light_id, "WATTS": str(int(light.wattage))}
            )
        
        # Draw switches
        self._add_comment("Switches")
        for switch in room.switches:
            self._insert_block(
                self.SWITCH_BLOCK,
                switch.x,
                switch.y,
                self.LAYER_SWITCH,
            )
        
        # Room label
        self._add_text(
            f"{room.room_type.value.upper()}",
            room.outlets[0].x if room.outlets else 0,
            room.outlets[0].y - 0.5 if room.outlets else 0,
            height=0.15,
            layer=self.LAYER_ANNOTATION
        )
        
        self._add_line(")")
        self._add_line("")
        
        return "\n".join(self.script_lines)
    
    def generate_project(self, project: ProjectDesign) -> str:
        """
        Generate complete AutoLISP script for a project.
        
        Args:
            project: Project design
            
        Returns:
            Complete AutoLISP script string
        """
        self.script_lines = []
        
        # Header
        self._add_comment("=" * 50)
        self._add_comment(f"MCP Core v2 - AutoLISP Export")
        self._add_comment(f"Project: {project.project_name}")
        self._add_comment(f"ID: {project.project_id}")
        self._add_comment("=" * 50)
        self._add_line("")
        
        # Layer setup
        self._setup_layers()
        self._add_line("")
        
        # Generate each room
        room_scripts = []
        for room in project.rooms:
            room_script = self.generate_room(room)
            room_scripts.append(room_script)
        
        script_body = "\n".join(self.script_lines)
        rooms_body = "\n".join(room_scripts)
        
        # Main function
        main_func = [
            "; ===== Main Drawing Function =====",
            f"(defun draw-project-{project.project_id.replace('-', '_')} ()",
            "  (setup-elec-layers)",
        ]
        
        for room in project.rooms:
            func_name = f"draw-{room.room_id.replace('-', '_')}"
            main_func.append(f"  ({func_name} 0 0)")
        
        main_func.append("  (princ)")
        main_func.append(")")
        main_func.append("")
        
        # Circuit schedule
        schedule = self._generate_circuit_schedule(project)
        
        # Combine all parts
        full_script = "\n".join([
            script_body,
            rooms_body,
            "\n".join(main_func),
            schedule
        ])
        
        return full_script
    
    def _generate_circuit_schedule(self, project: ProjectDesign) -> str:
        """Generate circuit schedule table."""
        lines = [
            "; ===== Circuit Schedule =====",
            "; Circuit ID | Type | Breaker | Wire | Load",
        ]
        
        for room in project.rooms:
            for circuit in room.circuits:
                lines.append(
                    f"; {circuit.circuit_id} | {circuit.circuit_type} | "
                    f"{circuit.breaker_size}A | {circuit.wire_size}mm² | "
                    f"{circuit.total_load}W"
                )
        
        lines.append(f"; Main Breaker: {project.main_breaker_size}A")
        lines.append(f"; Total Demand: {project.total_demand_load:.0f}W")
        
        return "\n".join(lines)
    
    def generate_simple_outlet_script(
        self,
        outlets: List[Dict[str, float]]
    ) -> str:
        """
        Generate simple script for outlet placement.
        
        Args:
            outlets: List of {x, y} coordinates
            
        Returns:
            Simple AutoLISP script
        """
        self.script_lines = []
        
        self._add_comment("Simple outlet placement script")
        self._add_line("(defun c:place-outlets ()")
        
        for i, outlet in enumerate(outlets):
            x = outlet.get("x", 0) * self.scale
            y = outlet.get("y", 0) * self.scale
            self._add_line(
                f'  (command "INSERT" "{self.OUTLET_BLOCK}" '
                f'(list {x:.3f} {y:.3f} 0) 1 1 0)'
            )
        
        self._add_line("  (princ)")
        self._add_line(")")
        
        return "\n".join(self.script_lines)
