# MCP Core v2 - Electrical Design System

A comprehensive electrical design calculation system that automates NEC-compliant electrical design for commercial and residential projects.

## Overview

MCP Core v2 is a Python-based electrical design automation system that:
- Calculates electrical loads according to NEC standards
- Sizes conductors and circuit breakers
- Determines conduit requirements
- Checks design compliance with NEC codes
- Generates AutoLISP code for AutoCAD integration

## Structure

```
mcp_core_v2/
├── config.py                   # Application configuration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── main.py                    # Main entry point
├── pipeline.py                # Design pipeline orchestrator
│
├── models/                    # Data models
│   ├── contracts.py          # Request/response contracts
│   ├── baseline.py           # NEC baseline data
│   └── catalog_models.py     # Product catalog models
│
├── dal/                       # Data Access Layer
│   ├── supabase_client.py    # Database client
│   └── catalog_dal.py        # Catalog operations
│
├── core/                      # Core calculation modules
│   ├── template_resolver.py  # Design template resolution
│   ├── load_calculator.py    # Load calculations
│   ├── wire_sizer.py         # Wire sizing
│   ├── breaker_selector.py   # Breaker selection
│   ├── conduit_sizer.py      # Conduit sizing
│   ├── compliance_checker.py # NEC compliance
│   ├── pandapower_adapter.py # Power flow analysis
│   ├── autolisp_generator.py # AutoCAD integration
│   └── result_builder.py     # Result aggregation
│
├── db/                        # Database
│   └── design_session_schema.sql  # PostgreSQL schema
│
└── tests/                     # Tests
    └── test_pipeline.py      # Pipeline tests
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Set up database:
```bash
# Execute the schema in your PostgreSQL/Supabase instance
psql -f db/design_session_schema.sql
```

## Usage

### Basic Example

```python
from models.contracts import DesignRequest, ElectricalLoad, PanelSpecification
from models.contracts import Location, VoltageType, LoadType
from pipeline import get_design_pipeline

# Create loads
loads = [
    ElectricalLoad(
        id="load_001",
        name="Office Lighting",
        load_type=LoadType.LIGHTING,
        voltage=VoltageType.SINGLE_PHASE_120V,
        power_watts=1200,
        quantity=8,
        location=Location(room="Office", floor="1"),
        is_continuous=True
    )
]

# Create panel
panels = [
    PanelSpecification(
        id="panel_001",
        name="LP-1",
        voltage=VoltageType.SINGLE_PHASE_120V,
        main_breaker_rating=200,
        number_of_circuits=42,
        location=Location(room="Electrical Room", floor="1"),
        feeds=["load_001"]
    )
]

# Create design request
request = DesignRequest(
    session_id="session_001",
    project_name="Office Building",
    loads=loads,
    panels=panels,
    service_voltage=VoltageType.SINGLE_PHASE_240V,
    utility_service_size=200
)

# Execute design
pipeline = get_design_pipeline()
result = pipeline.execute(request)

# Access results
print(f"Total Load: {result.calculations['panel_001']['total_va']} VA")
print(f"Compliant: {result.compliance_report['compliant']}")
```

### Running the Sample

```bash
python main.py
```

## Features

### Load Calculations
- Single and three-phase calculations
- Demand factor application per NEC
- Continuous load handling
- Motor load calculations

### Wire Sizing
- Ampacity-based sizing
- Voltage drop calculations
- NEC Table 310.16 compliance
- Copper and aluminum conductors
- Ground wire sizing per NEC 250.122

### Breaker Selection
- Standard breaker ratings
- AFCI/GFCI requirements
- Motor protection
- Coordination verification

### Conduit Sizing
- NEC Chapter 9 fill calculations
- Multiple conductor support
- EMT, IMC, RMC, PVC support

### Compliance Checking
- NEC 2023 standards
- Voltage drop verification
- AFCI/GFCI requirements
- Special location requirements

### AutoLISP Generation
- Panel layouts
- Device placement
- Wire runs
- Panel schedules
- AutoCAD-ready code

## Testing

Run tests:
```bash
pytest tests/test_pipeline.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

## Database Schema

The system uses PostgreSQL/Supabase with the following main tables:
- `design_sessions` - Design session tracking
- `electrical_loads` - Load specifications
- `panel_specifications` - Panel configurations
- `design_results` - Calculation results
- `catalog_*` - Product catalogs (breakers, wires, conduits, panels)

## Configuration

Key configuration options in `.env`:

```env
# Supabase
SUPABASE_URL=your_url
SUPABASE_KEY=your_key

# NEC Standards
NEC_VERSION=2023
VOLTAGE_DROP_LIMIT=0.03
TEMPERATURE_RATING=75

# Calculation Settings
SAFETY_FACTOR=1.25
DEFAULT_POWER_FACTOR=0.85
```

## Dependencies

Core dependencies:
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment management
- `supabase>=2.0.0` - Database client
- `pandapower>=2.13.0` - Power flow analysis
- `numpy>=1.24.0` - Numerical computations
- `pandas>=2.0.0` - Data processing
- `pytest>=7.4.0` - Testing

## NEC Compliance

The system implements:
- NEC 2023 calculations
- Article 220 - Load calculations
- Article 210 - Branch circuits
- Article 215 - Feeders
- Article 240 - Overcurrent protection
- Article 250 - Grounding
- Article 310 - Conductors
- Article 430 - Motors
- Chapter 9 - Tables

## License

Copyright (c) 2024

## Support

For issues and questions, please open an issue on GitHub.
