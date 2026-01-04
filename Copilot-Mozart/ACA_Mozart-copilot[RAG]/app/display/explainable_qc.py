"""
Explainable QC - Suggested Actions Module

Provides actionable suggestions for each QC warning,
not just pass/fail but "what to do next".

Author: Fixia
Date: 2026-01-03
"""

import logging
from enum import Enum
from typing import TypedDict, List, Optional, Dict, Any

logger = logging.getLogger("Aura.Display.ExplainableQC")


class ActionType(str, Enum):
    """Types of suggested actions"""
    UPSIZE_WIRE = "upsize_wire"
    ADD_RCBO = "add_rcbo"
    REDUCE_LOAD = "reduce_load"
    SPLIT_CIRCUIT = "split_circuit"
    UPSIZE_BREAKER = "upsize_breaker"
    ADD_GROUND = "add_ground"
    CHECK_DISTANCE = "check_distance"
    VERIFY_MANUAL = "verify_manual"
    NO_ACTION = "no_action"


class Severity(str, Enum):
    """Warning severity levels"""
    CRITICAL = "critical"  # Must fix before use
    WARNING = "warning"    # Should fix, may cause issues
    INFO = "info"          # Good to know, optional fix


class SuggestedAction(TypedDict):
    """A suggested action for a QC warning"""
    action_type: str  # ActionType value
    description: str  # Thai description
    before_value: Optional[str]  # Current value
    after_value: Optional[str]   # Suggested value
    effort: str  # 'low', 'medium', 'high'


class ExplainableWarning(TypedDict):
    """Extended warning with explanation and action"""
    code: str  # e.g., 'VD_EXCEED', 'NO_RCBO'
    message: str  # Main warning text
    reason: str  # Why this is a problem
    severity: str  # Severity level
    standard_ref: str  # Reference standard
    circuit_name: Optional[str]  # Affected circuit
    suggested_action: SuggestedAction


# === Warning Templates with Actions ===

WARNING_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "VD_EXCEED": {
        "message": "Voltage Drop เกินขีดจำกัด",
        "reason": "แรงดันตกที่ปลายสายมากเกินไป อาจทำให้อุปกรณ์ทำงานผิดปกติ",
        "severity": Severity.WARNING,
        "standard_ref": "วสท. 2564 ข้อ 5.2.2",
        "action_type": ActionType.UPSIZE_WIRE,
        "action_template": "เพิ่มขนาดสายจาก {before} เป็น {after}",
        "effort": "medium"
    },
    "NO_RCBO_WET": {
        "message": "ไม่มี RCBO สำหรับพื้นที่เปียก",
        "reason": "อุปกรณ์ในพื้นที่เปียก (ห้องน้ำ, ครัว) ต้องมีการป้องกันไฟรั่ว 30mA",
        "severity": Severity.CRITICAL,
        "standard_ref": "วสท. 2564 บทที่ 6",
        "action_type": ActionType.ADD_RCBO,
        "action_template": "ติดตั้ง RCBO 30mA แทน MCB ปัจจุบัน",
        "effort": "low"
    },
    "CIRCUIT_OVERLOAD": {
        "message": "วงจรมีโหลดเกินพิกัด",
        "reason": "กระแสโหลดใกล้เคียงหรือเกินพิกัดเบรกเกอร์",
        "severity": Severity.WARNING,
        "standard_ref": "NEC 2023 Article 210",
        "action_type": ActionType.SPLIT_CIRCUIT,
        "action_template": "แยกวงจรออกเป็น 2 วงจร หรือเพิ่มขนาดเบรกเกอร์",
        "effort": "high"
    },
    "AMPACITY_LOW": {
        "message": "สายนำไฟฟ้ามีขนาดเล็กเกินไป",
        "reason": "Ampacity ของสายไม่เพียงพอสำหรับกระแสโหลด",
        "severity": Severity.CRITICAL,
        "standard_ref": "NEC 2023 Table 310.16",
        "action_type": ActionType.UPSIZE_WIRE,
        "action_template": "เพิ่มขนาดสายจาก {before} เป็น {after}",
        "effort": "medium"
    },
    "BREAKER_UNDERSIZED": {
        "message": "ขนาด Breaker เล็กกว่าโหลด",
        "reason": "เบรกเกอร์อาจ trip บ่อยเนื่องจากไม่รองรับกระแสโหลด",
        "severity": Severity.WARNING,
        "standard_ref": "NEC 2023 Article 240",
        "action_type": ActionType.UPSIZE_BREAKER,
        "action_template": "เพิ่มขนาดเบรกเกอร์จาก {before}A เป็น {after}A",
        "effort": "low"
    },
    "DISTANCE_ASSUMED": {
        "message": "ใช้ระยะทางตั้งต้น",
        "reason": "ระยะเดินสายไม่ได้ระบุ ใช้ค่าเริ่มต้นซึ่งอาจไม่ตรงกับความเป็นจริง",
        "severity": Severity.INFO,
        "standard_ref": "-",
        "action_type": ActionType.CHECK_DISTANCE,
        "action_template": "ตรวจสอบระยะเดินสายจริงและระบุในระบบ",
        "effort": "low"
    },
    "COORDINATION_FAIL": {
        "message": "Breaker Coordination ไม่ถูกต้อง",
        "reason": "อัตราส่วน Main/Branch breaker ไม่เพียงพอสำหรับ Selective Coordination",
        "severity": Severity.WARNING,
        "standard_ref": "NEC 2023 Article 240.86",
        "action_type": ActionType.UPSIZE_BREAKER,
        "action_template": "เพิ่มขนาด Main Breaker ให้อัตราส่วน ≥ 1.5:1",
        "effort": "medium"
    },
}


