"""
Knowledge Service v2 - Folder-Based Architecture
Manages knowledge across 4 folders: db, example, mcp, standard

Philosophy: 
- Scan ALL files in 4 folders (not just indexed)
- knowledge_index.json = metadata/priority (NOT whitelist)
- Unindexed files still loadable (lower priority)
"""

import json
import logging
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

from app.config import settings
from app.models import KnowledgeFolder, DocumentMeta

logger = logging.getLogger("Aura.Knowledge")


class KnowledgeService:
    """
    Folder-based knowledge management
    
    Responsibilities:
    - Scan all files in db/, example/, mcp/, standard/
    - Load knowledge_index.json for metadata/priority
    - Provide filtered document lists by folder/group
    - Lazy load document content
    """
    
    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize knowledge service
        
        Args:
            index_path: Path to knowledge_index.json (defaults to config)
        """
        self.index_path = Path(index_path or settings.KNOWLEDGE_INDEX_PATH)
        self.knowledge_root = Path(settings.KNOWLEDGE_ROOT)
        
        # Folder paths
        self.folders = {
            "db": Path(settings.KNOWLEDGE_DIR_DB),
            "example": Path(settings.KNOWLEDGE_DIR_EXAMPLE),
            "mcp": Path(settings.KNOWLEDGE_DIR_MCP),
            "standard": Path(settings.KNOWLEDGE_DIR_STANDARD),
        }
        
        # Internal storage
        self._docs_by_path: Dict[str, DocumentMeta] = {}
        self._docs_by_id: Dict[str, DocumentMeta] = {}
        self._docs_by_group: Dict[str, List[DocumentMeta]] = {}
        self._docs_unindexed: List[DocumentMeta] = []
        self._index_data: List[Dict[str, Any]] = []
        
        # Load and scan
        self._load_index()
        self._scan_folders()
        
        logger.info(f"KnowledgeService v2 initialized: {len(self._docs_by_path)} documents")
    
    def _load_index(self) -> None:
        """Load knowledge_index.json for metadata"""
        try:
            if not self.index_path.exists():
                logger.warning(f"Knowledge index not found: {self.index_path}")
                self._index_data = []
                return
            
            with open(self.index_path, 'r', encoding='utf-8') as f:
                self._index_data = json.load(f)
            
            logger.info(f"Loaded index with {len(self._index_data)} entries")
            
        except Exception as e:
            logger.error(f"Failed to load knowledge index: {e}")
            self._index_data = []
    
    def _find_index_entry(self, rel_path: str) -> Optional[Dict[str, Any]]:
        """
        Find index entry matching relative path
        
        Args:
            rel_path: Path relative to KNOWLEDGE_ROOT
        
        Returns:
            Index entry dict or None
        """
        for entry in self._index_data:
            if entry.get("path") == rel_path:
                return entry
        return None
    
    def _compute_priority(self, index_entry: Optional[Dict[str, Any]]) -> int:
        """
        Compute retrieval priority
        
        Rules:
        - "must_read" tag → 95
        - "deprecated" tag → 20
        - High-priority groups → 90
        - Has index but normal → 60
        - No index → 50
        
        Args:
            index_entry: Entry from knowledge_index.json
        
        Returns:
            Priority score (higher = more important)
        """
        if not index_entry:
            return 50
        
        group = index_entry.get("group")
        tags = index_entry.get("tags", [])
        
        if "must_read" in tags:
            return 95
        if "deprecated" in tags:
            return 20
        if group in ["mcp_spec", "catalog_schema", "thai_standard", "example_project"]:
            return 90
        
        return 60
    
    def _scan_folders(self) -> None:
        """
        Scan all 4 folders for files
        
        Process:
        1. Walk each folder (*.md, *.txt, *.json)
        2. For each file:
           - Create DocumentMeta
           - Match with knowledge_index if exists
           - Compute priority
        3. Build internal indices
        """
        for folder_name, folder_path in self.folders.items():
            if not folder_path.exists():
                logger.warning(f"Folder not found: {folder_path}")
                continue
            
            for file_path in folder_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                if file_path.suffix not in [".md", ".txt", ".json"]:
                    continue
                
                # Relative path from KNOWLEDGE_ROOT
                try:
                    rel_path = file_path.relative_to(self.knowledge_root)
                except ValueError:
                    logger.warning(f"File outside knowledge root: {file_path}")
                    continue
                
                # Find in index
                index_entry = self._find_index_entry(str(rel_path))
                
                # Create DocumentMeta
                doc_meta = DocumentMeta(
                    id=index_entry.get("id") if index_entry else None,
                    path=str(file_path),
                    rel_path=str(rel_path),
                    folder=KnowledgeFolder(folder_name),
                    group=index_entry.get("group") if index_entry else None,
                    tags=index_entry.get("tags", []) if index_entry else [],
                    version=index_entry.get("version") if index_entry else None,
                    language=index_entry.get("language", "th") if index_entry else "th",
                    priority=self._compute_priority(index_entry)
                )
                
                # Store in indices
                self._docs_by_path[str(file_path)] = doc_meta
                
                if doc_meta.id:
                    self._docs_by_id[doc_meta.id] = doc_meta
                
                if doc_meta.group:
                    self._docs_by_group.setdefault(doc_meta.group, []).append(doc_meta)
                else:
                    self._docs_unindexed.append(doc_meta)
        
        logger.info(
            f"Scanned folders: {len(self._docs_by_path)} files, "
            f"{len(self._docs_unindexed)} unindexed"
        )
    
    # === Public API ===
    
    def list_docs(
        self,
        folder: Optional[str] = None,
        group: Optional[str] = None
    ) -> List[DocumentMeta]:
        """
        List documents with optional filters
        
        Args:
            folder: Filter by folder ("db", "example", "mcp", "standard")
            group: Filter by group from index (e.g., "mcp_spec")
        
        Returns:
            List of DocumentMeta sorted by priority descending
        """
        docs = list(self._docs_by_path.values())
        
        if folder:
            docs = [d for d in docs if d.folder == folder]
        
        if group:
            docs = [d for d in docs if d.group == group]
        
        # Sort by priority descending
        docs.sort(key=lambda d: d.priority, reverse=True)
        
        return docs
    
    def get_docs_for_mcp_spec(self) -> List[DocumentMeta]:
        """
        Get documents for MCP spec generation
        
        Strategy:
        - Include ALL files from db, mcp, standard, example
        - Priority ordering (high priority groups first)
        
        Returns:
            Sorted list by priority descending
        """
        all_docs = []
        
        # Add from all 4 folders
        for folder_name in ["db", "mcp", "standard", "example"]:
            all_docs.extend(self.list_docs(folder=folder_name))
        
        # Already sorted by priority in list_docs
        return all_docs
    
    def get_docs_for_ask(self, context_hint: List[str]) -> List[DocumentMeta]:
        """
        Get documents for /ask endpoint
        
        Context hint mapping:
        - "db" → folder db
        - "standard" → folder standard
        - "mcp_spec" → group mcp_spec
        - empty list → all folders
        
        Args:
            context_hint: List of folder names or group names
        
        Returns:
            Sorted list by priority descending
        """
        if not context_hint:
            return self.list_docs()
        
        docs = []
        for hint in context_hint:
            # Try as folder first
            if hint in ["db", "example", "mcp", "standard"]:
                docs.extend(self.list_docs(folder=hint))
            # Try as group
            elif hint in self._docs_by_group:
                docs.extend(self._docs_by_group[hint])
        
        # Remove duplicates and sort by priority
        seen: Set[str] = set()
        unique_docs = []
        for doc in docs:
            if doc.path not in seen:
                seen.add(doc.path)
                unique_docs.append(doc)
        
        unique_docs.sort(key=lambda d: d.priority, reverse=True)
        
        return unique_docs
    
    def load_doc_content(self, doc_meta: DocumentMeta) -> str:
        """
        Load document content (lazy)
        
        Args:
            doc_meta: Document metadata
        
        Returns:
            File content as string
        """
        try:
            with open(doc_meta.path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load {doc_meta.path}: {e}")
            return ""
    
    def get_doc_by_id(self, doc_id: str) -> Optional[DocumentMeta]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID from index
        
        Returns:
            DocumentMeta or None
        """
        return self._docs_by_id.get(doc_id)
    
    def list_groups(self) -> List[str]:
        """
        List all groups found in indexed documents
        
        Returns:
            Sorted list of group names
        """
        return sorted(self._docs_by_group.keys())
