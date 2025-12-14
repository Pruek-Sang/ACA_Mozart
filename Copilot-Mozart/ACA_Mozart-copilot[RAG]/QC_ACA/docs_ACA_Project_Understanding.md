# Source: ACA_Project_Understanding.md

```md
# 🏛️ ACA Mozart - Complete Architecture Understanding

**Document Version:** 1.0  
**Date:** 2025-12-02  
**Author:** Copilot (Claude Opus 4.5)

---

## 📋 Table of Contents

1. [System Overview](#1-system-overview)
2. [Component Breakdown](#2-component-breakdown)
3. [Complete Data Flow](#3-complete-data-flow)
4. [RAG Service Details](#4-rag-service-details)
5. [MCP Core Details](#5-mcp-core-details)
6. [Data Contract Mapping](#6-data-contract-mapping)
7. [Integration Architecture](#7-integration-architecture)
8. [Example End-to-End Flow](#8-example-end-to-end-flow)

---

## 1. System Overview

### 🎯 วัตถุประสงค์ของระบบ

**ACA Mozart** เป็นระบบออกแบบไฟฟ้าอัตโนมัติที่ประกอบด้วย 2 ส่วนหลัก:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ACA Mozart System                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────┐              ┌─────────────────┐                 │
│   │                 │   JSON       │                 │                 │
│   │   RAG Service   │─────────────▶│   MCP Core v2   │                 │
│   │   (Aura/Spec)   │  Spec        │   (Amadeus)     │                 │
│   │                 │              │                 │                 │
│   └────────┬────────┘              └────────┬────────┘                 │
│            │                                │                          │
│            │                                │                          │
│   "What to design"              "How to calculate"                     │
│   แปลภาษามนุษย์ → Spec           คำนวณไฟฟ้า → ผลลัพธ์                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 🔑 หลักการสำคัญ

| Component | ชื่อเรียก | หน้าที่หลัก | ห้ามทำ |
|-----------|----------|-------------|--------|
| **RAG Service** | Aura | แปลภาษามนุษย์ → JSON Spec | ❌ ห้ามคำนวณไฟฟ้า |
| **MCP Core** | Amadeus | คำนวณไฟฟ้าตามมาตรฐาน | ❌ ห้ามเดาความต้องการ |
| **Gateway** | Mozart | Route requests | ❌ ห้ามมี logic |

---

## 2. Component Breakdown

### 2.1 RAG Service (Aura) - `/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/`

```
ACA_Mozart-copilot[RAG]/
├── app/
│   ├── routes.py           # FastAPI endpoints
│   ├── service.py          # Core RAG logic + LLM
│   ├── models.py           # Pydantic schemas
│   ├── knowledge_service.py # Knowledge retrieval
│   ├── config.py           # Settings
│   ├── trust_log.py        # Audit logging
│   └── session_store.py    # Conversation memory (NEW)
│
├── rag_knowledge/          # Knowledge base (4 folders)
│   ├── db/                 # Device codes, templates, catalog
│   ├── mcp/                # MCP design docs
│   ├── standard/           # Thai electrical standards (วสท.)
│   └── example/            # Few-shot examples
│
├── vector_db/              # ChromaDB embeddings
├── tests/                  # Test suites
└── gate_way_new.py         # Intent router (MOZART/AMADEUS)
```

**API Endpoints:**
```
POST /api/v1/ask        → ถามคำถามทั่วไป (StandardResponse)
POST /api/v1/mcp_spec   → สร้าง spec สำหรับ MCP (McpSpecResponse)
POST /api/v1/retrieve_raw → Debug retrieval
```

### 2.2 MCP Core v2 (Amadeus) - `/home/builder/Desktop/ACA_Mozart/mcp_core_v2/`

```
mcp_core_v2/
├── main.py                 # Entry point
├── pipeline.py             # Design pipeline orchestrator
├── config.py               # Settings
├── integration.py          # Room-based integration
│
├── models/
│   ├── contracts.py        # DesignRequest/DesignResult
│   ├── baseline.py         # NEC constants, derating factors
│   └── catalog_models.py   # Product models
│
├── core/                   # Calculation modules
│   ├── load_calculator.py  # คำนวณโหลด
│   ├── wire_sizer.py       # เลือกขนาดสาย
│   ├── breaker_selector.py # เลือกเบรกเกอร์
│   ├── conduit_sizer.py    # เลือกขนาดท่อ
│   ├── compliance_checker.py # ตรวจมาตรฐาน NEC
│   └── autolisp_generator.py # สร้าง AutoCAD code
│
├── cad/                    # AutoLISP generators
│   ├── drawing/            # Drawing generators
│   ├── placement/          # Device placement
│   └── geometry/           # Room templates
│
└── dal/                    # Database access
    ├── supabase_client.py
    └── catalog_dal.py
