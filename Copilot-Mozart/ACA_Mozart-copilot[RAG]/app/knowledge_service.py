"""
Knowledge Service - The Librarian of Divine Wisdom
Manages canonical knowledge index following Canonical Funnel pattern

Philosophy: Ordo ab Chao
- Single source of truth: knowledge_index.json
- Group-based retrieval (no "search everything" chaos)
- Explicit document lifecycle
"""

import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger("Aura.Knowledge")


class DocMeta(BaseModel):
    """Metadata for a knowledge document"""
    id: str
    path: str
    group: str
    tags: List[str] = []
    version: str = "1.0"
    language: str = "th"


class KnowledgeService:
    """
    Service layer for canonical knowledge management
    
    Responsibilities:
    - Load and validate knowledge_index.json
    - Filter documents by group
    - Load document content
    - Provide context for specific use cases (e.g., mcp_spec)
    """
    
    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize knowledge service
        
        Args:
            index_path: Path to knowledge_index.json (defaults to config)
        """
        self.index_path = Path(index_path or settings.KNOWLEDGE_INDEX_PATH)
        self.knowledge_root = Path(settings.KNOWLEDGE_ROOT)
        self._index: List[DocMeta] = []
        self._load_index()
    
    def _load_index(self) -> None:
        """Load knowledge index from JSON file"""
        try:
            if not self.index_path.exists():
                logger.warning(f"Knowledge index not found: {self.index_path}")
                logger.info("Creating empty knowledge index")
                self._index = []
                self._save_index()
                return
            
            with open(self.index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            self._index = [DocMeta(**item) for item in index_data]
            logger.info(f"Loaded {len(self._index)} documents from knowledge index")
            
        except Exception as e:
            logger.error(f"Failed to load knowledge index: {e}")
            self._index = []
    
    def _save_index(self) -> None:
        """Save knowledge index to JSON file"""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index_data = [doc.model_dump() for doc in self._index]
            
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved knowledge index with {len(self._index)} documents")
            
        except Exception as e:
            logger.error(f"Failed to save knowledge index: {e}")
    
    def list_groups(self) -> List[str]:
        """
        List all available groups
        
        Returns:
            List of unique group names
        """
        groups = sorted(set(doc.group for doc in self._index))
        logger.debug(f"Available groups: {groups}")
        return groups
    
    def list_docs(self, group: Optional[str] = None) -> List[DocMeta]:
        """
        List documents, optionally filtered by group
        
        Args:
            group: Group name to filter by (None = all docs)
        
        Returns:
            List of document metadata
        """
        if group is None:
            return self._index.copy()
        
        filtered = [doc for doc in self._index if doc.group == group]
        logger.debug(f"Group '{group}': {len(filtered)} documents")
        return filtered
    
    def get_doc_meta(self, doc_id: str) -> Optional[DocMeta]:
        """
        Get metadata for a specific document
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document metadata or None if not found
        """
        for doc in self._index:
            if doc.id == doc_id:
                return doc
        
        logger.warning(f"Document not found: {doc_id}")
        return None
    
    def load_doc_content(self, doc_id: str) -> Optional[str]:
        """
        Load content of a document
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document content as string or None if not found
        """
        doc_meta = self.get_doc_meta(doc_id)
        if doc_meta is None:
            return None
        
        try:
            doc_path = self.knowledge_root / doc_meta.path
            
            if not doc_path.exists():
                logger.error(f"Document file not found: {doc_path}")
                return None
            
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"Loaded document: {doc_id} ({len(content)} chars)")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load document {doc_id}: {e}")
            return None
    
    def get_docs_for_mcp_spec(self) -> List[DocMeta]:
        """
        Get documents relevant for MCP spec generation
        
        Following HOW_TO_FIX_RAG_v2:
        - mcp_spec group: MCP design, contracts, schemas
        - catalog_schema group: DB structure, catalog info
        - thai_standard group: Electrical standards
        
        Returns:
            List of relevant document metadata
        """
        relevant_groups = ['mcp_spec', 'catalog_schema', 'thai_standard', 'example_project']
        
        docs = []
        for group in relevant_groups:
            docs.extend(self.list_docs(group))
        
        logger.info(f"Retrieved {len(docs)} docs for mcp_spec generation")
        return docs
    
    def get_docs_for_thai_standard(self) -> List[DocMeta]:
        """
        Get Thai electrical standard documents
        
        Returns:
            List of standard documents
        """
        return self.list_docs('thai_standard')
    
    def add_document(self, doc_meta: DocMeta) -> bool:
        """
        Add a document to the index
        
        Args:
            doc_meta: Document metadata
        
        Returns:
            True if added successfully
        """
        # Check if already exists
        existing = self.get_doc_meta(doc_meta.id)
        if existing:
            logger.warning(f"Document already exists: {doc_meta.id}")
            return False
        
        self._index.append(doc_meta)
        self._save_index()
        logger.info(f"Added document: {doc_meta.id}")
        return True
    
    def update_document(self, doc_id: str, doc_meta: DocMeta) -> bool:
        """
        Update document metadata
        
        Args:
            doc_id: Document ID to update
            doc_meta: New metadata
        
        Returns:
            True if updated successfully
        """
        for i, doc in enumerate(self._index):
            if doc.id == doc_id:
                self._index[i] = doc_meta
                self._save_index()
                logger.info(f"Updated document: {doc_id}")
                return True
        
        logger.warning(f"Document not found for update: {doc_id}")
        return False
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove document from index
        
        Args:
            doc_id: Document ID
        
        Returns:
            True if removed successfully
        """
        for i, doc in enumerate(self._index):
            if doc.id == doc_id:
                del self._index[i]
                self._save_index()
                logger.info(f"Removed document: {doc_id}")
                return True
        
        logger.warning(f"Document not found for removal: {doc_id}")
        return False
