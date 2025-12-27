"""
Normalizer - Text Normalization and Typo Handling

Cleans and normalizes user input before regex parsing.
Handles typos via dictionary lookup and fuzzy matching.

NOTE: For more sophisticated handling, consider RAG-based semantic matching.
      The existing service.py _normalize_typos() also handles some cases.

Created: 2025-12-28
"""

import re
import logging
from typing import List, Tuple

from app.parsers.device_catalog import TYPO_MAP, DEVICE_ALIASES

logger = logging.getLogger("Aura.Parsers.Normalizer")


def normalize_text(text: str) -> str:
    """
    Normalize user input text.
    
    Steps:
    1. Lowercase the text
    2. Apply typo corrections from TYPO_MAP
    3. Normalize whitespace
    
    Args:
        text: Raw user input
        
    Returns:
        Normalized text ready for regex parsing
    """
    if not text:
        return ""
    
    # Step 1: Basic normalization
    text = text.lower()
    normalized = text.strip()
    
    # Step 2: Apply typo corrections
    normalized = apply_typo_corrections(normalized)
    
    # Step 3: Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    logger.debug(f"[NORMALIZER] '{text[:50]}...' → '{normalized[:50]}...'")
    
    return normalized


def apply_typo_corrections(text: str) -> str:
    """
    Apply typo corrections from TYPO_MAP.
    
    Process:
    1. For each word in text, check if it's a known typo
    2. Replace with corrected version
    3. IMPORTANT: Avoid replacing substrings of already correct words
       (e.g., 'แอ' -> 'แอร์', but do not replace 'แอ' inside 'แอร์' to make 'แอร์ร์')
    
    Args:
        text: Input text
        
    Returns:
        Text with typos corrected
    """
    result = text
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_typos = sorted(TYPO_MAP.keys(), key=len, reverse=True)
    
    for typo in sorted_typos:
        correction = TYPO_MAP[typo]
        
        # Check if typo is a prefix of the correction (e.g. 'แอร' inside 'แอร์')
        if correction.startswith(typo) and len(correction) > len(typo):
             suffix = correction[len(typo):]
             # Check if the typo is followed by the suffix
             # e.g. Match 'แอร' only if NOT followed by '์'
             pattern_str = re.escape(typo) + f"(?!{re.escape(suffix)})"
             pattern = re.compile(pattern_str, re.IGNORECASE)
             result = pattern.sub(correction, result)
        else:
            # Standard case
            if typo.lower() in result.lower():
                pattern = re.compile(re.escape(typo), re.IGNORECASE)
                result = pattern.sub(correction, result)
                logger.debug(f"[TYPO] '{typo}' → '{correction}'")
    
    return result


def fuzzy_match_device(word: str, threshold: int = 2) -> str:
    """
    Fuzzy match a word to known device names.
    
    Uses Levenshtein distance to find closest match.
    
    Args:
        word: Input word to match
        threshold: Maximum edit distance (default: 2)
        
    Returns:
        Matched device alias or original word if no match
    """
    if not word:
        return word
    
    word_lower = word.lower()
    
    # First check exact match in aliases
    if word_lower in DEVICE_ALIASES:
        return word_lower
    
    # Try fuzzy matching
    best_match = None
    best_distance = threshold + 1
    
    for alias in DEVICE_ALIASES.keys():
        distance = levenshtein_distance(word_lower, alias.lower())
        if distance < best_distance:
            best_distance = distance
            best_match = alias
    
    if best_match and best_distance <= threshold:
        logger.debug(f"[FUZZY] '{word}' → '{best_match}' (distance={best_distance})")
        return best_match
    
    return word


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein (edit) distance between two strings.
    
    This is the minimum number of single-character edits
    (insertions, deletions, substitutions) required to
    change one word into the other.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost is 0 if characters match, 1 otherwise
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def extract_numbers(text: str) -> List[Tuple[int, str]]:
    """
    Extract all numbers with their units from text.
    
    Returns:
        List of (value, unit) tuples
        Unit is "BTU", "W", or "" if no unit found
    """
    results = []
    
    # Pattern: number followed by optional unit
    pattern = r'(\d+)\s*(btu|w|วัตต์|watt)?'
    
    matches = re.findall(pattern, text.lower())
    
    for value, unit in matches:
        unit_normalized = ""
        if unit in ["btu"]:
            unit_normalized = "BTU"
        elif unit in ["w", "วัตต์", "watt"]:
            unit_normalized = "W"
        
        results.append((int(value), unit_normalized))
    
    return results
