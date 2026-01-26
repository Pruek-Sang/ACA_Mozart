# 🏛️ ACA_Mozart Architecture

> **Last Updated**: January 26, 2026  
> **Branch**: Production-3Phase  
> **Status**: Production Ready (Electrical 1P/3P Complete)

---

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ACA_Mozart Ecosystem                              │
│                    Electrical Design Automation System                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │
│  │  FRONTEND   │      │   GATEWAY   │      │    RAG      │                 │
│  │  (React)    │─────▶│  (FastAPI)  │─────▶│  (FastAPI)  │                 │
│  │  Port: 80   │      │  Port: 8000 │      │  Port: 8080 │                 │
│  └─────────────┘      └─────────────┘      └──────┬──────┘                 │
│                                                    │                        │
│                                                    ▼                        │
│                                            ┌─────────────┐                 │
│                                            │  MCP CORE   │                 │
│                                            │  (FastAPI)  │◀── BACKEND      │
│                                            │  Port: 5001 │                 │
│                                            └─────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
ACA_Mozart/
│
├── 📋 ARCHITECTURE.md              # 👈 This file - Project architecture
├── 📋 README.md                    # Project overview & quick start
├── 📋 Detail_work.md               # Development notes
│
├── 🐳 docker-compose.fullstack.yml # Full local dev stack
├── 🐳 docker-compose.prod.yml      # Production deployment
├── 🗑️ cleanup-policy.json          # Artifact Registry cleanup
│
│
├── ⚡ mcp_core_v2/                  # ══════ BACKEND (Electrical Engine) ══════
│   │
│   ├── 🚀 api.py                   # [BACKEND] FastAPI endpoints for MCP Core
│   ├── ⚙️ pipeline.py              # [BACKEND] Main orchestrator - calculation flow
│   ├── 📊 config.py                # [BACKEND] Configuration & settings
│   ├── ❌ exceptions.py            # [BACKEND] Custom exceptions
│   ├── 🔗 integration.py           # [BACKEND] CAD integration helpers
│   │
│   ├── 📦 models/                  # ══ Data Contracts ══
│   │   ├── contracts.py            # [BACKEND] Pydantic models (VoltageType, LoadType, etc.)
│   │   ├── catalog_models.py       # [BACKEND] Breaker, Wire catalog types
│   │   └── baseline.py             # [BACKEND] NEC/EIT baseline constants
│   │
│   ├── ⚡ core/                     # ══ Calculation Modules ══
│   │   ├── load_calculator.py      # [BACKEND] Current & load calculations (I=P/V×PF)
│   │   ├── wire_sizer.py           # [BACKEND] Wire sizing by ampacity & voltage drop
│   │   ├── breaker_selector.py     # [BACKEND] Breaker selection (MCB, RCBO, MCCB)
│   │   ├── circuit_grouper.py      # [BACKEND] Group loads into circuits
│   │   ├── conduit_sizer.py        # [BACKEND] Conduit sizing per NEC 310
│   │   ├── compliance_checker.py   # [BACKEND] NEC/EIT compliance validation
│   │   ├── autolisp_generator.py   # [BACKEND] Generate AutoCAD AutoLISP code
│   │   ├── sld_generator.py        # [BACKEND] Single Line Diagram data
│   │   ├── boq_service.py          # [BACKEND] Bill of Quantities service
│   │   ├── lighting_calculator.py  # [BACKEND] Lighting load calculations
│   │   ├── room_defaults.py        # [BACKEND] Default loads per room type
│   │   ├── template_resolver.py    # [BACKEND] Building template resolver
│   │   ├── result_builder.py       # [BACKEND] Format calculation results
│   │   ├── pandapower_adapter.py   # [BACKEND] Power flow analysis (if needed)
│   │   └── price_scraper.py        # [BACKEND] Price scraping utilities
│   │
│   ├── 🔧 context/                 # ══ Injectors (Safety Features) ══
│   │   ├── derating_injector.py    # [BACKEND] Temperature/grouping derating
│   │   ├── ka_rating_injector.py   # [BACKEND] Short-circuit kA rating
│   │   ├── ng_link_injector.py     # [BACKEND] Neutral-Ground link check
│   │   ├── phase_balance_injector.py # [BACKEND] 3-Phase balance check
│   │   ├── input_sanitizer_injector.py # [BACKEND] Input validation
│   │   ├── service_vd_injector.py  # [BACKEND] Service voltage drop
│   │   ├── three_phase_injector.py # [BACKEND] 3-Phase detection
│   │   ├── solar_cell_injector.py  # [BACKEND] Solar PV integration
│   │   └── vehicle_mode_injector.py # [BACKEND] EV charger support
│   │
│   ├── 💾 dal/                     # ══ Data Access Layer ══
│   │   └── catalog_dal.py          # [BACKEND] Catalog data access
│   │
│   ├── 📚 catalog/                 # ══ Product Catalogs ══
│   │   └── *.csv                   # [DATA] Breaker, wire, conduit prices
│   │
│   ├── 🐳 Docker/                  # ══ Container Config ══
│   │   ├── Dockerfile              # [DOCKER] MCP Core image (Python 3.12)
│   │   ├── .dockerignore           # [DOCKER] Build exclusions
│   │   └── .env.example            # [CONFIG] Environment template
│   │
│   ├── 🧪 tests/                   # ══ MCP Tests ══
│   │   ├── test_pipeline.py        # [TEST] Pipeline unit tests
│   │   ├── test_phase_balance.py   # [TEST] 3-Phase balance tests
│   │   └── test_input_sanitizer.py # [TEST] Input validation tests
│   │
│   ├── 📊 catalog_rows.csv         # [DATA] Main product catalog (117 items)
│   └── 📋 requirements.txt         # [CONFIG] Python dependencies
│
│
├── 🤖 Copilot-Mozart/              # ══════ RAG + FRONTEND + GATEWAY ══════
│   │
│   ├── 📌 pinecone_indexer.py      # [TOOL] Pinecone vector indexing (legacy)
│   │
│   └── 📁 ACA_Mozart-copilot[RAG]/ # ══ Main RAG Service ══
│       │
│       ├── 🚀 main_ACA.py          # [RAG] Entry point (uvicorn runner)
│       ├── 🌐 gate_way_new.py      # [GATEWAY] Intent router (Mozart/Amadeus)
│       ├── ✅ check_service.py     # [TOOL] Health check utility
│       │
│       ├── 📦 app/                 # ══ RAG Application ══
│       │   │
│       │   ├── 🚀 routes.py        # [RAG] FastAPI endpoints (/ask, /design, etc.)
│       │   ├── 🧠 service.py       # [RAG] Core business logic (3847 lines!)
│       │   ├── 📊 models.py        # [RAG] Pydantic request/response models
│       │   ├── ⚙️ config.py        # [RAG] Configuration settings
│       │   │
│       │   ├── 🔗 mcp_client.py    # [RAG] HTTP client to MCP Core
│       │   ├── 🔄 mcp_adapter.py   # [RAG] Convert RAG spec → MCP format
│       │   │
│       │   ├── 📚 knowledge_service.py # [RAG] Folder-based knowledge manager
│       │   ├── 🔒 session_store.py # [RAG] In-memory session storage
│       │   ├── 📝 trust_log.py     # [RAG] JSONL audit logging
│       │   ├── 🔍 audit_validator.py # [RAG] Validation utilities
│       │   │
│       │   ├── 🎯 intent/          # ══ Intent Detection ══
│       │   │   └── edit_detector.py # [RAG] Detect add/delete/modify intent
│       │   │
│       │   ├── 📝 parsers/         # ══ Input Parsing ══
│       │   │   ├── hybrid_parser.py # [RAG] Regex + LLM parser orchestrator
│       │   │   ├── regex_parser.py  # [RAG] Fast regex-based parsing
│       │   │   ├── llm_parser.py    # [RAG] LLM fallback parser
│       │   │   ├── normalizer.py    # [RAG] Text normalization (typos)
│       │   │   ├── edit_command.py  # [RAG] Edit command models
│       │   │   └── device_catalog.py # [RAG] Device name matching
│       │   │
│       │   ├── 🔧 context/         # ══ Stateful Context ══
│       │   │   ├── supabase_client.py # [RAG] Supabase connection (sessions)
│       │   │   ├── merge_engine.py  # [RAG] Merge edits into design
│       │   │   ├── session_injector.py # [RAG] Session management
│       │   │   ├── project_injector.py # [RAG] Project context
│       │   │   ├── audit_logger.py  # [RAG] Conversation logging
│       │   │   ├── validator.py     # [RAG] Input validation
│       │   │   └── design_templates.py # [RAG] Building templates
│       │   │
│       │   ├── 🖥️ display/         # ══ Output Rendering ══
│       │   │   ├── compute.py       # [RAG] Single source of truth for display data
│       │   │   ├── boq_renderer.py  # [RAG] Bill of Quantities generator
│       │   │   ├── sld_renderer.py  # [RAG] Single Line Diagram generator
│       │   │   ├── markdown_renderer.py # [RAG] Markdown report
│       │   │   ├── qc_certificate.py # [RAG] QC certificate generator
│       │   │   ├── assumptions_renderer.py # [RAG] Design assumptions
│       │   │   ├── explainable_qc.py # [RAG] Warning explanations
│       │   │   ├── audit_document.py # [RAG] Audit document generator
│       │   │   └── revision_diff.py # [RAG] Version diff display
│       │   │
│       │   ├── 📋 formatters/      # ══ Output Formatters ══
│       │   │   ├── markdown_formatter.py # [RAG] Markdown output
│       │   │   ├── pdf_formatter.py # [RAG] PDF table formatting
│       │   │   ├── audit_formatter.py # [RAG] Audit report format
│       │   │   └── full_report_builder.py # [RAG] Complete report builder
│       │   │
│       │   ├── 🛡️ middleware/      # ══ Request Middleware ══
│       │   │   ├── rate_limiter.py  # [RAG] API rate limiting
│       │   │   ├── admin_auth.py    # [RAG] Admin authentication
│       │   │   ├── download_guard.py # [RAG] Download protection
│       │   │   └── feedback_collector.py # [RAG] User feedback
│       │   │
│       │   ├── ✅ logic/           # ══ Business Logic ══
│       │   │   └── validation.py    # [RAG] Wire formatting validation
│       │   │
│       │   └── 🔧 utils/           # ══ Utilities ══
│       │       └── formatting.py    # [RAG] Text formatting helpers
│       │
│       ├── 🧠 core/                # ══ Core RAG Engine ══
│       │   ├── vector_adapter.py   # [RAG] Vector DB interface (FAISS/Chroma)
│       │   ├── faiss_db.py         # [RAG] FAISS implementation
│       │   ├── database.py         # [RAG] ChromaDB implementation
│       │   ├── ingest.py           # [RAG] Document ingestion
│       │   └── privacy.py          # [RAG] PII protection
│       │
│       ├── 📚 rag_knowledge/       # ══ Knowledge Base ══
│       │   ├── knowledge_index.json # [DATA] Document metadata & priority
│       │   ├── db/                 # [DATA] Device catalogs (DEVICE_CODES.md)
│       │   ├── example/            # [DATA] Few-shot examples
│       │   ├── mcp/                # [DATA] MCP capabilities docs
│       │   └── standard/           # [DATA] Thai EIT/TIS standards
│       │
│       ├── 🎨 frontend/            # ══════ FRONTEND (React) ══════
│       │   │
│       │   ├── 📋 package.json     # [FRONTEND] Dependencies & scripts
│       │   ├── ⚙️ vite.config.ts   # [FRONTEND] Vite build config
│       │   ├── ⚙️ tsconfig.json    # [FRONTEND] TypeScript config
│       │   ├── 🔍 eslint.config.js # [FRONTEND] Linting rules
│       │   ├── 🧪 vitest.config.ts # [FRONTEND] Unit test config
│       │   ├── 🎭 playwright.config.ts # [FRONTEND] E2E test config
│       │   │
│       │   └── src/
│       │       ├── 🏠 App.tsx      # [FRONTEND] Main app component
│       │       ├── 🚪 main.tsx     # [FRONTEND] Entry point
│       │       │
│       │       ├── 🧩 components/  # ══ UI Components ══
│       │       │   ├── ChatPanel.tsx # [FRONTEND] Chat interface
│       │       │   ├── ResultViewer.tsx # [FRONTEND] Results display
│       │       │   ├── BOQTab.tsx   # [FRONTEND] Bill of Quantities view
│       │       │   ├── SLDViewer.tsx # [FRONTEND] SLD diagram viewer
│       │       │   ├── ContextPanel.tsx # [FRONTEND] Site context form
│       │       │   ├── ProjectSelector.tsx # [FRONTEND] Project picker
│       │       │   ├── LoginPage.tsx # [FRONTEND] Auth UI
│       │       │   ├── HealthPanel.tsx # [FRONTEND] Service health
│       │       │   ├── QCCertificatePanel.tsx # [FRONTEND] QC display
│       │       │   ├── AssumptionsPanel.tsx # [FRONTEND] Assumptions
│       │       │   ├── HistoryPanel.tsx # [FRONTEND] Session history
│       │       │   ├── FeedbackModal.tsx # [FRONTEND] Feedback form
│       │       │   └── ...          # Other components
│       │       │
│       │       ├── 🔗 lib/         # ══ Frontend Services ══
│       │       │   ├── api.ts       # [FRONTEND] API client
│       │       │   ├── supabase.ts  # [FRONTEND] Supabase auth client
│       │       │   ├── utils.ts     # [FRONTEND] Utility functions
│       │       │   └── logger.ts    # [FRONTEND] Client-side logging
│       │       │
│       │       ├── 🪝 hooks/       # ══ React Hooks ══
│       │       │   └── useHealthTracker.ts # [FRONTEND] Health monitoring
│       │       │
│       │       └── 📦 types/       # ══ TypeScript Types ══
│       │           └── index.ts     # [FRONTEND] Shared type definitions
│       │
│       ├── 🐳 Docker/              # ══ Container Configs ══
│       │   ├── Dockerfile_light    # [DOCKER] RAG image (Python 3.11, FAISS)
│       │   ├── Dockerfile.frontend-cloudrun # [DOCKER] Frontend (nginx)
│       │   ├── docker-compose.yml  # [DOCKER] Local dev stack
│       │   ├── nginx.conf          # [DOCKER] Local nginx config
│       │   ├── nginx-cloudrun.conf # [DOCKER] Cloud Run nginx config
│       │   └── requirements_*.txt  # [CONFIG] Python dependencies
│       │
│       ├── 🚀 Dockerfile.gateway   # [DOCKER] Gateway image
│       │
│       └── 🧪 tests/               # ══ RAG Tests ══
│           ├── test_parser_logic.py # [TEST] Parser tests
│           ├── test_merge_logic.py # [TEST] Merge engine tests
│           ├── test_mcp_adapter.py # [TEST] Adapter tests
│           ├── test_crud_flow.py   # [TEST] CRUD operation tests
│           ├── test_e2e_integration.py # [TEST] E2E tests
│           ├── backend/            # [TEST] Backend API tests
│           └── ...
│
│
├── 🧪 tests/                       # ══════ ROOT LEVEL TESTS ══════
│   ├── test_e2e_data_flow.py      # [TEST] RAG ↔ MCP data flow
│   ├── test_gateway_router.py      # [TEST] Gateway routing tests
│   ├── test_rag_mcp_contract.py    # [TEST] Contract validation
│   ├── test_supabase_schema.py     # [TEST] Database schema tests
│   ├── test_three_phase_integration.py # [TEST] 3-Phase feature tests
│   ├── test_smoke_production.py    # [TEST] Production smoke tests
│   └── chaos/                      # [TEST] Chaos engineering tests
│
│
├── 📜 scripts/                     # ══════ UTILITY SCRIPTS ══════
│   └── *.sh                        # Build, deploy, test scripts
│
│
├── ⚙️ .github/                     # ══════ CI/CD ══════
│   │
│   ├── 📋 copilot-instructions.md  # [DOC] Copilot project instructions
│   │
│   └── 🔄 workflows/               # ══ GitHub Actions ══
│       ├── docker-build.yml        # [CI] Build & push all Docker images
│       ├── three-phase-test.yml    # [CI] 3-Phase feature tests
│       ├── e2e-browser.yml         # [CI] Playwright E2E tests
│       ├── load-test.yml           # [CI] Performance tests
│       ├── price-scraper.yml       # [CI] Scheduled price updates
│       └── security.yml            # [CI] Security scanning
│
│
├── 📁 Doc/                         # ══════ DOCUMENTATION ══════
│   └── *.md                        # Design docs, troubleshooting guides
│
│
└── 📁 MCP-tool+Auto lisp GEN/      # ══════ LEGACY/REFERENCE ══════
    └── *.md                        # Original MCP design documents
