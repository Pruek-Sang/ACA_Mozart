"""Main pipeline orchestrator for electrical design."""

from typing import Dict, Any, Optional, List
from models.contracts import DesignRequest, DesignResult, ElectricalLoad
from core.template_resolver import get_template_resolver
from core.load_calculator import get_load_calculator
from core.wire_sizer import get_wire_sizer
from core.breaker_selector import get_breaker_selector
from core.conduit_sizer import get_conduit_sizer
from core.compliance_checker import get_compliance_checker
from core.autolisp_generator import get_autolisp_generator
from core.result_builder import get_result_builder
from core.circuit_grouper import get_circuit_grouper, GroupedCircuit
from core.lighting_calculator import get_lighting_calculator
from core.room_defaults import get_room_defaults_manager
from models.catalog_models import BreakerPoles, ConductorMaterial, BreakerType
from config import get_settings
from exceptions import InvalidSpecError, UnsupportedProjectError
# [NEXIA EXTENSION] Import Context Injectors
from context import DeratingInjector, KaRatingInjector, NgLinkInjector
import logging

logger = logging.getLogger(__name__)


class DesignPipeline:
    """Orchestrates the complete electrical design process."""
    
    def __init__(self):
        """Initialize design pipeline with all required modules."""
        self.settings = get_settings()
        self.template_resolver = get_template_resolver()
        self.load_calculator = get_load_calculator()
        self.wire_sizer = get_wire_sizer()
        self.breaker_selector = get_breaker_selector()
        self.conduit_sizer = get_conduit_sizer()
        self.compliance_checker = get_compliance_checker()
        self.autolisp_generator = get_autolisp_generator()
        self.result_builder = get_result_builder()
        # New modules for circuit grouping
        # self.circuit_grouper IS NOW INSTANTIATED PER-REQUEST in _group_circuits
        # to ensure correct building floor context and state isolation.
        self.lighting_calculator = get_lighting_calculator()
        self.room_defaults = get_room_defaults_manager()
        
        # [NEXIA EXTENSION] Initialize Injectors
        self.derating_injector = DeratingInjector()
        self.ka_rating_injector = KaRatingInjector()
        self.ng_link_injector = NgLinkInjector()
    
    def _validate_request(self, request: DesignRequest):
        """Validate design request before processing.
        
        Raises:
            InvalidSpecError: If required fields are missing or invalid
            UnsupportedProjectError: If project type is not supported
        """
        # Check for required panels
        if not request.panels or len(request.panels) == 0:
            logger.warning("Request has no panels - using flexible mode")
            # Don't raise error, allow flexible design
        
        # Check for service voltage
        if not request.service_voltage:
            raise InvalidSpecError("service_voltage is required")
        
        # Check utility service size
        if not request.utility_service_size or request.utility_service_size <= 0:
            raise InvalidSpecError("utility_service_size must be a positive number")
        
        # Future: Check building type restrictions
        # if hasattr(request, 'building_type'):
        #     if request.building_type == "factory" or request.building_type == "industrial":
        #         raise UnsupportedProjectError(
        #             "MCP v2 supports residential and light commercial only. "
        #             "Industrial/factory projects require MCP Enterprise."
        #         )
    
    def execute(self, request: DesignRequest) -> DesignResult:
        """Execute the complete design pipeline."""
        logger.info(f"Starting design pipeline for session {request.session_id}")
        
        try:
            # Validate input
            self._validate_request(request)
            
            # Step 1: Resolve templates
            logger.info("Step 1: Resolving design templates")
            self._resolve_templates(request)
            
            # Step 1.5: Group circuits (NEW - consolidate loads into proper circuits)
            logger.info("Step 1.5: Grouping circuits (lighting/receptacle by floor)")
            grouped_circuits = self._group_circuits(request)
            
            # Step 2: Calculate loads
            logger.info("Step 2: Calculating electrical loads")
            calculations = self._calculate_loads(request)
            
            # [NEXIA EXTENSION] Inject Derating Factors (Pre-Wire Sizing)
            # Get site_context directly from request (sent by RAG via Adapter)
            site_context = request.site_context or {}
            
            # 🆕 LOGGING: Verify site_context received
            logger.info(f"[INJECT] site_context received: {site_context}")
            
            # Apply Derating to loads in request
            # This modifies the load objects in place, affecting subsequent steps (Wire Sizing)
            # Note: Load Calculation (Step 2) is already done, so reported "Connected Load" is based on original values.
            # This is PERFECT. We want reported load to be real, but wire sizing to be derated.
            self.derating_injector.inject(request.loads, site_context)
            logger.info(f"[INJECT] Derating applied with context: area={site_context.get('installation_area', 'N/A')}, grouping={site_context.get('conduit_grouping', 'N/A')}")
            
            # Step 3: Size wires
            logger.info("Step 3: Sizing conductors")
            wire_sizing = self._size_wires(request, calculations)
            
            # Step 4: Select breakers (now with circuit grouping awareness)
            logger.info("Step 4: Selecting circuit breakers")
            breaker_selections = self._select_breakers_v2(request, calculations, grouped_circuits)
            
            # Step 5: Size conduits
            logger.info("Step 5: Sizing conduits")
            conduit_sizing = self._size_conduits(request, wire_sizing, breaker_selections)
            
            # Step 6: Check compliance
            logger.info("Step 6: Checking NEC/EIT compliance")
            compliance_report = self._check_compliance(request)
            
            # Step 7: Generate AutoLISP
            logger.info("Step 7: Generating AutoLISP code")
            design_results = {
                'calculations': calculations,
                'wire_sizing': wire_sizing,
                'breaker_selections': breaker_selections,
                'conduit_sizing': conduit_sizing,
                'grouped_circuits': grouped_circuits  # Add grouped circuits to results
            }
            autolisp_code = self._generate_autolisp(request, design_results)
            
            # Step 8: Build result
            logger.info("Step 8: Building final result")
            result = self.result_builder.build_result(
                request=request,
                calculations=calculations,
                wire_sizing=wire_sizing,
                breaker_selections=breaker_selections,
                conduit_sizing=conduit_sizing,
                compliance_report=compliance_report,
                autolisp_code=autolisp_code,
                grouped_circuits=grouped_circuits  # Pass grouped circuits
            )
            
            # [NEXIA EXTENSION] Post-Process Injection (Safety & Compliance)
            # Get site_context directly from request
            site_context = request.site_context or {}
            
            # 1. Enforce kA Ratings
            result = self.ka_rating_injector.inject(result, site_context)
            logger.info(f"[INJECT] kA rating check: distance={site_context.get('distance_to_transformer', 'N/A')}")
            
            # 2. Enforce N-G Link Rules
            result = self.ng_link_injector.inject(result, site_context)
            logger.info(f"[INJECT] N-G Link check: panel_type={site_context.get('panel_type', 'N/A')}")
            
            logger.info(f"Design pipeline completed for session {request.session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            raise
    
    def _resolve_templates(self, request: DesignRequest) -> Dict[str, Any]:
        """Resolve design templates for all loads."""
        return self.template_resolver.resolve_circuit_requirements(request.loads)
    
    def _group_circuits(self, request: DesignRequest) -> List[Dict[str, Any]]:
        """Group loads into logical circuits.
        
        This consolidates individual loads into proper residential circuits:
        - Lighting: Grouped by floor (all bedroom lights on floor 1 → 1 circuit)
        - Receptacles: Grouped by floor (excludes bathrooms)
        - AC: Dedicated circuit per unit
        - Water Heater: Dedicated RCBO circuit
        - Kitchen high-power: Dedicated circuits
        
        Returns:
            List of grouped circuit dictionaries
        """
        # Calculate max floor to determine if high-rise
        num_floors = 1
        for load in request.loads:
            try:
                if load.location and load.location.floor:
                    f = int(load.location.floor)
                    if f > num_floors:
                        num_floors = f
            except (ValueError, TypeError):
                continue
                
        # Create a FRESH circuit grouper for this request
        # This isolates state and correctly applies diversity factor based on num_floors
        # (get_circuit_grouper is imported at top of file)
        grouper = get_circuit_grouper(num_floors=num_floors)
        
        # Group loads into circuits
        grouper.group_loads(request.loads)
        
        # Get summary which includes circuit list in dict format
        summary = grouper.get_circuit_summary()
        circuits = summary.get('circuits', [])
        
        logger.info(
            f"Grouped {len(request.loads)} loads into {len(circuits)} circuits "
            f"(Building floors: {num_floors}, High-rise: {grouper.is_high_rise})"
        )
        return circuits

    
    def _calculate_loads(self, request: DesignRequest) -> Dict[str, Any]:
        """Calculate loads for all panels."""
        calculations = {}
        
        for panel in request.panels:
            panel_calc = self.load_calculator.calculate_panel_load(panel, request.loads)
            calculations[panel.id] = panel_calc
        
        return calculations
    
    def _size_wires(
        self,
        request: DesignRequest,
        _calculations: Dict[str, Any]  # Prefix with _ to mark as intentionally unused
    ) -> Dict[str, Any]:
        """Size wires for all circuits."""
        wire_sizing = {}
        
        for load in request.loads:
            # Calculate load current
            current = self.load_calculator.calculate_load_current(load)
            
            # Size wire with voltage drop consideration
            # Assuming 100 feet distance for now
            # Import VoltageType enum
            from models.contracts import VoltageType
            
            # Thai standard: 230V 1-phase, 400V 3-phase
            voltage_map = {
                VoltageType.SINGLE_PHASE_230V: 230,  # Thai standard
                VoltageType.THREE_PHASE_400V: 400,   # Thai standard
                VoltageType.SINGLE_PHASE_120V: 120,  # US standard
                VoltageType.SINGLE_PHASE_240V: 240,  # US standard
                VoltageType.THREE_PHASE_208V: 208,   # US standard
                VoltageType.THREE_PHASE_480V: 480    # US standard
            }
            voltage = voltage_map.get(load.voltage, 230)  # Default to Thai 230V
            
            # Determine power factor
            pf = load.power_factor if load.power_factor else self.settings.default_power_factor
            
            # Determine number of conductors based on voltage type
            if load.voltage in [VoltageType.THREE_PHASE_208V, VoltageType.THREE_PHASE_480V]:
                num_conductors = 3  # 3-phase (3 current-carrying conductors)
            else:
                num_conductors = 2  # Single-phase (2 current-carrying: hot + neutral)
            
            # Get ambient temperature from settings (default 30°C if not configured)
            ambient_temp = getattr(self.settings, 'ambient_temperature_c', 30.0)
            
            # Determine distance (in future, could come from load.distance_m)
            # For now, use conservative default based on location/floor
            distance_feet = 100  # Conservative default
            # TODO: Future enhancement - get from load.location or load.distance_m
            
            # Call wire sizer with full derating support
            wire_result = self.wire_sizer.size_wire_with_voltage_drop(
                current=current,
                distance_feet=distance_feet,
                voltage=voltage,
                max_voltage_drop_percent=3.0,
                material=ConductorMaterial.COPPER,
                temperature_rating=75,  # NEC standard for THHN/THWN
                ambient_temp_c=ambient_temp,
                num_conductors=num_conductors,
                power_factor=pf,
                insulation_thickness_mm=0.0,  # No thermal insulation (typical)
                soil_resistivity=0.0  # Not buried (typical branch circuit)
            )
            
            # Add ground wire sizing
            if 'wire_size' in wire_result:
                # We'll need breaker rating for ground sizing, use a default for now
                wire_result['ground_size'] = self.wire_sizer.size_ground_wire(
                    circuit_breaker_rating=20  # Default, will be refined with breaker selection
                )
            
            wire_sizing[load.id] = wire_result
        
        return wire_sizing
    
    def _select_breakers(
        self,
        request: DesignRequest,
        calculations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select breakers for all circuits (legacy - 1 load = 1 circuit)."""
        breaker_selections = {}
        
        for load in request.loads:
            # Calculate load current
            current = self.load_calculator.calculate_load_current(load)
            
            # Determine poles based on voltage
            if 'THREE_PHASE' in load.voltage.value:
                poles = BreakerPoles.THREE
            elif load.voltage.value == '240V_1PH':
                poles = BreakerPoles.DOUBLE
            else:
                poles = BreakerPoles.SINGLE
            
            # Select breaker
            breaker_result = self.breaker_selector.select_breaker(
                load_current=current,
                poles=poles,
                continuous_load=load.is_continuous
            )
            
            breaker_selections[load.id] = breaker_result
        
        # Select main breakers for panels
        for panel in request.panels:
            panel_calc = calculations.get(panel.id, {})
            demand_current = panel_calc.get('demand_current', 0)
            
            # Main breaker selection
            voltage_val = int(panel.voltage.value.split('V')[0])
            phases = 3 if 'THREE_PHASE' in panel.voltage.value else 1
            
            # Cap main breaker at panel's specified rating or utility service size
            max_allowed = min(
                panel.main_breaker_rating,
                request.utility_service_size
            )
            
            # If demand exceeds max allowed, use max and add warning
            if demand_current > max_allowed:
                logger.warning(
                    f"Panel {panel.id}: Demand current {demand_current:.1f}A exceeds "
                    f"max allowed {max_allowed}A. Using {max_allowed}A main breaker. "
                    f"Consider upgrading service or reducing loads."
                )
                effective_demand = max_allowed * 0.8  # Use 80% of max for safety margin
            else:
                effective_demand = demand_current
            
            main_breaker = self.breaker_selector.select_main_breaker(
                service_load=effective_demand,
                voltage=voltage_val,
                phases=phases
            )
            
            # Override to respect panel's main breaker rating
            if main_breaker.get('breaker_rating', 0) > max_allowed:
                main_breaker['breaker_rating'] = panel.main_breaker_rating
                main_breaker['capped'] = True
                main_breaker['original_calculated'] = demand_current
                main_breaker['warning'] = (
                    f"Main breaker capped at {panel.main_breaker_rating}A. "
                    f"Calculated demand was {demand_current:.1f}A. "
                    f"Consider upgrading utility service."
                )
            
            breaker_selections[f"{panel.id}_main"] = main_breaker
        
        return breaker_selections
    
    def _select_breakers_v2(
        self,
        request: DesignRequest,
        calculations: Dict[str, Any],
        grouped_circuits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select breakers for grouped circuits (NEW - proper residential grouping).
        
        This uses circuit grouping to select breakers:
        - Lighting circuits: 16A/20A standard breaker
        - Receptacle circuits: 16A/20A standard breaker  
        - AC dedicated: 20A-32A based on BTU
        - Water heater: RCBO 25A 30mA
        - Kitchen: 20A dedicated
        
        Returns:
            Dict with breaker selections keyed by circuit_id
        """
        breaker_selections = {}
        
        for circuit in grouped_circuits:
            circuit_id = circuit.get('circuit_id', circuit.get('id'))
            circuit_type = circuit.get('circuit_type', circuit.get('type', 'other'))
            total_current = circuit.get('total_current', circuit.get('current', 0))
            requires_rcbo = circuit.get('rcbo', False)
            
            # Determine poles (Thai standard: 230V 1-phase = 1P, 400V 3-phase = 3P)
            if circuit.get('voltage', 230) > 300:
                poles = BreakerPoles.THREE
            else:
                poles = BreakerPoles.SINGLE
            
            # Select breaker type based on circuit type
            if requires_rcbo:
                # Water heater, outdoor, wet location - use RCBO
                breaker_result = self.breaker_selector.select_rcbo_breaker(
                    load_current=total_current,
                    poles=BreakerPoles.DOUBLE,  # RCBO typically 2P
                    trip_current_ma=30  # Standard 30mA
                )
            elif circuit_type == 'hvac':
                # AC dedicated circuit - higher rating
                breaker_result = self.breaker_selector.select_breaker(
                    load_current=total_current,
                    poles=poles,
                    continuous_load=True  # AC is continuous
                )
            else:
                # Standard breaker for lighting, receptacle, etc.
                breaker_result = self.breaker_selector.select_breaker(
                    load_current=total_current,
                    poles=poles,
                    continuous_load=False
                )
            
            # Add circuit info to breaker result
            breaker_result['circuit_info'] = {
                'circuit_name': circuit.get('name', circuit.get('circuit_name', 'Unknown')),
                'circuit_type': circuit_type,
                'floor': circuit.get('floor', 'unknown'),
                'load_count': circuit.get('loads', circuit.get('load_count', 1))
            }
            
            breaker_selections[circuit_id] = breaker_result
        
        # Select main breakers for panels (same as before)
        for panel in request.panels:
            panel_calc = calculations.get(panel.id, {})
            demand_current = panel_calc.get('demand_current', 0)
            
            voltage_val = int(panel.voltage.value.split('V')[0])
            phases = 3 if 'THREE_PHASE' in panel.voltage.value else 1
            
            max_allowed = min(
                panel.main_breaker_rating,
                request.utility_service_size
            )
            
            if demand_current > max_allowed:
                logger.warning(
                    f"Panel {panel.id}: Demand current {demand_current:.1f}A exceeds "
                    f"max allowed {max_allowed}A. Using {max_allowed}A main breaker."
                )
                effective_demand = max_allowed * 0.8
            else:
                effective_demand = demand_current
            
            main_breaker = self.breaker_selector.select_main_breaker(
                service_load=effective_demand,
                voltage=voltage_val,
                phases=phases
            )
            
            if main_breaker.get('breaker_rating', 0) > max_allowed:
                main_breaker['breaker_rating'] = panel.main_breaker_rating
                main_breaker['capped'] = True
                main_breaker['warning'] = (
                    f"Main breaker capped at {panel.main_breaker_rating}A. "
                    f"Calculated demand was {demand_current:.1f}A."
                )
            
            breaker_selections[f"{panel.id}_main"] = main_breaker
        
        logger.info(f"Selected breakers for {len(grouped_circuits)} grouped circuits")
        return breaker_selections
    
    def _size_conduits(
        self,
        request: DesignRequest,
        wire_sizing: Dict[str, Any],
        _breaker_selections: Dict[str, Any]  # Reserved for future use
    ) -> Dict[str, Any]:
        """Size conduits for all circuits."""
        conduit_sizing = {}
        
        for load in request.loads:
            wire_data = wire_sizing.get(load.id, {})
            
            if 'wire_size' not in wire_data:
                continue
            
            phase_wire = wire_data['wire_size']
            ground_wire = wire_data.get('ground_size', '12')
            
            # Determine number of phases
            num_phases = 3 if 'THREE_PHASE' in load.voltage.value else 1
            if load.voltage.value == '240V_1PH':
                num_phases = 2
            
            # Size conduit
            conduit_result = self.conduit_sizer.size_conduit_for_circuit(
                phase_wire_size=phase_wire,
                num_phases=num_phases,
                neutral_wire_size=phase_wire if num_phases > 1 else None,
                ground_wire_size=ground_wire
            )
            
            conduit_sizing[load.id] = conduit_result
        
        return conduit_sizing
    
    def _check_compliance(self, request: DesignRequest) -> Dict[str, Any]:
        """Check design for NEC compliance."""
        return self.compliance_checker.check_design(request)
    
    def _generate_autolisp(
        self,
        request: DesignRequest,
        design_results: Dict[str, Any]
    ) -> str:
        """Generate AutoLISP code for the design."""
        try:
            return self.autolisp_generator.generate_complete_drawing(
                request,
                design_results
            )
        except Exception as e:
            logger.error(f"AutoLISP generation failed: {e}")
            return f"; Error generating AutoLISP: {e}"


# Global instance
_design_pipeline: Optional[DesignPipeline] = None


def get_design_pipeline() -> DesignPipeline:
    """Get the global design pipeline instance."""
    global _design_pipeline
    if _design_pipeline is None:
        _design_pipeline = DesignPipeline()
    return _design_pipeline
