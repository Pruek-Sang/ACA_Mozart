# 🎯 MCP Architecture - Complete Understanding

**Analyst**: Laplacia, The Demon of Calculation Maid  
**Date**: 2025-11-27  
**Sources**: How to Design ACA, plan.md, Walkthrough_ACA.md, Something else for MCP.md

---

## 📋 Executive Summary

### **MCP Core v2 ควรทำอะไร?**

**คำตอบ**: MCP Core v2 คือ **"เครื่องคำนวณไฟฟ้าแบบสมบูรณ์"** ที่รับ **ProjectInputSpec จาก RAG** แล้วคืน **ผลลัพธ์การคำนวณครบวงจร**

---

## 🏗️ สถาปัตยกรรมระบบ ACA_Mozart (ภาพรวม)

```
┌─────────────────┐
│    FRONTEND     │ ← User พิมพ์: "ออกแบบบ้าน 2 ห้องนอน มีครัวหนัก"
│   (Chatbot)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    GATEWAY / AGI                        │
│  - รับ user prompt                                       │
│  - ทำความเข้าใจความต้องการ (conversation flow)           │
└────────┬───────────────────────────────┬────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│   RAG SERVICE   │            │ MCP CORE V2     │
│                 │            │                 │
│ Input:          │            │ Input:          │
│  - User prompt  │            │  - JSON spec    │
│  - Conversation │            │                 │
│                 │            │ Process:        │
│ Process:        │            │  - Pandapower   │
│  - LLM parsing  │            │  - NEC calc     │
│  - Knowledge    │            │  - Wire/Breaker │
│    retrieval    │            │  - AutoLISP     │
│  - Validation   │            │                 │
│                 │──JSON──────▶│ Output:         │
│ Output:         │  spec      │  - Results JSON │
│  - Project      │            │  - BOQ          │
│    InputSpec    │            │  - AutoLISP     │
│  - McpSpec      │            │  - Compliance   │
│    Response     │            │                 │
└─────────────────┘            └─────────────────┘
         │                               │
         └───────────────┬───────────────┘
                        │
                        ▼
                ┌───────────────┐
                │   DATABASE    │
                │ amadeus.catalog│
                │  (Supabase)   │
                └───────────────┘
```

---

## 🎯 MCP Core v2 - หน้าที่ที่แท้จริง

### **Input (รับจาก RAG)**:
```json
{
  "project_input": {
    "rooms": [
      {
        "room_id": "R001",
        "room_type": "BEDROOM",
        "room_name": "ห้องนอน 1",
        "area_m2": 12.0,
        "template_code": "ROOMT-BEDROOM-STD"
      }
    ],
    "loads": [
      {
        "load_id": "L001",
        "room_id": "R001",
        "device_code": "AC-12000BTU",
        "device_name": "แอร์ 12000 BTU",
        "quantity": 1,
        "power_w": 1200,
        "voltage_v": 230,
        "phase": "single"
      }
    ],
    "constraints": {
      "rule_profile_id": "PROFILE-RESIDENTIAL-TH",
      "max_voltage_drop_pct": 3.0,
      "preferred_wire_material": "copper"
    }
  }
}
```

### **Process (ทำอะไร)**:

#### **Phase 1: Network Building** (pandapower)
```python
# pandapower_bridge/network_builder.py
network = NetworkBuilder.build_network(project_input)
# สร้าง bus, load, line ใน pandapower network
```

#### **Phase 2: Power Flow Analysis**
```python
# pandapower_bridge/power_flow_runner.py
results = PowerFlowRunner.run_power_flow(network)
# คำนวณ voltage drop, current flow จริง
```

#### **Phase 3: Result Extraction**
```python
# pandapower_bridge/result_extractor.py
extracted = ResultExtractor.extract_results(network, results)
# ดึง voltage_pu, loading_percent ออกมา
```

