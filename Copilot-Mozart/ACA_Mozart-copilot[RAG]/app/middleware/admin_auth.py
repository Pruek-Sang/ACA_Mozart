"""
Admin Authorization Middleware
Protects /api/v1/admin/* endpoints from unauthorized access.

Philosophy:
- Simple yet effective security
- Relies on ADMIN_API_KEY environment variable
- Returns 401 Unauthorized if key is invalid or missing
"""

import os
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("Aura.AdminAuth")

# Default key for development (Override in production!)
DEFAULT_ADMIN_KEY = "REDACTED_ADMIN_KEY"

def get_admin_key() -> str:
    """Get admin key from environment or default"""
    return os.getenv("ADMIN_API_KEY", DEFAULT_ADMIN_KEY)

async def verify_admin_access(request: Request):
    """
    Dependency for protecting admin routes.
    
    Checks for 'X-Admin-Key' header.
    Can be used as: dependencies=[Depends(verify_admin_access)]
    """
    # 1. Check if it's an admin route (Double safety)
    if "/api/v1/admin/" not in request.url.path:
        return  # Pass through non-admin routes

    # 2. Get Header
    request_key = request.headers.get("X-Admin-Key")
    
    # 3. Verify
    expected_key = get_admin_key()
    
    if not request_key:
        logger.warning(f"Admin access attempt without key: {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Missing 'X-Admin-Key' header"
        )
        
    if request_key != expected_key:
        logger.warning(f"Admin access attempt with invalid key: {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Invalid Admin Key"
        )
        
    # Access Granted
    logger.info(f"Admin access granted to {request.client.host} for {request.url.path}")
