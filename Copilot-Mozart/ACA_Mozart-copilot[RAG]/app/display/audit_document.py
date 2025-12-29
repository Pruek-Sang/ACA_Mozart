"""
Audit Document Renderer - PDF-Ready Formal Audit Document

This module renders DisplayData + audit_results into a formal PDF-ready document.
It reads from compute.py (DisplayData) and audit_validator.py results.

[CP-AUDIT-DOC] Checkpoint prefix for all audit document logs.

Output Format:
- Header (Project, Date, Standard)
- Audit Results Table (Check, User Value, Recommended, Status)
- Warnings Section (collected from injectors)
- Footer (Reviewer, Notes)
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

logger = logging.getLogger("Aura.Display.AuditDoc")


def render_audit_document(
    display_data: Dict[str, Any],
    audit_results: List[Dict[str, Any]],
    project_name: Optional[str] = None
) -> str:
    """
    [CP-AUDIT-DOC] Render formal audit document (PDF-ready Markdown).
    
    Args:
        display_data: DisplayData from compute.py
        audit_results: Results from audit_validator.validate_user_specs()
        project_name: Optional override for project name
    
    Returns:
        Markdown string ready for PDF conversion
    """
    logger.info("[CP-AUDIT-DOC] Rendering formal audit document...")
    
    lines: List[str] = []
    
    # Header
    lines.extend(_render_header(display_data, project_name))
    
    # Audit Results Table
    if audit_results:
        lines.extend(_render_audit_table(audit_results))
    else:
        lines.extend([
            "## ผลการตรวจสอบ",
            "",
            "> ไม่มีรายการที่ต้องตรวจสอบ (ผู้ใช้ไม่ได้ระบุค่าเอง)",
            "",
        ])
    
    # Warnings Section
    warnings = display_data.get('warnings', [])
    if warnings:
        lines.extend(_render_warnings(warnings))
    
    # Summary
    lines.extend(_render_summary(display_data, audit_results))
    
    # Footer
    lines.extend(_render_footer())
    
    result = "\n".join(lines)
    logger.info(f"[CP-AUDIT-DOC] Rendered {len(lines)} lines")
    
    return result


def _render_header(data: Dict[str, Any], project_name: Optional[str]) -> List[str]:
    """Render document header."""
    today = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y %H:%M")
    name = project_name or data.get('project_name', 'ไม่ระบุ')
    
    return [
        "# 📋 รายงานการตรวจสอบระบบไฟฟ้า",
        "",
        "| ข้อมูล | รายละเอียด |",
        "|--------|------------|",
        f"| โครงการ | {name} |",
        f"| วันที่ตรวจสอบ | {today} |",
        f"| มาตรฐานอ้างอิง | วสท. 2564 / NEC 2020 |",
        f"| โหลดรวม | {data.get('total_kw', 0):.2f} kW |",
        f"| กระแสรวม | {data.get('demand_current', 0):.1f} A |",
        "",
        "---",
        "",
    ]


def _render_audit_table(results: List[Dict[str, Any]]) -> List[str]:
    """Render audit results table."""
    lines = [
        "## ผลการตรวจสอบ",
        "",
        "| รายการตรวจสอบ | ค่าที่ระบุ | ค่าแนะนำ | ผล |",
        "|---------------|----------|---------|:--:|",
    ]
    
    pass_count = 0
    fail_count = 0
    warn_count = 0
    
    for row in results:
        check = row.get('check', row.get('circuit_name', 'Unknown'))
        user_val = row.get('user_value', '-')
        rec_val = row.get('recommended_value', row.get('auto_value', '-'))
        status = row.get('status', 'PASS')
        
        # Format status with emoji
        if status == 'PASS':
            status_str = '✅ PASS'
            pass_count += 1
        elif status == 'FAIL':
            status_str = '❌ FAIL'
            fail_count += 1
        else:
            status_str = '⚠️ WARN'
            warn_count += 1
        
        lines.append(f"| {check} | {user_val} | {rec_val} | {status_str} |")
    
    lines.extend([
        "",
        f"**สรุป:** ✅ PASS: {pass_count} | ❌ FAIL: {fail_count} | ⚠️ WARN: {warn_count}",
        "",
    ])
    
    return lines


def _render_warnings(warnings: List[str]) -> List[str]:
    """Render warnings section."""
    lines = [
        "## ⚠️ ข้อควรระวัง",
        "",
    ]
    
    for i, warn in enumerate(warnings[:10], 1):  # Limit to 10
        lines.append(f"{i}. {warn}")
    
    if len(warnings) > 10:
        lines.append(f"_...และอีก {len(warnings) - 10} รายการ_")
    
    lines.append("")
    return lines


def _render_summary(data: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
    """Render summary section."""
    total_checks = len(results)
    fail_checks = sum(1 for r in results if r.get('status') == 'FAIL')
    
    overall = "✅ ผ่านการตรวจสอบ" if fail_checks == 0 else "❌ ต้องแก้ไข"
    
    return [
        "## สรุปผล",
        "",
        f"- รายการตรวจสอบทั้งหมด: **{total_checks}** รายการ",
        f"- รายการที่ไม่ผ่าน: **{fail_checks}** รายการ",
        f"- ผลสรุป: **{overall}**",
        "",
        "---",
        "",
    ]


def _render_footer() -> List[str]:
    """Render document footer."""
    today = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y")
    
    return [
        "## ลายเซ็น",
        "",
        "| | |",
        "|---|---|",
        "| ผู้ตรวจสอบ | ______________________ |",
        f"| วันที่ | {today} |",
        "",
        "---",
        "",
        "_เอกสารนี้สร้างโดย Mozart System | วสท. 2564 | NEC 2020_",
    ]


def format_audit_for_frontend(audit_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format audit results for Frontend display (AuditRow format).
    
    Maps backend audit_results to frontend-expected format.
    """
    formatted = []
    
    for row in audit_results:
        formatted.append({
            'check': row.get('check', row.get('circuit_name', 'Unknown')),
            'user_value': str(row.get('user_value', '-')),
            'recommended_value': str(row.get('recommended_value', row.get('auto_value', '-'))),
            'status': row.get('status', 'PASS'),
        })
    
    return formatted
