"""
Edit Intent Detector - Stateful Intelligence Module

Detects whether user wants to EDIT existing design vs CREATE new one.
Separated from service.py for maintainability.

🆕 Features:
- Typo tolerance (เพิ่ม/เพิม/เพิท)
- Keyboard layout mistakes (ฟฟก = add)
- Pattern matching (เอา X ออก)

Created: 2025-12-28
Updated: 2026-01-11 - Added typo tolerance
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger("Aura.Intent.EditDetector")

# =============================================================================
# EDIT KEYWORDS - Thai & English (with typo variants)
# =============================================================================

# ADD variants (เพิ่ม, เพิม, เพิท, เพิ่ท, ใส่)
ADD_KEYWORDS: List[str] = [
    "เพิ่ม", "เพิม", "เพิท", "เพิ่ท", "เพิ้ม",  # Thai typos
    "ใส่เพิ่ม", "เพิ่มเข้า", "เพิ่มขึ้น", "ใส่",
    "add", "ฟฟก",  # English + keyboard layout mistake (TH keyboard: ฟฟก = add)
]

# DELETE/REMOVE variants (ลบ, ล, เอาออก, delete)
DELETE_KEYWORDS: List[str] = [
    "ลบ", "ลบออก", "เอาออก", "ถอด", "ถอดออก",
    "ตัด", "ตัดออก", "ยกเลิก",
    "delete", "deleted", "remove", "removed",
    "กำสำะำ",  # TH keyboard: delete
]

# CHANGE/MODIFY variants (เปลี่ยน, แก้, ปรับ)
CHANGE_KEYWORDS: List[str] = [
    "เปลี่ยน", "เปลียน", "เปลี่ยนเป็น",  # Thai typos
    "แก้", "แก้ไข", "แก้เป็น",
    "ปรับ", "ปรับเป็น", "ปรับใหม่",
    "อัพเดท", "อัปเดต", "อัพเดต",
    "change", "modify", "replace", "edit", "update",
    "swap", "switch",
    "แทน", "แทนที่", "สลับ",
]

# INCREASE/DECREASE variants
ADJUST_KEYWORDS: List[str] = [
    "เพิ่มขึ้น", "ลด", "ลดลง", "เพิ่มอีก", "ลดอีก",
    "increase", "decrease", "more", "less",
]

# All edit keywords combined
ALL_EDIT_KEYWORDS: List[str] = ADD_KEYWORDS + DELETE_KEYWORDS + CHANGE_KEYWORDS + ADJUST_KEYWORDS

# =============================================================================
# Pattern-based detection (for "เอา XXX ออก" style)
# =============================================================================

EDIT_PATTERNS: List[Tuple[str, str]] = [
    (r"เอา\s*\S+\s*ออก", "REMOVE"),      # เอา XXX ออก
    (r"ลบ\s*\S+\s*ออก", "REMOVE"),       # ลบ XXX ออก
    (r"เปลี่ยน\s*\S+\s*เป็น", "CHANGE"), # เปลี่ยน XXX เป็น YYY
    (r"แก้\s*\S+\s*เป็น", "CHANGE"),     # แก้ XXX เป็น YYY
    (r"เพิ่ม\s*\S+\s*อีก", "ADD"),       # เพิ่ม XXX อีก N ตัว
]


def detect_edit_intent(user_message: str) -> bool:
    """
    Detect if user wants to EDIT existing design vs CREATE new.
    
    🆕 Features:
    - Typo tolerance (เพิ่ม/เพิม/เพิท)
    - Keyboard layout mistakes (ฟฟก = add on TH keyboard)
    - Pattern matching (เอา X ออก)
    
    Flow:
    1. Check for explicit edit keywords (with typo variants)
    2. Check for edit patterns (เอา XXX ออก)
    3. If found → EDIT mode (return True)
    4. If not found → CREATE mode (return False)
    
    Examples:
    - "เพิ่มแอร์" → EDIT (เพิ่ม)
    - "เพิมแอร์" → EDIT (typo: เพิม)
    - "ฟฟก แอร์" → EDIT (keyboard: ฟฟก = add)
    - "เอาปั๊มน้ำออก" → EDIT (pattern)
    - "ออกแบบบ้าน 2 ชั้น" → CREATE (no edit keyword)
    
    Args:
        user_message: The user's input message
    
    Returns:
        bool: True = EDIT mode, False = CREATE mode
    """
    lower_msg = user_message.lower()
    
    # ==========================================================================
    # METHOD 1: Direct keyword matching (with typos)
    # ==========================================================================
    for keyword in ALL_EDIT_KEYWORDS:
        if keyword.lower() in lower_msg:
            logger.info(f"[EDIT_INTENT] ✅ Detected EDIT keyword: '{keyword}'")
            return True
    
    # ==========================================================================
    # METHOD 2: Pattern matching
    # ==========================================================================
    for pattern, action_type in EDIT_PATTERNS:
        if re.search(pattern, user_message, re.IGNORECASE):
            logger.info(f"[EDIT_INTENT] ✅ Detected EDIT pattern ({action_type}): '{pattern}'")
            return True
    
    logger.info(f"[EDIT_INTENT] No edit keywords/patterns found → CREATE mode")
    return False


def get_edit_action_type(user_message: str) -> str:
    """
    Determine which type of edit action is requested.
    
    Returns: "ADD", "REMOVE", "CHANGE", or "UNKNOWN"
    """
    lower_msg = user_message.lower()
    
    # Check ADD keywords
    for kw in ADD_KEYWORDS:
        if kw.lower() in lower_msg:
            return "ADD"
    
    # Check DELETE keywords
    for kw in DELETE_KEYWORDS:
        if kw.lower() in lower_msg:
            return "REMOVE"
    
    # Check CHANGE keywords
    for kw in CHANGE_KEYWORDS:
        if kw.lower() in lower_msg:
            return "CHANGE"
    
    # Check patterns
    for pattern, action_type in EDIT_PATTERNS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return action_type
    
    return "UNKNOWN"

