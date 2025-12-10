# 📋 ใบส่งมอบงาน ACA_Mozart Project
**วันที่**: 3 ธันวาคม 2025  
**ผู้ส่งมอบ**: Valkyrie (AI QA)  
**สถานะ**: MVP Phase 1-3 เสร็จ, รอ Testing

---

## 🎯 ภาพรวมโปรเจค

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACA_Mozart Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐     HTTP API      ┌──────────────────────┐  │
│   │  ACA_Mozart  │ ◄───────────────► │    MCP_Core v2       │  │
│   │    (RAG)     │    Port 8080      │  (Calculation Engine)│  │
│   │              │         ↓         │     Port 5001        │  │
│   │ - รับ input  │    JSON Request   │                      │  │
│   │ - วิเคราะห์   │         ↓         │ - คำนวณ Load         │  │
│   │ - ส่งผลลัพธ์  │    JSON Response  │ - เลือก Wire/Breaker │  │
│   │              │         ↓         │ - สร้าง AutoLISP     │  │
│   └──────────────┘    LISP Code      └──────────────────────┘  │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐                                             │
│   │    User      │  Copy LISP → AutoCAD                        │
│   └──────────────┘                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ คำเตือนสำคัญ

> **MCP_Core ≠ MCP Protocol**
> 
> - `MCP_Core v2` = **Calculation Engine** (คำนวณไฟฟ้า) - เป็น REST API ปกติ
> - `MCP Protocol` = Model Context Protocol (สำหรับ AI ↔ Tools) - **ยังไม่ได้ทำ**
> 
> ชื่อ "MCP" ในโปรเจคนี้ไม่เกี่ยวกับ MCP Protocol ของ Anthropic

---

## 📁 โครงสร้างไฟล์

```
/workspaces/ACA_Mozart/
├── mcp_core_v2/                    # Calculation Engine (REST API)
│   ├── api.py                      # FastAPI endpoints (port 5001)
│   ├── pipeline.py                 # Main orchestrator
│   ├── config.py                   # Settings (230V Thai standard)
│   ├── core/
│   │   ├── circuit_grouper.py      # ✅ NEW: Group circuits by floor
│   │   ├── lighting_calculator.py  # ✅ NEW: Lux calculation
│   │   ├── room_defaults.py        # ✅ NEW: Default room configs
│   │   ├── load_calculator.py      # Calculate load current
│   │   ├── wire_sizer.py           # Size wires + voltage drop
│   │   ├── breaker_selector.py     # Select breakers (+ RCBO)
│   │   ├── conduit_sizer.py        # Size conduits
│   │   ├── autolisp_generator.py   # Generate LISP code
│   │   └── ...
│   ├── models/
│   │   ├── contracts.py            # Pydantic models
│   │   ├── catalog_models.py       # BreakerType, WireSpec, etc.
│   │   └── baseline.py             # NEC/Thai standards
│   ├── dal/
│   │   └── catalog_dal.py          # Catalog data access
│   └── Docker/
│       └── Dockerfile              # Docker for MCP_Core
│
├── Copilot-Mozart/ACA_Mozart-copilot[RAG]/  # RAG Engine
│   ├── main_ACA.py                 # FastAPI app (port 8080)
│   ├── app/
│   │   ├── routes.py               # API endpoints
│   │   ├── service.py              # Business logic
│   │   ├── mcp_adapter.py          # Gateway to MCP_Core
│   │   ├── knowledge_service.py    # RAG retrieval
│   │   └── ...
│   ├── core/
│   │   ├── database.py             # Vector DB (ChromaDB)
│   │   ├── ingest.py               # Document ingestion
│   │   └── privacy.py              # Data privacy
│   ├── rag_knowledge/
│   │   └── db/
│   │       └── catalog_rows.csv    # Component catalog (117 rows)
│   └── Docker/
│       ├── Dockerfile_light        # Lightweight Docker
│       └── docker-compose.yml      # Both services
```

---

## ✅ สิ่งที่ทำเสร็จแล้ว

### 1. MCP_Core v2 - Calculation Engine

