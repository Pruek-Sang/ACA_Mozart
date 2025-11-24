"""FastAPI application for MCP Core v2.

Exposes the /mcp/v2/run endpoint for electrical design processing.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models.contracts import ProjectInputSpec, McpRunResult
from pipeline import MCPPipeline
from dal.catalog_dal import CatalogDAL
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global pipeline instance
_pipeline: MCPPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _pipeline
    
    logger.info("Initializing MCP Core v2 application")
    
    # Initialize pipeline
    catalog_dal = CatalogDAL()
    _pipeline = MCPPipeline(catalog_dal)
    
    logger.info("MCP Core v2 ready to accept requests")
    
    yield
    
    # Cleanup
    logger.info("Shutting down MCP Core v2")


# Create FastAPI app
app = FastAPI(
    title="MCP Core v2",
    description="Master Control Program for Electrical Design Automation",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "MCP Core v2",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    settings = get_settings()
    
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        "langsmith_enabled": settings.langchain_tracing_v2,
    }


@app.post("/mcp/v2/run", response_model=McpRunResult)
async def run_mcp_pipeline(input_spec: ProjectInputSpec) -> McpRunResult:
    """Execute the MCP electrical design pipeline.
    
    Takes a project input specification and returns a complete
    electrical design result including:
    - Circuit sizing (wires, breakers, conduits)
    - Power flow analysis
    - Compliance checking
    - AutoLISP script for CAD
    
    Args:
        input_spec: Project input specification
        
    Returns:
        McpRunResult with complete design output
        
    Raises:
        HTTPException: If pipeline execution fails
    """
    global _pipeline
    
    if _pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not initialized"
        )
    
    logger.info(f"Received request for project {input_spec.project_id}")
    
    try:
        result = _pipeline.run(input_spec)
        
        logger.info(
            f"Completed project {input_spec.project_id}: "
            f"{result.total_circuits} circuits, "
            f"{result.compliant_circuits} compliant"
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@app.get("/mcp/v2/status")
async def get_pipeline_status() -> Dict[str, Any]:
    """Get pipeline status and configuration."""
    settings = get_settings()
    
    return {
        "pipeline_ready": _pipeline is not None,
        "voltage_nominal": settings.voltage_nominal,
        "frequency": settings.frequency,
        "power_factor": settings.power_factor,
        "voltage_drop_limit_percent": settings.voltage_drop_limit_percent,
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
