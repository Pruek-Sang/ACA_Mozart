"""
File-based Catalog DAL - Reads catalog data from CSV files.

Replaces Supabase with local CSV file from rag_knowledge/db/catalog_rows.csv
This is the Single Source of Truth for both RAG and MCP.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# Path to catalog CSV (relative to mcp_core_v2/)
RAG_KNOWLEDGE_PATH = Path(__file__).parent.parent.parent / "Copilot-Mozart" / "ACA_Mozart-copilot[RAG]" / "rag_knowledge" / "db"
CATALOG_CSV = RAG_KNOWLEDGE_PATH / "catalog_rows.csv"


class CatalogRow:
    """Represents a single row from catalog_rows.csv"""
    
    def __init__(self, row: Dict[str, str]):
        self.id = row.get('id', '')
        self.kind = row.get('kind', '')
        self.name = row.get('name', '')
        self.description = row.get('description', '')
        self.version = row.get('version', '1.0.0')
        self.is_active = row.get('is_active', 'true').lower() == 'true'
        
        # Parse JSON data column
        data_str = row.get('data', '{}')
        try:
            self.data = json.loads(data_str) if data_str else {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON for {self.name}: {data_str[:100]}")
            self.data = {}
        
        # Parse meta column
        meta_str = row.get('meta', '{}')
        try:
            self.meta = json.loads(meta_str) if meta_str else {}
        except json.JSONDecodeError:
            self.meta = {}
    
    def get(self, key: str, default=None):
        """Get value from data dict"""
        return self.data.get(key, default)
    
    def __repr__(self):
        return f"CatalogRow(kind={self.kind}, name={self.name})"


class FileCatalogDAL:
    """
    File-based Data Access Layer for electrical catalog.
    
    Reads from rag_knowledge/db/catalog_rows.csv
    Provides same interface as Supabase-based CatalogDAL
    """
    
    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or CATALOG_CSV
        self._cache: Dict[str, List[CatalogRow]] = {}
        self._load_catalog()
    
    def _load_catalog(self):
        """Load and parse CSV file"""
        if not self.csv_path.exists():
            logger.error(f"Catalog CSV not found: {self.csv_path}")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    catalog_row = CatalogRow(row)
                    if not catalog_row.is_active:
                        continue  # Skip deprecated/inactive rows
                    
                    kind = catalog_row.kind
                    if kind not in self._cache:
                        self._cache[kind] = []
                    self._cache[kind].append(catalog_row)
            
            # Log what we loaded
            for kind, rows in self._cache.items():
                logger.info(f"Loaded {len(rows)} {kind} entries")
                
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
    
    # =========================================================================
    # Cable/Wire Operations
    # =========================================================================
    
    def get_cables(self, size_mm2: Optional[float] = None, 
                   insulation_type: Optional[str] = None) -> List[CatalogRow]:
        """Get cable specifications"""
        cables = self._cache.get('CABLE_SPEC', [])
        
        if size_mm2:
            cables = [c for c in cables if c.get('size_mm2') == size_mm2]
        if insulation_type:
            cables = [c for c in cables 
                     if insulation_type.upper() in c.get('insulation_type', '').upper()]
        
        return cables
    
    def get_cable_by_size(self, size_mm2: float, 
                          material: str = "CU") -> Optional[CatalogRow]:
        """Get specific cable by size"""
        cables = self.get_cables(size_mm2=size_mm2)
        for cable in cables:
            if cable.get('material', 'CU').upper() == material.upper():
                return cable
        return cables[0] if cables else None
    
    def get_cable_ampacity(self, size_mm2: float, in_conduit: bool = True) -> Optional[int]:
        """Get ampacity for a cable size"""
        cable = self.get_cable_by_size(size_mm2)
        if cable:
            key = 'ampacity_in_conduit_a' if in_conduit else 'ampacity_free_air_a'
            return cable.get(key)
        return None
    
    # =========================================================================
    # Derating Factor Operations
    # =========================================================================
    
    def get_derating_factors(self, factor_type: Optional[str] = None) -> List[CatalogRow]:
        """Get derating factors"""
        factors = self._cache.get('DERATING_FACTOR', [])
        
        if factor_type:
            factors = [f for f in factors 
                      if f.get('derating_type', '').lower() == factor_type.lower()
                      or f.get('factor_id', '').upper() == factor_type.upper()]
        
        return factors
    
    def get_ambient_temp_derating(self, temp_c: int, insulation_rating_c: int = 75) -> float:
        """Get temperature derating factor"""
        factors = self.get_derating_factors('ambient_temperature')
        
        for factor in factors:
            table = factor.get('table', [])
            for entry in table:
                if entry.get('ambient_temp_c', 0) == temp_c:
                    # Get appropriate column based on insulation rating
                    if insulation_rating_c == 60:
                        return entry.get('derating_factor_60c', 1.0)
                    elif insulation_rating_c == 90:
                        return entry.get('derating_factor_90c', 1.0)
                    else:
                        return entry.get('derating_factor_75c', 1.0)
        
        return 1.0  # Default no derating
    
    def get_conduit_fill_derating(self, num_conductors: int) -> float:
        """Get derating for number of conductors in conduit"""
        factors = self.get_derating_factors('conductor_grouping')
        
        for factor in factors:
            table = factor.get('table', [])
            for entry in table:
                min_cond = entry.get('min_conductors', 0)
                max_cond = entry.get('max_conductors', 999)
                if min_cond <= num_conductors <= max_cond:
                    return entry.get('derating_factor', 1.0)
        
        # Fallback to NEC Table 310.15(B)(3)(a)
        if num_conductors <= 3:
            return 1.0
        elif num_conductors <= 6:
            return 0.8
        elif num_conductors <= 9:
            return 0.7
        elif num_conductors <= 20:
            return 0.5
        else:
            return 0.4
    
    # =========================================================================
    # Component Operations
    # =========================================================================
    
    def get_components(self, component_type: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> List[CatalogRow]:
        """Get electrical components"""
        components = self._cache.get('COMPONENT', [])
        
        if component_type:
            components = [c for c in components 
                         if c.get('component_type', '').lower() == component_type.lower()]
        
        if tags:
            def has_tags(comp):
                comp_tags = comp.get('tags', [])
                return any(t in comp_tags for t in tags)
            components = [c for c in components if has_tags(c)]
        
        return components
    
    def get_component_by_name(self, name: str) -> Optional[CatalogRow]:
        """Get component by name"""
        components = self._cache.get('COMPONENT', [])
        for comp in components:
            if comp.name == name:
                return comp
        return None
    
    # =========================================================================
    # Appliance Operations
    # =========================================================================
    
    def get_appliances(self, category: Optional[str] = None) -> List[CatalogRow]:
        """Get appliance catalog"""
        appliances = self._cache.get('APPLIANCE', [])
        
        if category:
            appliances = [a for a in appliances 
                         if a.get('category', '').upper() == category.upper()]
        
        return appliances
    
    def get_appliance_by_code(self, code: str) -> Optional[CatalogRow]:
        """Get appliance by code (e.g., APP001)"""
        appliances = self._cache.get('APPLIANCE', [])
        for app in appliances:
            if app.get('appliance_code') == code or app.name == code:
                return app
        return None
    
    # =========================================================================
    # Circuit Template Operations
    # =========================================================================
    
    def get_circuit_templates(self, circuit_type: Optional[str] = None) -> List[CatalogRow]:
        """Get circuit templates"""
        templates = self._cache.get('CIRCUIT_TEMPLATE', [])
        
        if circuit_type:
            templates = [t for t in templates 
                        if t.get('circuit_type', '').lower() == circuit_type.lower()]
        
        return templates
    
    def get_circuit_template_by_name(self, name: str) -> Optional[CatalogRow]:
        """Get circuit template by name"""
        templates = self._cache.get('CIRCUIT_TEMPLATE', [])
        for tmpl in templates:
            if tmpl.name == name:
                return tmpl
        return None
    
    # =========================================================================
    # Validation Rule Operations
    # =========================================================================
    
    def get_validation_rules(self, rule_type: Optional[str] = None) -> List[CatalogRow]:
        """Get validation rules"""
        rules = self._cache.get('VALIDATION_RULE', [])
        
        if rule_type:
            rules = [r for r in rules 
                    if r.get('validation_type', '').lower() == rule_type.lower()]
        
        return rules
    
    # =========================================================================
    # Room Template Operations  
    # =========================================================================
    
    def get_room_templates(self, room_type: Optional[str] = None) -> List[CatalogRow]:
        """Get room templates"""
        templates = self._cache.get('ROOM_TEMPLATE', [])
        
        if room_type:
            templates = [t for t in templates 
                        if t.get('room_type', '').lower() == room_type.lower()]
        
        return templates
    
    # =========================================================================
    # Zone Bundle Operations
    # =========================================================================
    
    def get_zone_bundles(self, zone_type: Optional[str] = None) -> List[CatalogRow]:
        """Get zone bundles (predefined device groupings)"""
        bundles = self._cache.get('ZONE_BUNDLE', [])
        
        if zone_type:
            bundles = [b for b in bundles 
                      if b.get('zone_type', '').lower() == zone_type.lower()]
        
        return bundles
    
    # =========================================================================
    # Placement Rule Operations
    # =========================================================================
    
    def get_placement_rules(self, rule_category: Optional[str] = None) -> List[CatalogRow]:
        """Get placement rules for device positioning"""
        rules = self._cache.get('PLACEMENT_RULE', [])
        
        if rule_category:
            rules = [r for r in rules 
                    if r.get('category', '').lower() == rule_category.lower()]
        
        return rules
    
    # =========================================================================
    # Project Config Operations
    # =========================================================================
    
    def get_project_config(self) -> Optional[CatalogRow]:
        """Get project configuration"""
        configs = self._cache.get('PROJECT_CONFIG', [])
        return configs[0] if configs else None
    
    # =========================================================================
    # Geometry Filter Operations
    # =========================================================================
    
    def get_geometry_filters(self, filter_type: Optional[str] = None) -> List[CatalogRow]:
        """Get geometry filters for CAD processing"""
        filters = self._cache.get('GEOMETRY_FILTER', [])
        
        if filter_type:
            filters = [f for f in filters 
                      if f.get('filter_type', '').lower() == filter_type.lower()]
        
        return filters
    
    # =========================================================================
    # QA Plan Operations
    # =========================================================================
    
    def get_qa_plans(self) -> List[CatalogRow]:
        """Get QA/testing plans"""
        return self._cache.get('QA_PLAN', [])
    
    # =========================================================================
    # Electrical Standard Operations
    # =========================================================================
    
    def get_electrical_standard(self) -> Optional[CatalogRow]:
        """Get electrical standard configuration"""
        standards = self._cache.get('ELECTRICAL_STANDARD', [])
        return standards[0] if standards else None
    
    # =========================================================================
    # Panelboard Operations
    # =========================================================================
    
    def get_panelboards(self) -> List[CatalogRow]:
        """Get panelboard definitions"""
        return self._cache.get('PANELBOARD', [])
    
    # =========================================================================
    # Routing Rule Operations
    # =========================================================================
    
    def get_routing_rules(self) -> List[CatalogRow]:
        """Get wire routing rules"""
        return self._cache.get('ROUTING_RULE', [])
    
    # =========================================================================
    # Device Profile Operations
    # =========================================================================
    
    def get_device_profiles(self, device_type: Optional[str] = None) -> List[CatalogRow]:
        """Get device profiles"""
        profiles = self._cache.get('DEVICE_PROFILE', [])
        
        if device_type:
            profiles = [p for p in profiles 
                       if p.get('device_type', '').lower() == device_type.lower()]
        
        return profiles
    
    # =========================================================================
    # Generic Query
    # =========================================================================
    
    def query(self, kind: str, filters: Optional[Dict[str, Any]] = None) -> List[CatalogRow]:
        """Generic query by kind with optional filters"""
        rows = self._cache.get(kind, [])
        
        if filters:
            def matches(row):
                for key, value in filters.items():
                    if row.get(key) != value:
                        return False
                return True
            rows = [r for r in rows if matches(r)]
        
        return rows
    
    def get_all_kinds(self) -> List[str]:
        """Get all available kinds in catalog"""
        return list(self._cache.keys())
    
    def count(self, kind: str) -> int:
        """Count rows of a specific kind"""
        return len(self._cache.get(kind, []))


# =========================================================================
# Singleton instance
# =========================================================================

_catalog_instance: Optional[FileCatalogDAL] = None


def get_file_catalog() -> FileCatalogDAL:
    """Get singleton catalog instance"""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = FileCatalogDAL()
    return _catalog_instance


def reload_catalog():
    """Force reload of catalog (for testing)"""
    global _catalog_instance
    _catalog_instance = None
    return get_file_catalog()
