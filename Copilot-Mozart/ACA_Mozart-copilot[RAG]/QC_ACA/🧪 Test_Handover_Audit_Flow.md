# 🧪 Test Handover: Audit Mode Data Flow

> **วันที่:** 2025-12-25
> **สถานะ:** พร้อม Test (ยังไม่ได้ test จริง)
> **ความมั่นใจ:** 80%

---

## 🎯 เป้าหมาย

ทดสอบว่า **Audit Mode** ทำงานถูกต้อง:
1. ผู้ใช้พิมพ์ค่า breaker/wire เอง (เช่น "16a")
2. LLM สกัดค่าได้
3. ระบบเปรียบเทียบกับค่าที่คำนวณ
4. แสดงผล PASS/FAIL บน Frontend

---

## 📊 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                   │
│   "ออกแบบบ้าน น้ำอุ่น 3500W 16a"                                      │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         GATEWAY                                      │
│   gate_way_new.py                                                   │
│   - POST /api/v1/ask                                                │
│   - payload: { query, site_context, language }                      │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG SERVICE                                  │
│   app/service.py                                                    │
│                                                                     │
│   [CP-ASK] LLM Extraction                                           │
│   ↓                                                                 │
│   extracted_loads = [{                                              │
│     "device": "น้ำอุ่น",                                             │
│     "power_watts": 3500,                                            │
│     "user_breaker": 16,    ← ค่าที่ user ระบุ                        │
│     "confidence": 0.9                                               │
│   }]                                                                │
│   ↓                                                                 │
│   Attach to req._extracted_loads                                    │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP CORE                                     │
│   mcp_core_v2/pipeline.py                                           │
│                                                                     │
│   [CP7] Circuit Grouping                                            │
│   ↓                                                                 │
│   GroupedCircuit = {                                                │
│     "circuit_name": "วงจรน้ำอุ่น",                                   │
│     "breaker_rating": 20,  ← ค่าที่ MCP คำนวณ (auto)                 │
│     "wire_size": "4.0",                                             │
│     "loads": [...]                                                  │
│   }                                                                 │
│   ↓                                                                 │
│   ResultBuilder.build_result(grouped_circuits=[...])                │
│   ↓                                                                 │
│   DesignResponse.grouped_circuits                                   │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         AUDIT VALIDATION                             │
│   app/audit_validator.py                                            │
│                                                                     │
│   [CP-AUDIT] validate_user_specs(grouped_circuits, extracted_loads) │
│   ↓                                                                 │
│   Compare: user_breaker (16) vs auto_breaker (20)                   │
│   ↓                                                                 │
│   Result: FAIL (16 < 20)                                            │
│   ↓                                                                 │
│   audit_results = [{                                                │
│     "circuit_name": "วงจรน้ำอุ่น",                                   │
│     "checks": [{                                                    │
│       "item": "breaker",                                            │
│       "user_value": "16A",                                          │
│       "auto_value": "20A",                                          │
│       "status": "FAIL"                                              │
│     }]                                                              │
│   }]                                                                │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         AUDIT FORMATTER                              │
│   app/formatters/audit_formatter.py                                 │
│                                                                     │
│   [CP-FMT-AUDIT] format_audit_report(audit_results)                 │
│   ↓                                                                 │
│   Output Markdown:                                                  │
│   | โหลด | รายการ | ค่า User | ค่าแนะนำ | ผล |                       │
│   |------|--------|----------|----------|:--:|                       │
│   | น้ำอุ่น | Breaker | 16A (สีแดง) | 20A | ❌ |                     │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                     │
│                                                                     │
│   ซ้าย: ChatPane (MessageBubble.tsx)                                 │
│   - แสดง Load Schedule + Audit Report (Markdown)                    │
│                                                                     │
│   ขวา: AuditPane.tsx                                                │
│   - Parse Markdown → แสดง PASS/FAIL cards พร้อมสี                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Test Cases

### Test 1: Regression (Normal Input - ไม่มี Audit)

**Input:**
```
ออกแบบบ้าน 2 ชั้น มีแอร์ 3 ตัว ห้องนอน 2 ห้อง
```

**Expected:**
- ✅ Load Schedule แสดงปกติ
- ✅ **ไม่มี** Audit Report section
- ✅ AuditPane (ขวา) แสดง "ยังไม่มีข้อมูล Audit"

