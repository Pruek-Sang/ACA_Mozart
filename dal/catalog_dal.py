"""Data Access Object for reading from amadeus schema catalog views.

This module provides typed access to catalog data without exposing
raw JSON to consumers. Uses hardcoded demo data when database is
not available.
"""

import logging
from typing import List, Optional, Dict

from models.catalog_models import (
    RoomTemplate,
    CircuitTemplate,
    CableSpec,
    BreakerSpec,
    ConduitSpec,
    ApplianceSpec,
)
from .supabase_client import SupabaseClient, get_supabase_client

logger = logging.getLogger(__name__)


# Hardcoded realistic demo data for testing without database
DEMO_ROOM_TEMPLATES: Dict[str, RoomTemplate] = {
    "bedroom": RoomTemplate(
        template_id="rt-bedroom-01",
        room_type="bedroom",
        lighting_watts_per_m2=15.0,
        min_lighting_points=1,
        outlets_per_m2=0.25,
        min_outlets=2,
        outlet_watts_each=180.0,
        requires_dedicated_circuit=False,
        diversity_factor=0.8,
    ),
    "bathroom": RoomTemplate(
        template_id="rt-bathroom-01",
        room_type="bathroom",
        lighting_watts_per_m2=20.0,
        min_lighting_points=1,
        outlets_per_m2=0.2,
        min_outlets=1,
        outlet_watts_each=180.0,
        requires_dedicated_circuit=True,
        dedicated_circuit_load_w=3000.0,
        dedicated_circuit_name="Water Heater",
        diversity_factor=0.7,
    ),
    "kitchen": RoomTemplate(
        template_id="rt-kitchen-01",
        room_type="kitchen",
        lighting_watts_per_m2=20.0,
        min_lighting_points=2,
        outlets_per_m2=0.4,
        min_outlets=4,
        outlet_watts_each=300.0,
        requires_dedicated_circuit=True,
        dedicated_circuit_load_w=2500.0,
        dedicated_circuit_name="Kitchen Appliances",
        diversity_factor=0.6,
    ),
    "living_room": RoomTemplate(
        template_id="rt-living-01",
        room_type="living_room",
        lighting_watts_per_m2=15.0,
        min_lighting_points=2,
        outlets_per_m2=0.3,
        min_outlets=4,
        outlet_watts_each=180.0,
        requires_dedicated_circuit=False,
        diversity_factor=0.7,
    ),
}

DEMO_CIRCUIT_TEMPLATES: Dict[str, CircuitTemplate] = {
    "lighting": CircuitTemplate(
        template_id="ct-lighting-01",
        circuit_type="lighting",
        name_pattern="{room}_lighting",
        default_breaker_a=10,
        max_load_w=1000.0,
        max_outlets=10,
        default_wire_size_mm2=1.5,
        wire_type="THW",
    ),
    "outlet": CircuitTemplate(
        template_id="ct-outlet-01",
        circuit_type="outlet",
        name_pattern="{room}_outlets",
        default_breaker_a=16,
        max_load_w=2000.0,
        max_outlets=6,
        default_wire_size_mm2=2.5,
        wire_type="THW",
    ),
    "dedicated": CircuitTemplate(
        template_id="ct-dedicated-01",
        circuit_type="dedicated",
        name_pattern="{room}_{appliance}",
        default_breaker_a=20,
        max_load_w=4000.0,
        max_outlets=1,
        default_wire_size_mm2=4.0,
        wire_type="THW",
    ),
}

# Standard cable sizes (Thai standard)
DEMO_CABLE_SPECS: List[CableSpec] = [
    CableSpec(
        spec_id="cable-1.5",
        size_mm2=1.5,
        ampacity_in_conduit_a=14,
        ampacity_free_air_a=18,
        resistance_ohm_per_km=12.1,
        reactance_ohm_per_km=0.08,
        insulation_type="THW",
        outer_diameter_mm=3.0,
        max_temperature_c=75,
    ),
    CableSpec(
        spec_id="cable-2.5",
        size_mm2=2.5,
        ampacity_in_conduit_a=19,
        ampacity_free_air_a=25,
        resistance_ohm_per_km=7.41,
        reactance_ohm_per_km=0.08,
        insulation_type="THW",
        outer_diameter_mm=3.6,
        max_temperature_c=75,
    ),
    CableSpec(
        spec_id="cable-4.0",
        size_mm2=4.0,
        ampacity_in_conduit_a=26,
        ampacity_free_air_a=34,
        resistance_ohm_per_km=4.61,
        reactance_ohm_per_km=0.08,
        insulation_type="THW",
        outer_diameter_mm=4.2,
        max_temperature_c=75,
    ),
    CableSpec(
        spec_id="cable-6.0",
        size_mm2=6.0,
        ampacity_in_conduit_a=34,
        ampacity_free_air_a=43,
        resistance_ohm_per_km=3.08,
        reactance_ohm_per_km=0.08,
        insulation_type="THW",
        outer_diameter_mm=4.9,
        max_temperature_c=75,
    ),
    CableSpec(
        spec_id="cable-10.0",
        size_mm2=10.0,
        ampacity_in_conduit_a=46,
        ampacity_free_air_a=60,
        resistance_ohm_per_km=1.83,
        reactance_ohm_per_km=0.08,
        insulation_type="THW",
        outer_diameter_mm=6.0,
        max_temperature_c=75,
    ),
    CableSpec(
        spec_id="cable-16.0",
        size_mm2=16.0,
        ampacity_in_conduit_a=62,
        ampacity_free_air_a=80,
        resistance_ohm_per_km=1.15,
        reactance_ohm_per_km=0.08,
        insulation_type="THW",
        outer_diameter_mm=7.2,
        max_temperature_c=75,
    ),
    CableSpec(
        spec_id="cable-25.0",
        size_mm2=25.0,
        ampacity_in_conduit_a=80,
        ampacity_free_air_a=105,
        resistance_ohm_per_km=0.727,
        reactance_ohm_per_km=0.08,
        insulation_type="THW",
        outer_diameter_mm=8.6,
        max_temperature_c=75,
    ),
]

