import sys
import os
import re
sys.path.append(os.getcwd())

from app.parsers.device_catalog import ACTION_KEYWORDS
from app.parsers.regex_parser import PATTERNS, regex_parse
from app.parsers.normalizer import normalize_text

print("--- DEBUG REGEX PARSER ---")
undo_kws = ACTION_KEYWORDS.get("UNDO")
print(f"UNDO Keywords from Catalog: {undo_kws}")

# Test Normalization
test_str = "undo"
normalized = normalize_text(test_str)
print(f"Raw: '{test_str}' -> Normalized: '{normalized}'")

undo_pattern = PATTERNS.get("undo_command")
if undo_pattern:
    print(f"Undo Pattern: {undo_pattern.pattern}")
else:
    print("❌ Undo Pattern NOT FOUND in PATTERNS")

test_str = "undo"
print(f"Testing string: '{test_str}'")

# Test 1: Direct Regex
if undo_pattern:
    m = undo_pattern.search(test_str)
    print(f"Direct Match Result: {m}")

# Test 2: Full Parse
cmd = regex_parse(test_str)
print(f"regex_parse Result: {cmd}")
if cmd:
    print(f"Parsed Action: {cmd.action}")
