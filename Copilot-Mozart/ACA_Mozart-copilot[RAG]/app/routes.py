"""
API Routes - The Divine Endpoints
FastAPI route handlers with proper error handling

Philosophy: The Gateway of Wisdom
- Clear error messages
- Proper HTTP status codes
- Trust logging integration
- Request ID tracking
"""

import os
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import uuid

from app.models import (
    QueryRequest, StandardResponse,
    ProjectRequirements, McpSpecResponse,
    RawRetrieveRequest,
    IngestRequest, DeleteRequest,
    SiteContext,
    SiteContextBatchAnswer,
    SiteContextQuestionnaire,
    build_site_context_questionnaire
)
from app.service import RagService
from app.config import settings
from app.mcp_adapter import McpAdapter, convert_to_mcp
from app.mcp_client import McpClient, McpDesignResponse
from app.session_store import session_store
from core.ingest import IngestionEngine
from core.vector_adapter import get_vector_db
from app.logging_config import setup_logging
from pydantic import BaseModel

# 🆕 Stateful Intelligence imports
try:
    from app.context import session_injector
    from app.context.supabase_client import get_supabase_client, SupabaseHealthCheck
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    session_injector = None
    get_supabase_client = lambda: None

try:
    from app.middleware import rate_limiter, RateLimitExceeded
    RATE_LIMITER_AVAILABLE = True
except ImportError as e:
    RATE_LIMITER_AVAILABLE = False
    rate_limiter = None
    RateLimitExceeded = Exception  # Fallback

try:
    from app.middleware.admin_auth import verify_admin_access
    ADMIN_AUTH_AVAILABLE = True
except ImportError:
    ADMIN_AUTH_AVAILABLE = False
    verify_admin_access = lambda: None

    verify_admin_access = lambda: None

# Initialize Logging Infrastructure (Cloud or Local)
setup_logging()

logger = logging.getLogger("Aura.Routes")


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Mozart RAG Spec Engine - Aura's Divine Creation"
)

# Initialize service
rag_service = RagService()


# Middleware for request ID
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request start and completion with structured data"""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log access details (structured logging will capture extra fields)
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s",
        extra={
            "request_id": getattr(request.state, "request_id", ""),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": process_time
        }
    )
    return response


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standard error response format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# 🆕 Rate Limit Exception Handler
if RATE_LIMITER_AVAILABLE:
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit exceeded - return 429 with retry-after"""
        user_id = getattr(request.state, "user_id", request.client.host if request.client else "unknown")
        logger.warning(f"🚫 Rate limit exceeded for {user_id}: {exc.message}")
        return JSONResponse(
            status_code=429,
            content={
                "error": exc.message,
                "retry_after": exc.retry_after,
                "request_id": getattr(request.state, "request_id", "unknown")
            },
            headers={"Retry-After": str(exc.retry_after)}
        )


# === API Routes ===

@app.get("/")
async def root():
    """
    Health check + Supabase keepalive (prevents Free Tier pause!)
    
    Every call to this endpoint pings Supabase to keep the project active.
    """
    supabase_status = "not_configured"
    
    # 🔌 Keepalive ping - ทุก health check จะ ping Supabase
    if SUPABASE_AVAILABLE:
        client = get_supabase_client()
        if client:
            try:
                # Simple query to keep project alive (SELECT on sessions table)
                client.schema("mozart").table("sessions").select("id").limit(1).execute()
                supabase_status = "connected"
                logger.debug("🔌 Supabase keepalive: ping success")
            except Exception as e:
                supabase_status = "error"
                logger.warning(f"🔌 Supabase keepalive failed: {e}")
    
    return {
        "status": "alive", 
        "version": settings.API_VERSION,
        "supabase": supabase_status,
        "env": settings.APP_ENV
    }


class ClientLogEntry(BaseModel):
    level: str
    message: str
    context: dict = {}


