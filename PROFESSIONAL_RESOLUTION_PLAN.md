# 📋 ACA_Mozart System Analysis & Professional Resolution Plan
**Status**: Codespace ✅ Working → Local ❌ Broken  
**Date**: December 10, 2025  
**Analyst**: Opsia (DevOps & Infrastructure Guardian)

---

## 🔍 Executive Summary

ระบบ ACA_Mozart มีปัญหา **3 ประเด็นหลัก** ที่ทำให้ไม่สามารถรันได้ใน Local เครื่อง แม้ว่า Codespace นั้นทำงานได้ดี:

| # | ปัญหา | Impact | สถานะ |
|---|------|--------|-------|
| 1 | **FAISS Ingestion Hang** | ค้างไม่จบเมื่อ ingest knowledge | 🔴 Critical |
| 2 | **Knowledge File Discovery** | เจอเพียง 8 files แทนที่ 24-25 | 🔴 Critical |
| 3 | **Memory Persistence** | Vector DB ไม่ persist ระหว่าง sessions | 🟡 High |

---

## 🎓 Technical Root Cause Analysis

### Problem 1: FAISS Ingestion Hangs (ค้างตรงไหน?)

**ที่ค้าง:**
```
ingest_all.py → upsert_with_batching() → db.upsert(batch) → ❌ HANG
```

**สาเหตุแท้จริง:**

ดูจากไฟล์ `core/faiss_db.py`:

```python
def upsert(self, docs: List[Dict[str, Any]]) -> int:
    """Upsert documents and save to disk"""
    embedder = _get_embedder()  # ← ตรงนี้! Lazy load sentence-transformers
    embeddings = self._embed(texts)  # ← ฝัง embedding ทำให้ CPU/Memory โหลด
    self.index.add_with_ids(embeddings, ids)
    self._save()  # ← บันทึก FAISS index ลงดิสก์ (I/O บ้าง)
```

**วัฒนาการแบบ Timeline:**

1. **ครั้งแรก (First Run)**:
   - Sentence-transformers ยังไม่ load → ตรวจ disk → โหลดจาก Hugging Face (~400 MB)
   - Download ตรง Network → Slow
   - Embedding แต่ละ batch → CPU intensive
   - บันทึก FAISS index → Disk I/O

2. **บน Codespace**:
   - Network ดี → Download sentence-transformers เร็ว
   - CPU allocation ดี → Embedding เร็ว
   - Disk SSD → Save เร็ว
   - **Result**: ✅ เสร็จใน ~2-3 นาที

3. **บน Local**:
   - Network อาจช้า → Download ติด
   - CPU/RAM อาจต่ำ → Embedding ช้า
   - Disk HDD? → Save ช้า
   - **Result**: ❌ ค้างเกิน 5+ นาที หรือ timeout

---

### Problem 2: Knowledge File Discovery (เจอแค่ 8 files?)

**สาเหตุ:**

ดูจาก `core/ingest.py:90-120`:

```python
def process_folder(self, folder_path: str, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Process all files in a folder"""
    path = Path(folder_path)
    if not path.exists():
        logger.warning(f"Folder not found: {folder_path}")
        return []  # ← ⚠️ ถ้า path ไม่เจอ จะ return []
    
    # ค้นหาไฟล์
    if extensions:
        files = [f for f in path.glob(f"*.{ext}") for ext in extensions]
    else:
        files = list(path.glob("*"))  # ← glob ระดับบนสุด เท่านั้น!
```

**Problem**:
- `glob("*")` ค้นหาเฉพาะ **top-level files เท่านั้น**
- ไม่ recurse ลงไปในโฟลเดอร์ย่อย
- ควรใช้ `glob("**/*")` หรือ `rglob("*")`

**Structure ของ rag_knowledge:**
```
rag_knowledge/
├── db/                    ← 🔍 ไม่หา subcategories ใน db/
│   ├── DEVICE_CODES.md
│   ├── ROOM_TEMPLATES.md
│   └── ...
├── example/
│   └── basic_house_example.md
├── mcp/
│   ├── MCP_CAPABILITIES_AND_LIMITS.md
│   └── ...
└── standard/
    ├── TIS_648_Thai_Wiring.md
    └── ...
```

**บน Codespace**:
- ก่อนหน้านี้อาจใช้ `VectorDatabase` (ChromaDB) ที่ handle recursion ได้อัตโนมัติ
- พอเปลี่ยนเป็น FAISS → ใช้ `IngestionEngine` → ตรวจสอบ path literal

