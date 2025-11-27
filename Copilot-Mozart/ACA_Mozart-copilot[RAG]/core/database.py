"""
Vector Database - The Memory of Divine Knowledge
ChromaDB implementation for RAG document storage and retrieval

Philosophy: Aura's Memory Bank
- Local persistence for MVP (no external dependencies)
- Semantic search via sentence-transformers
- Full text preserved with metadata
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger("Aura.VectorDB")

# Lazy imports for ChromaDB (installed separately)
_chromadb = None
_embedding_function = None


def _get_chromadb():
    """Lazy load chromadb to avoid import errors if not installed"""
    global _chromadb
    if _chromadb is None:
        try:
            import chromadb
            _chromadb = chromadb
        except ImportError:
            raise ImportError(
                "ChromaDB not installed. Run: pip install chromadb"
            )
    return _chromadb


def _get_embedding_function():
    """Lazy load embedding function"""
    global _embedding_function
    if _embedding_function is None:
        try:
            from chromadb.utils import embedding_functions
            # Use default all-MiniLM-L6-v2 (fast, good quality)
            _embedding_function = embedding_functions.DefaultEmbeddingFunction()
        except ImportError:
            raise ImportError(
                "ChromaDB embedding not available. Run: pip install chromadb"
            )
    return _embedding_function


class VectorDatabase:
    """
    ChromaDB-backed vector database for RAG
    
    Features:
    - Persistent local storage (survives restarts)
    - Semantic search with sentence-transformers
    - Metadata filtering (folder, group, tags)
    - Source-based deletion for re-ingestion
    
    Collection schema:
    - id: md5 hash of source_path + chunk_index
    - document: text content
    - metadata: {source_path, folder, group, chunk_index, ...}
    """
    
    COLLECTION_NAME = "rag_knowledge"
    
    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize ChromaDB connection
        
        Args:
            persist_dir: Directory for persistent storage
                        Defaults to ./vector_db
        """
        chromadb = _get_chromadb()
        
        if persist_dir is None:
            persist_dir = str(Path(__file__).parent.parent / "vector_db")
        
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Get or create collection with embedding function
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=_get_embedding_function(),
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        logger.info(
            f"VectorDatabase initialized: {self.persist_dir}, "
            f"documents={self.collection.count()}"
        )
    
    def _generate_id(self, source_path: str, chunk_index: int = 0) -> str:
        """Generate deterministic ID from source and chunk index"""
        content = f"{source_path}::{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant documents
        
        Args:
            query: Natural language query
            filters: Metadata filters (e.g., {"folder": "db"})
            top_k: Number of results to return
        
        Returns:
            List of results with keys: content, source, score, metadata
        """
        if self.collection.count() == 0:
            logger.warning("Search on empty collection")
            return []
        
        # Build where clause from filters
        where = None
        if filters:
            # ChromaDB where syntax
            where = {k: v for k, v in filters.items()}
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count()),
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Transform to standard format
            output = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    output.append({
                        "content": doc,
                        "source": metadata.get("source_path", "unknown"),
                        "score": 1 - distance,  # Convert distance to similarity
                        "metadata": metadata
                    })
            
            logger.debug(f"Search found {len(output)} results for: {query[:50]}...")
            return output
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def upsert(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Insert or update documents
        
        Args:
            documents: List of dicts with keys:
                - content: str (required)
                - source_path: str (required)
                - metadata: dict (optional, e.g., folder, group)
                - chunk_index: int (optional, default 0)
        
        Returns:
            True if successful
        """
        if not documents:
            logger.warning("Upsert called with empty documents")
            return True
        
        try:
            ids = []
            texts = []
            metadatas = []
            
            for doc in documents:
                chunk_index = doc.get("chunk_index", 0)
                source_path = doc.get("source_path", "unknown")
                
                doc_id = self._generate_id(source_path, chunk_index)
                ids.append(doc_id)
                texts.append(doc["content"])
                
                # Build metadata
                meta = doc.get("metadata", {}).copy()
                meta["source_path"] = source_path
                meta["chunk_index"] = chunk_index
                metadatas.append(meta)
            
            # ChromaDB upsert
            self.collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Upserted {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return False
    
    def delete_source(self, source_path: str) -> bool:
        """
        Delete all documents from a source path
        
        Args:
            source_path: Exact source path to delete
        
        Returns:
            True if successful
        """
        try:
            # ChromaDB delete by metadata filter
            self.collection.delete(
                where={"source_path": source_path}
            )
            logger.info(f"Deleted documents from: {source_path}")
            return True
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def count(self) -> int:
        """Get total document count"""
        return self.collection.count()
    
    def clear(self) -> bool:
        """Delete all documents (for testing)"""
        try:
            # Get all IDs and delete
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)
            logger.info("Cleared all documents")
            return True
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            return False
