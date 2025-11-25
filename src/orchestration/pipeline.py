"""MCP Pipeline orchestrator for electrical design calculations."""

from typing import Optional

from src.core.autolisp_generator import AutoLispGenerator
from src.core.breaker_selector import BreakerSelector
from src.core.compliance_checker import ComplianceChecker
from src.core.conduit_sizer import ConduitSizer
from src.core.load_calculator import LoadCalculator
from src.core.pandapower_adapter import PandapowerAdapter
from src.core.result_builder import ResultBuilder
from src.core.template_resolver import TemplateResolver
from src.core.wire_sizer import WireSizer
from src.dal.catalog_dal import CatalogDAL
from src.models.contracts import McpRunResult, ProjectInputSpec


class MCPPipeline:
    """Main orchestration pipeline for MCP Core v2.
    
    Orchestrates the flow:
    1. Resolve templates -> BaselineContext
    2. Calculate loads
    3. Size wires
    4. Run circuit simulation (Pandapower)
    5. Select breakers
    6. Size conduits
    7. Check compliance
    8. Generate AutoLISP
    9. Build result
    """

    def __init__(self, dal: Optional[CatalogDAL] = None):
        """Initialize the pipeline with optional DAL.
        
        Args:
            dal: CatalogDAL instance for database access. If None, defaults are used.
        """
        self.dal = dal

        # Initialize pipeline components
        self.template_resolver = TemplateResolver(dal=dal)
        self.load_calculator = LoadCalculator()
        self.wire_sizer = WireSizer(dal=dal)
        self.pandapower_adapter = PandapowerAdapter()
        self.breaker_selector = BreakerSelector(dal=dal)
        self.conduit_sizer = ConduitSizer(dal=dal)
        self.compliance_checker = ComplianceChecker()
        self.autolisp_generator = AutoLispGenerator()
        self.result_builder = ResultBuilder()

    def run(self, project_input: ProjectInputSpec) -> McpRunResult:
        """Execute the complete MCP pipeline.
        
        Args:
            project_input: ProjectInputSpec with room definitions.
            
        Returns:
            McpRunResult with complete electrical design data.
        """
        # Step 1: Resolve templates to baseline context
        context = self.template_resolver.resolve(project_input)

        # Step 2: Calculate loads and design currents
        context = self.load_calculator.calculate(context)

        # Step 3: Size wires based on current and voltage drop
        context = self.wire_sizer.size_wires(context)

        # Step 4: Run power flow simulation for voltage drops
        context = self.pandapower_adapter.run_power_flow(context)

        # Step 5: Select breakers
        context = self.breaker_selector.select_breakers(context)

        # Step 6: Size conduits
        context = self.conduit_sizer.size_conduits(context)

        # Step 7: Check compliance
        context = self.compliance_checker.check(context)

        # Step 8: Generate AutoLISP script
        context.autolisp_script = self.autolisp_generator.generate(context)

        # Step 9: Build final result
        result = self.result_builder.build(context)

        return result
