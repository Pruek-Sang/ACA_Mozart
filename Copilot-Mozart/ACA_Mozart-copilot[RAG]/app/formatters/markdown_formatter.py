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
    
    # Wet area keywords (require RCBO for safety)
    # Note: Kitchen removed - not all kitchen items need RCBO, only those near water
    WET_AREA_KEYWORDS = ['ห้องน้ำ', 'ซักล้าง', 'bathroom', 'laundry', 'outdoor', 'ภายนอก', 'ระเบียง']
    
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
        grouped_circuits = mcp_result.get('grouped_circuits') or []  # Circuit groups from MCP
        conduit_sizing = mcp_result.get('conduit_sizing') or {}  # 🆕 Conduit sizing from MCP
        warnings = mcp_result.get('warnings') or []
        errors = mcp_result.get('errors') or []
        
        # Build report sections
        lines.extend(self._create_header(project_name, summary))
        lines.extend(self._create_main_equipment(summary))
        
        # Use grouped_circuits if available, else fall back to raw loads
        if grouped_circuits:
            lines.extend(self._create_circuit_schedule(grouped_circuits, wire_sizing, conduit_sizing))
            lines.extend(self._create_circuit_breaker_summary(grouped_circuits))
        else:
            # Legacy: use raw loads (backward compatibility)
            request = mcp_result.get('request') or {}
            loads = request.get('loads') or [] if isinstance(request, dict) else []
            lines.extend(self._create_load_schedule(loads, wire_sizing, breaker_selections))
            lines.extend(self._create_breaker_summary(breaker_selections))
        
        # 🆕 Collect circuits using default distance for Summary
        default_circuits = []
        for cid, w in wire_sizing.items():
            if w.get('used_default_distance', False):
                # Try to map ID to name if possible, or use ID
                # (Simple lookup from grouped_circuits would be better but expensive here)
                # We'll use the ID or try to find name in grouped_circuits
                c_name = cid
                for c in grouped_circuits:
                    if c.get('circuit_id') == cid or c.get('id') == cid:
                        c_name = c.get('circuit_name', cid)
                        break
                default_circuits.append(c_name)
        
        lines.extend(self._create_notes_section(warnings, errors, default_circuits))
        lines.extend(self._create_footer())
        
        return "\n".join(lines)
    
    def _create_header(self, project_name: str, summary: Dict) -> List[str]:
        """Create professional header with project info."""
        # 🆕 FIX: Use Thailand timezone instead of UTC
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y")
        
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
        """Create main equipment sizing section.
        
        Thai MEA Meter Sizing (มาตรฐาน กฟน./กฟภ.):
        - 5(15)A   : โหลด ≤3.5 kW (≤15A)
        - 15(45)A  : โหลด ≤10 kW (≤45A)  
        - 30(100)A : โหลด ≤23 kW (≤100A) - สูงสุดสำหรับมิเตอร์ธรรมดา
        - CT Meter : โหลด >23 kW (>100A) - ต้องใช้หม้อแปลงกระแส
        
        Note: demand_current คือกระแสรวม (ไม่ใช่ design current ×1.25)
        """
        demand_current = summary.get('demand_current')
        if demand_current is None:
            total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
            demand_current = total_watts / 230 if total_watts else 0
        
        # Determine sizes based on Thai MEA standards
        # 🆕 FIX: Corrected meter sizing thresholds
        if demand_current <= 15:
            meter, main_wire, main_cb = "5(15)A", "4 mm²", "16A/1P"
        elif demand_current <= 45:
            meter, main_wire, main_cb = "15(45)A", "10 mm²", "50A/2P"
        elif demand_current <= 100:
            # 30(100)A meter for demand up to 100A
            meter, main_wire, main_cb = "30(100)A", "25 mm²", "100A/2P"
        else:
            # >100A requires CT meter
            meter, main_wire, main_cb = "CT Meter", "50 mm²", "125A/2P"
        
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
                
                # Current - use provided value if available
                current = b.get('total_current', power / 230 if power > 0 else 0)
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
            '16A/1P': 'เต้ารับ',
            '20A/1P': 'เครื่องใช้ไฟฟ้าสูง',
            '20A/2P': 'น้ำอุ่น 3.5kW, เตา, ปั๊มน้ำ',
            '25A/2P': 'น้ำอุ่น 4.5kW',
            '30A/2P': 'แอร์ ≥24000BTU, น้ำอุ่น 5-6kW',
            '32A/2P': 'แอร์ขนาดใหญ่, น้ำอุ่น ≥6kW',
            '40A/2P': 'แอร์ขนาดใหญ่มาก',
            '50A/2P': 'วงจรหลัก',
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
    
    def _create_notes_section(self, warnings: List[str], errors: List[str], default_circuits: List[str] = None) -> List[str]:
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
        if warnings or errors or default_circuits:
            lines.append("### คำเตือนจากระบบ")
            lines.append("")
            
            # Show Errors first
            for err in errors[:3]:
                lines.append(f"- ❌ {err}")
            
            # 🆕 FIX: Consolidate duplicate warnings & prioritize critical ones
            critical_keywords = ["kA", "หม้อแปลง", "N-G", "Sub-panel", "RCBO", "≥10", "SUB-PANEL"]
            critical_warns = [w for w in warnings if any(kw in w for kw in critical_keywords)]
            other_warns = [w for w in warnings if w not in critical_warns]
            
            # Show critical warnings first (all of them)
            for warn in critical_warns:
                lines.append(f"- ⚠️ {warn}")
            
            # Filter other warnings
            vd_warns = [w for w in other_warns if "VD" in w or "Voltage Drop" in w or "ระยะ Default" in w]
            afci_warns = [w for w in other_warns if "AFCI" in w]
            remaining_warns = [w for w in other_warns if w not in vd_warns and w not in afci_warns]
            
            # 🆕 Show consolidated VD warning with specific circuit names from wire_sizing check
            if default_circuits:
                # Limit to 5 names to avoid spam
                examples = ", ".join(default_circuits[:5])
                more_count = len(default_circuits) - 5
                more_text = f" และอีก {more_count} วงจร" if more_count > 0 else ""
                lines.append(f"- ℹ️ **Voltage Drop:** มี {len(default_circuits)} วงจร ใช้ระยะ Default (เช่น {examples}{more_text}) → **ควรตรวจสอบระยะจริงหน้างาน**")
            elif vd_warns:
                # Fallback if default_circuits not passed but warnings exist
                lines.append(f"- ℹ️ Voltage Drop: พบวงจรที่ใช้ระยะ Default หรือมีแรงดันตกเกิน (ควรระบุระยะจริง)")
            
            # Show consolidated AFCI warning
            if afci_warns:
                lines.append(f"- ⚠️ AFCI Protection: มี {len(afci_warns)} วงจร ที่แนะนำติดตั้ง AFCI (ตาม NEC)")
            
            # Show remaining unique warnings (up to 5)
            for warn in remaining_warns[:5]:
                lines.append(f"- ⚠️ {warn}")
            lines.append("")
        
        return lines
    
    def _create_circuit_schedule(
        self, 
        grouped_circuits: List[Dict], 
        wire_sizing: Dict[str, Any] = None,
        conduit_sizing: Dict[str, Any] = None  # 🆕 Added conduit sizing
    ) -> List[str]:
        """Create circuit-based load schedule using grouped_circuits from MCP.
        
        This shows circuits (grouped loads) instead of individual loads.
        Each circuit has: name, total_watts, breaker_rating, wire_size, etc.
        VD% is read from wire_sizing dict, NOT from grouped_circuits.
        GRD and conduit are read from wire_sizing and conduit_sizing.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        wire_sizing = wire_sizing or {}
        conduit_sizing = conduit_sizing or {}
        lines = ["## ตารางวงจร (Circuit Schedule)", ""]
        
        # Group circuits by floor
        floors: Dict[str, List[Dict]] = {}
        for circuit in grouped_circuits:
            floor = circuit.get('floor', '1')
            if floor not in floors:
                floors[floor] = []
            floors[floor].append(circuit)
        
        # Sort floors
        sorted_floors = sorted(floors.keys(), key=lambda x: (x.isdigit(), int(x) if x.isdigit() else 999, x))
        
        circuit_num = 1
        
        for floor in sorted_floors:
            floor_circuits = floors[floor]
            floor_display = f"ชั้น {floor}" if floor.isdigit() else floor
            
            # Calculate floor total
            floor_watts = sum(c.get('total_watts', 0) for c in floor_circuits)
            
            # Floor header
            lines.append(f"### {floor_display} (รวม {round_up(floor_watts):,.0f} W)")
            lines.append("")
            
            # Table header with GRD, ท่อ, Ic columns
            lines.append("| # | วงจร | โหลด | kW | A | สาย | GRD | ท่อ | CB | Ic | VD% | หมายเหตุ |")
            lines.append("|:-:|------|------|----:|---:|-----|-----|-----|-----|:--:|----:|----------|")
            
            for circuit in floor_circuits:
                ckt_name = circuit.get('circuit_name', circuit.get('name', 'Unknown'))
                total_watts = round_up(circuit.get('total_watts', 0))
                total_current = round_up(circuit.get('total_current', 0), 1)
                breaker_rating = circuit.get('breaker_rating', 15)
                breaker_poles = circuit.get('breaker_poles', 1)
                wire_size = circuit.get('wire_size', '2.5')
                requires_rcbo = circuit.get('requires_rcbo', False)
                num_loads = circuit.get('loads', 0)
                if isinstance(num_loads, list):
                    num_loads = len(num_loads)
                notes = circuit.get('notes', [])
                
                # VD% - Read directly from circuit (injected by service.py)
                circuit_id = circuit.get('circuit_id') or circuit.get('id') or ckt_name
                vd_data = wire_sizing.get(circuit_id, {})
                vd = circuit.get('voltage_drop_percent', 2.0)
                
                # 🆕 Debug logging for VD source tracking
                is_default_vd = abs(vd - 2.0) < 0.001  # Compare with epsilon
                if is_default_vd:
                    logger.debug(f"[VD-DEBUG] Circuit '{ckt_name}' using default VD 2.0 (not found in wire_sizing)")
                else:
                    logger.debug(f"[VD-DEBUG] Circuit '{ckt_name}' VD={vd:.2f}% from wire_sizing")
                
                # Breaker type
                breaker_type = "RCBO" if requires_rcbo else "MCB"
                cb_display = f"{breaker_type} {breaker_rating}A/{breaker_poles}P"
                
                # 🆕 GRD (ground wire size) from wire_sizing
                grd_size = vd_data.get('ground_size', '2.5') if isinstance(vd_data, dict) else '2.5'
                
                # 🆕 Conduit (ท่อ) from conduit_sizing
                conduit_data = conduit_sizing.get(circuit_id, {})
                conduit_size = conduit_data.get('trade_size', '1/2"') if isinstance(conduit_data, dict) else '1/2"'
                
                # 🆕 Ic (kA) - default 6kA, can be upgraded by ka_rating_injector
                ic_ka = 6  # Default interrupting capacity
                
                # Note
                note_str = ""
                if requires_rcbo:
                    note_str = "**RCBO 30mA**"
                elif notes:
                    note_str = notes[0][:15] if notes else ""
                
                # Shorten name (increased limit for readability)
                name_short = ckt_name[:25] + "..." if len(ckt_name) > 28 else ckt_name
                loads_str = f"({num_loads} โหลด)" if num_loads > 1 else ""
                
                # Convert W to kW for display
                kw_display = total_watts / 1000
                
                lines.append(
                    f"| {circuit_num} | {name_short} | {loads_str} | "
                    f"{kw_display:.2f} | {total_current:.1f} | {wire_size}mm² | "
                    f"{grd_size}mm² | {conduit_size} | {cb_display} | {ic_ka} | {vd:.1f} | {note_str} |"
                )
                circuit_num += 1
            
            lines.append("")
        
        return lines
    
    def _create_circuit_breaker_summary(self, grouped_circuits: List[Dict]) -> List[str]:
        """Create breaker count summary from grouped_circuits."""
        lines = [
            "---",
            "",
            "## สรุปเบรกเกอร์",
            "",
            "| ขนาด | จำนวน | วงจร |",
            "|------|:-----:|------|",
        ]
        
        # Count breakers and collect circuit names
        breaker_info: Dict[str, Dict] = {}
        for circuit in grouped_circuits:
            rating = circuit.get('breaker_rating', 15)
            poles = circuit.get('breaker_poles', 1)
            ckt_name = circuit.get('circuit_name', circuit.get('name', 'Unknown'))
            
            if rating > 100:
                continue
            
            key = f"{rating}A/{poles}P"
            if key not in breaker_info:
                breaker_info[key] = {'count': 0, 'circuits': []}
            breaker_info[key]['count'] += 1
            breaker_info[key]['circuits'].append(ckt_name[:20])  # Increased from 12 to 20
        
        for rating, info in sorted(breaker_info.items()):
            circuits_str = ", ".join(info['circuits'][:3])
            if len(info['circuits']) > 3:
                circuits_str += f" (+{len(info['circuits'])-3})"
            lines.append(f"| {rating} | {info['count']} | {circuits_str} |")
        
        lines.append("")
        return lines
    
    def _create_footer(self) -> List[str]:
        """Create professional footer with disclaimer."""
        # 🆕 FIX: Use Thailand timezone instead of UTC
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y %H:%M")
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
            "> 📝 **หมายเหตุ:** ตารางโหลดนี้ออกแบบตามมาตรฐาน วสท. 2564 เพื่อความปลอดภัยสูงสุด "
            "ผู้รับเหมาสามารถปรับแก้ได้ตามดุลยพินิจและข้อตกลงกับเจ้าของบ้าน",
            "",
            "---",
            "",
            f"*สร้างโดย Mozart Electrical Design | {today}*",
        ]


# Convenience function
def format_design_report(mcp_result: Dict[str, Any]) -> str:
    """Quick function to format MCP result as Markdown."""
    formatter = MarkdownFormatter()
    return formatter.format(mcp_result)
