#!/usr/bin/env python3
"""
Ingest All Knowledge Documents into ChromaDB

Usage:
    python scripts/ingest_all.py
    python scripts/ingest_all.py --clear  # Clear DB before ingesting

Philosophy: Aura's Memory Initialization
- Ingests all 4 knowledge folders
- Preserves metadata from knowledge_index.json
- Idempotent (safe to run multiple times)
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import VectorDatabase
from core.ingest import IngestionEngine


def main():
    parser = argparse.ArgumentParser(description="Ingest all knowledge documents into ChromaDB")
    parser.add_argument("--clear", action="store_true", help="Clear database before ingesting")
    parser.add_argument("--folder", type=str, help="Ingest only specific folder (db, example, mcp, standard)")
    args = parser.parse_args()
    
    # Initialize
    db = VectorDatabase()
    engine = IngestionEngine()
    
    knowledge_root = Path(__file__).parent.parent / "rag_knowledge"
    
    print("=" * 60)
    print("🔮 Aura's Memory Initialization")
    print("=" * 60)
    print(f"📂 Knowledge root: {knowledge_root}")
    print(f"💾 Vector DB: {db.persist_dir}")
    print(f"📊 Current document count: {db.count()}")
    print()
    
    # Clear if requested
    if args.clear:
        print("🗑️  Clearing existing documents...")
        db.clear()
        print(f"📊 After clear: {db.count()} documents")
        print()
    
    # Define folders to process
    if args.folder:
        folders = [args.folder]
    else:
        folders = ["db", "example", "mcp", "standard"]
    
    total_docs = 0
    
    for folder_name in folders:
        folder_path = knowledge_root / folder_name
        
        if not folder_path.exists():
            print(f"⚠️  Folder not found: {folder_path}")
            continue
        
        print(f"📁 Processing: {folder_name}/")
        
        # Get all files
        files = list(folder_path.glob("*.md")) + \
                list(folder_path.glob("*.txt")) + \
                list(folder_path.glob("*.csv"))
        
        folder_docs = 0
        
        for file_path in files:
            print(f"   📄 {file_path.name}...", end=" ")
            
            try:
                # Process file
                docs = engine.process_file(str(file_path))
                
                if docs:
                    # Upsert to DB
                    db.upsert(docs)
                    folder_docs += len(docs)
                    print(f"✅ {len(docs)} chunks")
                else:
                    print("⚠️  No chunks extracted")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"   └─ Subtotal: {folder_docs} chunks from {len(files)} files")
        print()
        total_docs += folder_docs
    
    print("=" * 60)
    print(f"✨ Ingestion complete!")
    print(f"� Total documents ingested: {total_docs}")
    print(f"� Final DB count: {db.count()}")
    print("=" * 60)
    
    # Quick sanity check
    if db.count() > 0:
        print("\n🔍 Sanity check - searching for 'voltage'...")
        results = db.search("voltage drop calculation", top_k=2)
        for r in results:
            print(f"   Score: {r['score']:.2f} | {r['source'].split('/')[-1][:40]}")


if __name__ == "__main__":
    main()
