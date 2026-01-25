"""
MCP Client - HTTP Client for MCP Core API

Philosophy:
- Simple and focused: just call MCP, handle errors gracefully
- Timeout protection: don't wait forever
- Logging: track what we send and receive

Port: MCP Core runs on 5001 (not 8080, that's RAG!)
"""

import logging
import asyncio
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.mcp_adapter import McpDesignRequest
from app.config import settings

logger = logging.getLogger("Aura.McpClient")


# =============================================================================
# Configuration (from settings)
# =============================================================================

MCP_DESIGN_ENDPOINT = "/api/v1/design"  # MCP design endpoint


# =============================================================================
# Response Wrapper
# =============================================================================

@dataclass
class McpDesignResponse:
    """
    Response from MCP Core
    
    Contains all calculation results from MCP pipeline
    """
    success: bool
    session_id: Optional[str] = None
    
    # Project info (from MCP DesignResult)
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    
    # Calculation results (from MCP DesignResult)
    calculations: Optional[Dict[str, Any]] = None
    wire_sizing: Optional[Dict[str, Any]] = None
    breaker_selections: Optional[Dict[str, Any]] = None
    conduit_sizing: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    autolisp_code: Optional[str] = None
    readable_report: Optional[str] = None  # MCP human-readable report (Markdown)
    standards_markdown: Optional[str] = None  # Design standards summary
    
    # 🆕 FIX: Include request and summary for formatter
    request: Optional[Dict[str, Any]] = None  # Original request with loads
    summary: Optional[Dict[str, Any]] = None  # Load summary
    grouped_circuits: Optional[list] = None    # 🆕 FIX: Circuit grouping from MCP Core
    
    # Errors/warnings from MCP
    errors: Optional[list] = None
    warnings: Optional[list] = None
    
    # HTTP-level error (if failed)
    error_message: Optional[str] = None
    http_status: Optional[int] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "success": self.success,
            "session_id": self.session_id,
            "project_name": self.project_name,
            "project_number": self.project_number,
            "calculations": self.calculations,
            "wire_sizing": self.wire_sizing,
            "breaker_selections": self.breaker_selections,
            "conduit_sizing": self.conduit_sizing,
            "compliance_report": self.compliance_report,
            "autolisp_code": self.autolisp_code,
            "readable_report": self.readable_report,
            "standards_markdown": self.standards_markdown,
            "request": self.request,  # 🆕 FIX: Include for formatter
            "summary": self.summary,  # 🆕 FIX: Include for formatter
            "grouped_circuits": self.grouped_circuits,  # 🆕 FIX: Circuit groups for formatter
            "errors": self.errors,
            "warnings": self.warnings,
            "error_message": self.error_message
        }


# =============================================================================
# MCP Client
# =============================================================================

class McpClient:
    """
    HTTP Client for MCP Core
    
    Usage:
        client = McpClient()
        
        # Check if MCP is available
        if await client.health_check():
            # Call design
            response = await client.design(mcp_request)
            if response.success:
                print(response.wire_sizing)
    """
    
    def __init__(
        self, 
        base_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = (base_url or settings.MCP_CORE_URL).rstrip("/")
        self.timeout = timeout or settings.MCP_TIMEOUT
    
    async def health_check(self) -> bool:
        """
        Check if MCP Core is available
        
        Returns: True if MCP responds, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"MCP health check failed: {e}")
            return False
    
    async def design(self, request: McpDesignRequest) -> McpDesignResponse:
        """
        Call MCP Core design endpoint
        
        Args:
            request: McpDesignRequest (converted from RAG spec)
            
        Returns:
            McpDesignResponse with calculation results or error
        """
        url = f"{self.base_url}{MCP_DESIGN_ENDPOINT}"
        payload = request.to_dict()
        
        logger.info(f"Calling MCP Core: {url}")
        logger.debug(f"Payload: {payload}")
        
        # 🆕 Retry logic: 3 attempts with exponential backoff
        max_retries = 3
        retry_delays = [1, 2, 4]  # seconds
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # [CP-3PH-TRACE] Log what we receive from MCP API
                        logger.info(f"[CP-3PH-CLIENT] Received from MCP Core API:")
                        logger.info(f"[CP-3PH-CLIENT]   data keys: {list(data.keys())}")
                        if data.get('calculations'):
                            logger.info(f"[CP-3PH-CLIENT]   calculations.three_phase: {data['calculations'].get('three_phase', 'NOT FOUND')}")
                        if data.get('grouped_circuits'):
                            sample = data['grouped_circuits'][0] if data['grouped_circuits'] else {}
                            logger.info(f"[CP-3PH-CLIENT]   grouped_circuits[0].assigned_phase: {sample.get('assigned_phase', 'NOT FOUND')}")
                        
                        return McpDesignResponse(
                            success=True,
                            session_id=data.get("session_id"),
                            project_name=data.get("project_name"),  # 🆕 FIX
                            project_number=data.get("project_number"),  # 🆕 FIX
                            calculations=data.get("calculations"),
                            wire_sizing=data.get("wire_sizing"),
                            breaker_selections=data.get("breaker_selections"),
                            conduit_sizing=data.get("conduit_sizing"),
                            compliance_report=data.get("compliance_report"),
                            autolisp_code=data.get("autolisp_code"),
                            readable_report=data.get("readable_report"),
                            standards_markdown=data.get("standards_markdown"),
                            request=data.get("request"),  # 🆕 FIX: Include for formatter
                            summary=data.get("summary"),  # 🆕 FIX: Include for formatter
                            grouped_circuits=data.get("grouped_circuits"),  # 🆕 FIX: Circuit groups
                            errors=data.get("errors", []),
                            warnings=data.get("warnings", [])
                        )
                    else:
                        # MCP returned an error - don't retry
                        logger.error(f"MCP returned {response.status_code}: {response.text}")
                        return McpDesignResponse(
                            success=False,
                            error_message=f"MCP returned HTTP {response.status_code}",
                            http_status=response.status_code,
                            errors=[response.text[:500]]  # Truncate long errors
                        )
            
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(f"MCP call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"MCP call failed after {max_retries} attempts: {e}")
            
            except Exception as e:
                logger.error(f"MCP call failed: {e}", exc_info=True)
                return McpDesignResponse(
                    success=False,
                    error_message=str(e),
                    errors=[f"Unexpected error: {str(e)}"]
                )
        
        # All retries exhausted
        error_type = "Timeout" if isinstance(last_error, httpx.TimeoutException) else "Connection"
        return McpDesignResponse(
            success=False,
            error_message=f"MCP Core {error_type} after {max_retries} retries",
            errors=[f"{error_type} waiting for MCP Core response (tried {max_retries} times)"]
        )


# =============================================================================
# Convenience Functions
# =============================================================================

async def call_mcp_design(request: McpDesignRequest) -> McpDesignResponse:
    """
    Convenience function for one-off MCP call
    
    Usage:
        from app.mcp_client import call_mcp_design
        response = await call_mcp_design(mcp_request)
    """
    client = McpClient()
    return await client.design(request)


async def is_mcp_available() -> bool:
    """Check if MCP Core is available"""
    client = McpClient()
    return await client.health_check()


# =============================================================================
# Sync version (for testing without async)
# =============================================================================

def call_mcp_design_sync(request: McpDesignRequest) -> McpDesignResponse:
    """
    Synchronous version for testing
    
    WARNING: Use async version in production!
    """
    import asyncio
    return asyncio.run(call_mcp_design(request))
