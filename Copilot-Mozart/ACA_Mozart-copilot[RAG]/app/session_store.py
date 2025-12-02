"""
Session Store - Conversation Memory for Multi-Turn Interactions

Philosophy: 
- Start simple (in-memory)
- Scale later (Redis)
- Protect state integrity
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import uuid
import logging


def _utcnow() -> datetime:
    """UTC now with timezone info (Python 3.12+ compatible)"""
    return datetime.now(timezone.utc)

logger = logging.getLogger("Aura.Session")


@dataclass
class ConversationSession:
    """
    Single conversation session
    
    Lifecycle:
    1. gathering - Collecting requirements
    2. reviewing - Spec generated, user reviewing
    3. confirmed - User confirmed, ready for MCP
    4. completed - MCP processed
    """
    session_id: str
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    
    # Accumulated data
    partial_requirements: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, Any]] = field(default_factory=list)  # Chat history
    current_spec: Optional[Dict[str, Any]] = None  # Latest generated spec
    
    # State machine
    stage: str = "gathering"  # gathering | reviewing | confirmed | completed
    
    # MCP tracking
    mcp_response: Optional[Dict[str, Any]] = None
    
    def is_expired(self, ttl_minutes: int = 60) -> bool:
        """Check if session is expired"""
        return _utcnow() - self.updated_at > timedelta(minutes=ttl_minutes)
    
    def add_user_message(self, content: str):
        """Add user message to history"""
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": _utcnow().isoformat()
        })
        self.updated_at = _utcnow()
    
    def add_assistant_message(self, content: str, questions: Optional[List[str]] = None):
        """Add assistant message to history"""
        self.messages.append({
            "role": "assistant",
            "content": content,
            "questions": questions or [],
            "timestamp": _utcnow().isoformat()
        })
        self.updated_at = _utcnow()
    
    def get_conversation_context(self, max_turns: int = 10) -> str:
        """Get formatted conversation history for LLM context"""
        recent = self.messages[-max_turns*2:] if len(self.messages) > max_turns*2 else self.messages
        
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "stage": self.stage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "partial_requirements": self.partial_requirements,
            "messages": self.messages,
            "current_spec": self.current_spec,
            "mcp_response": self.mcp_response
        }


class SessionStore:
    """
    In-memory session storage
    
    Note: For production with multiple instances, use RedisSessionStore
    """
    
    def __init__(self, ttl_minutes: int = 60):
        self._sessions: Dict[str, ConversationSession] = {}
        self.ttl = ttl_minutes
        logger.info(f"SessionStore initialized with TTL={ttl_minutes} minutes")
    
    def create_session(self) -> ConversationSession:
        """Create a new conversation session"""
        session = ConversationSession(session_id=str(uuid.uuid4()))
        self._sessions[session.session_id] = session
        logger.info(f"Created session: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get session by ID, returns None if expired or not found"""
        session = self._sessions.get(session_id)
        if session:
            if session.is_expired(self.ttl):
                logger.info(f"Session expired: {session_id}")
                del self._sessions[session_id]
                return None
            return session
        return None
    
    def update_requirements(self, session_id: str, new_data: Dict[str, Any]):
        """Merge new requirements into session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Deep merge for rooms and loads (append), shallow for others
        current = session.partial_requirements
        
        for key, value in new_data.items():
            if value is None:
                continue
            
            if key in ["rooms", "loads", "user_constraints"]:
                # Append to list
                if key not in current:
                    current[key] = []
                if isinstance(value, list):
                    current[key].extend(value)
            else:
                # Override scalar
                current[key] = value
        
        session.partial_requirements = current
        session.updated_at = _utcnow()
        logger.debug(f"Updated requirements for session {session_id}")
    
    def set_spec(self, session_id: str, spec: Dict[str, Any]):
        """Set generated spec for session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.current_spec = spec
        session.stage = "reviewing"
        session.updated_at = _utcnow()
    
    def confirm_session(self, session_id: str):
        """Mark session as confirmed, ready for MCP"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if not session.current_spec:
            raise ValueError("Cannot confirm without spec")
        
        session.stage = "confirmed"
        session.updated_at = _utcnow()
        logger.info(f"Session confirmed: {session_id}")
    
    def complete_session(self, session_id: str, mcp_response: Dict[str, Any]):
        """Mark session as completed with MCP response"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.mcp_response = mcp_response
        session.stage = "completed"
        session.updated_at = _utcnow()
        logger.info(f"Session completed: {session_id}")
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def cleanup_expired(self) -> int:
        """Remove all expired sessions, returns count"""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired(self.ttl)]
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)
    
    def list_active_sessions(self) -> List[str]:
        """List all active session IDs"""
        return [
            sid for sid, s in self._sessions.items()
            if not s.is_expired(self.ttl)
        ]


# Singleton instance
session_store = SessionStore(ttl_minutes=60)


# === Optional: Redis-backed store for production ===

class RedisSessionStore:
    """
    Redis-backed session store for production
    
    Usage:
        store = RedisSessionStore("redis://localhost:6379/0")
    
    Note: Requires `pip install redis` to use
    """
    
    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        try:
            import redis as redis_lib  # type: ignore[import-not-found]
            self.redis = redis_lib.from_url(redis_url)
            self.ttl = ttl_seconds
            logger.info(f"RedisSessionStore connected to {redis_url}")
        except ImportError:
            raise RuntimeError("redis package required: pip install redis")
    
    def _key(self, session_id: str) -> str:
        return f"aura:session:{session_id}"
    
    def create_session(self) -> ConversationSession:
        session = ConversationSession(session_id=str(uuid.uuid4()))
        self._save(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        import json
        data = self.redis.get(self._key(session_id))
        if not data:
            return None
        
        d = json.loads(data)
        session = ConversationSession(
            session_id=d["session_id"],
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
            partial_requirements=d["partial_requirements"],
            messages=d["messages"],
            current_spec=d["current_spec"],
            stage=d["stage"],
            mcp_response=d.get("mcp_response")
        )
        return session
    
    def _save(self, session: ConversationSession):
        import json
        self.redis.setex(
            self._key(session.session_id),
            self.ttl,
            json.dumps(session.to_dict())
        )
    
    def update_requirements(self, session_id: str, new_data: Dict[str, Any]):
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Same merge logic as in-memory
        current = session.partial_requirements
        for key, value in new_data.items():
            if value is None:
                continue
            if key in ["rooms", "loads", "user_constraints"]:
                if key not in current:
                    current[key] = []
                if isinstance(value, list):
                    current[key].extend(value)
            else:
                current[key] = value
        
        session.partial_requirements = current
        session.updated_at = _utcnow()
        self._save(session)
