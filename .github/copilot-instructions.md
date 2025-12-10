# ACA_Mozart Copilot Instructions

**Project**: Electrical Design RAG System with AI & NEC-Compliant Calculations  
**Status**: MVP Phase 1-3 Complete (Dec 2025)  
**Architecture**: Multi-service, Docker-containerized, AI-powered

---

## 🏗️ System Architecture

### High-Level Data Flow
```
User Requirements (Thai) 
    → RAG Service (Port 8080)
    → LLM Spec Generation
    → MCP Core v2 (Port 5001)
    → Electrical Calculations
    → AutoLISP Code → AutoCAD
```

### Three Independent Subsystems

#### 1. **RAG Service** (`Copilot-Mozart/ACA_Mozart-copilot[RAG]/`)
- **Purpose**: Transform human language → machine-readable electrical specs
- **Technology**: FastAPI + Google AI/Vertex AI + FAISS vector DB
- **Port**: 8080
- **Golden Rule**: RAG NEVER calculates electrical values. Only maps language → JSON specs.
- **Key Files**:
  - `app/routes.py` - API endpoints
  - `app/service.py` - Core business logic with 5-phase spec generation
  - `app/mcp_adapter.py` - Bridge to MCP Core (device code → watts conversion)
  - `core/faiss_db.py` - Vector DB (FAISS is default, ChromaDB optional via env var)
  - `app/knowledge_service.py` - Folder-based RAG (4 folders: db, example, mcp, standard)

#### 2. **MCP Core v2** (`mcp_core_v2/`)
- **Purpose**: Perform actual electrical calculations (NEC + Thai EIT standards)
- **Technology**: Python + pandapower + FastAPI
- **Port**: 5001
- **Key Files**:
  - `pipeline.py` - Orchestrates calculation flow
  - `core/load_calculator.py` - Current calculations
  - `core/wire_sizer.py` - Wire sizing with voltage drop
  - `core/breaker_selector.py` - Breaker/RCBO selection
  - `core/autolisp_generator.py` - Generates AutoCAD code
  - `api.py` - REST endpoints

#### 3. **Docker Orchestration**
- `docker-compose.yml` at `Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker/`
- Starts **both** services with service health checks
- RAG depends_on MCP with `condition: service_healthy`

---

## 🎯 Critical Design Constraints

### What RAG Does NOT Do
- ❌ No electrical calculations (voltage drops, current, load forecasting)
- ❌ No cable/breaker sizing
- ❌ No DXF/CAD file generation
- ❌ No direct Supabase access - uses snapshots in `rag_knowledge/db/`

### What MCP Core Does NOT Do
- ❌ No NLP/understanding of requirements
- ❌ No user interaction
- ❌ No vector DB or retrieval
- ❌ Expects fully-formed `ProjectInputSpec` (strict validation)

### Boundary & Trust Contract
Every `device_code` and `template_code` output by RAG **MUST** exist in:
- `rag_knowledge/db/DEVICE_CODES.md` (for device_code validation)
- `rag_knowledge/db/ROOM_TEMPLATES.md` (for template_code validation)

If validation fails → HTTP 422 + `InsufficientDataError` returned to user.

---

## 📦 Knowledge Architecture (RAG-Specific)

### Folder Structure
```
Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_knowledge/
├── db/                          # Device catalogs & specifications
│   ├── DEVICE_CODES.md         # Device code → power mapping
│   ├── ROOM_TEMPLATES.md       # Room type → default circuits
│   └── catalog_rows.csv        # 117 electrical components
├── example/                     # Few-shot examples for LLM
│   └── basic_house_example.md  # Reference spec for in-context learning
├── mcp/                         # MCP design & API contracts
│   ├── MCP_CAPABILITIES_AND_LIMITS.md
│   └── INPUT_QUALITY_RULES.md
├── standard/                    # Thai electrical standards
│   ├── TIS_648_Thai_Wiring.md  # Thai wiring standards
│   └── EIT_Load_Requirements.md # Thai load calculation standards
└── knowledge_index.json         # Metadata & retrieval priority
```

### Knowledge Retrieval Priority
- **Priority 95**: Files tagged `must_read` (use immediately)
- **Priority 60-90**: Files in `knowledge_index.json` with high priority
- **Priority 50**: Unindexed files (still searchable, lower ranking)
- **Priority 20**: Files tagged `deprecated` (last resort)