# Standard breaker ratings
DEMO_BREAKER_SPECS: List[BreakerSpec] = [
    BreakerSpec(
        spec_id="mcb-6a",
        rating_a=6,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=1.5,
        max_wire_size_mm2=2.5,
    ),
    BreakerSpec(
        spec_id="mcb-10a",
        rating_a=10,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=1.5,
        max_wire_size_mm2=2.5,
    ),
    BreakerSpec(
        spec_id="mcb-16a",
        rating_a=16,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=2.5,
        max_wire_size_mm2=4.0,
    ),
    BreakerSpec(
        spec_id="mcb-20a",
        rating_a=20,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=2.5,
        max_wire_size_mm2=6.0,
    ),
    BreakerSpec(
        spec_id="mcb-25a",
        rating_a=25,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=4.0,
        max_wire_size_mm2=10.0,
    ),
    BreakerSpec(
        spec_id="mcb-32a",
        rating_a=32,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=6.0,
        max_wire_size_mm2=16.0,
    ),
    BreakerSpec(
        spec_id="mcb-40a",
        rating_a=40,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=10.0,
        max_wire_size_mm2=16.0,
    ),
    BreakerSpec(
        spec_id="mcb-50a",
        rating_a=50,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=16.0,
        max_wire_size_mm2=25.0,
    ),
    BreakerSpec(
        spec_id="mcb-63a",
        rating_a=63,
        breaking_capacity_ka=6.0,
        breaker_type="MCB",
        trip_curve="C",
        poles=1,
        width_modules=1,
        min_wire_size_mm2=16.0,
        max_wire_size_mm2=25.0,
    ),
]

# Standard conduit sizes
DEMO_CONDUIT_SPECS: List[ConduitSpec] = [
    ConduitSpec(
        spec_id="conduit-16",
        nominal_size_mm=16,
        inner_diameter_mm=15.8,
        max_fill_percent=40.0,
        usable_area_mm2=78.5,
        conduit_type="EMT",
        material="steel",
    ),
    ConduitSpec(
        spec_id="conduit-20",
        nominal_size_mm=20,
        inner_diameter_mm=20.9,
        max_fill_percent=40.0,
        usable_area_mm2=137.2,
        conduit_type="EMT",
        material="steel",
    ),
    ConduitSpec(
        spec_id="conduit-25",
        nominal_size_mm=25,
        inner_diameter_mm=26.6,
        max_fill_percent=40.0,
        usable_area_mm2=222.0,
        conduit_type="EMT",
        material="steel",
    ),
    ConduitSpec(
        spec_id="conduit-32",
        nominal_size_mm=32,
        inner_diameter_mm=35.1,
        max_fill_percent=40.0,
        usable_area_mm2=387.1,
        conduit_type="EMT",
        material="steel",
    ),
]


