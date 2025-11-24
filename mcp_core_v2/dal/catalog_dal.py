"""
MCP Core v2 Catalog DAL
Data Access Layer for amadeus.catalog schema in Supabase.
Provides fallback to baseline data when DB is unavailable.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from dal.supabase_client import get_supabase
from models.catalog_models import (
    WireSpec,
    BreakerSpec,
    ConduitSpec,
    RoomTemplate,
    ComplianceRule,
)
from models.baseline import (
    WIRE_SIZE_TABLE,
    STANDARD_BREAKER_SIZES,
    BASELINE_OUTLET_RULES,
    BASELINE_LIGHTING_RULES,
)


class CatalogDAL:
    """Data Access Layer for amadeus.catalog schema."""
    
    SCHEMA = "amadeus"
    
    def __init__(self):
        self.client = get_supabase()
        self._use_baseline = self.client is None
    
    @property
    def is_online(self) -> bool:
        """Check if connected to database."""
        return self.client is not None and not self._use_baseline
    
    # --- Wire Methods ---
    
    def get_wire_by_size(self, size_sqmm: float) -> Optional[WireSpec]:
        """Get wire specification by size."""
        if self._use_baseline:
            return self._get_baseline_wire(size_sqmm)
        
        try:
            result = (
                self.client
                .schema(self.SCHEMA)
                .table("wires")
                .select("*")
                .eq("size_sqmm", size_sqmm)
                .limit(1)
                .execute()
            )
            if result.data:
                return WireSpec(**result.data[0])
        except Exception as e:
            print(f"DB error, falling back to baseline: {e}")
            return self._get_baseline_wire(size_sqmm)
        
        return None
    
    def get_wire_for_current(self, current_amps: float) -> Optional[WireSpec]:
        """Get smallest wire that can handle given current."""
        if self._use_baseline:
            return self._get_baseline_wire_for_current(current_amps)
        
        try:
            result = (
                self.client
                .schema(self.SCHEMA)
                .table("wires")
                .select("*")
                .gte("max_current_amp", current_amps)
                .order("size_sqmm")
                .limit(1)
                .execute()
            )
            if result.data:
                return WireSpec(**result.data[0])
        except Exception as e:
            print(f"DB error, falling back to baseline: {e}")
            return self._get_baseline_wire_for_current(current_amps)
        
        return None
    
    def _get_baseline_wire(self, size_sqmm: float) -> Optional[WireSpec]:
        """Get wire from baseline data."""
        for wire in WIRE_SIZE_TABLE:
            if wire["size_sqmm"] == size_sqmm:
                return WireSpec(
                    id=uuid4(),
                    size_sqmm=wire["size_sqmm"],
                    max_current_amp=wire["max_amps"],
                )
        return None
    
    def _get_baseline_wire_for_current(self, current_amps: float) -> Optional[WireSpec]:
        """Get smallest baseline wire for current."""
        for wire in WIRE_SIZE_TABLE:
            if wire["max_amps"] >= current_amps:
                return WireSpec(
                    id=uuid4(),
                    size_sqmm=wire["size_sqmm"],
                    max_current_amp=wire["max_amps"],
                )
        return None
    
    # --- Breaker Methods ---
    
    def get_breaker_by_rating(self, rated_current: int) -> Optional[BreakerSpec]:
        """Get breaker by exact rating."""
        if self._use_baseline:
            return self._get_baseline_breaker(rated_current)
        
        try:
            result = (
                self.client
                .schema(self.SCHEMA)
                .table("breakers")
                .select("*")
                .eq("rated_current", rated_current)
                .limit(1)
                .execute()
            )
            if result.data:
                return BreakerSpec(**result.data[0])
        except Exception as e:
            print(f"DB error, falling back to baseline: {e}")
            return self._get_baseline_breaker(rated_current)
        
        return None
    
    def get_breaker_for_current(self, current_amps: float) -> Optional[BreakerSpec]:
        """Get smallest breaker that can handle given current."""
        if self._use_baseline:
            return self._get_baseline_breaker_for_current(current_amps)
        
        try:
            result = (
                self.client
                .schema(self.SCHEMA)
                .table("breakers")
                .select("*")
                .gte("rated_current", current_amps)
                .order("rated_current")
                .limit(1)
                .execute()
            )
            if result.data:
                return BreakerSpec(**result.data[0])
        except Exception as e:
            print(f"DB error, falling back to baseline: {e}")
            return self._get_baseline_breaker_for_current(current_amps)
        
        return None
    
    def _get_baseline_breaker(self, rated_current: int) -> Optional[BreakerSpec]:
        """Get breaker from baseline data."""
        if rated_current in STANDARD_BREAKER_SIZES:
            return BreakerSpec(
                id=uuid4(),
                rated_current=rated_current,
            )
        return None
    
    def _get_baseline_breaker_for_current(self, current_amps: float) -> Optional[BreakerSpec]:
        """Get smallest baseline breaker for current."""
        for size in STANDARD_BREAKER_SIZES:
            if size >= current_amps:
                return BreakerSpec(
                    id=uuid4(),
                    rated_current=size,
                )
        return None
    
    # --- Room Template Methods ---
    
    def get_room_template(self, room_type: str, area_sqm: float) -> Optional[RoomTemplate]:
        """Get room template by type and area."""
        if self._use_baseline:
            return self._get_baseline_template(room_type, area_sqm)
        
        try:
            result = (
                self.client
                .schema(self.SCHEMA)
                .table("room_templates")
                .select("*")
                .eq("room_type", room_type)
                .lte("min_area_sqm", area_sqm)
                .gte("max_area_sqm", area_sqm)
                .limit(1)
                .execute()
            )
            if result.data:
                return RoomTemplate(**result.data[0])
        except Exception as e:
            print(f"DB error, falling back to baseline: {e}")
            return self._get_baseline_template(room_type, area_sqm)
        
        return None
    
    def _get_baseline_template(self, room_type: str, area_sqm: float) -> Optional[RoomTemplate]:
        """Get room template from baseline data."""
        from models.contracts import RoomType
        
        try:
            rt = RoomType(room_type)
        except ValueError:
            return None
        
        outlet_rules = BASELINE_OUTLET_RULES.get(rt, {})
        lighting_rules = BASELINE_LIGHTING_RULES.get(rt, {})
        
        return RoomTemplate(
            id=uuid4(),
            room_type=room_type,
            min_area_sqm=0,
            max_area_sqm=1000,
            outlet_rules=outlet_rules,
            lighting_rules=lighting_rules,
            circuit_rules={
                "max_outlets_per_circuit": 10,
                "max_lights_per_circuit": 10,
                "max_watts_per_circuit": 2000,
            },
        )
    
    # --- Compliance Rules ---
    
    def get_compliance_rules(self, rule_type: Optional[str] = None) -> List[ComplianceRule]:
        """Get compliance rules, optionally filtered by type."""
        if self._use_baseline:
            return self._get_baseline_compliance_rules(rule_type)
        
        try:
            query = (
                self.client
                .schema(self.SCHEMA)
                .table("compliance_rules")
                .select("*")
            )
            if rule_type:
                query = query.eq("rule_type", rule_type)
            
            result = query.execute()
            return [ComplianceRule(**r) for r in result.data]
        except Exception as e:
            print(f"DB error, falling back to baseline: {e}")
            return self._get_baseline_compliance_rules(rule_type)
    
    def _get_baseline_compliance_rules(self, rule_type: Optional[str] = None) -> List[ComplianceRule]:
        """Get baseline compliance rules."""
        rules = [
            ComplianceRule(
                id=uuid4(),
                rule_code="EIT-4.2.1",
                rule_type="outlet_spacing",
                description="Maximum outlet spacing is 4.5m",
                check_function="check_outlet_spacing",
                parameters={"max_spacing_m": 4.5},
                severity="error",
            ),
            ComplianceRule(
                id=uuid4(),
                rule_code="EIT-4.3.1",
                rule_type="wire_sizing",
                description="Wire must be rated for 125% of circuit load",
                check_function="check_wire_rating",
                parameters={"safety_factor": 1.25},
                severity="error",
            ),
            ComplianceRule(
                id=uuid4(),
                rule_code="EIT-4.4.1",
                rule_type="breaker_coordination",
                description="Breaker must be rated <= wire ampacity",
                check_function="check_breaker_coordination",
                parameters={},
                severity="error",
            ),
            ComplianceRule(
                id=uuid4(),
                rule_code="EIT-5.1.1",
                rule_type="lighting_level",
                description="Minimum lighting levels per room type",
                check_function="check_lighting_level",
                parameters={},
                severity="warning",
            ),
        ]
        
        if rule_type:
            return [r for r in rules if r.rule_type == rule_type]
        return rules


# Singleton instance
_catalog_dal: Optional[CatalogDAL] = None


def get_catalog_dal() -> CatalogDAL:
    """Get or create CatalogDAL instance."""
    global _catalog_dal
    if _catalog_dal is None:
        _catalog_dal = CatalogDAL()
    return _catalog_dal
