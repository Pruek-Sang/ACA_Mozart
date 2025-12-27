"""
Rate Limiter - Protect Expensive API Calls

Philosophy:
- RAG calls use LLM = expensive!
- Prevent abuse and cost explosion
- In-memory for simplicity (can upgrade to Redis later)

Usage:
    from app.middleware import rate_limiter, RateLimitExceeded
    
    # Check rate limit
    try:
        rate_limiter.check("user_123", "design")
    except RateLimitExceeded as e:
        return {"error": str(e), "retry_after": e.retry_after}
    
    # Use as decorator
    @rate_limiter.limit("design")
    async def design_endpoint(user_id: str):
        ...
"""

import time
import logging
from typing import Dict, Optional, Callable
from collections import defaultdict
from functools import wraps
from dataclasses import dataclass
from starlette.requests import Request

logger = logging.getLogger("Aura.RateLimiter")


def get_real_ip(request: Request) -> str:
    """
    Extract real client IP from request, handling Load Balancer/Proxy scenarios.
    
    Priority:
    1. X-Forwarded-For header (first IP in chain)
    2. X-Real-IP header
    3. Direct client.host (fallback)
    
    Args:
        request: FastAPI/Starlette Request object
        
    Returns:
        Client IP address string
    """
    # X-Forwarded-For: client, proxy1, proxy2, ...
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    if x_forwarded_for:
        # First IP is the original client
        client_ip = x_forwarded_for.split(",")[0].strip()
        if client_ip:
            return client_ip
    
    # X-Real-IP is sometimes set by proxies
    x_real_ip = request.headers.get("X-Real-IP", "")
    if x_real_ip:
        return x_real_ip.strip()
    
    # Fallback to direct connection (may be Load Balancer IP)
    return request.client.host if request.client else "unknown"


