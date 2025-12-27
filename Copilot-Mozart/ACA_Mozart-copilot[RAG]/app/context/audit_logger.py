"""
Audit Logger - Stateful Intelligence Module

Logs conversation messages to Supabase for audit trail / legal traceability.
Fire-and-forget pattern - never blocks main flow.

Created: 2025-12-28
"""

import logging
from typing import Optional

logger = logging.getLogger("Aura.Context.AuditLogger")


async def log_conversation(
    session_id: str,
    role: str,
    content: str
) -> bool:
    """
    Log conversation message to Supabase for audit trail.
    
    This is a "fire and forget" async operation - it should never
    block or crash the main flow, even if Supabase is unavailable.
    
    Args:
        session_id: The current session UUID
        role: "user" or "assistant"
        content: The message content to log
        
    Returns:
        bool: True if logged successfully, False otherwise
    """
    try:
        # Import injector only when needed (lazy load)
        from app.context.session_injector import session_injector
        
        if not session_injector.is_available():
            logger.warning("[AUDIT] Supabase not available, skipping log")
            return False
        
        success = await session_injector.add_message(session_id, role, content)
        
        if success:
            logger.info(f"[AUDIT] Logged {role} message to session {session_id[:8]}...")
        else:
            logger.warning(f"[AUDIT] Failed to log message to session {session_id[:8]}...")
        
        return success
        
    except Exception as e:
        # Never crash main flow - just log and continue
        logger.error(f"[AUDIT] Exception while logging: {e}")
        return False
