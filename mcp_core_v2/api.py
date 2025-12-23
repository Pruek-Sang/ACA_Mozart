"""
MCP Core API - FastAPI HTTP Interface

Exposes MCP calculation pipeline via REST API.
This is the MISSING piece for RAG → MCP integration.

Port: 5001 (default)
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

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
    power_factor: Optional[float] = None  # 🆕 PF from RAG adapter (None = use default)

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
    # 🆕 Site context for safety calculations (Derating, kA, N-G Link)
    site_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Site & installation context: distance_to_transformer, installation_area, panel_type, conduit_grouping"
    )

class DesignResultOutput(BaseModel):
    """Output to RAG"""
    session_id: str
    project_name: Optional[str] = None  # 🆕 FIX: Include for formatter
    project_number: Optional[str] = None  # 🆕 FIX: Include for formatter
    calculations: Dict[str, Any] = Field(default_factory=dict)
    wire_sizing: Dict[str, Any] = Field(default_factory=dict)
    breaker_selections: Dict[str, Any] = Field(default_factory=dict)
    conduit_sizing: Dict[str, Any] = Field(default_factory=dict)
    compliance_report: Dict[str, Any] = Field(default_factory=dict)
    autolisp_code: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    standards_markdown: Optional[str] = None
    readable_report: Optional[str] = None  # Human-readable report
    # 🆕 FIX: Include request and summary for RAG formatter
    request: Optional[Dict[str, Any]] = None  # Original request with loads
    summary: Optional[Dict[str, Any]] = None  # Load summary
    grouped_circuits: Optional[List[Dict[str, Any]]] = None  # 🆕 FIX: Circuit grouping from pipeline

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
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

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
        mock_result = _mock_design_result(request)
        # Cache for SLD/BOQ generation
        _cache_session_result(request.session_id, {
            "calculations": mock_result.calculations,
            "breaker_selections": mock_result.breaker_selections,
            "wire_sizing": mock_result.wire_sizing,
            "loads": [l.model_dump() if hasattr(l, 'model_dump') else l.dict() for l in request.loads],
            "project_name": request.project_name
        })
        return mock_result
    
    try:
        # Convert input to internal format
        internal_request = _convert_to_internal(request)
        
        # Run pipeline
        pipeline = get_design_pipeline()
        result = pipeline.execute(internal_request)
        
        # Cache for SLD/BOQ generation
        _cache_session_result(request.session_id, {
            "calculations": result.calculations,
            "breaker_selections": result.breaker_selections,
            "wire_sizing": result.wire_sizing,
            "loads": [l.model_dump() if hasattr(l, 'model_dump') else vars(l) for l in internal_request.loads],
            "project_name": request.project_name
        })
        
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
    total_amps = total_watts / 230  # Thai standard 230V
    
    # Mock wire sizing
    wire_sizing = {}
    for load in request.loads:
        amps = (load.power_watts * load.quantity) / 230  # Thai standard 230V
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
        amps = (load.power_watts * load.quantity) / 230  # Thai standard 230V
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
; Generated: {datetime.now(timezone.utc).isoformat()}

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
    
    # Map voltage strings to VoltageType enum
    # Thai standard (EIT): 230V 1-phase, 400V 3-phase
    # US standard (NEC): 120V/240V 1-phase, 208V/480V 3-phase
    voltage_map = {
        # Thai/IEC Standard
        "230V_1PH": VoltageType.SINGLE_PHASE_230V,
        "400V_3PH": VoltageType.THREE_PHASE_400V,
        # US Standard
        "120V_1PH": VoltageType.SINGLE_PHASE_120V,
        "240V_1PH": VoltageType.SINGLE_PHASE_240V,
        "208V_3PH": VoltageType.THREE_PHASE_208V,
        "480V_3PH": VoltageType.THREE_PHASE_480V,
    }
    
    # Map load_type strings to LoadType enum
    load_type_map = {
        "lighting": LoadType.LIGHTING,
        "receptacle": LoadType.RECEPTACLE,
        "hvac": LoadType.HVAC,
        "motor": LoadType.MOTOR,
        "appliance": LoadType.APPLIANCE,
        "other": LoadType.OTHER,
    }
    
    # Convert loads
    internal_loads = []
    for load in request.loads:
        internal_loads.append(ElectricalLoad(
            id=load.id,
            name=load.name,
            load_type=load_type_map.get(load.load_type.lower(), LoadType.OTHER),
            power_watts=load.power_watts,
            voltage=voltage_map.get(load.voltage, VoltageType.SINGLE_PHASE_240V),
            quantity=load.quantity,
            location=Location(room=load.location.room, floor=load.location.floor or "1"),
            is_continuous=load.is_continuous,
            power_factor=load.power_factor if load.power_factor else 0.85  # 🆕 Use provided PF or default
        ))
    
    # Convert panels  
    internal_panels = []
    for panel in request.panels:
        internal_panels.append(PanelSpecification(
            id=panel.id,
            name=panel.name,
            voltage=voltage_map.get(panel.voltage, VoltageType.SINGLE_PHASE_240V),
            main_breaker_rating=panel.main_breaker_rating,
            number_of_circuits=panel.number_of_circuits,
            location=Location(room=panel.location.room, floor=panel.location.floor or "1"),
            feeds=panel.feeds
        ))
    
    # Determine service voltage
    service_voltage = voltage_map.get(request.service_voltage, VoltageType.SINGLE_PHASE_240V)
    
    return DesignRequest(
        session_id=request.session_id,
        project_name=request.project_name,
        project_number=request.project_number,
        loads=internal_loads,
        panels=internal_panels,
        service_voltage=service_voltage,
        utility_service_size=request.utility_service_size,
        site_context=request.site_context  # 🆕 Pass site_context to pipeline!
    )

def _convert_to_output(result) -> DesignResultOutput:
    """Convert internal result to API output format"""
    # Generate reports
    from core.result_builder import ResultBuilder
    builder = ResultBuilder()
    standards_md = builder.create_standards_markdown(result)
    readable = builder.create_readable_report(result)
    
    # 🆕 FIX: Create summary for RAG formatter
    summary = builder.create_summary(result)
    
    # 🆕 FIX: Convert request to dict for JSON serialization
    request_dict = None
    if result.request:
        request_dict = result.request.model_dump() if hasattr(result.request, 'model_dump') else vars(result.request)
    
    return DesignResultOutput(
        session_id=result.session_id,
        project_name=result.request.project_name if result.request else None,  # 🆕
        project_number=result.request.project_number if result.request else None,  # 🆕
        calculations=result.calculations,
        wire_sizing=result.wire_sizing,
        breaker_selections=result.breaker_selections,
        conduit_sizing=result.conduit_sizing,
        compliance_report=result.compliance_report,
        autolisp_code=result.autolisp_code,
        errors=result.errors,
        warnings=result.warnings,
        standards_markdown=standards_md,
        readable_report=readable,
        request=request_dict,  # 🆕 FIX: Include for formatter
        summary=summary,  # 🆕 FIX: Include for formatter
        grouped_circuits=result.grouped_circuits if hasattr(result, 'grouped_circuits') else []  # 🆕 FIX: Circuit groups
    )

# =============================================================================
# SLD & BOQ Endpoints (Separate from main pipeline - lazy fetch)
# These endpoints generate SLD/BOQ from cached design results
# =============================================================================

# In-memory session cache (simple implementation)
# In production, use Redis or similar
_session_cache: Dict[str, Dict[str, Any]] = {}

def _cache_session_result(session_id: str, result: Dict[str, Any]):
    """Cache design result for SLD/BOQ generation"""
    _session_cache[session_id] = {
        "calculations": result.get("calculations", {}),
        "breaker_selections": result.get("breaker_selections", {}),
        "wire_sizing": result.get("wire_sizing", {}),
        "loads": result.get("loads", []),
        "project_name": result.get("project_name", "Unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/sld/{session_id}")
async def get_sld(session_id: str):
    """
    Generate Single Line Diagram for a session.
    
    Returns JSON/SVG data for frontend to render.
    Uses cached design result from previous /design call.
    """
    try:
        from core.sld_generator import SldGenerator
        
        # Check cache
        if session_id not in _session_cache:
            raise HTTPException(
                status_code=404, 
                detail=f"Session {session_id} not found. Call /api/v1/design first."
            )
        
        cached = _session_cache[session_id]
        
        # Generate SLD
        generator = SldGenerator()
        sld_data = generator.generate_sld_data(
            breaker_selections=cached.get("breaker_selections", {}),
            wire_sizing=cached.get("wire_sizing", {}),
            calculations=cached.get("calculations", {}),
            project_name=cached.get("project_name", "Residential House")
        )
        
        return {
            "session_id": session_id,
            "sld": sld_data,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="SLD Generator not available")
    except Exception as e:
        logger.error(f"SLD generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/boq/{session_id}")
async def get_boq(session_id: str):
    """
    Generate Bill of Quantities for a session.
    
    Returns BOQ with prices from price database.
    Uses cached design result from previous /design call.
    """
    try:
        import os
        from core.boq_service import BoqService
        
        # Check cache
        if session_id not in _session_cache:
            raise HTTPException(
                status_code=404, 
                detail=f"Session {session_id} not found. Call /api/v1/design first."
            )
        
        cached = _session_cache[session_id]
        
        # Find catalog and prices files
        base_path = os.path.dirname(__file__)
        catalog_path = os.path.join(base_path, "catalog", "catalog_rows.csv")
        prices_path = os.path.join(base_path, "catalog", "prices.csv")
        
        # Fallback paths if not found
        if not os.path.exists(catalog_path):
            catalog_path = os.path.join(base_path, "models", "catalog_rows.csv")
        if not os.path.exists(prices_path):
            prices_path = os.path.join(base_path, "models", "prices.csv")
        
        # Generate BOQ
        boq_service = BoqService(catalog_path, prices_path)
        boq_items = boq_service.generate_from_dicts(
            breaker_selections=cached.get("breaker_selections", {}),
            wire_sizing=cached.get("wire_sizing", {}),
            loads=cached.get("loads", [])
        )
        
        # Convert to dict for JSON serialization
        boq_list = []
        for item in boq_items:
            if hasattr(item, 'model_dump'):
                boq_list.append(item.model_dump())
            elif hasattr(item, 'dict'):
                boq_list.append(item.dict())
            else:
                boq_list.append({
                    "item_code": item.item_code,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "source": getattr(item, 'source', 'Unknown')
                })
        
        # Calculate totals
        total = sum(item.get("total_price", 0) for item in boq_list)
        
        return {
            "session_id": session_id,
            "boq": boq_list,
            "total_price_thb": round(total, 2),
            "item_count": len(boq_list),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="BOQ Service not available")
    except Exception as e:
        logger.error(f"BOQ generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete cached session data"""
    if session_id in _session_cache:
        del _session_cache[session_id]
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
async def list_sessions():
    """List all cached sessions (for debugging)"""
    return {
        "sessions": list(_session_cache.keys()),
        "count": len(_session_cache)
    }

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_PORT", "5001"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