| Module | Status | Description |
|--------|--------|-------------|
| `load_calculator.py` | ✅ | คำนวณ current: `I = P / (V × PF)` |
| `wire_sizer.py` | ✅ | เลือก wire + คำนวณ voltage drop |
| `breaker_selector.py` | ✅ | เลือก breaker + **RCBO 30mA** (NEW) |
| `conduit_sizer.py` | ✅ | เลือกขนาดท่อร้อยสาย |
| `autolisp_generator.py` | ✅ | สร้าง AutoLISP code |
| `circuit_grouper.py` | ✅ NEW | รวม circuit ตามชั้น (lighting, receptacle) |
| `lighting_calculator.py` | ✅ NEW | คำนวณ Lux + เลือกหลอดไฟ |
| `room_defaults.py` | ✅ NEW | Default ห้อง (ขนาด, outlet ขั้นต่ำ) |

### 2. Thai Electrical Standards

| Standard | Value | Status |
|----------|-------|--------|
| Single-phase voltage | 230V | ✅ |
| Three-phase voltage | 400V | ✅ |
| Default power factor | 0.85 | ✅ |
| RCBO for wet locations | 30mA | ✅ |
| VD formula | `2×L×I×(R×cosθ+X×sinθ)/1000` | ✅ |

### 3. Circuit Grouping Logic

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| แอร์แยก Breaker | `CircuitType.HVAC` dedicated | ✅ |
| ห้องน้ำไม่มี Receptacle | `BATHROOM` excluded | ✅ |
| Lux calculation | `lighting_calculator.py` | ✅ |
| Lighting รวมตามชั้น | `LIGHTING` by floor | ✅ |
| Receptacle รวมตามชั้น | `RECEPTACLE` by floor | ✅ |
| Default 150 ตร.ม. | `room_defaults.py` | ✅ |
| เครื่องทำน้ำอุ่น RCBO | `WATER_HEATER` + RCBO 25A | ✅ |
| ขั้นต่ำ outlet ตาม ตร.ม. | `outlets_per_10sqm` | ✅ |
| Smart Home ready | `smart_home_ready` flag | ✅ |

### 4. RAG Engine (ACA_Mozart)

| Component | Status | Description |
|-----------|--------|-------------|
| Knowledge base | ✅ | ChromaDB + catalog_rows.csv |
| Device mapping | ✅ | 37 devices (+ 9 switches) |
| MCP adapter | ✅ | Gateway to MCP_Core |

### 5. Docker

| File | Status | Ports |
|------|--------|-------|
| `mcp_core_v2/Docker/Dockerfile` | ✅ | 5001 |
| `ACA_Mozart/Docker/Dockerfile_light` | ✅ | 8080 |
| `docker-compose.yml` | ✅ | Both services |

---

## ❌ สิ่งที่ยังไม่ได้ทำ

### 1. Testing
| Test Type | Status | Notes |
|-----------|--------|-------|
| Unit tests | ⏳ | มี test files แต่ยังไม่ได้ run ทั้งหมด |
| Integration tests | ❌ | RAG → MCP_Core flow |
| E2E tests | ❌ | User input → LISP output |
| AutoLISP validation | ❌ | ต้อง test ใน AutoCAD จริง |

### 2. AutoLISP
| Task | Status | Notes |
|------|--------|-------|
| Generate basic LISP | ✅ | Panel schedule, SLD |
| Test in AutoCAD | ❌ | ยังไม่ได้ทดสอบ |
| Complex drawings | ⏳ | Floor plan, lighting layout |

### 3. MCP Protocol (Save Files)
| Task | Status | Notes |
|------|--------|-------|
| MCP Server | ❌ | ยังไม่ได้สร้าง |
| Save file locally | ❌ | ต้องทำหลัง AutoLISP เสร็จ |
| AutoCAD integration | ❌ | Phase 3 |

### 4. UI/UX
| Task | Status | Notes |
|------|--------|-------|
| Web UI | ❌ | ยังไม่มี frontend |
| API documentation | ⏳ | มี FastAPI auto-docs |

---

## 🧪 วิธี Test

