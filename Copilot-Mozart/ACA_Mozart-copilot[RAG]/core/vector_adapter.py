"""
Vector Database Adapter
=======================
เลือก backend ได้: ChromaDB หรือ FAISS

ใช้ environment variable: VECTOR_DB_BACKEND=faiss|chroma
Default: faiss (เบากว่า)
"""

import os
import logging
from typing import List, Dict, Any, Optional, Protocol

logger = logging.getLogger("Aura.VectorDB")


class VectorDBInterface(Protocol):
    """Interface ที่ทั้ง ChromaDB และ FAISS ต้อง implement"""
    
    def count(self) -> int: ...
    def clear(self) -> None: ...
    def upsert(self, docs: List[Dict[str, Any]]) -> int: ...
    def search(self, query: str, filters: Optional[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]: ...


def get_vector_db(persist_dir: str = None) -> VectorDBInterface:
    """
    Get vector database instance based on config
    
    Environment:
        VECTOR_DB_BACKEND: 'faiss' (default) or 'chroma'
    
    Returns:
        VectorDB instance
    """
    backend = os.getenv("VECTOR_DB_BACKEND", "faiss").lower()
    
    if backend == "chroma":
        logger.info("Using ChromaDB backend")
        from core.database import VectorDatabase
        return VectorDatabase(persist_dir)
    else:
        logger.info("Using FAISS backend (lightweight)")
        from core.faiss_db import FAISSDatabase
        from app.config import settings
        from pathlib import Path
        
        # Use vector_db/faiss subdirectory (same as ingest script)
        persist_dir = persist_dir or str(Path(settings.VECTOR_DB_PATH) / "faiss")
        return FAISSDatabase(persist_dir)
