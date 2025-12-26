
from mcp_core_v2.models.contracts import DesignRequest, ElectricalLoad, Location, PanelSpecification, VoltageType
try:
    # 1. Toxic Load: 15,000 kW (MegaWatt) -> Should fail but currently passes
    toxic_load = ElectricalLoad(
        id="load_1",
        name="Nuclear Reactor",
        load_type="other",
        voltage=VoltageType.SINGLE_PHASE_230V,  # 1-phase!
        power_watts=15000000,  # 15 MW
        location=Location(room="Basement")
    )
    
    # 2. Toxic Distance: -50 meters -> Physics violation
    req = DesignRequest(
        session_id="toxic_1",
        project_name="Chaos Project",
        loads=[toxic_load],
        panels=[],
        service_voltage=VoltageType.SINGLE_PHASE_230V,
        utility_service_size=100,
        site_context={"distance_to_transformer": -50} # Negative distance
    )
    
    print("❌ VULNERABILITY CONFIRMED: Allowed 15MW load on 1-phase and -50m distance!")
except Exception as e:
    print(f"✅ BLOCKED: {e}")