@app.post("/api/v1/logs", tags=["System"])
async def log_client_event(entry: ClientLogEntry):
    """
    Ingest logs from frontend clients.
    These logs are forwarded to Cloud Logging with 'Aura.Client' logger.
    """
    client_logger = logging.getLogger("Aura.Client")
    log_msg = f"[CLIENT] {entry.message}"
    extra = {"json_fields": entry.context}  # 'json_fields' is standard for google-cloud-logging
    
    lvl = entry.level.upper()
    if lvl == "ERROR":
        client_logger.error(log_msg, extra=extra)
    elif lvl == "WARNING":
        client_logger.warning(log_msg, extra=extra)
    elif lvl == "DEBUG":
        client_logger.debug(log_msg, extra=extra)
    else:
        client_logger.info(log_msg, extra=extra)
        
    return {"status": "ok"}



@app.post("/api/v1/ask", response_model=StandardResponse)
async def ask_standard(req: QueryRequest, request: Request, session_id: str = None):
    """
    Ask a question about electrical standards
    
    This endpoint provides human-readable answers grounded in knowledge base.
    Rate limited: 20 requests/minute per user.
    
    🆕 Stateful Intelligence:
    - Pass session_id query param to enable EDIT mode and Audit Trail
    - Example: POST /api/v1/ask?session_id=xxx-xxx-xxx
    
    Errors:
    - 429: Rate limit exceeded
    - 503: Vector database unavailable
    - 504: LLM timeout
    """
    # ⏱️ Rate limit check (20/min for ask)
    if RATE_LIMITER_AVAILABLE and rate_limiter:
        user_id = getattr(request.state, "user_id", request.client.host if request.client else "anonymous")
        rate_limiter.check(user_id, "ask")
        logger.debug(f"⏱️ Rate check passed for {user_id} on /ask")
    
    # 🆕 Pass session_id to enable Stateful Intelligence
    response = await rag_service.process_ask(req, session_id=session_id)
    
    # =========================================================================
    # 🔧 AUTO-SAVE: Persist design result to Supabase
    # [FIX 2026-01-05] Session data was lost on refresh because we never saved!
    # [FIX 2026-01-04] StandardResponse is Pydantic model, NOT dict! Must convert first.
    # =========================================================================
    if SUPABASE_AVAILABLE and session_injector and session_id:
        try:
            # FIX: Convert Pydantic model to dict before using .get()
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else (response.dict() if hasattr(response, 'dict') else response)
            metadata = response_dict.get("metadata", {}) if isinstance(response_dict, dict) else {}
            
            # Check if this is a design response (has display_data or mcp_response)
            if metadata and (metadata.get("display_data") or metadata.get("mcp_response")):
                # Save the entire metadata (display_data, audit_results, sld_data, etc.)
                await session_injector.set_mcp_response(session_id, metadata)
                logger.info(f"✅ Auto-saved design to session {session_id[:8]}...")
        except Exception as e:
            # Don't fail the request if save fails - just log warning
            logger.warning(f"⚠️ Auto-save failed (non-blocking): {e}")
    
    return response



@app.post("/api/v1/mcp_spec", response_model=McpSpecResponse)
async def mcp_spec(req: ProjectRequirements, request: Request):
    """
    Generate MCP ProjectInputSpec from human requirements
    
    This is the CORE transformation endpoint.
    Rate limited: 10 requests/minute per user (expensive LLM call!).
    
    Errors:
    - 400: Incomplete/invalid requirements
    - 422: LLM output failed validation after retries
    - 429: Rate limit exceeded
    - 503: Vector database unavailable
    - 504: LLM timeout
    
    All requests are logged to trust_log for audit.
    """
    # ⏱️ Rate limit check (10/min for design-type endpoints)
    if RATE_LIMITER_AVAILABLE and rate_limiter:
        user_id = getattr(request.state, "user_id", request.client.host if request.client else "anonymous")
        rate_limiter.check(user_id, "design")
        logger.debug(f"⏱️ Rate check passed for {user_id} on /mcp_spec")
    
    return await rag_service.generate_mcp_spec(req)


