"""Data Access Layer for catalog data from Supabase amadeus schema."""

from typing import Optional

from supabase import Client

from src.models.catalog_models import (
    BreakerSpec,
    CableSpec,
    ConduitSpec,
    RoomTemplate,
)


class CatalogDAL:
    """Data Access Layer for fetching templates and specs from Supabase."""

    def __init__(self, client: Optional[Client] = None):
        """Initialize with optional Supabase client.
        
        Args:
            client: Supabase client instance. If None, will use singleton.
        """
        self._client = client
        self._room_templates_cache: Optional[dict[str, RoomTemplate]] = None
        self._cable_specs_cache: Optional[list[CableSpec]] = None
        self._breaker_specs_cache: Optional[list[BreakerSpec]] = None
        self._conduit_specs_cache: Optional[list[ConduitSpec]] = None

    @property
    def client(self) -> Client:
        """Get the Supabase client, lazy-loading from singleton if needed."""
        if self._client is None:
            from src.dal.supabase_client import get_supabase_client
            self._client = get_supabase_client()
        return self._client

    def get_room_template(self, room_type: str) -> Optional[RoomTemplate]:
        """Fetch room template by room type.
        
        Args:
            room_type: The type of room to fetch template for.
            
        Returns:
            RoomTemplate if found, None otherwise.
        """
        # Use cache if available
        if self._room_templates_cache is not None:
            return self._room_templates_cache.get(room_type.lower())

        try:
            response = (
                self.client.schema("amadeus")
                .table("room_templates")
                .select("*")
                .eq("room_type", room_type.lower())
                .execute()
            )
            if response.data and len(response.data) > 0:
                return RoomTemplate(**response.data[0])
        except Exception:
            pass
        
        return None

    def get_all_room_templates(self) -> dict[str, RoomTemplate]:
        """Fetch all room templates and cache them.
        
        Returns:
            Dictionary mapping room_type to RoomTemplate.
        """
        if self._room_templates_cache is not None:
            return self._room_templates_cache

        templates: dict[str, RoomTemplate] = {}
        try:
            response = (
                self.client.schema("amadeus")
                .table("room_templates")
                .select("*")
                .execute()
            )
            for row in response.data or []:
                template = RoomTemplate(**row)
                templates[template.room_type.lower()] = template
        except Exception:
            pass

        self._room_templates_cache = templates
        return templates

    def get_cable_specs(self, material: str = "copper") -> list[CableSpec]:
        """Fetch cable specifications ordered by size.
        
        Args:
            material: Cable material filter (default: copper).
            
        Returns:
            List of CableSpec sorted by size.
        """
        if self._cable_specs_cache is not None:
            return [c for c in self._cable_specs_cache if c.material == material]

        specs: list[CableSpec] = []
        try:
            response = (
                self.client.schema("amadeus")
                .table("cable_specs")
                .select("*")
                .eq("material", material)
                .order("size_sqmm")
                .execute()
            )
            for row in response.data or []:
                specs.append(CableSpec(**row))
        except Exception:
            pass

        return specs

    def get_all_cable_specs(self) -> list[CableSpec]:
        """Fetch all cable specs and cache them.
        
        Returns:
            List of all CableSpec.
        """
        if self._cable_specs_cache is not None:
            return self._cable_specs_cache

        specs: list[CableSpec] = []
        try:
            response = (
                self.client.schema("amadeus")
                .table("cable_specs")
                .select("*")
                .order("size_sqmm")
                .execute()
            )
            for row in response.data or []:
                specs.append(CableSpec(**row))
        except Exception:
            pass

        self._cable_specs_cache = specs
        return specs

    def get_breaker_specs(self) -> list[BreakerSpec]:
        """Fetch breaker specifications ordered by rating.
        
        Returns:
            List of BreakerSpec sorted by rating.
        """
        if self._breaker_specs_cache is not None:
            return self._breaker_specs_cache

        specs: list[BreakerSpec] = []
        try:
            response = (
                self.client.schema("amadeus")
                .table("breaker_specs")
                .select("*")
                .order("rating_a")
                .execute()
            )
            for row in response.data or []:
                specs.append(BreakerSpec(**row))
        except Exception:
            pass

        self._breaker_specs_cache = specs
        return specs

    def get_conduit_specs(self) -> list[ConduitSpec]:
        """Fetch conduit specifications ordered by size.
        
        Returns:
            List of ConduitSpec sorted by size.
        """
        if self._conduit_specs_cache is not None:
            return self._conduit_specs_cache

        specs: list[ConduitSpec] = []
        try:
            response = (
                self.client.schema("amadeus")
                .table("conduit_specs")
                .select("*")
                .order("size_mm")
                .execute()
            )
            for row in response.data or []:
                specs.append(ConduitSpec(**row))
        except Exception:
            pass

        self._conduit_specs_cache = specs
        return specs

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._room_templates_cache = None
        self._cable_specs_cache = None
        self._breaker_specs_cache = None
        self._conduit_specs_cache = None


