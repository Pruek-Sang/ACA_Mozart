# 🚀 Go to Countrywide: Roadmap สู่มาตรฐานระดับประเทศ

เอกสารนี้รวบรวม "Gap Analysis" และ "Action Plan" เพื่อยกระดับ **ACA Mozart** จากระบบออกแบบเบื้องต้น ให้กลายเป็น **"วิศวกรไฟฟ้า AI ระดับประเทศ"** ที่สามารถออกรายการคำนวณประกอบแบบ (Calculation Sheet) เพื่อยื่นขออนุญาตหรือ Sign แบบได้อย่างมั่นใจ 100%

---

## 🏗️ 1. สถานะปัจจุบัน (Current Status)
*   **ระดับความเก่ง:** 👨‍🔧 ช่างไฟมือโปร / วิศวกรจบใหม่
*   **จุดแข็ง:** เลือกขนาดมิเตอร์, จัดกลุ่มวงจร (Circuit Grouping), และเลือกขนาดสายย่อย (Branch Circuit) ได้ถูกต้องตามมาตรฐาน วสท.
*   **จุดอ่อน:** ยังใช้ "ค่าเฉลี่ย" หรือ "ตารางสำเร็จรูป" ในจุดวิกฤตที่ต้องคำนวณละเอียด (โดยเฉพาะสายเมน)

---

## 🔍 2. สิ่งที่ขาด (Missing Items) & ทำไมต้องแก้ (Gap Analysis)

### Gap 1 🔴: การคำนวณแรงดันตกสายเมน (Service Entrance Voltage Drop)
*   **อาการ:** ใช้ Lookup Table (เช่น Main 100A = สาย 35 sq.mm เสมอ) ไม่สนว่าหม้อแปลงอยู่ห่าง 10 เมตร หรือ 200 เมตร
*   **ทำไมต้องแก้:** 
    *   ถ้าระยะเกิน 50-100 เมตร สาย 35 sq.mm ไฟจะตกเกิน 2% ทำให้ไฟในบ้านกระพริบ แอร์ตัด หรืออุปกรณ์พัง
    *   มาตรฐาน วสท. บังคับว่า VD รวมต้องไม่เกิน 5% (เมน + ย่อย)
*   **ความรุนแรง:** 🚨 **CRITICAL** (สำหรับงานจริง)

### Gap 2 🟠: การรับค่าระยะสายย่อย (Branch Circuit Distance Input)
*   **อาการ:** ระบบสมมติว่าทุกวงจรเดินสายไกล 30 เมตร (100 ft) เท่ากันหมด
*   **ทำไมต้องแก้:**
    *   บ้านจริงมีห้องใกล้/ไกล ห้องไกล 15 เมตร กับ 30 เมตร ควรใช้สายต่างขนาดกันในบางกรณี (Load สูงๆ)
    *   เพื่อให้รายการคำนวณ (Calculation Sheet) สะท้อนความจริงระดับ "ห้องต่อห้อง"
*   **ความรุนแรง:** ⚠️ **MODERATE** (มาตรฐานยอมรับค่าเฉลี่ยได้ แต่ถ้าอยาก "เป๊ะ" ต้องแก้)

### Gap 3 🟡: โครงสร้างข้อมูลไม่รองรับฟิสิกส์จริง (Data Model Barriers)
*   **อาการ:** `ElectricalLoad` Model ไม่มีช่องเก็บค่า `distance` หรือ `feeder_distance`
*   **ทำไมต้องแก้:** ถ้าไม่มีที่เก็บข้อมูล ต่อให้ User พิมพ์มา AI ก็โยนทิ้ง ไม่รู้จะส่งไปคำนวณยังไง
*   **ความรุนแรง:** ⚙️ **FOUNDATION** (ต้องแก้ก่อนเพื่อน)

---

## 🛠️ 3. วิธีแก้ไข (Resolution Plan)

### Phase 1: 🧱 ปูพื้นฐาน (Foundation Upgrade)
*   [ ] **1.1 Update Model:** แก้ไฟล์ `models/contracts.py` เพิ่ม field:
    *   `DesignRequest.service_distance_m` (ระยะสายเมน)
    *   `ElectricalLoad.branch_distance_m` (ระยะสายย่อยจากตู้)
*   [ ] **1.2 Pipeline Update:** แก้ `pipeline.py` ให้ส่งค่าเหล่านี้ไปที่ module คำนวณ

