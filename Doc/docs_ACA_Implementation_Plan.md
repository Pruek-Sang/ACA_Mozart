# Source: ACA_Implementation_Plan.md

```md
# 📋 ACA Mozart - Implementation Plan & Audit Report
> **Generated:** 2024-12-02  
> **Status:** Pre-Implementation Analysis  
> **Scope:** RAG (Aura) + MCP Core v2 (Amadeus) Integration

---

## 📑 Table of Contents
1. [สิ่งที่ยังขาดในการทำให้แผนเป็นรูปเป็นร่าง](#1-missing-components)
2. [ยืนยันการทำ Adapter](#2-adapter-confirmation)
3. [จุดที่ต้อง Debug เป็นพิเศษ](#3-debug-points)
4. [Audit: ไฟล์ที่ไม่เกี่ยวข้อง](#4-file-audit)
5. [แผนการทำงานต่อ](#5-implementation-plan)
6. [การป้องกัน Regression](#6-regression-protection)
7. [Critical Reminders](#7-critical-reminders)

---

## 1. Missing Components
### สิ่งที่ยังขาดในการทำให้แผนเป็นรูปเป็นร่าง

```
┌─────────────────────────────────────────────────────────────────┐
│                    Current State vs Target                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ EXISTS (OK)           │  ❌ MISSING (ต้องสร้าง)              │
│  ─────────────────────────┼──────────────────────────────────── │
│  app/models.py            │  app/mcp_adapter.py                 │
│  app/service.py           │  app/mcp_client.py                  │
│  app/routes.py            │  routes: /api/v1/design             │
│  app/session_store.py     │  session integration in routes      │
│  app/knowledge_service.py │  (end-to-end test script)           │
│  app/trust_log.py         │                                     │
│  app/config.py            │                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 Missing Files to Create

| Priority | File | Purpose | Estimated Lines |
|----------|------|---------|-----------------|
| 🔴 P0 | `app/mcp_adapter.py` | Convert RAG → MCP data format | ~150 |
| 🔴 P0 | `app/mcp_client.py` | HTTP client to call MCP Core | ~80 |
| 🟡 P1 | Route updates in `app/routes.py` | Add `/api/v1/design` endpoint | ~50 |
| 🟢 P2 | Session integration | Wire session_store into routes | ~30 |

### 1.2 Integration Points Needed

```
┌─────────────────────────────────────────────────────────────────┐
│                  DATA FLOW GAP ANALYSIS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RAG Output (ProjectInputSpec)                                  │
│  ├── project_info: {name, type}                                 │
│  ├── electrical_system: {voltage, phases}                       │
│  ├── rooms: [{room_id, name, type, loads[]}]                    │
│  └── constraints: [strings]                                     │
│                         │                                       │
│                         ▼                                       │
│              ┌─────────────────────┐                            │
│              │  ❌ mcp_adapter.py  │  ← MISSING!                │
│              │  (Transformation)   │                            │
│              └─────────────────────┘                            │
│                         │                                       │
│                         ▼                                       │
│  MCP Input (DesignRequest)                                      │
│  ├── loads: [{name, power_watts, voltage, load_type}]           │
│  ├── panels: [{name, bus_voltage, max_circuits}]                │
│  └── service_voltage: SINGLE_PHASE_240V                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Adapter Confirmation
### ยืนยัน: ต้องทำ Adapter แน่นอน

### 2.1 ทำไมต้องมี Adapter?

| RAG (Aura) | MCP Core (Amadeus) | ต่างกันตรงไหน |
|------------|-------------------|---------------|
| `device_code: "AC-12000BTU"` | `power_watts: 1500, load_type: HVAC` | RAG ใช้ code, MCP ใช้ numeric |
| `voltage_system: "TH_1PH_230V"` | `VoltageType.SINGLE_PHASE_240V` | NEC uses 240V standard |
| `room.loads: []` | `loads: []` (flat list) | Nested vs Flat structure |
| `constraints: ["rcd_all"]` | Not supported | MCP ไม่อ่าน constraints |

### 2.2 Adapter Mapping Table (ต้อง Implement)

```python
# Device Code → MCP Load Mapping (ตัวอย่าง)
DEVICE_TO_MCP = {
    "AC-12000BTU": {"power_watts": 1500, "load_type": "HVAC"},
    "AC-18000BTU": {"power_watts": 2200, "load_type": "HVAC"},
    "AC-24000BTU": {"power_watts": 3000, "load_type": "HVAC"},
    "HEATER-3500W": {"power_watts": 3500, "load_type": "APPLIANCE"},
    "HEATER-4500W": {"power_watts": 4500, "load_type": "APPLIANCE"},
    "INDUCTION-3000W": {"power_watts": 3000, "load_type": "APPLIANCE"},
    "COOKTOP-INDUCTION-7KW": {"power_watts": 7000, "load_type": "APPLIANCE"},
    "OVEN-ELECTRIC-3KW": {"power_watts": 3000, "load_type": "APPLIANCE"},
    "SOCKET-16A": {"power_watts": 180, "load_type": "RECEPTACLE"},
}

