# ACA Mozart Copilot Instructions

## Architecture Overview
This is an electrical design RAG system: **Gateway → RAG/Copilot Service → MCP Core → AutoLISP/DXF**

- **RAG Service** (`app/`) = "Spec Engine" - transforms human requirements into MCP-compatible JSON specs
- **MCP Core** (external) = performs actual electrical calculations (pandapower, sizing, compliance)
- **Gateway** (`gate_way_new.py`) = intent routing (MOZART for technical, AMADEUS for chat), dialogue state

**Golden Rule**: RAG never calculates electrical values. It only maps human language → structured specs.

## Key Files & Patterns

### Data Contracts (`app/models_ACA.py`)
```python
# Input from user (human-readable)
ProjectRequirements  # project_name, building_type, voltage_system, rooms[], loads[], user_constraints[]

# Output to MCP (strict schema)
ProjectInputSpec  # project_info, electrical_system, rooms[RoomSpec], loads[LoadSpec], constraints
McpSpecResponse  # wraps project_input + standards_profile + llm_metadata
```
- All models use strict Pydantic typing - no `Dict[str, Any]`
- Room IDs: `R1, R2...`, Load IDs: `L1, L2...`, always sequential

### Knowledge System (`app/knowledge_service.py`)
Four folders under `rag_knowledge/`:
- `db/` - DEVICE_CODES.md, ROOM_TEMPLATES.md, catalog contracts
- `mcp/` - MCP design docs, input quality rules
- `standard/` - Thai electrical standards (วสท.)
- `example/` - Few-shot examples for prompt engineering

Use `KnowledgeService.get_docs_for_mcp_spec()` to retrieve context - it auto-prioritizes by `knowledge_index.json`.

### API Surface (`app/routes_ACA.py`)
```
POST /api/v1/ask         → QA about standards (returns StandardResponse)
POST /api/v1/mcp_spec    → Requirements → ProjectInputSpec (returns McpSpecResponse)
POST /api/v1/retrieve_raw → Debug retrieval hits
GET  /api/v1/knowledge/groups → List available doc groups
```

## Development Workflow

### Running Tests
```bash
pytest tests/ -v                     # All tests
pytest tests/ -v -m "not integration" # Unit tests only
```
Test cases in `tests/test_mcp_spec_cases.py` cover: basic house, heavy kitchen, incomplete data.

### Starting the Service
```bash
cp .env.example .env
# Set PROJECT_ID, LOCATION for Vertex AI
uvicorn app.routes_ACA:app --reload --port 8080
```

### Adding New Knowledge Documents
1. Add file to appropriate `rag_knowledge/{db,mcp,standard,example}/` folder
2. Update `rag_knowledge/knowledge_index.json` with metadata
3. Files without index entries still load (priority 50) but indexed get priority 60-95

## Critical Constraints

### What RAG Does NOT Do
- No voltage drop calculations
- No cable/breaker sizing
- No direct `amadeus.catalog` (Supabase) access - read from `rag_knowledge/db/` snapshots
- No DXF generation

### Validation Requirements
- Every `device_code` must exist in `rag_knowledge/db/DEVICE_CODES.md`
- Every `template_code` must exist in `rag_knowledge/db/ROOM_TEMPLATES.md`
- Every `room_id` in loads must reference an existing room
- LLM output must parse into `McpSpecResponse` - retry up to `RETRY_MAX_ATTEMPTS` on failure

### Trust Logging
Every `/api/v1/mcp_spec` call logs to `logs/mcp_spec/` (JSONL):
- Input requirements, retrieved docs, raw LLM output, parse success, validation errors

## Code Conventions

### Service Layer (`app/service_ACA.py`)
- `RagService.process_ask()` → handles `/ask`
- `RagService.generate_mcp_spec()` → handles `/mcp_spec` with 5-phase flow:
  1. Pre-validate requirements
  2. Generate human-readable plan (Thai)
  3. Build spec following plan
  4. Parse & validate
  5. Quality check (device codes, templates, semantic)

### Error Handling
- HTTP 400 = Invalid/incomplete requirements
- HTTP 422 = LLM output failed validation after retries (returns `InsufficientDataError`)
- HTTP 504 = LLM timeout

### Config (`app/config_ACA.py`)
All settings via `Settings` class with env override:
```python
MODEL_NAME_ANSWER = "gemini-2.0-flash-exp"
KNOWLEDGE_ROOT = BASE_DIR / "rag_knowledge"
RETRY_MAX_ATTEMPTS = 2
```

## Reference Documents
- `📜How to Design ACA_Mozart(new ver.).txt` - Full system design spec
- `🎑ACA_Mozart_Readme.md` - Detailed architecture overview
- `rag_knowledge/mcp/1)MCP_CAPABILITIES_AND_LIMITS.md` - MCP contract details
