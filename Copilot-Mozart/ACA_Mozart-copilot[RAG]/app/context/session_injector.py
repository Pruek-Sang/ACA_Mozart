"""
Session Injector - CRUD for mozart.sessions table

Philosophy:
- Mirror the structure of ConversationSession from session_store.py
- Provide DB persistence for stateful conversations
- Graceful fallback if DB unavailable

Usage:
    from app.context import session_injector
    
    # Create session
    session = await session_injector.create(user_id="xxx")
    
    # Load session
    session = await session_injector.load(session_id="xxx")
    
    # Update session
    await session_injector.update(session_id, {"stage": "confirmed"})
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict

from .supabase_client import get_supabase_client

logger = logging.getLogger("Aura.SessionInjector")

# =============================================================================
# CONFIGURATION
# =============================================================================

# TODO: Adjust session TTL based on production usage patterns
# Current: 24 hours. May need to increase for longer projects.
SESSION_TTL_HOURS = 24

# Max projects per user. Oldest will be auto-deleted when exceeded.
# TODO: In future, implement archiving to separate storage instead of deletion.
MAX_PROJECTS_PER_USER = 10

# Default project name when user doesn't provide one
DEFAULT_PROJECT_NAME = "\u0e1a\u0e49\u0e32\u0e19\u0e19\u0e32\u0e22\u0e2a\u0e21\u0e2b\u0e0d\u0e34\u0e07"


def _utcnow() -> datetime:
    """UTC now with timezone info."""
    return datetime.now(timezone.utc)


def _generate_guest_id() -> str:
    """Generate a guest user ID for anonymous users."""
    return f"guest_{uuid.uuid4().hex[:12]}"


@dataclass
class SessionData:
    """
    Session data structure matching mozart.sessions table.
    
    Compatible with ConversationSession from session_store.py
    """
    id: Optional[str] = None
    user_id: Optional[str] = None
    project_name: str = DEFAULT_PROJECT_NAME  # 🆕 User-defined name
    stage: str = "gathering"
    
    # Design data
    rooms: List[Dict] = field(default_factory=list)
    loads: List[Dict] = field(default_factory=list)
    site_context: Dict[str, Any] = field(default_factory=dict)  # 🆕 Stored with session
    
    # Conversation state
    messages: List[Dict] = field(default_factory=list)
    partial_requirements: Dict[str, Any] = field(default_factory=dict)
    current_spec: Optional[Dict] = None
    mcp_response: Optional[Dict] = None
    
    # 🆕 Phase 5: Undo history (separated from site_context)
    undo_history: List[Dict] = field(default_factory=list)
    
    # Metadata
    status: str = "active"
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON/DB storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "stage": self.stage,
            "rooms": self.rooms,
            "loads": self.loads,
            "site_context": self.site_context,
            "messages": self.messages,
            "partial_requirements": self.partial_requirements,
            "current_spec": self.current_spec,
            "mcp_response": self.mcp_response,
            "status": self.status,
            "undo_history": self.undo_history,  # 🆕 Phase 5
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create from DB row."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            project_name=data.get("project_name", DEFAULT_PROJECT_NAME),  # 🔧 FIX: Was missing!
            stage=data.get("stage", "gathering"),
            rooms=data.get("rooms") or [],
            loads=data.get("loads") or [],
            site_context=data.get("site_context") or {},
            messages=data.get("messages") or [],
            partial_requirements=data.get("partial_requirements") or {},
            current_spec=data.get("current_spec"),
            mcp_response=data.get("mcp_response"),
            undo_history=data.get("undo_history") or [],  # 🆕 Phase 5
            status=data.get("status", "active"),
            expires_at=data.get("expires_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class SessionInjector:
    """
    CRUD operations for mozart.sessions table.
    
    Follows Injector Pattern for separation of concerns.
    """
    
    TABLE = "sessions"
    SCHEMA = "mozart"
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self):
        """Lazy load Supabase client."""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client
    
    def is_available(self) -> bool:
        """Check if DB is available."""
        return self.client is not None
    
    # =========================================================================
    # CREATE
    # =========================================================================
    
    async def create(
        self, 
        user_id: Optional[str] = None, 
        project_name: Optional[str] = None,
        initial_data: Optional[Dict] = None
    ) -> Optional[SessionData]:
        """
        Create a new session in database.
        
        Supports both authenticated users and anonymous guests.
        Enforces max 10 projects per user - oldest deleted when exceeded.
        
        Args:
            user_id: Supabase auth user ID (None for guest)
            project_name: User-defined name (defaults to บ้านนายสมหญิง)
            initial_data: Optional initial session data
            
        Returns:
            SessionData or None if failed
        """
        if not self.is_available():
            logger.warning("[SESSION-CREATE] ❌ Supabase not available")
            return None
        
        try:
            logger.info("[SESSION-CREATE] === Creating new session ===")
            logger.info(f"[SESSION-CREATE] User ID: {user_id or 'GUEST'}")
            logger.info(f"[SESSION-CREATE] Project: {project_name or DEFAULT_PROJECT_NAME}")
            # 🆕 Support anonymous guests - use NULL for guest (Schema allows nullable user_id)
            # This fixes the "invalid input syntax for type uuid" error
            actual_user_id = user_id  # None for Guest, UUID for logged-in user
            
            # 🆕 Enforce max projects limit
            if user_id:  # Only for authenticated users
                existing = await self.load_by_user(user_id, limit=MAX_PROJECTS_PER_USER + 1)
                if len(existing) >= MAX_PROJECTS_PER_USER:
                    oldest = existing[-1]  # Oldest is last (sorted by updated_at desc)
                    logger.warning(f"Max projects ({MAX_PROJECTS_PER_USER}) reached, deleting oldest: {oldest.id}")
                    await self.delete(oldest.id)
            
            # 🆕 Calculate expiry time
            expires_at = (_utcnow() + timedelta(hours=SESSION_TTL_HOURS)).isoformat()
            
            data = {
                "user_id": actual_user_id,
                "project_name": project_name or DEFAULT_PROJECT_NAME,
                "stage": "gathering",
                "rooms": [],
                "loads": [],
                "site_context": {},
                "messages": [],
                "partial_requirements": {},
                "status": "active",
                "expires_at": expires_at,
            }
            
            if initial_data:
                data.update(initial_data)
            
            result = (
                self.client.schema(self.SCHEMA)
                .table(self.TABLE)
                .insert(data)
                .execute()
            )
            
            if result.data and len(result.data) > 0:
                session = SessionData.from_dict(result.data[0])
                logger.info(f"[SESSION-CREATE] ✅ Created: {session.id}")
                logger.info(f"[SESSION-CREATE] Project: {session.project_name}")
                logger.info(f"[SESSION-CREATE] Expires: {session.expires_at}")
                return session
            
            logger.warning("[SESSION-CREATE] ⚠️ No data returned from insert")
            return None
            
        except Exception as e:
            logger.error(f"[SESSION-CREATE] ❌ Failed: {e}")
            return None
    
    # =========================================================================
    # READ
    # =========================================================================
    
    async def load(self, session_id: str) -> Optional[SessionData]:
        """
        Load a session by ID.
        
        Args:
            session_id: Session UUID
            
        Returns:
            SessionData or None if not found
        """
        if not self.is_available():
            logger.warning("[SESSION-LOAD] ❌ Supabase not available")
            return None
        
        try:
            logger.info(f"[SESSION-LOAD] === Loading session: {session_id[:8]}... ===")
            result = (
                self.client.schema(self.SCHEMA)
                .table(self.TABLE)
                .select("*")
                .eq("id", session_id)
                .eq("status", "active")
                .single()
                .execute()
            )
            
            if result.data:
                session = SessionData.from_dict(result.data)
                logger.info(f"[SESSION-LOAD] ✅ Found: {session.project_name}")
                logger.info(f"[SESSION-LOAD] Has MCP: {bool(session.mcp_response)}")
                logger.info(f"[SESSION-LOAD] Messages: {len(session.messages) if session.messages else 0}")
                return session
            
            logger.warning(f"[SESSION-LOAD] ⚠️ Session not found: {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"[SESSION-LOAD] ❌ Failed: {e}")
            return None
    
    async def load_by_user(self, user_id: str, limit: int = 10) -> List[SessionData]:
        """
        Load recent sessions for a user.
        
        Args:
            user_id: Supabase auth user ID
            limit: Max number of sessions to return
            
        Returns:
            List of SessionData
        """
        if not self.is_available():
            return []
        
        try:
            result = (
                self.client.schema(self.SCHEMA)
                .table(self.TABLE)
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "active")
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return [SessionData.from_dict(row) for row in (result.data or [])]
            
        except Exception as e:
            logger.error(f"Failed to load sessions for user {user_id}: {e}")
            return []
    
    # =========================================================================
    # UPDATE
    # =========================================================================
    
    async def update(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a session.
        
        Args:
            session_id: Session UUID
            updates: Dict of fields to update
            
        Returns:
            True if successful
        """
        if not self.is_available():
            logger.warning("[SESSION-UPDATE] ❌ Supabase not available")
            return False
        
        try:
            logger.info(f"[SESSION-UPDATE] === Updating: {session_id[:8]}... ===")
            logger.info(f"[SESSION-UPDATE] Fields: {list(updates.keys())}")
            
            # Remove protected fields
            safe_updates = {k: v for k, v in updates.items() if k not in ["id", "user_id", "created_at"]}
            
            result = (
                self.client.schema(self.SCHEMA)
                .table(self.TABLE)
                .update(safe_updates)
                .eq("id", session_id)
                .execute()
            )
            
            success = result.data is not None and len(result.data) > 0
            if success:
                logger.info(f"[SESSION-UPDATE] ✅ Updated successfully")
            else:
                logger.warning(f"[SESSION-UPDATE] ⚠️ No data returned")
            
            return success
            
        except Exception as e:
            logger.error(f"[SESSION-UPDATE] ❌ Failed: {e}")
            return False
    
    async def update_stage(self, session_id: str, stage: str) -> bool:
        """Update session stage."""
        return await self.update(session_id, {"stage": stage})
    
    async def update_design(
        self,
        session_id: str,
        rooms: Optional[List] = None,
        loads: Optional[List] = None,
        site_context: Optional[Dict] = None,
    ) -> bool:
        """Update design data (rooms, loads, site_context)."""
        updates = {}
        if rooms is not None:
            updates["rooms"] = rooms
        if loads is not None:
            updates["loads"] = loads
        if site_context is not None:
            updates["site_context"] = site_context
        
        return await self.update(session_id, updates) if updates else False
    
    async def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to session history.
        
        Args:
            session_id: Session UUID
            role: "user" or "assistant"
            content: Message content
        """
        session = await self.load(session_id)
        if not session:
            return False
        
        messages = session.messages or []
        messages.append({
            "role": role,
            "content": content,
            "timestamp": _utcnow().isoformat(),
        })
        
        return await self.update(session_id, {"messages": messages})
    
    async def set_mcp_response(self, session_id: str, mcp_response: Dict) -> bool:
        """Save MCP calculation response."""
        return await self.update(session_id, {
            "mcp_response": mcp_response,
            "stage": "completed",
        })
    
    # =========================================================================
    # DELETE
    # =========================================================================
    
    async def delete(self, session_id: str) -> bool:
        """
        Soft delete a session (set status to 'expired').
        
        Args:
            session_id: Session UUID
        """
        return await self.update(session_id, {"status": "expired"})
    
    async def hard_delete(self, session_id: str) -> bool:
        """
        Permanently delete a session.
        
        Args:
            session_id: Session UUID
        """
        if not self.is_available():
            return False
        
        try:
            self.client.schema(self.SCHEMA).table(self.TABLE).delete().eq("id", session_id).execute()
            logger.info(f"Hard deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to hard delete session {session_id}: {e}")
            return False
    
    # =========================================================================
    # MIGRATE TO PROJECT
    # =========================================================================
    
    async def migrate_to_project(self, session_id: str, project_name: str) -> Optional[str]:
        """
        Migrate session to a permanent project.
        
        Args:
            session_id: Session UUID
            project_name: Name for the new project
            
        Returns:
            New project ID or None if failed
        """
        from .project_injector import project_injector
        
        session = await self.load(session_id)
        if not session:
            logger.error(f"Session {session_id} not found for migration")
            return None
        
        # Create project from session
        project = await project_injector.create_from_session(
            session=session,
            name=project_name,
        )
        
        if project:
            # Mark session as migrated
            await self.update(session_id, {"status": "migrated"})
            logger.info(f"Migrated session {session_id} to project {project.id}")
            return project.id
        
        return None


# Singleton instance
session_injector = SessionInjector()
