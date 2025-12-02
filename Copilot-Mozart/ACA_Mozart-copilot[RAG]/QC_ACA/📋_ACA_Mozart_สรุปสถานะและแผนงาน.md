# 📋 ACA Mozart - สรุปสถานะและแผนงาน

> **Updated:** 2025-12-02  
> **Status:** Phase 1-3 Complete, Phase 4 Pending  
> **Tests:** 40 passed, 2 skipped

---

## 🏗️ สถาปัตยกรรมระบบ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ACA Mozart Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   👤 User                                                                    │
│     │                                                                        │
│     ▼                                                                        │
│  ┌──────────────────┐                                                        │
│  │   Gateway        │  Port 8000                                             │
│  │  gate_way_new.py │  Intent Router (LLM + Regex)                          │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│     ┌─────┴─────┐                                                            │
│     ▼           ▼                                                            │
│  MOZART      AMADEUS                                                         │
│  (Technical) (Chat)                                                          │
│     │                                                                        │
│     ▼                                                                        │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     │
│  │   RAG (Aura)     │────▶│   MCP Adapter    │────▶│   MCP Core       │     │
│  │   Port 8080      │     │   mcp_adapter.py │     │   Port 5001      │     │
│  │                  │     │                  │     │                  │     │
│  │ • NLP/Thai       │     │ • Device→Watts   │     │ • NEC Calc       │     │
│  │ • Knowledge RAG  │     │ • Voltage Map    │     │ • Wire Sizing    │     │
│  │ • Spec Gen       │     │ • Schema Convert │     │ • Breaker Select │     │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘     │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │   ChromaDB       │  Vector Database                                       │
│  │   vector_db/     │  (ต้อง ingest ก่อนใช้งาน)                              │
│  └──────────────────┘                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 โครงสร้างไฟล์และหน้าที่

### 🔷 RAG Service (`Copilot-Mozart/ACA_Mozart-copilot[RAG]/`)

| ไฟล์ | หน้าที่ | สถานะ |
|------|---------|--------|
| **`app/routes.py`** | FastAPI endpoints (`/ask`, `/mcp_spec`, `/design`) | ✅ Done |
| **`app/service.py`** | Business logic - RAG retrieval + LLM spec generation | ✅ Done |
| **`app/models.py`** | Pydantic data models (ProjectInputSpec, LoadSpec, etc.) | ✅ Done |
| **`app/knowledge_service.py`** | Knowledge retrieval จาก ChromaDB + fallback | ✅ Done |
| **`app/config.py`** | Settings (ports, API keys, timeouts) | ✅ Done |
| **`app/mcp_adapter.py`** | **แปลง RAG → MCP** (device codes → watts) | ✅ NEW |
| **`app/mcp_client.py`** | **HTTP Client เรียก MCP Core API** | ✅ NEW |
| **`app/session_store.py`** | **Multi-turn conversation memory** | ✅ NEW |
| **`app/trust_log.py`** | Audit logging สำหรับ debug | ✅ Done |
| `gate_way_new.py` | Intent router (MOZART/AMADEUS) | ✅ Done |
| `main_ACA.py` | Entry point (uvicorn) | ✅ Done |

### 🔷 MCP Core (`mcp_core_v2/`)

| ไฟล์ | หน้าที่ | สถานะ |
|------|---------|--------|
| **`api.py`** | **FastAPI wrapper สำหรับ pipeline** | ✅ NEW |
| `pipeline.py` | MCPipeline - orchestrate calculations | ✅ Done |
| `wire_sizer.py` | Wire sizing ตาม NEC | ✅ Done |
| `breaker_selector.py` | Breaker selection | ✅ Done |
| `models/contracts.py` | Data contracts (DesignRequest, etc.) | ✅ Done |

### 🔷 Knowledge Base (`rag_knowledge/`)

| Folder | เนื้อหา |
|--------|---------|
| `db/` | Device codes, Room templates, Catalog |
| `mcp/` | MCP capabilities, quality rules |
| `standard/` | Thai electrical standards (วสท.) |
| `example/` | Few-shot examples |

### 🔷 Tests (`tests/`)

