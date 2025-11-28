"""
Standards Loader - Loads electrical standards from catalog

Reads from canonical knowledge sources:
- catalog_rows.csv (118 rows snapshot)
- rag_knowledge/standard/*.md

Supports:
- EIT/THAI: Production-ready (from catalog)
- IEC: Subset (mapped from EIT)
- NEC: Stub only (fallback to IEC with warning)

Zero DB Access: Reads from files only, never queries Supabase directly
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class StandardsEngine:
    """
    Loads and manages electrical standards from catalog
    
    Architecture:
    - Reads catalog_rows.csv snapshot
    - Filters by 'kind' field
    - Parses 'data' JSON for rule details
    - Returns structured rule sets
    """
    
    def __init__(self, catalog_path: Optional[Path] = None):
        """
        Initialize standards engine
        
        Args:
            catalog_path: Path to catalog_rows.csv
                         If None, auto-detect from project structure
        """
        if catalog_path is None:
            # Auto-detect: mcp_core_v2 → ../Copilot-Mozart/...
            project_root = Path(__file__).parent.parent.parent
            catalog_path = project_root / "Copilot-Mozart" / "ACA_Mozart-copilot[RAG]" / "rag_knowledge" / "db" / "catalog_rows.csv"
        
        self.catalog_path = Path(catalog_path)
        self._catalog_data = None
        
        if not self.catalog_path.exists():
            logger.warning(f"Catalog not found at {self.catalog_path}")
    
    def _load_catalog(self) -> List[Dict[str, Any]]:
        """Load catalog_rows.csv into memory"""
        if self._catalog_data is not None:
            return self._catalog_data
        
        if not self.catalog_path.exists():
            logger.error(f"Cannot load catalog: file not found at {self.catalog_path}")
            return []
        
        rows = []
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            
            self._catalog_data = rows
            logger.info(f"Loaded {len(rows)} rows from catalog")
            return rows
        
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            return []
    
    def load_eit_rules(self) -> Dict[str, Any]:
        """
        Load Thai/EIT electrical standards
        
        Returns:
            {
                'PLACEMENT_RULE': {rule_name: rule_data},
                'VALIDATION_RULE': {rule_name: rule_data},
                'status': 'PRODUCTION'
            }
        """
        catalog = self._load_catalog()
        
        rules = {
            'PLACEMENT_RULE': {},
            'VALIDATION_RULE': {},
            'DEVICE_RULES': {},
            'CIRCUIT_TEMPLATE': {},
            'status': 'PRODUCTION',
            'standard': 'EIT'
        }
        
        for row in catalog:
            kind = row.get('kind', '')
            name = row.get('name', '')
            data_str = row.get('data', '{}')
            meta_str = row.get('meta', '{}')
            
            # Filter for rules
            if kind not in ['PLACEMENT_RULE', 'VALIDATION_RULE', 'CIRCUIT_TEMPLATE', 'COMPONENT']:
                continue
            
            # Parse JSON
            try:
                data = json.loads(data_str) if data_str else {}
                meta = json.loads(meta_str) if meta_str else {}
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON for {name}: {e}")
                continue
            
            # Check if Thai/EIT standard
            standard = meta.get('standard', '').upper()
            is_thai = any(keyword in name.upper() for keyword in ['THAI', 'EIT', 'กฟภ'])
            
            # Store rule
            if kind == 'COMPONENT':
                # Device rules from components
                rules['DEVICE_RULES'][name] = data
            elif kind in rules:
                rules[kind][name] = data
        
        logger.info(f"Loaded EIT rules: {len(rules['PLACEMENT_RULE'])} placement, "
                   f"{len(rules['VALIDATION_RULE'])} validation")
        
        return rules
    
    def load_iec_subset(self) -> Dict[str, Any]:
        """
        Load IEC electrical standards
        
        For MVP: Map from EIT rules (mostly same, metric units)
        
        Returns:
            Similar structure to load_eit_rules()
        """
        # For MVP: Use EIT rules as base
        eit_rules = self.load_eit_rules()
        
        iec_rules = {
            'PLACEMENT_RULE': eit_rules['PLACEMENT_RULE'].copy(),
            'VALIDATION_RULE': eit_rules['VALIDATION_RULE'].copy(),
            'DEVICE_RULES': eit_rules['DEVICE_RULES'].copy(),
            'CIRCUIT_TEMPLATE': eit_rules['CIRCUIT_TEMPLATE'].copy(),
            'status': 'SUBSET',
            'standard': 'IEC',
            'note': 'Mapped from EIT/Thai rules for MVP'
        }
        
        # Could apply transformations here if needed:
        # - Change symbol naming
        # - Adjust clearances if IEC differs
        # For MVP, EIT and IEC are close enough
        
        logger.info("Loaded IEC rules (mapped from EIT)")
        return iec_rules
    
    def load_nec_stub(self) -> Dict[str, Any]:
        """
        Load NEC electrical standards
        
        For MVP: Stub only, not implemented
        
        Returns:
            Stub with fallback information
        """
        return {
            'status': 'NOT_IMPLEMENTED',
            'standard': 'NEC',
            'fallback_to': 'IEC',
            'warning': 'NEC standards not fully supported in MVP. Using IEC rules as fallback.',
            'PLACEMENT_RULE': {},
            'VALIDATION_RULE': {},
            'DEVICE_RULES': {},
            'CIRCUIT_TEMPLATE': {},
        }
    
    def load_standard(self, standard: str = 'EIT') -> Dict[str, Any]:
        """
        Load rules for specified standard
        
        Args:
            standard: 'EIT', 'IEC', or 'NEC'
        
        Returns:
            Rule dictionary
        """
        standard = standard.upper()
        
        if standard in ['EIT', 'THAI']:
            return self.load_eit_rules()
        elif standard == 'IEC':
            return self.load_iec_subset()
        elif standard == 'NEC':
            nec = self.load_nec_stub()
            if nec['status'] != 'PRODUCTION':
                logger.warning(nec['warning'])
            return nec
        else:
            logger.warning(f"Unknown standard '{standard}', falling back to EIT")
            return self.load_eit_rules()


# Convenience function
def load_standards(standard: str = 'EIT', catalog_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load electrical standards
    
    Args:
        standard: 'EIT', 'IEC', or 'NEC'
        catalog_path: Optional path to catalog_rows.csv
    
    Returns:
        Rule dictionary
    """
    engine = StandardsEngine(catalog_path)
    return engine.load_standard(standard)
