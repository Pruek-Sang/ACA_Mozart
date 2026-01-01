"""
Regex Parser - Pattern-Based Edit Command Parsing

Parses normalized text using regex patterns.
This is the fast path - handles 90% of common edit commands.

Created: 2025-12-28
"""

import re
import logging
from typing import Optional, Match

from app.parsers.edit_command import EditCommand, EditAction
from app.parsers.device_catalog import (
    get_device_type,
    get_action,
    ACTION_KEYWORDS,
    DEVICE_ALIASES,
)
from app.parsers.normalizer import extract_numbers

logger = logging.getLogger("Aura.Parsers.Regex")


# =============================================================================
# REGEX PATTERNS
# =============================================================================

# Build action pattern dynamically from keywords
ACTION_WORDS_TH = "|".join([
    kw for keywords in ACTION_KEYWORDS.values() 
    for kw in keywords if not kw.isascii()
])
ACTION_WORDS_EN = "|".join([
    kw for keywords in ACTION_KEYWORDS.values() 
    for kw in keywords if kw.isascii()
])

# Build device pattern from aliases
DEVICE_WORDS = "|".join(DEVICE_ALIASES.keys())

# Main patterns
PATTERNS = {
    # Pattern: เปลี่ยน + device + (room?) + เป็น + value + unit
    "change_thai": re.compile(
        rf"({ACTION_WORDS_TH})"  # Action word
        rf"\s*"
        rf"({DEVICE_WORDS})"    # Device
        rf"(?:\s*(?:ห้อง)?(\S+?))?"  # Optional room
        rf"\s*(?:เป็น|=)\s*"
        rf"(\d+)"               # Value
        rf"\s*(btu|w|วัตต์)?",      # Unit
        re.IGNORECASE
    ),
    
    # Pattern: change AC to 18000 BTU
    "change_english": re.compile(
        rf"({ACTION_WORDS_EN})"  # Action word
        rf"\s+"
        rf"({DEVICE_WORDS})"    # Device
        rf"(?:\s+(?:in\s+)?(\S+?))?"  # Optional room
        rf"\s+(?:to|=)\s+"
        rf"(\d+)"               # Value
        rf"\s*(btu|w)?",        # Unit
        re.IGNORECASE
    ),

    # Pattern: remove/delete + device + (room?)
    "remove_english": re.compile(
        rf"(remove|delete)"     # Remove action
        rf"\s+"
        rf"({DEVICE_WORDS})"    # Device
        rf"(?:\s+(?:in\s+)?(\S+?))?",  # Optional room
        re.IGNORECASE
    ),
    
    # Pattern: เพิ่ม + device + (value?) + (room?)
    "add_thai": re.compile(
        rf"(เพิ่ม|ใส่|ติดตั้ง)"  # Add action
        rf"\s*"
        rf"({DEVICE_WORDS})"    # Device
        rf"(?:\s*(\d+)\s*(btu|w|วัตต์|ตัว|จุด)?)?"  # Optional value+unit
        rf"(?:\s*(?:ที่|ใน)?ห้อง(\S+?))?",  # Optional room
        re.IGNORECASE
    ),
    
    # Pattern: ลบ/เอาออก + device + (room?)
    # Supports: "ลบแอร์", "เอาแอร์ออก", "ยกเลิกปั๊มน้ำ"
    "remove_thai": re.compile(
        rf"(ลบ|เอา|ยกเลิก)"  # Remove action start
        rf"\s*"
        rf"({DEVICE_WORDS})"    # Device
        rf"(?:\s*(?:ที่|ใน)?ห้อง(\S+?))?"  # Optional room
        rf"(?:\s*(?:ออก))?",    # Optional closing particle (for เอา...ออก)
        re.IGNORECASE
    ),
}


def regex_parse(text: str) -> Optional[EditCommand]:
    """
    Parse text using regex patterns.
    
    Args:
        text: Normalized text to parse
        
    Returns:
        EditCommand if matched, None otherwise
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Try each pattern
    for pattern_name, pattern in PATTERNS.items():
        match = pattern.search(text_lower)
        if match:
            logger.info(f"[REGEX] Matched pattern: {pattern_name}")
            return _build_command_from_match(match, pattern_name, text)
    
    logger.debug(f"[REGEX] No pattern matched for: '{text[:50]}...'")
    return None


def _build_command_from_match(match: Match, pattern_name: str, raw_input: str) -> EditCommand:
    """
    Build EditCommand from regex match.
    """
    groups = match.groups()
    
    # Determine action
    action_word = groups[0] if groups[0] else ""
    action_str = get_action(action_word)
    action = EditAction(action_str) if action_str else EditAction.UNKNOWN
    
    # Determine device
    device_word = groups[1] if len(groups) > 1 and groups[1] else ""
    device_type = get_device_type(device_word)
    
    # Extract room (varies by pattern)
    target_room = None
    if "change" in pattern_name:
        target_room = groups[2] if len(groups) > 2 and groups[2] else None
    elif "add" in pattern_name:
        target_room = groups[4] if len(groups) > 4 and groups[4] else None
    elif "remove" in pattern_name:
        target_room = groups[2] if len(groups) > 2 and groups[2] else None
    
    # Extract value and unit
    new_value = None
    unit = None
    quantity = None
    
    if "change" in pattern_name:
        new_value = int(groups[3]) if len(groups) > 3 and groups[3] else None
        unit = _normalize_unit(groups[4]) if len(groups) > 4 and groups[4] else None
    elif "add" in pattern_name:
        val_str = groups[2] if len(groups) > 2 and groups[2] else None
        if val_str:
            val = int(val_str)
            unit_hint = groups[3] if len(groups) > 3 else None
            if unit_hint in ["ตัว", "จุด"]:
                quantity = val
            else:
                new_value = val
                unit = _normalize_unit(unit_hint)
    
    # Infer unit from device if not specified
    if new_value and not unit:
        if device_type == "AC":
            unit = "BTU"
        elif device_type in ["HEATER", "PUMP", "INDUCTION"]:
            unit = "W"
    
    cmd = EditCommand(
        action=action,
        device_type=device_type,
        room_name=target_room,
        target_floor=None,  # Could extract from room name
        new_value=new_value,
        unit=unit,
        quantity=quantity,
        confidence=0.95 if device_type else 0.7,  # High confidence for regex match
        parse_method="regex",
        raw_input=raw_input,
        normalized_input=raw_input.lower(),
    )
    
    logger.info(f"[REGEX] Parsed: {cmd.action.value} {cmd.device_type} → {cmd.new_value} {cmd.unit}")
    
    return cmd


def _normalize_unit(unit: Optional[str]) -> Optional[str]:
    """Normalize unit string to standard form."""
    if not unit:
        return None
    
    unit_lower = unit.lower()
    
    if unit_lower in ["btu"]:
        return "BTU"
    elif unit_lower in ["w", "วัตต์", "watt"]:
        return "W"
    
    return unit.upper()
