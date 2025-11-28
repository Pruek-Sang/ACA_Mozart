"""Main entry point for MCP Core v2."""

import sys
import logging
from typing import Optional
from datetime import datetime

from models.contracts import (
    DesignRequest, ElectricalLoad, PanelSpecification,
    Location, VoltageType, LoadType
)
from pipeline import get_design_pipeline
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_core_v2.log')
    ]
)

logger = logging.getLogger(__name__)


def create_sample_request() -> DesignRequest:
    """Create a sample design request for testing."""
    
    # Define some sample loads
    loads = [
        ElectricalLoad(
            id="load_001",
            name="Office Lighting",
            load_type=LoadType.LIGHTING,
            voltage=VoltageType.SINGLE_PHASE_120V,
            power_watts=1200,
            quantity=8,
            location=Location(room="Office", floor="1"),
            is_continuous=True
        ),
        ElectricalLoad(
            id="load_002",
            name="Receptacles",
            load_type=LoadType.RECEPTACLE,
            voltage=VoltageType.SINGLE_PHASE_120V,
            power_watts=180,
            quantity=12,
            location=Location(room="Office", floor="1"),
            is_continuous=False
        ),
        ElectricalLoad(
            id="load_003",
            name="HVAC Unit",
            load_type=LoadType.HVAC,
            voltage=VoltageType.SINGLE_PHASE_240V,
            power_watts=3600,
            quantity=1,
            location=Location(room="Mechanical", floor="Roof"),
            is_continuous=True
        ),
        ElectricalLoad(
            id="load_004",
            name="Conference Room Lighting",
            load_type=LoadType.LIGHTING,
            voltage=VoltageType.SINGLE_PHASE_120V,
            power_watts=800,
            quantity=6,
            location=Location(room="Conference Room", floor="1"),
            is_continuous=True
        ),
    ]
    
    # Define a panel
    panels = [
        PanelSpecification(
            id="panel_001",
            name="LP-1",
            voltage=VoltageType.SINGLE_PHASE_120V,
            main_breaker_rating=200,
            number_of_circuits=42,
            location=Location(room="Electrical Room", floor="1"),
            feeds=["load_001", "load_002", "load_003", "load_004"]
        )
    ]
    
    # Create the design request
    request = DesignRequest(
        session_id="session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        project_name="Sample Office Building",
        project_number="2024-001",
        loads=loads,
        panels=panels,
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )
    
    return request


def main():
    """Main entry point."""
    logger.info("MCP Core v2 Starting...")
    
    # Get settings
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"NEC Version: {settings.nec_version}")
    
    # Create sample request
    logger.info("Creating sample design request...")
    request = create_sample_request()
    
    # Get pipeline
    pipeline = get_design_pipeline()
    
    # Execute design
    logger.info("Executing design pipeline...")
    try:
        result = pipeline.execute(request)
        
        # Log results
        logger.info("Design completed successfully!")
        logger.info(f"Session ID: {result.session_id}")
        logger.info(f"Errors: {len(result.errors)}")
        logger.info(f"Warnings: {len(result.warnings)}")
        
        if result.errors:
            logger.error("Errors encountered:")
            for error in result.errors:
                logger.error(f"  - {error}")
        
        if result.warnings:
            logger.warning("Warnings:")
            for warning in result.warnings:
                logger.warning(f"  - {warning}")
        
        # Print summary
        from core.result_builder import get_result_builder
        result_builder = get_result_builder()
        summary = result_builder.create_summary(result)
        
        logger.info("\nDesign Summary:")
        logger.info(f"  Project: {summary['project_name']}")
        logger.info(f"  Panels: {summary['component_count']['panels']}")
        logger.info(f"  Loads: {summary['component_count']['loads']}")
        logger.info(f"  Circuits: {summary['component_count']['circuits']}")
        logger.info(f"  Total Load: {summary['total_load_va']} VA")
        logger.info(f"  Compliant: {summary['status']['compliant']}")
        
        # Save AutoLISP if generated
        if result.autolisp_code:
            lisp_filename = f"design_{result.session_id}.lsp"
            with open(lisp_filename, 'w') as f:
                f.write(result.autolisp_code)
            logger.info(f"AutoLISP code saved to {lisp_filename}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Design pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