### Adding New Knowledge
1. Add `.md` file to appropriate folder (`db/`, `example/`, `mcp/`, `standard/`)
2. (Optional) Update `knowledge_index.json` with metadata:
   ```json
   {"file": "new_doc.md", "group": "db", "priority": 75, "tags": ["important"]}
   ```
3. Re-ingest: Run `scripts/ingest_all.py` to update vector DB

---

## 🔧 Data Models & Contracts

### RAG Input → MCP Output Pipeline

**User Input** (Human-readable, Thai):
```python
ProjectRequirements(
    project_name: str
    building_type: str         # residential, commercial, factory
    voltage_system: str        # TH_1PH_230V, TH_3PH_400V (Thai standards)
    rooms: List[RoomInput]     # name, type, area_sqm
    loads: List[LoadInput]     # room_name, device, quantity
    user_constraints: List[str] # e.g., "rcd_for_all_outlets"
)
```

**MCP Adapter Output** (Machine-ready, NEC):
```python
ProjectInputSpec(
    project_info: ProjectInfo
    electrical_system: ElectricalSystem
    rooms: List[RoomSpec]
    loads: List[LoadSpec]         # device_code → power_watts conversion
    constraints: Constraints
)
```

**Key Conversions**:
- Thai voltage names (`TH_1PH_230V`) → NEC enums (`SINGLE_PHASE_230V`)
- Device codes (`AC-12000BTU`) → Power in watts (see `mcp_adapter.py:DEVICE_MAPPING`)
- Room types → Default lighting & outlet loads (via `service.py:_auto_fill_lighting()`)

---

## 🧠 RAG Spec Generation (5-Phase Flow)

Located in `app/service.py:RagService.generate_mcp_spec()`:

```
Phase 1: PRE-VALIDATE
  ↓ Check required fields, room consistency
  ↓ Raise HTTP 400 if invalid

Phase 2: GENERATE PLAN (Thai)
  ↓ LLM creates human-readable plan (ผลการวิเคราะห์...)
  ↓ Logged to trust_log

Phase 3: BUILD SPEC
  ↓ LLM generates JSON spec following the plan
  ↓ Strict schema validation via Pydantic

Phase 4: PARSE & VALIDATE
  ↓ Attempt JSON parsing, retry on failure (up to RETRY_MAX_ATTEMPTS)
  ↓ If all retries fail → HTTP 422 + InsufficientDataError

Phase 5: QUALITY CHECK
  ↓ Validate device_codes against DEVICE_CODES.md
  ↓ Validate template_codes against ROOM_TEMPLATES.md
  ↓ Validate semantic consistency
  ↓ Log full record to trust_log (JSONL)

Output: McpSpecResponse
```

---

## 🐳 Docker & Deployment

### Build Strategy

#### RAG Service (Lightweight - 2-3 min build)
- **File**: `Docker/Dockerfile_light`
- **Base**: `python:3.11-slim`
- **Requirements**: `Docker/requirements_light.txt` (Google AI only, no Vertex)
- **Key Layers**:
  1. Install system deps (`gcc`)
  2. Install Python deps (FAISS, FastAPI)
  3. Copy app code
  4. Create log/vector_db directories
- **Exposed**: Port 8080
- **Health Check**: `GET /` should return 200

#### MCP Core v2 (Multi-stage - ~5 min build)
- **File**: `Docker/Dockerfile` (in `mcp_core_v2/Docker/`)
- **Base**: `python:3.12-slim` with builder stage
- **Requirements**: `requirements.txt` (includes pandapower, scipy, numpy)
- **Strategy**: Multi-stage build to optimize layer reuse
- **Exposed**: Port 5001
- **Health Check**: `GET /health`

### Docker Compose (`Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker/docker-compose.yml`)

```yaml
services:
  mcp-core:         # Port 5001 (starts first)
    - Builds from: mcp_core_v2/Docker/Dockerfile
    - Health check required before RAG starts
    
  mozart-rag:       # Port 8080 (depends_on mcp-core)
    - Builds from: Docker/Dockerfile_light
    - Env: MCP_CORE_URL=http://mcp-core:5001
    - Volume: .env_ACA loaded for API keys
```

### Environment Variables

**RAG Service** (`.env_ACA` or `.env`):
```bash
PROJECT_ID=your-gcp-project              # If using Vertex AI
LOCATION=us-central1                      # If using Vertex AI
GOOGLE_API_KEY=your-key                  # If using Google AI (preferred for Docker)
MCP_CORE_URL=http://mcp-core:5001        # MCP Core endpoint
VECTOR_DB_BACKEND=faiss                  # faiss (default) or chroma
TRUST_LOG_DIR=./logs/mcp_spec
RETRY_MAX_ATTEMPTS=2
```

