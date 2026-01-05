# 🔍 VD Pipeline Debug Summary

**Date:** 2026-01-05  
**Issue:** VD% = 2.0 ทุกวงจร + "36 วงจร ใช้ระยะ Default" แม้ผู้ใช้ระบุ 15m/25m

---

## 📋 Tests Performed

| Test | File | What It Tests | Result |
|------|------|---------------|:------:|
| **Regex Extraction** | `test_vd_definitive.py` | Pattern matching "ชั้น 1 = 15 เมตร" | ✅ `{1: 15.0, 2: 25.0}` |
| **LoadInput Model** | `test_vd_pipeline_e2e.py` | `branch_distance_m` field exists | ✅ Stores 15.0 |
| **LoadSpec Model** | `test_vd_pipeline_e2e.py` | `branch_distance_m` passed through | ✅ Stores 15.0 |
| **McpAdapter** | `test_vd_pipeline_e2e.py` | JSON output has distance | ✅ 15.0/25.0 in JSON |
| **MCP Core Model** | Code inspection | `ElectricalLoad.branch_distance_m` | ✅ Field exists (Line 64) |
| **MCP Pipeline** | Code inspection | Reads `load.branch_distance_m` | ✅ Line 25 checks it |
| **Key Conversion** | Code inspection | String→Int key conversion | ✅ Line 925 handles it |

---

## 🔬 Code Path Verification

### `service.py` - LLM Extraction (Line 920-958)
```
✅ llm_floor_distances extracted from LLM
✅ String keys converted to int
✅ Applied to each load via room_floor lookup
✅ Stored in extracted["floor_distances"]
```

### `service.py` - Convert to ProjectRequirements (Line 1800-1814)
```
✅ Reads l.get("branch_distance_m") from extracted loads
✅ Falls back to floor-based default if None
✅ Passes branch_distance_m to LoadInput
```

### `mcp_adapter.py` - Convert to MCP (Line 372)
```
✅ getattr(load, 'branch_distance_m', None)
✅ Includes in McpElectricalLoad
✅ Serializes to JSON for HTTP request
```

### `mcp_core_v2/pipeline.py` - VD Calculation (Line 283-293)
```
✅ Checks hasattr(load, 'branch_distance_m')
✅ Uses user value if present
✅ Falls back to default if None
```

---

## ❌ Problem Still Observed in Production

**User Input:**
```
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 1 = 15 เมตร/วงจร
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 2 = 25 เมตร/วงจร
```

**Expected Output:**
- Floor 1 circuits: VD% ≈ 1.0-1.5%
- Floor 2 circuits: VD% ≈ 2.0-2.5%

**Actual Output:**
- ALL circuits: VD% = 2.0 (identical)
- Warning: "36 วงจร ใช้ระยะ Default"

---

## 🔴 The Paradox

| Environment | Test Result |
|-------------|-------------|
| **Local (Code Inspection)** | ✅ All paths correct |
| **Local (E2E Test)** | ✅ Pipeline works |
| **Production (Manual)** | ❌ Still uses defaults |

---

## 🤔 Possible Explanations (Unverified)

1. **LLM Output Variance** - Production LLM may return different format than expected
2. **Untested Code Path** - Some path in production flow not covered by local tests
3. **Environment Difference** - Something different between local and Cloud Run
4. **Caching** - Old behavior cached somewhere
5. **Different Entry Point** - `/api/v1/ask` vs `/api/v1/design` have different flows

---

## 🎯 Next Steps

1. **Check GCP Logs** after commit `cf53712` deploys
   - Look for: `[LLM] floor_distances from LLM:`
   - Look for: `Applied X.Xm to DEVICE in ROOM`

2. **Add Explicit Logging** at each pipeline stage

3. **Create Integration Test** that calls actual `/api/v1/ask` endpoint

---

## 📁 Test Files Created

- `tests/test_vd_pipeline_e2e.py` - Component-level pipeline test
- `tests/test_vd_definitive.py` - Full simulation test

---

## 💡 Key Question

> **ถ้า Local Test ผ่านหมด ทำไม Production ถึงไม่ทำงาน?**

**Hypothesis:** Local tests simulate ideal LLM output. Production LLM may:
- Not return `floor_distances` at all
- Return different room names causing mismatch
- Return different data structure

**To Verify:** Need GCP logs or actual LLM response capture in production.
