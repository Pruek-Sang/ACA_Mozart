"""
JWT Auth Middleware - Decode Supabase JWT & Set request.state.user_id

Philosophy:
- PERMISSIVE: Never return 401 — Guest mode is a deliberate feature ("ทดลอง 24 ชม.")
- If token is valid → set request.state.user_id = Supabase user UUID (sub claim)
- If token is missing/invalid → set request.state.user_id = None (guest path continues)
- This single middleware unlocks session isolation, project list, and per-user rate limiting
  because all those features already read request.state.user_id

Supabase JWT format:
- Algorithm: HS256
- Audience: "authenticated"
- Payload.sub: User UUID (auth.users.id)
"""

import os
import logging

logger = logging.getLogger("Aura.JWTAuth")

# Load JWT secret from env — Supabase Dashboard → Settings → API → JWT Secret
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Try importing PyJWT
try:
    import jwt as pyjwt
    PYJWT_AVAILABLE = True
except ImportError:
    PYJWT_AVAILABLE = False
    logger.warning("⚠️ PyJWT not installed — JWT auth middleware disabled. Install with: pip install PyJWT>=2.8.0")


async def jwt_auth_middleware(request, call_next):
    """
    Extract and decode Supabase JWT from Authorization header.
    
    Sets request.state.user_id to:
    - Supabase user UUID (if valid JWT)
    - None (if no token, invalid token, or PyJWT not installed)
    
    NEVER returns 401 — guest mode must always work.
    """
    request.state.user_id = None  # Default: guest
    
    if not PYJWT_AVAILABLE or not SUPABASE_JWT_SECRET:
        # No JWT library or no secret configured → skip silently
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # No token → guest path (this is expected for guest users)
        return await call_next(request)
    
    token = auth_header[7:]  # Strip "Bearer "
    
    try:
        payload = pyjwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        
        user_id = payload.get("sub")
        if user_id:
            request.state.user_id = user_id
            logger.debug(f"🔑 JWT auth: user_id={user_id[:8]}...")
        
    except pyjwt.ExpiredSignatureError:
        logger.debug("🔑 JWT expired — treating as guest")
    except pyjwt.InvalidTokenError as e:
        logger.debug(f"🔑 JWT invalid ({e}) — treating as guest")
    except Exception as e:
        logger.warning(f"🔑 JWT decode unexpected error: {e}")
    
    return await call_next(request)
