# Source: 📱MCPtest case.md

```md
สรุปให้ก่อนเลย:  
 ตอนนี้ **MCP core v2 ของท่าน “คำนวณไฟ” ผ่านหมดในฝั่งสูตรกับ pipeline** แต่ **ยังไม่ได้ทดสอบฝั่ง HTTP / error code แบบ 4xx/5xx เลย** เพราะ test ที่เพื่อนเมดรันมันคือ `test_end_to_end.py` ที่ยิง Python ตรง ไม่ใช่ API server เจ้าค่ะนายท่าน

เรื่อง 402 / 501 ตอนนี้ไม่มีหรอก ยังไม่เคยถูกออกแบบเป็นส่วนหนึ่งของ MCP API ตามรัฐธรรมนูญฝั่ง MCP ที่ท่านเขียนไว้เองด้วยซ้ำ  
 ส่วนเอกสาร DB ที่พูดเรื่องโครงสร้าง catalog / integration ก็ยังเน้นชั้นข้อมูล ไม่ยุ่งกับ HTTP code เหมือนกันเจ้าค่ะนายท่าน

เดี๋ยวเมดแบ่งให้เป็น 3 ส่วน:

---

## **1\. อ่านผลที่เพื่อนมึงคายมาถูกมั้ย**

ข้อความชุดนี้:

🎉 Production Integration 100% Complete  
 End-to-End 23/23 ✅  
 Phase 1 Complete 32/33 ✅ 97%  
 Derating / VD / 1-phase / 3-phase ทุกอย่างผ่าน  
 VD อยู่ใต้ 3% หมด ฯลฯ

**แปลให้เป็นภาษาคน:**

* ตอนนี้ MCP core v2:

  * รับ input spec (ที่มาจาก RAG / requirements)

  * ผ่าน `template_resolver → load_calculator → pandapower_adapter → wire_sizer → breaker_selector → conduit_sizer → compliance_checker` เสร็จครบ loop

  * แล้วให้ผลลัพธ์ไฟฟ้าที่ “สมเหตุสมผล” (กระแส, derating, voltage drop ไม่หลุดจากมาตรฐาน) เจ้าค่ะนายท่าน

* Test 23/23 ที่ผ่าน คือ **“test ทางไฟฟ้า” กับ “flow ภายใน pipeline”**:

  * 1 เฟส, 3 เฟส

  * โหลดเล็ก / กลาง / ใหญ่

  * ค่ากระแสตรงสูตร

  * VD ≤ 3%

  * derating factor คูณถูก

  * ไม่ crash, ไม่ error ระหว่าง run

**สิ่งที่ *ยังไม่มี* ในชุดผลลัพธ์นี้:**

* ไม่มีการพูดถึง:

  * `POST /mcp/v2/run`

  * HTTP 4xx / 5xx

  * mapping exception → status code

สรุป:  
 สิ่งที่ท่านเห็นคือ **“ระดับเครื่องยนต์ MCP ทำงานได้จริง \+ ผ่าน test เยอะพอสมควร”**  
 แต่ **ยังไม่มีการออกแบบ/ทดสอบระดับ “บริการ HTTP” ที่ต้องมี 402 / 501 / 422 / 500** ตามที่ท่านถาม เจ้าค่ะนายท่าน

---

## **2\. ควรมี “Fail 402/501” ไหมใน MCP?**

ตอบตรง ๆ แบบวิศวกร:

### **2.1 ตอนนี้: ไม่จำเป็นต้องมี 402/501 ใน MCP core**

* **MCP core v2** ที่ท่านออกแบบในเอกสาร  
   โฟกัสหลักคือ:

   เอา ProjectInputSpec → คำนวณโหลด, สาย, breaker, conduit, ตรวจ VD แล้วคืนผลลัพธ์ \+ LISP  
   ไม่ได้บังคับว่าต้อง map เป็น HTTP code ใดเลยในชั้น core

* รหัสพวกนี้:

  * `402 Payment Required`  
     ปกติใช้ในระบบ billing / quota / subscription  
     → โปรเจกต์นี้ยังไม่มีระบบเก็บตัง ท่านจะใส่ก็ได้ แต่ตอนนี้ไม่มีเรื่องนี้ในรัฐธรรมนูญ MCP เลย

  * `501 Not Implemented`  
     อันนี้ “พอมีเหตุผล” ถ้าท่านอยากแจ้งว่า:

     MCP รองรับเฉพาะ “บ้านพักอาศัย ≤ X kVA”  
     ถ้ามีคนส่งโรงงาน 500 kVA มา → 501

     แต่ ณ ตอนนี้ **ยังไม่มี API layer ที่กำหนดแบบนี้ไว้ชัด ๆ**

**สรุป**:

* ในระดับ core / test ที่มีอยู่ตอนนี้  
   → ไม่ต้องมี 402 / 501 อะไรทั้งนั้น เพราะยังไม่ได้ขึ้นชั้น HTTP

* ถ้าท่านอยากให้มี  
   → ต้องออกแบบ “ชั้น API MCP” แยกจาก core ก่อน แล้วค่อยกำหนดว่า case ไหน \= 422, 400, 501, 503 ฯลฯ เจ้าค่ะนายท่าน

### **2.2 แต่ “ต้องมี test แบบ Error” ไหม?**

**ต้องมี** แต่ไม่จำเป็นต้องใช้เลข 402/501 ใน core

แยกเป็นสองชั้นแบบโปรแกรมเมอร์เก่ง ๆ ทำกัน:

1. **ชั้น MCP core (Python ฟังก์ชัน)**  
    ทดสอบว่า:

   * รับ spec พัง → **raise** exception ที่ตั้งใจ (เช่น `InvalidSpecError`, `CatalogLookupError`)

   * ไม่ปล่อย `KeyError`, `IndexError`, หรือ error งง ๆ หลุดออกมา

   * ไม่ crash เวลาไม่มี device code / room type แปลก ๆ ฯลฯ

2. **ชั้น MCP API (FastAPI / Flask / ฯลฯ)**  
    ตรงนี้ค่อย map:

   * ถ้า `InvalidSpecError` → HTTP 422

   * ถ้า `UnsupportedBuildingTypeError` → HTTP 501 (อันนี้คือที่ท่านพูดถึง)

   * ถ้า DB ล่ม / pandapower พัง → HTTP 500 หรือ 503

ตอนนี้ที่รัน `test_end_to_end.py` คือแบบที่ 1 เท่านั้น  
 ยังไม่มี layer ที่ 2 ให้ทดสอบ HTTP เลย เพราะงั้นไม่มี 402, 501 อะไรโผล่มาเจ้าค่ะนายท่าน

---

## **3\. Test Plan ฝั่ง MCP ที่ “ควรมีจริง ๆ” (แบบใช้ได้เลย)**

เมดสรุป test plan MCP ฝั่ง core \+ API ที่ **เข้ากับสถาปัตยกรรมตอนนี้** ให้เลย ท่านจะเอาไปแปะใน QC ก็ได้เจ้าค่ะนายท่าน

### **3.1 ชุดที่มีอยู่แล้ว (จาก log ที่ท่านให้)**

**กลุ่ม A – Core numeric & pipeline (มีแล้ว):**

* A1: Basic lighting circuit

* A2: HVAC 1-phase with PF

* A3: 3-phase motor

* A4: Multiple loads, multiple circuits

* A5: Derating factors at 30°C, grouping, no insulation

* A6: Voltage drop limits for 300W / 1500W / 3000W

อันนี้คือ “หัวใจ MCP core” และตอนนี้ผ่านหมด → ดีตามมาตรฐานโปรแกรมเมอร์สาย simulation เจ้าค่ะนายท่าน

### **3.2 สิ่งที่ยัง “ขาด” สำหรับ MVP ที่ดูเป็น product จริง**

#### **กลุ่ม B – Input validation & spec correctness**

**B1 – Missing required fields**

* Input: `ProjectInputSpec` ที่ไม่มี rooms / ไม่มี loads / ไม่มี main supply

* **Expected (core)**: raise `InvalidSpecError` พร้อมเหตุผล

* **Expected (API)**: HTTP 422 \+ body บอกว่า field ไหนหาย

---

**B2 – Unsupported building type (ตรงที่ท่านพูดถึง 501\)**

* Input: `building_type = "factory_500kVA"` (ชัด ๆ ว่าเกิน scope บ้านพัก)

* **Expected (core)**: raise `UnsupportedProjectError`

* **Expected (API)**: HTTP 501 (Not Implemented) \+ message ว่า “MCP v2 รองรับเฉพาะ residential LV”

นี่คือจุดที่ “501 มีเหตุผลจะใช้” ถ้าท่านอยากให้มีจริง ๆ เจ้าค่ะนายท่าน

---

**B3 – Invalid catalog reference**

* case: spec ที่ device\_code ไม่มีใน catalog

* **Expected (core)**: `CatalogLookupError`

* **Expected (API)**:

  * ถ้าผิดเพราะ user ส่งชื่อมั่ว → 422

  * ถ้าผิดเพราะ catalog ฝั่ง DB หายทั้ง table → 500 / 503

---

#### **กลุ่ม C – Standards / compliance errors**

**C1 – Voltage drop \> allowed**

* Input: โหลดหนักมาก \+ สายเล็กมาก → VD \> 5%

* **Expected:**

  * pipeline ไม่ crash

  * `compliance_checker` ใส่ flag `vd_ok = false`

  * `McpRunResult` บอกชัดว่า “ไม่ผ่านมาตรฐาน” แต่อาจยังส่งผลลัพธ์กลับมาให้ดู

ไม่จำเป็นต้องเป็น HTTP error ในขั้นแรก แต่ต้อง test ว่า “ตรวจเจอ” ไม่ใช่ปล่อยผ่านเงียบ ๆ เจ้าค่ะนายท่าน

---

**C2 – กระแสเกินสาย / breaker**

* สาย 2.5 mm² แต่ดันได้ 40A

* Expected:

  * wire\_sizer ต้อง upsize หรือ

  * ถ้า upsize แล้วก็ยังไม่พอ → flag non-compliant

  * **ไม่** ให้ได้ผลลัพธ์ที่ claim ว่าถูกต้อง

---

#### **กลุ่ม D – System / runtime error (internal)**

**D1 – Pandapower error**

* ลอง feed network แปลก ๆ ให้ pandapower ล้ม

* Expected:

  * core จับ exception แล้วห่อเป็น `SimulationError`

  * API map → HTTP 500 พร้อม trace\_id

---

**D2 – Catalog DB down (ตอนอนาคตต่อกับ Supabase)**

* Simulate connection error

* Expected:

  * core ไม่ล่มแบบ stacktrace ดิบ ๆ

  * API → 503 (Service Unavailable) ถ้าตาม pattern microservice

---

### **3.3 ว่าด้วยเรื่อง “402 Payment Required”**

ตอนนี้ทั้ง:

* README\_MCP

* MCP DESIGN HANDOVER

* HOW TO Design MCP  
   ไม่มีที่ไหนพูดถึง payment, billing, quota หรือ paywall เลย

**เอาตามหลักสถาปัตยกรรม:**

* 402 ใช้เมื่อ: “เรียก API ได้ แต่ต้องจ่ายตังก่อนถึงจะใช้งานได้เต็ม”

* โปรเจกต์นี้ตอนนี้ \= internal engine / R\&D → **ไม่จำเป็นเลย**

อย่าเพิ่งเอา 402 มาใส่ให้รกสมองตัวเองตอนนี้ดีกว่า  
 เก็บไว้ตอนท่านจะทำ **Amadeus SaaS** แล้วอยากใส่ layer billing ค่อยว่ากันเจ้าค่ะนายท่าน

---

## **4\. ตอบคำถามสุดท้ายแบบสั้น ๆ**

1. “สมควรเข้าใจตามนี้มั้ย”

2. “ต้องมี Fail 402 / 501 มั้ย”

1. **ใช่ ท่านเข้าใจถูกในภาพใหญ่**

   * Pipeline MCP core ทำงานครบ loop

   * มี test end-to-end เลขเยอะพอสมควร

   * ผลตัวอย่าง AC 1500W ที่ท่านแปะ \= ใช้ได้จริงตามหลักไฟฟ้า

2. **ไม่จำเป็นต้องมี 402 ตอนนี้**

   * ยังไม่มีเรื่อง billing ในสถาปัตยกรรม MCP

3. **501 ใช้ได้ “ถ้า” ท่านออกแบบ API MCP ให้ประกาศชัดว่า:**

   * รองรับเฉพาะ residential

   * โรงงาน 500kVA ขึ้นไป \= 501 Not Implemented

   * แปลว่า 501 อยู่ใน test plan **ชั้น API** ไม่ใช่ชั้น core

4. **สิ่งที่ควรทำต่อถ้าจะจริงจังแบบโปรโปรแกรมเมอร์:**

   * แยก test suite MCP core ให้ชัด:

     * numeric / pipeline (ที่มีอยู่แล้ว)

     * validation / compliance / error handling (ที่ยังไม่มีหรือมีน้อย)

   * แล้วค่อยออกแบบ MCP API layer \+ test 4xx/5xx รอบนอกอีกชั้น

ตอนนี้สิ่งที่มีอยู่ฝั่ง MCP core ถือว่า “ตรงแนวทางสายโปรฯ” เลยนะ ไม่มีอะไรป่าเถื่อน แค่ยังไม่ได้หุ้ม error semantics แบบเว็บเซอร์วิสให้ครบเท่านั้นเองเจ้าค่ะนายท่าน


```