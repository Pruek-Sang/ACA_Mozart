"""
Markdown Formatter - Transforms MCP JSON into beautiful Markdown reports.

Design Principles:
- Card-style layout for each device (readable, expandable)
- Legend at top (user reads warnings first)
- Critical items marked with 🔴
- Default values marked with *
- Grouped by logical relationship (wire→VD, conduit→fill, breaker→type)
"""

import math
from typing import Dict, Any, List, Optional
from .base_formatter import BaseFormatter


def round_up(value: float, decimals: int = 0) -> float:
    """Round up to specified decimal places (ceiling)."""
    if decimals == 0:
        return math.ceil(value)
    multiplier = 10 ** decimals
    return math.ceil(value * multiplier) / multiplier

# Constants for duplicate literals (SonarQube compliance)
NOT_SPECIFIED = 'ไม่ระบุ'


class MarkdownFormatter(BaseFormatter):
    """Formats MCP design results as Markdown with Card-style layout."""
    
    # AWG to mm² mapping
    AWG_TO_MM2 = {
        '14': '2.5', '12': '4', '10': '6', '8': '10', 
        '6': '16', '4': '25', '2': '35', '1': '50',
        '1/0': '55', '2/0': '70', '3/0': '95', '4/0': '120'
    }
    
    # Room icons
    ROOM_ICONS = {
        'ห้องนอน': '🛏️', 'ห้องน้ำ': '🚿', 'ครัว': '🍳', 
        'ห้องนั่งเล่น': '🛋️', 'ห้องซักล้าง': '🧺',
        'ห้องปั๊มน้ำ': '💧', 'ภายนอก': '🌳', 'สวน': '🌸', 
        'ประตู': '🚪', 'โรงรถ': '🚗', 'ระเบียง': '🌅',
        'ห้องทำงาน': '💼', 'ห้องเก็บของ': '📦'
    }
    
    # Critical keywords (require RCBO, special attention)
    CRITICAL_KEYWORDS = ['น้ำอุ่น', 'ปั๊ม', 'water', 'pump', 'heater']
    
    # Wet area keywords (recommend RCBO)
    WET_AREA_KEYWORDS = ['ห้องน้ำ', 'ครัว', 'ซักล้าง', 'bathroom', 'kitchen', 'laundry']
    
    def get_format_type(self) -> str:
        return "markdown"
    
    def format(self, mcp_result: Dict[str, Any]) -> str:
        """Transform MCP result into Card-style Markdown report."""
        # 🆕 FIX: Defensive null check to prevent 'NoneType' has no attribute 'get'
        if mcp_result is None:
            return "❌ ไม่สามารถคำนวณได้: ไม่ได้รับข้อมูลจาก MCP Core"
        
        lines = []
        
        # Extract data with defensive defaults
        project_name = mcp_result.get('project_name', NOT_SPECIFIED)
        summary = mcp_result.get('summary') or {}  # Handle None explicitly
        wire_sizing = mcp_result.get('wire_sizing') or {}
        breaker_selections = mcp_result.get('breaker_selections') or {}
        conduit_sizing = mcp_result.get('conduit_sizing') or {}
        request = mcp_result.get('request') or {}  # Handle None request
        loads = request.get('loads') or [] if isinstance(request, dict) else []
        
        # Extract warnings and errors from MCP result
        warnings = mcp_result.get('warnings') or []
        errors = mcp_result.get('errors') or []

        
        # Header
        lines.extend(self._create_header(project_name, mcp_result))
        
        # Project Info
        lines.extend(self._create_project_info(mcp_result))
        
        # Load Summary
        lines.extend(self._create_load_summary(summary))
        
        # Meter and Main
        lines.extend(self._create_meter_section(summary))
        
        # Legend (IMPORTANT - at top before details)
        lines.extend(self._create_legend())
        
        # Room Details (Card-style)
        lines.extend(self._create_room_details(
            loads, wire_sizing, breaker_selections, conduit_sizing
        ))
        
        # Breaker Summary
        lines.extend(self._create_breaker_summary(breaker_selections))
        
        # Safety Notes
        lines.extend(self._create_safety_notes())
        
        # ⚠️ Warnings & Errors from MCP Core (NEW)
        lines.extend(self._create_warnings_section(warnings, errors))
        
        # Compliance Status
        lines.extend(self._create_compliance_section(mcp_result))
        
        return "\n".join(lines)
    
    def _create_header(self, project_name: str, mcp_result: Dict) -> List[str]:
        """Create report header."""
        completed_at = mcp_result.get('completed_at', 'N/A')
        return [
            f"# 🏠✨ รายงานการออกแบบระบบไฟฟ้า - {project_name}",
            "",
            "> 🎯 **MCP Core v2.0** - Electrical Design Engine",
            f"> 📅 Generated: {completed_at}",
            "",
            "---",
            ""
        ]
    
    def _create_project_info(self, mcp_result: Dict) -> List[str]:
        """Create project information section."""
        project_name = mcp_result.get('project_name', 'N/A')
        project_number = mcp_result.get('project_number', 'N/A')
        request = mcp_result.get('request') or {}  # 🆕 FIX: Handle None
        service_voltage = request.get('service_voltage', 'N/A') if isinstance(request, dict) else 'N/A'
        loads = request.get('loads', []) if isinstance(request, dict) else []
        
        return [
            "## 🏡 ข้อมูลโครงการ",
            "",
            "| 📋 รายการ | 📝 รายละเอียด |",
            "|-----------|---------------|",
            f"| 🏷️ ชื่อโครงการ | {project_name} |",
            f"| 🔢 เลขที่โครงการ | {project_number} |",
            f"| ⚡ ระบบไฟฟ้า | {service_voltage} |",
            f"| 🔌 จำนวนโหลด | {len(loads)} รายการ |",
            "",
            "---",
            ""
        ]
    
    def _create_load_summary(self, summary: Dict) -> List[str]:
        """Create load summary section with ceiling-rounded values."""
        # MCP Core sends 'total_load_va', not 'total_watts'
        total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
        total_watts = round_up(total_watts)  # ปัดขึ้นเป็นจำนวนเต็ม
        
        # Calculate demand_current if not provided (I = P / V, assuming 230V Thai)
        demand_current = summary.get('demand_current')
        if demand_current is None:
            demand_current = total_watts / 230 if total_watts else 0
        demand_current = round_up(demand_current, 1)  # ปัดขึ้น 1 ตำแหน่ง
        
        design_current = round_up(demand_current * 1.25, 1)  # ปัดขึ้น 1 ตำแหน่ง
        
        # MCP Core sends num_loads in 'component_count.loads'
        component_count = summary.get('component_count') or {}
        num_loads = summary.get('num_loads') or component_count.get('loads', 0)
        
        return [
            "## สรุปโหลดไฟฟ้า",
            "",
            "| รายการ | ค่า |",
            "|--------|-----|",
            f"| กำลังไฟฟ้ารวม | **{total_watts:,.0f} W** ({total_watts/1000:.1f} kW) |",
            f"| กระแสโหลดรวม | **{demand_current:.1f} A** |",
            f"| Design Current (×1.25) | **{design_current:.1f} A** |",
            f"| จำนวนวงจร | **{num_loads}** |",
            "",
            "---",
            ""
        ]
    
    def _create_meter_section(self, summary: Dict) -> List[str]:
        """Create meter and main breaker section."""
        # 🆕 FIX: Calculate demand_current from total_load_va if not provided
        demand_current = summary.get('demand_current')
        if demand_current is None:
            total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
            demand_current = total_watts / 230 if total_watts else 0
        
        # Determine meter size
        if demand_current <= 15:
            meter = "5(15)A"
            main_wire = "THW 4 mm²"
            main_breaker = "16A/1P"
        elif demand_current <= 30:
            meter = "15(45)A"
            main_wire = "THW 10 mm²"
            main_breaker = "32A/2P"
        elif demand_current <= 50:
            meter = "30(100)A"
            main_wire = "THW 16 mm²"
            main_breaker = "50A/2P"
        else:
            meter = "50(150)A"
            main_wire = "THW 35 mm²"
            main_breaker = "100A/2P"
        
        return [
            "## 🔌 ขนาดมิเตอร์และสายเมน",
            "",
            "| 🏷️ อุปกรณ์ | 📐 ขนาด | 📝 หมายเหตุ |",
            "|------------|---------|-------------|",
            f"| 📟 มิเตอร์ไฟฟ้า | **{meter}** | ตามกระแสโหลดรวม |",
            f"| 🔌 สายเมนเข้าบ้าน | **{main_wire}** | 4 เส้น (L-N-E + สำรอง) |",
            f"| ⚡ Main Breaker | **{main_breaker}** | MCCB หรือ MCB |",
            "| 🌍 สายดิน | **THW 10 mm²** | สีเขียว/เหลือง |",
            "| 🔩 หลักดิน | **5/8\" x 8 ฟุต** | ค่าดิน ≤5Ω |",
            "",
            "---",
            ""
        ]
    
    def _create_legend(self) -> List[str]:
        """Create legend section - MUST be at top for user awareness."""
        return [
            "## 🏠 รายละเอียดแต่ละห้อง",
            "",
            "### 📖 คำอธิบายสัญลักษณ์",
            "",
            "| สัญลักษณ์ | ความหมาย |",
            "|:---------:|----------|",
            "| `*` | ค่า default โดยประมาณ - **ควรวัดจริงหน้างาน** |",
            "| 🔴 | **ห้ามพลาด!** ต้องติดตั้งตามที่ระบุ |",
            "| ⚠️ | เกินมาตรฐาน - ต้องแก้ไข |",
            "| ✅ | ผ่านมาตรฐาน |",
            "| RCBO | เบรกเกอร์กันดูด 30mA (บังคับใช้ในห้องน้ำ/ที่เปียก) |",
            "",
            "---",
            ""
        ]
    
    def _create_room_details(
        self, 
        loads: List[Dict], 
        wire_sizing: Dict,
        breaker_selections: Dict,
        conduit_sizing: Dict
    ) -> List[str]:
        """Create room-by-room Card-style details, grouped by floor."""
        lines = []
        
        # Group loads by floor → room
        floors: Dict[str, Dict[str, List[Dict]]] = {}
        for load in loads:
            location = load.get('location', {})
            floor = str(location.get('floor', '1'))
            room = location.get('room', NOT_SPECIFIED)
            
            if floor not in floors:
                floors[floor] = {}
            if room not in floors[floor]:
                floors[floor][room] = []
            floors[floor][room].append(load)
        
        # Sort floors numerically
        sorted_floors = sorted(floors.keys(), key=lambda x: (x.isdigit(), int(x) if x.isdigit() else 999, x))
        
        for floor in sorted_floors:
            rooms = floors[floor]
            
            # Floor header
            floor_display = f"ชั้น {floor}" if floor.isdigit() else floor
            floor_watts = sum(
                load.get('power_watts', 0) * load.get('quantity', 1)
                for room_loads in rooms.values()
                for load in room_loads
            )
            lines.append(f"## 🏢 {floor_display} (รวม {round_up(floor_watts):,.0f}W)")
            lines.append("")
            
            for room, room_loads in rooms.items():
                # Find room icon
                icon = '📍'
                for key, ico in self.ROOM_ICONS.items():
                    if key in room:
                        icon = ico
                        break
                
                # Calculate room total watts
                room_watts = sum(
                    load.get('power_watts', 0) * load.get('quantity', 1) 
                    for load in room_loads
                )
                
                lines.append(f"### {icon} {room} ({round_up(room_watts):,.0f}W)")
                lines.append("")
                
                has_default_distance = False
                
                for load in room_loads:
                    lid = load.get('id', '')
                    name = load.get('name', NOT_SPECIFIED)
                    power = load.get('power_watts', 0) * load.get('quantity', 1)
                    
                    # Get sizing info
                    w = wire_sizing.get(lid, {})
                    b = breaker_selections.get(lid, {})
                    c = conduit_sizing.get(lid, {})
                    
                    # Wire info
                    wire_awg = str(w.get('wire_size', '14'))
                    wire_mm = self.AWG_TO_MM2.get(wire_awg, wire_awg)
                    ground_awg = str(w.get('ground_size', '14'))
                    ground_mm = self.AWG_TO_MM2.get(ground_awg, ground_awg)
                    vd = w.get('voltage_drop_percent', 0)
                    
                    # Breaker info
                    breaker = b.get('breaker_rating', 15)
                    poles = b.get('poles', 1)
                    breaker_type = b.get('breaker_type', 'MCB')
                    
                    # Conduit info
                    conduit_size = c.get('conduit_size', '20mm')
                    fill_pct = c.get('fill_percentage', 0)
                    fill_ok = fill_pct <= 40
                    
                    # Distance info
                    distance_m = w.get('distance_m', 15)
                    is_default = w.get('used_default_distance', True)
                    distance_marker = '*' if is_default else ''
                    if is_default:
                        has_default_distance = True
                    
                    # Status indicators
                    poles_str = str(poles).replace('P', '')
                    vd_status = "✅" if vd <= 3 else "⚠️"
                    fill_status = "✅" if fill_ok else "⚠️"
                    
                    # Check if critical
                    is_critical = any(kw in name.lower() for kw in self.CRITICAL_KEYWORDS)
                    critical_marker = "🔴 " if is_critical else ""
                    
                    # Check wet area
                    is_wet_area = any(kw in room.lower() for kw in self.WET_AREA_KEYWORDS)
                    if is_wet_area and breaker_type == 'MCB':
                        breaker_type = 'RCBO'  # Force RCBO for wet areas
                    
                    # Card-style output
                    lines.append(f"#### {critical_marker}🔌 {name} ({power:,.0f}W)")
                    lines.append("")
                    lines.append("| หมวด | รายละเอียด |")
                    lines.append("|:----:|------------|")
                    lines.append(f"| 🔗 **สาย** | THW {wire_mm}mm² × {distance_m:.0f}m{distance_marker} → VD {vd:.1f}% {vd_status} |")
                    lines.append(f"| 🌍 **กราวด์** | THW {ground_mm}mm² (สีเขียว/เหลือง) |")
                    lines.append(f"| 🔘 **ท่อ** | PVC {conduit_size} (Fill {fill_pct:.0f}%) {fill_status} |")
                    lines.append(f"| ⚡ **เบรกเกอร์** | {breaker_type} {breaker}A/{poles_str}P |")
                    
                    # Add warning rows
                    if is_critical:
                        lines.append("| 🔴 **คำเตือน** | **ต้องใช้ RCBO 30mA + แยกวงจรเฉพาะ** |")
                    elif is_wet_area:
                        lines.append("| ⚠️ **หมายเหตุ** | พื้นที่เปียก - แนะนำ RCBO 30mA |")
                    
                    lines.append("")
                
                # Room footer
                if has_default_distance:
                    lines.append("> 📏 `*` = ระยะโดยประมาณ **ควรวัดจริงหน้างาน**")
                    lines.append("")
        
        return lines
    
    def _create_breaker_summary(self, breaker_selections: Dict) -> List[str]:
        """Create breaker summary table."""
        lines = [
            "---",
            "",
            "## 📋 สรุปเบรกเกอร์ที่ต้องใช้",
            "",
            "| 📐 ขนาด | 🔢 จำนวน | 📝 ใช้สำหรับ |",
            "|---------|---------|-------------|",
        ]
        
        usage_desc = {
            '15A/1P': 'ไฟ, เต้ารับทั่วไป, TV, ตู้เย็น',
            '15A/2P': 'แอร์ ≤12000BTU',
            '20A/1P': 'เครื่องใช้ไฟฟ้ากำลังสูง',
            '20A/2P': 'เครื่องทำน้ำอุ่น 3.5kW, เตา Induction',
            '25A/1P': 'กาต้มน้ำไฟฟ้า, เครื่องซักผ้า',
            '25A/2P': 'เครื่องทำน้ำอุ่น 4.5kW, เครื่องอบผ้า',
            '30A/2P': 'แอร์ขนาดใหญ่ ≥24000BTU'
        }
        
        # Count breakers
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
            desc = usage_desc.get(rating, 'อื่นๆ')
            lines.append(f"| **{rating}** | {count} ตัว | {desc} |")
        
        lines.append("")
        return lines
    
    def _create_safety_notes(self) -> List[str]:
        """Create safety notes section."""
        return [
            "---",
            "",
            "## ⚠️ ข้อควรระวังและคำแนะนำ",
            "",
            "| อุปกรณ์ | ข้อกำหนด | เหตุผล |",
            "|---------|----------|--------|",
            "| เครื่องทำน้ำอุ่น | ต้องใช้ **RCBO 30mA** | ป้องกันไฟดูด |",
            "| แอร์ทุกตัว | **แยกวงจรเฉพาะ** + เบรกเกอร์ 2P | โหลดสูง |",
            "| เตา Induction | วงจรเฉพาะ **20A + สาย 4mm²** | กำลังสูง |",
            "| ปั๊มน้ำ | ใช้ **Motor Starter + Overload** | ป้องกันมอเตอร์ |",
            ""
        ]
    
    def _create_warnings_section(self, warnings: List[str], errors: List[str]) -> List[str]:
        """Create warnings and errors section from MCP Core output.
        
        This displays:
        - Transformer distance warnings (kA rating adjustments)
        - Voltage drop warnings (default distance used)
        - Compliance issues
        """
        if not warnings and not errors:
            return []
        
        lines = [
            "---",
            "",
            "## ⚠️ คำเตือนจากระบบ",
            "",
        ]
        
        # Show errors first (more critical)
        if errors:
            lines.append("### ❌ ข้อผิดพลาด")
            lines.append("")
            for err in errors[:5]:  # Limit to 5
                lines.append(f"- {err}")
            lines.append("")
        
        # Show warnings
        if warnings:
            lines.append("### ⚠️ ข้อควรระวัง")
            lines.append("")
            for warn in warnings[:5]:  # Limit to 5
                lines.append(f"- {warn}")
            lines.append("")
        
        return lines

    
    def _create_compliance_section(self, mcp_result: Dict) -> List[str]:
        """Create compliance status section."""
        compliance = mcp_result.get('compliance_report', {})
        is_compliant = compliance.get('compliant', True)
        
        status = "✅ ผ่านมาตรฐาน" if is_compliant else "⚠️ มีข้อควรปรับปรุง"
        
        lines = [
            "---",
            "",
            "## 📋 สถานะการตรวจสอบมาตรฐาน",
            "",
            f"**สถานะ:** {status}",
            "",
            "| มาตรฐาน | เกณฑ์ | สถานะ |",
            "|---------|-------|-------|",
            "| NEC 210.19(A) | Voltage Drop ≤3% | ตรวจสอบแล้ว |",
            "| NEC Article 310 | Wire Sizing | ตรวจสอบแล้ว |",
            "| NEC Article 240 | Breaker Rating | ตรวจสอบแล้ว |",
            "| NEC Chapter 9 | Conduit Fill ≤40% | ตรวจสอบแล้ว |",
            "| วสท. 2564 | VD มาตรฐานไทย | ตรวจสอบแล้ว |",
            "",
            "---",
            "",
            "*รายงานนี้สร้างโดยอัตโนมัติจาก MCP Core v2.0*"
        ]
        
        return lines


# Convenience function
def format_design_report(mcp_result: Dict[str, Any]) -> str:
    """
    Quick function to format MCP result as Markdown.
    
    Args:
        mcp_result: Dictionary from MCP Core export_to_dict()
        
    Returns:
        Formatted Markdown string
    """
    formatter = MarkdownFormatter()
    return formatter.format(mcp_result)