# Voltage Mapping
VOLTAGE_MAP = {
    "TH_1PH_230V": VoltageType.SINGLE_PHASE_240V,
    "TH_3PH_400V": VoltageType.THREE_PHASE_208V,
}
```

### 2.3 สิ่งที่ MCP Core ต้องการ (จาก contracts.py)

```python
@dataclass
class DesignRequest:
    project_name: str
    loads: List[ElectricalLoad]      # ← ต้องแปลงจาก RAG's device_code
    panels: List[PanelSpecification]  # ← ต้องสร้างจาก room structure
    service_voltage: VoltageType      # ← ต้อง map จาก TH_xxx
    building_type: str = "residential"
    notes: str = ""

@dataclass  
class ElectricalLoad:
    name: str
    power_watts: float    # ← RAG ไม่มี! ต้องดึงจาก device_code
    voltage: int          # ← ต้องแปลงจาก voltage_system
    load_type: LoadType   # ← ต้อง map จาก device category
    quantity: int = 1
    location: str = ""
```

### 2.4 Conclusion
> ✅ **ยืนยัน: ต้องทำ Adapter เพราะ Data Schema ต่างกัน 100%**
> - RAG ใช้ "human-friendly" format (device codes, Thai voltage names)
> - MCP ใช้ "calculation-ready" format (watts, amps, NEC voltage)

---

## 3. Debug Points
### จุดที่ต้อง Debug เป็นพิเศษ

### 3.1 🔴 Critical Points (ต้องระวังมาก)

| # | Location | Risk | How to Debug |
|---|----------|------|--------------|
| 1 | **Voltage Mapping** | TH_1PH_230V → 240V mismatch | Unit test with explicit assert |
| 2 | **Device Code Lookup** | Unknown code = crash | Fallback + logging if not found |
| 3 | **Room-Load Association** | room_id mismatch | Validate before transform |
| 4 | **MCP Timeout** | MCP Core slow response | 30s timeout + graceful error |
| 5 | **Session State** | Race condition on update | Single-threaded for MVP |

### 3.2 🟡 Medium Risk Points

| # | Location | Risk | Mitigation |
|---|----------|------|------------|
| 6 | LLM Output Parse | JSON malformed | Retry with RETRY_MAX_ATTEMPTS |
| 7 | Vector DB | Embedding API fail | Keyword fallback exists ✅ |
| 8 | MCP URL Config | Wrong port hardcoded | Use config.py centrally |

### 3.3 Architecture Errors Found (ตรวจพบ)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE AUDIT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ CORRECT:                                                    │
│  ──────────                                                     │
│  • RAG → Knowledge retrieval → LLM → ProjectInputSpec           │
│  • MCP → NEC calculations → Wire/Breaker sizing                 │
│  • Port separation: RAG=8080, MCP=5001                          │
│  • RAG ไม่คำนวณค่าไฟฟ้า (ถูกต้อง!)                               │
│  • MCP ไม่ทำ NLP (ถูกต้อง!)                                      │
│                                                                 │
│  ⚠️  POTENTIAL ISSUES:                                          │
│  ────────────────────                                           │
│  1. core/ folder exists but NOT used by app/                    │
│     → database.py, ingest.py used by scripts/ only              │
│     → This is OK but could confuse new developers               │
│                                                                 │
│  2. session_store.py created but NOT wired to routes.py         │
│     → No endpoint uses session yet                              │
│                                                                 │
│  3. privacy.py has Vertex AI commented out, uses Google AI      │
│     → Inconsistent with service.py (which uses Vertex)          │
│     → May cause auth issues                                     │
│                                                                 │
│  ❌ ERRORS FOUND:                                               │
│  ───────────────                                                │
│  None critical. Architecture is sound.                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Unit Test Coverage Needed

```python
# Tests to write for mcp_adapter.py
def test_voltage_mapping_th_to_nec():
    """TH_1PH_230V → SINGLE_PHASE_240V"""
    