#### **Phase 4: Thai Modules**
```python
# thai_modules/wire_sizer_v2.py
wires = WireSizerV2.select_wires(extracted, catalog)
# เลือกสายตาม NEC + มอก. + Voltage Drop

# thai_modules/breaker_selector_v2.py
breakers = BreakerSelectorV2.select_breakers(wires, catalog)
# เลือกเบรกเกอร์ตาม curve, kA rating

# thai_modules/conduit_sizer.py
conduits = ConduitSizer.size_conduits(wires)
# คำนวณท่อตาม fill ratio

# thai_modules/cost_estimator.py
cost = CostEstimator.calculate_cost(wires, breakers, conduits, catalog)
# สร้าง BOQ + ราคา

# thai_modules/compliance_checker_v2.py
compliance = ComplianceCheckerV2.check_compliance(results, specs)
# ตรวจสอบมอก./EIT/NEC

# thai_modules/layout_optimizer.py
layout = LayoutOptimizer.optimize_layout(loads, constraints)
# วาง layout เส้นสาย

# thai_modules/autolisp_generator.py
lisp_code = AutoLISPGenerator.generate(layout, symbols)
# สร้าง AutoLISP สำหรับ AutoCAD
```

### **Output (ส่งกลับ)**:
```json
{
  "mcp_results": {
    "wires": {
      "L001": {
        "wire_size_mm2": 2.5,
        "ampacity_a": 25,
        "voltage_drop_pct": 2.1,
        "is_acceptable": true
      }
    },
    "breakers": {
      "L001": {
        "model": "ABB-S201",
        "rating_a": 20,
        "curve": "C",
        "icu_ka": 6
      }
    },
    "conduits": {
      "L001": {
        "size_mm": 20,
        "fill_pct": 35,
        "is_acceptable": true
      }
    },
    "cost": {
      "total_thb": 12500,
      "items": [
        {
          "code": "WIRE-THW-2.5MM",
          "description": "สาย THW 2.5 mm²",
          "quantity": 50,
          "unit": "เมตร",
          "unit_price": 15,
          "total": 750
        }
      ]
    },
    "compliance": {
      "is_compliant": true,
      "violations": []
    },
    "autolisp_code": "(defun c:draw-circuit () ...)"
  }
}
```

---

## 📂 โครงสร้างไฟล์ที่ MCP ต้องมี

### **✅ ที่มีอยู่แล้ว** (ใน `/mcp_core_v2`):
```
mcp_core_v2/
├── models/
│   ├── contracts.py          ✅ (แต่ต้อง sync กับ RAG)
│   ├── baseline.py           ✅
│   └── catalog_models.py     ✅
├── core/
│   ├── load_calculator.py    ✅
│   ├── wire_sizer.py         ✅
│   ├── breaker_selector.py   ✅
│   ├── conduit_sizer.py      ✅
│   └── compliance_checker.py ✅
└── pipeline.py               ✅
```

### **❌ ที่ยังขาดหายไป**:

#### **1. Pandapower Bridge** (3 ไฟล์หลัก)
```
mcp_core_v2/
└── pandapower_bridge/
    ├── network_builder.py     ❌ → ต้องสร้าง
    ├── power_flow_runner.py   ❌ → มี pandapower_adapter.py แต่ไม่ถูกใช้
    └── result_extractor.py    ❌ → ต้องสร้าง
```

**หน้าที่**:
- `network_builder.py`: แปลง ProjectInputSpec → pandapower network
- `power_flow_runner.py`: รัน power flow simulation
- `result_extractor.py`: ดึงผลลัพธ์ออกมาเป็น dict

#### **2. Thai Modules** (6 ไฟล์)
```
mcp_core_v2/
└── thai_modules/
    ├── wire_sizer_v2.py       ❌ → ต้องสร้าง (แตกต่างจาก core/wire_sizer.py)
    ├── breaker_selector_v2.py ❌ → ต้องสร้าง
    ├── cost_estimator.py      ❌ → ต้องสร้าง
    ├── layout_optimizer.py    ❌ → ต้องสร้าง
    └── autolisp_generator.py  ⚠️ → มีใน core/ แต่อาจต้อง enhance
```

