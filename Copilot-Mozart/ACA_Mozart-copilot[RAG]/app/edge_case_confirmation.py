"""
Edge Case Confirmation Module

Handles cases where the system needs user confirmation
instead of making assumptions.

Author: Fixia
Date: 2026-01-03
"""

import logging
from enum import Enum
from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger("Aura.EdgeCase")


class ConfirmationType(str, Enum):
    """Types of confirmations needed"""
    DISTANCE_NOT_SPECIFIED = "distance_not_specified"
    AC_BTU_NOT_SPECIFIED = "ac_btu_not_specified"
    DUPLICATE_ROOM = "duplicate_room"
    LOAD_NEAR_LIMIT = "load_near_limit"
    VD_NEAR_LIMIT = "vd_near_limit"
    AMBIGUOUS_INPUT = "ambiguous_input"
    HIGH_LOAD = "high_load"


class ConfirmationOption(TypedDict):
    """Single option for user to choose"""
    id: str
    label: str
    value: Any
    is_default: bool
    description: Optional[str]


class ConfirmationRequest(TypedDict):
    """Request for user confirmation"""
    confirmation_id: str
    confirmation_type: str
    title: str
    message: str
    context: Dict[str, Any]
    options: List[ConfirmationOption]
    allows_custom: bool
    custom_input_label: Optional[str]


class ConfirmationResponse(TypedDict):
    """User's response to confirmation"""
    confirmation_id: str
    selected_option_id: str
    custom_value: Optional[Any]


# === Confirmation Templates ===

CONFIRMATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    ConfirmationType.DISTANCE_NOT_SPECIFIED.value: {
        "title": "📏 ระบุระยะเดินสาย",
        "message": "ไม่ได้ระบุระยะเดินสายจาก MDB ถึงวงจร ต้องการใช้ค่าเริ่มต้นหรือไม่?",
        "options": [
            {"id": "default", "label": "ใช้ค่าเริ่มต้น", "is_default": True, "description": "ตามประเภทอาคาร (15-25m)"},
            {"id": "custom", "label": "ระบุเอง", "is_default": False, "description": None},
        ],
        "allows_custom": True,
        "custom_input_label": "ระยะทาง (เมตร)",
    },
    ConfirmationType.AC_BTU_NOT_SPECIFIED.value: {
        "title": "❄️ ระบุ BTU แอร์",
        "message": "ไม่ได้ระบุขนาด BTU ของแอร์ ต้องการให้คำนวณจากขนาดห้องหรือไม่?",
        "options": [
            {"id": "calculate", "label": "คำนวณอัตโนมัติ", "is_default": True, "description": "ใช้ขนาดห้อง × 600 BTU/ตร.ม."},
            {"id": "custom", "label": "ระบุ BTU", "is_default": False, "description": None},
        ],
        "allows_custom": True,
        "custom_input_label": "BTU",
    },
    ConfirmationType.DUPLICATE_ROOM.value: {
        "title": "🏠 ห้องซ้ำกัน",
        "message": "พบชื่อห้องซ้ำกัน ต้องการรวมโหลดหรือแยกเป็นห้องต่างกัน?",
        "options": [
            {"id": "merge", "label": "รวมโหลด", "is_default": True, "description": "รวมอุปกรณ์เป็นห้องเดียว"},
            {"id": "separate", "label": "แยกห้อง", "is_default": False, "description": "สร้างเป็นห้องแยก (1, 2, 3...)"},
        ],
        "allows_custom": False,
        "custom_input_label": None,
    },
    ConfirmationType.LOAD_NEAR_LIMIT.value: {
        "title": "⚡ โหลดใกล้ขีดจำกัด",
        "message": "วงจรมีโหลดใกล้ 80% ของพิกัดเบรกเกอร์ ต้องการแยกวงจรหรือไม่?",
        "options": [
            {"id": "keep", "label": "คงเดิม", "is_default": True, "description": "ไม่แยกวงจร (อาจ trip บ่อย)"},
            {"id": "split", "label": "แยกวงจร", "is_default": False, "description": "แบ่งโหลดเป็น 2 วงจร"},
        ],
        "allows_custom": False,
        "custom_input_label": None,
    },
    ConfirmationType.VD_NEAR_LIMIT.value: {
        "title": "📉 Voltage Drop ใกล้ขีดจำกัด",
        "message": "VD = {current_vd}% ใกล้ 3% ขีดจำกัด ต้องการเพิ่มขนาดสายหรือไม่?",
        "options": [
            {"id": "keep", "label": "คงเดิม", "is_default": True, "description": "ยังผ่านมาตรฐาน"},
            {"id": "upsize", "label": "เพิ่มขนาดสาย", "is_default": False, "description": "ลด VD ให้ต่ำกว่า 2%"},
        ],
        "allows_custom": False,
        "custom_input_label": None,
    },
    ConfirmationType.HIGH_LOAD.value: {
        "title": "🔌 โหลดรวมสูง",
        "message": "โหลดรวม {total_kw} kW สูงกว่าปกติสำหรับ {building_type} ยืนยันหรือไม่?",
        "options": [
            {"id": "confirm", "label": "ยืนยัน", "is_default": True, "description": "โหลดถูกต้อง"},
            {"id": "review", "label": "ตรวจสอบใหม่", "is_default": False, "description": "กลับไปแก้ไขโหลด"},
        ],
        "allows_custom": False,
        "custom_input_label": None,
    },
}


