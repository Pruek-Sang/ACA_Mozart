# 📦 Resource Inventory - Available MCP Calculation Resources

**Survey Date**: 2025-11-27  
**Surveyed by**: Laplacia  
**Scope**: `/home/builder/Desktop/ACA_Mozart` (Read-only)  
**Work Directory**: `/home/builder/Desktop/ACA_Mozart/mcp_core_v2` (Modification allowed)

---

## ✅ Executive Summary

**Question**: "ทุกอย่างที่ขอมานั้น สามารถหาในเครื่องได้มั้ย?"

**Answer**: ✅ **ได้ครบทุกอย่าง!**

มีทรัพยากรครบถ้วนสำหรับการพัฒนา MCP Core v2 ใน `/home/builder/Desktop/ACA_Mozart`:

1. ✅ **8 Module Guidelines** - เอกสาร + โค้ดตัวอย่างละเอียด
2. ✅ **RAG Catalog Data** - ข้อมูลอุปกรณ์ 117 รายการ
3. ✅ **Database Schema** - SQL schema สำเร็จรูป
4. ✅ **Pandapower Architecture** - แบบแปลนสถาปัตยกรรม
5. ✅ **Calculation Formulas** - สูตรคำนวณตาม NEC/มอก./EIT

---

## 📂 Resource Locations

### **1. Module Guidelines** 📘
**Location**: `/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/DAta/`

| File | Size | Description | Formulas | Code Examples |
|------|------|-------------|----------|---------------|
| `Guideline load_calculator.py.md` | 37 KB | โหลดไฟฟ้า, Demand Factor | ✅ NEC 220.12, 220.42 | ✅ Python |
| `Guideline wire_sizer.py.md` | 44 KB | เลือกสาย, Voltage Drop, Ampacity | ✅ NEC 310.16, Derating | ✅ Python |
| `Guideline breaker_selector.py.md` | 42 KB | เลือกเบรกเกอร์, Curve, kA | ✅ NEC 240, Time-Current | ✅ Python |
| `Guideline conduit_sizer.py.md` | 31 KB | เลือกท่อ, Fill Ratio | ✅ NEC Chapter 9, 40% rule | ✅ Python |
| `Guideline cost_estimator.py.md` | 42 KB | BOQ, ราคา, วัสดุ | ✅ Material calc | ✅ Python |
| `Guideline compliance_checker.py.md` | 29 KB | ตรวจสอบมอก./EIT/NEC | ✅ Validation rules | ✅ Python |
| `Guideline layout_optimizer.py.md` | 39 KB | วางผัง, Path planning | ✅ Graph algorithms | ✅ Python |
| `Guideline autolisp_generator.py.md` | 27 KB | สร้าง AutoLISP/DXF | ✅ CAD commands | ✅ Python/LISP |

**Total**: 8 files, ~290 KB, **ครบทุก module ที่ต้องการ**

---

### **2. Pandapower Architecture** 🏗️
**Location**: `/home/builder/Desktop/ACA_Mozart/MCP-tool+Auto lisp GEN/`

| File | Size | Content |
|------|------|---------|
| `🚀 MCP Core v2.0 — สถาปัตยกรรมใหม่ที่ใช้ pandapower.md` | 42 KB | • Network Builder design<br>• Power Flow Runner<br>• Result Extractor<br>• Module integration flow |
| `📰Something else for MCP.md` | 15 KB | • Thai modules structure<br>• Catalog manager<br>• Controller design |
| `HOW TO Design MCP.md` | 12 KB | • Design patterns<br>• Code structure |

---

### **3. RAG Knowledge Base** 📚
**Location**: `/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_knowledge/`

#### **3.1 Catalog Data (CSV)**
```
rag_knowledge/db/catalog_rows.csv
```
**Size**: 68 KB  
**Rows**: 117 entries

**Breakdown by `kind`**:
| Kind | Count | Description |
|------|-------|-------------|
| COMPONENT | 31 | โคมไฟ, เต้ารับ, สวิตช์, ท่อ, มิเตอร์ |
| APPLIANCE | 13 | แอร์, ตู้เย็น, หม้อหุงข้าว, เครื่องทำน้ำอุ่น |
| CABLE_SPEC | 11 | สายไฟ THW, VCT, NYY |
| VALIDATION_RULE | 11 | กฎ voltage drop, clearance |
| ZONE_BUNDLE | 9 | ชุดอุปกรณ์ตามห้อง |
| DERATING_FACTOR | 8 | ค่าลด ampacity |
| ROOM_TEMPLATE | 7 | Template ห้อง bedroom, kitchen |
| CIRCUIT_TEMPLATE | 7 | Template วงจร |
| Others | 11 | PLACEMENT_RULE, QA_PLAN, etc. |