@app.post("/api/v1/design")
async def design_electrical_system(req: ProjectRequirements, request: Request):
    """
    End-to-end electrical design: Requirements → RAG → MCP → Results
    
    This endpoint chains:
    1. RAG: Generate MCP spec from human requirements
    2. Adapter: Convert RAG output to MCP format
    3. MCP Core: Calculate wire sizing, breakers, etc.
    
    Returns combined result with both spec and calculations.
    Rate limited: 10 requests/minute per user (most expensive endpoint!).
    
    Errors:
    - 400: Invalid/incomplete requirements (including missing site_context!)
    - 422: Spec generation failed
    - 429: Rate limit exceeded
    - 503: MCP Core unavailable
    - 504: Timeout (RAG or MCP)
    """
    # ⏱️ Rate limit check (10/min for design - expensive!)
    if RATE_LIMITER_AVAILABLE and rate_limiter:
        user_id = getattr(request.state, "user_id", request.client.host if request.client else "anonymous")
        rate_limiter.check(user_id, "design")
        logger.info(f"⏱️ Rate check passed for {user_id} on /design")
    # 🆕 Step 0: Validate site_context (REQUIRED for safety!)
    if not req.site_context:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing site_context - required for safe electrical calculations!",
                "required_fields": [
                    "distance_to_transformer: 'less_than_50m' | '50_100m' | 'more_than_100m'",
                    "installation_area: 'indoor' | 'high_temp' | 'outdoor' | 'underground'",
                    "panel_type: 'main' | 'sub'",
                    "conduit_grouping: '1' | '2-3' | '4-6' (optional, default='1')"
                ],
                "message": "กรุณาระบุข้อมูลสภาพแวดล้อมและการติดตั้ง เพื่อความปลอดภัยในการคำนวณ"
            }
        )
    
    # Step 1: Generate spec via RAG
    logger.info(f"Design request for: {req.project_name}")
    spec_response = await rag_service.generate_mcp_spec(req)
    
    # Step 2: Convert to MCP format (with site_context!)
    adapter = McpAdapter()
    mcp_request = adapter.convert(
        spec_response.project_input, 
        req.site_context,
        spec_response.floor_distances  # 🆕 Pass extracted floor distances
    )
    
    # Log any unknown devices
    if adapter.unknown_devices:
        logger.warning(f"Unknown devices in request: {adapter.unknown_devices}")
    
    # Step 3: Call MCP Core
    mcp_client = McpClient()
    
    # Check MCP availability first
    if not await mcp_client.health_check():
        logger.warning("MCP Core not available, returning spec only")
        return {
            "status": "partial",
            "message": "MCP Core not available - returning spec only",
            "spec": spec_response.model_dump(),
            "mcp_request": mcp_request.to_dict(),
            "design_result": None
        }
    
    # Call MCP design
    mcp_response = await mcp_client.design(mcp_request)
    
    if mcp_response.success:
        return {
            "status": "complete",
            "spec": spec_response.model_dump(),
            "design_result": mcp_response.to_dict()
        }
    else:
        # MCP failed but we have the spec
        return {
            "status": "partial",
            "message": f"MCP calculation failed: {mcp_response.error_message}",
            "spec": spec_response.model_dump(),
            "mcp_request": mcp_request.to_dict(),
            "design_result": mcp_response.to_dict()
        }


# =============================================================================
# ADMIN ROUTES (Protected by Header X-Admin-Key)
# =============================================================================

@app.post("/api/v1/admin/retrieve_raw", dependencies=[Depends(verify_admin_access)])
async def retrieve_raw(req: RawRetrieveRequest):
    """
    Debug endpoint: Raw retrieval without LLM processing
    
    [ADMIN ONLY]
    Returns raw vector search results.
    """
    return await rag_service.retrieve_raw(req)


@app.post("/api/v1/admin/ingest", dependencies=[Depends(verify_admin_access)])
async def ingest(req: IngestRequest, bg_tasks: BackgroundTasks):
    """
    Ingest a document into vector database
    
    [ADMIN ONLY]
    Processing happens in background.
    
    Errors:
    - 400: File not found
    - 401: Unauthorized (Missing/Wrong Key)
    """
    # Pre-check file existence
    if not os.path.exists(req.file_path):
        raise HTTPException(
            status_code=400,
            detail=f"File not found: {req.file_path}"
        )
    
    engine = IngestionEngine()
    db = get_vector_db()
    
    def task(path):
        try:
            docs = engine.process_file(path)
            if docs:
                db.upsert(docs)
                logger.info(f"Ingested {len(docs)} documents from {path}")
        except Exception as e:
            logger.error(f"Ingestion failed for {path}: {e}")
    
    bg_tasks.add_task(task, req.file_path)
    
    return {
        "status": "Ingestion queued",
        "path": req.file_path
    }