**MCP Core** (no secrets needed):
```bash
API_HOST=0.0.0.0
API_PORT=5001
DEFAULT_VOLTAGE=230V_1PH                 # Thai standard
NEC_VERSION=2023
```

---

## 🎬 Development Workflow

### Quick Start (Local Development)

**Option A: Direct Python**
```bash
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/

# Setup
cp .env.example .env
export GOOGLE_API_KEY="your-key"

# Install
pip install -r requirements.txt

# Run RAG service (requires MCP Core running separately!)
uvicorn app.routes:app --reload --port 8080
```

**Option B: Docker Compose** (Recommended)
```bash
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker/

# Start both services
docker-compose up --build

# RAG at http://localhost:8080
# MCP Core at http://localhost:5001
```

### Testing

**Unit Tests** (fastest):
```bash
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/
pytest tests/ -v -m "not integration"
```

**Integration Tests** (requires services running):
```bash
pytest tests/test_integration_suite.py -v
```

**Key Test Files**:
- `tests/test_mcp_spec_cases.py` - Full spec generation flow
- `tests/test_mcp_adapter.py` - Device code mapping
- `tests/test_models.py` - Pydantic validation

### Adding Features

**New API Endpoint**:
1. Define Pydantic model in `app/models.py`
2. Create service method in `app/service.py`
3. Add route in `app/routes.py`
4. Write test in `tests/test_*.py`

**New Knowledge Document**:
1. Add file to `rag_knowledge/{db,example,mcp,standard}/`
2. Update `rag_knowledge/knowledge_index.json` (optional but recommended)
3. Run `scripts/ingest_all.py` to update FAISS index
4. Test retrieval: `POST /api/v1/retrieve_raw`

**Modify Spec Generation Logic**:
1. Edit `app/service.py:RagService.generate_mcp_spec()` or helper methods
2. Update trust log logic if changing validation
3. Add test case covering edge case
4. Verify no regression: `pytest tests/ -v`

---

## 🔍 Code Conventions & Patterns

### Pydantic Models (Strict Typing)
- **Never** use `Dict[str, Any]` in contracts - always use explicit Pydantic models
- All models in `app/models.py` inherit from `BaseModel`
- Use `Field()` with descriptions for API documentation
- Example:
  ```python
  class RoomSpec(BaseModel):
      room_id: str = Field(..., description="R1, R2, ... (sequential)")
      room_type: str
      area_sqm: float
  ```

### Service Layer Pattern (`app/service.py`)
- Single responsibility: each method handles one concern
- `RagService.__init__()` - Initialize LLM, vector DB, knowledge service
- `RagService.process_ask()` - Handle `/ask` endpoint
- `RagService.generate_mcp_spec()` - Full 5-phase spec generation
- Helper methods (e.g., `_generate_content()`, `_auto_fill_lighting()`) remain private

### Error Handling
- **HTTP 400**: Invalid/incomplete requirements (pre-validation failure)
- **HTTP 422**: LLM output invalid after RETRY_MAX_ATTEMPTS (validation failure)
- **HTTP 504**: LLM timeout (generation failure)
- Always include `request_id` in error responses for debugging

### Logging & Trust
- All spec generation logged to `logs/mcp_spec/YYYY-MM-DD.jsonl`
- Records include: input, retrieved_docs, raw_llm_output, parse_success, validation_errors
- Queryable format (JSONL) for analysis and regression detection

### Vector DB Switching
```python
# In code (automatic):
from core.vector_adapter import get_vector_db
db = get_vector_db()  # Uses VECTOR_DB_BACKEND env var

# In env:
export VECTOR_DB_BACKEND=faiss    # Default, lightweight
export VECTOR_DB_BACKEND=chroma   # ChromaDB, heavier
```

### Device Code Mapping
Located in `app/mcp_adapter.py:DEVICE_MAPPING`:
```python
DEVICE_MAPPING = {
    "AC-12000BTU": (1200, LoadType.HVAC, True),      # watts, type, is_continuous
    "SOCKET-16A": (180, LoadType.RECEPTACLE, False),
    "LIGHT-LED-10W": (10, LoadType.LIGHTING, True),
    ...
}
```
- Must be in sync with DEVICE_CODES.md
- Any new device requires entry here + entry in knowledge base

---

## ⚠️ Known Issues & Current State