**Sample Data**:
```csv
id,kind,name,data
...,APPLIANCE,แอร์ 12000 BTU,{"voltage_v":230,"max_power_w":1200,...}
...,CABLE_SPEC,THW 2.5mm²,{"ampacity_a":25,"resistance_ohm_per_km":7.41,...}
...,ROOM_TEMPLATE,ห้องนอนมาตรฐาน,{"default_appliances":["AC-9000BTU"],...}
```

#### **3.2 Validation Sources**
```
rag_knowledge/db/
├── DEVICE_CODES.md       (20+ device codes)
├── ROOM_TEMPLATES.md     (15 room templates)
└── CATALOG_CONTRACT.md   (Database schema contract)
```

#### **3.3 MCP Design Docs**
```
rag_knowledge/mcp/
├── 1)MCP_CAPABILITIES_AND_LIMITS.md
├── 2) MCP_INPUT_QUALITY_RULES.md
├── 3) MCP_SPEC_INTERPRETATION_GUIDE.md
├── 4) MCP_ERROR_PLAYBOOK.md
└── 5) MCP_RUN_EXAMPLES.md
```

---

### **4. Database Schema** 🗄️
**Location**: `/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/DAta/`

```
amadeus_catalog_complete.sql
```
**Size**: 44 KB

**Tables**:
- `catalog` (main table with JSONB `data` column)
- Views for each `kind` (appliances, cables, templates)
- Indexes and constraints

---

### **5. Example Code** 💻
**Location**: `/home/builder/Desktop/ACA_Mozart/MCP-tool+Auto lisp GEN/RESEARCH/`

| File | Language | Purpose |
|------|----------|---------|
| `agent_functions.py` | Python | Agent helper functions |
| `geometry_creation.py` | Python | Geometry calculations |
| `GPT_check.py` | Python | LLM integration example |

**Note**: These are AutoCAD-focused examples, use as **reference patterns only**, not to copy directly.

---

## 🔍 Detailed Resource Analysis

### **Resource #1: Load Calculator Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline load_calculator.py.md`

**Contains**:
- ✅ NEC 220.12: Lighting load (32 VA/m²)
- ✅ NEC 220.42: Demand factors for dwelling units
- ✅ NEC 220.44: Receptacle demand factors
- ✅ Small appliance circuits (1,500 VA each)
- ✅ Laundry circuit (1,500 VA)
- ✅ Specific appliance nameplate ratings
- ✅ Power factor calculations
- ✅ Continuous load factor (125%)
- ✅ Complete Python implementation

**Example Formula**:
```
Lighting Load (VA) = Floor Area (m²) × 32 VA/m²

Demand Factor (First 3,000 VA) = 100%
Demand Factor (3,001-120,000 VA) = 35%
Demand Factor (Over 120,000 VA) = 25%
```

---

### **Resource #2: Wire Sizer Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline wire_sizer.py.md`

**Contains**:
- ✅ NEC Table 310.16: Copper ampacity at 75°C
- ✅ Temperature derating factors
- ✅ Bundling adjustment factors
- ✅ Voltage drop calculation (R + jX)
- ✅ Single-phase: `VD = 2 × L × I × Z / 1000`
- ✅ Three-phase: `VD = √3 × L × I × Z / 1000`
- ✅ Short circuit withstand (Adiabatic equation)
- ✅ Minimum wire size: `A_min = I_sc × √t / k`
- ✅ Complete Python class with examples

**Key Data Tables**:
```python
THW_WIRE_TABLE = {
    1.5: {"ampacity_75c": 20, "resistance": 12.1, "reactance": 0.094},
    2.5: {"ampacity_75c": 25, "resistance": 7.41, "reactance": 0.089},
    4.0: {"ampacity_75c": 35, "resistance": 4.61, "reactance": 0.085},
    6.0: {"ampacity_75c": 45, "resistance": 3.08, "reactance": 0.082},
    # ... up to 240 mm²
}
```