| ไฟล์ | ทดสอบอะไร | สถานะ |
|------|-----------|--------|
| `test_models.py` | Pydantic models | ✅ 6 passed |
| `test_mcp_adapter.py` | Device/voltage mapping | ✅ 19 passed |
| `test_e2e_integration.py` | End-to-end flow (mocked) | ✅ 7 passed |
| `test_folder_based.py` | Knowledge + LLM | ✅ 8 passed |

---

## ✅ สิ่งที่ทำเสร็จแล้ว (Phase 1-3)

### Phase 1: MCP Adapter ✅
```
app/mcp_adapter.py
├── DEVICE_MAPPING: AC-12000BTU → 1200W, SOCKET-OUTLET → 180W
├── VOLTAGE_MAPPING: TH_1PH_230V → 240V_1PH (NEC)
├── McpAdapter.convert(): ProjectInputSpec → McpDesignRequest
└── 19 unit tests passed
```

### Phase 2: MCP Client ✅
```
app/mcp_client.py
├── McpClient.design(): async HTTP call to MCP Core
├── McpClient.health_check(): check if MCP alive
├── Timeout + error handling
└── McpDesignResponse wrapper
```

### Phase 3: Route Integration ✅
```
app/routes.py
├── POST /api/v1/ask → QA about standards
├── POST /api/v1/mcp_spec → Generate ProjectInputSpec
├── POST /api/v1/design → NEW: Full flow RAG→Adapter→MCP
└── GET /api/v1/health
```

### MCP Core API ✅
```
mcp_core_v2/api.py
├── POST /api/v1/design → Calculate wire/breaker sizing
├── GET /health
└── Mock mode when dependencies unavailable
```

---

## ⏳ สิ่งที่ค้างอยู่

### 1. 🔴 **Ingest Knowledge** (ต้องทำก่อน run)
```bash
cd /home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]
python scripts/ingest_all.py
```
- ถ้า vector_db/ ว่าง RAG จะตอบไม่ได้

### 2. 🟡 **Phase 4: Session Integration** (Optional)
```
app/session_store.py  ← พร้อมแล้ว แต่ยังไม่ wire
app/routes.py         ← ต้องเพิ่ม session endpoints

Tasks:
- เพิ่ม POST /api/v1/session/create
- เพิ่ม GET /api/v1/session/{id}
- แก้ /api/v1/ask ให้รับ session_id
```

### 3. 🟡 **MCP Core Dependencies**
```
mcp_core_v2/api.py ใช้ mock mode เพราะ:
- ไม่มี supabase package
- ไม่มี pandapower (ถ้าต้องการ real calc)

ถ้าต้องการ real calculations:
pip install supabase pandapower
```

### 4. 🟢 **Live Integration Test**
```bash
# Terminal 1: RAG
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]
python scripts/ingest_all.py  # ← ต้องทำก่อน!
uvicorn app.routes:app --port 8080

# Terminal 2: MCP
cd mcp_core_v2
python api.py  # port 5001

# Terminal 3: Gateway
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]
uvicorn gate_way_new:app --port 8000

# Test
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "ออกแบบไฟฟ้าบ้าน 2 ชั้น มี 3 ห้องนอน"}'
```

---

## 🔄 Data Flow (End-to-End)

```
1. User: "ออกแบบไฟฟ้าบ้าน 2 ชั้น 3 ห้องนอน"
                    │
                    ▼
2. Gateway (port 8000)
   - LLM classify intent → MOZART (technical)
   - Route to RAG
                    │
                    ▼
3. RAG /api/v1/design (port 8080)
   │
   ├─► KnowledgeService.retrieve()
   │   └─► ChromaDB query → relevant docs
   │
   ├─► LLM: Generate ProjectInputSpec
   │   {
   │     project_info: {name, type},
   │     rooms: [{room_id: "R1", name: "ห้องนอน", ...}],
   │     loads: [{load_id: "L1", device_code: "AC-12000BTU", ...}]
   │   }
   │
   ├─► McpAdapter.convert()
   │   - "AC-12000BTU" → {power_watts: 1200, load_type: "hvac"}
   │   - "TH_1PH_230V" → "240V_1PH"
   │
   └─► McpClient.design() → MCP Core
                    │
                    ▼
4. MCP Core /api/v1/design (port 5001)
   │
   ├─► WireSizer: Calculate wire sizes (NEC 310.15)
   ├─► BreakerSelector: Select breakers
   ├─► ConduitSizer: Size conduits
   │
   └─► Return:
       {
         wire_sizing: {"L1": "4.0 mm²"},
         breaker_selections: {"L1": 20},
         autolisp_code: "(defun c:DRAW-PANEL ...)"
       }
                    │
                    ▼
5. User ได้รับผลลัพธ์
```

