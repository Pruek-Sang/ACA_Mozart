"""
Audit Formatter - Format Audit Report separately from Load Schedule

[CP-FMT-AUDIT] Checkpoint prefix for all audit formatting logs.

This module is SEPARATE from markdown_formatter.py to keep concerns isolated.
The audit report shows User values vs Auto values with PASS/FAIL status.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger("Aura.AuditFormatter")


def format_audit_report(audit_results: List[Dict[str, Any]]) -> str:
    """
    [CP-FMT-AUDIT] Format audit results as Markdown.
    
    Args:
        audit_results: List of audit checks with PASS/FAIL status
    
    Returns:
        Markdown string for the audit report section
    """
    if not audit_results:
        logger.info("[CP-FMT-AUDIT] No audit results to format")
        return ""
    
    logger.info(f"[CP-FMT-AUDIT] Formatting {len(audit_results)} audit items")
    
    lines = [
        "",
        "---",
        "",
        "## 🔍 รายงานตรวจสอบ (Audit Report)",
        "",
        "> ⚠️ ค่าด้านล่างเป็น **ค่าที่ผู้ใช้ระบุ** เทียบกับ **ค่าที่ระบบแนะนำ**",
        "",
        "| โหลด | รายการ | ค่า User | ค่าแนะนำ | ผล |",
        "|------|--------|----------|----------|:--:|",
    ]
    
    fail_count = 0
    warn_count = 0
    pass_count = 0
    
    for result in audit_results:
        circuit = result.get('circuit_name', 'Unknown')[:15]
        device = result.get('device', '')
        
        for check in result.get('checks', []):
            item = check.get('item', '')
            user_val = check.get('user_value', '-')
            auto_val = check.get('auto_value', '-')
            status = check.get('status', 'PASS')
            
            if status == 'FAIL':
                status_icon = "❌"
                fail_count += 1
            elif status == 'WARN':
                status_icon = "⚠️"
                warn_count += 1
            else:
                status_icon = "✅"
                pass_count += 1
            
            # Translate item names
            item_display = {
                'breaker': 'Breaker',
                'wire_size': 'สายไฟ'
            }.get(item, item)
            
            lines.append(f"| {circuit} | {item_display} | {user_val} | {auto_val} | {status_icon} |")
    
    lines.append("")
    
    # Add summary
    total = fail_count + warn_count + pass_count
    lines.append(f"**สรุป:** ✅ {pass_count} รายการผ่าน")
    if warn_count > 0:
        lines.append(f", ⚠️ {warn_count} รายการเตือน")
    if fail_count > 0:
        lines.append(f", ❌ {fail_count} รายการไม่ผ่าน")
    lines.append("")
    
    # Add fail details if any
    if fail_count > 0:
        lines.append("")
        lines.append("### ❌ รายการที่ไม่ผ่าน")
        lines.append("")
        for result in audit_results:
            for check in result.get('checks', []):
                if check.get('status') == 'FAIL':
                    lines.append(f"- **{result.get('circuit_name', 'Unknown')}**: {check.get('reason', 'ไม่ระบุเหตุผล')}")
        lines.append("")
    
    logger.info(f"[CP-FMT-AUDIT] Format complete: {pass_count} PASS, {warn_count} WARN, {fail_count} FAIL")
    
    return "\n".join(lines)


def get_audit_summary(audit_results: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    [CP-FMT-AUDIT] Get summary counts from audit results.
    
    Returns:
        Dict with 'pass', 'warn', 'fail' counts
    """
    if not audit_results:
        return {'pass': 0, 'warn': 0, 'fail': 0}
    
    counts = {'pass': 0, 'warn': 0, 'fail': 0}
    for result in audit_results:
        for check in result.get('checks', []):
            status = check.get('status', 'PASS').lower()
            if status in counts:
                counts[status] += 1
    
    return counts
