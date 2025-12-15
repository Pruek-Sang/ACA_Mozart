 # 🎯 Quick Reference: Why Local Breaks (ทำไมเครื่องเราพัง?)

**สั้นๆ**: Codespace มี resource ดี + ML model cache → เร็ว  
Local มี resource จำกัด + ต้อง download model → ช้า + ค้าง

---

## 3 ปัญหาหลัก + วิธีแก้

### 1️⃣ FAISS Ingest ค้าง (Freezes for 10+ minutes)

**ทำไม?**
```
Sentence-transformers model = 400 MB
Codespace: Cache + fast network = download in 30s ✅
Local: First time download = 3-10 mins ❌
```

**วิธีแก้**:
- Pre-download model: `pip install sentence-transformers`
- Add progress indicator in `faiss_db.py` (show dots)
- Add timeout protection (5 min max)

---

### 2️⃣ Knowledge Files: 8 Found (Not 24!)

**ทำไม?**
```
ใน core/ingest.py:
- Old: glob("*")     ← non-recursive, เจอ top-level เท่า
- New: rglob("*")    ← recursive, เจอทุกที่ ✅
```

**วิธีแก้**:
Change 1 line in `ingest.py`:
```python
files = list(path.rglob("*"))  # rglob = recursive glob
files = [f for f in files if f.is_file()]
```

---

### 3️⃣ Vector DB Disappears After Reboot

**ทำไม?**
```
RAG service doesn't auto-check if vector_db is empty
If vector_db/ deleted or corrupted → start with 0 docs
```

**วิธีแก้**:
Add to `service.py.__init__()`:
```python
if self.db.count() == 0:
    logger.warning("Auto-ingesting knowledge base...")
    # ... run ingest_all.py code automatically ...
```

---

## 📋 Implementation Checklist

| Task | File | Lines | Status |
|------|------|-------|--------|
| Fix recursive glob | `core/ingest.py` | ~110 | 🔴 TODO |
| Add progress indicator | `core/faiss_db.py` | ~150 | 🔴 TODO |
| Add auto-init | `app/service.py` | ~95 | 🔴 TODO |
| Update .gitignore | `.gitignore` | - | 🔴 TODO |

---

## 🧪 Quick Test After Fixing

```bash
# Test 1: Should find 24+ files
python -c "from core.ingest import IngestionEngine; print(len(IngestionEngine().process_folder('rag_knowledge/db')))"

# Test 2: Should see progress
python scripts/ingest_all.py

# Test 3: Delete vector_db, run service, should auto-recover
rm -rf vector_db/
python main_ACA.py  # Should show: "Auto-ingesting..."
```

---

## 📚 Full Documentation

- **WHY_CODESPACE_VS_LOCAL.md** - Detailed technical analysis
- **PROFESSIONAL_RESOLUTION_PLAN.md** - Full implementation plan
- **SETUP_LOCAL.md** - Step-by-step user guide

---

**TL;DR**: 3 small code changes + 1 regex fix = Local works like Codespace ✅
