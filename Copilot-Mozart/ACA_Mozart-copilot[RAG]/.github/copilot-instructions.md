# ACA Mozart Copilot Instructions

## 1. Canonical System Picture
- The production chain is **Gateway → Dialogue (CAC_Mozart) → Copilot/RAG Service → MCP Core → AutoLISP/DXF**. Do not collapse layers.
- `CAC_Mozart` is the dialogue state machine. It owns slot collection (`task_type`, `room_type`, `room_dimensions`, `equipment_list`, etc.), persists to Redis with 1h TTL, and never runs calculations.
- The Copilot service (`amadeus_copilot_service_new_(zone_2_the_engineer's_workshop).py` + `rag_real.py`) is stateless. It reads rules from `amadeus.catalog`, calls VectorDB + LLM, and hands off specs to MCP over HTTP.
- MCP (`amadeus_mcp_serverNEW`, `MCP calculate mix`) is the only place that performs deterministic electrical math (pandapower, sizing, compliance, layout). RAG must only supply structured specs.

## 2. Contracts You Must Honor
- **ProjectRequirements** (human intake) must include project/building metadata, voltage/earthing hints, room list, load list (room+device+qty), and user constraints. Dialogue fills these slots before calling `/api/v1/mcp_spec`.
- **ProjectInputSpec** is the handover contract to MCP (ref. MCP DESIGN HANDOVER §3.2). Required fields:
  - `project_info`: `project_name`, normalized `building_type`, `spec_version` (currently `2.0`).
  - `electrical_system`: `voltage_system` codes like `TH_1PH_230V`, `earthing` (TT/TN-S... ).
  - `rooms`: each has `room_id`, `name`, `room_type` enum, `template_code` (ROOMT-*).
  - `loads`: each has `load_id`, `room_id`, `device_code` mapped to catalog, `qty`, optional `notes`.
  - `constraints`: `rule_profile_id` + `user_constraints` list.
- **McpSpecResponse** wraps `project_input`, `standards_profile` (rule profile id + notes), and `llm_metadata` (model + retrieved doc ids). Validate with strict Pydantic models; never return free-form dicts.

## 3. RAG API Surface (FastAPI in `main.py`)
- `/api/v1/ask`: Conversational QA about standards. Requires anonymized query, retrieved docs, and cited sources. Include `metadata.llm_model` and `metadata.retrieved_docs`.
- `/api/v1/mcp_spec`: Consumes ProjectRequirements JSON, builds prompt using approved docs only, calls Gemini with `response_mime_type="application/json"`, validates into `McpSpecResponse`, retries on validation failure, otherwise return structured payload.
- `/api/v1/retrieve_raw`: Developer-only to inspect retrieval hits.
- `/api/v1/ingest` + `/api/v1/delete`: Manage VectorDB against the canonical knowledge sources. Always check file existence before enqueueing ingestion jobs.

## 4. Canonical Funnel & Knowledge Discipline
- Maintain `knowledge_index.json` describing every retrievable document (`id`, `path`, `group`, `tags`, `version`). Core groups: `mcp_spec`, `thai_standard`, `catalog_schema`, `example_project`.
- Implement `knowledge_service.py` that can `list_groups`, `list_docs(group)`, `load_doc(doc_id)`, and helpers like `get_docs_for_mcp_spec()`.
- Retrieval for `/api/v1/mcp_spec` must be scoped to `mcp_spec` + `catalog_schema` (+ relevant standards) instead of querying the entire corpus.
- Record a **trust log** per `/mcp_spec` call: incoming ProjectRequirements, doc ids pulled, raw LLM response, parsed ProjectInputSpec, validation result.

## 5. Privacy & Safety Requirements
- `PrivacyGuard` anonymizes both user queries and retrieved chunks (Thai ID 13 digits, 08/09/06 phone patterns, emails) before the LLM sees them.
- Grounding verification (`validate_grounding`) runs after each answer. Confidence = `Low` if ungrounded, otherwise `High` for top score >0.7, else `Medium`.
- RAG never performs voltage-drop, cable sizing, breaker selection, or catalog writes. All calculations must flow to MCP `/mcp/v2/run`.

## 6. Developer Workflow Checklist
1. Dialogue layer gathers slots → build `ProjectRequirements`.
2. Call `/api/v1/mcp_spec` → receive validated `McpSpecResponse`.
3. Forward `project_input` to MCP `/mcp/v2/run` and stream results back to user.
4. Keep Supabase (`amadeus.catalog`) interactions behind DALs; RAG reads standards via docs or VectorDB only.
5. Never rely on in-memory/demo stores. Use the actual VectorDatabase + Redis connectors defined in `core/`.

## 7. Testing & Quality Gates
- Provide at least 3 residential scenarios (e.g., single-story 2-bedroom, two-story with heavy kitchen, incomplete room metadata). For each, assert:
  - HTTP 200, non-empty rooms list, every room has id/type/template.
  - Every load references an existing room_id.
  - `constraints.rule_profile_id` present.
  - Snapshot `project_input` JSON for regression detection.
- `/api/v1/mcp_spec` must never emit fields MCP doesn’t recognize; fail fast with explicit errors if Pydantic validation fails after retries.
- Before handover, ensure `knowledge_index.json` exists, retrieval scopes honor groups, trust logs are written, and Gateway can invoke MCP without manual JSON fixes.

## 8. When in Doubt
- Re-read `📜How to Design ACA_Mozart(new ver.).txt` plus `Report FIX RAG.md` and `Omega Design Report`. Those files are the law for feature scope.
- Any new module must follow the separation-of-concerns above: Dialogue = slot control, Copilot = spec orchestration, MCP = math engine.
- If a requirement is missing from docs, ask for clarification instead of guessing; the system must prefer explicit constraints over heuristics.