@app.post("/api/v1/admin/delete", dependencies=[Depends(verify_admin_access)])
async def delete_doc(req: DeleteRequest):
    """
    Delete documents from vector database by source path
    
    [ADMIN ONLY]
    Returns number of documents deleted.
    """
    db = get_vector_db()
    success = db.delete_source(req.source_path)
    
    return {
        "status": "Deleted" if success else "Failed",
        "source_path": req.source_path
    }


# =============================================================================
# Session-Based Site Context Endpoints (Memory + Interactive Questions)
# =============================================================================

@app.post("/api/v1/session/start")
async def start_session(request: Request, project_name: str = None):
    """
    Start a new conversation session.
    
    Args:
        project_name: Optional name for the project (default: บ้านนายสมหญิง)
    
    Returns session_id for subsequent calls.
    Session remembers user's answers across turns.
    """
    user_id = getattr(request.state, "user_id", None)
    session = session_store.create_session(user_id=user_id, project_name=project_name)
    
    # Return questionnaire immediately
    questionnaire = build_site_context_questionnaire(session.session_id)
    
    return {
        "session_id": session.session_id,
        "project_name": project_name or "บ้านนายสมหญิง",
        "message": "Session created. Please answer site context questions.",
        "site_context": questionnaire.model_dump()
    }


# =============================================================================
# 🔧 FIX: Route Order - Static routes MUST come before dynamic routes!
# FastAPI matches routes in order, so /session/list must be before /session/{id}
# Otherwise "list" gets matched as a session_id and returns 404
# =============================================================================

@app.get("/api/v1/session/list")
async def list_projects(request: Request):
    """
    List all projects for the current user (max 10).
    
    Returns list of session summaries for project selector UI.
    """
    user_id = getattr(request.state, "user_id", None) or (request.client.host if request.client else None)
    
    if not SUPABASE_AVAILABLE or not session_injector:
        # Fallback to in-memory
        active = session_store.list_active_sessions()
        return {
            "projects": [
                {"session_id": sid, "project_name": "In-Memory Session"}
                for sid in active[:10]
            ],
            "storage": "memory"
        }
    
    try:
        # FIX: Validate user_id is UUID before querying Supabase
        # IP addresses like "169.254.169.126" are not valid UUIDs
        import re
        is_valid_uuid = user_id and re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', str(user_id), re.I)
        if not is_valid_uuid:
            logger.warning(f"⚠️ Invalid user_id '{user_id}' (not UUID), returning empty project list")
            return {"projects": [], "storage": "supabase", "note": "no_valid_user_id"}
        
        sessions = await session_injector.load_by_user(user_id, limit=10)
        return {
            "projects": [
                {
                    "session_id": s.id,
                    "project_name": s.project_name,
                    "stage": s.stage,
                    "updated_at": s.updated_at,
                    "loads_count": len(s.loads) if s.loads else 0
                }
                for s in sessions
            ],
            "storage": "supabase"
        }
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return {"projects": [], "error": str(e)}