# Default room templates when database is not available
DEFAULT_ROOM_TEMPLATES: dict[str, RoomTemplate] = {
    "bedroom": RoomTemplate(
        room_type="bedroom",
        description="Standard bedroom",
        lighting_load_w_sqm=15.0,
        outlet_load_w=180.0,
        outlet_count_per_sqm=0.1,
        has_ac_circuit=True,
        ac_load_w=1500.0,
        lighting_demand_factor=1.0,
        outlet_demand_factor=0.5,
        ac_demand_factor=1.0,
    ),
    "living_room": RoomTemplate(
        room_type="living_room",
        description="Living room",
        lighting_load_w_sqm=20.0,
        outlet_load_w=180.0,
        outlet_count_per_sqm=0.15,
        has_ac_circuit=True,
        ac_load_w=2500.0,
        lighting_demand_factor=1.0,
        outlet_demand_factor=0.5,
        ac_demand_factor=1.0,
    ),
    "kitchen": RoomTemplate(
        room_type="kitchen",
        description="Kitchen",
        lighting_load_w_sqm=20.0,
        outlet_load_w=180.0,
        outlet_count_per_sqm=0.2,
        has_special_outlet=True,
        special_outlet_load_w=3000.0,
        lighting_demand_factor=1.0,
        outlet_demand_factor=0.75,
    ),
    "bathroom": RoomTemplate(
        room_type="bathroom",
        description="Bathroom",
        lighting_load_w_sqm=15.0,
        outlet_load_w=180.0,
        outlet_count_per_sqm=0.05,
        lighting_demand_factor=1.0,
        outlet_demand_factor=0.5,
    ),
    "office": RoomTemplate(
        room_type="office",
        description="Office/Study room",
        lighting_load_w_sqm=25.0,
        outlet_load_w=180.0,
        outlet_count_per_sqm=0.2,
        has_ac_circuit=True,
        ac_load_w=1500.0,
        lighting_demand_factor=1.0,
        outlet_demand_factor=0.75,
        ac_demand_factor=1.0,
    ),
    "storage": RoomTemplate(
        room_type="storage",
        description="Storage room",
        lighting_load_w_sqm=10.0,
        outlet_load_w=180.0,
        outlet_count_per_sqm=0.05,
        lighting_demand_factor=0.5,
        outlet_demand_factor=0.25,
    ),
}


# Default cable specs (NEC/EIT standard copper THW cables)
DEFAULT_CABLE_SPECS: list[CableSpec] = [
    CableSpec(
        size_sqmm=1.5,
        material="copper",
        insulation_type="THW",
        ampacity_30c=18,
        ampacity_40c=15,
        resistance_ohm_km=12.1,
        outer_diameter_mm=3.5,
    ),
    CableSpec(
        size_sqmm=2.5,
        material="copper",
        insulation_type="THW",
        ampacity_30c=25,
        ampacity_40c=21,
        resistance_ohm_km=7.41,
        outer_diameter_mm=4.0,
    ),
    CableSpec(
        size_sqmm=4.0,
        material="copper",
        insulation_type="THW",
        ampacity_30c=34,
        ampacity_40c=28,
        resistance_ohm_km=4.61,
        outer_diameter_mm=4.8,
    ),
    CableSpec(
        size_sqmm=6.0,
        material="copper",
        insulation_type="THW",
        ampacity_30c=44,
        ampacity_40c=36,
        resistance_ohm_km=3.08,
        outer_diameter_mm=5.5,
    ),
    CableSpec(
        size_sqmm=10.0,
        material="copper",
        insulation_type="THW",
        ampacity_30c=61,
        ampacity_40c=50,
        resistance_ohm_km=1.83,
        outer_diameter_mm=7.0,
    ),
    CableSpec(
        size_sqmm=16.0,
        material="copper",
        insulation_type="THW",
        ampacity_30c=82,
        ampacity_40c=68,
        resistance_ohm_km=1.15,
        outer_diameter_mm=8.5,
    ),
    CableSpec(
        size_sqmm=25.0,
        material="copper",
        insulation_type="THW",
        ampacity_30c=108,
        ampacity_40c=89,
        resistance_ohm_km=0.727,
        outer_diameter_mm=10.5,
    ),
    CableSpec(
        size_sqmm=35.0,
        material="copper",
        insulation_type="THW",
        ampacity_30c=135,
        ampacity_40c=111,
        resistance_ohm_km=0.524,
        outer_diameter_mm=12.0,
    ),
]


# Default breaker ratings (standard MCB ratings)
DEFAULT_BREAKER_SPECS: list[BreakerSpec] = [
    BreakerSpec(rating_a=6, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=10, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=16, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=20, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=25, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=32, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=40, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=50, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=63, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=80, poles=1, type="MCB", trip_curve="C"),
    BreakerSpec(rating_a=100, poles=1, type="MCCB", trip_curve="C"),
    BreakerSpec(rating_a=125, poles=1, type="MCCB", trip_curve="C"),
    BreakerSpec(rating_a=160, poles=1, type="MCCB", trip_curve="C"),
    BreakerSpec(rating_a=200, poles=1, type="MCCB", trip_curve="C"),
]


# Default conduit specs (PVC conduits per NEC)
DEFAULT_CONDUIT_SPECS: list[ConduitSpec] = [
    ConduitSpec(size_mm=16, material="PVC", internal_area_sqmm=137),
    ConduitSpec(size_mm=20, material="PVC", internal_area_sqmm=216),
    ConduitSpec(size_mm=25, material="PVC", internal_area_sqmm=353),
    ConduitSpec(size_mm=32, material="PVC", internal_area_sqmm=573),
    ConduitSpec(size_mm=40, material="PVC", internal_area_sqmm=885),
    ConduitSpec(size_mm=50, material="PVC", internal_area_sqmm=1385),
    ConduitSpec(size_mm=63, material="PVC", internal_area_sqmm=2210),
]
