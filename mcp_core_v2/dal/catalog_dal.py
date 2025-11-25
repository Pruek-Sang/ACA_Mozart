"""Catalog Data Access Layer."""

from typing import List, Optional, Dict, Any
from dal.supabase_client import get_supabase_client
from models.catalog_models import (
    CatalogBreaker, CatalogWire, CatalogConduit, CatalogPanel,
    BreakerType, BreakerPoles, ConductorMaterial, ConduitMaterial
)
import logging

logger = logging.getLogger(__name__)


class CatalogDAL:
    """Data access layer for catalog operations."""
    
    def __init__(self):
        """Initialize catalog DAL."""
        self.client = get_supabase_client()
    
    # Breaker operations
    def get_breakers(
        self, 
        ampere_rating: Optional[int] = None,
        breaker_type: Optional[BreakerType] = None,
        poles: Optional[BreakerPoles] = None
    ) -> List[CatalogBreaker]:
        """Get breakers from catalog with optional filters."""
        try:
            filters = {}
            if ampere_rating:
                filters['ampere_rating'] = ampere_rating
            if breaker_type:
                filters['breaker_type'] = breaker_type.value
            if poles:
                filters['poles'] = poles.value
            
            data = self.client.select('catalog_breakers', filters=filters)
            return [CatalogBreaker(**item) for item in data]
        except Exception as e:
            logger.error(f"Error fetching breakers: {e}")
            return []
    
    def get_breaker_by_rating(
        self, 
        ampere_rating: int,
        poles: BreakerPoles,
        breaker_type: BreakerType = BreakerType.STANDARD
    ) -> Optional[CatalogBreaker]:
        """Get a specific breaker by rating and configuration."""
        breakers = self.get_breakers(
            ampere_rating=ampere_rating,
            breaker_type=breaker_type,
            poles=poles
        )
        return breakers[0] if breakers else None
    
    def add_breaker(self, breaker: CatalogBreaker) -> CatalogBreaker:
        """Add a breaker to the catalog."""
        try:
            data = self.client.insert('catalog_breakers', breaker.model_dump())
            return CatalogBreaker(**data)
        except Exception as e:
            logger.error(f"Error adding breaker: {e}")
            raise
    
    # Wire operations
    def get_wires(
        self,
        awg_size: Optional[str] = None,
        material: Optional[ConductorMaterial] = None,
        min_ampacity: Optional[int] = None
    ) -> List[CatalogWire]:
        """Get wires from catalog with optional filters."""
        try:
            filters = {}
            if awg_size:
                filters['awg_size'] = awg_size
            if material:
                filters['material'] = material.value
            
            data = self.client.select('catalog_wires', filters=filters)
            wires = [CatalogWire(**item) for item in data]
            
            # Note: ampacity filtering would require joining with baseline data
            # For now, return all matching wires
            return wires
        except Exception as e:
            logger.error(f"Error fetching wires: {e}")
            return []
    
    def get_wire_by_size(
        self,
        awg_size: str,
        material: ConductorMaterial = ConductorMaterial.COPPER
    ) -> Optional[CatalogWire]:
        """Get a specific wire by size and material."""
        wires = self.get_wires(awg_size=awg_size, material=material)
        return wires[0] if wires else None
    
    def add_wire(self, wire: CatalogWire) -> CatalogWire:
        """Add a wire to the catalog."""
        try:
            data = self.client.insert('catalog_wires', wire.model_dump())
            return CatalogWire(**data)
        except Exception as e:
            logger.error(f"Error adding wire: {e}")
            raise
    
    # Conduit operations
    def get_conduits(
        self,
        trade_size: Optional[str] = None,
        material: Optional[ConduitMaterial] = None
    ) -> List[CatalogConduit]:
        """Get conduits from catalog with optional filters."""
        try:
            filters = {}
            if trade_size:
                filters['trade_size'] = trade_size
            if material:
                filters['material'] = material.value
            
            data = self.client.select('catalog_conduits', filters=filters)
            return [CatalogConduit(**item) for item in data]
        except Exception as e:
            logger.error(f"Error fetching conduits: {e}")
            return []
    
    def get_conduit_by_size(
        self,
        trade_size: str,
        material: ConduitMaterial = ConduitMaterial.EMT
    ) -> Optional[CatalogConduit]:
        """Get a specific conduit by size and material."""
        conduits = self.get_conduits(trade_size=trade_size, material=material)
        return conduits[0] if conduits else None
    
    def add_conduit(self, conduit: CatalogConduit) -> CatalogConduit:
        """Add a conduit to the catalog."""
        try:
            data = self.client.insert('catalog_conduits', conduit.model_dump())
            return CatalogConduit(**data)
        except Exception as e:
            logger.error(f"Error adding conduit: {e}")
            raise
    
    # Panel operations
    def get_panels(
        self,
        main_breaker_rating: Optional[int] = None,
        number_of_spaces: Optional[int] = None
    ) -> List[CatalogPanel]:
        """Get panels from catalog with optional filters."""
        try:
            filters = {}
            if main_breaker_rating:
                filters['main_breaker_rating'] = main_breaker_rating
            if number_of_spaces:
                filters['number_of_spaces'] = number_of_spaces
            
            data = self.client.select('catalog_panels', filters=filters)
            return [CatalogPanel(**item) for item in data]
        except Exception as e:
            logger.error(f"Error fetching panels: {e}")
            return []
    
    def add_panel(self, panel: CatalogPanel) -> CatalogPanel:
        """Add a panel to the catalog."""
        try:
            data = self.client.insert('catalog_panels', panel.model_dump())
            return CatalogPanel(**data)
        except Exception as e:
            logger.error(f"Error adding panel: {e}")
            raise


# Global instance
_catalog_dal: Optional[CatalogDAL] = None


def get_catalog_dal() -> CatalogDAL:
    """Get the global catalog DAL instance."""
    global _catalog_dal
    if _catalog_dal is None:
        _catalog_dal = CatalogDAL()
    return _catalog_dal
