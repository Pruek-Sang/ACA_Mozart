"""
Full Report Builder - Combine all display modules into one PDF-ready document

This module creates a comprehensive work package with:
- Cover page
- Table of Contents
- Load Schedule
- SLD Diagram
- BOQ
- Audit Summary
- Assumptions

Author: Fixia
Date: 2026-01-03
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("Aura.FullReport")


class ReportSection(TypedDict):
    """A section in the report"""
    id: str
    title: str
    content: str  # Markdown content
    page_break_before: bool


class CoverPageData(TypedDict):
    """Cover page information"""
    project_name: str
    client_name: Optional[str]
    building_type: str
    address: Optional[str]
    prepared_by: str
    date: str
    version: int


class FullReportData(TypedDict):
    """Complete report package"""
    cover: CoverPageData
    sections: List[ReportSection]
    generated_at: str
    total_pages_estimate: int


def generate_cover_page(
    project_name: str,
    building_type: str,
    version: int = 1,
    client_name: Optional[str] = None,
    address: Optional[str] = None,
    prepared_by: str = "Mozart AI"
) -> str:
    """Generate cover page Markdown."""
    date_str = datetime.now().strftime("%d/%m/%Y")
    
    lines = [
        "<!--COVER_PAGE-->",
        "",
        "# 📋 รายงานการออกแบบระบบไฟฟ้า",
        "",
        "---",
        "",
        f"## {project_name}",
        "",
        f"**ประเภทอาคาร:** {building_type}",
    ]
    
    if client_name:
        lines.append(f"**ลูกค้า:** {client_name}")
    if address:
        lines.append(f"**ที่อยู่:** {address}")
    
    lines.extend([
        "",
        "---",
        "",
        f"**จัดทำโดย:** {prepared_by}",
        f"**วันที่:** {date_str}",
        f"**เวอร์ชัน:** v{version}",
        "",
        "---",
        "",
        "*เอกสารนี้จัดทำโดยระบบ Mozart AI*",
        "*ควรตรวจสอบโดยวิศวกรผู้มีสิทธิ์ก่อนนำไปใช้งาน*",
        "",
    ])
    
    return "\n".join(lines)


def generate_toc(sections: List[ReportSection]) -> str:
    """Generate Table of Contents Markdown."""
    lines = [
        "# 📑 สารบัญ",
        "",
        "| หมวด | หน้า |",
        "|------|------|",
    ]
    
    page = 2  # Start after cover
    for section in sections:
        lines.append(f"| {section['title']} | {page} |")
        # Estimate pages per section (rough)
        content_length = len(section['content'])
        pages = max(1, content_length // 2000)
        page += pages
    
    lines.append("")
    return "\n".join(lines)


def generate_load_schedule_section(display_data: Dict[str, Any]) -> ReportSection:
    """Generate Load Schedule section."""
    circuits = display_data.get('circuits', [])
    
    lines = [
        "# ⚡ ตารางโหลด (Load Schedule)",
        "",
        "## สรุปโหลดรวม",
        "",
        f"- **วงจรทั้งหมด:** {len(circuits)} วงจร",
        f"- **โหลดรวม:** {display_data.get('total_kw', 0):.2f} kW",
        f"- **Main Breaker:** {display_data.get('main_breaker', '-')}A",
        f"- **Demand Factor:** {display_data.get('demand_factor', 0.78) * 100:.0f}%",
        "",
        "## รายละเอียดวงจร",
        "",
        "| # | วงจร | VA | Breaker | Wire | VD% |",
        "|---|------|----|---------|----|-----|",
    ]
    
    for idx, circuit in enumerate(circuits, 1):
        name = circuit.get('name', '-')
        va = circuit.get('load_va', 0)
        breaker = f"{circuit.get('breaker_type', 'MCB')} {circuit.get('breaker_at', 16)}A"
        wire = circuit.get('wire_size', '2.5mm²')
        vd = circuit.get('vd_percent', 0)
        vd_str = f"{vd:.1f}%" if vd else "-"
        
        lines.append(f"| {idx} | {name} | {va} | {breaker} | {wire} | {vd_str} |")
    
    lines.append("")
    
    return {
        "id": "load_schedule",
        "title": "ตารางโหลด (Load Schedule)",
        "content": "\n".join(lines),
        "page_break_before": True,
    }


def generate_boq_section(boq_data: Dict[str, Any]) -> ReportSection:
    """Generate BOQ section."""
    lines = [
        "# 💰 ประมาณการวัสดุ (Bill of Quantities)",
        "",
        f"**วันที่:** {boq_data.get('date', '-')}",
        "",
    ]
    
    for section in boq_data.get('sections', []):
        lines.append(f"## {section['section_id']}. {section['section_name']}")
        lines.append("")
        lines.append("| รายการ | จำนวน | หน่วย | ราคา/หน่วย | รวม |")
        lines.append("|--------|-------|-------|-----------|------|")
        
        for item in section.get('items', []):
            lines.append(
                f"| {item['description'][:30]}... | {item['quantity']} | {item['unit']} | "
                f"฿{item['material_unit_price']:,.0f} | ฿{item['total_price']:,.0f} |"
            )
        
        lines.append(f"\n**รวม {section['section_name']}:** ฿{section['section_total']:,.2f}")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        f"**รวมวัสดุ:** ฿{boq_data.get('subtotal_material', 0):,.2f}",
        f"**รวมค่าแรง:** ฿{boq_data.get('subtotal_labor', 0):,.2f}",
        f"**รวมทั้งสิ้น:** ฿{boq_data.get('grand_total', 0):,.2f}",
        f"**VAT {boq_data.get('vat_percent', 7)}%:** ฿{boq_data.get('vat_amount', 0):,.2f}",
        f"**ยอดสุทธิ:** ฿{boq_data.get('final_total', 0):,.2f}",
        "",
    ])
    
    return {
        "id": "boq",
        "title": "ประมาณการวัสดุ (BOQ)",
        "content": "\n".join(lines),
        "page_break_before": True,
    }


def generate_audit_section(audit_results: Dict[str, Any]) -> ReportSection:
    """Generate Audit/QC section."""
    lines = [
        "# ✅ สรุปการตรวจสอบ (Audit Summary)",
        "",
    ]
    
    # Compliance status
    is_compliant = audit_results.get('is_compliant', False)
    status_emoji = "✅" if is_compliant else "❌"
    lines.append(f"**สถานะ:** {status_emoji} {'ผ่านมาตรฐาน' if is_compliant else 'ไม่ผ่านมาตรฐาน'}")
    lines.append("")
    
    # Warnings
    warnings = audit_results.get('warnings', [])
    if warnings:
        lines.append("## ⚠️ ข้อเตือน")
        lines.append("")
        for w in warnings:
            if isinstance(w, dict):
                lines.append(f"- **{w.get('message', '-')}**")
                lines.append(f"  - เหตุผล: {w.get('reason', '-')}")
                lines.append(f"  - แนะนำ: {w.get('suggested_action', {}).get('description', '-')}")
            else:
                lines.append(f"- {w}")
        lines.append("")
    
    # Checks passed
    lines.append("## ✅ รายการที่ผ่าน")
    lines.append("")
    for check in audit_results.get('checks_passed', []):
        lines.append(f"- ✅ {check}")
    lines.append("")
    
    return {
        "id": "audit",
        "title": "สรุปการตรวจสอบ (Audit)",
        "content": "\n".join(lines),
        "page_break_before": True,
    }


def generate_assumptions_section(assumptions: List[Dict[str, Any]]) -> ReportSection:
    """Generate Assumptions section."""
    lines = [
        "# 📊 สมมติฐานที่ใช้ในการออกแบบ",
        "",
        "| รายการ | ค่าที่ใช้ | แหล่งที่มา | มาตรฐาน |",
        "|--------|---------|------------|---------|",
    ]
    
    for a in assumptions:
        source_label = {
            "default": "ค่าเริ่มต้น",
            "user": "ผู้ใช้ระบุ",
            "calculated": "คำนวณ"
        }.get(a.get('source', ''), a.get('source', ''))
        
        lines.append(
            f"| {a.get('label', '-')} | **{a.get('value', '-')}** | "
            f"{source_label} | {a.get('standard_ref', '-')} |"
        )
    
    lines.append("")
    return {
        "id": "assumptions",
        "title": "สมมติฐาน (Assumptions)",
        "content": "\n".join(lines),
        "page_break_before": True,
    }


def build_full_report(
    project_name: str,
    building_type: str,
    display_data: Dict[str, Any],
    boq_data: Dict[str, Any],
    audit_results: Dict[str, Any],
    assumptions: List[Dict[str, Any]],
    version: int = 1,
    client_name: Optional[str] = None
) -> FullReportData:
    """
    Build complete report package.
    
    Args:
        project_name: Project name
        building_type: Building type
        display_data: From compute_display_data()
        boq_data: From generate_boq()
        audit_results: From audit functions
        assumptions: From collect_assumptions()
        version: Report version
        client_name: Optional client name
        
    Returns:
        FullReportData ready for PDF generation
    """
    logger.info(f"[REPORT] Building full report for: {project_name}")
    
    # Generate sections
    sections: List[ReportSection] = []
    
    # 1. Load Schedule
    sections.append(generate_load_schedule_section(display_data))
    
    # 2. BOQ
    sections.append(generate_boq_section(boq_data))
    
    # 3. Audit
    sections.append(generate_audit_section(audit_results))
    
    # 4. Assumptions
    sections.append(generate_assumptions_section(assumptions))
    
    # Cover page
    cover = CoverPageData(
        project_name=project_name,
        client_name=client_name,
        building_type=building_type,
        address=None,
        prepared_by="Mozart AI",
        date=datetime.now().strftime("%d/%m/%Y"),
        version=version,
    )
    
    # Estimate total pages
    total_content = sum(len(s['content']) for s in sections)
    estimated_pages = max(5, total_content // 1500)
    
    return {
        "cover": cover,
        "sections": sections,
        "generated_at": datetime.now().isoformat(),
        "total_pages_estimate": estimated_pages,
    }


def render_full_report_markdown(report: FullReportData) -> str:
    """Render complete report as single Markdown document."""
    parts = [
        generate_cover_page(
            report["cover"]["project_name"],
            report["cover"]["building_type"],
            report["cover"]["version"],
            report["cover"]["client_name"],
        ),
        "",
        "<!--PAGE_BREAK-->",
        "",
        generate_toc(report["sections"]),
        "",
    ]
    
    for section in report["sections"]:
        if section["page_break_before"]:
            parts.append("<!--PAGE_BREAK-->")
            parts.append("")
        parts.append(section["content"])
        parts.append("")
    
    # Footer
    parts.extend([
        "---",
        "",
        f"*Report generated: {report['generated_at']}*",
        f"*Estimated pages: {report['total_pages_estimate']}*",
    ])
    
    return "\n".join(parts)
