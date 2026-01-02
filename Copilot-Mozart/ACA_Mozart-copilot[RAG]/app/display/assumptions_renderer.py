"""
Assumptions Renderer - Collect and display design assumptions

This module collects all assumptions used in the design calculation
and formats them for display in the audit report.

Author: Fixia
Date: 2026-01-03
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

logger = logging.getLogger("Aura.Display.Assumptions")


class AssumptionItem(TypedDict):
    """Single assumption item"""
    key: str  # e.g., "branch_distance"
    label: str  # Thai: "ระยะเดินสาย"
    value: str  # e.g., "15m"
    source: str  # "default" | "user" | "calculated"
    category: str  # "distance" | "electrical" | "protection"
    standard_ref: str  # e.g., "วสท. 2564"


class AssumptionsData(TypedDict):
    """Complete assumptions output"""
    project_name: str
    assumptions: List[AssumptionItem]
    has_user_overrides: bool
    total_defaults: int


# === Default Values Reference ===
DEFAULT_ASSUMPTIONS: Dict[str, Dict[str, Any]] = {
    "branch_distance": {
        "label": "ระยะเดินสาย (Branch)",
        "default": "15-25m ตามชั้น",
        "standard_ref": "วสท. 2564",
        "category": "distance"
    },
    "service_distance": {
        "label": "ระยะจากมิเตอร์ถึงตู้เมน",
        "default": "30m",
        "standard_ref": "วสท. 2564",
        "category": "distance"
    },
    "vd_branch_limit": {
        "label": "Voltage Drop Limit (Branch)",
        "default": "≤ 3%",
        "standard_ref": "วสท. 2564",
        "category": "electrical"
    },
    "vd_service_limit": {
        "label": "Voltage Drop Limit (Service)",
        "default": "≤ 2%",
        "standard_ref": "วสท. 2564",
        "category": "electrical"
    },
    "vd_total_limit": {
        "label": "Voltage Drop Limit (Total)",
        "default": "≤ 5%",
        "standard_ref": "วสท. 2564",
        "category": "electrical"
    },
    "power_factor": {
        "label": "Power Factor (ค่าตั้งต้น)",
        "default": "0.85",
        "standard_ref": "IEC 60364",
        "category": "electrical"
    },
    "safety_factor": {
        "label": "Safety Factor",
        "default": "125%",
        "standard_ref": "NEC 2023",
        "category": "protection"
    },
    "continuous_load_factor": {
        "label": "Continuous Load Factor",
        "default": "125%",
        "standard_ref": "NEC 220.10",
        "category": "protection"
    },
    "ambient_temp": {
        "label": "อุณหภูมิแวดล้อม",
        "default": "30°C",
        "standard_ref": "วสท. 2564",
        "category": "electrical"
    },
    "rcbo_wet_location": {
        "label": "RCBO สำหรับพื้นที่เปียก",
        "default": "30mA",
        "standard_ref": "วสท. 2564",
        "category": "protection"
    },
    "max_outlets_per_circuit": {
        "label": "จุดปลั๊กสูงสุดต่อวงจร",
        "default": "10 จุด",
        "standard_ref": "วสท. 2564",
        "category": "protection"
    },
    "max_lighting_watts": {
        "label": "โหลดไฟสูงสุดต่อวงจร",
        "default": "1,500W",
        "standard_ref": "วสท. 2564",
        "category": "protection"
    },
}


def collect_assumptions(
    display_data: Dict[str, Any],
    user_specs: Optional[Dict[str, Any]] = None
) -> AssumptionsData:
    """
    Collect assumptions from display data and compare with defaults.
    
    Args:
        display_data: Output from compute_display_data()
        user_specs: User-specified values (if any)
        
    Returns:
        AssumptionsData with all assumptions listed
    """
    logger.info("[ASSUMPTIONS] Collecting design assumptions...")
    
    assumptions: List[AssumptionItem] = []
    total_defaults = 0
    has_user_overrides = False
    
    # Process each default assumption
    for key, default_info in DEFAULT_ASSUMPTIONS.items():
        # Check if user provided this value
        user_value = user_specs.get(key) if user_specs else None
        
        if user_value is not None:
            source = "user"
            value = str(user_value)
            has_user_overrides = True
        else:
            source = "default"
            value = default_info["default"]
            total_defaults += 1
        
        assumptions.append({
            "key": key,
            "label": default_info["label"],
            "value": value,
            "source": source,
            "category": default_info["category"],
            "standard_ref": default_info["standard_ref"],
        })
    
    # Add calculated values from display_data
    if display_data.get("main_breaker"):
        assumptions.append({
            "key": "main_breaker",
            "label": "Main Breaker ที่คำนวณได้",
            "value": f"{display_data['main_breaker']}A",
            "source": "calculated",
            "category": "protection",
            "standard_ref": "วสท. 2564",
        })
    
    if display_data.get("total_kw"):
        assumptions.append({
            "key": "total_load",
            "label": "โหลดรวม",
            "value": f"{display_data['total_kw']:.2f} kW",
            "source": "calculated",
            "category": "electrical",
            "standard_ref": "-",
        })
    
    result: AssumptionsData = {
        "project_name": display_data.get("project_name", "โครงการ"),
        "assumptions": assumptions,
        "has_user_overrides": has_user_overrides,
        "total_defaults": total_defaults,
    }
    
    logger.info(f"[ASSUMPTIONS] Collected {len(assumptions)} assumptions ({total_defaults} defaults)")
    return result


def render_assumptions_markdown(assumptions_data: AssumptionsData) -> str:
    """
    Render assumptions as Markdown for audit document.
    
    Args:
        assumptions_data: Output from collect_assumptions()
        
    Returns:
        Markdown string
    """
    lines: List[str] = [
        "## 📊 สมมติฐานที่ใช้ในการออกแบบ",
        "",
    ]
    
    if assumptions_data["total_defaults"] > 0:
        lines.append(f"> ⚠️ ใช้ค่าเริ่มต้น {assumptions_data['total_defaults']} รายการ (ไม่ได้ระบุโดยผู้ใช้)")
        lines.append("")
    
    # Group by category
    categories = {
        "distance": ("📏 ระยะทาง", []),
        "electrical": ("⚡ ค่าทางไฟฟ้า", []),
        "protection": ("🛡️ การป้องกัน", []),
    }
    
    for assumption in assumptions_data["assumptions"]:
        cat = assumption["category"]
        if cat in categories:
            categories[cat][1].append(assumption)
    
    # Render each category
    for cat_key, (cat_label, items) in categories.items():
        if not items:
            continue
        
        lines.extend([
            f"### {cat_label}",
            "",
            "| รายการ | ค่าที่ใช้ | แหล่งที่มา | มาตรฐาน |",
            "|--------|---------|------------|---------|",
        ])
        
        for item in items:
            source_emoji = {
                "default": "⚙️ ค่าเริ่มต้น",
                "user": "✏️ ผู้ใช้ระบุ",
                "calculated": "🔢 คำนวณ"
            }.get(item["source"], item["source"])
            
            lines.append(
                f"| {item['label']} | **{item['value']}** | {source_emoji} | {item['standard_ref']} |"
            )
        
        lines.append("")
    
    return "\n".join(lines)


def format_assumptions_for_frontend(assumptions_data: AssumptionsData) -> List[Dict[str, Any]]:
    """
    Format assumptions for frontend display.
    
    Maps to frontend-expected format for AssumptionsPanel.
    """
    return [
        {
            "key": a["key"],
            "label": a["label"],
            "value": a["value"],
            "source": a["source"],
            "category": a["category"],
            "isDefault": a["source"] == "default",
        }
        for a in assumptions_data["assumptions"]
    ]
