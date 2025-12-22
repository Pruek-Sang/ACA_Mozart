"""
Device Catalog Loader
─────────────────────────────────────────────────────────────────────
Loads device specifications from devices.csv and provides lookup functions.

This module replaces the hardcoded DEVICE_MAPPING dict in mcp_adapter.py
with a CSV-based approach for easier maintenance.

Usage:
    from app.catalog.device_loader import get_device_info, list_all_devices
    
    # Get device spec
    info = get_device_info("HEATER-3500W")
    # Returns: (power_watts, load_type, is_continuous)
    
    # Add new device
    # Just edit devices.csv and redeploy!
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from functools import lru_cache

logger = logging.getLogger("Aura.DeviceCatalog")

# Path to devices.csv (relative to this file)
CATALOG_PATH = Path(__file__).parent / "devices.csv"


class LoadType:
    """Load type constants matching mcp_adapter.py"""
    LIGHTING = "lighting"
    RECEPTACLE = "receptacle"
    HVAC = "hvac"
    MOTOR = "motor"
    APPLIANCE = "appliance"
    OTHER = "other"


# Map string to LoadType
LOAD_TYPE_MAP = {
    "LIGHTING": LoadType.LIGHTING,
    "RECEPTACLE": LoadType.RECEPTACLE,
    "HVAC": LoadType.HVAC,
    "MOTOR": LoadType.MOTOR,
    "APPLIANCE": LoadType.APPLIANCE,
    "OTHER": LoadType.OTHER,
}

# Default for unknown devices
DEFAULT_DEVICE = (500, LoadType.OTHER, False)


@lru_cache(maxsize=1)
def _load_catalog() -> Dict[str, Tuple[float, str, bool]]:
    """
    Load device catalog from CSV file.
    
    Returns:
        Dict mapping device_code -> (power_watts, load_type, is_continuous)
    
    Note: Uses LRU cache to avoid re-reading file on every call.
          Clear cache with _load_catalog.cache_clear() if file changes.
    """
    catalog: Dict[str, Tuple[float, str, bool]] = {}
    
    if not CATALOG_PATH.exists():
        logger.warning(f"Device catalog not found: {CATALOG_PATH}")
        return catalog
    
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Skip comments (rows starting with #)
                device_code = row.get("device_code", "").strip()
                if not device_code or device_code.startswith("#"):
                    continue
                
                try:
                    power_watts = float(row.get("power_watts", 0))
                    load_type_str = row.get("load_type", "OTHER").upper()
                    load_type = LOAD_TYPE_MAP.get(load_type_str, LoadType.OTHER)
                    is_continuous_str = row.get("is_continuous", "false").lower()
                    is_continuous = is_continuous_str in ("true", "1", "yes")
                    
                    catalog[device_code] = (power_watts, load_type, is_continuous)
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row for {device_code}: {e}")
                    continue
        
        logger.info(f"Loaded {len(catalog)} devices from catalog")
        
    except Exception as e:
        logger.error(f"Failed to load device catalog: {e}")
    
    return catalog


def get_device_info(device_code: str) -> Tuple[float, str, bool]:
    """
    Get device specification by code.
    
    Args:
        device_code: Device identifier (e.g., 'HEATER-3500W')
    
    Returns:
        Tuple of (power_watts, load_type, is_continuous)
        Returns DEFAULT_DEVICE if not found.
    """
    catalog = _load_catalog()
    info = catalog.get(device_code)
    
    if info is None:
        logger.warning(f"Unknown device code: {device_code}, using default")
        return DEFAULT_DEVICE
    
    return info


def list_all_devices() -> List[str]:
    """Get list of all known device codes."""
    catalog = _load_catalog()
    return list(catalog.keys())


def device_exists(device_code: str) -> bool:
    """Check if device code exists in catalog."""
    catalog = _load_catalog()
    return device_code in catalog


def reload_catalog():
    """Force reload of catalog from CSV (clears cache)."""
    _load_catalog.cache_clear()
    logger.info("Device catalog cache cleared, will reload on next access")


def get_devices_by_category(category: str) -> List[str]:
    """
    Get all device codes in a category.
    
    Note: Requires re-reading CSV since we don't cache category info.
    """
    devices = []
    
    if not CATALOG_PATH.exists():
        return devices
    
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                device_code = row.get("device_code", "").strip()
                device_category = row.get("category", "").upper()
                
                if device_category == category.upper() and not device_code.startswith("#"):
                    devices.append(device_code)
    
    except Exception as e:
        logger.error(f"Failed to read catalog for category {category}: {e}")
    
    return devices


# For backward compatibility with existing code
def get_device_mapping() -> Dict[str, Tuple[float, str, bool]]:
    """
    Get full device mapping dict.
    
    This is for backward compatibility with code that expects the
    old DEVICE_MAPPING dict from mcp_adapter.py.
    """
    return _load_catalog()