```

---

## 🔄 Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           REQUEST FLOW                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  👤 User Input (Thai/English)                                            │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────┐                                                         │
│  │  FRONTEND   │  React + TypeScript + Vite                              │
│  │  (Port 80)  │  • Chat interface                                       │
│  │             │  • Site context form                                    │
│  │             │  • Result display (BOQ, SLD, LoadSchedule)              │
│  └──────┬──────┘                                                         │
│         │ POST /api/ask                                                  │
│         ▼                                                                │
│  ┌─────────────┐                                                         │
│  │   GATEWAY   │  FastAPI + Intent Router                                │
│  │ (Port 8000) │  • Classify intent (Mozart/Amadeus)                     │
│  │             │  • Rate limiting                                        │
│  │             │  • CORS handling                                        │
│  └──────┬──────┘                                                         │
│         │ Proxy to RAG                                                   │
│         ▼                                                                │
│  ┌─────────────┐                                                         │
│  │     RAG     │  FastAPI + Google AI + FAISS                            │
│  │ (Port 8080) │  • Parse user intent                                    │
│  │             │  • Retrieve knowledge                                   │
│  │             │  • Generate MCP spec                                    │
│  │             │  • Merge edits (stateful)                               │
│  │             │  • Format output                                        │
│  └──────┬──────┘                                                         │
│         │ POST /api/v1/design                                            │
│         ▼                                                                │
│  ┌─────────────┐                                                         │
│  │  MCP CORE   │  FastAPI + Calculation Engine                           │
│  │ (Port 5001) │  • Load calculations (I = P/V×PF)                       │
│  │             │  • Wire sizing (ampacity + VD)                          │
│  │             │  • Breaker selection                                    │
│  │             │  • Circuit grouping                                     │
│  │             │  • Compliance check (NEC/EIT)                           │
│  │             │  • Generate AutoLISP                                    │
│  └──────┬──────┘                                                         │
│         │                                                                │
│         ▼                                                                │
│  📊 Calculation Results                                                  │
│       │                                                                  │
│       ▼ (Back up through RAG → Gateway → Frontend)                       │
│                                                                          │
│  🖥️ Display: LoadSchedule + BOQ + SLD + QC Certificate                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🐳 Docker Images

| Image | Registry | Port | Purpose |
|-------|----------|------|---------|
| `mozart-frontend` | Artifact Registry | 80 | React UI (nginx) |
| `mozart-gateway` | Artifact Registry | 8000 | Intent Router |
| `mozart-rag` | Artifact Registry | 8080 | RAG + Display |
| `mcp-core` | Artifact Registry | 5001 | Calculation Engine |

---

## 🔑 Key Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS | Modern SPA |
| **Gateway** | FastAPI, slowapi | Routing, rate limiting |
| **RAG** | FastAPI, Google AI (Gemini), FAISS, Pydantic | NLP + retrieval |
| **Backend** | FastAPI, Pydantic, NumPy | Electrical calculations |
| **Database** | Supabase (PostgreSQL) | Sessions, projects |
| **Vector DB** | FAISS (default), ChromaDB (optional) | Semantic search |
| **CI/CD** | GitHub Actions | Build, test, deploy |
| **Container** | Docker, Google Artifact Registry | Image management |
| **Hosting** | Google Cloud Run | Serverless containers |

---

## 📋 Component Legend

| Tag | Meaning |
|-----|---------|
| `[BACKEND]` | MCP Core - Electrical calculation engine |
| `[RAG]` | RAG Service - NLP, retrieval, spec generation |
| `[GATEWAY]` | Gateway - Intent routing & proxy |
| `[FRONTEND]` | React UI components |
| `[DOCKER]` | Container configuration |
| `[CI]` | GitHub Actions workflows |
| `[TEST]` | Test files |
| `[DATA]` | Data files (catalogs, knowledge) |
| `[CONFIG]` | Configuration files |
| `[DOC]` | Documentation |
| `[TOOL]` | Utility scripts |

---

## 🔌 Port Summary

| Service | Port | Protocol |
|---------|------|----------|
| Frontend (nginx) | 80 | HTTP |
| Gateway | 8000 | HTTP |
| RAG Service | 8080 | HTTP |
| MCP Core | 5001 | HTTP |
| Supabase | - | HTTPS (external) |

---

## 🚀 Quick Start

```bash
# Clone & navigate
git clone https://github.com/Pruek-Sang/ACA_Mozart.git
cd ACA_Mozart