```

---

## 3. Complete Data Flow

### 3.1 High-Level Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │────▶│  Gateway │────▶│   RAG    │────▶│   MCP    │────▶│  Output  │
│  Input   │     │ (Mozart) │     │  (Aura)  │     │(Amadeus) │     │  Result  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │                │
     │                │                │                │                │
     ▼                ▼                ▼                ▼                ▼
 "บ้าน 2 ชั้น     Intent:         ProjectInput      DesignResult     - Panel Schedule
  มีแอร์ 3 ตัว"   MOZART          Spec (JSON)      - wire sizes     - AutoLISP
                                                   - breakers       - Compliance
                                                   - conduits
```

### 3.2 Detailed Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: User Input (ภาษาธรรมชาติ)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User: "ออกแบบบ้าน 2 ชั้น 180 ตร.ม.                                        │
│          - ห้องนั่งเล่น ชั้น 1 มีแอร์ 1 ตัว                                  │
│          - ห้องนอนใหญ่ ชั้น 2 มีแอร์ 1 ตัว                                   │
│          - ห้องน้ำ 2 ห้อง มีเครื่องทำน้ำอุ่น                                 │
│          - ครัวมีเตาไฟฟ้า induction"                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Gateway (gate_way_new.py) - Intent Classification                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   if "ออกแบบ" or "design" or "spec":                                        │
│       intent = "MOZART"  → Forward to RAG /api/v1/mcp_spec                  │
│   else:                                                                     │
│       intent = "AMADEUS" → Forward to Chat/QA                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: RAG Service - Knowledge Retrieval                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   KnowledgeService.get_docs_for_mcp_spec() retrieves from 4 folders:        │
│                                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │     db/     │  │    mcp/     │  │  standard/  │  │  example/   │       │
│   │ DEVICE_CODES│  │ MCP_CAPS    │  │ วสท. 2564  │  │ few-shot    │       │
│   │ ROOM_TEMPL  │  │ INPUT_RULES │  │ THW tables │  │ examples    │       │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
│   Priority: example (95) > mcp (90) > standard (80) > db (70)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: RAG Service - LLM Processing (5 Phases)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Phase 1: Pre-validate requirements                                        │
│            - Check rooms, loads exist                                       │
│            - Return 422 if critical data missing                            │
│                                                                             │
│   Phase 2: Generate human-readable plan (Thai)                              │
│            - "1. วิเคราะห์ห้อง: 6 ห้อง..."                                  │
│            - "2. จัดกลุ่มโหลด: แอร์ 3 ตัว..."                               │
│            - "3. เลือก Template: ROOMT-LIVING-STD..."                       │
│                                                                             │
│   Phase 3: Build spec following plan                                        │
│            - Map room types → BEDROOM, KITCHEN, LIVING, BATHROOM            │
│            - Map devices → AC-12000BTU, HEATER-3500W, INDUCTION-3000W       │
│            - Generate IDs: R1, R2... L1, L2...                              │
│                                                                             │
│   Phase 4: Parse & validate (Pydantic)                                      │
│            - McpSpecResponse.parse_raw(llm_output)                          │
│            - Retry up to 2 times if parse fails                             │
│                                                                             │
│   Phase 5: Quality check                                                    │
│            - Validate device_codes exist in DEVICE_CODES.md                 │
│            - Validate template_codes exist in ROOM_TEMPLATES.md             │
│            - LLM semantic judge                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: RAG Output - McpSpecResponse (JSON)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   {                                                                         │
│     "project_input": {                                                      │
│       "project_info": {                                                     │
│         "project_name": "บ้าน 2 ชั้น",                                      │
│         "building_type": "RESIDENTIAL",                                     │
│         "spec_version": "2.0"                                               │
│       },                                                                    │
│       "electrical_system": {                                                │
│         "voltage_system": "TH_1PH_230V",                                    │
│         "earthing": "TT"                                                    │
│       },                                                                    │
│       "rooms": [                                                            │
│         {"room_id": "R1", "name": "ห้องนั่งเล่น 1F",                        │
│          "room_type": "LIVING", "template_code": "ROOMT-LIVING-STD"},       │
│         {"room_id": "R2", "name": "ครัว 1F",                                │
│          "room_type": "KITCHEN", "template_code": "ROOMT-KITCHEN-HEAVY"},   │
│         ...                                                                 │
│       ],                                                                    │
│       "loads": [                                                            │
│         {"load_id": "L1", "room_id": "R1",                                  │
│          "device_code": "AC-12000BTU", "qty": 1},                           │
│         {"load_id": "L2", "room_id": "R3",                                  │
│          "device_code": "HEATER-3500W", "qty": 1},                          │
│         {"load_id": "L3", "room_id": "R2",                                  │
│          "device_code": "INDUCTION-3000W", "qty": 1},                       │
│         ...                                                                 │
│       ],                                                                    │
│       "constraints": {                                                      │
│         "rule_profile_id": "TH_RESIDENTIAL_LV",                             │
│         "user_constraints": ["rcd_for_all_outlets"]                         │
│       }                                                                     │
│     },                                                                      │
│     "standards_profile": {...},                                             │
│     "llm_metadata": {...}                                                   │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Adapter Layer - Convert RAG → MCP Format (TO BE IMPLEMENTED)        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   RAG Format (ProjectInputSpec)      MCP Format (DesignRequest)             │
│   ──────────────────────────────     ─────────────────────────              │
│                                                                             │
│   rooms[].room_type: "LIVING"   →    loads[].location.room: "ห้องนั่งเล่น"  │
│   loads[].device_code: "AC-12000BTU" → loads[].load_type: HVAC              │
│                                        loads[].power_watts: 1500            │
│   voltage_system: "TH_1PH_230V" →    service_voltage: SINGLE_PHASE_240V     │
│                                                                             │
│   Device Code Mapping:                                                      │
│   ┌────────────────────┬────────────────┬─────────────┐                    │
│   │ RAG device_code    │ MCP load_type  │ power_watts │                    │
│   ├────────────────────┼────────────────┼─────────────┤                    │
│   │ AC-12000BTU        │ HVAC           │ 1500        │                    │
│   │ HEATER-3500W       │ APPLIANCE      │ 3500        │                    │
│   │ INDUCTION-3000W    │ APPLIANCE      │ 3000        │                    │
│   │ SOCKET-16A         │ RECEPTACLE     │ 3680        │                    │
│   │ LIGHT-LED          │ LIGHTING       │ varies      │                    │
│   └────────────────────┴────────────────┴─────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: MCP Core - Design Pipeline                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   pipeline.execute(DesignRequest) runs 8 steps:                             │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 1: Validate Request                                        │      │
│   │         - Check panels, service_voltage, utility_size           │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 2: Resolve Templates                                       │      │
│   │         - Map loads to circuit requirements                     │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 3: Calculate Loads (load_calculator.py)                    │      │
│   │         - I = P / (V × PF) for single phase                     │      │
│   │         - I = P / (√3 × V × PF) for three phase                 │      │
│   │         - Apply continuous load factor (×1.25)                  │      │
│   │         - Apply demand factors per NEC                          │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 4: Size Wires (wire_sizer.py)                              │      │
│   │         - Check ampacity (NEC Table 310.16)                     │      │
│   │         - Calculate voltage drop                                │      │
│   │         - Apply derating factors:                               │      │
│   │           • DF001: Conductor grouping (0.4-1.0)                 │      │
│   │           • DF002: Ambient temperature (0.58-1.0)               │      │
│   │           • DF003: Soil resistivity (0.7-1.0)                   │      │
│   │           • DF004: Thermal insulation (0.6-1.0)                 │      │
│   │         - Size ground wire per NEC 250.122                      │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 5: Select Breakers (breaker_selector.py)                   │      │
│   │         - Find next standard rating: 15,20,25,30,35,40...       │      │
│   │         - Apply 125% for continuous loads                       │      │
│   │         - Select AFCI/GFCI where required                       │      │
│   │         - Select main breaker for panels                        │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 6: Size Conduits (conduit_sizer.py)                        │      │
│   │         - Calculate wire areas                                  │      │
│   │         - Apply NEC Chapter 9 fill percentages                  │      │
│   │         - Select conduit size                                   │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 7: Check Compliance (compliance_checker.py)                │      │
│   │         - NEC 2023 compliance                                   │      │
│   │         - Voltage drop ≤ 3% (branch), ≤ 5% (total)              │      │
│   │         - AFCI/GFCI requirements                                │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │ Step 8: Generate AutoLISP (autolisp_generator.py)               │      │
│   │         - E-101: Lighting Plan                                  │      │
│   │         - E-201: Power Plan                                     │      │
│   │         - E-301: Single Line Diagram                            │      │
│   │         - E-401: Panel Schedule                                 │      │
│   │         - E-501: Typical Details                                │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: MCP Output - DesignResult                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   DesignResult(                                                             │
│     session_id="session_20251202_120000",                                   │
│     request=DesignRequest(...),                                             │
│                                                                             │
│     calculations={                                                          │
│       "panel_001": {                                                        │
│         "total_va": 15000,                                                  │
│         "total_current": 65.2,                                              │
│         "demand_current": 52.1,                                             │
│         "utilization": 52.1%                                                │
│       }                                                                     │
│     },                                                                      │
│                                                                             │
│     wire_sizing={                                                           │
│       "load_001": {"wire_size": "10", "ground_size": "12",                  │
│                    "voltage_drop": 1.8%},                                   │
│       "load_002": {"wire_size": "8", "ground_size": "10",                   │
│                    "voltage_drop": 2.1%}                                    │
│     },                                                                      │
│                                                                             │
│     breaker_selections={                                                    │
│       "load_001": {"breaker_rating": 20, "poles": 1},                       │
│       "load_002": {"breaker_rating": 25, "poles": 2}                        │
│     },                                                                      │
│                                                                             │
│     conduit_sizing={                                                        │
│       "load_001": {"conduit_size": "3/4", "fill_percent": 28%},             │
│       "load_002": {"conduit_size": "1", "fill_percent": 32%}                │
│     },                                                                      │
│                                                                             │
│     compliance_report={                                                     │
│       "compliant": true,                                                    │
│       "checks": [...]                                                       │
│     },                                                                      │
│                                                                             │
│     autolisp_code="(defun c:DRAW-E101 () ...)",                             │
│                                                                             │
│     errors=[],                                                              │
│     warnings=["Consider larger feeder for selective coordination"]          │
│   )                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 9: Final Output to User                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │  Panel Schedule │  │  Single Line    │  │   AutoCAD       │            │
│   │  (E-401)        │  │  Diagram (E-301)│  │   .lsp files    │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   พร้อมส่งให้วิศวกรตรวจสอบและนำไปใช้งาน                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. RAG Service Details

### 4.1 Knowledge Base Structure

```
rag_knowledge/
├── knowledge_index.json     # Metadata & priority
│
├── db/                      # Priority: 70
│   ├── DEVICE_CODES.md      # Valid device codes
│   ├── ROOM_TEMPLATES.md    # Valid room templates
│   ├── CATALOG_CONTRACT.md  # Database schema
│   └── PROJECT_CONFIG.md    # Project defaults
│
├── mcp/                     # Priority: 90
│   ├── 1)MCP_CAPABILITIES_AND_LIMITS.md
│   ├── 2)MCP_INPUT_QUALITY_RULES.md
│   ├── 3)MCP_SPEC_INTERPRETATION_GUIDE.md
│   ├── 4)MCP_ERROR_PLAYBOOK.md
│   └── 5)MCP_RUN_EXAMPLES.md
│
├── standard/                # Priority: 80
│   ├── Thai standard.md     # มาตรฐาน วสท. 2564
│   ├── Residential LV.md    # การออกแบบบ้านพักอาศัย
│   └── KEY_TABLES.md        # ตาราง THW ampacity
│
└── example/                 # Priority: 95
    ├── example_house_1floor_basic.md
    ├── example_house_2floor_kitchen_heavy.md
    └── example_incomplete_data.md
```

### 4.2 RAG Models (app/models.py)

```python
# Input from user (human-readable)
class ProjectRequirements:
    project_name: str
    building_type: str          # "residential", "commercial"
    voltage_system: str         # "TH_1PH_230V", "TH_3PH_400V"
    rooms: List[RoomInput]      # name, type, area_sqm
    loads: List[LoadInput]      # room_name, device, quantity
    user_constraints: List[str] # "rcd_for_all_outlets"

# Output to MCP (strict schema)
class ProjectInputSpec:
    project_info: ProjectInfo
    electrical_system: ElectricalSystem
    rooms: List[RoomSpec]       # room_id, room_type, template_code
    loads: List[LoadSpec]       # load_id, room_id, device_code, qty
    constraints: Constraints

class McpSpecResponse:
    project_input: ProjectInputSpec
    standards_profile: StandardsProfile
    llm_metadata: LlmMetadata
```

---

## 5. MCP Core Details

### 5.1 MCP Models (models/contracts.py)

```python
class DesignRequest:
    session_id: str
    project_name: str
    loads: List[ElectricalLoad]
    panels: List[PanelSpecification]
    service_voltage: VoltageType
    utility_service_size: int

class ElectricalLoad:
    id: str
    name: str
    load_type: LoadType    # LIGHTING, RECEPTACLE, HVAC, MOTOR, APPLIANCE
    voltage: VoltageType   # SINGLE_PHASE_120V, SINGLE_PHASE_240V, etc.
    power_watts: float
    quantity: int
    location: Location     # room, floor
    is_continuous: bool

class DesignResult:
    session_id: str
    calculations: Dict       # Load calculations
    wire_sizing: Dict        # Wire sizes
    breaker_selections: Dict # Breaker ratings
    conduit_sizing: Dict     # Conduit sizes
    compliance_report: Dict  # NEC compliance
    autolisp_code: str       # AutoCAD code
```

### 5.2 NEC Baseline Constants (models/baseline.py)

```python
# Voltage drop limits
voltage_drop_branch: 3%
voltage_drop_feeder: 2%
voltage_drop_total: 5%

# Continuous load factor
continuous_load_factor: 1.25

# Standard breaker ratings (A)
[15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 125, 150, 200...]

# Wire ampacity at 75°C (NEC Table 310.16)
copper_ampacity_75C = {
    "14": 20, "12": 25, "10": 35, "8": 50, "6": 65, "4": 85,
    "2": 115, "1/0": 150, "2/0": 175, "4/0": 230, ...
}

# Derating factors
DF001: Conductor grouping (0.4-1.0)
DF002: Ambient temperature (0.58-1.0)
DF003: Soil thermal resistivity (0.7-1.0)
DF004: Thermal insulation (0.6-1.0)
```

---

## 6. Data Contract Mapping

### 6.1 Voltage System Mapping

| RAG (Thai) | MCP (NEC) |
|------------|-----------|
| `TH_1PH_230V` | `SINGLE_PHASE_240V` |
| `TH_3PH_400V` | `THREE_PHASE_480V` |

### 6.2 Device Code → Load Mapping

| RAG device_code | MCP load_type | power_watts | Notes |
|-----------------|---------------|-------------|-------|
| `AC-12000BTU` | `HVAC` | 1500 | 12000 BTU ≈ 1.5kW |
| `AC-18000BTU` | `HVAC` | 2200 | 18000 BTU ≈ 2.2kW |
| `HEATER-3500W` | `APPLIANCE` | 3500 | Water heater |
| `INDUCTION-3000W` | `APPLIANCE` | 3000 | Induction cooker |
| `SOCKET-16A` | `RECEPTACLE` | 3680 | 230V × 16A |
| `SOCKET-13A` | `RECEPTACLE` | 2990 | 230V × 13A |
| `LIGHT-LED` | `LIGHTING` | varies | Per fixture |

### 6.3 Room Type Mapping

| RAG room_type | MCP location.room | Default fixtures |
|---------------|-------------------|------------------|
| `BEDROOM` | "ห้องนอน" | 2 outlets, 1 light, 1 AC |
| `LIVING` | "ห้องนั่งเล่น" | 4 outlets, 2 lights, 1 AC |
| `KITCHEN` | "ครัว" | 4 outlets, 1 light, cooking |
| `BATHROOM` | "ห้องน้ำ" | 1 outlet (GFCI), 1 light |

---

## 7. Integration Architecture

### 7.1 Current State (ยังไม่เชื่อมต่อ)

```
┌─────────────┐         ┌─────────────┐
│     RAG     │  ─ ✗ ─  │     MCP     │
│   :8080     │         │   :????     │
└─────────────┘         └─────────────┘
      │                       │
      │                       │
 ProjectInputSpec       DesignRequest
   (JSON)                 (Python)
```

### 7.2 Target Architecture (เป้าหมาย)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gateway (Mozart)                        │
│                       gate_way_new.py                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│   RAG Service   │             │   MCP Core v2   │
│   (Aura)        │             │   (Amadeus)     │
│   :8080         │             │   :8001         │
└────────┬────────┘             └────────┬────────┘
         │                               │
         │    ┌─────────────────┐        │
         │    │   MCP Adapter   │        │
         └───▶│ (mcp_adapter.py)│───────▶│
              │                 │        │
              │ convert_spec()  │        │
              └─────────────────┘        │
                                         │
                                         ▼
                              ┌─────────────────┐
                              │   AutoLISP      │
                              │   Output        │
                              └─────────────────┘
```

### 7.3 Files to Create

| File | Purpose |
|------|---------|
| `app/mcp_adapter.py` | Convert ProjectInputSpec → DesignRequest |
| `app/mcp_client.py` | HTTP client to call MCP Core |
| `app/routes.py` (update) | Add `/api/v1/design` endpoint |

---

## 8. Example End-to-End Flow

### Input (User)
```
"ออกแบบห้องนอน 1 ห้อง มีแอร์ 12000BTU และเต้ารับ 4 จุด"
```

### Step 1: RAG receives ProjectRequirements
```python
ProjectRequirements(
    project_name="ห้องนอน",
    building_type="residential",
    voltage_system="TH_1PH_230V",
    rooms=[
        RoomInput(name="ห้องนอน", type="bedroom", area_sqm=25.0)
    ],
    loads=[
        LoadInput(room_name="ห้องนอน", device="AC-12000BTU", quantity=1),
        LoadInput(room_name="ห้องนอน", device="SOCKET-16A", quantity=4)
    ]
)
```

### Step 2: RAG generates McpSpecResponse
```json
{
  "project_input": {
    "project_info": {
      "project_name": "ห้องนอน",
      "building_type": "RESIDENTIAL",
      "spec_version": "2.0"
    },
    "electrical_system": {
      "voltage_system": "TH_1PH_230V",
      "earthing": "TT"
    },
    "rooms": [
      {
        "room_id": "R1",
        "name": "ห้องนอน",
        "room_type": "BEDROOM",
        "template_code": "ROOMT-BEDROOM-STD",
        "area_sqm": 25.0
      }
    ],
    "loads": [
      {
        "load_id": "L1",
        "room_id": "R1",
        "device_code": "AC-12000BTU",
        "qty": 1
      },
      {
        "load_id": "L2",
        "room_id": "R1",
        "device_code": "SOCKET-16A",
        "qty": 4
      }
    ],
    "constraints": {
      "rule_profile_id": "TH_RESIDENTIAL_LV",
      "user_constraints": []
    }
  }
}
```

### Step 3: Adapter converts to DesignRequest
```python
DesignRequest(
    session_id="session_20251202_120000",
    project_name="ห้องนอน",
    loads=[
        ElectricalLoad(
            id="L1",
            name="AC-12000BTU",
            load_type=LoadType.HVAC,
            voltage=VoltageType.SINGLE_PHASE_240V,
            power_watts=1500,
            quantity=1,
            location=Location(room="ห้องนอน", floor="1"),
            is_continuous=True
        ),
        ElectricalLoad(
            id="L2",
            name="SOCKET-16A",
            load_type=LoadType.RECEPTACLE,
            voltage=VoltageType.SINGLE_PHASE_240V,
            power_watts=3680,
            quantity=4,
            location=Location(room="ห้องนอน", floor="1"),
            is_continuous=False
        )
    ],
    panels=[...],
    service_voltage=VoltageType.SINGLE_PHASE_240V,
    utility_service_size=100
)
```

### Step 4: MCP calculates and returns DesignResult
```python
DesignResult(
    calculations={
        "panel_001": {
            "total_va": 16220,  # 1500 + (3680*4)
            "total_current": 70.5,
            "demand_current": 56.4
        }
    },
    wire_sizing={
        "L1": {"wire_size": "10", "voltage_drop": 1.2%},
        "L2": {"wire_size": "12", "voltage_drop": 0.8%}
    },
    breaker_selections={
        "L1": {"breaker_rating": 20, "poles": 2},  # AC needs 240V
        "L2": {"breaker_rating": 20, "poles": 1}
    },
    compliance_report={"compliant": True}
)
```

### Final Output to User
```
✅ ผลการออกแบบห้องนอน:

📊 สรุปโหลด:
- รวม: 16,220 VA
- กระแสรวม: 70.5 A
- Demand: 56.4 A

🔌 วงจรแอร์ (L1):
- สาย: 10 mm² (THW)
- เบรกเกอร์: 20A 2P
- Voltage Drop: 1.2%

🔌 วงจรเต้ารับ (L2):
- สาย: 12 mm² (THW)  
- เบรกเกอร์: 20A 1P
- Voltage Drop: 0.8%

✅ ผ่านมาตรฐาน NEC/วสท.
```

---

## 📝 Summary

| Aspect | RAG (Aura) | MCP (Amadeus) |
|--------|------------|---------------|
| **หน้าที่** | แปลภาษามนุษย์ → Spec | คำนวณไฟฟ้า |
| **Input** | Natural language / ProjectRequirements | DesignRequest |
| **Output** | McpSpecResponse (JSON) | DesignResult |
| **Knowledge** | rag_knowledge/ (4 folders) | NEC baseline + catalog |
| **LLM** | Gemini 2.0 Flash | ไม่ใช้ LLM |
| **Port** | :8080 | :8001 (TBD) |

---

**Document maintained by:** Copilot  
**Last updated:** 2025-12-02

```