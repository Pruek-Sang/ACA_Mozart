"""
Hybrid Parser - Orchestrator for Edit Command Parsing

Combines Normalizer → Regex → LLM in sequence.
This is the main entry point for edit parsing.

Chain of Thought:
1. Normalize input (fix typos)
2. Try regex parser (fast, free)
3. If regex fails, try LLM parser (slower, paid)

Created: 2025-12-28
"""

import logging
from typing import Optional

from app.parsers.edit_command import EditCommand, EditAction
from app.parsers.normalizer import normalize_text
from app.parsers.regex_parser import regex_parse

logger = logging.getLogger("Aura.Parsers.Hybrid")


async def parse_edit_command(text: str, use_llm_fallback: bool = True) -> Optional[EditCommand]:
    """
    Parse an edit command from user input.
    
    This is the main entry point for the edit parser.
    
    Chain:
    1. Normalize input (fix typos, lowercase)
    2. Try regex parsing (fast, free, predictable)
    3. If regex fails and use_llm_fallback=True, try LLM
    
    Args:
        text: Raw user input
        use_llm_fallback: Whether to use LLM if regex fails
        
    Returns:
        EditCommand if parsed successfully, None otherwise
    """
    if not text or not text.strip():
        logger.warning("[HYBRID] Empty input, returning None")
        return None
    
    raw_input = text
    
    # =========================================================================
    # STEP 1: NORMALIZE (Fix typos, standardize text)
    # =========================================================================
    normalized = normalize_text(text)
    logger.info(f"[HYBRID] Step 1 - Normalized: '{normalized[:50]}...'")
    
    # =========================================================================
    # STEP 2: REGEX PARSE (Fast path - 90% of cases)
    # =========================================================================
    print(f"DEBUG: Hybrid calling regex_parse with '{normalized}'")
    result = regex_parse(normalized)
    
    if result and result.is_valid():
        result.raw_input = raw_input
        result.normalized_input = normalized
        logger.info(f"[HYBRID] ✅ Regex matched: {result.action.value} {result.device_type}")
        return result
    
    logger.debug("[HYBRID] Regex failed, trying LLM fallback...")
    
    # =========================================================================
    # STEP 3: LLM PARSE (Fallback - 10% edge cases)
    # =========================================================================
    if use_llm_fallback:
        try:
            from app.parsers.llm_parser import llm_parse
            
            result = await llm_parse(normalized)
            
            if result and result.is_valid():
                result.raw_input = raw_input
                result.normalized_input = normalized
                logger.info(f"[HYBRID] ✅ LLM matched: {result.action.value} {result.device_type}")
                return result
                
        except Exception as e:
            logger.error(f"[HYBRID] LLM fallback failed: {e}")
    
    # =========================================================================
    # STEP 4: FAILED - Could not parse
    # =========================================================================
    logger.warning(f"[HYBRID] ❌ Could not parse: '{text[:50]}...'")
    
    return EditCommand(
        action=EditAction.UNKNOWN,
        device_type="",
        confidence=0.0,
        parse_method="failed",
        raw_input=raw_input,
        normalized_input=normalized,
    )


def parse_edit_command_sync(text: str) -> Optional[EditCommand]:
    """
    Synchronous version of parse_edit_command (regex only).
    
    Use this when you don't want async/LLM overhead.
    """
    if not text or not text.strip():
        return None
    
    normalized = normalize_text(text)
    result = regex_parse(normalized)
    
    if result:
        result.raw_input = text
        result.normalized_input = normalized
    
    return result