class CatalogDAL:
    """Data Access Object for catalog data.
    
    Provides typed access to room templates, circuit templates, cable specs,
    breaker specs, and conduit specs. Falls back to demo data when database
    is not available.
    """

    def __init__(self, supabase_client: Optional[SupabaseClient] = None):
        """Initialize CatalogDAL.
        
        Args:
            supabase_client: Optional Supabase client for database access
        """
        self._client = supabase_client or get_supabase_client()
        self._use_demo_data = self._client is None
        
        if self._use_demo_data:
            logger.info("Using demo data (no database connection)")

    def get_room_template(self, room_type: str) -> Optional[RoomTemplate]:
        """Get room template by type.
        
        Args:
            room_type: Type of room (e.g., "bedroom", "kitchen")
            
        Returns:
            RoomTemplate if found, None otherwise
        """
        if self._use_demo_data:
            return DEMO_ROOM_TEMPLATES.get(room_type.lower())
        
        try:
            data = self._client.select(
                table="room_templates",
                filters={"room_type": room_type},
                limit=1,
                schema="amadeus"
            )
            if data:
                return RoomTemplate(**data[0])
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch room template from DB, using demo: {e}")
            return DEMO_ROOM_TEMPLATES.get(room_type.lower())

    def get_circuit_template(self, circuit_type: str) -> Optional[CircuitTemplate]:
        """Get circuit template by type.
        
        Args:
            circuit_type: Type of circuit (lighting/outlet/dedicated)
            
        Returns:
            CircuitTemplate if found, None otherwise
        """
        if self._use_demo_data:
            return DEMO_CIRCUIT_TEMPLATES.get(circuit_type.lower())
        
        try:
            data = self._client.select(
                table="circuit_templates",
                filters={"circuit_type": circuit_type},
                limit=1,
                schema="amadeus"
            )
            if data:
                return CircuitTemplate(**data[0])
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch circuit template from DB, using demo: {e}")
            return DEMO_CIRCUIT_TEMPLATES.get(circuit_type.lower())

    def get_cable_specs(self) -> List[CableSpec]:
        """Get all available cable specifications.
        
        Returns:
            List of CableSpec ordered by size
        """
        if self._use_demo_data:
            return sorted(DEMO_CABLE_SPECS, key=lambda x: x.size_mm2)
        
        try:
            data = self._client.select(
                table="cable_specs",
                schema="amadeus"
            )
            if data:
                specs = [CableSpec(**row) for row in data]
                return sorted(specs, key=lambda x: x.size_mm2)
            return DEMO_CABLE_SPECS
        except Exception as e:
            logger.warning(f"Failed to fetch cable specs from DB, using demo: {e}")
            return sorted(DEMO_CABLE_SPECS, key=lambda x: x.size_mm2)

    def get_cable_spec_by_size(self, size_mm2: float) -> Optional[CableSpec]:
        """Get cable specification by size.
        
        Args:
            size_mm2: Cable cross-sectional area in mm²
            
        Returns:
            CableSpec if found, None otherwise
        """
        specs = self.get_cable_specs()
        for spec in specs:
            if abs(spec.size_mm2 - size_mm2) < 0.1:
                return spec
        return None

    def get_breaker_specs(self) -> List[BreakerSpec]:
        """Get all available breaker specifications.
        
        Returns:
            List of BreakerSpec ordered by rating
        """
        if self._use_demo_data:
            return sorted(DEMO_BREAKER_SPECS, key=lambda x: x.rating_a)
        
        try:
            data = self._client.select(
                table="breaker_specs",
                schema="amadeus"
            )
            if data:
                specs = [BreakerSpec(**row) for row in data]
                return sorted(specs, key=lambda x: x.rating_a)
            return DEMO_BREAKER_SPECS
        except Exception as e:
            logger.warning(f"Failed to fetch breaker specs from DB, using demo: {e}")
            return sorted(DEMO_BREAKER_SPECS, key=lambda x: x.rating_a)

    def get_breaker_spec_by_rating(self, rating_a: int) -> Optional[BreakerSpec]:
        """Get breaker specification by rating.
        
        Args:
            rating_a: Breaker current rating in Amps
            
        Returns:
            BreakerSpec if found, None otherwise
        """
        specs = self.get_breaker_specs()
        for spec in specs:
            if spec.rating_a == rating_a:
                return spec
        return None

    def get_conduit_specs(self) -> List[ConduitSpec]:
        """Get all available conduit specifications.
        
        Returns:
            List of ConduitSpec ordered by size
        """
        if self._use_demo_data:
            return sorted(DEMO_CONDUIT_SPECS, key=lambda x: x.nominal_size_mm)
        
        try:
            data = self._client.select(
                table="conduit_specs",
                schema="amadeus"
            )
            if data:
                specs = [ConduitSpec(**row) for row in data]
                return sorted(specs, key=lambda x: x.nominal_size_mm)
            return DEMO_CONDUIT_SPECS
        except Exception as e:
            logger.warning(f"Failed to fetch conduit specs from DB, using demo: {e}")
            return sorted(DEMO_CONDUIT_SPECS, key=lambda x: x.nominal_size_mm)

    def get_conduit_spec_by_size(self, size_mm: int) -> Optional[ConduitSpec]:
        """Get conduit specification by nominal size.
        
        Args:
            size_mm: Conduit nominal size in mm
            
        Returns:
            ConduitSpec if found, None otherwise
        """
        specs = self.get_conduit_specs()
        for spec in specs:
            if spec.nominal_size_mm == size_mm:
                return spec
        return None