def create_confirmation_request(
    confirmation_type: ConfirmationType,
    context: Optional[Dict[str, Any]] = None
) -> ConfirmationRequest:
    """
    Create a confirmation request for the given type.
    
    Args:
        confirmation_type: Type of confirmation needed
        context: Additional context for the message
        
    Returns:
        ConfirmationRequest ready to send to frontend
    """
    import uuid
    
    template = CONFIRMATION_TEMPLATES.get(confirmation_type.value, {})
    ctx = context or {}
    
    # Format message with context
    message = template.get("message", "ต้องการยืนยันหรือไม่?")
    for key, value in ctx.items():
        message = message.replace(f"{{{key}}}", str(value))
    
    # Build options
    options: List[ConfirmationOption] = []
    for opt in template.get("options", []):
        options.append({
            "id": opt["id"],
            "label": opt["label"],
            "value": opt.get("value", opt["id"]),
            "is_default": opt["is_default"],
            "description": opt.get("description"),
        })
    
    return {
        "confirmation_id": str(uuid.uuid4()),
        "confirmation_type": confirmation_type.value,
        "title": template.get("title", "ยืนยัน"),
        "message": message,
        "context": ctx,
        "options": options,
        "allows_custom": template.get("allows_custom", False),
        "custom_input_label": template.get("custom_input_label"),
    }


def check_edge_cases(
    parsed_input: Dict[str, Any]
) -> List[ConfirmationRequest]:
    """
    Check parsed input for edge cases that need confirmation.
    
    Args:
        parsed_input: Parsed user input from parser
        
    Returns:
        List of confirmation requests (empty if none needed)
    """
    confirmations: List[ConfirmationRequest] = []
    
    # Check: Distance not specified
    if not parsed_input.get("service_distance_m") and not parsed_input.get("distances"):
        confirmations.append(create_confirmation_request(
            ConfirmationType.DISTANCE_NOT_SPECIFIED,
            {"building_type": parsed_input.get("building_type", "บ้านเดี่ยว")}
        ))
    
    # Check: AC without BTU
    for room in parsed_input.get("rooms", []):
        for device in room.get("devices", []):
            if "แอร์" in device.get("name", "").lower() or "ac" in device.get("name", "").lower():
                if not device.get("btu") and not device.get("power_w"):
                    confirmations.append(create_confirmation_request(
                        ConfirmationType.AC_BTU_NOT_SPECIFIED,
                        {"room": room.get("name", ""), "device": device.get("name", "")}
                    ))
    
    return confirmations


def process_confirmation_response(
    response: ConfirmationResponse,
    current_input: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process user's confirmation response and update input.
    
    Returns:
        Updated input with user's choices applied
    """
    updated = current_input.copy()
    conf_type = response.get("confirmation_type", "")
    selected = response.get("selected_option_id", "")
    custom = response.get("custom_value")
    
    if conf_type == ConfirmationType.DISTANCE_NOT_SPECIFIED.value:
        if selected == "custom" and custom:
            updated["service_distance_m"] = float(custom)
        # else: use default, no change needed
    
    # Add more handlers as needed...
    
    return updated