---

## 📊 Test Status

```
Total: 40 passed, 2 skipped

tests/test_models.py           6 passed   ✅
tests/test_mcp_adapter.py     19 passed   ✅
tests/test_e2e_integration.py  7 passed   ✅ (2 skipped - need live MCP)
tests/test_folder_based.py     8 passed   ✅
```

---

## 🎯 Next Steps (Priority Order)

| # | Task | Command/File | Est. Time |
|---|------|--------------|-----------|
| 1 | **Ingest knowledge** | `python scripts/ingest_all.py` | 2 min |
| 2 | Run RAG | `uvicorn app.routes:app --port 8080` | - |
| 3 | Run MCP | `python mcp_core_v2/api.py` | - |
| 4 | Test E2E | `curl localhost:8080/api/v1/design` | 5 min |
| 5 | Phase 4: Session | Wire `session_store.py` to routes | 30 min |

---

## 📎 Quick Reference

### Ports
| Service | Port |
|---------|------|
| Gateway | 8000 |
| RAG (Aura) | 8080 |
| MCP Core | 5001 |

### Key Files to Edit
| ต้องการทำ | แก้ไฟล์ |
|-----------|---------|
| เพิ่ม device code | `app/mcp_adapter.py` → DEVICE_MAPPING |
| เพิ่ม endpoint | `app/routes.py` |
| แก้ LLM prompt | `app/service.py` |
| เพิ่ม knowledge | `rag_knowledge/` + run ingest |
| แก้ MCP calc | `mcp_core_v2/wire_sizer.py` |

---

## 📂 Git Status

### Latest Commits (Pushed to GitHub)
```
7996681 feat(mcp_core_v2): Add FastAPI wrapper for MCP Core pipeline
5d76763 feat: Add MCP Adapter, Client, and Session integration (Phase 1-3)
```

### Files Committed
- `app/mcp_adapter.py` ✅
- `app/mcp_client.py` ✅
- `app/session_store.py` ✅
- `app/config.py` ✅
- `app/routes.py` ✅
- `gate_way_new.py` ✅
- `tests/test_e2e_integration.py` ✅
- `tests/test_mcp_adapter.py` ✅
- `mcp_core_v2/api.py` ✅
- `ACA_Implementation_Plan.md` ✅
- `ACA_Project_Understanding.md` ✅

---

## 🔗 Related Documents

| Document | Location | Description |
|----------|----------|-------------|
| Implementation Plan | `ACA_Implementation_Plan.md` | 4-phase roadmap detail |
| Architecture Doc | `ACA_Project_Understanding.md` | System design overview |
| MCP Understanding | `QC_ACA/MCP_Understanding.md` | MCP Core internals |
| Design Guide | `QC_ACA/📜How to Design ACA_Mozart(new ver.).txt` | Original design spec |

---

## ⚠️ Critical Reminders

### Role Separation (ห้ามสลับ!)
```
RAG (Aura) DOES:              MCP Core (Amadeus) DOES:
─────────────────────         ──────────────────────────
✅ Parse human language       ✅ NEC calculations
✅ Retrieve knowledge         ✅ Wire sizing
✅ Generate structured spec   ✅ Breaker selection
✅ Validate device codes      ✅ Conduit sizing
✅ Map room→load              ✅ Voltage drop calc
                              ✅ Generate AutoLISP

RAG DOES NOT:                 MCP DOES NOT:
──────────────                ─────────────
❌ Calculate wire sizes       ❌ Understand Thai
❌ Do voltage drop math       ❌ Parse natural language
❌ Select breakers            ❌ Retrieve documents
❌ Generate DXF/AutoLISP      ❌ Handle "บ้าน 2 ชั้น"
```

### Validation Checklist (Before Deploy)
```
□ Port 8080 = RAG only
□ Port 5001 = MCP only  
□ RAG output = ProjectInputSpec (not watts, not amps)
□ MCP input = DesignRequest (watts, voltage type)
□ Device codes validated against DEVICE_CODES.md
□ Room IDs sequential (R1, R2, ...)
□ All existing tests pass
□ vector_db/ has been ingested
```
