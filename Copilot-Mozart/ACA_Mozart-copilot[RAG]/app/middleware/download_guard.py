"""
Download Protection Module
==========================
Protect premium Excel downloads from unauthorized access.

📋 PURPOSE:
-----------
ป้องกันการ download ข้อมูลโดยไม่ได้รับอนุญาต

🎯 APPROACHES (Choose one):
---------------------------

1. WATERMARK APPROACH:
   - ใส่ watermark ใน Excel (user email, timestamp)
   - ไม่ block download แต่ track ว่าใครเอาไป
   - Pros: Simple, non-intrusive
   - Cons: ไม่ได้ป้องกันจริงๆ

2. TOKEN-BASED APPROACH:
   - Generate one-time download token
   - Token หมดอายุหลังใช้ 1 ครั้ง หรือ 5 นาที
   - Pros: Secure, audit trail
   - Cons: Complex, need backend changes

3. RATE LIMIT APPROACH:
   - จำกัด download ต่อ user ต่อวัน (e.g., 10 downloads/day)
   - Pros: ป้องกัน bulk download
   - Cons: ไม่ได้ป้องกัน legitimate users

🔧 COMPONENTS TO IMPLEMENT:
---------------------------

Frontend (ResultViewer.tsx):
- watermarkExcel(workbook, userEmail, timestamp)
- requestDownloadToken() -> token
- downloadWithToken(token)

Backend (app/routes.py):
- POST /api/v1/download/token - Generate download token
- GET /api/v1/download/{token} - Validate and serve file
- Track download count per user

Database (Supabase):
- download_tokens table (token, user_id, created_at, used_at, expires_at)
- download_logs table (user_id, file_type, timestamp)

📦 FILES TO CREATE:
-------------------
1. app/middleware/download_guard.py - Token validation middleware
2. frontend/src/lib/downloadProtection.ts - Frontend helper
3. app/routes_download.py - Download endpoints

📝 INTEGRATION POINTS:
----------------------
- ResultViewer.tsx: handleDownloadExcel() - add token request
- app/routes.py: Add download routes
- Supabase: Create tables for tokens and logs

⚠️ SECURITY CONSIDERATIONS:
---------------------------
- Tokens should be UUID4, not sequential
- Tokens expire after 5 minutes OR single use
- Log all download attempts (success and failure)
- Rate limit: 10 downloads per user per hour

Author: [TO BE IMPLEMENTED]
Date: [TO BE IMPLEMENTED]
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class DownloadToken:
    """Represents a one-time download token."""
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    used: bool = False
    file_type: str = "excel"


class DownloadGuard:
    """
    Middleware for protecting premium downloads.
    
    Usage:
        guard = DownloadGuard(token_ttl_minutes=5)
        token = guard.create_token(user_id="user123")
        is_valid = guard.validate_token(token)
        guard.mark_used(token)
    """
    
    # ════════════════════════════════════════════════════════════════════════
    # CONFIGURABLE CONSTANTS
    # ════════════════════════════════════════════════════════════════════════
    
    DEFAULT_TOKEN_TTL_MINUTES = 5
    DEFAULT_MAX_DOWNLOADS_PER_HOUR = 10
    
    # ════════════════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ════════════════════════════════════════════════════════════════════════
    
    def __init__(
        self, 
        token_ttl_minutes: int = DEFAULT_TOKEN_TTL_MINUTES,
        max_downloads_per_hour: int = DEFAULT_MAX_DOWNLOADS_PER_HOUR
    ):
        """
        Initialize Download Guard.
        
        Args:
            token_ttl_minutes: Token expiration time in minutes
            max_downloads_per_hour: Max downloads allowed per user per hour
        """
        self.token_ttl = token_ttl_minutes
        self.max_downloads = max_downloads_per_hour
        # TODO: Connect to Supabase for persistent storage
        self._tokens: Dict[str, DownloadToken] = {}  # In-memory fallback
        logger.info(f"DownloadGuard initialized: ttl={token_ttl_minutes}min, max={max_downloads_per_hour}/hr")
    
    # ════════════════════════════════════════════════════════════════════════
    # TOKEN MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════
    
    def create_token(self, user_id: str, file_type: str = "excel") -> str:
        """
        Create a one-time download token for a user.
        
        TODO: Implement
        1. Generate UUID4 token
        2. Set expiration time (now + TTL)
        3. Store in Supabase (or in-memory fallback)
        4. Return token string
        """
        raise NotImplementedError("TO BE IMPLEMENTED")
    
    def validate_token(self, token: str) -> bool:
        """
        Check if token is valid (exists, not expired, not used).
        
        TODO: Implement
        1. Lookup token in storage
        2. Check if expired
        3. Check if already used
        4. Return True/False
        """
        raise NotImplementedError("TO BE IMPLEMENTED")
    
    def mark_used(self, token: str) -> bool:
        """
        Mark token as used (one-time use).
        
        TODO: Implement
        1. Update token record in storage
        2. Return success/failure
        """
        raise NotImplementedError("TO BE IMPLEMENTED")
    
    # ════════════════════════════════════════════════════════════════════════
    # RATE LIMITING
    # ════════════════════════════════════════════════════════════════════════
    
    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded download rate limit.
        
        TODO: Implement
        1. Count downloads in last hour for user
        2. Return True if under limit, False if exceeded
        """
        raise NotImplementedError("TO BE IMPLEMENTED")
    
    def log_download(self, user_id: str, file_type: str, success: bool) -> None:
        """
        Log download attempt for audit trail.
        
        TODO: Implement
        1. Insert into download_logs table
        2. Include timestamp, success status
        """
        raise NotImplementedError("TO BE IMPLEMENTED")
    
    # ════════════════════════════════════════════════════════════════════════
    # WATERMARK (Optional approach)
    # ════════════════════════════════════════════════════════════════════════
    
    def generate_watermark(self, user_email: str) -> Dict[str, Any]:
        """
        Generate watermark info to embed in Excel.
        
        Returns:
            Dict with: user_email, timestamp, hash
        """
        raise NotImplementedError("TO BE IMPLEMENTED")


# ════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ════════════════════════════════════════════════════════════════════════════

def get_download_guard() -> DownloadGuard:
    """
    Factory function to get DownloadGuard instance.
    
    Usage in routes.py:
        from middleware.download_guard import get_download_guard
        
        guard = get_download_guard()
        token = guard.create_token(user_id=current_user.id)
    """
    return DownloadGuard()
