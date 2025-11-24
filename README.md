# ACA_Mozart - MCP Core v2

Master Control Program (MCP) for Electrical Design Automation.

## Overview

MCP Core v2 is a comprehensive electrical design system that transforms high-level room specifications into complete electrical designs including:

- Circuit sizing (wires, breakers, conduits)
- Power flow analysis using pandapower
- Code compliance validation
- AutoLISP script generation for CAD

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

### Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /mcp/v2/run` - Execute MCP pipeline
- `GET /mcp/v2/status` - Pipeline status

### Example Request

```bash
curl -X POST http://localhost:8000/mcp/v2/run \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-001",
    "project_name": "Test Project",
    "rooms": [
      {
        "name": "Bedroom",
        "room_type": "bedroom",
        "width_m": 4.0,
        "length_m": 3.0,
        "height_m": 2.8
      }
    ],
    "voltage": 220,
    "phases": 1
  }'
```

## Running Tests

```bash
pytest
```

## Project Structure

```
ACA_Mozart/
├── main.py                 # FastAPI application
├── pipeline.py             # Main orchestration pipeline
├── config.py               # Pydantic settings
├── requirements.txt        # Dependencies
├── models/                 # Data models
│   ├── contracts.py        # Input/Output contracts
│   ├── baseline.py         # Intermediate representations
│   └── catalog_models.py   # Catalog data models
├── dal/                    # Data Access Layer
│   ├── supabase_client.py  # Supabase connection
│   └── catalog_dal.py      # Catalog data access
├── core/                   # Core logic modules
│   ├── template_resolver.py
│   ├── load_calculator.py
│   ├── pandapower_adapter.py
│   ├── wire_sizer.py
│   ├── breaker_selector.py
│   ├── conduit_sizer.py
│   ├── compliance_checker.py
│   ├── autolisp_generator.py
│   └── result_builder.py
├── db/                     # Database schemas
│   └── design_session_schema.sql
└── tests/                  # Test suite
    └── test_pipeline.py
```

## Features

- **Single-phase equivalent modeling** for pandapower analysis
- **LangSmith tracing** integration for observability
- **Hardcoded demo data** for testing without database
- **Code compliance checking** against voltage drop limits
- **AutoLISP script generation** for AutoCAD integration

## License

Proprietary