### 1. Start Services (Docker)
```bash
cd /workspaces/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker
docker-compose up -d
```

### 2. Start Services (Local)
```bash
# Terminal 1: MCP_Core
cd /workspaces/ACA_Mozart/mcp_core_v2
python api.py  # Port 5001

# Terminal 2: RAG
cd /workspaces/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]
python main_ACA.py  # Port 8080
```

### 3. Test MCP_Core API
```bash
curl http://localhost:5001/health
```

### 4. Test Circuit Grouper
```python
cd /workspaces/ACA_Mozart/mcp_core_v2
python -c '
from core.circuit_grouper import get_circuit_grouper
from models.contracts import ElectricalLoad, LoadType, VoltageType, Location

loads = [
    ElectricalLoad(
        id="light-1", name="Bedroom Light", 
        load_type=LoadType.LIGHTING,
        power_watts=60, 
        location=Location(floor="1", room="bedroom1"),
        voltage=VoltageType.SINGLE_PHASE_230V
    ),
]

grouper = get_circuit_grouper()
circuits = grouper.group_loads(loads)
print(f"Grouped into {len(circuits)} circuits")
'
```

---

## 📊 Catalog Status

| Type | Count | Status |
|------|-------|--------|
| COMPONENT | 31 | ✅ |
| APPLIANCE | 13 | ✅ |
| CABLE_SPEC | 11 | ✅ |
| CONDUIT_SPEC | 8 | ✅ |
| BREAKER | varies | ✅ |
| **Total** | **117 rows** | ✅ |

---

## 🔧 Environment

| Item | Value |
|------|-------|
| Python | 3.12.1 |
| FastAPI | latest |
| ChromaDB | latest |
| Docker | Available |
| OS | Ubuntu 24.04 (Dev Container) |

---

## 📝 Git Status

```
Repository: Pruek-Sang/ACA_Mozart
Branch: main
Last commit: 57b9168 (feat: Add circuit grouping modules)
```

### Recent Commits:
1. `57b9168` - feat: Add circuit grouping, lighting calculator, room defaults modules
2. Previous - Docker files, Thai 230V standard, RCBO support

---

## 🎯 Next Steps (สำหรับ AI ถัดไป)

### Priority 1: Testing
1. Run existing unit tests
2. Test RAG → MCP_Core integration
3. Validate AutoLISP output

### Priority 2: AutoLISP Completion
1. Test generated LISP in AutoCAD
2. Fix any LISP syntax issues
3. Add more drawing types (floor plan, lighting)

### Priority 3: MCP Protocol (Optional)
1. Create MCP Server for Claude Desktop
2. Implement local file saving
3. AutoCAD COM integration

---

## ⚡ Quick Reference

### Formulas (Verified ✅)

```
# Current (Single-phase)
I = P / (V × PF)
I = 1000W / (230V × 0.85) = 5.1A

# Current (Three-phase)
I = P / (√3 × V × PF)
I = 3000W / (1.732 × 400V × 0.85) = 5.1A

# Voltage Drop (Single-phase)
VD = 2 × L × I × (R×cosθ + X×sinθ) / 1000

# Lux Calculation
Required Lumens = Area × Lux × MF / UF
Fixtures = Lumens / Lumens_per_fixture
```

### Key Ports
| Service | Port |
|---------|------|
| MCP_Core | 5001 |
| RAG (ACA_Mozart) | 8080 |

### Key Files
| Purpose | File |
|---------|------|
| Main pipeline | `mcp_core_v2/pipeline.py` |
| Circuit grouping | `mcp_core_v2/core/circuit_grouper.py` |
| Device mapping | `ACA_Mozart/app/mcp_adapter.py` |
| Catalog | `ACA_Mozart/rag_knowledge/db/catalog_rows.csv` |

---

## 📞 Contact

หากมีคำถาม ให้ถาม Valkyrie หรือดู:
- `/workspaces/ACA_Mozart/COMPLETE_DOCUMENTATION.md`
- `/workspaces/ACA_Mozart/mcp_core_v2/README.md`

---

**End of Handover Document**
