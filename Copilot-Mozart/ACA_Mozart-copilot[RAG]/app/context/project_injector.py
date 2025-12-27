"""
Project Injector - CRUD for mozart.projects table

Philosophy:
- Projects are PERMANENT saved designs
- Sessions migrate to Projects when user clicks "Save"
- Versioning support for Undo/Redo

Usage:
    from app.context import project_injector
    
    # Create project from session
    project = await project_injector.create_from_session(session, "My House")
    
    # Load user's projects
    projects = await project_injector.load_by_user(user_id)
    
    # Create new version (for undo/redo)
    new_version = await project_injector.create_version(project_id, updates)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .supabase_client import get_supabase_client

logger = logging.getLogger("Aura.ProjectInjector")


def _utcnow() -> datetime:
    """UTC now with timezone info."""
    return datetime.now(timezone.utc)


@dataclass
class ProjectData:
    """
    Project data structure matching mozart.projects table.
    """
    id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Metadata
    name: str = ""
    description: Optional[str] = None
    
    # Design data
    rooms: List[Dict] = field(default_factory=list)
    loads: List[Dict] = field(default_factory=list)
    site_context: Dict[str, Any] = field(default_factory=dict)
    mcp_response: Optional[Dict] = None
    sld_data: Optional[Dict] = None
    
    # Versioning
    version: int = 1
    parent_id: Optional[str] = None
    
    # Status
    status: str = "draft"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON/DB storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "name": self.name,
            "description": self.description,
            "rooms": self.rooms,
            "loads": self.loads,
            "site_context": self.site_context,
            "mcp_response": self.mcp_response,
            "sld_data": self.sld_data,
            "version": self.version,
            "parent_id": self.parent_id,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectData":
        """Create from DB row."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            name=data.get("name", ""),
            description=data.get("description"),
            rooms=data.get("rooms") or [],
            loads=data.get("loads") or [],
            site_context=data.get("site_context") or {},
            mcp_response=data.get("mcp_response"),
            sld_data=data.get("sld_data"),
            version=data.get("version", 1),
            parent_id=data.get("parent_id"),
            status=data.get("status", "draft"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class ProjectInjector:
    """
    CRUD operations for mozart.projects table.
    
    Follows Injector Pattern for separation of concerns.
    """
    
    TABLE = "mozart.projects"
    
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
        user_id: str,
        name: str,
        description: Optional[str] = None,
        initial_data: Optional[Dict] = None,
    ) -> Optional[ProjectData]:
        """
        Create a new project.
        
        Args:
            user_id: Supabase auth user ID
            name: Project name
            description: Optional description
            initial_data: Optional initial project data
            
        Returns:
            ProjectData or None if failed
        """
        if not self.is_available():
            logger.warning("Supabase not available, cannot create project")
            return None
        
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "description": description,
                "rooms": [],
                "loads": [],
                "site_context": {},
                "version": 1,
                "status": "draft",
            }
            
            if initial_data:
                data.update(initial_data)
            
            result = self.client.table(self.TABLE).insert(data).execute()
            
            if result.data and len(result.data) > 0:
                project = ProjectData.from_dict(result.data[0])
                logger.info(f"Created project: {project.id} - {name}")
                return project
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None
    
    async def create_from_session(
        self,
        session,  # SessionData from session_injector
        name: str,
        description: Optional[str] = None,
    ) -> Optional[ProjectData]:
        """
        Create a project from a session (migration).
        
        Args:
            session: SessionData instance
            name: Project name
            description: Optional description
            
        Returns:
            ProjectData or None if failed
        """
        return await self.create(
            user_id=session.user_id,
            name=name,
            description=description,
            initial_data={
                "session_id": session.id,
                "rooms": session.rooms,
                "loads": session.loads,
                "site_context": session.site_context,
                "mcp_response": session.mcp_response,
                "status": "active" if session.mcp_response else "draft",
            },
        )
    
    # =========================================================================
    # READ
    # =========================================================================
    
    async def load(self, project_id: str) -> Optional[ProjectData]:
        """
        Load a project by ID.
        
        Args:
            project_id: Project UUID
            
        Returns:
            ProjectData or None if not found
        """
        if not self.is_available():
            logger.warning("Supabase not available, cannot load project")
            return None
        
        try:
            result = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("id", project_id)
                .single()
                .execute()
            )
            
            if result.data:
                return ProjectData.from_dict(result.data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load project {project_id}: {e}")
            return None
    
    async def load_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ProjectData]:
        """
        Load projects for a user.
        
        Args:
            user_id: Supabase auth user ID
            status: Optional filter by status
            limit: Max number of projects to return
            
        Returns:
            List of ProjectData
        """
        if not self.is_available():
            return []
        
        try:
            query = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("user_id", user_id)
                .neq("status", "archived")  # Don't show archived by default
                .order("updated_at", desc=True)
                .limit(limit)
            )
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            
            return [ProjectData.from_dict(row) for row in (result.data or [])]
            
        except Exception as e:
            logger.error(f"Failed to load projects for user {user_id}: {e}")
            return []
    
    async def search(self, user_id: str, query: str, limit: int = 20) -> List[ProjectData]:
        """
        Search projects by name (case-insensitive).
        
        Args:
            user_id: Supabase auth user ID
            query: Search query
            limit: Max results
            
        Returns:
            List of matching ProjectData
        """
        if not self.is_available():
            return []
        
        try:
            result = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("user_id", user_id)
                .ilike("name", f"%{query}%")
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return [ProjectData.from_dict(row) for row in (result.data or [])]
            
        except Exception as e:
            logger.error(f"Failed to search projects: {e}")
            return []
    
    # =========================================================================
    # UPDATE
    # =========================================================================
    
    async def update(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a project.
        
        Args:
            project_id: Project UUID
            updates: Dict of fields to update
            
        Returns:
            True if successful
        """
        if not self.is_available():
            logger.warning("Supabase not available, cannot update project")
            return False
        
        try:
            # Remove protected fields
            safe_updates = {k: v for k, v in updates.items() 
                          if k not in ["id", "user_id", "created_at", "version", "parent_id"]}
            
            result = (
                self.client.table(self.TABLE)
                .update(safe_updates)
                .eq("id", project_id)
                .execute()
            )
            
            success = result.data is not None and len(result.data) > 0
            if success:
                logger.debug(f"Updated project {project_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return False
    
    async def rename(self, project_id: str, new_name: str) -> bool:
        """Rename a project."""
        return await self.update(project_id, {"name": new_name})
    
    async def set_status(self, project_id: str, status: str) -> bool:
        """Change project status."""
        if status not in ["draft", "active", "archived"]:
            logger.error(f"Invalid status: {status}")
            return False
        return await self.update(project_id, {"status": status})
    
    # =========================================================================
    # VERSIONING (for Undo/Redo)
    # =========================================================================
    
    async def create_version(
        self,
        project_id: str,
        updates: Dict[str, Any],
    ) -> Optional[ProjectData]:
        """
        Create a new version of a project (for undo/redo).
        
        The old version becomes the parent, new version is active.
        
        Args:
            project_id: Current project ID
            updates: Changes for the new version
            
        Returns:
            New ProjectData or None if failed
        """
        current = await self.load(project_id)
        if not current:
            return None
        
        # Create new version with incremented number
        new_data = {
            "user_id": current.user_id,
            "session_id": current.session_id,
            "name": current.name,
            "description": current.description,
            "rooms": updates.get("rooms", current.rooms),
            "loads": updates.get("loads", current.loads),
            "site_context": updates.get("site_context", current.site_context),
            "mcp_response": updates.get("mcp_response", current.mcp_response),
            "sld_data": updates.get("sld_data", current.sld_data),
            "version": current.version + 1,
            "parent_id": current.id,  # Link to previous version
            "status": current.status,
        }
        
        try:
            result = self.client.table(self.TABLE).insert(new_data).execute()
            
            if result.data and len(result.data) > 0:
                project = ProjectData.from_dict(result.data[0])
                logger.info(f"Created version {project.version} of project {project.name}")
                return project
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create version: {e}")
            return None
    
    async def get_version_history(self, project_id: str) -> List[ProjectData]:
        """
        Get version history of a project (newest first).
        
        Follow parent_id chain backwards.
        """
        history = []
        current_id = project_id
        
        while current_id and len(history) < 100:  # Safety limit
            project = await self.load(current_id)
            if not project:
                break
            history.append(project)
            current_id = project.parent_id
        
        return history
    
    # =========================================================================
    # DELETE
    # =========================================================================
    
    async def archive(self, project_id: str) -> bool:
        """
        Archive a project (soft delete).
        
        Args:
            project_id: Project UUID
        """
        return await self.set_status(project_id, "archived")
    
    async def hard_delete(self, project_id: str) -> bool:
        """
        Permanently delete a project.
        
        Args:
            project_id: Project UUID
        """
        if not self.is_available():
            return False
        
        try:
            self.client.table(self.TABLE).delete().eq("id", project_id).execute()
            logger.info(f"Hard deleted project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to hard delete project {project_id}: {e}")
            return False


# Singleton instance
project_injector = ProjectInjector()