**ความแตกต่าง v2 กับ core/**:
- `core/`: ใช้ logic พื้นฐาน (NEC standard)
- `thai_modules/`: ใช้ผลจาก pandapower + กฎไทย (มอก./EIT) + catalog จริง

#### **3. Supabase Client** (2 ไฟล์)
```
mcp_core_v2/
└── supabase_client/
    ├── catalog_manager.py     ❌ → ต้องสร้าง
    └── schemas.py             ❌ → ต้องสร้าง
```

**หน้าที่**:
- ดึงข้อมูลจาก `amadeus.catalog` (wire specs, breaker models, prices)
- Sync กับสัญญาใน `CATALOG_CONTRACT.md`

#### **4. Utils** (2 ไฟล์)
```
mcp_core_v2/
└── utils/
    ├── json_loader.py         ❌ → ต้องสร้าง
    └── validators.py          ❌ → ต้องสร้าง
```

**หน้าที่**:
- โหลด JSON input จาก RAG
- Validate input ก่อนเข้า calculation

#### **5. Controller** (1 ไฟล์)
```
mcp_core_v2/
└── mcp_controller_v2.py       ❌ → ต้องสร้าง (ทำหน้าที่เหมือน pipeline.py แต่ครบกว่า)
```

**หน้าที่**: orchestrate ทุก step ตั้งแต่ pandapower → thai modules → output

#### **6. Config**
```
mcp_core_v2/
└── config/
    └── settings.py            ❌ → ต้องสร้าง
```

---

## 🔄 Data Flow ที่ถูกต้อง

### **Step-by-Step**:

```
1. Gateway รับ user prompt
   │
   ▼
2. RAG Service
   ├─ process_ask() → ตอบคำถาม
   └─ generate_mcp_spec() → สร้าง ProjectInputSpec
      │
      ▼
3. MCP Controller V2
   ├─ load ProjectInputSpec (JSON)
   ├─ NetworkBuilder → สร้าง pandapower network
   ├─ PowerFlowRunner → runpp()
   ├─ ResultExtractor → ดึงผลลัพธ์
   ├─ WireSizerV2 → เลือกสาย (ใช้ผล pandapower)
   ├─ BreakerSelectorV2 → เลือกเบรกเกอร์
   ├─ ConduitSizer → คำนวณท่อ
   ├─ CostEstimator → คำนวณราคา + BOQ
   ├─ ComplianceChecker → ตรวจสอบมอก./NEC
   ├─ LayoutOptimizer → วาง layout
   └─ AutoLISPGenerator → สร้าง .lsp code
      │
      ▼
4. Output: mcp_results.json + autolisp.lsp
   │
   ▼
5. Gateway ส่งกลับ User
```

---

## 📊 Comparison: Current vs Required

| Component | Current Status | Required | Priority |
|-----------|---------------|----------|----------|
| **Pandapower Bridge** | ⚠️ Partial (adapter exists but unused) | ✅ Full integration | 🔴 HIGH |
| **Thai Modules** | ❌ None | ✅ All 6 modules | 🔴 HIGH |
| **Supabase Client** | ⚠️ Basic (dal/supabase_client.py) | ✅ CatalogManager | 🟡 MEDIUM |
| **Controller V2** | ⚠️ Basic (pipeline.py) | ✅ Full orchestration | 🔴 HIGH |
| **Cost Estimator** | ❌ None | ✅ BOQ + Pricing | 🟡 MEDIUM |
| **Layout Optimizer** | ❌ None | ✅ 2D/3D layout | 🟢 LOW |
| **AutoLISP** | ✅ Exists | ⚠️ May need enhancement | 🟢 LOW |

---

## 🎯 MCP ต้องทำอะไรได้บ้าง? (Final Answer)

### **Core Capabilities**:

1. ✅ **รับ ProjectInputSpec จาก RAG**
   - Format: JSON ตาม schema ที่ sync กับ RAG

2. ✅ **คำนวณไฟฟ้าด้วย Pandapower**
   - Build network, run power flow, extract results

3. ✅ **เลือก Wire/Breaker/Conduit**
   - ตามผลจาก pandapower + NEC + มอก. + catalog

4. ✅ **คำนวณราคา + BOQ**
   - รายการวัสดุ + ปริมาณ + ราคารวม

5. ✅ **ตรวจสอบ Compliance**
   - มอก./EIT/NEC violations

6. ✅ **วาง Layout**
   - ตำแหน่งอุปกรณ์ + เส้นทางสาย

7. ✅ **สร้าง AutoLISP**
   - สำหรับนำเข้า AutoCAD

8. ✅ **Export Results**
   - JSON, PDF reports, DXF/LISP files

---

## 🚧 Gap Analysis

### **ปัญหาที่พบ**:

1. **Pandapower ไม่ได้ใช้งาน**
   - มี `pandapower_adapter.py` แต่ไม่ถูกเรียกใน pipeline

2. **ไม่มี Thai Modules**
   - ขาด wire_sizer_v2, cost_estimator, layout_optimizer

3. **ไม่มี CatalogManager**
   - ไม่ได้ต่อกับ `amadeus.catalog` จริง

4. **ไม่มี Controller V2**
   - `pipeline.py` ทำไม่ครบ (ไม่มี cost, layout, BOQ)

5. **Input/Output Format ไม่ sync กับ RAG**
   - `contracts.py` ต้อง update ให้ตรงกับ RAG schema

---

## 💡 Recommendations

### **Immediate Actions** (ต้องทำก่อน):

1. **Sync Schema กับ RAG**
   - อัพเดต `models/contracts.py` ให้ตรง ProjectInputSpec ของ RAG

2. **Integrate Pandapower**
   - แปลง `pandapower_adapter.py` → `pandapower_bridge/`
   - เขียน network_builder, result_extractor

3. **สร้าง Thai Modules**
   - wire_sizer_v2, breaker_selector_v2, cost_estimator

4. **สร้าง Controller V2**
   - orchestrate ทุก step ให้ครบ

### **Medium Term**:

5. **Catalog Integration**
   - สร้าง CatalogManager ต่อกับ Supabase

6. **BOQ + Pricing**
   - Implement cost_estimator

### **Long Term**:

7. **Layout Optimization**
   - Implement layout_optimizer

8. **Enhanced AutoLISP**
   - อาจต้อง enhance ให้ support layout data

---

## 📝 สรุป

### **MCP Core v2 ควรทำอะไร?**

**คำตอบสุดท้าย**:

> MCP Core v2 คือ **"เครื่องยนต์คำนวณไฟฟ้า"** ที่:
> 1. รับ **JSON spec** จาก RAG (ProjectInputSpec)
> 2. ใช้ **Pandapower** จำลองวงจรไฟฟ้าจริง
> 3. ใช้ **Thai Modules** เลือก Wire/Breaker/Conduit ตามกฎไทย + catalog
> 4. คำนวณ **BOQ + ราคา**
> 5. ตรวจสอบ **Compliance** (มอก./EIT/NEC)
> 6. วาง **Layout** เส้นสาย
> 7. สร้าง **AutoLISP** สำหรับ AutoCAD
> 8. ส่งคืน **mcp_results.json** + ไฟล์ CAD

### **Code ที่มีตอนนี้ใช้งานได้หรือไม่?**

**คำตอบ**: ⚠️ **ใช้ได้บางส่วน** (30-40%)
- Load calculation, Wire sizing, Breaker selection → ใช้ได้
- แต่ขาด: Pandapower integration, Thai modules, Cost/BOQ, Layout

### **ต้องทำอะไรเพิ่ม?**

**คำตอบ**: ต้องเพิ่ม **60-70%** ของ features:
1. Pandapower bridge (3 files)
2. Thai modules (6 files)
3. Catalog manager (2 files)
4. Controller V2 (1 file)
5. Utils (2 files)

---

**Prepared by**: Laplacia  
**Confidence**: 95% (based on 4 source documents)  
**Status**: ✅ **FULLY UNDERSTOOD**
