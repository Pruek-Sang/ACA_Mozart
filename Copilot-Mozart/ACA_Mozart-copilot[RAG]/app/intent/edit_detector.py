"""
Edit Intent Detector - Stateful Intelligence Module

Detects whether user wants to EDIT existing design vs CREATE new one.
Separated from service.py for maintainability.

Created: 2025-12-28
"""

import logging
from typing import List

logger = logging.getLogger("Aura.Intent.EditDetector")

# =============================================================================
# EDIT KEYWORDS - Thai & English
# =============================================================================
# Keywords that indicate user wants to EDIT existing design (not CREATE new)

EDIT_KEYWORDS_TH: List[str] = [
    "เปลี่ยน", "แก้", "ลบ", "เพิ่ม", "ปรับ", "อัพเดท", "ลด", "เพิ่มขึ้น",
    "แก้ไข", "อัปเดต", "ลบออก", "เอาออก", "ใส่เพิ่ม", "เพิ่มเข้า"
]

EDIT_KEYWORDS_EN: List[str] = [
    "change", "modify", "remove", "add", "update", "delete", "edit",
    "replace", "increase", "decrease", "swap", "switch"
]


def detect_edit_intent(user_message: str) -> bool:
    """
    Detect if user wants to EDIT existing design vs CREATE new.
    
    This is separate from _detect_design_intent which distinguishes Design vs Q&A.
    
    Flow:
    1. Check for explicit edit keywords (Thai + English)
    2. If found → EDIT mode (return True)
    3. If not found → CREATE mode (return False)
    
    Examples:
    - "เปลี่ยนแอร์เป็น 18000 BTU" → EDIT (เปลี่ยน)
    - "เพิ่มเครื่องทำน้ำอุ่น" → EDIT (เพิ่ม)
    - "ลบปั๊มน้ำออก" → EDIT (ลบ)
    - "ออกแบบบ้าน 2 ชั้น" → CREATE (no edit keyword)
    
    Args:
        user_message: The user's input message
    
    Returns:
        bool: True = EDIT mode, False = CREATE mode
    """
    lower_msg = user_message.lower()
    
    # Check Thai keywords
    for keyword in EDIT_KEYWORDS_TH:
        if keyword in lower_msg:
            logger.info(f"[EDIT_INTENT] Detected EDIT keyword (TH): '{keyword}'")
            return True
    
    # Check English keywords
    for keyword in EDIT_KEYWORDS_EN:
        if keyword in lower_msg:
            logger.info(f"[EDIT_INTENT] Detected EDIT keyword (EN): '{keyword}'")
            return True
    
    logger.info(f"[EDIT_INTENT] No edit keywords found → CREATE mode")
    return False
