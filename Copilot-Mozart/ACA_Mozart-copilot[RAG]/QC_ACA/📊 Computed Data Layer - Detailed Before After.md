# 📊 Computed Data Layer - Detailed Before/After

> **อ้างอิง:** `QC_ACA/🎨 Computed Data Layer - Implementation Plan.md`

---

## 🔴 BEFORE (ปัจจุบัน)

### Data Flow:
```
mcp_result (JSON from MCP Core)
    │
    └──→ markdown_formatter.py ──→ Markdown string
             │
             ├── _create_header()         ← คำนวณ total_watts, demand_current
             ├── _create_main_equipment() ← คำนวณ meter_size, main_breaker
             ├── _create_circuit_schedule()
             └── _create_footer()
```

### ไฟล์ที่เกี่ยวข้อง:
```
app/formatters/
├── __init__.py
├── base_formatter.py
├── markdown_formatter.py    ← ⚠️ มีทั้ง CALCULATE + RENDER
├── audit_formatter.py       ← แยกต่างหาก
└── pdf_formatter.py         ← แยกต่างหาก
```

### ❌ ปัญหา:
- `markdown_formatter.py` **คำนวณเอง** (lines 92-98, 129-145)
- ถ้าต้องการ SLD/BOQ → **ต้องคำนวณใหม่** → ค่าอาจไม่ตรง!

---

## 🟢 AFTER (หลังแก้ไข)

### Data Flow:
```
mcp_result (JSON from MCP Core)
    │
    └──→ compute.py ──→ DisplayData (JSON dict)
              │
              └──→ { total_watts, demand_current, main_breaker,
                     meter_size, circuits[], warnings[], ... }
              │
    ┌─────────┼─────────────┬──────────────────┐
    │         │             │                  │
    ↓         ↓             ↓                  ↓
markdown_  audit_       sld_           (อนาคต)
renderer   renderer     renderer       boq_renderer
    │         │             │                  │
    ↓         ↓             ↓                  ↓
Markdown   Audit MD     SLD JSON        BOQ Excel
```

### ไฟล์ที่เปลี่ยน:

#### 🆕 ไฟล์ใหม่ (สร้าง):
```
app/display/                    ← 🆕 โฟลเดอร์ใหม่
├── __init__.py                 ← 🆕 exports
├── compute.py                  ← 🆕 คำนวณครั้งเดียว
└── markdown_renderer.py        ← 🆕 render Markdown (ไม่คำนวณ)
```

#### ✏️ ไฟล์ที่แก้ไข:
| ไฟล์ | เปลี่ยนอะไร |
|------|------------|
| `app/models.py` | เพิ่ม `display_data: Optional[Dict]` ใน AnswerMetadata |
| `app/service.py` | เรียก `compute_display_data()` → `render_markdown()` |

#### ⚡ ไฟล์ที่เก็บไว้ (ไม่ลบ):
| ไฟล์ | ทำไมเก็บไว้ |
|------|------------|
| `app/formatters/markdown_formatter.py` | Backward compatibility (ใช้เดิมได้ถ้าเกิดปัญหา) |
| `app/formatters/audit_formatter.py` | ยังใช้อยู่ (อาจ refactor ทีหลัง) |

---

## 🔧 Logic ที่ต้องย้ายออกจาก Markdown

### จาก `markdown_formatter.py`:

| Method | Line | Logic ที่คำนวณ | ย้ายไป |
|--------|------|--------------|--------|
| `_create_header()` | 92-98 | `total_watts`, `demand_current` | `compute.py` |
| `_create_main_equipment()` | 129-145 | `meter_size`, `main_wire`, `main_cb` | `compute.py` |
| `round_up()` | 17-22 | Helper function | `compute.py` |

### ตัวอย่าง Code ที่ย้าย:

**FROM `markdown_formatter.py` line 92-98:**
```python
# ⚠️ คำนวณทุกครั้งที่ render!
total_watts = summary.get('total_watts', 0)
demand_current = total_watts / 230 if total_watts else 0
```