**บน Local**:
- Path อาจเป็น Windows (backslash) หรือ relative path → glob ไม่เจอ
- PYTHONPATH ไม่ setup → Path resolver ผิด

---

### Problem 3: Memory Persistence (Vector DB หายหลังรีบูต?)

**ปัญหา:**
- FAISS index เก็บบน disk ที่ `vector_db/faiss/`
- แต่ถ้า `vector_db/` directory ไม่ exist → FAISS สร้างใหม่ (empty)
- RAG service ไม่ทำ auto-ingest → เริ่มด้วย vector DB ว่าง

**ส่วนหลัก (config.py)**:
```python
VECTOR_DB_PATH: str = str(BASE_DIR / "vector_db")

def model_post_init(self):
    object.__setattr__(self, 'VECTOR_DB_PATH', resolve_path(self.VECTOR_DB_PATH))
```

**ปัญหา**:
- Path resolve ถูกต้อง
- แต่ `faiss_db.py` ไม่ auto-ingest หลังจาก init
- ต้องรัน `scripts/ingest_all.py` **ทุกครั้ง** หลังจากซื้อเครื่องใหม่ หรือ directory เสีย

---

## 💡 Professional Resolution Plan

### 🔧 Fix 1: Add FAISS Ingest Timeout & Progress Monitoring

**ไฟล์**: `core/faiss_db.py`

**สิ่งที่ต้องทำ**:
```python
# เพิ่ม timeout protection สำหรับ embedding layer
# เพิ่ม progress indicator ให้ user รู้ว่ากำลังทำงาน

class FAISSDatabase:
    def __init__(self, persist_dir: str = "./vector_db_faiss", embedding_timeout: int = 300):
        self.embedding_timeout = embedding_timeout  # 5 นาที max
        # ... rest of init
    
    def upsert(self, docs: List[Dict[str, Any]]) -> int:
        """Upsert with progress indicator"""
        print(f"📦 Upserting {len(docs)} documents...")
        
        for idx, doc in enumerate(docs):
            # Print progress every 5 docs
            if idx % 5 == 0:
                print(f"  ⏳ Processing {idx}/{len(docs)}...")
            
            # Embed with timeout
            try:
                embedding = self._embed_with_timeout([doc['content']], timeout=self.embedding_timeout)
            except TimeoutError:
                print(f"  ⚠️  Timeout on document {idx}, skipping...")
                continue
```

---

### 🔧 Fix 2: Fix Knowledge File Discovery (Recursive Glob)

**ไฟล์**: `core/ingest.py`

**เปลี่ยนจาก:**
```python
files = list(path.glob("*"))  # ❌ Non-recursive
```

**เป็น:**
```python
# Recursive glob ที่ support nested folders
if extensions:
    files = []
    for ext in extensions:
        files.extend(path.rglob(f"*.{ext}"))  # ✅ Recursive
else:
    files = list(path.rglob("*"))  # ✅ Recursive, all files
    files = [f for f in files if f.is_file()]  # Filter out directories
```

---

### 🔧 Fix 3: Add Persistent Vector DB Auto-Initialization

**ไฟล์**: `app/service.py` (RagService.__init__)

**เพิ่มหลังจากสร้าง vector_db**:
```python
def __init__(self):
    from core.vector_adapter import get_vector_db
    self.db = get_vector_db()
    
    # ✅ New: Auto-check if vector DB is empty
    if self.db.count() == 0:
        logger.warning("⚠️  Vector DB is empty! Ingesting knowledge base...")
        try:
            from core.ingest import IngestionEngine
            engine = IngestionEngine()
            
            knowledge_root = Path(settings.KNOWLEDGE_ROOT)
            for folder in ["db", "example", "mcp", "standard"]:
                folder_path = knowledge_root / folder
                docs = engine.process_folder(str(folder_path))
                if docs:
                    self.db.upsert(docs)
                    logger.info(f"✅ Ingested {len(docs)} from {folder}/")
        except Exception as e:
            logger.error(f"❌ Auto-ingest failed: {e}")
            raise
```

---

### 📦 Fix 4: Add .gitignore Entries (ไม่ commit vector DB)

**ไฟล์**: `.gitignore` ที่ root

**เพิ่มเติม:**
```bash
# Vector Database (too large, rebuild on each machine)
vector_db/
vector_db_faiss/

# FAISS index files
*.faiss
*.pkl

# Embedding cache
*.pickle

# Logs
logs/
*.log

# Test artifacts
.pytest_cache/
__pycache__/
*.pyc
```

