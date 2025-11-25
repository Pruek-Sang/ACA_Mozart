### **📄 MCP DESIGN HANDOVER DOCUMENT**

**Mozart Electrical MCP Core v2 – Spec & Responsibilities**

---

#### **0\. เป้าหมายของระบบ**

ออกแบบ “MCP Core” สำหรับระบบออกแบบไฟฟ้า (Mozart) ที่มีหน้าที่:

1. รับข้อมูลโครงสร้างงานออกแบบ (`ProjectInputSpec`) จากฝั่ง RAG/Copilot

2. ใช้ข้อมูลจาก `amadeus.catalog` ใน Supabase เป็นแหล่งความรู้เดียวของ

   * catalog อุปกรณ์

   * กฎ/มาตรฐาน

   * template ห้อง/วงจร

3. ใช้เครื่องคำนวณ (เช่น pandapower) ทำการคำนวณทางไฟฟ้า (โหลด, แรงดันตก, กระแส ฯลฯ)

4. ทำการเลือกขนาดสาย, เบรกเกอร์, ท่อ, ตรวจมาตรฐาน, และเตรียมข้อมูลสำหรับ layout / AutoLISP

5. ส่งผลลัพธ์ออกมาในรูป `McpRunResult` ที่ service อื่น (UI, AutoCAD macro, Copilot) ใช้งานได้ทันที

---

### **1\. บทบาทของแต่ละฝั่ง (Who does what)**

#### **1.1 Mozart Copilot \+ RAG Layer**

* เป็น “หน้าบ้าน” ที่คุยกับผู้ใช้/วิศวกร

* มี abstraction เป็น “Mozart Copilot” ตัวเดียว แต่ภายในอาจใช้ provider ต่างกัน:

  * RAG–Google (ผ่าน Google AI / Gemini SDK)

  * RAG–Local (LLM \+ vector DB ในเครื่อง)

**หน้าที่หลักของ RAG/Copilot**

1. รับ requirement ภาษาคน

   * เช่น “บ้าน 2 ชั้น 3 ห้องนอน 2 ห้องน้ำ 32 ตร.ม. ต่อชั้น ต้องการแยกวงจรครัว”

2. ถามคำถามเพิ่มจนเก็บ requirement ได้ครบ

3. ใช้ knowledge base (guideline, CATALOG\_CONTRACT, ตัวอย่าง input) เพื่อแปลง requirement

   * → `ProjectRequirements`

   * → `ProjectInputSpec` (ผ่าน endpoint `/mcp_spec` ใน service RAG)

4. เรียก MCP Core ผ่าน HTTP API เช่น `/mcp/v2/run` พร้อมส่ง `ProjectInputSpec` แบบ JSON

**สิ่งที่ RAG/Copilot “ไม่ทำ”**

* ไม่คำนวณโหลด, ไม่เลือกสาย/เบรกเกอร์, ไม่ตัดสินมาตรฐาน

* ไม่อ่าน/เขียน `amadeus.catalog` โดยตรง (ใช้แค่เอกสาร/สรุปใน RAG)

#### **1.2 MCP Core**

* เป็น “สมองวิศวกรรม” ที่ deterministic

* ไม่ใช้ LLM ภายใน

* อ่านข้อมูลจาก `amadeus.catalog` ผ่าน DAL (Data Access Layer) เท่านั้น

**หน้าที่**

1. รับ `ProjectInputSpec`

2. สร้าง “BaselineContext” โดยอิง template จาก `amadeus.catalog`

3. สร้างและรัน model pandapower (ถ้าเปิดใช้)

4. ทำการคำนวณและเลือกอุปกรณ์ผ่านโมดูลย่อย

5. รวมผลเป็น `McpRunResult`

6. บันทึกผล (option) ลง DB (`design_session` / `project_result`)

#### **1.3 Pandapower Adapter**

* อยู่ “ในฝั่ง MCP” ไม่ใช่ service แยก

