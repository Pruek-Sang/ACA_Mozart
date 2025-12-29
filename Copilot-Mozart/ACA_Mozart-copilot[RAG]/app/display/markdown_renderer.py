"""
Markdown Renderer - Render DisplayData to Markdown

This module ONLY renders, it does NOT calculate.
All calculations come from compute.py (DisplayData).

[CP-RENDER] Checkpoint prefix for all render-related logs.

Design Pattern:
- Read Only: Reads from DisplayData, never calculates
- Pure Function: Same input → Same output
- Backward Compatible: Output matches existing markdown_formatter.py format
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from .compute import DisplayData, CircuitData

logger = logging.getLogger("Aura.Display.Renderer")


def render_markdown(display_data: DisplayData) -> str:
    """
    [CP-RENDER] Render DisplayData to Markdown string.
    
    This is a PURE RENDER function - no calculations!
    All values come from display_data (computed by compute.py).
    
    Args:
        display_data: DisplayData from compute_display_data()
    
    Returns:
        Markdown string matching existing format
    """
    logger.info("[CP-RENDER] Rendering markdown...")
    
    lines: List[str] = []
    
    # Create header
    lines.extend(_render_header(display_data))
    
    # Create main equipment
    lines.extend(_render_main_equipment(display_data))
    
    # Create circuit schedule
    lines.extend(_render_circuit_schedule(display_data))
    
    # Create footer
    lines.extend(_render_footer(display_data))
    
    result = "\n".join(lines)
    logger.info(f"[CP-RENDER] Rendered {len(lines)} lines")
    
    return result


def _render_header(data: DisplayData) -> List[str]:
    """Render header section (project info + summary)."""
    today = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y")
    
    return [
        "# ตารางโหลดไฟฟ้า (Load Schedule)",
        "",
        f"**โครงการ:** {data['project_name']}",
        f"**วันที่:** {today}",
        "",
        "---",
        "",
        "## สรุปภาพรวม",
        "",
        "| รายการ | ค่า |",
        "|--------|-----|",
        f"| โหลดรวม | {data['total_watts']:,.0f} W ({data['total_kw']:.1f} kW) |",
        f"| กระแสรวม | {data['demand_current']:.1f} A |",
        f"| Design Current (×1.25) | {data['design_current']:.1f} A |",
        "",
    ]


def _render_main_equipment(data: DisplayData) -> List[str]:
    """Render main equipment section."""
    return [
        "## อุปกรณ์หลัก",
        "",
        "| อุปกรณ์ | ขนาด |",
        "|---------|------|",
        f"| มิเตอร์ไฟฟ้า | {data['meter_size']} |",
        f"| สายเมน (THW) | {data['main_wire']} |",
        f"| Main Breaker | {data['main_breaker']} |",
        "| สายดิน | 10 mm² |",
        '| หลักดิน | 5/8" × 8 ฟุต (≤5Ω) |',
        "",
        "---",
        "",
    ]


def _render_circuit_schedule(data: DisplayData) -> List[str]:
    """Render circuit schedule table."""
    lines = [
        "## รายการวงจรย่อย",
        "",
        "| # | วงจร | ห้อง | โหลด (W) | กระแส (A) | สาย | CB | VD% |",
        "|:-:|------|------|--------:|--------:|-----|----:|----:|",
    ]
    
    circuits = data.get('circuits', [])
    for i, ckt in enumerate(circuits, 1):
        name = ckt['circuit_name']
        if len(name) > 20:
            name = name[:17] + "..."
        
        room = ckt.get('room', '')
        if len(room) > 15:
            room = room[:12] + "..."
        
        lines.append(
            f"| {i} | {name} | {room} | "
            f"{ckt['total_watts']:,.0f} | {ckt['total_current']:.1f} | "
            f"{ckt['wire_size']} mm² | {ckt['breaker_rating']}A/{ckt['breaker_poles']}P | "
            f"{ckt['vd_percent']:.1f}% |"
        )
    
    lines.extend([
        "",
        f"**รวม {data['circuit_count']} วงจร**",
        "",
    ])
    
    return lines


def _render_footer(data: DisplayData) -> List[str]:
    """Render footer with warnings and notes."""
    lines = ["---", ""]
    
    # Warnings section
    warnings = data.get('warnings', [])
    if warnings:
        lines.extend([
            "## ⚠️ ข้อควรระวัง",
            "",
        ])
        for warn in warnings[:5]:  # Show up to 5
            lines.append(f"- {warn}")
        lines.append("")
    
    # Errors section
    errors = data.get('errors', [])
    if errors and errors != ['No data available']:
        lines.extend([
            "## ❌ ข้อผิดพลาด",
            "",
        ])
        for err in errors[:3]:  # Show up to 3
            lines.append(f"- {err}")
        lines.append("")
    
    # Standard footer
    lines.extend([
        "---",
        "",
        "*คำนวณตามมาตรฐาน วสท. 2021 | Mozart System*",
    ])
    
    return lines