# =============================================================================
# 🆕 GET SESSION DATA - Load saved design for restoration after refresh
# [FIX 2026-01-05] Frontend needs to restore saved design on page refresh
# =============================================================================
@app.get("/api/v1/session/{session_id}/data")
async def get_session_data(session_id: str, request: Request):
    """
    Load saved design data for a session.
    
    Used by Frontend to restore session state after page refresh.
    Returns rooms, loads, site_context, messages, and MCP response.
    
    Errors:
    - 404: Session not found or storage unavailable
    """
    if not SUPABASE_AVAILABLE or not session_injector:
        raise HTTPException(
            status_code=503,
            detail="Session storage not available"
        )
    
    try:
        session = await session_injector.load(session_id)
        
        if not session:
            raise HTTPException(404, f"Session not found: {session_id[:8]}...")
        
        logger.info(f"📂 Loaded session data for {session_id[:8]}... ({len(session.loads or [])} loads)")
        
        return {
            "session_id": session_id,
            "project_name": session.project_name,
            "stage": session.stage,
            "rooms": session.rooms or [],
            "loads": session.loads or [],
            "site_context": session.site_context or {},
            "mcp_response": session.mcp_response,
            "messages": session.messages or [],
            "updated_at": session.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load session data: {e}")
        raise HTTPException(500, f"Failed to load session: {str(e)}")

@app.get("/api/v1/session/{session_id}/site", response_model=SiteContextQuestionnaire)
async def get_site_context_questions(session_id: str):
    """
    Get site context questionnaire for session
    
    Shows which questions are answered and which are pending.
    Use this to display form/radio buttons to user.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found or expired: {session_id}")
    
    # Get current site_context from partial_requirements
    current_site = session.partial_requirements.get("site_context", {})
    
    return build_site_context_questionnaire(session_id, current_site)


@app.post("/api/v1/session/{session_id}/site")
async def update_site_context(session_id: str, answers: SiteContextBatchAnswer):
    """
    Update site context with user's answers
    
    Accepts batch of answers (can answer multiple questions at once).
    Values are REMEMBERED for this session.
    
    Example:
        POST /api/v1/session/{session_id}/site
        {
            "answers": [
                {"field_name": "distance_to_transformer", "value": "less_than_50m"},
                {"field_name": "installation_area", "value": "indoor"}
            ]
        }
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found or expired: {session_id}")
    
    # Get or create site_context in partial_requirements
    if "site_context" not in session.partial_requirements:
        session.partial_requirements["site_context"] = {}
    
    site_ctx = session.partial_requirements["site_context"]
    
    # Apply answers
    for ans in answers.answers:
        site_ctx[ans.field_name] = ans.value
        logger.info(f"Session {session_id}: set {ans.field_name} = {ans.value}")
    
    # Return updated questionnaire
    questionnaire = build_site_context_questionnaire(session_id, site_ctx)
    
    return {
        "status": "updated",
        "site_context": questionnaire.model_dump()
    }


@app.get("/api/v1/session/{session_id}")
async def get_session_status(session_id: str):
    """
    Get full session status including all accumulated data
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found or expired: {session_id}")
    
    site_ctx = session.partial_requirements.get("site_context", {})
    questionnaire = build_site_context_questionnaire(session_id, site_ctx)
    
    return {
        "session_id": session_id,
        "stage": session.stage,
        "partial_requirements": session.partial_requirements,
        "site_context_status": questionnaire.model_dump(),
        "current_spec": session.current_spec,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }


@app.post("/api/v1/session/{session_id}/design")
async def design_with_session(session_id: str, req: ProjectRequirements):
    """
    Design electrical system using session's remembered site_context
    
    If site_context not in request, uses values stored in session.
    This allows user to answer site questions ONCE and reuse across designs.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found or expired: {session_id}")
    
    # Merge site_context: request takes priority, fallback to session
    session_site = session.partial_requirements.get("site_context", {})
    
    if req.site_context:
        # Use request's site_context (explicit)
        final_site_context = req.site_context
    elif session_site:
        # Use session's remembered site_context
        final_site_context = SiteContext(
            distance_to_transformer=session_site.get("distance_to_transformer", "more_than_100m"),
            installation_area=session_site.get("installation_area", "indoor"),
            panel_type=session_site.get("panel_type", "main"),
            conduit_grouping=session_site.get("conduit_grouping", "1")
        )
        logger.info(f"Using session's remembered site_context for {session_id}")
    else:
        # Neither provided - return questionnaire
        questionnaire = build_site_context_questionnaire(session_id, {})
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Site context not provided",
                "message": "กรุณาตอบคำถามเกี่ยวกับสถานที่ติดตั้งก่อน",
                "questionnaire": questionnaire.model_dump()
            }
        )
    
    # Override request's site_context with final value
    req.site_context = final_site_context
    
    # Now proceed with design (same as /api/v1/design)
    logger.info(f"Session {session_id}: Design request for {req.project_name}")
    spec_response = await rag_service.generate_mcp_spec(req)
    
    # Store spec in session
    session_store.set_spec(session_id, spec_response.model_dump())
    
    # Convert to MCP format
    adapter = McpAdapter()
    mcp_request = adapter.convert(spec_response.project_input, req.site_context)
    
    # Call MCP Core
    mcp_client = McpClient()
    
    if not await mcp_client.health_check():
        logger.warning("MCP Core not available")
        return {
            "status": "partial",
            "session_id": session_id,
            "message": "MCP Core not available - returning spec only",
            "spec": spec_response.model_dump(),
            "design_result": None
        }
    
    mcp_response = await mcp_client.design(mcp_request)
    
    if mcp_response.success:
        session_store.complete_session(session_id, mcp_response.to_dict())
        return {
            "status": "complete",
            "session_id": session_id,
            "spec": spec_response.model_dump(),
            "design_result": mcp_response.to_dict()
        }
    else:
        return {
            "status": "partial",
            "session_id": session_id,
            "message": f"MCP calculation failed: {mcp_response.error_message}",
            "spec": spec_response.model_dump(),
            "design_result": mcp_response.to_dict()
        }


