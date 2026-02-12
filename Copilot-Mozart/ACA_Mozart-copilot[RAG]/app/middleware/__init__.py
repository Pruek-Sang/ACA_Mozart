"""
Middleware Layer - Request Processing for Mozart RAG

This module provides middleware components:
- RateLimiter: Protect expensive LLM/RAG calls

Philosophy:
- Protect API costs (LLM calls are expensive!)
- Fair usage across users
- Graceful degradation
"""

from .rate_limiter import RateLimiter, rate_limiter, RateLimitExceeded
from .jwt_auth import jwt_auth_middleware

__all__ = [
    "RateLimiter",
    "rate_limiter",
    "RateLimitExceeded",
    "jwt_auth_middleware",
]
