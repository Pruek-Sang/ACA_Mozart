"""
boq_renderer.py - Generate Bill of Quantities (BOQ) from DisplayData

Purpose: Create BOQ table matching professional format (material + labor + total)
Input: DisplayData from compute.py
Output: BOQData structure for frontend

Author: Estrella 🌟
Date: 2024-12-31
"""

import logging
from typing import TypedDict, List, Optional, Dict, Any

logger = logging.getLogger(__name__)


# === BOQ Type Definitions ===

class BOQItem(TypedDict):
    """Single BOQ line item with pack/wastage info"""
    item_no: str
    description: str
    quantity: float
    unit: str
    material_unit_price: float
    material_total: float
    labor_unit_price: float
    labor_total: float
    total_price: float
    remark: str
    # 🆕 New fields for practical purchasing
    pack_unit: str  # e.g., 'ม้วน', 'กล่อง', 'ชิ้น'
    pack_size: float  # e.g., 100 (per roll), 12 (per box)
    wastage_percent: float  # e.g., 10, 15
    order_qty: float  # Quantity to order (with wastage, rounded to pack)


class BOQSection(TypedDict):
    """BOQ section (e.g., E.1, E.2, E.3)"""
    section_id: str
    section_name: str
    items: List[BOQItem]
    section_total: float


class BOQData(TypedDict):
    """Complete BOQ output"""
    project_name: str
    date: str
    sections: List[BOQSection]
    subtotal_material: float
    subtotal_labor: float
    grand_total: float
    vat_percent: float
    vat_amount: float
    final_total: float
    # 🆕 Price validity (30 days from generation)
    price_valid_date: str  # Format: DD/MM/YYYY
    price_valid_warning: str  # Warning message
    # 🆕 Price source tracking
    price_source: str  # "prices.csv" | "catalog_fallback"


# === Price Catalog (with pack sizes and wastage) ===
# Updated with practical purchasing information
import math
import csv
import os

# 🆕 Global: Track price source
_PRICE_SOURCE = "catalog_fallback"
_LOADED_PRICES: Dict[str, Dict[str, Any]] = {}

# CSV device_code → PRICE_CATALOG key mapping
CSV_KEY_MAPPING = {
    'WIRE-THW-2.5': 'IEC01-2.5',
    'WIRE-THW-4': 'IEC01-4',
    'WIRE-THW-6': 'IEC01-6',
    'WIRE-THW-10': 'IEC01-10',
    'WIRE-THW-16': 'IEC01-16',
    'WIRE-THW-25': 'IEC01-25',
    'WIRE-THW-35': 'IEC01-35',
    'WIRE-THW-50': 'IEC01-50',
    'CB-1P-10A': 'MCB-1P-10AT',
    'CB-1P-16A': 'MCB-1P-16AT',
    'CB-1P-20A': 'MCB-1P-20AT',
    'CB-1P-32A': 'MCB-1P-32AT',
    'CB-2P-100A': 'MCB-2P-100AT',
    'RCBO-1P-16A': 'RCBO-1P-16AT-30mA',
    'RCBO-1P-20A': 'RCBO-1P-20AT-30mA',
}