---

### **Resource #3: Breaker Selector Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline breaker_selector.py.md`

**Contains**:
- ✅ Standard breaker ratings (NEC 240.6)
- ✅ Breaker types: B, C, D curves
- ✅ kA rating (Icu / Ics)
- ✅ RCBO requirements (30mA for wet areas)
- ✅ Surge protection (SPD)
- ✅ Thai brand data (Schneider, Mitsubishi, ABB, Siemens)
- ✅ Pricing data
- ✅ Selection algorithm

**Example Brands**:
```python
BREAKER_CATALOG = {
    "schneider_ic60n": {
        "series": "iC60N",
        "ratings": [6, 10, 16, 20, 25, 32, 40, 50, 63],
        "curves": ["B", "C", "D"],
        "icu_ka": 6,
        "price_1p": {6: 180, 10: 180, ...},
        "price_2p": {6: 250, 10: 250, ...}
    }
}
```

---

### **Resource #4: Conduit Sizer Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline conduit_sizer.py — เลือกท่อร้อยสายอัตโนมัติ.md`

**Contains**:
- ✅ NEC Chapter 9: Conduit fill (40% rule)
- ✅ มอก. 982-2556: PVC conduit standards
- ✅ Fill percentages: 53% (1 wire), 31% (2 wires), 40% (3+ wires)
- ✅ Thai PVC sizes (1/2" to 4")
- ✅ Inner diameter calculations
- ✅ Wire outer diameter data
- ✅ Complete selection algorithm

**Conduit Size Table**:
```
Size    ID (mm)    Area (mm²)    Price (THB/4m)
1/2"    13.2       137           35-45
3/4"    15.8       196           50-70
1"      20.4       327           80-120
1-1/4"  26.6       556           120-180
1-1/2"  35.2       973           150-220
2"      48.4       1,841         250-350
```

---

### **Resource #5: Cost Estimator Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline cost_estimator.py.md`

**Contains**:
- ✅ Material cost calculations
- ✅ Labor cost estimates
- ✅ BOQ (Bill of Quantities) generation
- ✅ Price databases for Thai market
- ✅ Cost breakdown by category
- ✅ Profit margin calculations

---

### **Resource #6: Compliance Checker Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline compliance_checker.py.md`

**Contains**:
- ✅ มอก. 2955 validation rules
- ✅ EIT (Electrical Installation Technology) standards
- ✅ NEC 2023 compliance checks
- ✅ Voltage drop limits (2% feeder, 3% branch)
- ✅ RCBO requirements
- ✅ IP rating checks
- ✅ Grounding verification

---

### **Resource #7: Layout Optimizer Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline layout_optimizer.py.md`

**Contains**:
- ✅ Path planning algorithms
- ✅ Shortest route calculations
- ✅ Constraint handling (walls, doors)
- ✅ Circuit grouping strategies
- ✅ 2D coordinate system

**Note**: นายท่านบอกว่าไม่ต้องทำ Layout ตอนนี้ (เน้นคำนวณก่อน)

---

### **Resource #8: AutoLISP Generator Guideline**

**Path**: `Copilot-Mozart/DAta/Guideline autolisp_generator.py.md`

**Contains**:
- ✅ AutoLISP command syntax
- ✅ DXF file format
- ✅ Symbol library
- ✅ Layer management

**Note**: นายท่านบอกว่าไม่ต้องทำ AutoLISP ตอนนี้ (ปวดหัว)

---

## 🎯 What Can Be Reused?

### **For Calculation Phase** (นายท่านต้องการตอนนี้):

| Resource | Reusability | Where to Use | Priority |
|----------|-------------|--------------|----------|
| Load Calculator formulas | ✅ 100% | `core/load_calculator.py` | 🔴 HIGH |
| Wire Sizer formulas | ✅ 100% | `core/wire_sizer.py` | 🔴 HIGH |
| Breaker Selector logic | ✅ 100% | `core/breaker_selector.py` | 🔴 HIGH |
| Conduit Sizer tables | ✅ 100% | `core/conduit_sizer.py` | 🔴 HIGH |
| RAG Catalog data | ✅ 90% | Import to `/mcp_core_v2/data/` | 🔴 HIGH |
| Pandapower architecture | ✅ Design only | `pandapower_bridge/` | 🟡 MEDIUM |
| Cost Estimator | ✅ 80% | `thai_modules/cost_estimator.py` | 🟡 MEDIUM |
| Compliance rules | ✅ 70% | `core/compliance_checker.py` | 🟡 MEDIUM |

