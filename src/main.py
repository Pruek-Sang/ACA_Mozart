"""FastAPI application for MCP Core v2."""

from fastapi import FastAPI, HTTPException

from src.models.contracts import McpRunResult, ProjectInputSpec
from src.orchestration.pipeline import MCPPipeline

app = FastAPI(
    title="MCP Core v2",
    description="Mozart Calculation Pipeline - Automated Electrical Design System",
    version="2.0.0",
)


@app.get("/")
async def root():
    """Root endpoint returning service information."""
    return {
        "service": "MCP Core v2",
        "description": "Mozart Calculation Pipeline - Automated Electrical Design System",
        "version": "2.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/mcp/v2/run", response_model=McpRunResult)
async def run_mcp_pipeline(project_input: ProjectInputSpec) -> McpRunResult:
    """Execute the MCP pipeline for electrical design calculations.
    
    Takes architectural room inputs and outputs fully calculated electrical
    design data including:
    - Load calculations
    - Wire sizing
    - Breaker selection
    - Conduit sizing
    - Voltage drop analysis
    - Compliance verification
    - AutoCAD scripts
    
    Args:
        project_input: ProjectInputSpec with project and room definitions.
        
    Returns:
        McpRunResult with complete electrical design output.
        
    Raises:
        HTTPException: If pipeline execution fails.
    """
    try:
        pipeline = MCPPipeline()
        result = pipeline.run(project_input)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
