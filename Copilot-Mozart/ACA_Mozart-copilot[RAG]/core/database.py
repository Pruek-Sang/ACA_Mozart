"""
Vector Database - The Memory of Divine Knowledge
ChromaDB implementation for RAG document storage and retrieval

Philosophy: Aura's Memory Bank
- Local persistence for MVP (no external dependencies)
- Semantic search via Gemini Embedding API (ไม่กิน RAM!)
- Full text preserved with metadata
"""

import logging
import os
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
    """
    Get Embedding Function
    
    Priority:
    1. Gemini Embedding API (ไม่กิน RAM!) - ต้องมี GOOGLE_API_KEY
    2. None (ใช้ keyword search แทน) - ถ้า API key ไม่มี
    
    WARNING: ไม่ใช้ local embedding (all-MiniLM) เพราะกิน RAM มาก!
    """
    global _embedding_function
    if _embedding_function is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set - embedding disabled, will use keyword search")
            return None
        
        try:
            from chromadb.utils import embedding_functions
            # Use Gemini Embedding API - ไม่ต้องโหลด model local!
            _embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                api_key=api_key,
                model_name="models/text-embedding-004"  # Gemini embedding model
            )
            logger.info("Using Gemini Embedding API (text-embedding-004)")
        except Exception as e:
            # ⚠️ ไม่ใช้ DefaultEmbeddingFunction เพราะกิน RAM!
            logger.error(f"Gemini Embedding failed: {e}")
            logger.warning("Embedding disabled - will use keyword search as fallback")
            return None
    
    return _embedding_function


class VectorDatabase:
    """
    ChromaDB-backed vector database for RAG
    
    Features:
    - Persistent local storage (survives restarts)
    - Semantic search with Gemini Embedding API (ไม่กิน RAM!)
    - Metadata filtering (folder, group, tags)
    - Source-based deletion for re-ingestion
    
    ⚠️ WARNING: ไม่ใช้ local embedding (sentence-transformers/all-MiniLM)
               เพราะกิน RAM มาก ทำให้เครื่องค้าง!
    
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
        
        # Get embedding function (may be None if API key not set)
        embedding_fn = _get_embedding_function()
        self.embedding_enabled = embedding_fn is not None
        
        # Try loading existing collection first to avoid embedding conflict
        try:
            self.collection = self.client.get_collection(name=self.COLLECTION_NAME)
            logger.info(f"Loaded existing collection without changing embedding: {self.persist_dir}")
        except Exception:
            # Create collection (only set embedding on creation)
            if self.embedding_enabled:
                self.collection = self.client.get_or_create_collection(
                    name=self.COLLECTION_NAME,
                    embedding_function=embedding_fn,  # type: ignore[arg-type]
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"VectorDatabase initialized with Gemini Embedding: {self.persist_dir}")
            else:
                # No embedding - store documents for keyword search
                self.collection = self.client.get_or_create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.warning(f"VectorDatabase initialized WITHOUT embedding (keyword mode): {self.persist_dir}")
        
        logger.info(f"Document count: {self.collection.count()}")
    
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
        Search for relevant documents
        
        Uses:
        - Semantic search (if Gemini Embedding enabled)
        - Keyword search (fallback if no embedding)
        
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
        
        where = {k: v for k, v in filters.items()} if filters else None
        
        try:
            if self.embedding_enabled:
                return self._semantic_search(query, where, top_k)
            return self._keyword_search(query, where, top_k)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _semantic_search(
        self, query: str, where: Optional[Dict], top_k: int
    ) -> List[Dict[str, Any]]:
        """Semantic search with Gemini Embedding"""
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        output = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                output.append({
                    "content": doc,
                    "source": metadata.get("source_path", "unknown"),
                    "score": 1 - distance,
                    "metadata": metadata
                })
        
        logger.debug(f"Semantic search found {len(output)} results for: {query[:50]}...")
        return output
    
    def _keyword_search(
        self, query: str, where: Optional[Dict], top_k: int
    ) -> List[Dict[str, Any]]:
        """Keyword search fallback (no embedding)"""
        all_docs = self.collection.get(
            where=where,
            include=["documents", "metadatas"]
        )
        
        if not all_docs["documents"]:
            return []
        
        query_keywords = set(query.lower().split())
        scored_results = []
        
        for i, doc in enumerate(all_docs["documents"]):
            matches = sum(1 for kw in query_keywords if kw in doc.lower())
            score = matches / max(len(query_keywords), 1)
            if score > 0:
                scored_results.append((i, score, doc))
        
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        output = []
        for idx, score, doc in scored_results[:top_k]:
            metadata = all_docs["metadatas"][idx] if all_docs["metadatas"] else {}
            output.append({
                "content": doc,
                "source": metadata.get("source_path", "unknown"),
                "score": score,
                "metadata": metadata
            })
        
        logger.debug(f"Keyword search found {len(output)} results for: {query[:50]}...")
        return output
    
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