**Verify Logs:**
```
[CP-AUDIT-FLOW] No user specs, skipping audit
```

---

### Test 2: Audit FAIL (User breaker ต่ำกว่า Auto)

**Input:**
```
ออกแบบบ้าน น้ำอุ่น 3500W 16a
```

**Expected:**
- ✅ Load Schedule แสดง น้ำอุ่น with breaker 20A (auto)
- ✅ Audit Report section แสดง:
  ```
  | น้ำอุ่น | Breaker | 16A | 20A | ❌ |
  ```
- ✅ AuditPane (ขวา) แสดง FAIL card สีแดง

**Verify Logs:**
```
[CP-ASK] extracted: user_breaker=16
[CP-AUDIT-FLOW] User specs found, running audit validation
[CP-AUDIT] FAIL: วงจรน้ำอุ่น breaker 16A < 20A
[CP-FMT-AUDIT] Format complete: 0 PASS, 0 WARN, 1 FAIL
```

---

### Test 3: Audit PASS (User breaker >= Auto)

**Input:**
```
ออกแบบบ้าน น้ำอุ่น 3500W 25a
```

**Expected:**
- ✅ Load Schedule แสดง breaker 20A (auto)
- ✅ Audit Report section แสดง:
  ```
  | น้ำอุ่น | Breaker | 25A | 20A | ✅ |
  ```
- ✅ AuditPane (ขวา) แสดง PASS card สีเขียว

**Verify Logs:**
```
[CP-AUDIT] PASS: วงจรน้ำอุ่น breaker 25A >= 20A
```

---

### Test 4: Audit WARN (User breaker ใหญ่เกินไป)

**Input:**
```
ออกแบบบ้าน น้ำอุ่น 3500W 50a
```

**Expected:**
- ✅ Audit Report แสดง WARN (50A > 20A * 1.5)
- ✅ AuditPane แสดง WARN card สีเหลือง

---

### Test 5: Wire Size Check

**Input:**
```
ออกแบบบ้าน น้ำอุ่น 3500W สาย 2.5mm
```

**Expected:**
- ✅ Audit แสดง wire_size: user=2.5mm, auto=4.0mm → FAIL

---

## 📁 Files Involved

| File | Role | Checkpoint |
|------|------|------------|
| `gate_way_new.py` | Route to RAG | [CP1] |
| `app/service.py` | LLM extraction, MCP call, audit integration | [CP-ASK], [CP-AUDIT-FLOW] |
| `mcp_core_v2/pipeline.py` | Calculate, group circuits | [CP7] |
| `mcp_core_v2/core/circuit_grouper.py` | Create GroupedCircuit | - |
| `mcp_core_v2/core/result_builder.py` | Build DesignResult | - |
| `app/audit_validator.py` | Compare user vs auto | [CP-AUDIT] |
| `app/formatters/audit_formatter.py` | Format to Markdown | [CP-FMT-AUDIT] |
| `frontend/.../AuditPane.tsx` | Parse & display | - |

---

## ⚠️ Known Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM ไม่สกัด `user_breaker` | Medium | High | Check prompt & few-shot examples |
| Device name mismatch | Medium | Medium | Fuzzy matching in audit_validator |
| Frontend parse ผิด | Low | Medium | Regex ตรงกับ formatter output |
| MCP ไม่ส่ง `grouped_circuits` | Low | High | Check API response |

---

## 🔍 Debug Commands

### 1. Check Cloud Run Logs
```bash
gcloud run logs read mozart-rag --region asia-southeast1 --limit 50 | grep -E "\[CP-"
```

### 2. Test API Directly
```bash
curl -X POST https://mozart-rag-rc5mtgajza-as.a.run.app/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "ออกแบบบ้าน น้ำอุ่น 3500W 16a", "language": "th"}'
```

### 3. Check LLM Extraction
Look for in logs:
```
[CP-ASK] Extracted loads: ...user_breaker...
```

---

## ✅ Success Criteria

1. **Test 1 passes** - No regression on normal flow
2. **Test 2 passes** - Audit FAIL shows correctly
3. **Test 3 passes** - Audit PASS shows correctly
4. **AuditPane renders** - Right pane shows data
5. **Colors work** - Red/Yellow/Green displayed

---

*Created: 2025-12-25 00:21*
*Author: AI Assistant (Maid)*