---

### 🎯 Fix 5: Add Better Documentation for Local Setup

**ไฟล์ใหม่**: `SETUP_LOCAL.md`

```markdown
# Local Development Setup Guide

## Prerequisites
- Python 3.11+
- 8 GB RAM minimum
- 2 GB free disk space

## Initial Setup

### Step 1: Install Dependencies
\`\`\`bash
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/
pip install -r requirements.txt
# or for lightweight setup:
pip install -r Docker/requirements_light.txt
\`\`\`

### Step 2: Initialize Knowledge Base (CRITICAL!)
\`\`\`bash
# This takes 3-5 minutes on first run
python scripts/ingest_all.py

# Watch progress - should see dots (....) as it processes
# Final output should show ~24-25 documents ingested
\`\`\`

### Step 3: Verify Setup
\`\`\`bash
# Check vector DB was created
ls -la vector_db/faiss/

# Should see:
# - faiss.index (MB-sized)
# - metadata.pkl (KB-sized)
\`\`\`

### Step 4: Run RAG Service
\`\`\`bash
# Terminal 1: Run MCP Core
cd mcp_core_v2
python main.py  # Starts on port 5001

# Terminal 2: Run RAG Service
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/
python main_ACA.py  # Starts on port 8080

# Test:
curl http://localhost:8080/
# Should return: {"service": "Mozart RAG Spec Engine", ...}
\`\`\`

## Troubleshooting

### Issue: Ingest Hangs
- **Cause**: Downloading sentence-transformers (~400 MB)
- **Solution**: Be patient (3-5 minutes). Monitor with `top` command.
- **Workaround**: Pre-download: `pip install sentence-transformers`

### Issue: Only 8 files found instead of 24
- **Cause**: Path resolution or glob not recursive
- **Solution**: Run with debug: `python scripts/ingest_all.py --debug`

### Issue: Vector DB empty after reboot
- **Cause**: `vector_db/` directory not created or permissions
- **Solution**: 
  ```bash
  mkdir -p vector_db/faiss
  python scripts/ingest_all.py --clear
  ```
```

---

## 📊 Impact Summary

| Fix | File | Impact | Priority |
|-----|------|--------|----------|
| 1 | `faiss_db.py` | Add timeout + progress | 🔴 Critical |
| 2 | `ingest.py` | Fix recursive glob | 🔴 Critical |
| 3 | `service.py` | Auto-initialize | 🟡 High |
| 4 | `.gitignore` | Don't commit vector_db | 🟡 High |
| 5 | `SETUP_LOCAL.md` | Documentation | 🟢 Medium |

---

## 🚀 Recommended Implementation Order

1. **Start with Fix 2** (ingest.py glob) - easiest, no dependencies
2. **Then Fix 1** (faiss_db.py timeout) - critical for UX
3. **Then Fix 3** (service.py auto-init) - prevents empty DB issue
4. **Then Fix 4** (.gitignore) - cleanliness
5. **Finally Fix 5** (SETUP_LOCAL.md) - documentation

---

## 🧪 Testing Strategy

### Unit Test Checklist
```bash
# 1. Test ingestion
python -c "from core.ingest import IngestionEngine; e = IngestionEngine(); d = e.process_folder('rag_knowledge/db'); print(f'Found {len(d)} chunks')"

# 2. Test FAISS upsert
python -c "from core.faiss_db import get_faiss_db; db = get_faiss_db(); print(f'DB count: {db.count()}')"

# 3. Test RAG service init
python -c "from app.service import RagService; r = RagService(); print(f'Service initialized, KB has {len(r.knowledge.list_docs())} docs')"
```

### Integration Test
```bash
# Run full ingest pipeline
python scripts/ingest_all.py --clear

# Check results
sqlite3 vector_db/faiss/metadata.pkl ".schema"  # or just check file size
```

---

## 📝 Implementation Checklist

Before fixing, confirm:

- [ ] Read this entire document
- [ ] Understand root causes (not just symptoms)
- [ ] Check current state of files locally
- [ ] Backup current state
- [ ] Implement fixes in order
- [ ] Test each fix individually
- [ ] Run full regression test
- [ ] Update SETUP_LOCAL.md
- [ ] Commit with clear messages

---

*Prepared by Opsia - DevOps & Infrastructure Guardian*  
*Status: Ready for implementation approval*
