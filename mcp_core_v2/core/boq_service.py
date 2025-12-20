"""
BOQ Service for generating Bill of Quantities from Design Result.
Uses catalog rules for routing estimation and external price database.
"""

import csv
import logging
import math
import os
from typing import List, Dict, Any, Optional

# Import BoqItem from contracts (single source of truth)
try:
    from models.contracts import BoqItem
except ImportError:
    # Fallback for standalone testing
    from pydantic import BaseModel
    class BoqItem(BaseModel):
        item_code: str
        description: str
        quantity: float
        unit: str
        unit_price: float
        total_price: float
        source: str = "Estimate"

logger = logging.getLogger(__name__)

class BoqService:
    def __init__(self, catalog_path: str, prices_path: str):
        self.catalog_path = catalog_path
        self.prices_path = prices_path
        self.prices = self._load_prices()
        self.routing_rules = self._load_routing_rules()

    def _load_prices(self) -> Dict[str, Dict[str, Any]]:
        """Load prices from CSV - supports multiple sources per device."""
        prices = {}
        try:
            # Try multi-source prices first, fallback to simple prices
            multi_prices_path = self.prices_path.replace('prices.csv', 'prices_multi.csv')
            prices_file = multi_prices_path if os.path.exists(multi_prices_path) else self.prices_path
            
            with open(prices_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    device_code = row.get('device_code', '')
                    
                    # Skip comment lines (start with #) and empty rows
                    if not device_code or device_code.startswith('#'):
                        continue
                    
                    source = row.get('source', 'Unknown')
                    
                    if device_code not in prices:
                        prices[device_code] = {'sources': [], 'cheapest': None}
                    
                    price_entry = {
                        'price': float(row.get('price_thb', 0)),
                        'unit': row.get('unit', 'pcs'),
                        'source': source,
                        'url': row.get('url', '')
                    }
                    prices[device_code]['sources'].append(price_entry)
                    
                    # Track cheapest
                    if prices[device_code]['cheapest'] is None or \
                       price_entry['price'] < prices[device_code]['cheapest']['price']:
                        prices[device_code]['cheapest'] = price_entry
                        
        except FileNotFoundError:
            logger.warning(f"Price file not found at {self.prices_path}")
        return prices

    def _load_routing_rules(self) -> Dict[str, Any]:
        """Load routing rules from catalog_rows.csv."""
        import json
        rules = {}
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Only process ROUTING_RULE kind
                    if row.get('kind') == 'ROUTING_RULE':
                        rule_name = row.get('name', '')
                        try:
                            data = json.loads(row.get('data', '{}'))
                            rules[rule_name] = {
                                'allowed_path': data.get('allowed_path', []),
                                'min_bend_radius_mm': data.get('min_bend_radius_mm', 150),
                                'max_conduit_fill_pct': data.get('max_conduit_fill_pct', 40),
                                # Default estimates for wire length calculation
                                'vertical_drop_m': 2.5,
                                'overhead_factor': 1.2
                            }
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse data for routing rule: {rule_name}")
        except FileNotFoundError:
            logger.warning(f"Catalog file not found at {self.catalog_path}")
        
        # Fallback default if no rules found
        if not rules:
            rules["DEFAULT"] = {
                'vertical_drop_m': 2.5,
                'overhead_factor': 1.2
            }
        return rules

    def generate_boq(self, design_result: Any) -> List[BoqItem]:
        """Generate BOQ from design result.
        
        Note: This method is a placeholder. Use generate_from_dicts() instead
        which accepts the raw calculation dictionaries.
        """
        # The actual integration happens in ResultBuilder which has the raw dicts.
        # Use generate_from_dicts() for the real implementation.
        return []

    def generate_from_dicts(self, 
                          breaker_selections: Dict[str, Any],
                          wire_sizing: Dict[str, Any],
                          loads: List[Any]) -> List[BoqItem]:
        
        boq_map: Dict[str, float] = {} # code -> qty

        # 1. Breakers + Consumer Unit
        num_circuits = len(breaker_selections)
        for circuit_id, data in breaker_selections.items():
            breaker_type = data.get('breaker_type', 'CB-1P-16A') # Default fallback
            boq_map[breaker_type] = boq_map.get(breaker_type, 0) + 1
        
        # Add consumer unit based on circuit count
        if num_circuits > 0:
            if num_circuits <= 12:
                boq_map['CONSUMER-UNIT-12'] = 1
            elif num_circuits <= 18:
                boq_map['CONSUMER-UNIT-18'] = 1
            else:
                boq_map['CONSUMER-UNIT-24'] = 1

        # 2. Wires (Estimate length based on circuit info)
        # Uses routing rules and circuit data to estimate more accurately
        for circuit_id, data in wire_sizing.items():
            wire_size = data.get('size_mm2', '2.5')
            wire_type = f"WIRE-THW-{wire_size}"
            
            # Calculate length based on available data
            # Priority: explicit length > room area estimate > default
            if 'cable_length_m' in data:
                # Best case: explicit length from calculation
                length = float(data['cable_length_m'])
            elif 'room_area_sqm' in data:
                # Estimate: perimeter approximation + vertical drop
                area = float(data['room_area_sqm'])
                perimeter = math.sqrt(area) * 4  # Approximate perimeter
                vertical_drop = 2.5  # Standard ceiling height
                overhead = 1.2  # 20% for bends/waste
                length = (perimeter / 2 + vertical_drop) * overhead
            else:
                # Default fallback: conservative 15m per circuit
                length = 15.0
            
            boq_map[wire_type] = boq_map.get(wire_type, 0) + length
            
            # Add conduit for each circuit (estimate: same length as wire)
            boq_map['CONDUIT-EMT-1/2'] = boq_map.get('CONDUIT-EMT-1/2', 0) + (length / 3)  # 3m per stick

        # 3. Devices (Loads) + Switches + Junction Boxes
        # ElectricalLoad uses 'id' field (e.g., "COMP-OUTLET-16A") as device identifier
        # We need to extract a countable code from the load's id or name
        for load in loads:
            # Handle both Pydantic objects and dicts
            if hasattr(load, 'id'):
                # Pydantic object - use name for device type, quantity for count
                code = getattr(load, 'name', None) or load.id
                qty = getattr(load, 'quantity', 1)
            elif isinstance(load, dict):
                code = load.get('name') or load.get('id') or load.get('device_code')
                qty = load.get('quantity', 1)
            else:
                code = None
                qty = 1
            
            if code:
                boq_map[code] = boq_map.get(code, 0) + qty
                
                # Add switch for each lighting load
                load_type = None
                if hasattr(load, 'load_type'):
                    load_type = str(load.load_type)
                elif isinstance(load, dict):
                    load_type = load.get('load_type', '')
                
                if load_type and 'lighting' in str(load_type).lower():
                    boq_map['COMP-SWITCH-1GANG'] = boq_map.get('COMP-SWITCH-1GANG', 0) + 1
                    boq_map['COMP-JUNCTION-BOX'] = boq_map.get('COMP-JUNCTION-BOX', 0) + qty
        
        # 4. Add grounding system (1 per project)
        boq_map['COMP-GROUND-ROD'] = 1
        boq_map['WIRE-GROUND-10'] = 15  # 15 meters ground wire

        # Convert to BoqItem list (use cheapest price, but include all sources info)
        result = []
        for code, qty in boq_map.items():
            price_data = self.prices.get(code)
            
            if price_data and 'cheapest' in price_data:
                # New multi-source format
                cheapest = price_data['cheapest']
                all_sources = price_data['sources']
                
                # Build description with price comparison
                if len(all_sources) > 1:
                    comparison = " | ".join([
                        f"{s['source']}: ฿{s['price']:.0f}" for s in all_sources
                    ])
                    description = f"{code} ({comparison})"
                else:
                    description = f"{code}"
                
                item = BoqItem(
                    item_code=code,
                    description=description,
                    quantity=qty,
                    unit=cheapest['unit'],
                    unit_price=cheapest['price'],
                    total_price=qty * cheapest['price'],
                    source=f"{cheapest['source']} ⭐ถูกสุด"
                )
            else:
                # Fallback for unknown items
                item = BoqItem(
                    item_code=code,
                    description=f"{code}",
                    quantity=qty,
                    unit='pcs',
                    unit_price=0.0,
                    total_price=0.0,
                    source='ไม่พบราคา'
                )
            result.append(item)
            
        return result
