# 🔧 Mozart Session/VD Fix Memory - 2026-01-07

## สรุปปัญหาและการแก้ไข

---

## 1. ✅ VOLTAGE DROP (VD) Pipeline Fix

### ปัญหา:
- VD แสดง 2.0% ตลอด (ค่า default) แทนค่าจริงที่คำนวณได้
- ค่า VD ถูกคำนวณถูกต้องใน `mcp_core_v2/pipeline.py` แต่หายไประหว่างทาง

### Root Cause:
- `wire_sizing` keyed by `load.id` (เช่น `load_1`, `load_2`)
- `compute.py` พยายาม lookup ด้วย `circuit_id` (เช่น `ckt_1`)
- **Key mismatch** → fallback ไป default 2.0%

### วิธีแก้ไข:
1. **service.py Line 106-175**: เพิ่ม `_inject_vd_to_circuits()` helper
   - Map VD จาก `wire_sizing[load.id]` → `grouped_circuits[ckt].voltage_drop_percent`
   - เรียกก่อน `compute_display_data()`

2. **compute.py Line 405-414**: แก้ `_process_circuits()`
   - อ่าน `voltage_drop_percent` จาก circuit dict โดยตรง (ไม่ lookup wire_sizing)

3. **markdown_formatter.py Line 445-448**: 
   - อ่าน VD จาก circuit dict เหมือนกัน

---

## 2. ✅ SESSION PERSISTENCE Fix

### ปัญหา:
- กดสร้าง Project ใหม่แล้วทับอันเก่า
- Session หายเมื่อ refresh

### Root Cause:
- Supabase table `mozart.sessions` **ไม่มี column `project_name`**
- Backend พยายาม INSERT → Supabase reject (400 Bad Request)
- Fallback ไป in-memory → ข้อมูลหายเมื่อ Cloud Run restart

### Cloud Log Evidence:
```
ERROR - Failed to create session: 
  {'message': "Could not find the 'project_name' column of 'sessions'", 
   'code': 'PGRST204'}
```

### วิธีแก้ไข:
**Run SQL บน Supabase Dashboard:**
```sql
ALTER TABLE mozart.sessions 
ADD COLUMN IF NOT EXISTS project_name TEXT DEFAULT 'บ้านนายสมหญิง';
```

✅ User ทำแล้วเมื่อ 2026-01-06 23:55

---

## 3. ✅ AUDIT WARNING Fixes

### ปัญหาที่แก้ไข:

| ปัญหา | Root Cause | วิธีแก้ | File |
|-------|-----------|--------|------|
| ชื่อตัด "INDUCTION...ห" | `[:20]` truncation | ลบ truncation | `markdown_formatter.py:521`, `audit_formatter.py:49` |
| "36 วงจร" (นับผิด) | Loop ผ่าน load.id 36 ตัว | Map to unique circuits | `markdown_formatter.py:81-105` |
| "require 125%" (สับสน) | Message ไม่ชัด | เปลี่ยนเป็น "✅ ใช้...แล้ว" | `compliance_checker.py:161-167` |
| "ขนาดเดิม" (คลุมเครือ) | Placeholder fallback | เปลี่ยนเป็น "(ดูค่าในตาราง)" | `explainable_qc.py:160-172` |

---

## 4. ⚠️ Known Issues (Not Fixed Yet)

### 4.1 session_id = None บางครั้ง
- Cloud log แสดง `session_id: None` ในบาง requests
- สาเหตุ: Race condition - user กด submit ก่อน auth ready
- แนะนำ: ตรวจสอบ Frontend `App.tsx` ให้รอ session ready ก่อน enable submit

### 4.2 APP_ENV AttributeError (เมื่อวาน - Deploy time)
```
AttributeError: 'Settings' object has no attribute 'APP_ENV'
```
- เกิดเมื่อ 2026-01-05 18:10
- ต้องเช็ค `app/settings.py` ว่ามี `APP_ENV` field

---

## Files Modified (This Session)

### Backend:
- `app/service.py` - VD injection
- `app/display/compute.py` - VD reading
- `app/formatters/markdown_formatter.py` - VD reading, circuit name fix, unique count
- `app/formatters/audit_formatter.py` - circuit name fix
- `app/display/explainable_qc.py` - better fallback messages
- `mcp_core_v2/core/compliance_checker.py` - continuous load message

### Database:
- `mozart.sessions` - Added `project_name TEXT` column

---

## Verification Commands

```bash
# Check recent errors
gcloud logging read 'resource.labels.service_name="mozart-rag" AND severity>=WARNING' \
  --project=gen-lang-client-0658701327 --limit=20 --freshness=1h

# Check session create success
gcloud logging read 'textPayload=~"Created session"' \
  --project=gen-lang-client-0658701327 --limit=10 --freshness=1h
```

---

**Last Updated:** 2026-01-07 00:00 (ICT)
