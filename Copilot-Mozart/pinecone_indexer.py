#!/usr/bin/env python3
"""
Pinecone Indexer - Upload documents from Firebase Storage to Pinecone

Usage:
    # Set environment variables first
    export PINECONE_API_KEY="your-key"
    export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
    
    # Run
    python pinecone_indexer.py
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "mozart-rag"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

FIREBASE_BUCKET = "aca-storage.firebasestorage.app"

# Embedding config
EMBEDDING_MODEL = "textembedding-gecko@003"
EMBEDDING_DIM = 768
GCP_PROJECT = "gen-lang-client-0658701327"
GCP_LOCATION = "us-central1"

# Chunking config
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


# ═══════════════════════════════════════════════════════════════
# Dependencies (install: pip install pinecone-client google-cloud-storage langchain vertexai)
# ═══════════════════════════════════════════════════════════════

def check_dependencies():
    """Check if required packages are installed."""
    missing = []
    try:
        import pinecone
    except ImportError:
        missing.append("pinecone-client")
    try:
        from google.cloud import storage
    except ImportError:
        missing.append("google-cloud-storage")
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        missing.append("langchain")
    try:
        import vertexai
    except ImportError:
        missing.append("google-cloud-aiplatform")
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"   Run: pip install {' '.join(missing)}")
        return False
    return True


# ═══════════════════════════════════════════════════════════════
# Firebase Storage Functions
# ═══════════════════════════════════════════════════════════════

def list_firebase_files(bucket_name: str, prefix: str = "") -> List[str]:
    """List all .md files from Firebase Storage bucket."""
    from google.cloud import storage
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    md_files = [blob.name for blob in blobs if blob.name.endswith('.md')]
    print(f"📁 Found {len(md_files)} markdown files in {bucket_name}/{prefix}")
    return md_files


def download_file_content(bucket_name: str, file_path: str) -> str:
    """Download file content from Firebase Storage."""
    from google.cloud import storage
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    
    return blob.download_as_text()


# ═══════════════════════════════════════════════════════════════
# Chunking Functions
# ═══════════════════════════════════════════════════════════════

def chunk_document(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Split document into chunks with metadata."""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    
    chunks = splitter.split_text(text)
    
    return [
        {
            "text": chunk,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        }
        for i, chunk in enumerate(chunks)
    ]


# ═══════════════════════════════════════════════════════════════
# Embedding Functions
# ═══════════════════════════════════════════════════════════════

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings using Vertex AI."""
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
    
    embeddings = []
    batch_size = 5  # Vertex AI limit
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        results = model.get_embeddings(batch)
        embeddings.extend([r.values for r in results])
    
    return embeddings


# ═══════════════════════════════════════════════════════════════
# Pinecone Functions
# ═══════════════════════════════════════════════════════════════

def init_pinecone():
    """Initialize Pinecone and create index if needed."""
    from pinecone import Pinecone, ServerlessSpec
    
    if not PINECONE_API_KEY:
        raise ValueError("❌ PINECONE_API_KEY not set!")
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Create index if not exists
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"📦 Creating index '{PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION)
        )
    
    return pc.Index(PINECONE_INDEX_NAME)


def upsert_to_pinecone(index, vectors: List[Dict[str, Any]]):
    """Upload vectors to Pinecone."""
    batch_size = 100
    
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"   ✅ Upserted {min(i+batch_size, len(vectors))}/{len(vectors)}")


# ═══════════════════════════════════════════════════════════════
# Main Pipeline
# ═══════════════════════════════════════════════════════════════

def index_firebase_to_pinecone(folder_prefix: str = ""):
    """Main pipeline: Firebase -> Chunk -> Embed -> Pinecone"""
    
    print("=" * 60)
    print("🌲 Pinecone Indexer for Mozart RAG")
    print("=" * 60)
    
    # 1. Check deps
    if not check_dependencies():
        return
    
    # 2. Init Pinecone
    print("\n📡 Connecting to Pinecone...")
    index = init_pinecone()
    print(f"   ✅ Connected to index '{PINECONE_INDEX_NAME}'")
    
    # 3. List files
    print(f"\n📂 Listing files from Firebase Storage...")
    files = list_firebase_files(FIREBASE_BUCKET, folder_prefix)
    
    if not files:
        print("❌ No files found!")
        return
    
    # 4. Process each file
    all_vectors = []
    
    for file_path in files:
        print(f"\n📄 Processing: {file_path}")
        
        # Download
        content = download_file_content(FIREBASE_BUCKET, file_path)
        print(f"   📥 Downloaded {len(content)} chars")
        
        # Chunk
        metadata = {
            "source": file_path,
            "bucket": FIREBASE_BUCKET,
            "type": file_path.split("/")[0] if "/" in file_path else "general"
        }
        chunks = chunk_document(content, metadata)
        print(f"   ✂️  Split into {len(chunks)} chunks")
        
        # Embed
        texts = [c["text"] for c in chunks]
        embeddings = get_embeddings(texts)
        print(f"   🧠 Got {len(embeddings)} embeddings")
        
        # Prepare vectors
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{file_path.replace('/', '_')}_{i}"
            all_vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    **chunk["metadata"],
                    "text": chunk["text"][:1000]  # Pinecone metadata limit
                }
            })
    
    # 5. Upload to Pinecone
    print(f"\n🚀 Uploading {len(all_vectors)} vectors to Pinecone...")
    upsert_to_pinecone(index, all_vectors)
    
    print("\n" + "=" * 60)
    print("✅ DONE! All documents indexed to Pinecone")
    print(f"   Index: {PINECONE_INDEX_NAME}")
    print(f"   Vectors: {len(all_vectors)}")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    folder = sys.argv[1] if len(sys.argv) > 1 else ""
    index_firebase_to_pinecone(folder)