def test_device_code_to_watts():
    """AC-12000BTU → 1500W"""
    
def test_unknown_device_fallback():
    """Unknown code should not crash"""
    
def test_flatten_room_loads():
    """Nested room.loads → flat loads list"""
```

---

## 4. File Audit
### ไฟล์ที่ไม่เกี่ยวข้อง / Legacy Code

### 4.1 Project Files Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                      FILE AUDIT REPORT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📁 ROOT LEVEL (.py files)                                      │
│  ─────────────────────────                                      │
│                                                                 │
│  ✅ ACTIVE (ใช้งานจริง):                                        │
│  • main_ACA.py          - Entry point, uvicorn runner           │
│  • gate_way_new.py      - Intent routing (MOZART/AMADEUS)       │
│                                                                 │
│  🟡 UTILITY (ใช้เฉพาะกิจ):                                      │
│  • debug_regex.py       - One-time regex debug (can delete)     │
│  • test_interactive_project.py - Manual test script             │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  📁 app/ FOLDER                                                 │
│  ────────────────                                               │
│  ✅ ALL ACTIVE:                                                 │
│  • config.py            - Settings management                   │
│  • models.py            - Pydantic data models                  │
│  • routes.py            - FastAPI endpoints                     │
│  • service.py           - Business logic (RAG)                  │
│  • knowledge_service.py - Knowledge retrieval                   │
│  • trust_log.py         - Audit logging                         │
│  • session_store.py     - Session management (NEW, unused yet)  │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  📁 core/ FOLDER                                                │
│  ───────────────                                                │
│  🟡 INFRASTRUCTURE (ใช้โดย scripts/ ไม่ใช่ app/):               │
│  • database.py          - VectorDB wrapper (ChromaDB)           │
│  • ingest.py            - Document ingestion                    │
│  • privacy.py           - PII anonymization                     │
│                                                                 │
│  ⚠️  NOTE: core/ is NOT imported by app/                        │
│      app/knowledge_service.py reimplements similar logic        │
│      This creates DUPLICATION                                   │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  📁 tests/ FOLDER                                               │
│  ────────────────                                               │
│  ✅ ACTIVE TESTS:                                               │
│  • test_models.py       - Model validation tests                │
│  • test_mcp_spec_cases.py - MCP spec generation tests           │
│  • test_folder_based.py - Folder structure tests                │
│                                                                 │
│  🟡 UTILITY/EXPLORATION:                                        │
│  • test_integration_suite.py - Integration tests                │
│  • test_mcp_suite.py    - MCP-specific tests                    │
│  • test_rag_suite.py    - RAG-specific tests                    │
│  • explore_llm_responses.py - Manual exploration tool           │
│                                                                 │
│  📁 tests/one_shot_qa/  - QA evaluation framework               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Recommended Actions

| File | Status | Recommendation |
|------|--------|----------------|
| `debug_regex.py` | 🗑️ DELETABLE | One-time debug, not needed |
| `test_interactive_project.py` | 🔄 KEEP | Useful for manual testing |
| `core/` folder | ⚠️ REVIEW | Consolidate with app/ or document clearly |
| `core/privacy.py` | ⚠️ FIX | Auth method inconsistent |

### 4.3 ls -la Output (Root)

```
total 439
-rwxr-xr-x  2210 Dec  2  debug_regex.py        ← 🗑️ CAN DELETE
-rwxr-xr-x 16442 Dec  2  gate_way_new.py       ← ✅ ACTIVE
-rwxr-xr-x   318 Nov 27  main_ACA.py           ← ✅ ACTIVE (entry)
-rwxr-xr-x  4586 Dec  2  test_interactive_project.py ← 🟡 UTILITY