**TO `compute.py`:**
```python
# ✅ คำนวณครั้งเดียว ใน DisplayData
display_data = {
    'total_watts': round_up(total_watts),
    'demand_current': round_up(demand_current, 1),
    'main_breaker': main_breaker,
    ...
}
```

---

## 📋 สรุปไฟล์

| จำนวน | ประเภท | ไฟล์ |
|:-----:|--------|------|
| **3** | 🆕 สร้างใหม่ | `display/__init__.py`, `display/compute.py`, `display/markdown_renderer.py` |
| **2** | ✏️ แก้ไข | `service.py`, `models.py` |
| **0** | ❌ ลบ | ไม่มี (เก็บ markdown_formatter.py ไว้) |

---

## ✅ ประโยชน์

1. **ทุก output ใช้ค่าเดียวกัน** (Markdown, SLD, BOQ)
2. **Frontend ได้ `display_data` JSON** → แสดง Table ได้ทันที
3. **Test แยกได้** - test compute, test renderer
4. **ไม่ลบ code เดิม** - ถ้ามีปัญหา fallback ได้

---

## 🔍 Audit Enhancement (PDF-Ready)

### ปัญหาเดิม:
- `audit_results` ไม่ถูกส่งแยก → Frontend ต้อง parse Markdown
- ไม่มีเอกสาร Audit ทางการ

### วิธีแก้:

```
audit_validator.py (คงเดิม)
       ↓
audit_results (JSON)
       │
       ├──→ audit_formatter.py (คงเดิม) → Markdown in Chat
       │
       ├──→ metadata.audit_results 🆕 → Frontend Tab "Audit"
       │
       └──→ audit_document.py 🆕 → เอกสาร PDF-ready
                                    ├── Header (โครงการ, วันที่)
                                    ├── Table (รายการตรวจ, ค่า User, ค่าแนะนำ, ผล)
                                    ├── Warnings รวมจาก injectors
                                    ├── Standards Reference
                                    └── Footer (ผู้ตรวจสอบ, หมายเหตุ)
```

---

## 📦 BOQ (Bill of Quantity)

### Data Source:
- ใช้ `pdf_formatter.py` ที่มีอยู่
- Function: `format_pdf_table(mcp_result)` → Structured dict

### การส่งไป Frontend:
```python
metadata=AnswerMetadata(
    pdf_data=format_pdf_table(result),  # 🆕
)
```

---

## 🖼️ SLD (Single Line Diagram) - Future

### Data Source:
- จะสร้าง `sld_renderer.py`
- อ่านจาก `display_data` (circuits, main_breaker, etc.)

---

## 📋 Phased Implementation

| Phase | งาน | ไฟล์ที่แก้ |
|:-----:|-----|----------|
| **1** | Load Table โชว์ก่อน | `models.py`, `display/compute.py`, `service.py`, `App.tsx` |
| **2** | ต่อท่อ Audit (PDF-ready) | `display/audit_document.py`, `models.py`, `service.py` |
| **3** | ต่อท่อ BOQ | `models.py`, `service.py` (ใช้ pdf_formatter ที่มี) |
| **4** | ต่อท่อ SLD | `display/sld_renderer.py`, `models.py`, `service.py` |

---

## 📁 สรุปไฟล์ทั้งหมด

| จำนวน | ประเภท | ไฟล์ |
|:-----:|--------|------|
| **4** | 🆕 สร้างใหม่ | `display/__init__.py`, `compute.py`, `markdown_renderer.py`, `audit_document.py` |
| **2** | ✏️ แก้ไข | `service.py`, `models.py` |
| **2** | ✏️ แก้ Frontend | `App.tsx`, `types/index.ts` |
| **0** | ❌ ลบ | ไม่มี (เก็บ formatters เดิม) |

---

## ✅ หลักการสำคัญ

1. **ลด Regression** - ไม่ลบ code เดิม, เพิ่ม layer wrap ทับ
2. **MVC** - แยก compute / formatters / controller
3. **ทำทีละ Phase** - โชว์ได้ก่อน แล้วค่อยต่อท่อ
4. **Compute Once** - `display_data` ใช้ร่วมกันทุก output

---

*Updated: 2025-12-30 | By Fixia*

