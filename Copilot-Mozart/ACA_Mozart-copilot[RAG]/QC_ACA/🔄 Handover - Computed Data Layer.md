# 🔄 Handover Document - Computed Data Layer

> **Session:** 2025-12-30  
> **Status:** ⚠️ Partial Complete - มี pending issues  
> **Next Developer:** [ชื่อ]

---

## ✅ สิ่งที่ทำเสร็จแล้ว

| Phase | Status | Description |
|:-----:|:------:|-------------|
| 0 | ✅ | Deep Dive Analysis - หา root cause |
| 1 | ✅ | Computed Data Layer - `compute.py` (Source of Truth) |
| 2 | ⚠️ | Audit - มีแค่ warning, ยังไม่มี QC Form |
| 3 | ✅ | BOQ - ต่อท่อ `pdf_data` แล้ว |
| 4 | ⚠️ | SLD - ใช้งานได้ แต่ดูการ์ตูน |
| 5 | ✅ | Frontend SLD Viewer |
| 6 | ✅ | Integration Check + Type Fix |
| 7 | ✅ | Price Scraper Fix |

---

## ❌ Known Issues (ต้องแก้)

### Issue 1: ตาราง Load Table ไม่ตรงกับ PDF Reference

**ปัญหา:**
- ตาราง Load Table ปัจจุบันไม่ตรงกับ format ที่ต้องการ
- ต้องตรวจสอบว่ามี reference PDF อยู่ที่ไหน

**ตรวจสอบ:**
```
QC_ACA/Pasted image.png  ← reference format?
```

**แก้ที่:**
- `app/display/compute.py` - ปรับ CircuitData fields
- `frontend/src/components/ResultViewer.tsx` - ปรับ columns

---

### Issue 2: Audit ไม่มี QC Form

**ปัญหา:**
- ปัจจุบันแสดงแค่ warnings
- ยังไม่มี formal QC checklist form

**แก้ที่:**
- `app/display/audit_document.py` - เพิ่ม QC form template
- `app/audit_validator.py` - เพิ่ม checklist items

**Expected Output:**
```
| รายการตรวจสอบ | มาตรฐาน | ค่าที่ได้ | ผล |
|---------------|---------|----------|:--:|
| สายไฟ > กระแส | วสท. 5.3 | 2.5mm² > 22A | ✅ |
| VD% < 3% | วสท. 6.2 | 2.1% | ✅ |
| Breaker rating | NEC 240.4 | 20A/25A | ⚠️ |
```

---

### Issue 3: SLD ดูการ์ตูนไป

**ปัญหา:**
- ใช้ emoji icons (📊, ⚡, 🛡️)
- สีสันสดใส ไม่ professional

**แก้ที่:**
- `app/display/sld_renderer.py` - ปรับ layout
- `frontend/src/components/SLDViewer.tsx` - ใช้ proper electrical symbols

**Expected:**
- ใช้ IEC 60617 electrical symbols
- สีโทน engineering (grayscale + accent)
- Line weight ตาม standard

---

## 📁 Files สำคัญที่ต้องเข้าใจ

### Backend: `app/display/`

```
app/display/
├── __init__.py          # Package exports
├── compute.py           # ⭐ SOURCE OF TRUTH - ศูนย์กลางคำนวณ
├── markdown_renderer.py # Render Markdown (ไม่คำนวณ)
├── audit_document.py    # PDF-ready audit (ต้องเพิ่ม QC form)
└── sld_renderer.py      # SLD JSON + SVG (ต้องปรับ professional)
```

### Frontend: Components

```
frontend/src/components/
├── ResultViewer.tsx     # Main viewer - 3 tabs
├── SLDViewer.tsx        # SLD renderer (ต้องปรับ)
└── ...
```

---

## 🔗 Data Flow (ต้องเข้าใจ)

```
User Input
    ↓
Gateway → RAG → MCP Core
    ↓
mcp_response.to_dict()
    ↓
┌────────────────────────────────┐
│     compute.py                 │ ← Source of Truth
│     compute_display_data()     │
│     Returns: DisplayData       │
└────────────────┬───────────────┘
                 │
    ┌────────────┼────────────────────┐
    │            │            │       │
    ↓            ↓            ↓       ↓
service.py   render_sld()   format_  render_
    │                       audit    markdown
    ↓
metadata {
  display_data,    ← Load Table
  audit_results,   ← Audit Tab
  pdf_data,        ← BOQ
  sld_data         ← SLD Tab
}
    ↓
Frontend App.tsx
    ↓
ResultViewer.tsx
```

---

## 🎯 Next Steps (Priority Order)

### P0: Must Fix Before Deploy
- [ ] ตรวจสอบ Load Table format กับ reference PDF
- [ ] Test on Cloud Run

### P1: Should Fix Soon
- [ ] เพิ่ม QC Form ใน Audit Tab
- [ ] ปรับ SLD ให้ professional

### P2: Nice to Have
- [ ] Download PDF button
- [ ] Export to Excel

---

## 📞 Contact

Questions? ดูไฟล์:
- `QC_ACA/🎀 Session Walkthrough 2025-12-30.md` - รายละเอียดทุก step
- `QC_ACA/📊 Computed Data Layer - Detailed Before After.md` - Before/After analysis

---

*Handover Created: 2025-12-30 03:06*