def create_explainable_warning(
    warning_code: str,
    circuit_name: Optional[str] = None,
    before_value: Optional[str] = None,
    after_value: Optional[str] = None,
    custom_message: Optional[str] = None
) -> ExplainableWarning:
    """
    Create an explainable warning with suggested action.
    
    Args:
        warning_code: Code from WARNING_TEMPLATES
        circuit_name: Name of affected circuit
        before_value: Current problematic value
        after_value: Suggested corrected value
        custom_message: Override default message
        
    Returns:
        ExplainableWarning with full context
    """
    template = WARNING_TEMPLATES.get(warning_code, {
        "message": custom_message or "ข้อเตือน",
        "reason": "ตรวจสอบรายละเอียดเพิ่มเติม",
        "severity": Severity.INFO,
        "standard_ref": "-",
        "action_type": ActionType.VERIFY_MANUAL,
        "action_template": "ตรวจสอบด้วยตนเอง",
        "effort": "low"
    })
    
    # Format action description
    action_desc = template.get("action_template", "")
    
    if before_value:
        action_desc = action_desc.replace("{before}", before_value)
    else:
        # Fallback: remove placeholder or use generic term
        action_desc = action_desc.replace("{before}", "ขนาดเดิม")

    if after_value:
        action_desc = action_desc.replace("{after}", after_value)
    else:
        # Fallback
        action_desc = action_desc.replace("{after}", "ขนาดที่เหมาะสม")
    
    return {
        "code": warning_code,
        "message": custom_message or template["message"],
        "reason": template["reason"],
        "severity": template["severity"].value if isinstance(template["severity"], Severity) else template["severity"],
        "standard_ref": template["standard_ref"],
        "circuit_name": circuit_name,
        "suggested_action": {
            "action_type": template["action_type"].value if isinstance(template["action_type"], ActionType) else template["action_type"],
            "description": action_desc,
            "before_value": before_value,
            "after_value": after_value,
            "effort": template.get("effort", "low"),
        }
    }


def convert_legacy_warnings(legacy_warnings: List[str]) -> List[ExplainableWarning]:
    """
    Convert legacy string warnings to explainable format.
    
    Maps old warning strings to new format with actions.
    Now actively attempts to extract circuit names from warning text.
    """
    explainable: List[ExplainableWarning] = []
    import re
    
    for warning in legacy_warnings:
        warning_lower = warning.lower()
        
        # Try to exact circuit name if present (e.g. "Circuit L1: ...")
        # Pattern 1: "Circuit X:" or "Circuit X uses"
        circuit_match = re.search(r'circuit\s+([a-zA-Z0-9_-]+)', warning, re.IGNORECASE)
        # Pattern 2: "for 'X'" or "for X"
        if not circuit_match:
            circuit_match = re.search(r"for\s+'?([a-zA-Z0-9_\s-]+)'?", warning, re.IGNORECASE)
            
        circuit_name = circuit_match.group(1) if circuit_match else None
        
        # Detect warning type
        if "voltage drop" in warning_lower or "vd" in warning_lower:
            explainable.append(create_explainable_warning(
                "VD_EXCEED",
                custom_message=warning,
                circuit_name=circuit_name
            ))
        elif "rcbo" in warning_lower or "ไฟรั่ว" in warning_lower:
            explainable.append(create_explainable_warning(
                "NO_RCBO_WET",
                custom_message=warning,
                circuit_name=circuit_name
            ))
        elif "overload" in warning_lower or "เกินพิกัด" in warning_lower:
            explainable.append(create_explainable_warning(
                "CIRCUIT_OVERLOAD",
                custom_message=warning,
                circuit_name=circuit_name
            ))
        elif "ampacity" in warning_lower:
            explainable.append(create_explainable_warning(
                "AMPACITY_LOW",
                custom_message=warning,
                circuit_name=circuit_name
            ))
        elif "distance" in warning_lower or "ระยะ" in warning_lower:
            # 🆕 For default distance, make message clearer if we have name
            msg = warning
            if circuit_name and "default" in warning_lower:
                msg = f"วงจร {circuit_name} ใช้ระยะสาย Default (ควรตรวจสอบ)"
                
            explainable.append(create_explainable_warning(
                "DISTANCE_ASSUMED",
                custom_message=msg,
                circuit_name=circuit_name
            ))
        else:
            # Generic warning
            explainable.append({
                "code": "GENERIC",
                "message": warning,
                "reason": "ตรวจสอบรายละเอียด",
                "severity": Severity.INFO.value,
                "standard_ref": "-",
                "circuit_name": circuit_name,
                "suggested_action": {
                    "action_type": ActionType.VERIFY_MANUAL.value,
                    "description": "ตรวจสอบด้วยตนเอง",
                    "before_value": None,
                    "after_value": None,
                    "effort": "low",
                }
            })
    
    return explainable


def format_warnings_for_frontend(warnings: List[ExplainableWarning]) -> List[Dict[str, Any]]:
    """Format warnings for frontend display."""
    return [
        {
            "code": w["code"],
            "message": w["message"],
            "reason": w["reason"],
            "severity": w["severity"],
            "standardRef": w["standard_ref"],
            "circuitName": w["circuit_name"],
            "action": {
                "type": w["suggested_action"]["action_type"],
                "description": w["suggested_action"]["description"],
                "beforeValue": w["suggested_action"]["before_value"],
                "afterValue": w["suggested_action"]["after_value"],
                "effort": w["suggested_action"]["effort"],
            },
        }
        for w in warnings
    ]