# Start full stack (Docker)
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker
docker-compose up --build

# Access
# Frontend: http://localhost:80
# Gateway:  http://localhost:8000
# RAG:      http://localhost:8080
# MCP Core: http://localhost:5001
```

---

## 📊 Test Coverage

| Test Suite | Location | Purpose |
|------------|----------|---------|
| E2E Data Flow | `tests/test_e2e_data_flow.py` | RAG ↔ MCP integration |
| 3-Phase | `tests/test_three_phase_integration.py` | 3-Phase features |
| RAG Unit | `Copilot-Mozart/.../tests/` | RAG service tests |
| MCP Unit | `mcp_core_v2/tests/` | Calculation tests |
| Frontend | `frontend/tests/` | Component tests |
| E2E Browser | `frontend/e2e/` | Playwright tests |

---

## 🏗️ Future: Structural Engineering Module

```
ACA_Mozart/
├── mcp_core_v2/              # ⚡ Electrical (CURRENT)
│
└── structural_core/          # 🏗️ Structural (PLANNED)
    ├── core/
    │   ├── footing_designer.py
    │   ├── beam_designer.py
    │   └── column_designer.py
    ├── models/
    │   └── contracts.py
    ├── api.py
    ├── Dockerfile
    └── requirements.txt
```

---

*Generated by Copilot Agent | ACA_Mozart Architecture v3.0 | January 26, 2026*
