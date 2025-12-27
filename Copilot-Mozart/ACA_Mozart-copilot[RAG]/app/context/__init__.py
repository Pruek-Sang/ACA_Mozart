"""
Context Layer - Data Access for Mozart Stateful Intelligence

This module provides injectors for accessing Supabase database:
- SupabaseClient: Connection management
- SessionInjector: CRUD for mozart.sessions
- ProjectInjector: CRUD for mozart.projects
- AuditLogger: Conversation logging for traceability
- MergeEngine: Design merge/patch logic

Philosophy:
- Separation of concerns (MVC pattern)
- Injector pattern for testability
- Fallback to stateless if DB unavailable
"""

from .supabase_client import supabase_client, get_supabase_client
from .session_injector import SessionInjector, session_injector
from .project_injector import ProjectInjector, project_injector
from .audit_logger import log_conversation
from .merge_engine import merge_design_changes

__all__ = [
    "supabase_client",
    "get_supabase_client",
    "SessionInjector",
    "session_injector",
    "ProjectInjector", 
    "project_injector",
    "log_conversation",
    "merge_design_changes",
]
