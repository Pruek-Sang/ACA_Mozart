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


# === Price Catalog (with pack sizes and wastage) ===
# Updated with practical purchasing information
import math

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
    
    # RCBO - Sold individually
    'RCBO-1P-10AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCBO-1P-16AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCBO-1P-20AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    'RCBO-1P-32AT-30mA': {'material': 1133.00, 'labor': 0.00, 'unit': 'ตัว', 'brand': 'Schneider', 'pack_unit': 'ตัว', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': ['ABB', 'Hager']},
    
    # Accessories - Lump sum
    'ACCESSORY': {'material': 1000.00, 'labor': 1000.00, 'unit': 'เหมา', 'brand': 'Local', 'pack_unit': 'เหมา', 'pack_size': 1, 'wastage': 0.0, 'alt_brands': []},
}


def calculate_order_qty(quantity: float, pack_size: float, wastage: float) -> float:
    """Calculate order quantity with wastage, rounded up to pack size"""
    if pack_size <= 0:
        return quantity
    qty_with_wastage = quantity * (1 + wastage)
    return math.ceil(qty_with_wastage / pack_size) * pack_size


def get_price(key: str) -> Dict[str, Any]:
    """Get price from catalog with fallback"""
    if key in PRICE_CATALOG:
        return PRICE_CATALOG[key]
    # Try partial match
    for catalog_key in PRICE_CATALOG:
        if catalog_key in key or key in catalog_key:
            return PRICE_CATALOG[catalog_key]
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
        sections: List[BOQSection] = []
        total_material = 0.0
        total_labor = 0.0
        
        circuits = display_data.get('circuits', [])
        
        # === E.1: Main Cable Section ===
        e1_items: List[BOQItem] = []
        main_wire = display_data.get('main_feeder_size', '10')
        main_wire_key = f"IEC01-{main_wire.replace(' mm²', '').replace('Sq.mm', '').strip()}"
        price = get_price(main_wire_key)
        
        # Main cable (estimate 50m for residential)
        main_qty = 50.0
        e1_items.append({
            'item_no': '1',
            'description': f'สาย {main_wire_key} (สายเมนหลักจากมิเตอร์ถึงตู้ไฟ)',
            'quantity': main_qty,
            'unit': price['unit'],
            'material_unit_price': price['material'],
            'material_total': round(price['material'] * main_qty, 2),
            'labor_unit_price': price['labor'],
            'labor_total': round(price['labor'] * main_qty, 2),
            'total_price': round((price['material'] + price['labor']) * main_qty, 2),
            'remark': price.get('brand', 'Yazaki'),
        })
        
        # Ground cable
        grd_key = 'IEC01-10'
        grd_price = get_price(grd_key)
        grd_qty = 15.0
        e1_items.append({
            'item_no': '2',
            'description': f'สาย {grd_key} (สายหลักดิน)',
            'quantity': grd_qty,
            'unit': grd_price['unit'],
            'material_unit_price': grd_price['material'],
            'material_total': round(grd_price['material'] * grd_qty, 2),
            'labor_unit_price': grd_price['labor'],
            'labor_total': round(grd_price['labor'] * grd_qty, 2),
            'total_price': round((grd_price['material'] + grd_price['labor']) * grd_qty, 2),
            'remark': grd_price.get('brand', 'Yazaki'),
        })
        
        # EMT/PVC for main
        conduit_key = 'EMT-1-1/2'
        conduit_price = get_price(conduit_key)
        conduit_qty = 18.0
        e1_items.append({
            'item_no': '3',
            'description': f'ท่อ {conduit_key} (ท่อเมน)',
            'quantity': conduit_qty,
            'unit': conduit_price['unit'],
            'material_unit_price': conduit_price['material'],
            'material_total': round(conduit_price['material'] * conduit_qty, 2),
            'labor_unit_price': conduit_price['labor'],
            'labor_total': round(conduit_price['labor'] * conduit_qty, 2),
            'total_price': round((conduit_price['material'] + conduit_price['labor']) * conduit_qty, 2),
            'remark': conduit_price.get('brand', 'Panasonic'),
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
        e2_items: List[BOQItem] = []
        
        # Load Center
        circuit_count = len(circuits)
        lc_size = 'LC-30' if circuit_count > 18 else ('LC-24' if circuit_count > 12 else 'LC-18')
        lc_price = get_price(lc_size)
        e2_items.append({
            'item_no': '1',
            'description': f'ตู้ไฟฟ้า Load Center {lc_size.split("-")[1]} ช่อง',
            'quantity': 1.0,
            'unit': 'ชุด',
            'material_unit_price': lc_price['material'],
            'material_total': lc_price['material'],
            'labor_unit_price': lc_price['labor'],
            'labor_total': lc_price['labor'],
            'total_price': lc_price['material'] + lc_price['labor'],
            'remark': lc_price.get('brand', 'Schneider'),
        })
        
        # Main Breaker
        main_breaker = display_data.get('main_breaker', 100)
        main_breaker_key = f"MCB-2P-{main_breaker}AT"
        mb_price = get_price(main_breaker_key)
        e2_items.append({
            'item_no': '2',
            'description': f'MCB 2P {main_breaker}AT, 30kA (เมนเบรกเกอร์)',
            'quantity': 1.0,
            'unit': 'ตัว',
            'material_unit_price': mb_price['material'],
            'material_total': mb_price['material'],
            'labor_unit_price': mb_price['labor'],
            'labor_total': mb_price['labor'],
            'total_price': mb_price['material'] + mb_price['labor'],
            'remark': mb_price.get('brand', 'Schneider'),
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
            e2_items.append({
                'item_no': str(item_no),
                'description': breaker_key.replace("-", " ").replace("1P", "1P "),
                'quantity': float(qty),
                'unit': 'ตัว',
                'material_unit_price': b_price['material'],
                'material_total': round(b_price['material'] * qty, 2),
                'labor_unit_price': b_price['labor'],
                'labor_total': round(b_price['labor'] * qty, 2),
                'total_price': round((b_price['material'] + b_price['labor']) * qty, 2),
                'remark': b_price.get('brand', 'Schneider'),
            })
            item_no += 1
            
        for breaker_key, qty in rcbo_groups.items():
            b_price = get_price(breaker_key)
            e2_items.append({
                'item_no': str(item_no),
                'description': breaker_key.replace("-", " "),
                'quantity': float(qty),
                'unit': 'ตัว',
                'material_unit_price': b_price['material'],
                'material_total': round(b_price['material'] * qty, 2),
                'labor_unit_price': b_price['labor'],
                'labor_total': round(b_price['labor'] * qty, 2),
                'total_price': round((b_price['material'] + b_price['labor']) * qty, 2),
                'remark': b_price.get('brand', 'Schneider'),
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
            e3_items.append({
                'item_no': str(item_no),
                'description': f'สาย {wire_key} (วงจรสาขา)',
                'quantity': round(qty, 2),
                'unit': w_price['unit'],
                'material_unit_price': w_price['material'],
                'material_total': round(w_price['material'] * qty, 2),
                'labor_unit_price': w_price['labor'],
                'labor_total': round(w_price['labor'] * qty, 2),
                'total_price': round((w_price['material'] + w_price['labor']) * qty, 2),
                'remark': w_price.get('brand', 'Yazaki'),
            })
            item_no += 1
            
        for conduit_key, qty in conduit_summary.items():
            c_price = get_price(conduit_key)
            e3_items.append({
                'item_no': str(item_no),
                'description': f'ท่อ {conduit_key}',
                'quantity': round(qty, 2),
                'unit': c_price['unit'],
                'material_unit_price': c_price['material'],
                'material_total': round(c_price['material'] * qty, 2),
                'labor_unit_price': c_price['labor'],
                'labor_total': round(c_price['labor'] * qty, 2),
                'total_price': round((c_price['material'] + c_price['labor']) * qty, 2),
                'remark': c_price.get('brand', 'PRI'),
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
        }
        
        logger.info(f"[BOQ] Generated BOQ: {len(sections)} sections, Total: {final_total:,.2f} THB")
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
        }
