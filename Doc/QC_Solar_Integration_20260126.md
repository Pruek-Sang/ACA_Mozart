# 🌞 QC Summary: Solar PV On-Grid Integration

**Date**: 2026-01-26  
**Author**: Civilia (Construction & M&E Engineer Maid)  
**Branch**: Production-3Phase  
**Status**: ✅ COMPLETE

---

## 📋 Implementation Summary

### Objective
Integrate On-Grid Solar PV support (Net Metering) into ACA_Mozart electrical design system with:
- 1-Phase support: ≤5kW (MEA residential)
- 3-Phase support: >5kW up to 30kW
- CT Meter requirement for >10kW
- Real calculations (no mocking)
- 90%+ accuracy target

---

## ✅ Files Modified (13 Files)

### Phase 1: Core Data Models

| File | Change | Status |
|------|--------|--------|
| `mcp_core_v2/models/contracts.py` | Added `SOLAR = "solar"` to LoadType enum | ✅ |
| `mcp_core_v2/core/circuit_grouper.py` | Added `SOLAR = "solar"` to CircuitType enum | ✅ |
| `mcp_core_v2/core/circuit_grouper.py` | Added 'SOLAR', 'โซลาร์', 'PV', 'INVERTER' to DEDICATED_LOAD_TYPES | ✅ |
| `app/mcp_adapter.py` (RAG) | Added `SOLAR = "solar"` to LoadType enum | ✅ |
| `app/mcp_adapter.py` (RAG) | Added DEVICE_MAPPING entries: SOLAR-ONGRID-3KW through 30KW | ✅ |
| `rag_knowledge/db/DEVICE_CODES.md` | Added Solar PV Systems section with 8 device codes | ✅ |

### Phase 2: Injector & Pipeline

| File | Change | Status |
|------|--------|--------|
| `mcp_core_v2/context/__init__.py` | Export SolarCellInjector | ✅ |
| `mcp_core_v2/pipeline.py` | Import SolarCellInjector + hook at Step 7.5 | ✅ |
| `mcp_core_v2/context/solar_cell_injector.py` | Complete implementation (~380 lines) | ✅ |

### Phase 3: Display Layer

| File | Change | Status |
|------|--------|--------|
| `app/display/compute.py` | Added Solar fields to DisplayData TypedDict | ✅ |
| `app/display/compute.py` | Added `_extract_solar_fields()` function | ✅ |
| `app/display/compute.py` | Added solar fields to `_empty_display_data()` | ✅ |
| `app/display/sld_renderer.py` | Added Solar node with `_create_solar_node()` | ✅ |
| `app/display/boq_renderer.py` | Added Section E.4 for Solar equipment pricing | ✅ |
| `app/display/audit_document.py` | Added `_render_solar_section()` for audit | ✅ |

### Phase 4: Frontend Types

| File | Change | Status |
|------|--------|--------|
| `frontend/src/types/index.ts` | Added 3-phase fields to DisplayData | ✅ |
| `frontend/src/types/index.ts` | Added Solar interfaces (7 new types) | ✅ |

---

## 🔌 Connection Points Verified

### 1. Device Code Flow
```
DEVICE_CODES.md → DEVICE_MAPPING (mcp_adapter.py)
  ↓
LoadType.SOLAR → pipeline.py → SolarCellInjector
```
✅ All SOLAR-ONGRID-* codes in both files

### 2. Pipeline Hook
```
pipeline.py:__init__()
  → self.solar_cell_injector = get_solar_cell_injector()

pipeline.py:execute() Step 7.5
  → if self.solar_cell_injector.should_inject(request):
  →   solar_data = self.solar_cell_injector.inject(...)
  →   calculations['solar'] = solar_data
```
✅ Injector initialized and called at correct step

### 3. Display Layer Flow
```
calculations['solar'] → compute.py:_extract_solar_fields()
  ↓
DisplayData.has_solar, solar_* fields
  ↓
sld_renderer.py → Solar node in SLD
boq_renderer.py → Section E.4 with pricing
audit_document.py → Solar section in audit
```
✅ All renderers read from compute.py

### 4. Frontend Types
```
DisplayData (compute.py) → DisplayData (index.ts)
  ↓
has_solar, solar_inverter, solar_dc_circuit, etc.
```
✅ All solar fields defined in TypeScript

---

## 📊 Solar Calculation Details

### Inverter Sizing (solar_cell_injector.py)
- Ratio: 0.90 (inverter slightly smaller than panel DC capacity)
- Common sizes: 1.5, 2.0, 3.0, 3.6, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0 kW

### DC Circuit (NEC 690.8)
- Voc safety factor: 1.25
- Isc safety factor: 1.25
- Wire sizing table by current range
- DC breaker sizing to next standard size