drwxr-xr-x  4096 Dec  2  app/                  ← ✅ CORE
drwxr-xr-x  4096 Nov 27  core/                 ← ⚠️ INFRASTRUCTURE
drwxr-xr-x  4096 Nov 27  tests/                ← ✅ TESTS
drwxr-xr-x  4096 Nov 27  rag_knowledge/        ← ✅ KNOWLEDGE
drwxr-xr-x     0 Dec  2  docs/                 ← 📝 DOCUMENTATION
drwxr-xr-x     0 Dec  2  frontend_UI_UX/       ← 🎨 FRONTEND
```

### 4.4 Legacy Architecture Check

> **คำถาม:** มีสถาปัตยกรรมเก่าหลงเหลือไหม?
> 
> **คำตอบ:** ไม่มี legacy architecture ที่ขัดแย้ง แต่มี:
> 1. `core/` folder ที่ทำหน้าที่คล้าย `app/` บางส่วน (database, ingest)
> 2. `privacy.py` ใช้ Google AI แต่ `service.py` ใช้ Vertex AI
> 3. ไม่มีไฟล์ที่ import สถาปัตยกรรมเก่า

---

## 5. Implementation Plan
### แผนการทำงานต่อจากนี้

```
╔══════════════════════════════════════════════════════════════════╗
║              IMPLEMENTATION ROADMAP (4 PHASES)                   ║
╚══════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: MCP ADAPTER (Day 1)                                   │
│  ────────────────────────────                                   │
│                                                                 │
│  Goal: แปลง RAG output → MCP input ได้ถูกต้อง                   │
│                                                                 │
│  Tasks:                                                         │
│  ┌────┬──────────────────────────────────────────┬────────────┐ │
│  │ #  │ Task                                     │ Est. Time  │ │
│  ├────┼──────────────────────────────────────────┼────────────┤ │
│  │ 1  │ Create app/mcp_adapter.py                │ 1 hour     │ │
│  │ 2  │ Implement DEVICE_TO_MCP mapping          │ 30 min     │ │
│  │ 3  │ Implement voltage_to_nec() function      │ 15 min     │ │
│  │ 4  │ Implement flatten_loads() function       │ 30 min     │ │
│  │ 5  │ Write unit tests for adapter             │ 45 min     │ │
│  └────┴──────────────────────────────────────────┴────────────┘ │
│                                                                 │
│  Deliverable: mcp_adapter.py with 100% test coverage            │
│  Risk Level: 🟢 LOW (isolated, no side effects)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: MCP CLIENT (Day 1-2)                                  │
│  ─────────────────────────────                                  │
│                                                                 │
│  Goal: เรียก MCP Core API ได้                                   │
│                                                                 │
│  Tasks:                                                         │
│  ┌────┬──────────────────────────────────────────┬────────────┐ │
│  │ #  │ Task                                     │ Est. Time  │ │
│  ├────┼──────────────────────────────────────────┼────────────┤ │
│  │ 1  │ Create app/mcp_client.py                 │ 30 min     │ │
│  │ 2  │ Add MCP_CORE_URL to config.py            │ 10 min     │ │
│  │ 3  │ Implement async call_mcp_design()        │ 30 min     │ │
│  │ 4  │ Add timeout + retry logic                │ 20 min     │ │
│  │ 5  │ Write integration test (mock MCP)        │ 30 min     │ │
│  └────┴──────────────────────────────────────────┴────────────┘ │
│                                                                 │
│  Deliverable: mcp_client.py with error handling                 │
│  Risk Level: 🟡 MEDIUM (depends on MCP availability)            │
│                                                                 │
│  Dependencies:                                                  │
│  • MCP Core running on port 5001                                │
│  • Endpoint: POST /api/v1/design                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: ROUTE INTEGRATION (Day 2)                             │
│  ──────────────────────────────────                             │
│                                                                 │
│  Goal: End-to-end API ทำงานได้                                  │
│                                                                 │
│  Tasks:                                                         │
│  ┌────┬──────────────────────────────────────────┬────────────┐ │
│  │ #  │ Task                                     │ Est. Time  │ │
│  ├────┼──────────────────────────────────────────┼────────────┤ │
│  │ 1  │ Add /api/v1/design endpoint to routes.py │ 30 min     │ │
│  │ 2  │ Wire: generate_mcp_spec → adapter → mcp  │ 30 min     │ │
│  │ 3  │ Add session_id parameter support         │ 20 min     │ │
│  │ 4  │ Test end-to-end with 2 rooms             │ 30 min     │ │
│  └────┴──────────────────────────────────────────┴────────────┘ │
│                                                                 │
│  Deliverable: Working /api/v1/design endpoint                   │
│  Risk Level: 🟡 MEDIUM (touching existing routes.py)            │
│                                                                 │
│  Test Case (Minimum Viable):                                    │
│  • Input: 2 rooms (living room + bedroom)                       │
│  • Loads: AC + Socket                                           │
│  • Expected: MCP returns wire sizing + breaker selection        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: SESSION INTEGRATION (Day 3, Optional)                 │
│  ───────────────────────────────────────────────                │
│                                                                 │
│  Goal: Multi-turn conversation ทำงานได้                         │
│                                                                 │
│  Tasks:                                                         │
│  ┌────┬──────────────────────────────────────────┬────────────┐ │
│  │ #  │ Task                                     │ Est. Time  │ │
│  ├────┼──────────────────────────────────────────┼────────────┤ │
│  │ 1  │ Add session endpoints to routes.py       │ 30 min     │ │
│  │ 2  │ Modify /ask to accept session_id         │ 20 min     │ │
│  │ 3  │ Store conversation in session            │ 20 min     │ │
│  │ 4  │ Test progressive requirement gathering   │ 30 min     │ │
│  └────┴──────────────────────────────────────────┴────────────┘ │
│                                                                 │
│  Deliverable: Multi-turn works                                  │
│  Risk Level: 🟢 LOW (session_store.py ready, just wire)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.1 Detailed Task Breakdown

