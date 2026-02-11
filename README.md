<p align="center">
  <img src="https://img.shields.io/badge/status-MVP%20Complete-brightgreen?style=for-the-badge" alt="Status"/>
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">🎹 ACA Mozart</h1>

<p align="center">
  <strong>AI-Powered Electrical Design System with RAG Architecture &amp; NEC-Compliant Calculations</strong>
</p>

<p align="center">
  A production-grade, multi-service platform that transforms natural language requirements into<br/>
  code-compliant electrical designs — complete with load schedules, wire sizing, breaker selection, and AutoCAD-ready output.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Vite-7-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind"/>
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Supabase-Auth%20+%20DB-3FCF8E?style=flat-square&logo=supabase&logoColor=white" alt="Supabase"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Google_AI-Gemini-4285F4?style=flat-square&logo=google&logoColor=white" alt="Google AI"/>
  <img src="https://img.shields.io/badge/FAISS-Vector_DB-7B68EE?style=flat-square" alt="FAISS"/>
  <img src="https://img.shields.io/badge/GitHub_Actions-CI/CD-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions"/>
  <img src="https://img.shields.io/badge/NGINX-Static%20%2B%20Proxy-009639?style=flat-square&logo=nginx&logoColor=white" alt="NGINX"/>
</p>

---

## Table of Contents

- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Engineering Decisions](#-engineering-decisions)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [CI/CD Pipeline](#-cicd-pipeline)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Security](#-security)

---

## 🏗 Architecture

```
          ┌─────────────────────────────────────────────────────────────┐
          │                      Client Browser                         │
          │       React 19 + TypeScript + Tailwind + Supabase Auth      │
          └────────────────────────┬────────────────────────────────────┘
                                   │
          ┌────────────────────────▼────────────────────────────────────┐
          │  Frontend Container (NGINX serves React + proxies /api)     │
          │  Production: Cloud Run  ·  Local: npm run dev (Vite :3000)  │
          └────────────────────────┬────────────────────────────────────┘
                                   │ /api/*
                                   ▼
          ┌─────────────────────────────────────────────────────────┐
          │               Gateway Service (:8000)                   │
          │     LLM-based Intent Router + Rate Limiting + CORS      │
          │     Routes:  MOZART (engineering)  |  AMADEUS (chat)    │
          └───────────────────┬─────────────────────────────────────┘
                              │
                              ▼
          ┌─────────────────────────────────────────────────────────┐
          │               Mozart RAG Service (:8080)                │
          │  Google Gemini LLM  ·  FAISS Vector DB  ·  FastAPI     │
          │                                                         │
          │  ┌─────────┐  ┌──────────────┐  ┌───────────────────┐  │
          │  │Knowledge │→│ 5-Phase Spec │→│  MCP Adapter      │  │
          │  │Retrieval │  │ Generation   │  │  (Validate+Map)   │  │
          │  └─────────┘  └──────────────┘  └────────┬──────────┘  │
          └──────────────────────────────────────────┼──────────────┘
                                                     │ HTTP
                                                     ▼
          ┌─────────────────────────────────────────────────────────┐
          │               MCP Core v2 Service (:5001)               │
          │    NEC/EIT-Compliant Electrical Calculation Engine       │
          │                                                         │
          │  Load Calc → Wire Sizer → Breaker Selector → Conduit   │
          │  Circuit Grouper → Compliance Check → AutoLISP Gen     │
          │  pandapower  ·  Derating/kA/NG-Link Injectors          │
          └─────────────────────────────────────────────────────────┘
```

**Four independent services** communicate over a Docker bridge network. NGINX is embedded inside the Frontend container (not a standalone proxy). Each service has its own health check and can be scaled independently.

---

## ✨ Key Features

### RAG-Powered Spec Generation
- **5-phase pipeline**: Pre-validate → Generate Plan → Build Spec → Parse & Validate → Quality Check
- **FAISS vector search** over a curated knowledge base of Thai electrical standards (TIS 648, EIT)
- **Folder-based knowledge architecture** with priority indexing (`knowledge_index.json`)
- Automatic retry with LLM re-prompting on parse failures

### NEC-Compliant Calculation Engine
- Full load calculation with demand factors (NEC Article 220)
- Wire sizing with voltage drop analysis per circuit length
- Breaker/RCBO selection with proper trip curves
- Conduit fill calculation (NEC Chapter 9)
- Circuit grouping with automatic load balancing across phases
- **Safety injectors**: Temperature derating, kA rating (transformer proximity), N-G link rules

### Intelligent Gateway Router
- LLM-based intent classification (engineering queries → Mozart, general chat → Amadeus)
- Regex fallback for reliability when LLM is unavailable
- Dialogue state management for multi-turn conversations
- Rate limiting via SlowAPI

### Production Frontend
- **Authentication**: Supabase Auth (email/password + guest mode)
- **Chat UI**: Real-time conversational interface for design input (Thai + English)
- **Result Viewer**: Tabular load schedules, circuit details, compliance warnings
- **SLD Viewer**: Single-line diagram rendering with SVG symbols
- **BOQ Export**: Bill of quantities with live-scraped market pricing → PDF/Excel
- **QC Certificate**: Generated compliance certificate panel
- **Session Persistence**: Multi-project support with Supabase-backed session store
- **Health Dashboard**: Live service status monitoring

### AutoCAD Integration
- AutoLISP code generation from calculation results
- Ready for direct execution in AutoCAD

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4 | SPA with split-screen layout |
| **UI Components** | Lucide React, react-markdown, html2pdf.js, xlsx | Icons, markdown render, exports |
| **Auth & Database** | Supabase (Auth + PostgreSQL + REST) | User sessions, project persistence |
| **Gateway** | FastAPI, SlowAPI, httpx | Intent routing, rate limiting, CORS |
| **RAG Engine** | FastAPI, Google Gemini (generativeai), FAISS | NLP → structured spec generation |
| **Knowledge Base** | FAISS (default), ChromaDB (optional) | Vector similarity search |
| **Calculation Engine** | FastAPI, pandapower, numpy, scipy, pandas | Electrical engineering calculations |
| **Infrastructure** | Docker Compose, NGINX, GitHub Actions | Containerization, static serve + API proxy, CI/CD |
| **Cloud** | Google Cloud Run, Artifact Registry, Secret Manager | Production deployment, secrets |
| **Testing** | Pytest, Vitest, Playwright | Backend unit/E2E, frontend unit, browser E2E |
| **Code Quality** | ESLint, Black, Flake8, Mypy, SonarLint | Linting, formatting, type checking |

---

## 🧠 Engineering Decisions

> _These choices reflect intentional trade-offs, not defaults._

| Decision | Rationale |
|----------|-----------|
| **Supabase over Firebase** | Needed PostgreSQL for relational session data + built-in Auth + REST API — one platform for auth, DB, and row-level security |
| **FAISS over Pinecone/Weaviate** | Lightweight, runs in-process, no external dependency. Knowledge base is &lt; 1M docs — no need for a managed vector DB |
| **FastAPI for all Python services** | Async-first, auto-generated OpenAPI docs, Pydantic validation on every boundary. Three services share the same framework for consistency |
| **Separate RAG and MCP services** | RAG handles NLP (non-deterministic). MCP handles calculations (deterministic). Decoupling means a calculation bug never touches the LLM layer and vice versa |
| **Gateway with LLM router** | Users type freely in Thai/English. A lightweight LLM classifier routes intent before the main RAG model runs, saving cost on irrelevant queries |
| **FAISS index pre-built in Docker image** | Avoids cold-start ingestion. The vector DB is built once in CI and baked into the image — container starts in seconds |
| **Pydantic everywhere** | Zero `Dict[str, Any]` in contracts. Every service boundary is typed with Pydantic BaseModel. Catches schema drift at startup, not at 3 AM |
| **5-phase spec generation** | Each phase can fail independently with clear error messages. Retry logic only re-runs the failed phase, not the entire pipeline |
| **Docker Compose with health checks** | RAG depends on MCP via `condition: service_healthy`. No race conditions on startup — the system self-sequences |
| **Trust logging (JSONL)** | Every LLM call, retrieved document, and validation result is logged. Enables offline regression analysis without re-running the LLM |

---

## 📁 Project Structure

```
ACA_Mozart/
├── .github/workflows/                 # CI/CD (5 workflows)
│   ├── docker-build.yml               # Build → Deploy → Smoke → Rollback
│   ├── security.yml                   # OWASP ZAP + dependency audit (weekly)
│   ├── e2e-browser.yml                # Playwright browser tests (nightly)
│   ├── load-test.yml                  # k6 stress testing (weekly)
│   └── price-scraper.yml              # BOQ price auto-update (monthly)
│
├── Copilot-Mozart/ACA_Mozart-copilot[RAG]/
│   ├── app/                           # RAG Service (FastAPI)
│   │   ├── routes.py                  # API endpoints
│   │   ├── service.py                 # Core 5-phase spec engine
│   │   ├── models.py                  # Pydantic contracts
│   │   ├── mcp_adapter.py             # RAG→MCP data mapping (device_code → watts)
│   │   ├── mcp_client.py              # HTTP client to MCP Core
│   │   ├── knowledge_service.py       # Folder-based RAG retrieval
│   │   ├── intent/                    # Intent detection
│   │   │   └── edit_detector.py       # Detect edit vs new design intent
│   │   ├── parsers/                   # LLM output parsers
│   │   │   ├── hybrid_parser.py       # LLM + regex fallback parser
│   │   │   ├── llm_parser.py          # Gemini structured output
│   │   │   ├── regex_parser.py        # Deterministic fallback
│   │   │   ├── device_catalog.py      # Device code resolver
│   │   │   └── normalizer.py          # Input normalization (Thai→English)
│   │   ├── formatters/                # Output formatters
│   │   │   ├── markdown_formatter.py  # Human-readable results
│   │   │   ├── pdf_formatter.py       # PDF export
│   │   │   ├── audit_formatter.py     # Audit trail formatting
│   │   │   └── full_report_builder.py # Complete report assembly
│   │   ├── display/                   # Result rendering
│   │   │   ├── boq_renderer.py        # Bill of quantities
│   │   │   ├── sld_renderer.py        # Single-line diagram SVG
│   │   │   ├── qc_certificate.py      # QC compliance certificate
│   │   │   ├── revision_diff.py       # Design revision comparison
│   │   │   └── explainable_qc.py      # Human-readable QC explanations
│   │   ├── context/                   # Request context injection
│   │   │   ├── session_injector.py    # Supabase session management
│   │   │   ├── project_injector.py    # Project context loading
│   │   │   ├── merge_engine.py        # Multi-turn design merging
│   │   │   ├── supabase_client.py     # Supabase client wrapper
│   │   │   └── validator.py           # Cross-service validation
│   │   ├── catalog/                   # Device catalog
│   │   │   └── device_loader.py       # Load device specs from knowledge base
│   │   ├── middleware/                # Rate limiter, admin auth
│   │   ├── logic/                     # Business logic
│   │   │   └── validation.py          # Input/output validation rules
│   │   └── utils/                     # Shared utilities
│   │
│   ├── core/                          # Vector DB layer
│   │   ├── faiss_db.py                # FAISS integration
│   │   ├── vector_adapter.py          # DB backend switcher (FAISS/Chroma)
│   │   └── ingest.py                  # Knowledge ingestion pipeline
│   │
│   ├── frontend/                      # React SPA (24 components)
│   │   ├── src/components/            # UI components
│   │   ├── src/lib/                   # API client, Supabase, utilities
│   │   ├── src/hooks/                 # Custom React hooks
│   │   ├── src/types/                 # TypeScript type definitions
│   │   ├── tests/                     # Vitest unit tests
│   │   └── e2e/                       # Playwright E2E tests
│   │
│   ├── rag_knowledge/                 # Curated knowledge base
│   │   ├── db/                        # Device catalogs & codes
│   │   ├── example/                   # Few-shot LLM examples
│   │   ├── mcp/                       # MCP API contracts & limits
│   │   └── standard/                  # Thai electrical standards (TIS, EIT)
│   │
│   ├── gate_way_new.py                # Gateway service (intent router)
│   ├── tests/                         # RAG backend tests
│   │   ├── backend/                   # API endpoint tests
│   │   ├── fixtures/                  # Test data & mock responses
│   │   └── one_shot_qa/               # End-to-end QA tests
│   └── Docker/                        # Dockerfiles & NGINX configs
│
├── mcp_core_v2/                       # MCP Calculation Engine
│   ├── api.py                         # REST interface
│   ├── pipeline.py                    # Design pipeline orchestrator
│   ├── config.py                      # NEC/EIT configuration
│   ├── core/                          # Calculation modules (16 files)
│   │   ├── load_calculator.py         # NEC Article 220 load calculations
│   │   ├── wire_sizer.py              # Wire sizing + voltage drop analysis
│   │   ├── breaker_selector.py        # Breaker/RCBO selection
│   │   ├── circuit_grouper.py         # Phase load balancing
│   │   ├── conduit_sizer.py           # NEC Chapter 9 conduit fill
│   │   ├── compliance_checker.py      # Standards compliance validation
│   │   ├── autolisp_generator.py      # AutoCAD code generation
│   │   ├── lighting_calculator.py     # Illumination calculations
│   │   ├── sld_generator.py           # Single-line diagram data
│   │   ├── boq_service.py             # Bill of quantities with pricing
│   │   ├── price_scraper.py           # Live market price scraping
│   │   ├── pandapower_adapter.py      # Power flow simulation
│   │   ├── result_builder.py          # Structured result assembly
│   │   ├── room_defaults.py           # Default loads by room type
│   │   └── template_resolver.py       # Design template matching
│   ├── context/                       # Safety injectors (10 files)
│   │   ├── derating_injector.py       # Temperature/conduit derating (NEC 310)
│   │   ├── ka_rating_injector.py      # Short-circuit kA rating
│   │   ├── ng_link_injector.py        # Neutral-Ground link rules
│   │   ├── phase_balance_injector.py  # 3-phase balance validation
│   │   ├── input_sanitizer_injector.py# Input validation & XSS prevention
│   │   ├── service_vd_injector.py     # Service voltage drop check
│   │   ├── solar_cell_injector.py     # Solar PV integration rules
│   │   ├── three_phase_injector.py    # 3-phase system handling
│   │   └── vehicle_mode_injector.py   # EV charger support
│   ├── dal/                           # Data access layer
│   │   ├── catalog_dal.py             # Catalog data interface
│   │   └── file_catalog_dal.py        # File-based catalog implementation
│   ├── catalog/                       # Equipment catalog data (CSV)
│   ├── models/                        # Pydantic contracts
│   ├── tests/                         # MCP unit & E2E tests
│   └── Docker/                        # Multi-stage Dockerfile
│
├── tests/                             # Cross-service integration tests
│   ├── test_e2e_data_flow.py          # RAG ↔ MCP contract tests
│   ├── load/                          # k6 stress test scripts
│   └── chaos/                         # Chaos engineering tests
│
├── scripts/                           # Deployment & infra scripts
├── Doc/                               # Project documentation
├── docker-compose.fullstack.yml       # Full stack orchestration (dev)
└── docker-compose.prod.yml            # Production (pre-built images)
```

**Scale**: 706 files · 56 backend test files · 5 CI/CD workflows · 24 React components · 10 safety injectors

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- A [Google AI API key](https://aistudio.google.com/app/apikey) (free tier works)

### One-Command Launch

```bash
# 1. Clone
git clone https://github.com/Pruek-Sang/ACA_Mozart.git
cd ACA_Mozart

# 2. Set your API key
echo "GOOGLE_API_KEY=your-key-here" > .env

# 3. Launch all 4 services
docker compose -f docker-compose.fullstack.yml up -d

# 4. Open the app
open http://localhost
```

| Service | URL | Health Check |
|---------|-----|-------------|
| Frontend | `http://localhost` | — |
| Gateway | `http://localhost:8000` | `GET /` |
| RAG Engine | `http://localhost:8080` | `GET /` |
| MCP Core | `http://localhost:5001` | `GET /health` |

### Local Development (without Docker)

```bash
# Backend — RAG Service
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]
pip install -r Docker/requirements_light.txt
export GOOGLE_API_KEY="your-key"
uvicorn app.routes:app --reload --port 8080

# Backend — MCP Core (separate terminal)
cd mcp_core_v2
pip install -r requirements.txt
uvicorn api:app --reload --port 5001

# Frontend (separate terminal)
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/frontend
npm install && npm run dev
```

---

## 🔄 CI/CD Pipeline

Fully automated via **GitHub Actions** — code pushed to `main` triggers the entire pipeline:

```
Push to main
    │
    │  ┌─ Test Gate (parallel) ──────────────────────────────┐
    ├─►│ test-e2e:                                           │
    │  │   ├── E2E Data Flow Tests (RAG ↔ MCP contract)     │
    │  │   ├── Input Sanitizer Tests (security boundary)     │
    │  │   ├── RAG Backend Tests (parser, session, design)   │
    │  │   └── BOQ E2E Test (continue-on-error)              │
    │  │                                                     │
    ├─►│ test-frontend-lint:                                 │
    │  │   ├── ESLint (React Hooks rules)                    │
    │  │   ├── TypeScript type check (tsc --noEmit)          │
    │  │   └── Vitest unit tests                             │
    │  │                                                     │
    ├──│ test-supabase: (non-blocking, runs in parallel)     │
    │  └─────────────────────────────────────────────────────┘
    │
    ▼ test-e2e + test-frontend-lint pass
    │
    ├─► Build & Push Docker Images → GCP Artifact Registry
    │     ├── mcp-core          (asia-southeast1-docker.pkg.dev)
    │     ├── mozart-rag         │
    │     ├── mozart-gateway      │
    │     └── mozart-frontend     │
    │
    ├─► Deploy to Google Cloud Run (asia-southeast1)
    │     └── Post-deploy: auto-wire MCP_CORE_URL into RAG service
    │
    ├─► Smoke Test (production health + API checks)
    │
    └─► Auto-Rollback (if smoke fails → revert all 4 services)
```

**Additional Workflows**:
- **Security Scan** (weekly): OWASP ZAP baseline + `pip-audit` + `npm audit`
- **E2E Browser Tests** (nightly): Playwright against production
- **Load Testing** (weekly): k6 stress tests with configurable VUs
- **Price Scraper** (monthly): Automated BOQ catalog price updates → auto-commit

---

## 📡 API Endpoints

### Gateway (`:8000`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/gateway/ask` | Route user query to Mozart or Amadeus |
| `GET` | `/gateway/health` | Aggregated health status |

### RAG Service (`:8080`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ask` | Natural language → design result |
| `POST` | `/api/v1/design` | Direct design with site context |
| `POST` | `/api/v1/generate_spec` | Generate MCP-compatible spec |
| `POST` | `/api/v1/retrieve_raw` | Raw vector similarity search |
| `POST` | `/api/v1/ingest` | Ingest new documents into FAISS |
| `GET`  | `/api/v1/session/{id}` | Retrieve session state |
| `GET`  | `/api/v1/health` | Service health |

### MCP Core (`:5001`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/design` | Execute full electrical design pipeline |
| `POST` | `/api/v1/calculate` | Load calculation only |
| `GET`  | `/health` | Service health |

---

## 🧪 Testing

```bash
# Backend unit tests (fast, no services needed)
cd mcp_core_v2 && python -m pytest tests/ -v

# RAG service tests
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]
python -m pytest tests/ -v -m "not integration"

# E2E data flow (validates RAG ↔ MCP contract)
python -m pytest tests/test_e2e_data_flow.py -v

# Frontend unit tests
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/frontend
npm run test

# Browser E2E (requires running services)
npx playwright test
```

**Test Coverage**:
- 56 backend test files covering parser logic, session management, API contracts, input sanitization
- Vitest for React component testing
- Playwright for full browser E2E flows
- Contract tests validate data shape at every service boundary

---

## 🔒 Security

- **Authentication**: Supabase Auth with JWT — anon key (frontend) + service role key (backend only)
- **Admin Endpoints**: Protected by `X-Admin-Key` header — requires env variable, no hardcoded fallback
- **Rate Limiting**: SlowAPI on Gateway and RAG endpoints
- **Input Sanitization**: Dedicated sanitizer injector validates all MCP Core inputs
- **CORS**: Explicit origin allowlist per environment
- **Secrets Management**: All credentials via environment variables; CI/CD uses GitHub Secrets; Cloud Run services use **GCP Secret Manager** (`--set-secrets`) — secrets never stored in env vars or images
- **Automated Scanning**: Weekly OWASP ZAP + dependency audits via GitHub Actions
- **Auto-Rollback**: Failed smoke tests trigger automatic rollback to previous Cloud Run revisions
- **Docker**: Non-root containers, multi-stage builds, minimal base images

---

## 📜 Standards Reference

- **EIT Standard 2001-56** — Thai Electrical Installation Standard
- **NEC 2023** — National Electrical Code (US)
- **TIS 648** — Thai Industrial Standard for Wiring
- **IEC 60364** — International Electrotechnical Commission

---

<p align="center">
  <sub>Built by <a href="https://github.com/Pruek-Sang">Pruek-Sang</a></sub>
</p>
