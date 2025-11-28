"""
Ingestion Engine - The Gateway of Knowledge
Processes documents for vector database ingestion

Philosophy: Order from Chaos
- Parse various document formats (Markdown, TXT, CSV)
- Chunk intelligently by headers/paragraphs
- Extract metadata from knowledge_index.json
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("Aura.Ingest")


class IngestionEngine:
    """
    Document ingestion and processing for RAG knowledge base
    
    Responsibilities:
    - Read document files (Markdown, TXT, CSV)
    - Chunk content by sections (using headers)
    - Extract metadata from knowledge_index.json
    - Prepare documents for ChromaDB upsert
    
    Chunking Strategy:
    - Markdown: Split by ## headers, preserve hierarchy
    - TXT: Split by double newlines (paragraphs)
    - CSV: Each row is a chunk
    - Max chunk size: 2000 chars (with overlap)
    """
    
    MAX_CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 200
    
    def __init__(self, knowledge_index_path: Optional[str] = None):
        """
        Initialize ingestion engine
        
        Args:
            knowledge_index_path: Path to knowledge_index.json for metadata
        """
        self.knowledge_index = {}
        
        if knowledge_index_path:
            self._load_knowledge_index(knowledge_index_path)
        else:
            # Try default path
            default_path = Path(__file__).parent.parent / "rag_knowledge" / "knowledge_index.json"
            if default_path.exists():
                self._load_knowledge_index(str(default_path))
        
        logger.info(f"IngestionEngine initialized, index entries: {len(self.knowledge_index)}")
    
    def _load_knowledge_index(self, path: str) -> None:
        """Load knowledge_index.json for document metadata"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both array and object format
                if isinstance(data, list):
                    docs = data
                else:
                    docs = data.get("documents", [])
                # Build lookup by file path
                for doc in docs:
                    if "path" in doc:
                        self.knowledge_index[doc["path"]] = doc
        except Exception as e:
            logger.warning(f"Failed to load knowledge index: {e}")
    
    def _get_metadata_for_file(self, file_path: str) -> Dict[str, Any]:
        """Get metadata from knowledge_index.json for a file"""
        path = Path(file_path)
        
        # Try to find in index by relative path
        for key, meta in self.knowledge_index.items():
            if path.name == Path(key).name or str(path).endswith(key):
                # Convert tags list to comma-separated string (ChromaDB doesn't accept lists)
                tags = meta.get("tags", [])
                tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)
                return {
                    "id": meta.get("id"),
                    "group": meta.get("group"),
                    "tags": tags_str,  # String, not list!
                    "priority": meta.get("priority", 50),
                    "language": meta.get("language", "th")
                }
        
        # Default metadata
        return {"priority": 50, "language": "th", "tags": ""}
    
    def _detect_folder(self, file_path: str) -> str:
        """Detect which knowledge folder this file belongs to"""
        path_str = str(file_path).lower()
        if "/db/" in path_str:
            return "db"
        elif "/example/" in path_str:
            return "example"
        elif "/mcp/" in path_str:
            return "mcp"
        elif "/standard/" in path_str:
            return "standard"
        return "unknown"
    
    def _chunk_markdown(self, content: str) -> List[str]:
        """
        Chunk markdown by headers
        
        Strategy:
        - Split by ## (H2) headers
        - Keep H1 as context prefix
        - Merge small chunks, split large ones
        """
        chunks = []
        
        # Find H1 title for context
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        h1_title = h1_match.group(1) if h1_match else ""
        
        # Split by H2 headers
        sections = re.split(r'\n(?=##\s+)', content)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Add H1 context if section doesn't have it
            if h1_title and not section.startswith('#'):
                section = f"# {h1_title}\n\n{section}"
            
            # Split large sections
            if len(section) > self.MAX_CHUNK_SIZE:
                sub_chunks = self._split_large_chunk(section)
                chunks.extend(sub_chunks)
            else:
                chunks.append(section)
        
        return chunks
    
    def _chunk_text(self, content: str) -> List[str]:
        """Chunk plain text by paragraphs"""
        paragraphs = re.split(r'\n\n+', content)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < self.MAX_CHUNK_SIZE:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_csv(self, content: str) -> List[str]:
        """Chunk CSV - each row (or group of rows) as a chunk"""
        lines = content.strip().split('\n')
        if not lines:
            return []
        
        header = lines[0]
        chunks = []
        current_chunk = header
        
        for line in lines[1:]:
            if len(current_chunk) + len(line) < self.MAX_CHUNK_SIZE:
                current_chunk += "\n" + line
            else:
                chunks.append(current_chunk)
                current_chunk = header + "\n" + line
        
        if current_chunk and current_chunk != header:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_large_chunk(self, text: str) -> List[str]:
        """Split a large chunk with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.MAX_CHUNK_SIZE
            
            # Try to break at sentence/paragraph boundary
            if end < len(text):
                # Look for paragraph break
                break_point = text.rfind('\n\n', start, end)
                if break_point == -1:
                    # Look for sentence break
                    break_point = text.rfind('. ', start, end)
                if break_point > start:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.CHUNK_OVERLAP
        
        return chunks
    
    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a file for ingestion into VectorDB
        
        Args:
            file_path: Absolute path to file
        
        Returns:
            List of document chunks ready for VectorDatabase.upsert()
            Each dict has: content, source_path, metadata, chunk_index
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return []
        
        if not content.strip():
            logger.warning(f"Empty file: {file_path}")
            return []
        
        # Determine file type and chunk accordingly
        suffix = path.suffix.lower()
        if suffix in ['.md', '.markdown']:
            chunks = self._chunk_markdown(content)
        elif suffix == '.csv':
            chunks = self._chunk_csv(content)
        else:
            chunks = self._chunk_text(content)
        
        if not chunks:
            logger.warning(f"No chunks extracted from: {file_path}")
            return []
        
        # Get metadata
        base_metadata = self._get_metadata_for_file(file_path)
        base_metadata["folder"] = self._detect_folder(file_path)
        base_metadata["file_name"] = path.name
        
        # Build document list
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "content": chunk,
                "source_path": str(path),
                "chunk_index": i,
                "metadata": base_metadata.copy()
            })
        
        logger.info(f"Processed {file_path}: {len(documents)} chunks")
        return documents
    
    def process_folder(self, folder_path: str, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Process all files in a folder
        
        Args:
            folder_path: Path to folder
            extensions: File extensions to process (default: ['.md', '.txt', '.csv'])
        
        Returns:
            Combined list of all document chunks
        """
        if extensions is None:
            extensions = ['.md', '.txt', '.csv']
        
        folder = Path(folder_path)
        if not folder.is_dir():
            logger.error(f"Not a directory: {folder_path}")
            return []
        
        all_documents = []
        
        for ext in extensions:
            for file_path in folder.rglob(f"*{ext}"):
                docs = self.process_file(str(file_path))
                all_documents.extend(docs)
        
        logger.info(f"Processed folder {folder_path}: {len(all_documents)} total chunks")
        return all_documents
