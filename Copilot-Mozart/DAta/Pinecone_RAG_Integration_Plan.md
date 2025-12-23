# 🌲 Pinecone RAG Integration Plan

> **Status:** Ready for Implementation  
> **Created:** 2025-12-23  
> **Owner:** Mozart Team

---

## 📐 Architecture: Hybrid Mode (Option C)

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  🌲 Pinecone (Cloud) - NEW CONTENT                          │
│  ─────────────────────────────────────                       │
│  • Use Cases (ตัวอย่างบ้านจริง)                              │
│  • FAQ (คำถามที่ถามบ่อย)                                     │
│  • Product Specs (อุปกรณ์รุ่นใหม่)                           │
│  • Troubleshooting (วิธีแก้ปัญหา)                            │
│                                                              │
│  Source: Firebase Storage                                    │
│  Update: API upload (ไม่ต้อง deploy)                         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  💾 FAISS (Local) - CORE KNOWLEDGE                          │
│  ─────────────────────────────────                           │
│  • db/ (Device codes, Catalog, Room templates)              │
│  • mcp/ (MCP capabilities, Error playbook)                  │
│  • standard/ (Thai_Standard, วสท. 2564)                     │
│                                                              │
│  Source: rag_knowledge/ folder in Docker                     │
│  Update: Deploy ใหม่                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Steps

### Phase 1: Setup Pinecone (5 min)
- [ ] สมัคร Pinecone ที่ https://pinecone.io (Free tier)
- [ ] สร้าง Index: `mozart-rag` (dimension=768)
- [ ] เก็บ API Key ใน GCP Secret Manager

### Phase 2: Create Indexer Script ✅ DONE
- [x] สร้าง `pinecone_indexer.py`
- **ไฟล์:** `/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/pinecone_indexer.py`

**วิธีใช้:**
```bash
# 1. ติดตั้ง dependencies
pip install pinecone-client google-cloud-storage langchain google-cloud-aiplatform

# 2. Set API Key
export PINECONE_API_KEY="your-key"

# 3. Run
python pinecone_indexer.py              # ทั้ง bucket
python pinecone_indexer.py use_cases    # เฉพาะ folder
```

### Phase 3: RAG Integration (20 min)
- [ ] สร้าง `app/adapters/pinecone_adapter.py`
- [ ] เพิ่ม Query Router logic
- [ ] Config: `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`

### Phase 4: Test & Verify (10 min)
- [ ] Test Q&A queries → Pinecone
- [ ] Test Design queries → Local FAISS
- [ ] Verify both sources work

---

## 📂 Firebase Storage Structure (Recommended)

```
aca-storage.firebasestorage.app/
├── use_cases/
│   ├── บ้านเดี่ยว_2ชั้น_ครอบครัว4คน.md
│   ├── ทาวน์เฮ้าส์_3ชั้น_home_office.md
│   └── คอนโด_studio_ไม่มีครัว.md
│
├── faq/
│   ├── ทำไมต้องใช้_RCBO.md
│   ├── ความต่าง_MCB_vs_MCCB.md
│   └── วิธีเลือกขนาดมิเตอร์.md
│
├── products/
│   ├── แอร์_Daikin_2024.md
│   └── น้ำอุ่น_Panasonic_2024.md
│
└── troubleshooting/
    ├── ปัญหา_0W_แก้ยังไง.md
    └── ปัญหา_VD_เกิน_3_เปอร์เซ็นต์.md
```

---

## 🔀 Query Router Logic

```python
def route_query(query: str) -> str:
    """Decide which vector DB to use."""
    
    # Design keywords → Local FAISS
    design_keywords = ['ออกแบบ', 'บ้าน', 'คำนวณ', 'วงจร', 'design']
    if any(kw in query.lower() for kw in design_keywords):
        return "local"
    
    # Q&A keywords → Pinecone
    qa_keywords = ['คือ', 'อะไร', 'ทำไม', 'มาตรฐาน', 'what', 'why']
    if any(kw in query.lower() for kw in qa_keywords):
        return "pinecone"
    
    # Default: Both (merge results)
    return "both"
```

---

## 💰 Cost Estimate

| Resource | Free Limit | Mozart Usage |
|----------|-----------|--------------|
| Pinecone Vectors | 100,000 | ~5,000 |
| Pinecone Queries | Unlimited | ✅ |
| Firebase Storage | 5 GB | ~50 MB |

**Total Cost: ฟรี**

---

## 🔑 Prerequisites

1. Pinecone API Key (สมัครฟรี)
2. Firebase Storage bucket: `aca-storage.firebasestorage.app`
3. GCP Secret Manager access

---

*Plan created by Valida AI - v1.0*
