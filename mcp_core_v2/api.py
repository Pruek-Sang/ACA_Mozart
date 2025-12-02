"""
MCP Core API - FastAPI HTTP Interface

Exposes MCP calculation pipeline via REST API.
This is the MISSING piece for RAG → MCP integration.

Port: 5001 (default)
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import pipeline (use mock if dependencies missing)
try:
    from pipeline import get_design_pipeline
    from models.contracts import (
        DesignRequest, ElectricalLoad, PanelSpecification,
        Location, VoltageType, LoadType, DesignResult
    )
    PIPELINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Pipeline import failed: {e}. Using mock mode.")
    PIPELINE_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# API Models (match what RAG's mcp_client.py sends)
# =============================================================================

class LocationInput(BaseModel):
    room: str
    floor: Optional[str] = None

class LoadInput(BaseModel):
    id: str
    name: str
    load_type: str  # lighting, receptacle, hvac, motor, appliance, other
    voltage: str    # 120V_1PH, 240V_1PH, 208V_3PH, 480V_3PH
    power_watts: float
    quantity: int = 1
    location: LocationInput
    is_continuous: bool = False
    notes: Optional[str] = None

class PanelInput(BaseModel):
    id: str
    name: str
    voltage: str
    main_breaker_rating: int
    number_of_circuits: int
    location: LocationInput
    feeds: List[str] = Field(default_factory=list)

class DesignRequestInput(BaseModel):
    """Input from RAG adapter"""
    session_id: str
    project_name: str
    project_number: Optional[str] = None
    loads: List[LoadInput]
    panels: List[PanelInput]
    service_voltage: str
    utility_service_size: int = 100

class DesignResultOutput(BaseModel):
    """Output to RAG"""
    session_id: str
    calculations: Dict[str, Any] = Field(default_factory=dict)
    wire_sizing: Dict[str, Any] = Field(default_factory=dict)
    breaker_selections: Dict[str, Any] = Field(default_factory=dict)
    conduit_sizing: Dict[str, Any] = Field(default_factory=dict)
    compliance_report: Dict[str, Any] = Field(default_factory=dict)
    autolisp_code: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="MCP Core v2 API",
    version="2.0.0",
    description="Electrical Design Calculation Engine (NEC-based)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "MCP Core v2",
        "status": "alive",
        "pipeline_available": PIPELINE_AVAILABLE
    }

@app.get("/health")
async def health():
    """Health endpoint for RAG client"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/design", response_model=DesignResultOutput)
async def design(request: DesignRequestInput) -> DesignResultOutput:
    """
    Main design calculation endpoint
    
    Receives: DesignRequest from RAG adapter
    Returns: DesignResult with calculations
    """
    logger.info(f"Design request: {request.project_name} ({len(request.loads)} loads)")
    
    if not PIPELINE_AVAILABLE:
        # Return mock result for testing
        return _mock_design_result(request)
    
    try:
        # Convert input to internal format
        internal_request = _convert_to_internal(request)
        
        # Run pipeline
        pipeline = get_design_pipeline()
        result = pipeline.execute(internal_request)
        
        # Convert result to output format
        return _convert_to_output(result)
        
    except Exception as e:
        logger.error(f"Design failed: {e}", exc_info=True)
        return DesignResultOutput(
            session_id=request.session_id,
            errors=[str(e)],
            warnings=["Design calculation failed, returning partial result"]
        )

def _mock_design_result(request: DesignRequestInput) -> DesignResultOutput:
    """Generate mock result for testing when pipeline not available"""
    
    # Calculate totals
    total_watts = sum(load.power_watts * load.quantity for load in request.loads)
    total_amps = total_watts / 240  # Assume 240V
    
    # Mock wire sizing
    wire_sizing = {}
    for load in request.loads:
        amps = (load.power_watts * load.quantity) / 240
        if amps <= 15:
            wire = "2.5 mm² (14 AWG)"
        elif amps <= 20:
            wire = "4.0 mm² (12 AWG)"
        elif amps <= 30:
            wire = "6.0 mm² (10 AWG)"
        else:
            wire = "10.0 mm² (8 AWG)"
        
        wire_sizing[load.id] = {
            "wire_size": wire,
            "current_amps": round(amps, 2),
            "voltage_drop_percent": round(amps * 0.05, 2)  # Mock
        }
    
    # Mock breaker selections
    breaker_selections = {}
    for load in request.loads:
        amps = (load.power_watts * load.quantity) / 240
        # Round up to standard sizes
        if amps <= 15:
            breaker = 15
        elif amps <= 20:
            breaker = 20
        elif amps <= 30:
            breaker = 30
        else:
            breaker = 50
        
        breaker_selections[load.id] = {
            "breaker_rating": breaker,
            "poles": 1 if "1PH" in request.service_voltage else 3
        }
    
    # Mock AutoLISP
    autolisp = f'''
; AutoLISP - Generated by MCP Core
; Project: {request.project_name}
; Generated: {datetime.utcnow().isoformat()}

(defun c:DRAW-PANEL ()
  (princ "\\nDrawing panel schedule...")
  (setq panel-name "{request.panels[0].name if request.panels else 'Main Panel'}")
  (setq total-load {total_watts})
  (setq main-breaker {request.panels[0].main_breaker_rating if request.panels else 100})
  ; Panel drawing code here
  (princ "\\nPanel complete.")
  (princ)
)

(defun c:DRAW-CIRCUITS ()
  (princ "\\nDrawing circuits...")
  ; Circuit drawing code
  (princ)
)

(princ "\\nMCP Core AutoLISP loaded. Commands: DRAW-PANEL, DRAW-CIRCUITS")
(princ)
'''
    
    return DesignResultOutput(
        session_id=request.session_id,
        calculations={
            "total_load_watts": total_watts,
            "total_load_amps": round(total_amps, 2),
            "demand_factor": 0.7,
            "calculated_demand_amps": round(total_amps * 0.7, 2)
        },
        wire_sizing=wire_sizing,
        breaker_selections=breaker_selections,
        conduit_sizing={
            "main_conduit": "25mm EMT" if total_amps < 50 else "32mm EMT"
        },
        compliance_report={
            "nec_compliant": True,
            "version": "NEC 2020",
            "notes": ["All circuits properly sized", "GFCI required for wet locations"]
        },
        autolisp_code=autolisp,
        errors=[],
        warnings=["Mock calculation - install dependencies for full pipeline"]
    )

def _convert_to_internal(request: DesignRequestInput):
    """Convert API input to internal DesignRequest format"""
    # This would convert to the internal contracts.py format
    # For now, return as-is since we're using mock
    return request

def _convert_to_output(result) -> DesignResultOutput:
    """Convert internal result to API output format"""
    return DesignResultOutput(
        session_id=result.session_id,
        calculations=result.calculations,
        wire_sizing=result.wire_sizing,
        breaker_selections=result.breaker_selections,
        conduit_sizing=result.conduit_sizing,
        compliance_report=result.compliance_report,
        autolisp_code=result.autolisp_code,
        errors=result.errors,
        warnings=result.warnings
    )

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_PORT", "5001"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
