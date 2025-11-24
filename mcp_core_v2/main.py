"""
MCP Core v2 Main Entry Point
CLI and programmatic entry point for the design pipeline.
"""

import sys
import json
from typing import Optional

from models.contracts import RoomType, RoomInput, ProjectInput
from pipeline import DesignPipeline, create_demo_project, run_demo


def run_cli():
    """Run command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MCP Core v2 - Electrical Design Pipeline"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo design (4x3m bedroom)"
    )
    parser.add_argument(
        "--room-type",
        type=str,
        choices=[rt.value for rt in RoomType],
        help="Room type for quick design"
    )
    parser.add_argument(
        "--width",
        type=float,
        help="Room width in meters"
    )
    parser.add_argument(
        "--length",
        type=float,
        help="Room length in meters"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["json", "summary", "autolisp"],
        default="summary",
        help="Output format"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Run appropriate mode
    if args.demo:
        result = run_demo()
    elif args.room_type and args.width and args.length:
        pipeline = DesignPipeline()
        result = pipeline.quick_design(
            room_type=args.room_type,
            width=args.width,
            length=args.length,
        )
    else:
        parser.print_help()
        sys.exit(1)
    
    # Format output
    if args.output == "json":
        output = result.model_dump_json(indent=2)
    elif args.output == "autolisp":
        if hasattr(result, "autolisp_script"):
            output = result.autolisp_script
        else:
            # Generate for room design
            from core.autolisp_generator import AutoLISPGenerator
            gen = AutoLISPGenerator()
            output = gen.generate_room(result)
    else:
        output = format_summary(result)
    
    # Write output
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(output)
        print(f"Output written to {args.output_file}")
    else:
        print(output)


def format_summary(result) -> str:
    """Format design result as human-readable summary."""
    lines = []
    lines.append("=" * 50)
    lines.append("MCP Core v2 Design Summary")
    lines.append("=" * 50)
    
    if hasattr(result, "project_id"):
        # Project design
        lines.append(f"Project: {result.project_name}")
        lines.append(f"ID: {result.project_id}")
        lines.append(f"Rooms: {len(result.rooms)}")
        lines.append("")
        
        for room in result.rooms:
            lines.append(f"--- {room.room_id} ({room.room_type.value}) ---")
            lines.append(f"  Area: {room.area:.1f} m²")
            lines.append(f"  Outlets: {len(room.outlets)}")
            lines.append(f"  Lights: {len(room.lights)}")
            lines.append(f"  Circuits: {len(room.circuits)}")
            lines.append(f"  Total Load: {room.total_load_watts:.0f}W")
            lines.append("")
        
        lines.append("--- System Summary ---")
        lines.append(f"Main Breaker: {result.main_breaker_size}A")
        lines.append(f"Total Connected Load: {result.total_connected_load:.0f}W")
        lines.append(f"Total Demand Load: {result.total_demand_load:.0f}W")
        lines.append(f"Compliant: {result.compliance.is_compliant}")
        
        if result.compliance.violations:
            lines.append("\nViolations:")
            for v in result.compliance.violations:
                lines.append(f"  - {v}")
        
        if result.compliance.warnings:
            lines.append("\nWarnings:")
            for w in result.compliance.warnings:
                lines.append(f"  - {w}")
    
    else:
        # Room design
        lines.append(f"Room: {result.room_id}")
        lines.append(f"Type: {result.room_type.value}")
        lines.append(f"Area: {result.area:.1f} m²")
        lines.append("")
        lines.append(f"Outlets: {len(result.outlets)}")
        lines.append(f"Lights: {len(result.lights)}")
        lines.append(f"Switches: {len(result.switches)}")
        lines.append(f"Circuits: {len(result.circuits)}")
        lines.append("")
        
        for circuit in result.circuits:
            lines.append(f"Circuit {circuit.circuit_id}:")
            lines.append(f"  Type: {circuit.circuit_type}")
            lines.append(f"  Breaker: {circuit.breaker_size}A")
            lines.append(f"  Wire: {circuit.wire_size}mm²")
            lines.append(f"  Conduit: {circuit.conduit_size}mm")
            lines.append(f"  Load: {circuit.total_load:.0f}W")
        
        lines.append("")
        lines.append(f"Total Load: {result.total_load_watts:.0f}W")
    
    lines.append("")
    lines.append("=" * 50)
    
    return "\n".join(lines)


def design_from_json(json_input: str) -> str:
    """
    Design from JSON input.
    
    Args:
        json_input: JSON string with project specification
        
    Returns:
        JSON string with project design
    """
    data = json.loads(json_input)
    
    # Parse rooms
    rooms = []
    for room_data in data.get("rooms", []):
        room = RoomInput(
            room_id=room_data["room_id"],
            room_type=RoomType(room_data["room_type"]),
            width=room_data["width"],
            length=room_data["length"],
            height=room_data.get("height", 2.8),
            special_loads=room_data.get("special_loads"),
        )
        rooms.append(room)
    
    project = ProjectInput(
        project_id=data.get("project_id", "project-001"),
        project_name=data.get("project_name", "Unnamed Project"),
        rooms=rooms,
        voltage=data.get("voltage", 220.0),
        phases=data.get("phases", 1),
    )
    
    pipeline = DesignPipeline(
        voltage=project.voltage,
        phases=project.phases,
    )
    result = pipeline.design_project(project)
    
    return result.model_dump_json(indent=2)


if __name__ == "__main__":
    run_cli()
