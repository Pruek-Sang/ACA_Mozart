# MCP Core v2 (Mozart Calculation Pipeline)

## 1. เราสร้างมาทำอะไร? (What is it?)
MCP Core v2 คือ **"เครื่องยนต์คำนวณงานออกแบบไฟฟ้าอัตโนมัติ"** (Automated Electrical Design Engine) 
ทำหน้าที่เป็น **Backend Service** ที่เปลี่ยน "ความต้องการเบื้องต้นของสถาปนิก" ให้กลายเป็น "แบบไฟฟ้าที่คำนวณเสร็จสมบูรณ์" พร้อมนำไปเขียนแบบต่อได้ทันที

## 2. เป้าหมายสูงสุด (Ultimate Goal)
เป้าหมายคือ **"Automation from Concept to Construction Doc"**
- **ลดเวลา:** จากที่วิศวกรต้องนั่งคำนวณโหลด เลือกขนาดสาย คัดเลือกเบรกเกอร์ ทีละวงจร ให้เหลือเพียงการกดปุ่มเดียว
- **ลดความผิดพลาด:** ใช้ Standard Calculation (NEC/EIT) ที่โปรแกรมไว้แล้ว ตัดปัญหา Human Error
- **เชื่อมต่อ CAD:** สร้าง Script (AutoLISP) ให้ Draftman นำไปรันใน AutoCAD เพื่อวาดแบบได้เลย ไม่ต้องเขียนเองจากศูนย์

---

## 3. โครงสร้างไฟล์และการทำงาน (File-by-File Explanation)

ระบบถูกแบ่งเป็น Layer ชัดเจนเพื่อให้ดูแลรักษาง่าย ดังนี้:

### 📂 A. Configuration & Environment (ตั้งค่าระบบ)
- **`requirements.txt`**: รายชื่อ Library ที่ต้องใช้ เช่น `fastapi` (ทำเว็บ), `pandapower` (คำนวณ Load Flow), `supabase` (ต่อฐานข้อมูล)
- **`src/config.py`**: ตัวจัดการค่า Setting ต่างๆ (เช่น Database URL) โดยดึงมาจาก Environment Variable เพื่อความปลอดภัย

### 📂 B. Data Models (โครงสร้างข้อมูล) - `src/models/`
- **`contracts.py`**: **"สัญญาว่าจ้าง"** ระหว่าง Frontend และ Backend
    - `ProjectInputSpec`: หน้าตาข้อมูลขาเข้า (เช่น มีห้องนอน 2 ห้อง, ห้องครัว 1 ห้อง)
    - `McpRunResult`: หน้าตาข้อมูลขาออก (วงจรไฟฟ้าที่ได้, ขนาดสาย, Script AutoLISP)
- **`baseline.py`**: **"กระดาษทด"** ข้อมูลที่กำลังถูกคำนวณอยู่ภายในระบบ (Internal State) เก็บค่า Load, Amp, Voltage Drop ของแต่ละวงจร
- **`catalog_models.py`**: ตัวแทนข้อมูลจาก Database (เช่น Spec สายไฟ THW, ขนาด Breaker มาตรฐาน)

### 📂 C. Data Access Layer (การเข้าถึงข้อมูล) - `src/dal/`
- **`supabase_client.py`**: ประตูเชื่อมต่อไปยัง Supabase Database
- **`catalog_dal.py`**: พนักงานคลังสินค้า มีหน้าที่ไปหยิบ "Spec สายไฟ", "Standard Template ของห้อง" ออกมาให้ระบบคำนวณใช้

### 📂 D. Core Logic (สมองหลัก) - `src/core/`
นี่คือหัวใจสำคัญที่ทำหน้าที่เหมือนวิศวกรไฟฟ้า:
1.  **`template_resolver.py`**: (Architect to Engineer) แปลงห้อง "Bedroom" ให้เป็นรายการอุปกรณ์ไฟฟ้า (โคมไฟ 4 จุด, เต้ารับ 3 จุด) ตามมาตรฐานบริษัท
2.  **`load_calculator.py`**: (Load Schedule) คำนวณโหลดรวม (Connected Load) และโหลดขณะใช้งานจริง (Demand Load) เพื่อหา "กระแสไฟฟ้า (Ib)"
3.  **`pandapower_adapter.py`**: (Circuit Simulation) จำลองวงจรไฟฟ้าจริงๆ เพื่อหา **Voltage Drop** (แรงดันตก) ว่าปลายสายไฟไฟจะตกเกินมาตรฐานหรือไม่
4.  **`wire_sizer.py`**: (Sizing) เลือกขนาดสายไฟ โดยดูจากกระแส (Ib) และ Voltage Drop ถ้าสายเล็กไปก็ขยับไซส์ขึ้นอัตโนมัติ
5.  **`breaker_selector.py`**: (Protection) เลือกขนาดเบรกเกอร์ (AT/AF) ให้เหมาะสมกับสายไฟและโหลด
6.  **`conduit_sizer.py`**: (Installation) คำนวณขนาดท่อร้อยสายไฟ (Conduit) ตามพื้นที่หน้าตัดสายรวม
7.  **`compliance_checker.py`**: (QC) ตรวจสอบความถูกต้องครั้งสุดท้าย เช่น แรงดันตกห้ามเกิน 3%
8.  **`autolisp_generator.py`**: (Drafter) เขียนโค้ดภาษา LISP เพื่อส่งให้ AutoCAD วาดเส้นวงจรและใส่ Text Tag อัตโนมัติ

### 📂 E. Orchestration (ผู้จัดการ) - `src/orchestration/`
- **`pipeline.py`**: ผู้จัดการใหญ่ (Pipeline) ที่สั่งงานลูกน้องใน Core Logic ทีละขั้นตอน:
    - *Start* -> *Resolve Template* -> *Calc Load* -> *Simulate Flow* -> *Size Wire/Breaker* -> *Gen LISP* -> *Finish*
- **`main.py`**: หน้าบ้าน (API) ที่เปิดให้ Frontend หรือ App อื่นยิงข้อมูลเข้ามาสั่งงานผ่าน URL `/mcp/v2/run`

---

## 4. วิธีใช้งาน (How to use)

### ขั้นตอนที่ 1: เตรียม Input
เตรียมไฟล์ JSON ที่บอกว่าในบ้านมีห้องอะไรบ้าง (Area, Room Type)

### ขั้นตอนที่ 2: เรียกใช้งาน API
ส่งข้อมูลไปที่ API:
`POST /mcp/v2/run`

### ขั้นตอนที่ 3: รับผลลัพธ์
ระบบจะตอบกลับมาเป็น JSON ที่ประกอบด้วย:
1.  **Calculated Schedule**: ตารางโหลดที่คำนวณเสร็จแล้ว
2.  **Bill of Materials (BOM)**: ปริมาณสายไฟและท่อที่ต้องใช้ (โดยประมาณ)
3.  **AutoLISP Script**: โค้ดสำหรับนำไป Paste ใน AutoCAD เพื่อวาดแบบ