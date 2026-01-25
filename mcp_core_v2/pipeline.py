"""Main pipeline orchestrator for electrical design."""

from typing import Dict, Any, Optional, List
from models.contracts import DesignRequest, DesignResult, ElectricalLoad, LoadType
from core.template_resolver import get_template_resolver
from core.load_calculator import get_load_calculator
from core.wire_sizer import get_wire_sizer
from core.breaker_selector import get_breaker_selector
from core.conduit_sizer import get_conduit_sizer
from core.compliance_checker import get_compliance_checker
from core.autolisp_generator import get_autolisp_generator
from core.result_builder import get_result_builder
from core.circuit_grouper import get_circuit_grouper, GroupedCircuit, check_three_phase_required, calculate_connected_load
from core.lighting_calculator import get_lighting_calculator
from core.room_defaults import get_room_defaults_manager
from models.catalog_models import BreakerPoles, ConductorMaterial, BreakerType
from config import get_settings, get_branch_distance_feet, METERS_TO_FEET
from exceptions import InvalidSpecError, UnsupportedProjectError, ThreePhaseRequiredError
# [NEXIA EXTENSION] Import Context Injectors
from context import DeratingInjector, KaRatingInjector, NgLinkInjector
from context.input_sanitizer_injector import InputSanitizerInjector
# [3-PHASE EXTENSION] Import Phase Balance Injector
from context.phase_balance_injector import get_phase_balance_injector
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
        self.input_sanitizer = InputSanitizerInjector()  # 🆕 PRE-validation
        
        # [3-PHASE EXTENSION] Initialize Phase Balance Injector
        self.phase_balance_injector = get_phase_balance_injector(max_imbalance=15.0)
        
        # [3-PHASE] Configuration
        self.three_phase_threshold_kw = 25.0  # วสท. 2564
    
    def _check_three_phase_threshold(self, request: DesignRequest) -> Dict[str, Any]:
        """
        [CP-3PH-DETECT] Check if 3-phase system is required based on load.
        
        Sprint 1: Threshold Detection
        - Calculate connected load
        - Check against 25kW threshold
        - Raise ThreePhaseRequiredError if load exceeds threshold but 1-phase specified
        
        Returns:
            Dict with keys:
            - is_three_phase: bool
            - connected_load_kw: float  
            - warnings: list
        """
        logger.info("[CP-3PH-DETECT] Checking 3-phase threshold...")
        
        try:
            is_required, connected_kw, warnings = check_three_phase_required(
                loads=request.loads,
                service_voltage=request.service_voltage,
                threshold_kw=self.three_phase_threshold_kw
            )
            
            # Determine if current system is 3-phase
            voltage_str = request.service_voltage.value if hasattr(request.service_voltage, 'value') else str(request.service_voltage)
            is_three_phase = '3PH' in voltage_str.upper() or 'THREE' in voltage_str.upper()
            
            result = {
                'is_three_phase': is_three_phase,
                'connected_load_kw': connected_kw,
                'three_phase_required': is_required,
                'warnings': warnings
            }
            
            logger.info(
                f"[CP-3PH-DETECT] Result: is_3phase={is_three_phase}, "
                f"connected={connected_kw:.2f}kW, required={is_required}"
            )
            
            return result
            
        except ThreePhaseRequiredError:
            # Re-raise to be caught by execute()
            raise
    
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
        # [CP7] Checkpoint: Pipeline Entry
        loads_count = len(request.loads) if request.loads else 0
        rooms_count = len(request.rooms) if hasattr(request, 'rooms') and request.rooms else 0
        logger.info(f"[CP7-IN] Pipeline start: {rooms_count} rooms, {loads_count} loads, session={request.session_id}")
        
        try:
            # 🆕 PRE-FLIGHT CHECK: Sanitize inputs before processing
            sanitize_result = self.input_sanitizer.sanitize(request)
            if not sanitize_result.is_valid:
                logger.warning(f"[SANITIZE] Blocked: {len(sanitize_result.errors)} errors")
                return self.result_builder.build_result(
                    request=request,
                    calculations={},
                    wire_sizing={},
                    breaker_selections={},
                    conduit_sizing={},
                    compliance_report={"status": "BLOCKED", "reason": "Input Validation Failed"},
                    grouped_circuits=[],
                    autolisp_code=None,
                    errors=sanitize_result.errors,
                    warnings=sanitize_result.warnings
                )
            
            # Add sanitizer warnings to result (if any)
            sanitize_warnings = sanitize_result.warnings
            
            # Validate input
            self._validate_request(request)
            
            # ============================================================
            # [3-PHASE] Step 0: Check 3-phase threshold (Sprint 1)
            # ============================================================
            logger.info("[CP-3PH-DETECT] Step 0: Checking 3-phase threshold")
            three_phase_check = self._check_three_phase_threshold(request)
            is_three_phase = three_phase_check['is_three_phase']
            three_phase_warnings = three_phase_check.get('warnings', [])
            
            # Add 3-phase warnings to sanitize warnings
            sanitize_warnings.extend(three_phase_warnings)
            
            logger.info(
                f"[CP-3PH-DETECT] System: {'3-Phase' if is_three_phase else '1-Phase'}, "
                f"Connected: {three_phase_check['connected_load_kw']:.2f} kW"
            )
            
            # ============================================================
            # [3-PHASE] Step 0.5: Apply Phase Balance (if 3-phase) - Sprint 2
            # ============================================================
            phase_balance_result = None
            if is_three_phase:
                logger.info("[CP-3PH-BALANCE] Step 0.5: Applying phase balance")
                try:
                    # This will assign loads to L1/L2/L3
                    phase_balance_result = self.phase_balance_injector.inject(request)
                    logger.info(f"[CP-3PH-BALANCE] Phase balance applied successfully")
                except NotImplementedError:
                    # Phase balance not yet implemented - continue with warning
                    logger.warning("[CP-3PH-BALANCE] Phase balance injector not yet implemented, skipping")
                    three_phase_warnings.append(
                        "⚠️ Phase balance injector ยังไม่ implement - โหลดยังไม่ถูกแบ่งใน L1/L2/L3"
                    )
            
            # Step 1: Resolve templates
            logger.info("Step 1: Resolving design templates")
            self._resolve_templates(request)
            
            # Step 1.5: Group circuits (NEW - consolidate loads into proper circuits)
            logger.info("Step 1.5: Grouping circuits (lighting/receptacle by floor)")
            grouped_circuits = self._group_circuits(request)
            logger.info(f"[CP7] Grouped into {len(grouped_circuits)} circuits")
            
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
            
            # Step 6: Check compliance (including VD limits per วสท. 2564)
            logger.info("Step 6: Checking NEC/EIT/วสท. compliance")
            compliance_report = self._check_compliance(request, wire_sizing)
            
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
            print(f"[MCP-DEBUG] site_context received: {site_context}")  # Guaranteed output
            print(f"[MCP-DEBUG] distance_to_transformer: {site_context.get('distance_to_transformer', 'MISSING')}")
            
            # 1. Enforce kA Ratings
            result = self.ka_rating_injector.inject(result, site_context)
            logger.info(f"[INJECT] kA rating check: distance={site_context.get('distance_to_transformer', 'N/A')}")
            print(f"[MCP-DEBUG] After kA inject - warnings: {getattr(result, 'warnings', [])}")
            
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
        """Size wires for all circuits with voltage drop calculation.
        
        Distance priority:
        1. load.branch_distance_m (user specified per load)
        2. Default table based on building_type + floor_level
        3. Fallback: 15m (conservative default)
        """
        wire_sizing = {}
        
        # Track if we used default distance (for warning)
        used_default_distance = False
        
        for load in request.loads:
            # Calculate load current
            current = self.load_calculator.calculate_load_current(load)
            
            # ============================================================
            # Distance Calculation (วสท. 2564 Compliant)
            # ============================================================
            # Priority: load.branch_distance_m > default table > fallback
            if hasattr(load, 'branch_distance_m') and load.branch_distance_m is not None:
                # User specified distance
                distance_feet = load.branch_distance_m * METERS_TO_FEET
                distance_source = "user_specified"
            else:
                # Use default table based on building type and floor
                building_type = getattr(request, 'building_type', None)
                floor_level = getattr(load.location, 'floor', None)
                distance_feet = get_branch_distance_feet(building_type, floor_level)
                distance_source = "default_table"
                used_default_distance = True
            
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
            
            # Call wire sizer with full derating support
            # Use VD limit from settings (วสท. 2564: Branch ≤ 3%)
            max_vd_percent = getattr(self.settings, 'vd_limit_branch_percent', 3.0)
            
            wire_result = self.wire_sizer.size_wire_with_voltage_drop(
                current=current,
                distance_feet=distance_feet,
                voltage=voltage,
                max_voltage_drop_percent=max_vd_percent,
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
            
            # ============================================================
            # Add distance metadata for output display and warnings
            # ============================================================
            wire_result['distance_m'] = distance_feet / METERS_TO_FEET
            wire_result['distance_feet'] = distance_feet
            wire_result['distance_source'] = distance_source
            wire_result['used_default_distance'] = (distance_source == "default_table")
            
            wire_sizing[load.id] = wire_result

            # ============================================================
            # [SAFETY-FIX] Enforce 2.5mm² minimum for AC/Receptacles
            # ============================================================
            # วสท. Standard: Min 2.5 sq.mm for Power Circuits
            if load.load_type in [LoadType.HVAC, LoadType.RECEPTACLE, LoadType.MOTOR, LoadType.APPLIANCE]:
                current_size = wire_result.get('wire_size', '0')
                safety_min = "2.5"
                try:
                    # Simple comparison for small sizes (1.5 < 2.5)
                    # Note: Larger sizes like 1/0 won't trigger this < 2.5 check anyway
                    if float(current_size) < float(safety_min):
                        logger.warning(f"[SAFETY] Forcing {load.name} to {safety_min}mm² (was {current_size}mm²)")
                        
                        # Re-calculate VD with new size
                        vd, vd_pct = self.wire_sizer._calculate_voltage_drop(
                            current=current,
                            distance_feet=distance_feet,
                            wire_size=safety_min,
                            voltage=voltage,
                            operating_temp_c=75,
                            power_factor=pf,
                            material=ConductorMaterial.COPPER
                        )
                        
                        # Update result
                        wire_result['wire_size'] = safety_min
                        wire_result['voltage_drop'] = vd
                        wire_result['voltage_drop_percent'] = vd_pct
                        wire_result['ampacity'] = self.wire_sizer.get_wire_properties(safety_min)['copper_ampacity_75C']
                        
                        # Add note
                        notes = wire_result.get('notes', [])
                        if isinstance(notes, str): notes = [notes]
                        # Flag for frontend to show warning/info
                        wire_result['is_min_enforced'] = True
                except ValueError:
                    pass  # Non-numeric size (e.g. 1/0), likely large enough
        
        # Add global flag for default distance usage
        if used_default_distance:
            wire_sizing['_metadata'] = {
                'used_default_distance': True,
                'warning': '⚠️ ค่า Voltage Drop คำนวณจากระยะ Default ตามประเภทอาคาร หากระยะจริงมากกว่านี้ ควรระบุในคำขอ'
            }
        
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
    
    def _check_compliance(
        self,
        request: DesignRequest,
        wire_sizing: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Check design for NEC/EIT/วสท. compliance including VD limits."""
        return self.compliance_checker.check_design(request, wire_sizing)
    
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