class RateLimitExceeded(Exception):
    """
    Raised when rate limit is exceeded.
    
    Attributes:
        message: Error message
        retry_after: Seconds until limit resets
    """
    
    def __init__(self, message: str, retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int  # Max requests
    window: int    # Time window in seconds
    
    def __str__(self) -> str:
        return f"{self.requests} requests per {self.window}s"


# Default rate limits for different endpoints
# NOTE: Limits are set for ~20 concurrent users behind Cloud Run Load Balancer
# Until we properly extract X-Forwarded-For, all users share these limits!
DEFAULT_LIMITS: Dict[str, RateLimit] = {
    "design": RateLimit(200, 60),       # 200 designs per minute (~10 per user × 20 users)
    "ask": RateLimit(400, 60),          # 400 questions per minute (~20 per user × 20 users)
    "chat": RateLimit(600, 60),         # 600 chat messages per minute
    "session": RateLimit(1000, 60),     # 1000 session ops per minute
    "project": RateLimit(600, 60),      # 600 project ops per minute
    "health": RateLimit(2000, 60),      # 2000 health checks per minute
    "default": RateLimit(600, 60),      # Default: 600 per minute
}


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    
    Thread-safe for single-process deployments.
    For multi-instance, upgrade to Redis-based implementation.
    """
    
    def __init__(self, limits: Optional[Dict[str, RateLimit]] = None):
        """
        Initialize rate limiter.
        
        Args:
            limits: Custom rate limits by endpoint type
        """
        self.limits = limits or DEFAULT_LIMITS.copy()
        
        # Storage: {user_id: {endpoint: [timestamp, timestamp, ...]}}
        self._requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        
        logger.info(f"RateLimiter initialized with limits: {self.limits}")
    
    def _get_limit(self, endpoint: str) -> RateLimit:
        """Get rate limit for endpoint."""
        return self.limits.get(endpoint, self.limits.get("default", RateLimit(30, 60)))
    
    def _clean_old_requests(self, timestamps: list, window: int) -> list:
        """Remove timestamps outside the window."""
        now = time.time()
        cutoff = now - window
        return [ts for ts in timestamps if ts > cutoff]
    
    def check(
        self,
        user_id: str,
        endpoint: str = "default",
        cost: int = 1,
    ) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            user_id: User identifier (IP, user ID, API key, etc.)
            endpoint: Endpoint type for limit lookup
            cost: Request cost (for weighted limiting)
            
        Returns:
            True if allowed
            
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        limit = self._get_limit(endpoint)
        now = time.time()
        
        # Get and clean user's request history
        user_requests = self._requests[user_id]
        timestamps = self._clean_old_requests(user_requests.get(endpoint, []), limit.window)
        
        # Calculate effective count (with cost)
        effective_count = len(timestamps) + cost
        
        if effective_count > limit.requests:
            # Calculate retry_after
            if timestamps:
                oldest = min(timestamps)
                retry_after = int(limit.window - (now - oldest)) + 1
            else:
                retry_after = limit.window
            
            logger.warning(
                f"Rate limit exceeded for {user_id} on {endpoint}: "
                f"{len(timestamps)}/{limit.requests} requests"
            )
            
            raise RateLimitExceeded(
                f"Rate limit exceeded: {limit}. Please try again later.",
                retry_after=max(1, retry_after),
            )
        
        # Record this request
        timestamps.append(now)
        user_requests[endpoint] = timestamps
        
        return True
    
    def get_remaining(self, user_id: str, endpoint: str = "default") -> Dict[str, int]:
        """
        Get remaining requests for user.
        
        Returns:
            Dict with 'remaining', 'limit', and 'reset' (seconds)
        """
        limit = self._get_limit(endpoint)
        now = time.time()
        
        user_requests = self._requests.get(user_id, {})
        timestamps = self._clean_old_requests(user_requests.get(endpoint, []), limit.window)
        
        remaining = max(0, limit.requests - len(timestamps))
        
        # Calculate reset time
        if timestamps:
            oldest = min(timestamps)
            reset = int(limit.window - (now - oldest))
        else:
            reset = limit.window
        
        return {
            "remaining": remaining,
            "limit": limit.requests,
            "reset": max(0, reset),
        }
    
    def reset(self, user_id: str, endpoint: Optional[str] = None):
        """
        Reset rate limit for a user.
        
        Args:
            user_id: User identifier
            endpoint: Optional specific endpoint to reset (None = all)
        """
        if user_id in self._requests:
            if endpoint:
                self._requests[user_id][endpoint] = []
            else:
                del self._requests[user_id]
        
        logger.info(f"Reset rate limit for {user_id}" + (f" on {endpoint}" if endpoint else ""))
    
    def limit(self, endpoint: str = "default", cost: int = 1):
        """
        Decorator for rate-limited endpoints.
        
        Usage:
            @rate_limiter.limit("design")
            async def design_endpoint(user_id: str, ...):
                ...
        
        Note: Function must accept 'user_id' as first argument or keyword.
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Try to extract user_id
                user_id = kwargs.get("user_id")
                if not user_id and args:
                    user_id = args[0]
                
                if not user_id:
                    user_id = "anonymous"
                
                # Check rate limit
                self.check(user_id, endpoint, cost)
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def cleanup(self):
        """
        Remove old entries to prevent memory leak.
        
        Call periodically (e.g., every hour).
        """
        now = time.time()
        max_window = max(limit.window for limit in self.limits.values())
        cutoff = now - max_window
        
        to_delete = []
        
        for user_id, endpoints in self._requests.items():
            for endpoint, timestamps in list(endpoints.items()):
                cleaned = [ts for ts in timestamps if ts > cutoff]
                if cleaned:
                    endpoints[endpoint] = cleaned
                else:
                    del endpoints[endpoint]
            
            if not endpoints:
                to_delete.append(user_id)
        
        for user_id in to_delete:
            del self._requests[user_id]
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} inactive users from rate limiter")


# Singleton instance
rate_limiter = RateLimiter()


# FastAPI middleware integration
def get_rate_limit_headers(user_id: str, endpoint: str = "default") -> Dict[str, str]:
    """
    Get rate limit headers for HTTP response.
    
    Usage:
        headers = get_rate_limit_headers(user_id, "design")
        return JSONResponse(content=data, headers=headers)
    """
    info = rate_limiter.get_remaining(user_id, endpoint)
    return {
        "X-RateLimit-Limit": str(info["limit"]),
        "X-RateLimit-Remaining": str(info["remaining"]),
        "X-RateLimit-Reset": str(info["reset"]),
    }
