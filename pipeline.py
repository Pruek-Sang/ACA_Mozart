"""MCP Pipeline orchestration for MCP Core v2.

The main pipeline class that sequences all core modules to process
a project from input specification to final design result.
"""

import logging
from typing import Dict, Tuple

from models.contracts import ProjectInputSpec, McpRunResult
from models.baseline import BaselineContext
from dal.catalog_dal import CatalogDAL
from core.template_resolver import TemplateResolver
from core.load_calculator import LoadCalculator
from core.pandapower_adapter import PandapowerAdapter, PowerFlowResults
from core.wire_sizer import WireSizer, WireSizingResult
from core.breaker_selector import BreakerSelector, BreakerSelectionResult
from core.conduit_sizer import ConduitSizer, ConduitSizingResult
from core.compliance_checker import ComplianceChecker, ComplianceReport
from core.autolisp_generator import AutoLispGenerator
from core.result_builder import ResultBuilder
from config import get_settings

logger = logging.getLogger(__name__)


class MCPPipeline:
    """Main orchestration pipeline for MCP electrical design.
    
    Sequences all processing stages:
    1. Template Resolution - Convert input spec to detailed baseline
    2. Load Calculation - Calculate electrical loads and currents
    3. Power Flow Analysis - Run pandapower simulation
    4. Component Sizing - Size wires, breakers, conduits
    5. Compliance Checking - Validate against codes
    6. Script Generation - Generate AutoLISP output
    7. Result Building - Aggregate all results
    """

    def __init__(self, catalog_dal: CatalogDAL = None):
        """Initialize pipeline with dependencies.
        
        Args:
            catalog_dal: Optional catalog data access. Uses default if not provided.
        """
        settings = get_settings()
        
        # Initialize DAL
        self._catalog = catalog_dal or CatalogDAL()
        
        # Initialize core modules
        self._template_resolver = TemplateResolver(self._catalog)
        self._load_calculator = LoadCalculator(
            voltage=settings.voltage_nominal,
            power_factor=settings.power_factor
        )
        self._pandapower = PandapowerAdapter(
            self._catalog,
            voltage=settings.voltage_nominal
        )
        self._wire_sizer = WireSizer(
            self._catalog,
            voltage=settings.voltage_nominal,
            voltage_drop_limit=settings.voltage_drop_limit_percent
        )
        self._breaker_selector = BreakerSelector(self._catalog)
        self._conduit_sizer = ConduitSizer(self._catalog)
        self._compliance_checker = ComplianceChecker(
            voltage_drop_limit=settings.voltage_drop_limit_percent
        )
        self._autolisp_generator = AutoLispGenerator()
        self._result_builder = ResultBuilder()
        
        self._settings = settings

    def run(self, input_spec: ProjectInputSpec) -> McpRunResult:
        """Execute the complete MCP pipeline.
        
        Args:
            input_spec: Project input specification
            
        Returns:
            McpRunResult with complete design output
        """
        logger.info(f"Starting MCP pipeline for project {input_spec.project_id}")
        
        # Reset result builder for new run
        self._result_builder.reset()
        
        # Stage 1: Template Resolution
        logger.info("Stage 1: Template Resolution")
        context = self._template_resolver.resolve(input_spec)
        
        # Stage 2: Load Calculation
        logger.info("Stage 2: Load Calculation")
        context = self._load_calculator.calculate(context)
        
        # Stage 3: Power Flow Analysis
        logger.info("Stage 3: Power Flow Analysis")
        power_flow_results = self._run_power_flow(context)
        
        # Stage 4: Component Sizing
        logger.info("Stage 4: Component Sizing")
        circuit_results = self._size_all_circuits(context, power_flow_results)
        
        # Stage 5: Compliance Checking (done in stage 4 per circuit)
        logger.info("Stage 5: Compliance Checking")
        system_compliance = self._compliance_checker.check_system(context)
        if system_compliance.warnings:
            for warning in system_compliance.warnings:
                self._result_builder.add_warning(warning)
        
        # Stage 6: Script Generation
        logger.info("Stage 6: AutoLISP Generation")
        autolisp_script = self._autolisp_generator.generate(context)
        
        # Stage 7: Main Breaker Selection
        logger.info("Stage 7: Main Breaker Selection")
        total_demand = self._load_calculator.calculate_total_demand(context)
        main_breaker_a = self._breaker_selector.select_main_breaker(
            total_demand_load_w=total_demand,
            voltage=self._settings.voltage_nominal,
            power_factor=self._settings.power_factor
        )
        
        # Stage 8: Result Building
        logger.info("Stage 8: Building Final Result")
        result = self._result_builder.build(
            context=context,
            circuit_results=circuit_results,
            power_flow_results=power_flow_results,
            autolisp_script=autolisp_script,
            main_breaker_a=main_breaker_a,
        )
        
        logger.info(
            f"Pipeline complete: {result.total_circuits} circuits, "
            f"{result.compliant_circuits} compliant, "
            f"main breaker {result.main_breaker_recommended_a}A"
        )
        
        return result

    def _run_power_flow(self, context: BaselineContext) -> PowerFlowResults:
        """Run power flow analysis on the context.
        
        Args:
            context: Baseline context with calculated loads
            
        Returns:
            Power flow results
        """
        try:
            self._pandapower.build_network(context)
            return self._pandapower.run_power_flow()
        except Exception as e:
            logger.error(f"Power flow analysis failed: {e}")
            self._result_builder.add_warning(f"Power flow analysis failed: {e}")
            # Return fallback results
            return PowerFlowResults(
                total_load_kw=context.total_connected_load_w / 1000,
                total_current_a=0,
                power_factor=self._settings.power_factor,
                voltage_at_furthest_point_v=self._settings.voltage_nominal,
                max_voltage_drop_percent=0,
                convergence_achieved=False,
                bus_voltages={},
                line_currents={},
                line_loading_percent={},
            )

    def _size_all_circuits(
        self,
        context: BaselineContext,
        power_flow_results: PowerFlowResults
    ) -> Dict[str, Tuple[
        WireSizingResult,
        BreakerSelectionResult,
        ConduitSizingResult,
        ComplianceReport
    ]]:
        """Size all circuit components.
        
        Args:
            context: Baseline context
            power_flow_results: Results from power flow
            
        Returns:
            Dictionary mapping circuit_id to result tuples
        """
        results = {}
        
        for room in context.rooms:
            for circuit in room.circuits:
                # Get actual current from power flow if available
                actual_current = power_flow_results.line_currents.get(
                    f"line_{circuit.circuit_id}",
                    circuit.design_current_a
                )
                
                # Size wire
                wire_result = self._wire_sizer.size_wire(circuit, actual_current)
                
                # Select breaker
                breaker_result = self._breaker_selector.select_breaker(
                    circuit,
                    wire_result.ampacity_a,
                    actual_current
                )
                
                # Size conduit
                conduit_result = self._conduit_sizer.size_conduit(
                    wire_result.wire_size_mm2,
                    num_conductors=2,  # Single phase: live + neutral
                    include_ground=True
                )
                
                # Check compliance
                compliance = self._compliance_checker.check_circuit(
                    circuit, wire_result, breaker_result
                )
                
                results[circuit.circuit_id] = (
                    wire_result,
                    breaker_result,
                    conduit_result,
                    compliance
                )
        
        return results
