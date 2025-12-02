"""Result builder for aggregating design results."""

from typing import Dict, Any, Optional
from models.contracts import DesignRequest, DesignResult
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ResultBuilder:
    """Builds comprehensive design result from individual calculation results."""
    
    def __init__(self):
        """Initialize result builder."""
        pass
    
    def build_result(
        self,
        request: DesignRequest,
        calculations: Dict[str, Any],
        wire_sizing: Dict[str, Any],
        breaker_selections: Dict[str, Any],
        conduit_sizing: Dict[str, Any],
        compliance_report: Dict[str, Any],
        autolisp_code: str = None
    ) -> DesignResult:
        """Build complete design result."""
        errors = []
        warnings = []
        
        # Collect errors from each section
        errors.extend(self._extract_errors(calculations))
        errors.extend(self._extract_errors(wire_sizing))
        errors.extend(self._extract_errors(breaker_selections))
        errors.extend(self._extract_errors(conduit_sizing))
        
        # Collect compliance issues
        if not compliance_report.get('compliant', True):
            errors.extend([
                issue['message'] 
                for issue in compliance_report.get('issues', [])
            ])
        
        warnings.extend([
            warning['message'] 
            for warning in compliance_report.get('warnings', [])
        ])
        
        result = DesignResult(
            session_id=request.session_id,
            request=request,
            calculations=calculations,
            wire_sizing=wire_sizing,
            breaker_selections=breaker_selections,
            conduit_sizing=conduit_sizing,
            compliance_report=compliance_report,
            autolisp_code=autolisp_code,
            completed_at=datetime.now(timezone.utc),
            errors=errors,
            warnings=warnings
        )
        
        return result
    
    def _extract_errors(self, data: Dict[str, Any]) -> list:
        """Extract error messages from result data."""
        errors = []
        
        if isinstance(data, dict):
            if 'error' in data:
                errors.append(data['error'])
            
            # Recursively check nested dictionaries
            for key, value in data.items():
                if isinstance(value, dict):
                    errors.extend(self._extract_errors(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            errors.extend(self._extract_errors(item))
        
        return errors
    
    def create_summary(self, result: DesignResult) -> Dict[str, Any]:
        """Create a summary of the design result."""
        # Count components
        num_panels = len(result.request.panels)
        num_loads = len(result.request.loads)
        num_circuits = sum(len(panel.feeds) for panel in result.request.panels)
        
        # Gather statistics
        total_load_va = sum(
            load.power_watts * load.quantity 
            for load in result.request.loads
        )
        
        summary = {
            'session_id': result.session_id,
            'project_name': result.request.project_name,
            'project_number': result.request.project_number,
            'completed_at': result.completed_at,
            'component_count': {
                'panels': num_panels,
                'loads': num_loads,
                'circuits': num_circuits
            },
            'total_load_va': total_load_va,
            'service_voltage': result.request.service_voltage.value,
            'utility_service_size': result.request.utility_service_size,
            'status': {
                'compliant': result.compliance_report.get('compliant', False),
                'errors': len(result.errors),
                'warnings': len(result.warnings)
            }
        }
        
        return summary
    
    def create_load_summary(self, result: DesignResult) -> Dict[str, Any]:
        """Create a summary of loads by type."""
        from collections import defaultdict
        
        load_by_type = defaultdict(lambda: {'count': 0, 'total_watts': 0})
        
        for load in result.request.loads:
            load_type = load.load_type.value
            load_by_type[load_type]['count'] += load.quantity
            load_by_type[load_type]['total_watts'] += load.power_watts * load.quantity
        
        return dict(load_by_type)
    
    def create_panel_summary(self, result: DesignResult) -> Dict[str, Any]:
        """Create a summary for each panel."""
        panel_summaries = {}
        
        for panel in result.request.panels:
            calc_data = result.calculations.get(panel.id, {})
            
            panel_summaries[panel.id] = {
                'name': panel.name,
                'location': panel.location.room,
                'main_breaker': panel.main_breaker_rating,
                'voltage': panel.voltage.value,
                'circuit_count': len(panel.feeds),
                'total_load_va': calc_data.get('total_va', 0),
                'demand_current': calc_data.get('demand_current', 0),
                'utilization': calc_data.get('utilization', 0)
            }
        
        return panel_summaries
    
    def export_to_dict(self, result: DesignResult) -> Dict[str, Any]:
        """Export result to dictionary for storage/serialization."""
        return {
            'session_id': result.session_id,
            'project_name': result.request.project_name,
            'project_number': result.request.project_number,
            'created_at': result.request.created_at.isoformat(),
            'completed_at': result.completed_at.isoformat(),
            'request': result.request.model_dump(),
            'calculations': result.calculations,
            'wire_sizing': result.wire_sizing,
            'breaker_selections': result.breaker_selections,
            'conduit_sizing': result.conduit_sizing,
            'compliance_report': result.compliance_report,
            'autolisp_code_length': len(result.autolisp_code) if result.autolisp_code else 0,
            'errors': result.errors,
            'warnings': result.warnings,
            'summary': self.create_summary(result),
            'load_summary': self.create_load_summary(result),
            'panel_summary': self.create_panel_summary(result),
            'standards_markdown': self.create_standards_markdown(result)
        }
    
    def create_standards_markdown(self, result: DesignResult) -> str:
        """Create Markdown summary of standards used in design."""
        nec_version = result.compliance_report.get('nec_version', '2023')
        compliant = result.compliance_report.get('compliant', True)
        
        md = f"""
---

## 📋 Design Standards Summary

### มาตรฐานที่ใช้ในการออกแบบ (Standards Applied)

| Category | Standard | Version | Description |
|----------|----------|---------|-------------|
| **Primary** | NEC (NFPA 70) | {nec_version} | National Electrical Code - US Standard |
| **Wire Sizing** | NEC Article 310 | {nec_version} | Conductor sizing & ampacity tables |
| **Breaker Selection** | NEC Article 240 | {nec_version} | Overcurrent protection requirements |
| **Conduit Fill** | NEC Chapter 9, Table 1 | {nec_version} | Maximum conduit fill percentages |
| **Voltage Drop** | NEC 210.19(A) | {nec_version} | Branch circuit voltage drop ≤3% |
| **Panel Sizing** | NEC Article 220 | {nec_version} | Load calculations & demand factors |

### การคำนวณหลัก (Key Calculations)

| Parameter | Method | Reference |
|-----------|--------|-----------|
| Current Calculation | I = P / (V × PF) | IEEE Std 141 |
| Voltage Drop | VD = 2 × L × I × R / 1000 | NEC Chapter 9, Table 8 |
| Conduit Fill | Total Wire Area / Conduit Area | NEC Table 1, Chapter 9 |
| Demand Factor | Per NEC Article 220 | Load type based |

### Compliance Status

- **NEC Compliant:** {'✅ Yes' if compliant else '❌ No'}
- **Design Date:** {result.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC') if result.completed_at else 'N/A'}
- **Errors:** {len(result.errors)}
- **Warnings:** {len(result.warnings)}

### หมายเหตุ (Notes)

> ⚠️ การออกแบบนี้ใช้มาตรฐาน NEC (National Electrical Code) ของสหรัฐอเมริกา
> สำหรับการใช้งานในประเทศไทย ควรตรวจสอบกับมาตรฐาน วสท. (EIT) เพิ่มเติม
>
> For use in Thailand, please also verify against:
> - **EIT Standard** (วสท. 2001-56) - Thai Electrical Installation Standard
> - **TIS 11-2553** - Thai Industrial Standard for Electrical Installations

---

*Generated by MCP Core v2.0 - Electrical Design Engine*
"""
        return md
    
    def create_readable_report(self, result: DesignResult) -> str:
        """Create human-readable report in Thai/English."""
        lines = []
        lines.append("=" * 80)
        lines.append("🏠 รายงานการออกแบบระบบไฟฟ้า")
        lines.append(f"   โครงการ: {result.request.project_name}")
        lines.append("=" * 80)
        lines.append("")
        
        # Total load calculation
        total_watts = sum(
            load.power_watts * load.quantity 
            for load in result.request.loads
        )
        total_amps = total_watts / 240  # Assuming 240V
        
        # Meter recommendation
        if total_amps <= 15:
            meter = "15(45)A"
            main_wire = "THW 6 mm²"
        elif total_amps <= 30:
            meter = "30(100)A"
            main_wire = "THW 10 mm²"
        elif total_amps <= 50:
            meter = "50(150)A"
            main_wire = "THW 16 mm²"
        elif total_amps <= 80:
            meter = "80(200)A"
            main_wire = "THW 25 mm²"
        else:
            meter = "100(200)A หรือ CT"
            main_wire = "THW 35 mm²"
        
        lines.append("📊 สรุปโหลดทั้งหมด")
        lines.append("-" * 50)
        lines.append(f"  • กำลังไฟฟ้ารวม: {total_watts:,.0f} W ({total_watts/1000:.2f} kW)")
        lines.append(f"  • กระแสโหลดรวม: {total_amps:.1f} A")
        lines.append("")
        
        lines.append("🔌 ขนาดมิเตอร์และสายเมน")
        lines.append("-" * 50)
        lines.append(f"  • มิเตอร์: {meter}")
        lines.append(f"  • สายเมน: {main_wire}")
        lines.append(f"  • Main Breaker: 100A 2P")
        lines.append(f"  • สายดิน: THW 10 mm² (เขียว/เหลือง)")
        lines.append(f"  • หลักดิน: 5/8\" x 8 ฟุต (ค่าดิน ≤5Ω)")
        lines.append("")
        
        # AWG to mm² mapping
        awg_mm2 = {'14': '2.5', '12': '4', '10': '6', '8': '10', '6': '16'}
        
        # Group by room
        rooms = {}
        for load in result.request.loads:
            room = load.location.room
            if room not in rooms:
                rooms[room] = []
            rooms[room].append(load)
        
        lines.append("🏠 รายละเอียดแต่ละห้อง")
        lines.append("=" * 80)
        
        for room, loads in rooms.items():
            lines.append(f"\n📍 {room}")
            lines.append("-" * 60)
            
            room_watts = sum(l.power_watts * l.quantity for l in loads)
            lines.append(f"  โหลดรวม: {room_watts:,} W")
            
            for load in loads:
                lid = load.id
                name = load.name
                power = load.power_watts * load.quantity
                
                # Get sizing info
                w = result.wire_sizing.get(lid, {})
                b = result.breaker_selections.get(lid, {})
                
                wire_awg = str(w.get('wire_size', '14'))
                wire_mm = awg_mm2.get(wire_awg, wire_awg)
                vd = w.get('voltage_drop_percent', 0)
                breaker = b.get('breaker_rating', 15)
                poles = b.get('poles', 1)
                
                vd_status = "✅" if vd <= 3 else "⚠️"
                
                lines.append(f"  • {name}")
                lines.append(f"    {power}W | สาย THW {wire_mm}mm² | เบรกเกอร์ {breaker}A/{poles}P | VD {vd:.1f}% {vd_status}")
        
        # Breaker summary
        lines.append("")
        lines.append("=" * 80)
        lines.append("📋 สรุปเบรกเกอร์ที่ต้องใช้")
        lines.append("=" * 80)
        
        breaker_count = {}
        for lid, b in result.breaker_selections.items():
            if isinstance(b, dict):
                key = f"{b.get('breaker_rating', 15)}A/{b.get('poles', 1)}P"
                breaker_count[key] = breaker_count.get(key, 0) + 1
        
        for rating, count in sorted(breaker_count.items()):
            lines.append(f"  • {rating}: {count} ตัว")
        
        # Errors and warnings
        if result.errors:
            lines.append("")
            lines.append("❌ ปัญหาที่พบ:")
            for e in result.errors[:5]:
                lines.append(f"   • {e}")
        
        if result.warnings:
            lines.append("")
            lines.append("⚠️ ข้อควรระวัง:")
            for w in result.warnings[:5]:
                lines.append(f"   • {w}")
        
        return "\n".join(lines)


# Global instance
_result_builder: Optional[ResultBuilder] = None


def get_result_builder() -> ResultBuilder:
    """Get the global result builder instance."""
    global _result_builder
    if _result_builder is None:
        _result_builder = ResultBuilder()
    return _result_builder