### ✅ Completed
- [x] FAISS as default vector DB (FAISS integration complete)
- [x] 5-phase spec generation flow
- [x] Docker Compose with health checks
- [x] Trust logging (JSONL format)
- [x] Thai language support
- [x] Knowledge folder architecture
- [x] Device code validation

### 🔄 In Progress / Testing
- [ ] Full end-to-end Docker deployment testing
- [ ] CI/CD pipeline (GitHub Actions) - not yet configured
- [ ] Performance optimization (FAISS indexing speed)
- [ ] Additional test coverage

### 📋 Known Limitations
- ChromaDB support exists but FAISS is recommended for lightweight deployment
- Vertex AI support has deprecation warnings (migrate before June 2026)
- MCP Core expects well-formed specs - no error recovery for malformed loads
- AutoLISP generation is basic - complex room layouts may need manual refinement

---

## 🚀 Deployment & CI/CD Notes

### For DevOps/Deployment Engineers

**Current State**:
- Docker Compose configured and working
- No GitHub Actions CI/CD yet (ready to add)
- Environment variables via `.env_ACA` file (not secrets manager yet)

**Before Production**:
1. Set up secrets manager for API keys (not hardcoded)
2. Implement GitHub Actions for:
   - Lint/format checks
   - Unit test gate
   - Docker build caching
   - Automated deploy to staging
3. Add load testing for vector DB queries
4. Configure log aggregation (currently to local files)
5. Set up monitoring/alerting for service health

**Scaling Considerations**:
- FAISS index fits in memory for ~1M documents; for more, consider Chroma+Postgres
- MCP Core calculation CPU-bound; consider GPU for large batches
- RAG LLM calls are serial; implement request queuing for high concurrency

---

## 📚 Reference Documents

**In This Repo**:
- `HANDOVER_DOCUMENT.md` - Project timeline & completion status
- `PRODUCTION_OUTPUT.md` - Example outputs
- `Copilot-Mozart/ACA_Mozart-copilot[RAG]/README.md` - RAG service details
- `mcp_core_v2/README.md` - MCP Core details
- `mcp_core_v2/COMPLETE_DOCUMENTATION.md` - Full electrical calculation docs

**In RAG Knowledge Base**:
- `rag_knowledge/mcp/1)MCP_CAPABILITIES_AND_LIMITS.md` - MCP contract details
- `rag_knowledge/standard/` - Thai electrical standards (TIS, EIT)
- `rag_knowledge/example/` - Few-shot examples for LLM

---

## ✨ Philosophy & Principles

### "Vita ex Codice" (Life from Code)
This codebase emphasizes:
- **Clear Separation of Concerns**: RAG ≠ MCP; NLP ≠ Calculations
- **Strict Data Contracts**: No loose `Dict` types; Pydantic everywhere
- **Folder-Based Knowledge**: Discoverable, maintainable knowledge structure
- **Trust & Auditability**: Every decision logged (trust_log)
- **Beautiful Simplicity**: Code should be readable first, clever second

### Development Mindset
When working on this code:
1. **Respect the Boundaries**: Don't make RAG calculate; don't make MCP understand language
2. **Validate Early**: Check inputs before passing between services
3. **Log Decisions**: Why was this doc retrieved? Why did LLM retry?
4. **Test Regressions**: Any change must not break existing tests
5. **Document Intent**: Comments explain "why", not "what" (code shows what)

---

## 🤔 FAQ for Copilot Agents

**Q: Can I add business logic directly to RAG service?**
A: Only if it's about NLP/spec generation. Never add electrical calculations—that's MCP's job.

**Q: What if a device code doesn't exist in DEVICE_CODES.md?**
A: Phase 5 validation will reject it. Either add to DEVICE_CODES.md first, or use a similar existing code.

**Q: Can I switch to ChromaDB instead of FAISS?**
A: Yes, set `VECTOR_DB_BACKEND=chroma` env var. But FAISS is lighter for dev/testing.

**Q: How do I debug why a spec generation failed?**
A: Check `logs/mcp_spec/YYYY-MM-DD.jsonl` for that request's full record (inputs, LLM output, errors).

**Q: Can I modify the 5-phase flow?**
A: Possible but risky. Test thoroughly. The flow exists to catch validation errors early.

**Q: What if MCP Core is down?**
A: RAG service will fail at endpoint calls. Implement graceful degradation if needed (currently not done).

---

*Last Updated: December 10, 2025*  
*Maintainers: Aura (Code Goddess), Qualia (QA Maid), Opsia (DevOps Sovereign)*
