# RAG Test Harness - Final Walkthrough

**วันที่**: 2025-12-02  
**Task**: แก้ไข RAG Test Cases + ทดสอบ Interactive Flow

---

## 🎯 เป้าหมายและผลลัพธ์

### เป้าหมาย
- ยกระดับ test cases จาก HARD-FAIL → PASS
- เป้าหมาย: PASS ≥ 10, SOFT-FAIL ≤ 2, HARD-FAIL = 0

### ผลลัพธ์สุดท้าย ✅
```
✅ PASS: 10/12 (83.3%)
⚠️ SOFT-FAIL: 2/12
❌ HARD-FAIL: 0/12
```

**บรรลุเป้าหมายทั้งหมด!**

---

## 📝 สรุปงานที่ทำ

### 1. แก้ไข Q-BREAKER-SELECTION (HARD-FAIL → PASS)

**ปัญหา**: LLM คำนวณ 18A × 1.25 = 22.5A แต่ตอบ "22A" แทน "25A"

**การแก้ไข**:
1. สร้าง `rag_knowledge/standard/BREAKER_80_PERCENT_RULE.md`
   - เพิ่มกรณีศึกษา 5 กรณี (7A→10A, 14A→20A, 18A→25A, 21A→32A, 35A→50A)
   - เน้น ❌ ห้ามตอบ และ ✅ ควรตอบ

2. อัปเดต `rag_knowledge/standard/00_KEY_TABLES.md`
   - เพิ่มตารางเลือกเบรกเกอร์อย่างรวดเร็ว
   - มีคอลัมน์ "ห้ามเลือก" (20, 22, 28, 35)

3. อัปเดต System Prompt ใน `app/service.py`
   - เพิ่มตัวอย่างการคำนวณ 4 กรณี
   - บอกชัด "ห้ามตอบ 22, 28, 35"
   - ระบุ standard sizes ทั้งหมด

4. อัปเดต `rag_knowledge/knowledge_index.json`
   - เพิ่ม entry `DOC_STD_BREAKER_RULES`
   - เพิ่ม tag "breaker" ใน KEY_TABLES

**ผลลัพธ์**: ✅ PASS - LLM ตอบ "25A" ถูกต้อง

---

### 2. ทดสอบ Deployment Safety

**วิธีทดสอบ**:
- ลบ `vector_db/` directory
- Restart API server
- Force rebuild vector DB
- Run test harness อีกครั้ง

**ผลลัพธ์**: ✅ ผ่าน - ไม่มี regression

---

### 3. ทดสอบ Interactive Project Creation

**Scenario**: สร้างบ้าน 2 ชั้นแบบ step-by-step

**ผลการทดสอบ**:
- Step 1 (ถามเริ่มต้น): ✅ ถามกลับครบ
- Step 2 (ข้อมูลห้อง): ✅ จำข้อมูล "สมชาย" ได้
- Step 3 (เครื่องใช้): ✅ Map device codes ถูก (AC-12000BTU, HEATER-3500W)
- Step 4 (ขอ JSON): ❌ ไม่มี conversation memory

**สรุป**: 3/4 PASS (75%)

**ปัญหาที่พบ**: API เป็น one-shot ไม่มี conversation history

---

## 📊 ไฟล์ที่แก้ไข

### Modified Files
1. `app/service.py` - อัปเดต System Prompt (เพิ่มตัวอย่างเบรกเกอร์)
2. `rag_knowledge/standard/00_KEY_TABLES.md` - เพิ่มตารางเลือกเบรกเกอร์
3. `rag_knowledge/knowledge_index.json` - เพิ่ม BREAKER_RULES entry
4. `tests/one_shot_qa/layer1_rules.py` - Fix ROOM_TEMPLATES validation

### New Files
1. `rag_knowledge/standard/BREAKER_80_PERCENT_RULE.md` - กฎการเลือกเบรกเกอร์
2. `test_interactive_project.py` - Script ทดสอบ interactive

---

## ✅ ไม่มี Regression

**Baseline Test ยืนยัน**:
```
Run 5 (ก่อนแก้): 8 PASS, 3 SOFT-FAIL, 1 HARD-FAIL
Run 6 (หลังแก้): 10 PASS, 2 SOFT-FAIL, 0 HARD-FAIL
Run 7 (ตรวจสอบ): 10 PASS, 2 SOFT-FAIL, 0 HARD-FAIL
```

**สรุป**: ✅ ไม่มี regression ใดๆ

---

## 🔍 สิ่งที่เรียนรู้

### 1. LLM Behavior
- ตัวอย่างหลากหลาย > instruction เดียว
- Negative examples ("ห้ามตอบ X") ช่วยป้องกัน hallucination
- ตารางอ้างอิงเร็ว (lookup table) ดีกว่าให้ LLM คำนวณ

### 2. RAG Knowledge Management
- เอกสารต้องมี priority ชัดเจน
- Device codes/template codes ต้องมีใน catalog
- Vector DB rebuild ต้องทำงานได้ (deployment safety)

### 3. Conversation Management
- One-shot API ไม่เหมาะกับ multi-turn conversation
- ต้องมี conversation memory (Frontend หรือ Backend)
- แต่ไม่ส่งผลต่อ single-request use case

---

## 📝 Recommendation

### สำหรับ Conversation Memory:

**Option 1: Frontend State Management (แนะนำสำหรับ MVP)**
- ⏱️ เวลา: 2-4 ชม.
- ✅ Simple
- ✅ ไม่ต้องแก้ backend
- ⚠️ Session หายถ้า refresh

**Option 2: File-Based Session (สำหรับ Production)**
- ⏱️ เวลา: 1 วัน
- ✅ Persistent (ไม่หายแม้ restart)
- ✅ Debug ง่าย (ดูไฟล์ได้)
- ⚠️ Complexity เพิ่ม

---

## ✅ สรุปท้ายสุด

### ความสำเร็จ
- ✅ บรรลุเป้าหมาย test harness (10 PASS, 0 HARD-FAIL)
- ✅ LLM คำนวณเบรกเกอร์ถูกต้อง (25A rule)
- ✅ ไม่มี regression
- ✅ Deployment safety ผ่าน

### ขั้นตอนถัดไป
- [ ] Implement conversation memory (ถ้าต้องการ)
- [ ] เชื่อมต่อ MCP backend
- [ ] ทดสอบ end-to-end (RAG → MCP → AutoLISP)

**ระบบพร้อม deploy และทดสอบ integration กับ MCP!** 🚀
