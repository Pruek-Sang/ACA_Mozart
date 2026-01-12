"""
Device Catalog - Device Types, Aliases, and Typo Mappings

Contains all device-related constants and mappings for the Edit Parser.
This is the single source of truth for device recognition.

NOTE: If you need more sophisticated typo handling in the future,
      consider adding RAG-based semantic matching here.
      The service.py already has chain-of-thought typo handling in
      _normalize_typos() which covers some cases.

Created: 2025-12-28
"""

from typing import Dict, List, Set


# =============================================================================
# DEVICE TYPES (Canonical Names)
# =============================================================================
# These are the internal device codes used throughout the system

DEVICE_TYPES: Set[str] = {
    "AC",           # Air conditioner
    "HEATER",       # Water heater
    "PUMP",         # Water pump
    "INDUCTION",    # Induction cooktop
    "SOCKET",       # Power outlet
    "LIGHT",        # LED light
    "FAN_CEILING",  # Ceiling fan
    "FAN_EXHAUST",  # Exhaust fan
    "MICROWAVE",    # Microwave
    "REFRIGERATOR", # Refrigerator
    "KETTLE",       # Electric kettle
    "RICE_COOKER",  # Rice cooker
    "EV_CHARGER",   # EV charger
}


# =============================================================================
# DEVICE ALIASES (Maps various names to canonical device type)
# =============================================================================
# Key = alias (lowercase), Value = canonical device type

DEVICE_ALIASES: Dict[str, str] = {
    # AC variants
    "แอร์": "AC",
    "เครื่องปรับอากาศ": "AC",
    "แอร์คอน": "AC",
    "aircon": "AC",
    "ac": "AC",
    "air": "AC",
    "air conditioner": "AC",
    
    # Heater variants
    "น้ำอุ่น": "HEATER",
    "เครื่องทำน้ำอุ่น": "HEATER",
    "เครื่องน้ำอุ่น": "HEATER",
    "วอเตอร์ฮีทเตอร์": "HEATER",
    "ฮีทเตอร์": "HEATER",
    "heater": "HEATER",
    "water heater": "HEATER",
    
    # Pump variants
    "ปั๊มน้ำ": "PUMP",
    "ปั๊ม": "PUMP",
    "pump": "PUMP",
    "water pump": "PUMP",
    
    # Induction variants
    "เตาไฟฟ้า": "INDUCTION",
    "เตาแม่เหล็กไฟฟ้า": "INDUCTION",
    "เตาแม่เหล็ก": "INDUCTION",
    "induction": "INDUCTION",
    "electric stove": "INDUCTION",
    
    # Socket variants
    "เต้ารับ": "SOCKET",
    "ปลั๊ก": "SOCKET",
    "socket": "SOCKET",
    "outlet": "SOCKET",
    
    # Light variants
    "ไฟ": "LIGHT",
    "หลอดไฟ": "LIGHT",
    "ดาวน์ไลท์": "LIGHT",
    "led": "LIGHT",
    "light": "LIGHT",
    
    # Fan variants
    "พัดลมเพดาน": "FAN_CEILING",
    "พัดลม": "FAN_CEILING",
    "ceiling fan": "FAN_CEILING",
    "พัดลมดูดอากาศ": "FAN_EXHAUST",
    "exhaust fan": "FAN_EXHAUST",
    
    # Kitchen appliances
    "ไมโครเวฟ": "MICROWAVE",
    "microwave": "MICROWAVE",
    "ตู้เย็น": "REFRIGERATOR",
    "refrigerator": "REFRIGERATOR",
    "fridge": "REFRIGERATOR",
    "กาต้มน้ำ": "KETTLE",
    "kettle": "KETTLE",
    "หม้อหุงข้าว": "RICE_COOKER",
    "rice cooker": "RICE_COOKER",
    
    # EV
    "ev charger": "EV_CHARGER",
    "ที่ชาร์จรถ": "EV_CHARGER",
}


# =============================================================================
# TYPO MAP (Common typos → Correct word)
# =============================================================================
# This handles keyboard misses, transliteration errors, and common mistakes
# Key = typo (lowercase), Value = correct word (will then be matched to alias)

TYPO_MAP: Dict[str, str] = {
    # แอร์ typos (Thai)
    "แอ": "แอร์",
    "แอ์": "แอร์",
    "เเอร์": "แอร์",   # Wrong ไม้เอก
    "แอร": "แอร์",
    
    # แอร์ typos (English)
    "aur": "แอร์",
    "arr": "แอร์",
    "aar": "แอร์",
    "aiir": "แอร์",
    "aer": "แอร์",
    "aair": "แอร์",
    
    # น้ำอุ่น typos
    "น้ำร้อน": "น้ำอุ่น",  # Common confusion
    "เครื่องทำน้ำร้อน": "เครื่องทำน้ำอุ่น",
    
    # ปั๊มน้ำ typos
    "ปั้มน้ำ": "ปั๊มน้ำ",  # Wrong tone mark
    "ปั้ม": "ปั๊มน้ำ",
    
    # Unit typos
    "วัตต์": "w",
    "วัตท์": "w",
    "watt": "w",
    "บีทียู": "btu",
}


# =============================================================================
# VALID VALUES PER DEVICE (For validation)
# =============================================================================

VALID_VALUES: Dict[str, Dict[str, List[int]]] = {
    "AC": {
        "BTU": [9000, 12000, 18000, 24000, 30000, 36000, 48000],
    },
    "HEATER": {
        "W": [3500, 4500, 6000],
    },
    "PUMP": {
        "W": [750, 1500],
    },
    "INDUCTION": {
        "W": [3000, 5000],
    },
}


# =============================================================================
# ACTION KEYWORDS
# =============================================================================

ACTION_KEYWORDS: Dict[str, List[str]] = {
    "CHANGE": [
        # Thai
        "เปลี่ยน", "แก้", "ปรับ", "อัพเดท", "อัปเดต", "แก้ไข",
        # English
        "change", "modify", "update", "edit",
    ],
    "ADD": [
        # Thai
        "เพิ่ม", "ใส่", "ติดตั้ง", "ใส่เพิ่ม", "เพิ่มเข้า",
        # English
        "add", "install",
    ],
    "REMOVE": [
        # Thai
        "ลบ", "เอาออก", "ยกเลิก", "ลบออก", "เอา",
        # English
        "remove", "delete",
    ],
    "UNDO": [
        # Thai
        "ย้อนกลับ", "เลิกทำ", "ไม่เอาแล้ว", "กลับ",
        # English
        "undo", "revert", "back", "cancel",
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_device_type(word: str) -> str:
    """
    Get canonical device type from any alias or typo.
    
    Args:
        word: User input word (will be lowercased)
        
    Returns:
        Canonical device type (e.g., "AC") or empty string if not found
    """
    word_lower = word.lower().strip()
    
    # Check typo map first
    if word_lower in TYPO_MAP:
        word_lower = TYPO_MAP[word_lower].lower()
    
    # Check aliases
    if word_lower in DEVICE_ALIASES:
        return DEVICE_ALIASES[word_lower]
    
    # Check if already canonical
    if word_lower.upper() in DEVICE_TYPES:
        return word_lower.upper()
    
    return ""


def get_action(word: str) -> str:
    """
    Get action type from keyword.
    
    Returns: "CHANGE", "ADD", "REMOVE", or ""
    """
    word_lower = word.lower().strip()
    
    for action, keywords in ACTION_KEYWORDS.items():
        if word_lower in [k.lower() for k in keywords]:
            return action
    
    return ""
