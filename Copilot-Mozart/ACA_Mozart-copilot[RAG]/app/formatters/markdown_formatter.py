"""
Markdown Formatter - Professional Load Schedule Format

Design Principles:
- Table-based layout per floor (like real engineering load schedules)
- Minimal emojis, professional appearance
- Circuit numbering (C1-1, C1-2, etc.)
- Compact columns for field engineers
"""

import math
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base_formatter import BaseFormatter


def round_up(value: float, decimals: int = 0) -> float:
    """Round up to specified decimal places (ceiling)."""
    if decimals == 0:
        return math.ceil(value)
    multiplier = 10 ** decimals
    return math.ceil(value * multiplier) / multiplier


# Constants
NOT_SPECIFIED = 'ไม่ระบุ'


class MarkdownFormatter(BaseFormatter):
    """Formats MCP design results as professional Load Schedule."""
    
    # AWG to mm² mapping
    AWG_TO_MM2 = {
        '14': '2.5', '12': '4', '10': '6', '8': '10', 
        '6': '16', '4': '25', '2': '35', '1': '50',
        '1/0': '55', '2/0': '70', '3/0': '95', '4/0': '120'
    }
    
    # Critical keywords (require RCBO)
    CRITICAL_KEYWORDS = ['น้ำอุ่น', 'ปั๊ม', 'water', 'pump', 'heater']
    
    # Wet area keywords
    WET_AREA_KEYWORDS = ['ห้องน้ำ', 'ครัว', 'ซักล้าง', 'bathroom', 'kitchen', 'laundry']
    
    def get_format_type(self) -> str:
        return "markdown"
    
    def format(self, mcp_result: Dict[str, Any]) -> str:
        """Transform MCP result into professional Load Schedule."""
        if mcp_result is None:
            return "❌ ไม่สามารถคำนวณได้: ไม่ได้รับข้อมูลจาก MCP Core"
        
        lines = []
        
        # Extract data
        project_name = mcp_result.get('project_name', NOT_SPECIFIED)
        summary = mcp_result.get('summary') or {}
        wire_sizing = mcp_result.get('wire_sizing') or {}
        breaker_selections = mcp_result.get('breaker_selections') or {}
        conduit_sizing = mcp_result.get('conduit_sizing') or {}
        request = mcp_result.get('request') or {}
        loads = request.get('loads') or [] if isinstance(request, dict) else []
        warnings = mcp_result.get('warnings') or []
        errors = mcp_result.get('errors') or []
        
        # Build report sections
        lines.extend(self._create_header(project_name, summary))
        lines.extend(self._create_main_equipment(summary))
        lines.extend(self._create_load_schedule(loads, wire_sizing, breaker_selections))
        lines.extend(self._create_breaker_summary(breaker_selections))
        lines.extend(self._create_notes_section(warnings, errors))
        lines.extend(self._create_footer())
        
        return "\n".join(lines)
    
    def _create_header(self, project_name: str, summary: Dict) -> List[str]:
        """Create professional header with project info."""
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Calculate totals
        total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
        total_watts = round_up(total_watts)
        demand_current = summary.get('demand_current')
        if demand_current is None:
            demand_current = total_watts / 230 if total_watts else 0
        demand_current = round_up(demand_current, 1)
        
        return [
            "# ตารางโหลดไฟฟ้า (Load Schedule)",
            "",
            f"**โครงการ:** {project_name}",
            f"**วันที่:** {today}",
            "",
            "---",
            "",
            "## สรุปภาพรวม",
            "",
            "| รายการ | ค่า |",
            "|--------|-----|",
            f"| โหลดรวม | {total_watts:,.0f} W ({total_watts/1000:.1f} kW) |",
            f"| กระแสรวม | {demand_current:.1f} A |",
            f"| Design Current (×1.25) | {round_up(demand_current * 1.25, 1):.1f} A |",
            "",
        ]
    
    def _create_main_equipment(self, summary: Dict) -> List[str]:
        """Create main equipment sizing section."""
        demand_current = summary.get('demand_current')
        if demand_current is None:
            total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
            demand_current = total_watts / 230 if total_watts else 0
        
        # Determine sizes
        if demand_current <= 15:
            meter, main_wire, main_cb = "5(15)A", "4 mm²", "16A/1P"
        elif demand_current <= 30:
            meter, main_wire, main_cb = "15(45)A", "10 mm²", "32A/2P"
        elif demand_current <= 50:
            meter, main_wire, main_cb = "30(100)A", "16 mm²", "50A/2P"
        elif demand_current <= 100:
            meter, main_wire, main_cb = "50(150)A", "35 mm²", "100A/2P"
        else:
            meter, main_wire, main_cb = "CT", "50 mm²", "125A/2P"
        
        return [
            "## อุปกรณ์หลัก",
            "",
            "| อุปกรณ์ | ขนาด |",
            "|---------|------|",
            f"| มิเตอร์ไฟฟ้า | {meter} |",
            f"| สายเมน (THW) | {main_wire} |",
            f"| Main Breaker | {main_cb} |",
            "| สายดิน | 10 mm² |",
            "| หลักดิน | 5/8\" × 8 ฟุต (≤5Ω) |",
            "",
            "---",
            "",
        ]
    
    def _create_load_schedule(
        self, 
        loads: List[Dict], 
        wire_sizing: Dict,
        breaker_selections: Dict
    ) -> List[str]:
        """Create professional load schedule table per floor."""
        lines = ["## ตารางโหลด", ""]
        
        # Group by floor
        floors: Dict[str, List[Dict]] = {}
        for load in loads:
            location = load.get('location', {})
            floor = str(location.get('floor', '1'))
            if floor not in floors:
                floors[floor] = []
            floors[floor].append(load)
        
        # Sort floors
        sorted_floors = sorted(floors.keys(), key=lambda x: (x.isdigit(), int(x) if x.isdigit() else 999, x))
        
        circuit_num = 1
        
        for floor in sorted_floors:
            floor_loads = floors[floor]
            floor_display = f"ชั้น {floor}" if floor.isdigit() else floor
            
            # Calculate floor total
            floor_watts = sum(
                load.get('power_watts', 0) * load.get('quantity', 1)
                for load in floor_loads
            )
            
            # Floor header
            lines.append(f"### {floor_display} (รวม {round_up(floor_watts):,.0f} W)")
            lines.append("")
            
            # Table header
            lines.append("| # | ห้อง | โหลด | W | A | สาย | CB | VD% | หมายเหตุ |")
            lines.append("|:-:|------|------|---:|---:|-----|-----|----:|----------|")
            
            for load in floor_loads:
                lid = load.get('id', '')
                room = load.get('location', {}).get('room', '')
                name = load.get('name', '')
                power = load.get('power_watts', 0) * load.get('quantity', 1)
                power = round_up(power)
                
                # Get sizing info
                w = wire_sizing.get(lid, {})
                b = breaker_selections.get(lid, {})
                
                # Wire
                wire_awg = str(w.get('wire_size', '14'))
                wire_mm = self.AWG_TO_MM2.get(wire_awg, wire_awg)
                vd = w.get('voltage_drop_percent', 0)
                vd = round_up(vd, 1)
                
                # Breaker
                breaker = b.get('breaker_rating', 15)
                poles = str(b.get('poles', 1)).replace('P', '')
                breaker_type = b.get('breaker_type', 'MCB')
                
                # Current
                current = power / 230 if power > 0 else 0
                current = round_up(current, 1)
                
                # Check if wet area or critical
                is_wet = any(kw in room.lower() for kw in self.WET_AREA_KEYWORDS)
                is_critical = any(kw in name.lower() for kw in self.CRITICAL_KEYWORDS)
                
                # Determine note
                note = ""
                if is_critical:
                    note = "**RCBO 30mA**"
                    breaker_type = "RCBO"
                elif is_wet:
                    note = "แนะนำ RCBO"
                    breaker_type = "RCBO"
                
                # Distance marker
                is_default = w.get('used_default_distance', True)
                dist_marker = "*" if is_default else ""
                
                # CB display
                cb_display = f"{breaker_type} {breaker}A/{poles}P"
                
                # Shorten room name for table
                room_short = room[:12] + "..." if len(room) > 15 else room
                name_short = name[:12] + "..." if len(name) > 15 else name
                
                lines.append(
                    f"| {circuit_num} | {room_short} | {name_short} | "
                    f"{power:,.0f} | {current:.1f} | {wire_mm}mm²{dist_marker} | "
                    f"{cb_display} | {vd:.1f} | {note} |"
                )
                circuit_num += 1
            
            lines.append("")
        
        # Note about default distance
        lines.append("> `*` = ระยะ default (ควรวัดจริงหน้างาน)")
        lines.append("")
        return lines
    
    def _create_breaker_summary(self, breaker_selections: Dict) -> List[str]:
        """Create breaker count summary."""
        lines = [
            "---",
            "",
            "## สรุปเบรกเกอร์",
            "",
            "| ขนาด | จำนวน | ใช้สำหรับ |",
            "|------|:-----:|----------|",
        ]
        
        usage_desc = {
            '15A/1P': 'ไฟ, เต้ารับทั่วไป',
            '20A/1P': 'เครื่องใช้ไฟฟ้าสูง',
            '20A/2P': 'น้ำอุ่น 3.5kW, เตา',
            '25A/2P': 'น้ำอุ่น 4.5kW',
            '30A/2P': 'แอร์ ≥24000BTU',
        }
        
        breaker_count: Dict[str, int] = {}
        for lid, b in breaker_selections.items():
            if isinstance(b, dict):
                rating = b.get('breaker_rating', 15)
                poles = str(b.get('poles', 1)).replace('P', '')
                if rating > 100:
                    continue
                key = f"{rating}A/{poles}P"
                breaker_count[key] = breaker_count.get(key, 0) + 1
        
        for rating, count in sorted(breaker_count.items()):
            desc = usage_desc.get(rating, '-')
            lines.append(f"| {rating} | {count} | {desc} |")
        
        lines.append("")
        return lines
    
    def _create_notes_section(self, warnings: List[str], errors: List[str]) -> List[str]:
        """Create notes and warnings section."""
        lines = [
            "---",
            "",
            "## หมายเหตุ",
            "",
            "### ข้อกำหนดความปลอดภัย",
            "",
            "| อุปกรณ์ | ข้อกำหนด |",
            "|---------|----------|",
            "| น้ำอุ่น | RCBO 30mA + วงจรเฉพาะ |",
            "| แอร์ | วงจรเฉพาะ + 2P |",
            "| เตาไฟฟ้า | วงจรเฉพาะ 20A |",
            "| ปั๊มน้ำ | Motor Starter + Overload |",
            "",
        ]
        
        # Add warnings if any
        if warnings or errors:
            lines.append("### คำเตือนจากระบบ")
            lines.append("")
            for err in errors[:3]:
                lines.append(f"- ❌ {err}")
            for warn in warnings[:5]:
                lines.append(f"- ⚠️ {warn}")
            lines.append("")
        
        return lines
    
    def _create_footer(self) -> List[str]:
        """Create professional footer."""
        today = datetime.now().strftime("%d/%m/%Y %H:%M")
        return [
            "---",
            "",
            "## มาตรฐานอ้างอิง",
            "",
            "| มาตรฐาน | หัวข้อ |",
            "|---------|--------|",
            "| วสท. 2564 | การเดินสายและติดตั้งอุปกรณ์ไฟฟ้า |",
            "| NEC 2023 | Wire Sizing, Breaker Selection |",
            "| IEC 60364 | Low-voltage Installations |",
            "",
            "---",
            "",
            f"*สร้างโดย MCP Core v2.0 | {today}*",
        ]


# Convenience function
def format_design_report(mcp_result: Dict[str, Any]) -> str:
    """Quick function to format MCP result as Markdown."""
    formatter = MarkdownFormatter()
    return formatter.format(mcp_result)
