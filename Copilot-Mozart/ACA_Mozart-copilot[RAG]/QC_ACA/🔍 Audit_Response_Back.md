# 🔍 Audit Mode - Response Back Walkthrough

> **วันที่:** 2025-12-24
> **Commits:** `07c7a80`, `4d70b94`, `4abb068`
> **Status:** ✅ Deployed to Cloud Run

---

## 🎯 เป้าหมาย

ให้ผู้ใช้ระบุค่าเอง (เช่น breaker 16A) แล้วระบบตรวจสอบว่าผ่านหรือไม่

---

## 📥 Input ที่คาดหวัง

### Case 1: Normal Input (ไม่มี User Spec)
```
บ้าน 2 ชั้น มีแอร์ 3 ตัว ห้องนอน 2 ห้อง
```

### Case 2: Input พร้อม User Breaker (Audit FAIL)
```
บ้าน 2 ชั้น น้ำอุ่น 3500W 16a ห้องน้ำ 1 ห้อง
```

### Case 3: Input พร้อม User Breaker (Audit PASS)
```
บ้าน 2 ชั้น น้ำอุ่น 3500W 25a ห้องน้ำ 1 ห้อง
```

---

## 📤 Expected Output

### Case 1: Normal (ไม่มี Audit Section)

```markdown
# 📋 ตารางโหลด (Load Schedule)

## 🏠 ชั้น 1

### ห้องนอน
| อุปกรณ์ | จำนวน | กำลังไฟ | เบรกเกอร์ | ขนาดสาย |
|---------|-------|---------|-----------|---------|
| แอร์ 12000 BTU | 1 | 1,100W | 16A | 2.5 mm² |

...

✅ **ไม่มี Audit Section** (เพราะไม่ได้ระบุ breaker/wire)
```

---

### Case 2: Audit FAIL (16A < 20A แนะนำ)

```markdown
# 📋 ตารางโหลด (Load Schedule)

## 🏠 ชั้น 1

### ห้องน้ำ
| อุปกรณ์ | จำนวน | กำลังไฟ | เบรกเกอร์ | ขนาดสาย |
|---------|-------|---------|-----------|---------|
| น้ำอุ่น 3500W | 1 | 3,500W | 20A | 4.0 mm² |

---

## 🔍 รายงานตรวจสอบ (Audit Report)

> ⚠️ ค่าด้านล่างเป็น **ค่าที่ผู้ใช้ระบุ** เทียบกับ **ค่าที่ระบบแนะนำ**

| โหลด | รายการ | ค่า User | ค่าแนะนำ | ผล |
|------|--------|----------|----------|:--:|
| น้ำอุ่น 3500W | Breaker | <span style='background:#ffcccc;color:#cc0000'><b>16A</b></span> | 20A | ❌ |

**สรุป:** ✅ 0 รายการผ่าน, ❌ 1 รายการไม่ผ่าน

### ❌ รายการที่ไม่ผ่าน
- **น้ำอุ่น 3500W**: Breaker 16A เล็กกว่าที่แนะนำ 20A
```

---

### Case 3: Audit PASS (25A >= 20A แนะนำ)

```markdown
# 📋 ตารางโหลด (Load Schedule)

## 🏠 ชั้น 1

### ห้องน้ำ
| อุปกรณ์ | จำนวน | กำลังไฟ | เบรกเกอร์ | ขนาดสาย |
|---------|-------|---------|-----------|---------|
| น้ำอุ่น 3500W | 1 | 3,500W | 20A | 4.0 mm² |

---

## 🔍 รายงานตรวจสอบ (Audit Report)

> ⚠️ ค่าด้านล่างเป็น **ค่าที่ผู้ใช้ระบุ** เทียบกับ **ค่าที่ระบบแนะนำ**

| โหลด | รายการ | ค่า User | ค่าแนะนำ | ผล |
|------|--------|----------|----------|:--:|
| น้ำอุ่น 3500W | Breaker | <span style='background:#d4edda;color:#155724'><b>25A</b></span> | 20A | ✅ |

**สรุป:** ✅ 1 รายการผ่าน
```

---

## 🎨 Color Styling

| Status | Background | Text Color | ตัวอย่าง |
|--------|------------|------------|----------|
| ❌ FAIL | #ffcccc | #cc0000 | <span style='background:#ffcccc;color:#cc0000'><b>16A</b></span> |
| ⚠️ WARN | #fff3cd | #856404 | <span style='background:#fff3cd;color:#856404'><b>32A</b></span> |
| ✅ PASS | #d4edda | #155724 | <span style='background:#d4edda;color:#155724'><b>25A</b></span> |

---

## 📁 Files Changed

| ไฟล์ | งาน |
|------|-----|
| `app/service.py` | LLM schema + Integration |
| `app/audit_validator.py` | 🆕 Compare User vs Auto |
| `app/formatters/audit_formatter.py` | 🆕 Format Audit Report |

---

## 🔍 Checkpoint Logging

```
[CP-ASK] → _should_ask_back()
[CP-AUDIT-FLOW] → Attach loads, validate
[CP-AUDIT] → validate_user_specs()
[CP-FMT-AUDIT] → format_audit_report()
```

---

*Created: 2025-12-24 23:53*
