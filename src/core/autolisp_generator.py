"""AutoLISP generator for creating CAD scripts."""

from src.models.baseline import BaselineContext


class AutoLispGenerator:
    """Generates AutoLISP scripts for AutoCAD electrical drawings."""

    def generate(self, context: BaselineContext) -> str:
        """Generate AutoLISP script for the project.
        
        Creates script commands for:
        - Drawing circuit symbols
        - Adding circuit tags/labels
        - Creating load schedule table
        
        Args:
            context: BaselineContext with circuit data.
            
        Returns:
            AutoLISP script string.
        """
        lines: list[str] = []

        # Header
        lines.append("; MCP Core v2 Generated AutoLISP Script")
        lines.append(f"; Project: {context.project_name}")
        lines.append(f"; Project ID: {context.project_id}")
        lines.append("")

        # Define helper function
        lines.append(self._generate_helper_functions())

        # Generate circuit drawing commands
        lines.append("; Circuit Drawing Commands")
        y_offset = 0

        for room in context.rooms:
            lines.append(f"; Room: {room.room_id} ({room.room_type})")

            for circuit in room.circuits:
                # Generate circuit tag
                tag_text = self._format_circuit_tag(circuit)
                lines.append(
                    f'(draw-circuit-tag "{circuit.circuit_id}" '
                    f'"{tag_text}" {y_offset})'
                )
                y_offset += 15

            y_offset += 10  # Extra spacing between rooms

        # Generate load schedule
        lines.append("")
        lines.append("; Load Schedule Table")
        lines.append(self._generate_load_schedule(context))

        # Footer
        lines.append("")
        lines.append("; End of generated script")
        lines.append('(princ "\\nMCP circuits drawn successfully.")')
        lines.append("(princ)")

        return "\n".join(lines)

    def _generate_helper_functions(self) -> str:
        """Generate AutoLISP helper functions."""
        return '''
; Helper function to draw circuit tag
(defun draw-circuit-tag (circuit-id tag-text y-pos / pt)
  (setq pt (list 0 y-pos 0))
  (command "_.TEXT" pt 2.5 0 tag-text)
  (command "_.TEXT" (list 100 y-pos 0) 2.5 0 circuit-id)
)

; Helper function to draw circuit symbol
(defun draw-circuit-symbol (circuit-type x-pos y-pos / )
  (cond
    ((= circuit-type "lighting")
     (command "_.CIRCLE" (list x-pos y-pos 0) 3))
    ((= circuit-type "outlet")
     (command "_.RECTANGLE" 
       (list (- x-pos 2) (- y-pos 2) 0) 
       (list (+ x-pos 2) (+ y-pos 2) 0)))
    ((= circuit-type "ac")
     (command "_.POLYGON" 6 (list x-pos y-pos 0) "I" 3))
    (t
     (command "_.POINT" (list x-pos y-pos 0)))
  )
)
'''

    def _format_circuit_tag(self, circuit) -> str:
        """Format circuit tag text for CAD label.
        
        Args:
            circuit: BaselineCircuit object.
            
        Returns:
            Formatted tag string.
        """
        # Format: TYPE - WIRE x BREAKER / CONDUIT
        # Example: LTG - 2.5mm² x 16A / 20mm
        type_abbrev = {
            "lighting": "LTG",
            "outlet": "OUT",
            "ac": "AC",
            "special_outlet": "SPL",
            "custom": "CST",
        }.get(circuit.circuit_type, circuit.circuit_type[:3].upper())

        tag = (
            f"{type_abbrev} - {circuit.wire_size_sqmm}mm² x "
            f"{circuit.breaker_rating_a:.0f}A / {circuit.conduit_size_mm:.0f}mm"
        )

        return tag

    def _generate_load_schedule(self, context: BaselineContext) -> str:
        """Generate AutoLISP commands for load schedule table.
        
        Args:
            context: BaselineContext with all data.
            
        Returns:
            AutoLISP string for load schedule.
        """
        lines: list[str] = []
        lines.append("(defun draw-load-schedule (x-start y-start / )")

        # Table header
        lines.append(f'  (command "_.TEXT" (list x-start y-start 0) 3.5 0 "LOAD SCHEDULE")')
        lines.append(
            '  (command "_.TEXT" (list x-start (- y-start 10) 0) 2.5 0 '
            f'"Project: {context.project_name}")'
        )

        # Summary row
        total_kw = context.total_demand_load_w / 1000
        lines.append(
            f'  (command "_.TEXT" (list x-start (- y-start 20) 0) 2.5 0 '
            f'"Total Demand: {total_kw:.2f} kW")'
        )
        lines.append(
            f'  (command "_.TEXT" (list x-start (- y-start 25) 0) 2.5 0 '
            f'"Main Breaker: {context.main_breaker_rating_a:.0f} A")'
        )

        # Compliance status
        status = "COMPLIANT" if context.overall_compliant else "NON-COMPLIANT"
        lines.append(
            f'  (command "_.TEXT" (list x-start (- y-start 30) 0) 2.5 0 '
            f'"Status: {status}")'
        )

        lines.append(")")
        lines.append("(draw-load-schedule 0 -200)")

        return "\n".join(lines)