# 🔧 NOTE: /session/list route moved to Line ~410 to fix route matching order


@app.delete("/api/v1/session/{session_id}")
async def delete_session(session_id: str, confirm: str = None):
    """
    Delete a session and forget all remembered values.
    
    ⚠️ REQUIRES confirmation: pass ?confirm=CONFIRM to actually delete.
    
    Example: DELETE /api/v1/session/xxx-xxx?confirm=CONFIRM
    """
    # Check CONFIRM requirement
    if confirm != "CONFIRM":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Deletion requires confirmation",
                "message": "กรุณาพิมพ์ 'CONFIRM' เพื่อยืนยันการลบโปรเจกต์",
                "required": "?confirm=CONFIRM"
            }
        )
    
    # Try Supabase first
    if SUPABASE_AVAILABLE and session_injector:
        try:
            success = await session_injector.delete(session_id)
            if success:
                logger.info(f"Deleted session via Supabase: {session_id}")
                return {
                    "status": "deleted",
                    "session_id": session_id,
                    "message": "โปรเจกต์ถูกลบแล้ว"
                }
        except Exception as e:
            logger.error(f"Failed to delete session via Supabase: {e}")
    
    # Fallback to in-memory
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found: {session_id}")
    
    session_store.delete_session(session_id)
    return {
        "status": "deleted",
        "session_id": session_id,
        "message": "โปรเจกต์ถูกลบแล้ว (in-memory)"
    }


# =============================================================================
# MCP Protocol Endpoints
# =============================================================================

@app.get("/mcp/manifest")
async def mcp_manifest():
    """
    MCP tool manifest
    
    This endpoint declares available tools for MCP protocol.
    """
    return {
        "name": "ee_standard_expert",
        "description": "RAG Service for QA and MCP Spec Generation (Aura v3.2)",
        "version": settings.API_VERSION,
        "tools": [
            {
                "name": "ask_standard",
                "description": "Ask electrical standard questions (Human readable answers)",
                "input_schema": QueryRequest.model_json_schema()
            },
            {
                "name": "generate_mcp_spec",
                "description": "Generate MCP Project Input JSON from requirements (No calculations, semantic mapping only)",
                "input_schema": ProjectRequirements.model_json_schema()
            }
        ]
    }


# === Admin/Debug Endpoints ===

@app.get("/api/v1/knowledge/groups")
async def list_knowledge_groups():
    """List available knowledge groups"""
    groups = rag_service.knowledge.list_groups()
    return {"groups": groups}


@app.get("/api/v1/knowledge/docs/{group}")
async def list_knowledge_docs(group: str):
    """List documents in a knowledge group"""
    docs = rag_service.knowledge.list_docs(group)
    return {
        "group": group,
        "count": len(docs),
        "docs": [doc.model_dump() for doc in docs]
    }


@app.get("/api/v1/trust_log/recent")
async def get_recent_trust_logs(limit: int = 10):
    """Get recent trust log records (today)"""
    from app.trust_log import trust_logger
    records = trust_logger.read_records(limit=limit)
    return {
        "count": len(records),
        "records": records
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )
