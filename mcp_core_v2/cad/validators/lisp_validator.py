"""
LISP Validator - Syntax and Semantic Validation

Validates AutoLISP files for:
1. Syntax (parentheses, encoding, structure)
2. Semantic (data consistency with MCP)
3. Drawing standards compliance
"""

import logging
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LISPValidationError(Exception):
    """Raised when LISP validation fails"""
    pass


def validate_lisp_syntax(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate LISP file syntax
    
    Spec (from plan):
    1. Balanced parentheses: count('(') == count(')')
    2. No invalid characters (control chars except \n, \r, \t)
    3. Basic LISP structure: has (defun ...) or (command ...)
    4. File readable with UTF-8 encoding
    
    Args:
        file_path: Path to .lsp file
    
    Returns:
        (is_valid, list_of_errors)
    
    Example:
        ok, errors = validate_lisp_syntax('E-301.lsp')
        assert ok, f"Syntax errors: {errors}"
    """
    errors = []
    
    # 1. Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError as e:
        return (False, [f"Encoding error: {e}. File must be UTF-8."])
    except Exception as e:
        return (False, [f"Cannot read file: {e}"])
    
    # 2. Check parentheses balance
    open_count = content.count('(')
    close_count = content.count(')')
    
    if open_count != close_count:
        errors.append(
            f"Unbalanced parentheses: {open_count} open, {close_count} close"
        )
    
    # Check for negative balance (more ) than ()
    balance = 0
    for i, char in enumerate(content):
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1
        
        if balance < 0:
            errors.append(
                f"Parenthesis error at position {i}: "
                f"closing ')' without matching '('"
            )
            break
    
    # 3. Check for basic LISP structure
    has_defun = '(defun' in content or '(DEFUN' in content
    has_command = '(command' in content or '(COMMAND' in content
    
    if not has_defun and not has_command:
        errors.append(
            "No LISP commands found. Expected (defun ...) or (command ...)"
        )
    
    # 4. Check for invalid control characters
    for i, char in enumerate(content):
        ord_char = ord(char)
        # Allow: newline (10), carriage return (13), tab (9)
        # Disallow: other control characters (0-31, except 9,10,13)
        if ord_char < 32 and ord_char not in [9, 10, 13]:
            errors.append(
                f"Invalid control character at position {i}: "
                f"ASCII {ord_char}"
            )
            break  # Only report first occurrence
    
    # 5. Check file not empty
    if len(content.strip()) == 0:
        errors.append("File is empty")
    
    is_valid = len(errors) == 0
    return (is_valid, errors)


def validate_lisp_semantic(file_path: Path, mcp_result: Any, 
                          placed_devices: Optional[Dict[str, List]] = None) -> Tuple[bool, List[str]]:
    """
    Validate LISP file semantic consistency with MCP
    
    Spec (from plan):
    1. Circuit count matches MCP
    2. Device count matches placement (±1 tolerance)
    3. Wire sizes match MCP
    4. Breaker sizes match MCP
    
    Args:
        file_path: Path to .lsp file
        mcp_result: DesignResult from MCP pipeline
        placed_devices: Optional dict of placed devices
    
    Returns:
        (is_valid, list_of_errors)
    
    Example:
        ok, errors = validate_lisp_semantic(
            'E-301.lsp',
            mcp_result,
            {'outlets': [...], 'lights': [...]}
        )
        assert ok, f"Semantic errors: {errors}"
    """
    errors = []
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return (False, [f"Cannot read file: {e}"])
    
    # 1. Check circuit count
    try:
        mcp_circuits = _extract_mcp_circuits(mcp_result)
        lisp_circuits = _extract_lisp_circuit_labels(content)
        
        if mcp_circuits and lisp_circuits:
            mcp_count = len(mcp_circuits)
            lisp_count = len(lisp_circuits)
            
            if mcp_count != lisp_count:
                errors.append(
                    f"Circuit count mismatch: "
                    f"MCP has {mcp_count}, LISP has {lisp_count}"
                )
    except Exception as e:
        logger.warning(f"Could not validate circuit count: {e}")
    
    # 2. Check device count (if placed_devices provided)
    if placed_devices:
        try:
            mcp_device_count = sum(len(devices) for devices in placed_devices.values())
            lisp_device_count = _count_insert_commands(content)
            
            # Allow ±1 tolerance (footer symbols, panel symbols, etc.)
            diff = abs(mcp_device_count - lisp_device_count)
            if diff > 1:
                errors.append(
                    f"Device count mismatch (tolerance ±1): "
                    f"Placed {mcp_device_count}, LISP has {lisp_device_count}"
                )
        except Exception as e:
            logger.warning(f"Could not validate device count: {e}")
    
    # 3. Check wire sizes match MCP
    try:
        if hasattr(mcp_result, 'wires') and mcp_result.wires:
            for wire in mcp_result.wires[:3]:  # Check first 3
                wire_size = getattr(wire, 'size_mm2', None)
                if wire_size:
                    wire_pattern = f"{wire_size}mm"
                    if wire_pattern not in content:
                        errors.append(
                            f"Wire size {wire_size}mm² from MCP not found in LISP"
                        )
                        break  # Don't spam errors
    except Exception as e:
        logger.warning(f"Could not validate wire sizes: {e}")
    
    # 4. Check breaker sizes match MCP
    try:
        if hasattr(mcp_result, 'breakers') and mcp_result.breakers:
            for breaker in mcp_result.breakers[:3]:  # Check first 3
                rating = getattr(breaker, 'rating', None)
                if rating:
                    breaker_pattern = f"{rating}A"
                    if breaker_pattern not in content:
                        errors.append(
                            f"Breaker {rating}A from MCP not found in LISP"
                        )
                        break
    except Exception as e:
        logger.warning(f"Could not validate breaker sizes: {e}")
    
    is_valid = len(errors) == 0
    return (is_valid, errors)


def _extract_mcp_circuits(mcp_result: Any) -> List[str]:
    """Extract circuit IDs from MCP result"""
    circuits = []
    
    try:
        if hasattr(mcp_result, 'wires'):
            for i, wire in enumerate(mcp_result.wires):
                circuit_id = getattr(wire, 'circuit_id', f'CKT-{i+1}')
                circuits.append(circuit_id)
    except:
        pass
    
    return circuits


def _extract_lisp_circuit_labels(content: str) -> List[str]:
    """Extract circuit labels from LISP content"""
    # Look for patterns like "CKT-01", "LT-01", "PWR-01"
    pattern = r'(CKT|LT|PWR|BATH)-\d+'
    matches = re.findall(pattern, content)
    return list(set(matches))  # Unique


def _count_insert_commands(content: str) -> int:
    """Count INSERT commands in LISP (= number of blocks/devices)"""
    # Case insensitive count of (command "INSERT" ...
    pattern = r'\(command\s+"?INSERT"?'
    matches = re.findall(pattern, content, re.IGNORECASE)
    return len(matches)


def validate_all(lisp_files: Dict[str, Path], mcp_result: Any, 
                placed_devices: Optional[Dict] = None) -> Dict[str, Tuple[bool, List[str]]]:
    """
    Validate multiple LISP files
    
    Args:
        lisp_files: {'E-301': Path, 'E-401': Path}
        mcp_result: MCP result
        placed_devices: Optional placed devices
    
    Returns:
        {
            'E-301': (True, []),
            'E-401': (False, ['error1', 'error2'])
        }
    """
    results = {}
    
    for name, file_path in lisp_files.items():
        # Syntax
        syntax_ok, syntax_errors = validate_lisp_syntax(file_path)
        
        # Semantic
        semantic_ok, semantic_errors = validate_lisp_semantic(
            file_path, mcp_result, placed_devices
        )
        
        # Combined
        all_ok = syntax_ok and semantic_ok
        all_errors = syntax_errors + semantic_errors
        
        results[name] = (all_ok, all_errors)
    
    return results
