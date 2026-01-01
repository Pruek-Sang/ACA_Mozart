"""
Formatting utilities for electrical design outputs.
"""
from typing import Union, Optional

def format_wire_size(size_mm2: Union[float, int, str]) -> str:
    """
    Format wire size with proper unit and decimal places.
    
    Args:
        size_mm2: Wire size in mm² (can be float, int, or string)
        
    Returns:
        Formatted string, e.g., "2.5 mm²", "10 mm²"
    """
    if size_mm2 is None:
        return "?"
        
    try:
        # Handle string input like "2.5 sqmm" or "4"
        if isinstance(size_mm2, str):
            # Remove existing units if present to clean up
            clean_str = size_mm2.lower().replace("mm2", "").replace("sqmm", "").replace("mm", "").strip()
            val = float(clean_str)
        else:
            val = float(size_mm2)
            
        # If integer, show as int (4.0 -> 4)
        if val.is_integer():
            return f"{int(val)} mm²"
        else:
            return f"{val} mm²"
            
    except ValueError:
        return f"{size_mm2} mm²"
