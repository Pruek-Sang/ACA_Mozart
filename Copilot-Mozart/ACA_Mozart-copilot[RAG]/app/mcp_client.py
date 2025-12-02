"""
MCP Client - HTTP Client for MCP Core API

Philosophy:
- Simple and focused: just call MCP, handle errors gracefully
- Timeout protection: don't wait forever
- Logging: track what we send and receive

Port: MCP Core runs on 5001 (not 8080, that's RAG!)
"""

import logging
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
    
    # Calculation results (from MCP DesignResult)
    calculations: Optional[Dict[str, Any]] = None
    wire_sizing: Optional[Dict[str, Any]] = None
    breaker_selections: Optional[Dict[str, Any]] = None
    conduit_sizing: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    autolisp_code: Optional[str] = None
    
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
            "calculations": self.calculations,
            "wire_sizing": self.wire_sizing,
            "breaker_selections": self.breaker_selections,
            "conduit_sizing": self.conduit_sizing,
            "compliance_report": self.compliance_report,
            "autolisp_code": self.autolisp_code,
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
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    return McpDesignResponse(
                        success=True,
                        session_id=data.get("session_id"),
                        calculations=data.get("calculations"),
                        wire_sizing=data.get("wire_sizing"),
                        breaker_selections=data.get("breaker_selections"),
                        conduit_sizing=data.get("conduit_sizing"),
                        compliance_report=data.get("compliance_report"),
                        autolisp_code=data.get("autolisp_code"),
                        errors=data.get("errors", []),
                        warnings=data.get("warnings", [])
                    )
                else:
                    # MCP returned an error
                    logger.error(f"MCP returned {response.status_code}: {response.text}")
                    return McpDesignResponse(
                        success=False,
                        error_message=f"MCP returned HTTP {response.status_code}",
                        http_status=response.status_code,
                        errors=[response.text[:500]]  # Truncate long errors
                    )
        
        except httpx.TimeoutException:
            logger.error(f"MCP timeout after {self.timeout}s")
            return McpDesignResponse(
                success=False,
                error_message=f"MCP Core timeout after {self.timeout}s",
                errors=["Timeout waiting for MCP Core response"]
            )
        
        except httpx.ConnectError:
            logger.error(f"Cannot connect to MCP Core at {self.base_url}")
            return McpDesignResponse(
                success=False,
                error_message=f"Cannot connect to MCP Core at {self.base_url}",
                errors=["MCP Core is not running or unreachable"]
            )
        
        except Exception as e:
            logger.error(f"MCP call failed: {e}", exc_info=True)
            return McpDesignResponse(
                success=False,
                error_message=str(e),
                errors=[f"Unexpected error: {str(e)}"]
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