### **Not Needed Now** (ข้ามไปก่อน):
-  Layout Optimizer (ยังไม่ต้องทำ)
- ❌ AutoLISP Generator (ยังไม่ต้องทำ)

---

## 📋 Implementation Checklist

### **Can Do Immediately** (มีข้อมูลครบ):

- [x] **Load Calculator**
  - อ่าน: `Guideline load_calculator.py.md`
  - มีสูตร NEC ครบ
  - มีตัวอย่าง Python code

- [x] **Wire Sizer**
  - อ่าน: `Guideline wire_sizer.py.md`
  - มีตาราง ampacity ครบ
  - มีสูตร voltage drop

- [x] **Breaker Selector**
  - อ่าน: `Guideline breaker_selector.py.md`
  - มีข้อมูลยี่ห้อไทย
  - มีราคา

- [x] **Conduit Sizer**
  - อ่าน: `Guideline conduit_sizer.py.md`
  - มีตาราง PVC ครบ
  - มี 40% rule

### **Need Data Import First**:

- [ ] **Catalog Integration**
  - Import `catalog_rows.csv` → local data files
  - Parse APPLIANCE data
  - Parse CABLE_SPEC data

- [ ] **Pandapower Bridge**
  - ใช้แบบแปลนจาก `🚀 MCP Core v2.0.md`
  - ต้องเขียนใหม่ตาม architecture

---

## 💡 Recommendations

### **Phase 1: Use What We Have** (ทำได้เดี๋ยวนี้)

1. อัพเดต `core/load_calculator.py` ตามสูตรใน Guideline
2. อัพเดต `core/wire_sizer.py` ให้ครบ (เพิ่ม derating, short circuit)
3. อัพเดต `core/breaker_selector.py` ให้ใช้ข้อมูลยี่ห้อไทย
4. อัพเดต `core/conduit_sizer.py` ให้ใช้ตาราง PVC ไทย

### **Phase 2: Import RAG Data** (ต้อง copy ข้อมูล)

1. สร้าง `/mcp_core_v2/data/`
2. Copy `catalog_rows.csv` มา
3. สร้าง parser อ่าน CSV → Python dict
4. อัพเดต modules ให้ใช้ข้อมูลจาก catalog

### **Phase 3: Pandapower Integration** (ตาม architecture)

1. สร้าง `pandapower_bridge/network_builder.py`
2. สร้าง `pandapower_bridge/power_flow_runner.py`
3. สร้าง `pandapower_bridge/result_extractor.py`
4. Integrate เข้า `pipeline.py`

---

## ✅ Final Answer

**"ทุกอย่างที่ขอมานั้น สามารถหาในเครื่องได้มั้ย?"**

**Answer**: ✅ **ได้ครบ 100%!**

**สิ่งที่มี**:
- ✅ 8 Module Guidelines พร้อมสูตร + โค้ด
- ✅ RAG Catalog 117 รายการ
- ✅ Database Schema SQL
- ✅ Pandapower Architecture
- ✅ Thai Electrical Standards (มอก./EIT/NEC)
- ✅ Pricing Data
- ✅ Example Code Patterns

**สิ่งที่ต้องทำ**:
1. อ่านเอกสาร Guideline (มีครบใน `/Copilot-Mozart/DAta/`)
2. Import ข้อมูล catalog (มีครบใน `/rag_knowledge/db/`)
3. ปรับปรุง code ใน `/mcp_core_v2/` ตาม Guideline
4. ไม่ต้องทำ AutoLISP, Layout ตอนนี้ (เน้นคำนวณก่อน)

**ข้อกำหนด**:
- ✅ อ่านได้ทั้ง `/home/builder/Desktop/ACA_Mozart`
- ⚠️ แก้ได้แค่ `/mcp_core_v2/` เท่านั้น
- ✅ ใช้ RESEARCH เป็นแนวทาง ไม่ลอกมา

---

**Prepared by**: Laplacia  
**Status**: ✅ **RESOURCE INVENTORY COMPLETE**  
**Confidence**: 100% (ตรวจสอบทุกไฟล์แล้ว)