```
PHASE 1: mcp_adapter.py
═══════════════════════

File: app/mcp_adapter.py

┌─────────────────────────────────────────────────────────────────┐
│  class McpAdapter:                                              │
│      """Convert RAG ProjectInputSpec → MCP DesignRequest"""     │
│                                                                 │
│      DEVICE_TO_MCP = { ... }  # Device code mapping             │
│      VOLTAGE_MAP = { ... }    # Voltage mapping                 │
│                                                                 │
│      def convert(spec: ProjectInputSpec) -> DesignRequest:      │
│          """Main conversion function"""                         │
│          loads = self._flatten_loads(spec.rooms)                │
│          panels = self._create_panels(spec.rooms)               │
│          voltage = self._map_voltage(spec.electrical_system)    │
│          return DesignRequest(...)                              │
│                                                                 │
│      def _flatten_loads(rooms) -> List[ElectricalLoad]:         │
│          """Convert nested room.loads to flat list"""           │
│                                                                 │
│      def _map_voltage(system) -> VoltageType:                   │
│          """TH_1PH_230V → SINGLE_PHASE_240V"""                  │
│                                                                 │
│      def _device_to_watts(code: str) -> int:                    │
│          """AC-12000BTU → 1500"""                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

PHASE 2: mcp_client.py
═══════════════════════

File: app/mcp_client.py

┌─────────────────────────────────────────────────────────────────┐
│  class McpClient:                                               │
│      """HTTP client for MCP Core API"""                         │
│                                                                 │
│      def __init__(self, base_url: str):                         │
│          self.base_url = base_url  # http://localhost:5001      │
│          self.timeout = 30.0                                    │
│                                                                 │
│      async def design(request: DesignRequest) -> DesignResult:  │
│          """Call POST /api/v1/design on MCP Core"""             │
│          async with httpx.AsyncClient() as client:              │
│              response = await client.post(...)                  │
│              return DesignResult.from_dict(response.json())     │
│                                                                 │
│      async def health_check() -> bool:                          │
│          """Check if MCP Core is available"""                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

PHASE 3: routes.py updates
═══════════════════════════

File: app/routes.py (ADD, don't modify existing)

┌─────────────────────────────────────────────────────────────────┐
│  # NEW ENDPOINT                                                 │
│  @app.post("/api/v1/design")                                    │
│  async def design_electrical_system(                            │
│      requirements: ProjectRequirements,                         │
│      session_id: Optional[str] = None                           │
│  ) -> DesignResponse:                                           │
│      """                                                        │
│      End-to-end design:                                         │
│      1. RAG: requirements → ProjectInputSpec                    │
│      2. Adapter: ProjectInputSpec → DesignRequest               │
│      3. MCP: DesignRequest → DesignResult                       │
│      """                                                        │
│      # Step 1: Generate spec via existing service               │
│      spec = await rag_service.generate_mcp_spec(requirements)   │
│                                                                 │
│      # Step 2: Convert to MCP format                            │
│      mcp_request = adapter.convert(spec.project_input)          │
│                                                                 │
│      # Step 3: Call MCP Core                                    │
│      result = await mcp_client.design(mcp_request)              │
│                                                                 │
│      return DesignResponse(                                     │
│          spec=spec,                                             │
│          design_result=result                                   │
│      )                                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Regression Protection
### การป้องกัน Regression

### 6.1 Files That MUST NOT Change

| File | Why | Protected By |
|------|-----|--------------|
| `app/models.py` | Data contracts | Existing tests |
| `app/service.py` | Core RAG logic | test_mcp_spec_cases.py |
| `app/knowledge_service.py` | Knowledge retrieval | Working in prod |
| `rag_knowledge/*` | Knowledge base | Read-only |

### 6.2 Safe Addition Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAFE MODIFICATION RULES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ SAFE (DO):                                                  │
│  ─────────────                                                  │
│  • ADD new files (mcp_adapter.py, mcp_client.py)                │
│  • ADD new endpoints (don't modify existing ones)               │
│  • ADD new config values (don't change existing)                │
│  • ADD imports at top of existing files                         │
│                                                                 │
│  ❌ UNSAFE (DON'T):                                             │
│  ────────────────                                               │
│  • Modify existing endpoint signatures                          │
│  • Change model field names/types                               │
│  • Delete any existing code                                     │
│  • Change knowledge retrieval logic                             │
│                                                                 │
│  🔄 VERIFY AFTER EACH PHASE:                                    │
│  ───────────────────────────                                    │
│  $ pytest tests/test_mcp_spec_cases.py -v                       │
│  $ pytest tests/test_models.py -v                               │
│                                                                 │
│  If any test fails → ROLLBACK immediately                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Testing Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      TESTING LAYERS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Unit Tests (mcp_adapter)                              │
│  ─────────────────────────────────                              │
│  • Test each mapping function in isolation                      │
│  • Mock everything external                                     │
│  • Run: pytest tests/test_mcp_adapter.py                        │
│                                                                 │
│  Layer 2: Integration Tests (mcp_client)                        │
│  ────────────────────────────────────────                       │
│  • Test with mock MCP server                                    │
│  • Verify request/response format                               │
│  • Run: pytest tests/test_mcp_client.py                         │
│                                                                 │
│  Layer 3: End-to-End Tests (/api/v1/design)                     │
│  ──────────────────────────────────────────                     │
│  • Full flow with real MCP Core                                 │
│  • Test minimum viable case (2 rooms)                           │
│  • Run: python tests/explore_llm_responses.py                   │
│                                                                 │
│  Layer 4: Regression Tests (existing)                           │
│  ─────────────────────────────────────                          │
│  • Run BEFORE and AFTER each phase                              │
│  • Run: pytest tests/ -v -m "not integration"                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Critical Reminders
### ห้ามลืม!

### 7.1 Port Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                      PORT MAPPING (CORRECT)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Service          │  Port  │  URL                               │
│  ─────────────────┼────────┼────────────────────────────────── │
│  RAG (Aura)       │  8080  │  http://localhost:8080             │
│  MCP Core         │  5001  │  http://localhost:5001             │
│  Gateway          │  8000  │  http://localhost:8000             │
│  Frontend         │  (any) │  Static HTML                       │
│                                                                 │
│  ⚠️  DO NOT CONFUSE:                                            │
│  • RAG listens on 8080, calls MCP on 5001                       │
│  • Gateway listens on 8000, routes to RAG (8080)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Role Separation (CRITICAL!)

```
┌─────────────────────────────────────────────────────────────────┐
│              RAG vs MCP RESPONSIBILITY (ห้ามสลับ!)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RAG (Aura) DOES:                 │  MCP Core (Amadeus) DOES:   │
│  ─────────────────────────        │  ────────────────────────── │
│  ✅ Parse human language          │  ✅ NEC calculations        │
│  ✅ Retrieve knowledge            │  ✅ Wire sizing             │
│  ✅ Generate structured spec      │  ✅ Breaker selection       │
│  ✅ Validate device codes         │  ✅ Conduit sizing          │
│  ✅ Map room→load associations    │  ✅ Voltage drop calc       │
│                                   │  ✅ Generate AutoLISP       │
│                                                                 │
│  RAG DOES NOT:                    │  MCP DOES NOT:              │
│  ──────────────                   │  ─────────────              │
│  ❌ Calculate wire sizes          │  ❌ Understand Thai         │
│  ❌ Do voltage drop math          │  ❌ Parse natural language  │
│  ❌ Select breakers               │  ❌ Retrieve documents      │
│  ❌ Generate DXF/AutoLISP         │  ❌ Handle "บ้าน 2 ชั้น"    │
│                                                                 │
│  ⚠️  If you catch yourself making RAG calculate amps            │
│     or MCP understand "ห้องนอนใหญ่" → YOU'RE DOING IT WRONG!   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Validation Checklist (Before Each Deploy)

```
□ Port 8080 = RAG only
□ Port 5001 = MCP only  
□ RAG output = ProjectInputSpec (not watts, not amps)
□ MCP input = DesignRequest (watts, voltage type)
□ Device codes validated against DEVICE_CODES.md
□ Room IDs sequential (R1, R2, ...)
□ All existing tests pass
```

### 7.4 Known Device Codes (Quick Reference)

```python
# From rag_knowledge/db/DEVICE_CODES.md
VALID_DEVICE_CODES = [
    # AC Units
    "AC-9000BTU", "AC-12000BTU", "AC-18000BTU", "AC-24000BTU",
    
    # Heaters
    "HEATER-3500W", "HEATER-4500W", "HEATER-6000W",
    
    # Kitchen
    "INDUCTION-3000W", "COOKTOP-INDUCTION-7KW", 
    "OVEN-ELECTRIC-3KW", "OVEN-ELECTRIC-5KW",
    
    # General
    "SOCKET-16A", "LIGHTING-LED",
    
    # Pumps
    "PUMP-0.5HP", "PUMP-1HP", "PUMP-2HP"
]
```

---

## 📌 Summary

| Question | Answer |
|----------|--------|
| 1. ขาดอะไร | mcp_adapter.py, mcp_client.py, route /api/v1/design |
| 2. ต้องทำ Adapter? | ✅ ยืนยัน เพราะ data schema ต่างกัน 100% |
| 3. จุด Debug | Voltage mapping, Device lookup, MCP timeout |
| 4. ไฟล์ไม่เกี่ยว | debug_regex.py (ลบได้), core/ folder (ชี้แจงหน้าที่) |
| 5. แผนงาน | 4 Phases, เริ่มจาก adapter → client → route → session |
| 6. ป้องกัน Regression | ADD only, run tests before/after each phase |
| 7. ห้ามลืม | Port 8080/5001, RAG≠คำนวณ, MCP≠NLP |

---

## 🚀 Next Action

> **Ready to proceed?**
> 
> เริ่ม Phase 1: สร้าง `app/mcp_adapter.py` พร้อม unit tests
> 
> Command to verify before starting:
> ```bash
> pytest tests/test_models.py tests/test_mcp_spec_cases.py -v
> ```

```