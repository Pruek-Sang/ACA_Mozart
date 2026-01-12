"""
Parsers Module - Edit Command Parsing for Stateful Intelligence

This module provides the parsing infrastructure for edit commands.

Architecture:
    User Input → [Normalizer] → [Regex Parser] → Match? → Return
                                      ↓
                                     NO
                                      ↓
                                [LLM Parser] → Return

Main Entry Point:
    from app.parsers import parse_edit_command
    
    result = await parse_edit_command("เปลี่ยนแอร์เป็น 18000 BTU")
    print(result.action, result.device_type, result.new_value)

NOTE: For more sophisticated typo handling, consider adding 
      RAG-based semantic matching in the future.

Created: 2025-12-28
"""

from app.parsers.edit_command import EditCommand, EditAction, TargetType
from app.parsers.hybrid_parser import parse_edit_command, parse_edit_command_sync
from app.parsers.device_catalog import (
    DEVICE_TYPES,
    DEVICE_ALIASES,
    TYPO_MAP,
    get_device_type,
    get_action,
)
from app.parsers.normalizer import normalize_text

__all__ = [
    # Main entry points
    "parse_edit_command",
    "parse_edit_command_sync",
    
    # Data structures
    "EditCommand",
    "EditAction",
    
    # Utilities
    "normalize_text",
    "get_device_type",
    "get_action",
    
    # Constants
    "DEVICE_TYPES",
    "DEVICE_ALIASES",
    "TYPO_MAP",
]
