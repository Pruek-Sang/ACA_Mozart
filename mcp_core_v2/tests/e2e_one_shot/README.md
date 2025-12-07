# 🧪 One-Shot E2E Test Suite

Complete end-to-end testing framework for ACA Mozart RAG → MCP integration.

## 📋 Overview

This test suite validates the **complete flow** from user prompt to final design output:

```
User Prompt → RAG /mcp_spec → ProjectInputSpec → MCP Core → DesignResult
```

### Test Layers

1.  **Layer 0: Infrastructure** - Health checks and connectivity
2.  **Layer 1: RAG → Spec** - Spec generation and validation
3.  **Layer 2: Spec → MCP** - Electrical calculation accuracy

---

## 🚀 Quick Start

### 1. Generate Golden References (First Time Only)

```bash
cd /home/builder/Desktop/ACA_Mozart/mcp_core_v2/tests/e2e_one_shot

# Generate all golden specs and results
python golden_generator.py --mode all

# Or generate for specific test
python golden_generator.py --mode rag-only --test-id OS-1
```

**What this does:**
- Calls RAG `/mcp_spec` with each prompt
- Saves golden spec to `fixtures/golden_specs/`
- Runs MCP pipeline on each spec
- Saves golden result to `fixtures/golden_results/`

### 2. Run Tests

```bash
# Run all tests
python test_runner.py

# Run specific layer
python test_runner.py --layer 1

# Run specific test
python test_runner.py --test-id OS-1
```

### 3. View Results

```bash
# Check latest report
cat reports/run_YYYYMMDD_HHMMSS.json

# Or view summary (auto-printed at end)
```

---

## 📁 Structure

```
e2e_one_shot/
├── __init__.py
├── README.md                  # This file
├── config.yaml               # Test configuration
│
├── test_runner.py            # Main test orchestrator
├── golden_generator.py       # Generate golden references
│
├── layer0_infra.py           # Infrastructure tests
├── layer1_rag_spec.py        # RAG validation
├── layer2_mcp_calc.py        # MCP calculation validation
│
├── fixtures/
│   ├── prompts/              # User prompts (input)
│   │   ├── OS-1_simple_house.txt
│   │   ├── OS-2_heavy_kitchen.txt
│   │   └── ...
│   │
│   ├── golden_specs/         # Expected RAG output
│   │   ├── OS-1_spec.json
│   │   └── ...
│   │
│   └── golden_results/       # Expected MCP output
│       ├── OS-1_result.json
│       └── ...
│
└── reports/                  # Test run reports
    └── run_YYYYMMDD_HHMMSS.json
```

---

## 🧪 Test Cases

### OS-1: Simple House Sanity
**Purpose:** Baseline validation  
**Scenario:** 1-floor house, basic loads, short wire runs  
**Validates:** Basic RAG→MCP flow works correctly

### OS-2: Heavy Kitchen + VD Edge
**Purpose:** Stress test voltage drop calculation  
**Scenario:** 2-floor house, heavy kitchen loads, 25m wire run  
**Validates:** VD calculation, wire upsizing, derating factors

### OS-3: Borderline Loading
**Purpose:** Test utility limit handling  
**Scenario:** Small main breaker (50A), loads near capacity  
**Validates:** Demand factor, capacity warnings

### OS-4: Mix Load Types
**Purpose:** Multi-type load handling  
**Scenario:** Lighting + receptacles + HVAC + appliances  
**Validates:** Load type mapping, power factor handling

### OS-5: THW Standards
**Purpose:** Thai standard compliance  
**Scenario:** Uses THW wire, Thai ampacity tables  
**Validates:** Knowledge base integration, standard lookup

### OS-6: Invalid Spec Handling
**Purpose:** Error handling  
**Scenario:** Intentionally invalid voltage/breaker config  
**Validates:** Validation errors, graceful failure

---

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
# Endpoints
rag_endpoint: "http://localhost:8080/api/v1/mcp_spec"
mcp_endpoint: "http://localhost:8001/design"  # Or direct pipeline

# Timeouts
timeout: 30

# Tolerances
tolerance:
  current_percent: 5.0        # ±5% for current
  voltage_drop_percent: 0.5   # ±0.5% for VD
  wire_size_exact: true       # Wire must match exactly
  breaker_exact: true         # Breaker must match exactly
```

---

## 📊 Understanding Results

### Test Report Format

```json
{
  "timestamp": "20251202_235959",
  "summary": {
    "total": 18,
    "passed": 16,
    "failed": 2,
    "errors": 0,
    "pass_rate": "88.9%"
  },
  "results": [
    {
      "test_id": "L1-OS-1",
      "test_name": "OS-1: RAG spec generation",
      "layer": 1,
      "status": "PASS",
      "duration_s": 2.35,
      "message": "Spec generation passed"
    },
    ...
  ]
}
```

### Status Codes

- ✅ **PASS** - Test passed
- ❌ **FAIL** - Test failed (results differ from golden)
- 💥 **ERROR** - Exception occurred
- ⏭️ **SKIP** - Test skipped

---

## 🔧 Adding New Test Cases

### Step 1: Create Prompt

Create `fixtures/prompts/OS-X_description.txt`:

```
ออกแบบ...
[Detailed requirements in Thai]
```

### Step 2: Generate Golden

```bash
python golden_generator.py --mode all
```

This will:
1. Call RAG with your prompt
2. Save spec to `golden_specs/OS-X_spec.json`
3. Run MCP on spec
4. Save result to `golden_results/OS-X_result.json`

### Step 3: Run Test

```bash
python test_runner.py --test-id OS-X
```

---

## 🐛 Troubleshooting

### "RAG service unreachable"
- Check if RAG is running: `curl http://localhost:8080/health`
- Verify endpoint in `config.yaml`

### "Golden files not found"
- Run `golden_generator.py` first
- Check files exist in `fixtures/golden_*/`

### "MCP pipeline failed"
- Check MCP Core v2 tests pass: `pytest tests/test_pipeline.py`
- Verify dependencies installed

### "Results differ from golden"
- Check if this is expected (e.g., code changed)
- Regenerate golden if intentional: `python golden_generator.py --mode mcp-only`
- Check tolerance in `config.yaml`

---

## 📝 CI/CD Integration

### Example GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Start RAG service
        run: |
          cd Copilot-Mozart/ACA_Mozart-copilot[RAG]
          uvicorn app.routes:app --port 8080 &
          sleep 5
      
      - name: Run E2E tests
        run: |
          cd mcp_core_v2/tests/e2e_one_shot
          python test_runner.py
      
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: e2e-report
          path: mcp_core_v2/tests/e2e_one_shot/reports/
```

---

## 🎯 Success Criteria

A **complete successful run** should show:

```
============================================================
📊 TEST SUMMARY
============================================================
Total:  18
Passed: 18 ✅
Failed: 0 ❌
Errors: 0 💥
Pass Rate: 100.0%
============================================================
```

This means:
- ✅ RAG and MCP services are healthy
- ✅ All RAG specs match golden references
- ✅ All MCP calculations match golden results
- ✅ System ready for production use

---

**Maintained by:** Aura  
**Version:** 1.0.0  
**Last Updated:** 2025-12-03
