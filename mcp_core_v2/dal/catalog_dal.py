"""
Catalog Data Access Layer - File-based Implementation.

This replaces Supabase with local CSV file reading.
Uses rag_knowledge/db/catalog_rows.csv as Single Source of Truth.
"""

from typing import List, Optional, Dict, Any
from dal.file_catalog_dal import get_file_catalog, FileCatalogDAL, CatalogRow
from models.catalog_models import (
    CatalogBreaker, CatalogWire, CatalogConduit, CatalogPanel,
    BreakerType, BreakerPoles, ConductorMaterial, ConduitMaterial,
    WireInsulation, PanelType
)
from models.baseline import NECBaseline
import logging

logger = logging.getLogger(__name__)


class CatalogDAL:
    """
    Data access layer for catalog operations.
    
    Now uses file-based catalog from CSV instead of Supabase.
    Falls back to NECBaseline for standard ratings.
    """
    
    def __init__(self):
        """Initialize catalog DAL with file-based backend."""
        self.file_catalog = get_file_catalog()
        self.nec = NECBaseline()
        logger.info("CatalogDAL initialized with file-based backend")
    
    # Breaker operations
    def get_breakers(
        self, 
        ampere_rating: Optional[int] = None,
        breaker_type: Optional[BreakerType] = None,
        poles: Optional[BreakerPoles] = None
    ) -> List[CatalogBreaker]:
        """
        Get breakers from NEC baseline with optional filters.
        Since CSV doesn't have breaker catalog, use NECBaseline standard ratings.
        """
        try:
            # Get standard breaker ratings from NEC baseline
            standard_ratings = self.nec.standard_breaker_ratings
            breakers = []
            
            for rating in standard_ratings:
                # Apply ampere_rating filter
                if ampere_rating and rating != ampere_rating:
                    continue
                    
                # Create breaker with requested or default config
                breaker_poles = poles or BreakerPoles.SINGLE
                breaker_type_val = breaker_type or BreakerType.STANDARD
                
                breaker = CatalogBreaker(
                    id=f"BRK-{rating}-{breaker_poles.value}",
                    model_number=f"BR{rating}{breaker_poles.value}",
                    manufacturer="Generic",
                    ampere_rating=rating,
                    voltage_rating=240,
                    poles=breaker_poles,
                    breaker_type=breaker_type_val,
                    interrupt_rating=10000,
                    price=15.0 + (rating * 0.5),
                    notes=f"{rating}A {breaker_poles.value} Breaker"
                )
                breakers.append(breaker)
            
            return breakers
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
        # Check if requested rating is valid per NEC
        standard_ratings = self.nec.standard_breaker_ratings
        
        if ampere_rating in standard_ratings:
            return CatalogBreaker(
                id=f"BRK-{ampere_rating}-{poles.value}",
                model_number=f"BR{ampere_rating}{poles.value}",
                manufacturer="Generic",
                ampere_rating=ampere_rating,
                voltage_rating=240,
                poles=poles,
                breaker_type=breaker_type,
                interrupt_rating=10000,
                price=15.0 + (ampere_rating * 0.5),
                notes=f"{ampere_rating}A {poles.value} Breaker"
            )
        return None
    
    def add_breaker(self, breaker: CatalogBreaker) -> CatalogBreaker:
        """Add a breaker to the catalog (not supported in file mode)."""
        logger.warning("add_breaker not supported in file-based mode")
        return breaker
    
    # Wire operations
    def get_wires(
        self,
        awg_size: Optional[str] = None,
        material: Optional[ConductorMaterial] = None
    ) -> List[CatalogWire]:
        """Get wires from CSV catalog with optional filters."""
        try:
            cables = self.file_catalog.get_cables()
            wires = []
            
            for cable in cables:
                # Parse cable data
                data = cable.data or {}
                cable_awg = data.get('awg_size', cable.name)
                cable_material = data.get('material', 'copper')
                
                # Apply filters
                if awg_size and cable_awg != awg_size:
                    continue
                if material and cable_material.upper() != material.value:
                    continue
                
                wire = CatalogWire(
                    id=f"WIRE-{cable.name}",
                    manufacturer=data.get('manufacturer', 'Generic'),
                    awg_size=cable_awg,
                    material=ConductorMaterial(cable_material.upper()) if cable_material else ConductorMaterial.COPPER,
                    insulation_type=WireInsulation.THHN,
                    voltage_rating=data.get('voltage_rating', 600),
                    temperature_rating=data.get('temperature_rating', 90),
                    stranding=data.get('stranding', '7-strand'),
                    price_per_foot=data.get('price_per_foot', 0.50),
                    notes=cable.description or f"{cable_awg} Wire"
                )
                wires.append(wire)
            
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
        """Add a wire to the catalog (not supported in file mode)."""
        logger.warning("add_wire not supported in file-based mode")
        return wire
    
    # Conduit operations
    def get_conduits(
        self,
        trade_size: Optional[str] = None,
        material: Optional[ConduitMaterial] = None
    ) -> List[CatalogConduit]:
        """Get conduits from NEC baseline."""
        try:
            # Get from NEC baseline conduit sizes
            conduit_data = self.nec.conduit_fill
            conduits = []
            
            for size_key in conduit_data.keys():
                size = size_key.replace('"', '')  # Remove inch marks if present
                
                if trade_size and size != trade_size:
                    continue
                
                mat = material or ConduitMaterial.EMT
                
                conduit = CatalogConduit(
                    id=f"COND-{size}-{mat.value}",
                    manufacturer="Generic",
                    trade_size=size,
                    material=mat,
                    notes=f'{size}" {mat.value} Conduit'
                )
                conduits.append(conduit)
            
            return conduits
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
        """Add a conduit to the catalog (not supported in file mode)."""
        logger.warning("add_conduit not supported in file-based mode")
        return conduit
    
    # Panel operations
    def get_panels(
        self,
        main_breaker_rating: Optional[int] = None,
        number_of_spaces: Optional[int] = None
    ) -> List[CatalogPanel]:
        """Get panels from file catalog or generate defaults."""
        try:
            # Standard residential panel configurations
            panel_configs = [
                (100, 20), (100, 30), (125, 30), (150, 30),
                (200, 40), (200, 42), (225, 42)
            ]
            panels = []
            
            for rating, spaces in panel_configs:
                if main_breaker_rating and rating != main_breaker_rating:
                    continue
                if number_of_spaces and spaces != number_of_spaces:
                    continue
                
                panel = CatalogPanel(
                    id=f"PNL-{rating}-{spaces}",
                    model_number=f"PNL{rating}-{spaces}",
                    manufacturer="Generic",
                    panel_type=PanelType.LOADCENTER,
                    main_breaker_rating=rating,
                    bus_rating=rating,
                    number_of_spaces=spaces,
                    max_circuits=spaces,
                    voltage=240,
                    phases=1,
                    enclosure_type="NEMA 1",
                    price=150.0 + (rating * 1.5),
                    notes=f"{rating}A Main, {spaces}-Space Panel"
                )
                panels.append(panel)
            
            return panels
        except Exception as e:
            logger.error(f"Error fetching panels: {e}")
            return []
    
    def add_panel(self, panel: CatalogPanel) -> CatalogPanel:
        """Add a panel to the catalog (not supported in file mode)."""
        logger.warning("add_panel not supported in file-based mode")
        return panel


# Global instance
_catalog_dal: Optional[CatalogDAL] = None


def get_catalog_dal() -> CatalogDAL:
    """Get the global catalog DAL instance."""
    global _catalog_dal
    if _catalog_dal is None:
        _catalog_dal = CatalogDAL()
    return _catalog_dal