PRICE_CATALOG: Dict[str, Dict[str, Any]] = {
    # Main Cables - Sold in 100m rolls
    'IEC01-50': {'material': 237.00, 'labor': 30.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    'IEC01-35': {'material': 160.00, 'labor': 25.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    'IEC01-25': {'material': 110.00, 'labor': 20.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    'IEC01-16': {'material': 75.00, 'labor': 18.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    'IEC01-10': {'material': 62.00, 'labor': 13.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    'IEC01-6': {'material': 38.00, 'labor': 10.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    'IEC01-4': {'material': 18.00, 'labor': 9.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    'IEC01-2.5': {'material': 10.00, 'labor': 8.00, 'unit': 'ม.', 'brand': 'Yazaki', 'pack_unit': 'ม้วน', 'pack_size': 100, 'wastage': 0.10, 'alt_brands': ['Thai-Union', 'Phelps Dodge']},
    
    # Conduit - Sold in 4m lengths (bundle of 10 = 40m)
    'EMT-1-1/2': {'material': 121.00, 'labor': 40.00, 'unit': 'ม.', 'brand': 'Panasonic', 'pack_unit': 'มัด(10)', 'pack_size': 40, 'wastage': 0.15, 'alt_brands': ['BS', 'Super']},
    'EMT-1': {'material': 73.00, 'labor': 32.00, 'unit': 'ม.', 'brand': 'Panasonic', 'pack_unit': 'มัด(10)', 'pack_size': 40, 'wastage': 0.15, 'alt_brands': ['BS', 'Super']},
    'PVC-1': {'material': 28.00, 'labor': 34.00, 'unit': 'ม.', 'brand': 'PRI', 'pack_unit': 'เส้น(4m)', 'pack_size': 4, 'wastage': 0.15, 'alt_brands': ['SCG', 'Thai Pipe']},
    'PVC-3/4': {'material': 17.00, 'labor': 32.00, 'unit': 'ม.', 'brand': 'PRI', 'pack_unit': 'เส้น(4m)', 'pack_size': 4, 'wastage': 0.15, 'alt_brands': ['SCG', 'Thai Pipe']},
    'PVC-1/2': {'material': 10.00, 'labor': 30.00, 'unit': 'ม.', 'brand': 'PRI', 'pack_unit': 'เส้น(4m)', 'pack_size': 4, 'wastage': 0.15, 'alt_brands': ['SCG', 'Thai Pipe']},
    
    # Load Center - Sold individually
    'LC-30': {'material': 6108.00, 'labor': 3000.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'LC-24': {'material': 4800.00, 'labor': 2500.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'LC-18': {'material': 3600.00, 'labor': 2000.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    
    # MCB (per pole) - Sold individually, often box of 6
    'MCB-1P-10AT': {'material': 78.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-1P-16AT': {'material': 78.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-1P-20AT': {'material': 78.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-1P-32AT': {'material': 78.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-1P-40AT': {'material': 595.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-2P-10AT': {'material': 156.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-2P-100AT': {'material': 2884.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    
    # [CP-3PH-BOQ] 3-Phase MCB/MCCB - For 3-phase main breakers (Sprint 6)
    'MCB-3P-20AT': {'material': 234.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-3P-32AT': {'material': 234.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-3P-40AT': {'material': 280.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-3P-50AT': {'material': 380.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCB-3P-63AT': {'material': 480.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'MCCB-3P-100AT': {'material': 3200.00, 'labor': 500.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'MCCB-3P-125AT': {'material': 3800.00, 'labor': 500.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'MCCB-3P-160AT': {'material': 4500.00, 'labor': 600.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'MCCB-3P-200AT': {'material': 5200.00, 'labor': 700.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'MCCB-3P-250AT': {'material': 6500.00, 'labor': 800.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    
    # [CP-3PH-BOQ] 3-Phase RCD/RCCB - For 3-phase ground fault protection
    'RCCB-4P-40AT-30mA': {'material': 2800.00, 'labor': 300.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCCB-4P-63AT-30mA': {'material': 3200.00, 'labor': 300.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCCB-4P-100AT-30mA': {'material': 4500.00, 'labor': 400.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    
    # [CP-3PH-BOQ] 3-Phase Load Center / MDB
    'MDB-3PH-8W': {'material': 8500.00, 'labor': 4000.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'MDB-3PH-12W': {'material': 12000.00, 'labor': 5000.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'MDB-3PH-18W': {'material': 16000.00, 'labor': 6000.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    'MDB-3PH-24W': {'material': 22000.00, 'labor': 7000.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Siemens']},
    
    # [CP-3PH-BOQ] CT Meter Components (for >30kW)
    'CT-METER-5A': {'material': 3500.00, 'labor': 1500.00, 'unit': 'ชุด', 'brand': 'MEA', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': []},
    'CT-100-5A': {'material': 800.00, 'labor': 200.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB']},
    'CT-200-5A': {'material': 1200.00, 'labor': 250.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB']},
    'CT-400-5A': {'material': 1800.00, 'labor': 300.00, 'unit': 'ชุด', 'brand': 'Schneider', 'pack_unit': 'ชุด', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB']},
    
    # RCBO - Sold individually
    'RCBO-1P-10AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCBO-1P-16AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCBO-1P-20AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCBO-1P-32AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    
    # Accessories - Lump sum
    'ACCESSORY': {'material': 1000.00, 'labor': 1000.00, 'unit': 'เหมา', 'brand': 'Local', 'pack_unit': 'เหมา', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': []},
}


def load_prices_from_csv() -> tuple[Dict[str, Dict[str, Any]], str]:
    """
    Load prices from prices.csv if available.
    
    Returns:
        (prices_dict, source_name)
    """
    global _PRICE_SOURCE, _LOADED_PRICES
    
    logger.info("[BOQ-PRICE] === Starting price loading ===")
    
    # Try multiple possible paths
    csv_paths = [
        '/app/catalog/prices.csv',  # 🆕 Docker path (RAG service)
        'catalog/prices.csv',  # Local development
        '/home/builder/Desktop/ACA_Mozart/mcp_core_v2/catalog/prices.csv',  # Local absolute
        'mcp_core_v2/catalog/prices.csv',  # Legacy
        '../mcp_core_v2/catalog/prices.csv',  # Legacy
    ]
    
    for csv_path in csv_paths:
        logger.debug(f"[BOQ-PRICE] Trying path: {csv_path}")
        if os.path.exists(csv_path):
            try:
                prices_from_csv: Dict[str, Dict[str, Any]] = {}
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        csv_code = row.get('device_code', '')
                        # Map CSV code to our catalog key
                        catalog_key = CSV_KEY_MAPPING.get(csv_code)
                        if catalog_key and catalog_key in PRICE_CATALOG:
                            # Use CSV price for material, keep other fields from catalog
                            base = PRICE_CATALOG[catalog_key].copy()
                            try:
                                base['material'] = float(row.get('price_thb', base['material']))
                            except ValueError:
                                pass
                            # Update brand from source
                            source = row.get('source', '')
                            if source and source != 'mock':
                                base['brand'] = source
                            prices_from_csv[catalog_key] = base
                
                if prices_from_csv:
                    # Merge: CSV prices override catalog for matching keys
                    merged = PRICE_CATALOG.copy()
                    merged.update(prices_from_csv)
                    _LOADED_PRICES = merged
                    _PRICE_SOURCE = "prices.csv"
                    logger.info(f"[BOQ-PRICE] ✅ SUCCESS: Loaded {len(prices_from_csv)} prices from CSV")
                    logger.info(f"[BOQ-PRICE] CSV path: {csv_path}")
                    logger.info(f"[BOQ-PRICE] Mapped keys: {list(prices_from_csv.keys())[:5]}...")
                    return merged, "prices.csv"
            except Exception as e:
                logger.warning(f"[BOQ] Failed to load prices from {csv_path}: {e}")
    
    # Fallback to hardcoded catalog
    _LOADED_PRICES = PRICE_CATALOG
    _PRICE_SOURCE = "catalog_fallback"
    logger.warning("[BOQ] Using fallback PRICE_CATALOG (no prices.csv found)")
    return PRICE_CATALOG, "catalog_fallback"


def get_price_source() -> str:
    """Get the current price source (for UI display)."""
    return _PRICE_SOURCE


def calculate_order_qty(quantity: float, pack_size: float, wastage: float) -> float:
    """Calculate order quantity with wastage, rounded up to pack size"""
    if pack_size <= 0:
        return quantity
    qty_with_wastage = quantity * (1 + wastage)
    return math.ceil(qty_with_wastage / pack_size) * pack_size


def get_price(key: str) -> Dict[str, Any]:
    """Get price from loaded prices (CSV or catalog fallback)"""
    # Ensure prices are loaded
    if not _LOADED_PRICES:
        load_prices_from_csv()
    
    if key in _LOADED_PRICES:
        return _LOADED_PRICES[key]
    # Try partial match
    for catalog_key in _LOADED_PRICES:
        if catalog_key in key or key in catalog_key:
            return _LOADED_PRICES[catalog_key]
    # Fallback
    logger.warning(f"[BOQ] Price not found for: {key}, using fallback")
    return {'material': 100.00, 'labor': 50.00, 'unit': 'ชิ้น', 'brand': 'Unknown'}


def generate_boq(display_data: Dict[str, Any], project_name: str = "โครงการ") -> BOQData:
    """
    Generate BOQ from DisplayData
    
    Args:
        display_data: Output from compute_display_data()
        project_name: Project name for header
        
    Returns:
        BOQData structure for frontend
    """
    try:
        logger.info("[BOQ-GEN] === Starting BOQ generation ===")
        logger.info(f"[BOQ-GEN] Project: {project_name}")
        
        sections: List[BOQSection] = []
        total_material = 0.0
        total_labor = 0.0
        
        circuits = display_data.get('circuits', [])
        is_three_phase = display_data.get('is_three_phase', False)
        
        logger.info(f"[BOQ-GEN] Input circuits: {len(circuits)}")
        logger.info(f"[BOQ-GEN] Main wire: {display_data.get('main_feeder_size', 'N/A')}")
        logger.info(f"[BOQ-GEN] Main breaker: {display_data.get('main_cb_type', 'N/A')}")
        logger.info(f"[CP-3PH-BOQ] is_three_phase: {is_three_phase}")
        
        # === E.1: Main Cable Section ===
        # [CP-3PH-BOQ] Updated for 3-phase (4 wires instead of 2)
        e1_items: List[BOQItem] = []
        main_wire = display_data.get('main_feeder_size', '10')
        main_wire_key = f"IEC01-{main_wire.replace(' mm²', '').replace('Sq.mm', '').strip()}"
        price = get_price(main_wire_key)
        
        # Main cable (estimate 50m for residential)
        # [CP-3PH-BOQ] 3-phase needs 4 wires (3 phases + neutral), single-phase needs 2
        base_length = 50.0
        if is_three_phase:
            # 3-phase: 4 wires × length
            wire_count = 4
            cable_desc_suffix = '(L1,L2,L3,N)'
        else:
            # Single-phase: 2 wires × length
            wire_count = 2
            cable_desc_suffix = '(Phase+Neutral)'
        
        main_qty = base_length * wire_count
        main_brand = price.get('brand', 'Yazaki')
        main_wire_mm = main_wire.replace(' mm²', '').replace('Sq.mm', '').strip()
        e1_items.append({
            'item_no': '1',
            'description': f'สาย IEC01 (THW) {main_wire_mm} mm² ({main_brand}) - สายเมนหลัก {cable_desc_suffix}',
            'quantity': main_qty,
            'unit': price['unit'],
            'material_unit_price': price['material'],
            'material_total': round(price['material'] * main_qty, 2),
            'labor_unit_price': price['labor'],
            'labor_total': round(price['labor'] * main_qty, 2),
            'total_price': round((price['material'] + price['labor']) * main_qty, 2),
            'remark': f"{main_brand} ({wire_count} เส้น)",
        })
        
        # Ground cable
        grd_key = 'IEC01-10'
        grd_price = get_price(grd_key)
        grd_qty = 15.0
        grd_brand = grd_price.get('brand', 'Yazaki')
        e1_items.append({
            'item_no': '2',
            'description': f'สาย IEC01 (THW) 10 mm² ({grd_brand}) - สายดินหลัก',
            'quantity': grd_qty,
            'unit': grd_price['unit'],
            'material_unit_price': grd_price['material'],
            'material_total': round(grd_price['material'] * grd_qty, 2),
            'labor_unit_price': grd_price['labor'],
            'labor_total': round(grd_price['labor'] * grd_qty, 2),
            'total_price': round((grd_price['material'] + grd_price['labor']) * grd_qty, 2),
            'remark': grd_brand,
        })
        
        # EMT/PVC for main
        conduit_key = 'EMT-1-1/2'
        conduit_price = get_price(conduit_key)
        conduit_qty = 18.0
        conduit_brand = conduit_price.get('brand', 'Panasonic')
        e1_items.append({
            'item_no': '3',
            'description': f'ท่อ EMT 1-1/2" ({conduit_brand}) - ท่อเมนหลัก',
            'quantity': conduit_qty,
            'unit': conduit_price['unit'],
            'material_unit_price': conduit_price['material'],
            'material_total': round(conduit_price['material'] * conduit_qty, 2),
            'labor_unit_price': conduit_price['labor'],
            'labor_total': round(conduit_price['labor'] * conduit_qty, 2),
            'total_price': round((conduit_price['material'] + conduit_price['labor']) * conduit_qty, 2),
            'remark': conduit_brand,
        })
        
        # Accessories
        acc_price = get_price('ACCESSORY')
        e1_items.append({
            'item_no': '4',
            'description': 'อุปกรณ์ประกอบ E.1',
            'quantity': 1.0,
            'unit': 'เหมา',
            'material_unit_price': acc_price['material'],
            'material_total': acc_price['material'],
            'labor_unit_price': acc_price['labor'],
            'labor_total': acc_price['labor'],
            'total_price': acc_price['material'] + acc_price['labor'],
            'remark': '',
        })
        
        e1_total = sum(item['total_price'] for item in e1_items)
        sections.append({
            'section_id': 'E.1',
            'section_name': 'สายเมนไฟฟ้าแรงต่ำ',
            'items': e1_items,
            'section_total': e1_total,
        })
        
        # === E.2: Load Center Section ===
        # [CP-3PH-BOQ] Updated for 3-phase MDB (Sprint 6)
        e2_items: List[BOQItem] = []
        is_three_phase = display_data.get('is_three_phase', False)
        
        # Load Center / MDB
        circuit_count = len(circuits)
        
        if is_three_phase:
            # 3-Phase: Use Main Distribution Board (MDB)
            # Size selection based on circuit count (ways)
            if circuit_count > 18:
                panel_key = 'MDB-3PH-24W'
                panel_slots = '24'
            elif circuit_count > 12:
                panel_key = 'MDB-3PH-18W'
                panel_slots = '18'
            elif circuit_count > 6:
                panel_key = 'MDB-3PH-12W'
                panel_slots = '12'
            else:
                panel_key = 'MDB-3PH-8W'
                panel_slots = '8'
            
            panel_desc = f'ตู้ MDB 3-Phase {panel_slots} วงจร'
            logger.info(f"[CP-3PH-BOQ] 3-Phase MDB selected: {panel_key}")
        else:
            # Single-Phase: Use Load Center
            if circuit_count > 18:
                panel_key = 'LC-30'
                panel_slots = '30'
            elif circuit_count > 12:
                panel_key = 'LC-24'
                panel_slots = '24'
            else:
                panel_key = 'LC-18'
                panel_slots = '18'
            
            panel_desc = f'ตู้ไฟฟ้า Load Center {panel_slots} ช่อง'
        
        lc_price = get_price(panel_key)
        lc_brand = lc_price.get('brand', 'Schneider')
        e2_items.append({
            'item_no': '1',
            'description': f'{panel_desc} ({lc_brand})',
            'quantity': 1.0,
            'unit': 'ชุด',
            'material_unit_price': lc_price['material'],
            'material_total': lc_price['material'],
            'labor_unit_price': lc_price['labor'],
            'labor_total': lc_price['labor'],
            'total_price': lc_price['material'] + lc_price['labor'],
            'remark': lc_brand,
        })
        
        # [CP-3PH-BOQ] Main Breaker - Updated for 3-phase systems (Sprint 6)
        is_three_phase = display_data.get('is_three_phase', False)
        main_breaker = display_data.get('main_breaker', 100)
        
        # Extract numeric rating (handle dict, "100A", or 100 formats)
        if isinstance(main_breaker, dict):
            # Handle dict format: {'rating': 100, 'poles': 3}
            main_breaker_val = int(main_breaker.get('rating', 100))
            # Override is_three_phase if poles is specified
            if main_breaker.get('poles', 2) == 3:
                is_three_phase = True
        elif isinstance(main_breaker, str):
            main_breaker_val = int(''.join(filter(str.isdigit, main_breaker)) or 100)
        else:
            main_breaker_val = int(main_breaker)
        
        if is_three_phase:
            # 3-phase: Use 3P MCCB for ratings ≥100A, else 3P MCB
            if main_breaker_val >= 100:
                main_breaker_key = f"MCCB-3P-{main_breaker_val}AT"
                breaker_type_label = f'MCCB 3P {main_breaker_val}AT 25kA'
            else:
                main_breaker_key = f"MCB-3P-{main_breaker_val}AT"
                breaker_type_label = f'MCB 3P {main_breaker_val}AT 10kA'
            
            logger.info(f"[CP-3PH-BOQ] 3-Phase main breaker: {main_breaker_key}")
        else:
            # Single-phase: Use 2P MCB/MCCB
            main_breaker_key = f"MCB-2P-{main_breaker_val}AT"
            breaker_type_label = f'MCCB 2P {main_breaker_val}AT 10kA'
        
        mb_price = get_price(main_breaker_key)
        mb_brand = mb_price.get('brand', 'Schneider')
        e2_items.append({
            'item_no': '2',
            'description': f'{breaker_type_label} ({mb_brand}) - เมนเบรกเกอร์',
            'quantity': 1.0,
            'unit': 'ตัว',
            'material_unit_price': mb_price['material'],
            'material_total': mb_price['material'],
            'labor_unit_price': mb_price['labor'],
            'labor_total': mb_price['labor'],
            'total_price': mb_price['material'] + mb_price['labor'],
            'remark': f"{mb_brand} {'(3-Phase)' if is_three_phase else ''}".strip(),
        })
        
        # Branch breakers - Group by rating
        mcb_groups: Dict[str, int] = {}
        rcbo_groups: Dict[str, int] = {}
        
        for circuit in circuits:
            breaker_type = circuit.get('breaker_type', 'MCB')
            breaker_at = circuit.get('breaker_at', circuit.get('breaker_rating', 16))
            
            if breaker_type == 'RCBO' or circuit.get('requires_rcbo', False):
                key = f"RCBO-1P-{breaker_at}AT-30mA"
                rcbo_groups[key] = rcbo_groups.get(key, 0) + 1
            else:
                key = f"MCB-1P-{breaker_at}AT"
                mcb_groups[key] = mcb_groups.get(key, 0) + 1
        
        item_no = 3
        for breaker_key, qty in mcb_groups.items():
            b_price = get_price(breaker_key)
            b_brand = b_price.get('brand', 'Schneider')
            # Extract AT value from key like 'MCB-1P-16AT'
            at_val = breaker_key.split('-')[-1].replace('AT', '')
            e2_items.append({
                'item_no': str(item_no),
                'description': f'MCB 1P {at_val}AT 6kA ({b_brand})',
                'quantity': float(qty),
                'unit': 'ตัว',
                'material_unit_price': b_price['material'],
                'material_total': round(b_price['material'] * qty, 2),
                'labor_unit_price': b_price['labor'],
                'labor_total': round(b_price['labor'] * qty, 2),
                'total_price': round((b_price['material'] + b_price['labor']) * qty, 2),
                'remark': b_brand,
            })
            item_no += 1
            
        for breaker_key, qty in rcbo_groups.items():
            b_price = get_price(breaker_key)
            b_brand = b_price.get('brand', 'Schneider')
            # Extract AT value from key like 'RCBO-1P-16AT-30mA'
            at_val = breaker_key.split('-')[2].replace('AT', '')
            e2_items.append({
                'item_no': str(item_no),
                'description': f'RCBO 1P {at_val}AT 30mA ({b_brand})',
                'quantity': float(qty),
                'unit': 'ตัว',
                'material_unit_price': b_price['material'],
                'material_total': round(b_price['material'] * qty, 2),
                'labor_unit_price': b_price['labor'],
                'labor_total': round(b_price['labor'] * qty, 2),
                'total_price': round((b_price['material'] + b_price['labor']) * qty, 2),
                'remark': b_brand,
            })
            item_no += 1
        
        # E.2 Accessories
        e2_items.append({
            'item_no': str(item_no),
            'description': 'อุปกรณ์ประกอบ E.2',
            'quantity': 1.0,
            'unit': 'เหมา',
            'material_unit_price': 1000.0,
            'material_total': 1000.0,
            'labor_unit_price': 1000.0,
            'labor_total': 1000.0,
            'total_price': 2000.0,
            'remark': '',
        })
        
        e2_total = sum(item['total_price'] for item in e2_items)
        logger.info(f"[BOQ-GEN] E.2 Generated: {len(e2_items)} items, Total: {e2_total:,.2f} THB")
        sections.append({
            'section_id': 'E.2',
            'section_name': 'ตู้ไฟฟ้า',
            'items': e2_items,
            'section_total': e2_total,
        })
        
        # === E.3: Branch Wiring Section ===
        e3_items: List[BOQItem] = []
        
        # Group circuits by floor for wiring calculation
        wire_summary: Dict[str, float] = {}  # wire_size -> total_length
        conduit_summary: Dict[str, float] = {}  # conduit_size -> total_length
        
        for circuit in circuits:
            wire_size = circuit.get('wire_size_l', circuit.get('wire_size', '2.5'))
            if isinstance(wire_size, str):
                wire_size = wire_size.replace(' mm²', '').replace('Sq.mm', '').strip()
            wire_key = f"IEC01-{wire_size}"
            
            # Estimate 15m per circuit avg
            wire_summary[wire_key] = wire_summary.get(wire_key, 0) + 15.0
            
            conduit_size = circuit.get('conduit_size', '1/2"')
            conduit_key = f"PVC-{conduit_size}".replace('"', '').replace('1/2', '1/2')
            conduit_summary[conduit_key] = conduit_summary.get(conduit_key, 0) + 15.0
        
        item_no = 1
        for wire_key, qty in wire_summary.items():
            w_price = get_price(wire_key)
            w_brand = w_price.get('brand', 'Yazaki')
            # Extract wire size from key like 'IEC01-2.5'
            wire_mm = wire_key.split('-')[-1]
            e3_items.append({
                'item_no': str(item_no),
                'description': f'สาย IEC01 (THW) {wire_mm} mm² ({w_brand})',
                'quantity': round(qty, 2),
                'unit': w_price['unit'],
                'material_unit_price': w_price['material'],
                'material_total': round(w_price['material'] * qty, 2),
                'labor_unit_price': w_price['labor'],
                'labor_total': round(w_price['labor'] * qty, 2),
                'total_price': round((w_price['material'] + w_price['labor']) * qty, 2),
                'remark': w_brand,
            })
            item_no += 1
            
        for conduit_key, qty in conduit_summary.items():
            c_price = get_price(conduit_key)
            c_brand = c_price.get('brand', 'PRI')
            # Extract conduit size from key like 'PVC-1/2'
            conduit_size = conduit_key.split('-')[-1]
            e3_items.append({
                'item_no': str(item_no),
                'description': f'ท่อ PVC {conduit_size}" ({c_brand})',
                'quantity': round(qty, 2),
                'unit': c_price['unit'],
                'material_unit_price': c_price['material'],
                'material_total': round(c_price['material'] * qty, 2),
                'labor_unit_price': c_price['labor'],
                'labor_total': round(c_price['labor'] * qty, 2),
                'total_price': round((c_price['material'] + c_price['labor']) * qty, 2),
                'remark': c_brand,
            })
            item_no += 1
        
        # E.3 Accessories
        e3_items.append({
            'item_no': str(item_no),
            'description': 'อุปกรณ์ประกอบ E.3 (Flexible, Junction Box, etc.)',
            'quantity': 1.0,
            'unit': 'เหมา',
            'material_unit_price': 5000.0,
            'material_total': 5000.0,
            'labor_unit_price': 2000.0,
            'labor_total': 2000.0,
            'total_price': 7000.0,
            'remark': '',
        })
        
        e3_total = sum(item['total_price'] for item in e3_items)
        sections.append({
            'section_id': 'E.3',
            'section_name': 'สายไฟฟ้าและท่อร้อยสาย',
            'items': e3_items,
            'section_total': e3_total,
        })
        
        # === E.4: [CP-SOLAR-BOQ] Solar PV System (if present) ===
        has_solar = display_data.get('has_solar', False)
        if has_solar:
            e4_items: List[BOQItem] = []
            solar_capacity_kw = display_data.get('solar_capacity_kw', 0)
            solar_inverter = display_data.get('solar_inverter', {})
            solar_dc_circuit = display_data.get('solar_dc_circuit', {})
            solar_ac_circuit = display_data.get('solar_ac_circuit', {})
            solar_protection = display_data.get('solar_protection', [])
            
            logger.info(f"[CP-SOLAR-BOQ] Generating Solar section: {solar_capacity_kw:.1f}kW")
            
            item_no = 1
            
            # 1. Solar Panels (estimate ~3,000-4,000 THB per panel, 450W per panel)
            num_panels = math.ceil(solar_capacity_kw * 1000 / 450)
            panel_price = 3500.0  # Per panel (450W)
            e4_items.append({
                'item_no': str(item_no),
                'description': f'แผงโซลาร์ 450W Mono PERC (Tier 1) - {solar_capacity_kw:.1f}kW system',
                'quantity': num_panels,
                'unit': 'แผง',
                'material_unit_price': panel_price,
                'material_total': round(panel_price * num_panels, 2),
                'labor_unit_price': 500.0,  # Installation per panel
                'labor_total': round(500.0 * num_panels, 2),
                'total_price': round((panel_price + 500.0) * num_panels, 2),
                'remark': 'Longi, JA Solar, Trina',
            })
            item_no += 1
            
            # 2. Grid-Tie Inverter
            inverter_kw = solar_inverter.get('rated_kw', solar_capacity_kw * 0.9)
            inverter_price_per_kw = 3500.0  # THB per kW for string inverter
            inverter_total = round(inverter_kw * inverter_price_per_kw, 2)
            e4_items.append({
                'item_no': str(item_no),
                'description': f'อินเวอร์เตอร์ Grid-Tie {inverter_kw:.0f}kW ({solar_inverter.get("phase_type", "1-Phase")})',
                'quantity': 1,
                'unit': 'ตัว',
                'material_unit_price': inverter_total,
                'material_total': inverter_total,
                'labor_unit_price': 2000.0,  # Inverter installation
                'labor_total': 2000.0,
                'total_price': round(inverter_total + 2000.0, 2),
                'remark': 'Huawei, SMA, GoodWe',
            })
            item_no += 1
            
            # 3. DC Solar Cable (PV1-F)
            dc_wire_size = solar_dc_circuit.get('wire_size_mm2', 4.0)
            dc_cable_length = 50.0  # Estimate 50m for rooftop
            dc_cable_price = 25.0 if dc_wire_size <= 4 else 35.0  # Per meter
            e4_items.append({
                'item_no': str(item_no),
                'description': f'สาย DC PV1-F {dc_wire_size}mm² (UV resistant, double insulated)',
                'quantity': dc_cable_length,
                'unit': 'ม.',
                'material_unit_price': dc_cable_price,
                'material_total': round(dc_cable_price * dc_cable_length, 2),
                'labor_unit_price': 8.0,
                'labor_total': round(8.0 * dc_cable_length, 2),
                'total_price': round((dc_cable_price + 8.0) * dc_cable_length, 2),
                'remark': 'TUV certified',
            })
            item_no += 1
            
            # 4. DC Disconnect Switch
            dc_breaker_a = solar_dc_circuit.get('dc_breaker_a', 20)
            e4_items.append({
                'item_no': str(item_no),
                'description': f'DC Disconnect Switch 600V {dc_breaker_a}A',
                'quantity': 1,
                'unit': 'ตัว',
                'material_unit_price': 1500.0,
                'material_total': 1500.0,
                'labor_unit_price': 300.0,
                'labor_total': 300.0,
                'total_price': 1800.0,
                'remark': 'NEC 690.15 required',
            })
            item_no += 1
            
            # 5. AC Breaker for Solar
            ac_breaker_a = solar_ac_circuit.get('ac_breaker_a', 20)
            ac_breaker_type = solar_ac_circuit.get('breaker_type', 'RCBO 30mA')
            ac_breaker_price = 1200.0 if 'RCBO' in ac_breaker_type else 250.0
            e4_items.append({
                'item_no': str(item_no),
                'description': f'{ac_breaker_type} {ac_breaker_a}A (Solar AC)',
                'quantity': 1,
                'unit': 'ตัว',
                'material_unit_price': ac_breaker_price,
                'material_total': ac_breaker_price,
                'labor_unit_price': 0.0,
                'labor_total': 0.0,
                'total_price': ac_breaker_price,
                'remark': 'Schneider/ABB',
            })
            item_no += 1
            
            # 6. Surge Protectors (DC + AC)
            e4_items.append({
                'item_no': str(item_no),
                'description': 'DC Surge Protector Type 2 (600V DC)',
                'quantity': 1,
                'unit': 'ตัว',
                'material_unit_price': 2500.0,
                'material_total': 2500.0,
                'labor_unit_price': 200.0,
                'labor_total': 200.0,
                'total_price': 2700.0,
                'remark': 'Required for lightning protection',
            })
            item_no += 1
            
            # 7. Mounting Structure (rooftop)
            structure_per_panel = 800.0  # Aluminum racking per panel
            e4_items.append({
                'item_no': str(item_no),
                'description': 'โครงรางอลูมิเนียม + ขาติดตั้ง (Roof mounting)',
                'quantity': num_panels,
                'unit': 'ชุด',
                'material_unit_price': structure_per_panel,
                'material_total': round(structure_per_panel * num_panels, 2),
                'labor_unit_price': 400.0,  # Installation per panel
                'labor_total': round(400.0 * num_panels, 2),
                'total_price': round((structure_per_panel + 400.0) * num_panels, 2),
                'remark': 'Anodized aluminum',
            })
            item_no += 1
            
            # 8. Installation & Commissioning
            installation_fee = round(solar_capacity_kw * 1500.0, 2)  # 1,500 THB per kW
            e4_items.append({
                'item_no': str(item_no),
                'description': 'ค่าติดตั้ง ทดสอบ และ Commissioning',
                'quantity': 1,
                'unit': 'เหมา',
                'material_unit_price': 0.0,
                'material_total': 0.0,
                'labor_unit_price': installation_fee,
                'labor_total': installation_fee,
                'total_price': installation_fee,
                'remark': f'{solar_capacity_kw:.1f}kW × 1,500 THB/kW',
            })
            
            e4_total = sum(item['total_price'] for item in e4_items)
            sections.append({
                'section_id': 'E.4',
                'section_name': f'ระบบโซลาร์เซลล์ {solar_capacity_kw:.1f}kW (On-Grid)',
                'items': e4_items,
                'section_total': e4_total,
            })
            
            logger.info(f"[CP-SOLAR-BOQ] Solar section total: {e4_total:,.2f} THB")
        
        # === Calculate Totals ===
        for section in sections:
            for item in section['items']:
                total_material += item['material_total']
                total_labor += item['labor_total']
        
        grand_total = total_material + total_labor
        vat_percent = 7.0
        vat_amount = round(grand_total * vat_percent / 100, 2)
        final_total = round(grand_total + vat_amount, 2)
        
        # Generate date
        from datetime import datetime
        date_str = datetime.now().strftime('%d/%m/%Y')
        
        from datetime import timedelta
        price_valid_until = datetime.now() + timedelta(days=30)
        price_valid_date = price_valid_until.strftime('%d/%m/%Y')
        
        # 🆕 Get price source (CSV or fallback)
        current_price_source = get_price_source()
        
        boq_data: BOQData = {
            'project_name': project_name,
            'date': date_str,
            'sections': sections,
            'subtotal_material': round(total_material, 2),
            'subtotal_labor': round(total_labor, 2),
            'grand_total': round(grand_total, 2),
            'vat_percent': vat_percent,
            'vat_amount': vat_amount,
            'final_total': final_total,
            # 🆕 Price validity
            'price_valid_date': price_valid_date,
            'price_valid_warning': f'⚠️ ราคา ณ วันที่ {date_str} มีอายุ 30 วัน (ถึง {price_valid_date})',
            # 🆕 Price source
            'price_source': current_price_source,
        }
        
        # 🆕 Verbose logging for debugging
        logger.info("[BOQ-GEN] === BOQ Generation Complete ===")
        logger.info(f"[BOQ-GEN] Sections: {len(sections)}")
        logger.info(f"[BOQ-GEN] Material Total: {total_material:,.2f} THB")
        logger.info(f"[BOQ-GEN] Labor Total: {total_labor:,.2f} THB")
        logger.info(f"[BOQ-GEN] Grand Total: {grand_total:,.2f} THB")
        logger.info(f"[BOQ-GEN] Final (with VAT): {final_total:,.2f} THB")
        logger.info(f"[BOQ-GEN] Price Source: {current_price_source}")
        logger.info(f"[BOQ-GEN] Price Valid Until: {price_valid_date}")
        return boq_data
        
    except Exception as e:
        logger.error(f"[BOQ] Error generating BOQ: {e}")
        # Return empty BOQ with error
        return {
            'project_name': project_name,
            'date': '',
            'sections': [],
            'subtotal_material': 0.0,
            'subtotal_labor': 0.0,
            'grand_total': 0.0,
            'vat_percent': 7.0,
            'vat_amount': 0.0,
            'final_total': 0.0,
            'price_valid_date': '',
            'price_valid_warning': '❌ Error generating BOQ',
            'price_source': 'error',
        }