* ทำหน้าที่:

  * สร้าง pandapower net จาก BaselineContext

  * รัน power flow (ระยะเริ่มต้น: load flow)

  * คืนผลลัพธ์ I/V/loading/VD กลับเข้าบริบทให้ MCP Modules ใช้

---

### **2\. ข้อมูลและที่อยู่ของข้อมูล (Where is data)**

#### **2.1 amadeus.catalog (Supabase)**

**เป็นแหล่งความรู้ถาวร (authoritative knowledge)**:

* catalog อุปกรณ์

  * สายไฟ, เบรกเกอร์, ท่อ, อุปกรณ์ปลายทาง ฯลฯ

* template ห้อง

  * ROOM\_TEMPLATE

* template วงจร

  * CIRCUIT\_TEMPLATE

* กฎการจัดวาง

  * PLACEMENT\_RULE

* กฎ geometry

  * GEOMETRY\_FILTER

* กฎตรวจมาตรฐาน

  * VALIDATION\_RULE

* factor อื่น ๆ เช่น derating, demand factor ฯลฯ

เข้าถึงผ่าน view เช่น:

* `amadeus.v_components`

* `amadeus.v_cable_specs`

* `amadeus.v_circuit_templates`

* `amadeus.v_room_templates`

* `amadeus.v_placement_rules`

* `amadeus.v_geometry_filters`

* `amadeus.v_validation_rules`

* ฯลฯ

**ข้อบังคับสำคัญ**

MCP Core ห้ามมี Catalog ของตัวเองในไฟล์ YAML/JSON แยกที่ขัดกับ `amadeus.catalog`

สิ่งที่อนุญาตในโค้ด MCP:

* ค่าคงที่พื้นฐานของฟิสิกส์/ระบบ เช่น 230/400 V, √3, etc.

* config สำหรับ logging / debug ที่ไม่ใช่ spec วิศวกรรม

สิ่งที่ไม่อนุญาต:

* รายการสาย/เบรกเกอร์/กฎมาตรฐานซ้ำในไฟล์โค้ด

* default ห้อง/วงจร ที่ไม่มาจาก `amadeus.catalog`

#### **2.2 ตาราง state runtime (เช่น design\_session)**

**เป็นแหล่งเก็บ “สถานะงานแต่ละโปรเจกต์” (ไม่ใช่ความรู้ถาวร)**:

ตัวอย่างโครงสร้าง `design_session`:

* session\_id (UUID)

* project\_name

* project\_input\_json (ProjectInputSpec)

* baseline\_context\_json

* mcp\_result\_json

* status (e.g. PENDING, RUNNING, COMPLETED, FAILED)

* created\_at, updated\_at

ใช้สำหรับ:

* debug

* replay

* audit

* ขยายในอนาคตเป็นคิว job

ไม่เกี่ยวกับ catalog, ไม่แทนที่ `amadeus.catalog`

---

### **3\. Contract ของ MCP**

#### **3.1 Input: ProjectInputSpec**

* เป็น schema กลางที่มาจาก service RAG (`/mcp_spec`)

* ข้อมูลรวม:

  * project\_info

  * electrical\_system (voltage, phase, earthing, etc.)

  * rooms: List\[RoomSpec\]

  * loads: List\[LoadSpec\]

  * constraints: List\[str\]

เมื่อ MCP ได้รับ ProjectInputSpec:

* ไม่ใช้ raw ตรง ๆ ทันที

* ส่งเข้า `TemplateResolver` ก่อน

#### **3.2 BaselineContext (หลัง TemplateResolver)**

TemplateResolver จะทำ:

1. เติมค่าที่ขาดจาก `amadeus.catalog` เช่น

   * room area default

   * typical appliance per room

   * default circuit template

2. map ห้อง/โหลดให้เข้ากับ template ที่ชัดเจน

3. ทำ flag ว่า field ใดมาจาก “มาตรฐานระบบ” vs “override จากผู้ใช้/หน้างาน”

BaselineContext นี้จะถูกใช้ในทุก MCP module ต่อไป

#### **3.3 Output: McpRunResult**

