"""
FAISS Vector Database - Lightweight Alternative to ChromaDB
============================================================
ใช้ FAISS สำหรับ semantic search แทน ChromaDB

ข้อดี:
- เร็วมาก, ไม่กิน RAM เยอะ
- Save/Load ง่าย (ไฟล์ .index + .pkl)
- ไม่ต้อง run server

ข้อเสีย:
- ไม่มี built-in metadata filter (ทำเอง)
"""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger("Aura.FAISS")

# Lazy imports
_faiss = None
_sentence_transformer = None


def _get_faiss():
    """Lazy load faiss"""
    global _faiss
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
        except ImportError:
            raise ImportError("FAISS not installed. Run: pip install faiss-cpu")
    return _faiss


def _get_embedder():
    """Get sentence transformer for embeddings"""
    global _sentence_transformer
    if _sentence_transformer is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use same model as ChromaDB default
            _sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer: all-MiniLM-L6-v2")
        except ImportError:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
    return _sentence_transformer


class FAISSDatabase:
    """
    FAISS-based vector database with metadata support
    
    Interface compatible with existing ChromaDB usage
    """
    
    def __init__(self, persist_dir: str = "./vector_db_faiss"):
        """
        Initialize FAISS database
        
        Args:
            persist_dir: Directory to store index and metadata
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.persist_dir / "faiss.index"
        self.meta_path = self.persist_dir / "metadata.pkl"
        
        # Storage
        self.documents: List[str] = []  # Original text
        self.metadata: List[Dict[str, Any]] = []  # Metadata per doc
        self.ids: List[str] = []  # Document IDs
        self.index = None  # FAISS index
        
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        
        # Load existing if available
        self._load()
        
        logger.info(f"FAISSDatabase initialized: {len(self.documents)} documents")
    
    def _load(self) -> None:
        """Load existing index and metadata from disk"""
        faiss = _get_faiss()
        
        if self.index_path.exists() and self.meta_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                
                with open(self.meta_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
                    self.ids = data.get('ids', [])
                
                logger.info(f"Loaded {len(self.documents)} documents from disk")
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                self._init_empty_index()
        else:
            self._init_empty_index()
    
    def _init_empty_index(self) -> None:
        """Initialize empty FAISS index"""
        faiss = _get_faiss()
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product (cosine similarity)
        self.documents = []
        self.metadata = []
        self.ids = []
    
    def _save(self) -> None:
        """Save index and metadata to disk"""
        faiss = _get_faiss()
        
        faiss.write_index(self.index, str(self.index_path))
        
        with open(self.meta_path, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'ids': self.ids
            }, f)
        
        logger.debug(f"Saved {len(self.documents)} documents to disk")
    
    def _embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts"""
        embedder = _get_embedder()
        embeddings = embedder.encode(texts, normalize_embeddings=True)
        return embeddings.astype('float32')
    
    def count(self) -> int:
        """Return number of documents"""
        return len(self.documents)
    
    def clear(self) -> None:
        """Clear all documents"""
        self._init_empty_index()
        self._save()
        logger.info("Cleared all documents")
    
    def upsert(self, docs: List[Dict[str, Any]]) -> int:
        """
        Add or update documents
        
        Args:
            docs: List of dicts with 'id', 'content', 'metadata'
        
        Returns:
            Number of documents added
        """
        if not docs:
            return 0
        
        texts = []
        new_ids = []
        new_metadata = []
        
        for doc in docs:
            doc_id = doc.get('id', f"doc_{len(self.documents) + len(texts)}")
            content = doc.get('content', '')
            meta = doc.get('metadata', {})
            
            # Check if exists (update)
            if doc_id in self.ids:
                idx = self.ids.index(doc_id)
                self.documents[idx] = content
                self.metadata[idx] = meta
                # Note: FAISS doesn't support update, would need to rebuild
                # For simplicity, skip embedding update
                continue
            
            texts.append(content)
            new_ids.append(doc_id)
            new_metadata.append(meta)
        
        if texts:
            # Generate embeddings
            embeddings = self._embed(texts)
            
            # Add to index
            self.index.add(embeddings)
            
            # Store metadata
            self.documents.extend(texts)
            self.ids.extend(new_ids)
            self.metadata.extend(new_metadata)
            
            # Persist
            self._save()
        
        return len(texts)
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            filters: Optional metadata filters (e.g., {"folder": "db"})
            top_k: Number of results
        
        Returns:
            List of results with content, source, section, score
        """
        if self.count() == 0:
            logger.warning("FAISS index is empty")
            return []
        
        # Generate query embedding
        query_embedding = self._embed([query])
        
        # Search more than needed for filtering
        search_k = min(top_k * 3, self.count())
        
        scores, indices = self.index.search(query_embedding, search_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:  # FAISS returns -1 for not found
                continue
            
            meta = self.metadata[idx]
            
            # Apply filters
            if filters:
                match = True
                for key, value in filters.items():
                    if meta.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append({
                'content': self.documents[idx],
                'source': meta.get('source_path', meta.get('file_name', 'unknown')),
                'section': meta.get('folder', 'unknown'),
                'score': float(score),
                'metadata': meta
            })
            
            if len(results) >= top_k:
                break
        
        return results
    
    def get(self, limit: int = 100) -> Dict[str, Any]:
        """Get all documents (for compatibility with ChromaDB interface)"""
        return {
            'ids': self.ids[:limit],
            'documents': self.documents[:limit],
            'metadatas': self.metadata[:limit]
        }


# Singleton instance
_db_instance = None


def get_faiss_db(persist_dir: str = None) -> FAISSDatabase:
    """Get or create FAISS database instance"""
    global _db_instance
    
    if _db_instance is None:
        from app.config import settings
        persist_dir = persist_dir or str(Path(settings.VECTOR_DB_PATH).parent / "vector_db_faiss")
        _db_instance = FAISSDatabase(persist_dir)
    
    return _db_instance