### Phase 2: 🧠 เพิ่มความฉลาดให้ AI (RAG Upgrade)
*   [ ] **2.1 Extract Service Distance:** อัพเกรด Prompt ให้แกะ "ระยะหม้อแปลง" ใส่ตัวแปร `service_distance_m`
*   [ ] **2.2 Extract Branch Distance:** อัพเกรด Prompt ให้แกะ "ระยะห้อง" (ถ้ามี) เช่น "ห้องครัวอยู่หลังบ้าน ไกล 20 เมตร" ใส่ `branch_distance_m`
*   [ ] **2.3 Auto-Estimate:** สร้าง Logic "เดา" ระยะห้องตามขนาดบ้าน ถ้า User ไม่บอก (เช่น บ้าน 2 ชั้น -> ชั้น 2 ไกลเฉลี่ย 15m)

### Phase 3: ⚙️ เครื่องจักรคำนวณฟิสิกส์ (Core Engine Upgrade)
*   [ ] **3.1 Real Service VD Calc:** 
    *   เขียนฟังก์ชันใหม่ใน `wire_sizer.py` เพื่อคำนวณสายเมน
    *   Logic: `Loop` เริ่มจากสายมาตรฐาน -> เช็ค VD -> ถ้าไม่ผ่าน -> ขยับ Size -> เช็คใหม่
*   [ ] **3.2 Dynamic Branch VD:**
    *   เปลี่ยนค่า Hardcode `100 ft` เป็น `load.branch_distance_m`

---

### 🆕 Phase 0: 📊 Output Formatter (แสดง VD% ในตาราง)
*   [ ] **0.1 Show VD in Load Schedule:** แก้ไข `_format_design_result_as_text()` ใน `service.py` ให้แสดง VD% ต่อวงจร
*   [ ] **0.2 Show Service VD:** เพิ่มบรรทัดใน SERVICE ENTRANCE section แสดง VD ของสายเมน

### 🆕 Phase 2.4: 📏 Default Distance Table
*   [ ] **2.4 Auto-Estimate Table:** สร้างตาราง default ระยะตามประเภทบ้าน
    ```
    บ้านเดี่ยว 1 ชั้น: ชั้น 1 = 15m (avg)
    บ้านเดี่ยว 2 ชั้น: ชั้น 1 = 15m, ชั้น 2 = 25m
    บ้านเดี่ยว 3 ชั้น: ชั้น 1 = 15m, ชั้น 2 = 25m, ชั้น 3 = 35m
    ทาวน์เฮ้าส์: ชั้น 1 = 10m, ชั้น 2 = 18m
    ```

### 🆕 Phase 3.3: 🔗 Cable Derating Chain
*   [ ] **3.3 Derating → VD Chain:** เพิ่ม logic: ถ้าสายต้อง Derate เพิ่มขึ้น → VD จะยิ่งสูง → ต้องขยับ Size อีก

### 🆕 Phase 4: 🧪 Testing & Verification
*   [ ] **4.1 Unit Test:** เพิ่ม test case ใน `Test_MCP/test_pipeline.py` สำหรับ VD calculation
*   [ ] **4.2 E2E Test:** เพิ่ม test case ใน `test_extreme_case.py` สำหรับ Extreme Distance (200m)
*   [ ] **4.3 Regression Test:** ตรวจสอบว่า Output เดิมไม่เปลี่ยน (ถ้าไม่ได้ระบุระยะ)

---

## 🔍 5. Code Analysis Summary (Sophia's Findings)

| ไฟล์ | บรรทัด | สิ่งที่พบ |
|------|--------|----------|
| `models/contracts.py` | 49-60 | `ElectricalLoad` ไม่มี `distance` field |
| `wire_sizer.py` | 63-183 | `size_wire_with_voltage_drop()` มีอยู่แล้ว รับ `distance_feet` |
| `pipeline.py` | 275 | ❌ **Hardcoded** `distance_feet = 100` |
| `service.py` | 540-678 | Extraction prompt ไม่มีคำถามเรื่องระยะ |

---

## ✅ 6. ตัวอย่างความสำเร็จ (Definition of Done)

เมื่อทำครบ ระบบจะสามารถตอบแบบนี้ได้:

> **User:** "ขอไฟเมน 100A ระยะหม้อแปลง 150 เมตร ห้องน้ำชั้น 2 ไกล 20 เมตร"

> **System Response:**
> "เนื่องจากระยะหม้อแปลงไกลมาก (150m) ทำให้เกิดแรงดันตกสูง...
> ระบบจึง **อัพเกรดสายเมนจาก 35 sq.mm เป็น 70 sq.mm** เพื่อให้ไฟไม่ตก (VD < 1.5%) ✅
>
> ส่วนห้องน้ำชั้น 2 ระยะ 20m ใช้สาย 2.5 sq.mm ได้ปกติ (VD 0.8%) ✅"

---

### 📝 หมายเหตุ
ไฟล์นี้ถูกสร้างขึ้นเพื่อเป็นแผนแม่บท (Master Plan) ในการพัฒนาสู่ระดับ Countrywide Standard 
เก็บไว้ที่: `QC_ACA/Go_to_Countrywide_🚀.md`