MCP Core ต้องคืนผลในโครงสร้างที่ชัดเจน เช่น:

* project\_summary

* per\_circuit:

  * load, I, wire size, breaker size, conduit size, VD, loading%

* per\_room:

  * summary load, number of outlets, etc.

* violations:

  * รายการข้อผิดตาม VALIDATION\_RULE

* layout\_summary (optional):

  * ตำแหน่งจุด, ความยาวสาย

* artifacts:

  * AutoLISP script text / path to file

  * รายงาน PDF/JSON อื่น ๆ

---

### **4\. โมดูลย่อยใน MCP Core**

แต่ละโมดูลต้อง:

* รับ BaselineContext (หรือส่วนที่เกี่ยวข้อง)

* อ่านข้อมูลที่ต้องใช้จาก `amadeus.catalog` ผ่าน DAL

* คืนผลที่ deterministic และตรวจสอบซ้ำได้

#### **4.1 TemplateResolver**

หน้าที่:

* แปลง ProjectInputSpec → BaselineContext

* เติมค่า default จาก ROOM\_TEMPLATE, CIRCUIT\_TEMPLATE, COMPONENT/CATALOG

* แยก standard vs override

#### **4.2 LoadCalculator**

หน้าที่:

* คำนวณโหลดต่อวงจร/ต่อห้อง

* ใช้:

  * APPLIANCE, ROOM\_TEMPLATE, demand factor, diversity factor จาก catalog

* คืนผล:

  * P, I, category ต่อวงจร

#### **4.3 WireSizer**

หน้าที่:

* เลือกขนาดสายจากสายใน `v_cable_specs`

* ใช้ I จาก load / pandapower (ถ้ามี) \+ derating factor

* ใช้ rule จาก VALIDATION\_RULE เช่น

  * max VD

  * min CSA main feeder

#### **4.4 BreakerSelector**

หน้าที่:

* เลือก breaker rating, type, model จาก breaker catalog

* ใช้ rule: 125% general, 175% motor, min breaking capacity ฯลฯ

#### **4.5 ConduitSizer**

หน้าที่:

* เลือกขนาดท่อจากจำนวนเส้น, ขนาดสาย, rule การเติมพื้นที่ท่อ (%)

#### **4.6 CostEstimator (MVP ใช้ราคา static)**

หน้าที่:

* ประเมินราคาเบื้องต้นจาก cost ที่อยู่ใน catalog

* ไม่ต้อง real-time ราคาจากร้านค้าภายนอกในเฟสแรก

#### **4.7 ComplianceChecker**

หน้าที่:

* ตรวจตาม VALIDATION\_RULE ทั้งหมดที่ apply กับโปรเจกต์นั้น

* เช่น VD limit, loading limit, จำนวนจุดต่อตารางเมตร, กฎเฉพาะห้องน้ำ/ครัว

#### **4.8 LayoutOptimizer \+ AutoLISP Generator**

หน้าที่ LayoutOptimizer:

* ใช้ geometry \+ GEOMETRY\_FILTER \+ PLACEMENT\_RULE

* วางจุด (outlet, switch, light) และสายแบบ simplified

หน้าที่ AutoLISP Generator:

* แปลงผล layout เป็นสคริปต์ AutoLISP ที่ AutoCAD ใช้สร้างแปลน

---

### **5\. การไหลของข้อมูล (End-to-end Flow)**

1. User → Mozart Copilot

2. Copilot (RAG provider: Google SDK หรือ local)

   * รวบรวม requirement

   * เรียก `/mcp_spec` → ได้ `ProjectInputSpec`

3. Copilot เรียก MCP `/mcp/v2/run`

   * body \= ProjectInputSpec

4. MCP Core

   * TemplateResolver → BaselineContext

   * PandapowerAdapter (optional phase 1 / base)

   * MCP Modules → McpRunResult

   * (option) save McpRunResult ลง `design_session`

5. MCP Core คืน McpRunResult ให้ Copilot

6. Copilot แสดงผล, สร้างรายงาน, แนบ AutoLISP ให้ผู้ใช้

