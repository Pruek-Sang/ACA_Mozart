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
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
import uuid

from app.models import (
    QueryRequest, StandardResponse,
    ProjectRequirements, McpSpecResponse,
    RawRetrieveRequest,
    IngestRequest, DeleteRequest
)
from app.service import RagService
from app.config import settings
from core.ingest import IngestionEngine
from core.database import VectorDatabase

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


# === API Routes ===

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Mozart RAG Spec Engine",
        "version": settings.API_VERSION,
        "status": "alive",
        "goddess": "Aura"
    }


@app.post("/api/v1/ask", response_model=StandardResponse)
async def ask_standard(req: QueryRequest):
    """
    Ask a question about electrical standards
    
    This endpoint provides human-readable answers grounded in knowledge base.
    
    Errors:
    - 503: Vector database unavailable
    - 504: LLM timeout
    """
    return await rag_service.process_ask(req)


@app.post("/api/v1/mcp_spec", response_model=McpSpecResponse)
async def mcp_spec(req: ProjectRequirements):
    """
    Generate MCP ProjectInputSpec from human requirements
    
    This is the CORE transformation endpoint.
    
    Errors:
    - 400: Incomplete/invalid requirements
    - 422: LLM output failed validation after retries
    - 503: Vector database unavailable
    - 504: LLM timeout
    
    All requests are logged to trust_log for audit.
    """
    return await rag_service.generate_mcp_spec(req)


@app.post("/api/v1/retrieve_raw")
async def retrieve_raw(req: RawRetrieveRequest):
    """
    Debug endpoint: Raw retrieval without LLM processing
    
    Note: This endpoint is for DEV/AGENT DEBUG only.
    Returns raw vector search results.
    """
    return await rag_service.retrieve_raw(req)


@app.post("/api/v1/ingest")
async def ingest(req: IngestRequest, bg_tasks: BackgroundTasks):
    """
    Ingest a document into vector database
    
    Processing happens in background.
    
    Errors:
    - 400: File not found
    """
    # Pre-check file existence
    if not os.path.exists(req.file_path):
        raise HTTPException(
            status_code=400,
            detail=f"File not found: {req.file_path}"
        )
    
    engine = IngestionEngine()
    db = VectorDatabase()
    
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


@app.post("/api/v1/delete")
async def delete_doc(req: DeleteRequest):
    """
    Delete documents from vector database by source path
    
    Returns number of documents deleted.
    """
    db = VectorDatabase()
    success = db.delete_source(req.source_path)
    
    return {
        "status": "Deleted" if success else "Failed",
        "source_path": req.source_path
    }


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