### AC Circuit
- Design current: AC current × 1.25
- Wire sizing table by current range
- Breaker type: RCBO 30mA for ≤10kW, MCCB for >10kW

### Net Metering (MEA/PEA)
- Residential limit: ≤10kW
- CT meter required: >10kW
- Programs: residential, residential_ct, commercial

### Energy Estimate
- Peak sun hours: 4.5 hr/day (Thailand average)
- System efficiency: 80%
- Daily kWh = capacity × 4.5 × 0.80

---

## 💰 BOQ Pricing (Section E.4)

| Item | Unit Price | Notes |
|------|------------|-------|
| Solar Panel 450W | 3,500 THB/panel | Longi, JA, Trina |
| Grid-Tie Inverter | 3,500 THB/kW | Huawei, SMA, GoodWe |
| DC Cable PV1-F | 25-35 THB/m | TUV certified |
| DC Disconnect | 1,500 THB | NEC 690.15 |
| AC Breaker RCBO | 1,200 THB | Schneider/ABB |
| DC SPD Type 2 | 2,500 THB | Lightning protection |
| Mounting Structure | 800 THB/panel | Aluminum |
| Installation | 1,500 THB/kW | Labor |

---

## 📋 Cloud Logging Checkpoints

| Checkpoint | Location | Purpose |
|------------|----------|---------|
| `[CP-SOLAR-INIT]` | solar_cell_injector.py | Singleton creation |
| `[CP-SOLAR-START]` | pipeline.py | Entry to Step 7.5 |
| `[CP-SOLAR-DETECT]` | pipeline.py | Solar loads found |
| `[CP-SOLAR-CALC]` | solar_cell_injector.py | Calculation in progress |
| `[CP-SOLAR-DONE]` | pipeline.py | Complete with summary |
| `[CP-SOLAR-SKIP]` | pipeline.py | No solar found |
| `[CP-SOLAR-DISPLAY]` | compute.py | Extracting for display |
| `[CP-SOLAR-SLD]` | sld_renderer.py | Adding to SLD |
| `[CP-SOLAR-BOQ]` | boq_renderer.py | Generating BOQ section |
| `[CP-SOLAR-AUDIT]` | audit_document.py | Adding audit section |

---

## 🧪 Test Scenarios

### Basic Test (Manual)
```
Input:
  - บ้าน 2 ชั้น 3-phase
  - โหลด: AC 24000BTU × 3, เครื่องทำน้ำอุ่น 4500W × 2
  - Solar: SOLAR-ONGRID-10KW

Expected:
  - has_solar: true
  - solar_capacity_kw: 10.0
  - inverter: 10kW (3-Phase)
  - net_metering: eligible_residential = true, requires_ct = false
  - BOQ Section E.4 total: ~200,000 THB
```

### Edge Cases
1. **1-Phase + 5kW Solar** → Should work, no 3-phase warning
2. **1-Phase + 7kW Solar** → Should warn about 3-phase requirement
3. **3-Phase + 15kW Solar** → Should show CT meter requirement
4. **No Solar** → has_solar: false, no solar sections in output

---

## ⚠️ Known Limitations

1. **Off-Grid/Hybrid**: Not implemented (Tech Debt B/C)
2. **Micro-inverters**: Not supported (string inverters only)
3. **Battery storage**: Not calculated
4. **Shading analysis**: Not performed
5. **Panel degradation**: Not factored into energy estimate

---

## 🔄 Future Enhancements (Tech Debt)

- [ ] Off-Grid system support (Type B)
- [ ] Hybrid system support (Type C)
- [ ] Battery storage calculations
- [ ] Multiple string configurations
- [ ] Shading loss estimation
- [ ] Roof orientation optimization
- [ ] Time-of-use tariff calculation

---

## ✅ Verification Checklist

- [x] LoadType.SOLAR exists in MCP Core contracts
- [x] LoadType.SOLAR exists in RAG mcp_adapter
- [x] CircuitType.SOLAR exists in circuit_grouper
- [x] SOLAR in DEDICATED_LOAD_TYPES
- [x] SolarCellInjector exported from context
- [x] Pipeline imports and hooks injector
- [x] solar_cell_injector.py has inject() method
- [x] inject() returns Dict (not None when solar present)
- [x] compute.py extracts solar_data
- [x] DisplayData has all solar fields
- [x] SLD renders solar node
- [x] BOQ has Section E.4
- [x] Audit document has solar section
- [x] Frontend types match backend

---

**Signed**: Civilia 🏗️  
**Date**: 2026-01-26  
**Branch**: Production-3Phase

---

*"Solar power ทำให้บ้านพึ่งพาตัวเองได้ และลด Carbon Footprint อย่างมาก นะคะนายท่าน~" ☀️*
