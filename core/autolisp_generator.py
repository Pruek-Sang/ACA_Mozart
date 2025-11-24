"""AutoLISP generator for MCP Core v2.

Generates AutoLISP scripts for AutoCAD electrical layout drawings.
"""

import logging
from datetime import datetime
from typing import List, Optional

from models.baseline import BaselineContext, BaselineRoom, BaselineCircuit, BaselineLoad
from models.contracts import AutoLispScript

logger = logging.getLogger(__name__)


class AutoLispGenerator:
    """Generates AutoLISP scripts for CAD layout."""

    # AutoCAD layer definitions
    LAYERS = {
        "lighting": "E-LITE",
        "outlet": "E-POWR",
        "dedicated": "E-POWR-SPEC",
        "panel": "E-PANEL",
        "wire": "E-WIRE",
        "annotation": "E-ANNO",
    }

    # Symbol block names
    SYMBOLS = {
        "light": "LIGHT-CEILING",
        "outlet": "OUTLET-DUPLEX",
        "switch": "SWITCH-SINGLE",
        "panel": "PANEL-MAIN",
        "dedicated": "OUTLET-SPECIAL",
    }

    def __init__(self, scale_factor: float = 100.0):
        """Initialize AutoLISP generator.
        
        Args:
            scale_factor: Drawing scale factor (mm per unit)
        """
        self._scale = scale_factor

    def generate(self, context: BaselineContext) -> AutoLispScript:
        """Generate complete AutoLISP script for the project.
        
        Args:
            context: Baseline context with all rooms and circuits
            
        Returns:
            AutoLispScript with complete script content
        """
        logger.info(f"Generating AutoLISP script for project {context.project_id}")
        
        lines = []
        
        # Header
        lines.extend(self._generate_header(context))
        
        # Layer setup
        lines.extend(self._generate_layer_setup())
        
        # Main defun
        lines.append("")
        lines.append(f"(defun c:MCP-{context.project_id[:8]} ()")
        lines.append('  (princ "\\nMCP Electrical Layout Generator")')
        lines.append('  (princ "\\nCreating electrical layout...")')
        
        # Draw each room
        for room in context.rooms:
            lines.extend(self._generate_room_layout(room))
        
        # Draw panel
        lines.extend(self._generate_panel_layout(context))
        
        # Close main function
        lines.append('  (princ "\\nLayout complete.")')
        lines.append("  (princ)")
        lines.append(")")
        
        # Footer
        lines.extend(self._generate_footer(context))
        
        script_content = "\n".join(lines)
        
        return AutoLispScript(
            script_content=script_content,
            generated_at=datetime.utcnow(),
            target_software="AutoCAD",
        )

    def _generate_header(self, context: BaselineContext) -> List[str]:
        """Generate script header comments."""
        return [
            ";; ========================================",
            f";; MCP Electrical Layout - {context.project_name}",
            f";; Project ID: {context.project_id}",
            f";; Generated: {datetime.utcnow().isoformat()}",
            f";; Total Area: {context.total_area_m2:.1f} m²",
            f";; Total Circuits: {context.total_circuits}",
            f";; Total Load: {context.total_connected_load_w:.0f} W",
            ";; ========================================",
            "",
            ";; Helper functions",
            "",
            "(defun mcp-make-layer (name color / )",
            '  (if (not (tblsearch "LAYER" name))',
            "    (command \"_.LAYER\" \"_M\" name \"_C\" color \"\" \"\")",
            "  )",
            ")",
            "",
            "(defun mcp-insert-symbol (blkname pt layer sc rot / )",
            "  (command \"_.LAYER\" \"_S\" layer \"\")",
            "  (if (tblsearch \"BLOCK\" blkname)",
            "    (command \"_.INSERT\" blkname pt sc sc rot)",
            '    (command "_.POINT" pt)',
            "  )",
            ")",
            "",
            "(defun mcp-draw-wire (pt1 pt2 layer / )",
            "  (command \"_.LAYER\" \"_S\" layer \"\")",
            "  (command \"_.LINE\" pt1 pt2 \"\")",
            ")",
            "",
        ]

    def _generate_layer_setup(self) -> List[str]:
        """Generate layer creation commands."""
        lines = [
            "(defun mcp-setup-layers ()",
            '  (princ "\\nSetting up layers...")',
        ]
        
        layer_colors = {
            "E-LITE": 3,      # Green
            "E-POWR": 1,      # Red
            "E-POWR-SPEC": 6, # Magenta
            "E-PANEL": 5,     # Blue
            "E-WIRE": 8,      # Grey
            "E-ANNO": 7,      # White
        }
        
        for layer, color in layer_colors.items():
            lines.append(f'  (mcp-make-layer "{layer}" {color})')
        
        lines.append(")")
        lines.append("")
        
        return lines

    def _generate_room_layout(self, room: BaselineRoom) -> List[str]:
        """Generate layout commands for a single room."""
        lines = [
            "",
            f"  ;; Room: {room.name} ({room.room_type})",
            f"  ;; Size: {room.width_m}m x {room.length_m}m = {room.area_m2:.1f}m²",
        ]
        
        # Base position for room (would be determined by floor plan in real implementation)
        base_x = 0
        base_y = 0
        
        for circuit in room.circuits:
            lines.extend(self._generate_circuit_symbols(circuit, base_x, base_y))
        
        return lines

    def _generate_circuit_symbols(
        self,
        circuit: BaselineCircuit,
        base_x: float,
        base_y: float
    ) -> List[str]:
        """Generate symbol placement for a circuit."""
        lines = [
            f"  ;; Circuit: {circuit.name} ({circuit.circuit_type.value})",
        ]
        
        layer = self.LAYERS.get(circuit.circuit_type.value, "E-POWR")
        
        for load in circuit.loads:
            # Calculate position
            x = base_x + (load.x_position_m or 0) * self._scale
            y = base_y + (load.y_position_m or 0) * self._scale
            
            # Determine symbol based on load type
            if circuit.circuit_type.value == "lighting":
                symbol = self.SYMBOLS["light"]
            elif circuit.circuit_type.value == "dedicated":
                symbol = self.SYMBOLS["dedicated"]
            else:
                symbol = self.SYMBOLS["outlet"]
            
            lines.append(
                f'  (mcp-insert-symbol "{symbol}" '
                f'(list {x:.1f} {y:.1f} 0) "{layer}" 1.0 0)'
            )
        
        return lines

    def _generate_panel_layout(self, context: BaselineContext) -> List[str]:
        """Generate panel location and annotation."""
        lines = [
            "",
            "  ;; Main Panel",
            f'  (mcp-insert-symbol "{self.SYMBOLS["panel"]}" '
            f'(list 0 0 0) "{self.LAYERS["panel"]}" 1.0 0)',
            "",
            "  ;; Panel Schedule Annotation",
            f'  (command "_.LAYER" "_S" "{self.LAYERS["annotation"]}" "")',
            f'  (command "_.MTEXT" (list 500 -100 0) "_W" "200"',
            f'    "PANEL SCHEDULE"',
            f'    "Project: {context.project_name}"',
            f'    "Total Load: {context.total_connected_load_w:.0f}W"',
            f'    "Circuits: {context.total_circuits}"',
            '    "")',
        ]
        
        return lines

    def _generate_footer(self, context: BaselineContext) -> List[str]:
        """Generate script footer with execution entry point."""
        return [
            "",
            ";; Auto-execute setup on load",
            "(mcp-setup-layers)",
            "",
            f";; To run: Type MCP-{context.project_id[:8]} at command prompt",
            f'(princ "\\nMCP Layout loaded. Type MCP-{context.project_id[:8]} to generate layout.")',
            "(princ)",
            "",
            ";; End of MCP AutoLISP Script",
        ]

    def generate_circuit_schedule(self, context: BaselineContext) -> str:
        """Generate circuit schedule as formatted text.
        
        Args:
            context: Baseline context
            
        Returns:
            Formatted circuit schedule text
        """
        lines = [
            "=" * 80,
            f"CIRCUIT SCHEDULE - {context.project_name}",
            "=" * 80,
            "",
            f"{'Circuit':<20} {'Type':<12} {'Load (W)':<10} {'Current (A)':<12} {'Room':<15}",
            "-" * 80,
        ]
        
        for room in context.rooms:
            for circuit in room.circuits:
                lines.append(
                    f"{circuit.name:<20} "
                    f"{circuit.circuit_type.value:<12} "
                    f"{circuit.total_connected_load_w:<10.0f} "
                    f"{circuit.design_current_a:<12.2f} "
                    f"{room.name:<15}"
                )
        
        lines.append("-" * 80)
        lines.append(
            f"{'TOTAL':<20} {'':<12} "
            f"{context.total_connected_load_w:<10.0f} "
            f"{'':<12} {'':<15}"
        )
        lines.append("=" * 80)
        
        return "\n".join(lines)
