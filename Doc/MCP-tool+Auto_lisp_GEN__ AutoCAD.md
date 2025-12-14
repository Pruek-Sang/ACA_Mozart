# Source: 📐 ข้อมูลเพิ่มเติม_ AutoCAD สำหรับงานออกแบบบ้านพักอาศัย.md

```md
# **📐 ข้อมูลเพิ่มเติม: AutoCAD สำหรับงานออกแบบบ้านพักอาศัย**

## **🎯 ส่วนที่เกี่ยวข้องโดยตรงกับ AutoCAD \+ คำแนะนำเพิ่มเติม**

---

## **1\. มาตรฐาน AutoCAD Drawing สำหรับบ้านพักอาศัย**

## **1.1 Layer Standards (มาตรฐาน Layer ที่ต้องมี)**

**หลักการ:** ใช้ระบบ **AIA (American Institute of Architects)** หรือ **ISO 13567** แต่ปรับให้เข้ากับไทย

**Layer Naming Convention:**

text  
`[ชั้น]-[ระบบ]-[ประเภท]-[สถานะ]`

`ตัวอย่าง:`  
`A-WALL-FULL     = สถาปัตย์ - กำแพงทึบ`  
`A-DOOR-SWING    = สถาปัตย์ - ประตูบาน`  
`A-WIND-FIX      = สถาปัตย์ - หน้าต่างบานตาย`  
`S-BEAM-CONC     = โครงสร้าง - คานคอนกรีต`  
`S-COLU-RECT     = โครงสร้าง - เสาสี่เหลี่ยม`  
`E-LITE-CEIL     = ไฟฟ้า - โคมไฟเพดาน`  
`E-POWR-RECEP    = ไฟฟ้า - เต้ารับปลั๊ก`  
`E-SWIT-WALL     = ไฟฟ้า - สวิตช์`  
`E-WIRE-COND     = ไฟฟ้า - ท่อร้อยสาย`  
`P-WATR-SUPP     = ประปา - ท่อน้ำดี`  
`P-SANI-DRAN     = สุขาภิบาล - ท่อระบายน้ำ`

**Layer สำหรับงานไฟฟ้าบ้านพัก (ต้องมี):**

text  
`E-GRID          = เส้นกริด/แกน`  
`E-DIME          = เส้นขนาดและบอกระยะ`  
`E-TEXT          = ข้อความ/คำอธิบาย`  
`E-SYMB          = สัญลักษณ์อุปกรณ์ไฟฟ้า`  
`E-LITE-CEIL     = โคมไฟเพดาน`  
`E-LITE-WALL     = โคมไฟผนัง`  
`E-POWR-RECEP    = เต้ารับปลั๊กทั่วไป`  
`E-POWR-SPEC     = เต้ารับพิเศษ (แอร์/เตา)`  
`E-SWIT-SNGL     = สวิตช์เดี่ยว`  
`E-SWIT-MULT     = สวิตช์หลายทาง`  
`E-WIRE-COND     = ท่อร้อยสายไฟ`  
`E-WIRE-TRAY     = รางเดินสาย`  
`E-PNLB-MDB      = ตู้ MDB/Sub-DB`  
`E-CIRC-LINE     = เส้นแสดงวงจร`  
`E-EQPM          = อุปกรณ์พิเศษ (UPS/Generator)`  
`E-GRND          = ระบบลงดิน`  
`E-NOTE          = หมายเหตุและรายละเอียด`

**Color Standards (มาตรฐานสี):**

text  
`Layer E-WALL-*     = Color 8 (เทาเข้ม) - กำแพงอ้างอิง`  
`Layer E-LITE-*     = Color 3 (เขียว) - ระบบแสงสว่าง`  
`Layer E-POWR-*     = Color 1 (แดง) - ระบบปลั๏ก`  
`Layer E-SWIT-*     = Color 4 (ฟ้าอ่อน) - สวิตช์`  
`Layer E-WIRE-*     = Color 6 (ม่วง) - ท่อและสาย`  
`Layer E-PNLB-*     = Color 2 (เหลือง) - ตู้ไฟ`  
`Layer E-TEXT       = Color 7 (ขาว/ดำ) - ข้อความ`  
`Layer E-DIME       = Color 5 (น้ำเงิน) - ขนาด`

**Line Weight Standards:**

text  
`กำแพง/โครงสร้าง = 0.50 mm`  
`เส้นวงจรหลัก = 0.35 mm`  
`เส้นวงจรย่อย = 0.25 mm`  
`เส้นอ้างอิง = 0.18 mm`  
`ข้อความ = 0.13 mm`

---

## **1.2 Drawing Set ที่ต้องส่งมอบ (AutoCAD Files)**

**ชุดแบบออกแบบบ้าน 2 ชั้น ครบชุด:**

## **A. งานสถาปัตยกรรม (Architectural Drawings)**

text  
`A-000   = Cover Sheet + Index`  
`A-001   = Site Plan (แปลนที่ตั้ง + ระยะร่น)`  
`A-101   = Floor Plan - ชั้น 1`  
`A-102   = Floor Plan - ชั้น 2`  
`A-103   = Floor Plan - หลังคา`  
`A-201   = Elevations (รูปด้าน 4 ด้าน)`  
`A-301   = Sections (รูปตัด A-A, B-B)`  
`A-401   = Door/Window Schedule + Details`  
`A-501   = Stair Details`  
`A-601   = Toilet Details`

## **B. งานโครงสร้าง (Structural Drawings)**

text  
`S-001   = Foundation Plan (แปลนฐานราก)`  
`S-101   = Structural Floor Plan - ชั้น 1`  
`S-102   = Structural Floor Plan - ชั้น 2`  
`S-201   = Beam Schedule + Details`  
`S-301   = Column Schedule + Details`  
`S-401   = Roof Structure Plan`  
`S-501   = Structural Details (รายละเอียดต่อเสริม)`

## **C. งานไฟฟ้า (Electrical Drawings) ← นี่คือส่วนสำคัญสำหรับ Amadeus\!**

text  
`E-000   = Electrical Symbol Legend + Notes`  
`E-001   = Electrical Site Plan (ตำแหน่ง MDB + มิเตอร์)`  
`E-101   = Lighting Plan - ชั้น 1`  
`E-102   = Lighting Plan - ชั้น 2`  
`E-201   = Power Plan - ชั้น 1 (ปลั๊ก + สวิตช์)`  
`E-202   = Power Plan - ชั้น 2`  
`E-301   = Power Riser Diagram (Single Line Diagram)`  
`E-401   = Panel Schedule (รายการตู้ MDB/Sub-DB)`  
`E-501   = Electrical Details (ท่อร้อยสาย/ราง/ลงดิน)`  
`E-601   = Load Calculation Sheet`

## **D. งานสุขาภิบาล (Plumbing/Sanitary)**

text  
`P-101   = Plumbing Plan - ชั้น 1 (น้ำดี + น้ำเสีย)`  
`P-102   = Plumbing Plan - ชั้น 2`  
`P-201   = Sanitary Riser Diagram`  
`P-301   = Water Tank + Septic Tank Details`

---

## **2\. AutoCAD Workflow สำหรับงานไฟฟ้าบ้าน**

## **2.1 ขั้นตอนการทำงาน (ที่ Amadeus ต้องรู้)**

**Phase 1: ได้รับแบบสถาปัตย์ (A-101, A-102)**

1. รับไฟล์ DWG แบบพื้น  
2. ตรวจสอบ:  
   * Scale ถูกต้อง (1:100 หรือ 1:50)  
   * Units \= Meters  
   * กำแพง/ห้อง/ประตู-หน้าต่าง ชัดเจน  
3. **Xref** แบบสถาปัตย์เป็น Underlay (ห้ามแก้ไข\!)

**Phase 2: วาง Layout ไฟฟ้า**

1. สร้าง Layer ตามมาตรฐาน (E-LITE-*, E-POWR-*, E-SWIT-\*)  
2. วางตำแหน่งอุปกรณ์:  
   * โคมไฟ (ดูทิศทางแสง)  
   * ปลั๊ก (ระยะจากพื้น 0.30-0.50 m)  
   * สวิตช์ (สูงจากพื้น 1.30 m)  
   * Air-con outlets (สูง 2.20-2.50 m)  
3. ใส่ Block สัญลักษณ์มาตรฐาน

**Phase 3: คำนวณโหลดและวงจร** ← **Amadeus MCP ทำงานที่นี่\!**

1. นับจำนวนอุปกรณ์แต่ละห้อง  
2. ส่งข้อมูลให้ MCP คำนวณ:  
   * จำนวนวงจร  
   * ขนาดสาย  
   * ขนาด Breaker  
   * แรงดันตก  
3. MCP Return:  
   * Circuit Assignment  
   * Cable sizing  
   * Panel Schedule

**Phase 4: เขียน Single Line Diagram**

1. วาด Riser Diagram จาก MDB → Sub-DB → แต่ละวงจร  
2. ใส่ขนาด Breaker, สาย, ท่อ  
3. แสดงโหลดแต่ละวงจร (VA/A)

**Phase 5: Panel Schedule**

1. สร้างตาราง Panel Schedule  
2. แสดง:  
   * เบอร์วงจร  
   * รายละเอียดวงจร (Lighting/Socket/AC)  
   * โหลด (VA)  
   * Breaker (A)  
   * ขนาดสาย (sq.mm)  
   * ขนาดท่อ (mm)

**Phase 6: Details**

1. Typical Details:  
   * วิธีเดินท่อร้อยสายในฝ้า  
   * วิธีฝังท่อในผนัง/พื้น  
   * การต่อลงดิน  
   * การติดตั้ง MDB

---

## **2.2 Block Library ที่ต้องมี (Dynamic Blocks)**

**สัญลักษณ์ไฟฟ้ามาตรฐาน (ต้อง Standardize\!):**

**โคมไฟ:**

text  
`E-LITE-DOWNLIGHT-9W      = ดาวน์ไลท์ LED 9W`  
`E-LITE-TUBE-18W          = หลอดยาว 18W`  
`E-LITE-PENDANT           = โคมห้อย`  
`E-LITE-WALL-SCONCE       = โคมผนัง`  
`E-LITE-SPOTLIGHT         = สปอตไลท์`  
`E-LITE-EMERGENCY         = ไฟฉุกเฉิน`

**ปลั๊ก:**

text  
`E-RECEP-SINGLE           = ปลั๊กเดี่ยว`  
`E-RECEP-DOUBLE           = ปลั๊กคู่`  
`E-RECEP-TRIPLE           = ปลั๊ก 3 ช่อง`  
`E-RECEP-WP               = ปลั๊กกันน้ำ (Waterproof)`  
`E-RECEP-FLOOR            = ปลั๊กฝังพื้น`  
`E-RECEP-AC               = ปลั๊กแอร์ (20A)`  
`E-RECEP-COOKER           = ปลั๊กเตาไฟฟ้า (32A)`

**สวิตช์:**

text  
`E-SWITCH-1WAY            = สวิตช์ทางเดียว`  
`E-SWITCH-2WAY            = สวิตช์ 2 ทาง`  
`E-SWITCH-3WAY            = สวิตช์ 3 ทาง`  
`E-SWITCH-DIMMER          = สวิตช์ปรับแสง`  
`E-SWITCH-TIMER           = สวิตช์ตั้งเวลา`  
`E-SWITCH-MOTION          = สวิตช์เซนเซอร์`

**ตู้/อุปกรณ์:**

text  
`E-PANEL-MDB              = ตู้ MDB`  
`E-PANEL-SUBDB            = ตู้ Sub-DB`  
`E-PANEL-METER            = ตู้มิเตอร์`  
`E-EQPM-DOORBELL          = กระดิ่งบ้าน`  
`E-EQPM-TELEPHONE         = โทรศัพท์`  
`E-EQPM-DATA              = จุดอินเทอร์เน็ต`  
`E-EQPM-CCTV              = กล้องวงจรปิด`

**การต่อเชื่อม:**

text  
`E-WIRE-CONDUIT           = ท่อร้อยสาย`  
`E-WIRE-FLEXIBLE          = ท่ออ่อน`  
`E-WIRE-TRAY              = รางเดินสาย`  
`E-WIRE-UNDERFLOOR        = เดินใต้พื้น`  
`E-WIRE-CONCEALED         = ฝังในผนัง/ฝ้า`

---

## **2.3 Text Styles และ Dimension Styles**

**Text Styles มาตรฐาน:**

text  
`TH-ARIAL-2.5     = ข้อความหัวข้อ (ภาษาไทย Arial 2.5mm)`  
`TH-ARIAL-2.0     = ข้อความทั่วไป (ภาษาไทย Arial 2.0mm)`  
`TH-ARIAL-1.5     = ข้อความย่อย (ภาษาไทย Arial 1.5mm)`  
`EN-ARIAL-2.5     = ข้อความหัวข้อ (English Arial 2.5mm)`  
`EN-ARIAL-2.0     = ข้อความทั่วไป (English Arial 2.0mm)`  
`NOTE-ARIAL-1.2   = หมายเหตุ (Arial 1.2mm)`

**Dimension Styles:**

text  
`DIM-METRIC-100   = มาตราส่วน 1:100 (Arrow 2mm, Text 2mm)`  
`DIM-METRIC-50    = มาตราส่วน 1:50 (Arrow 2.5mm, Text 2.5mm)`  
`DIM-DETAIL       = รายละเอียด (Arrow 3mm, Text 3mm)`

---

## **3\. มาตรฐานการวาง AutoCAD สำหรับงานไฟฟ้า**

## **3.1 ระยะห่างมาตรฐาน**

**ปลั๊ก (Receptacles):**

* **ห้องนั่งเล่น/นอน**: ทุก 3-4 เมตร  
* **ห้องครัว**: ทุก 1.5-2 เมตร (เคาน์เตอร์)  
* **ห้องน้ำ**: อย่างน้อย 1 จุด (ใกล้กระจก)  
* **ระยะจากพื้น**: 0.30-0.50 m (ทั่วไป), 1.00 m (เคาน์เตอร์)  
* **ระยะจากมุมห้อง**: ≤ 1.80 m

**สวิตช์ (Switches):**

* **ระยะจากพื้น**: 1.30 m (มาตรฐาน)  
* **ระยะจากกรอบประตู**: 0.15-0.20 m  
* **ห้องนอน**: ข้างเตียง \+ ประตูเข้า (2-way switch)  
* **บันได**: บนและล่าง (3-way switch)

**โคมไฟ (Lighting):**

* **ดาวน์ไลท์ในห้องนั่งเล่น**: ทุก 1.5-2.0 m  
* **โคมไฟห้องครัว**: เหนือเคาน์เตอร์ ทุก 1.0-1.5 m  
* **โคมไฟห้องน้ำ**: กลางห้อง \+ เหนือกระจก  
* **โคมไฟบันได**: ทุกชั้น \+ ระหว่างชั้น

---

## **3.2 ข้อควรระวังเมื่อวาง Layout**

**DO (ควรทำ):**

* ✅ วาง Xref แบบสถาปัตย์ก่อนเริ่มงาน  
* ✅ ใช้ Layer ตามมาตรฐาน (อย่าสร้าง Layer เอง\!)  
* ✅ ใส่ Attributes ใน Block (ชื่อ, กำลัง, ขนาด)  
* ✅ วาดเส้นวงจรด้วย Polyline (แก้ไขง่าย)  
* ✅ ใส่ Text หมายเลขวงจรข้างอุปกรณ์  
* ✅ ทำ Panel Schedule เป็น Table (ไม่ใช่รูปภาพ\!)  
* ✅ Plot ออกมาทดสอบก่อนส่งมอบ

**DON'T (ห้ามทำ):**

* ❌ ห้ามแก้ไข Xref แบบสถาปัตย์  
* ❌ ห้ามใช้ Layer 0 วาดอะไรก็ตาม  
* ❌ ห้ามใช้สี ByBlock หรือ ByLayer ผิด  
* ❌ ห้ามวางปลั๊กหลังประตู/บานหน้าต่าง  
* ❌ ห้ามวางสวิตช์ในห้องน้ำ (ใช้สวิตช์กันน้ำนอกห้อง)  
* ❌ ห้ามให้สายไฟตัดผ่านห้องน้ำ (เสี่ยงชื้น)  
* ❌ ห้ามใส่โหลดหนักหลายตัวในวงจรเดียว

---

## **4\. Integration: Amadeus → AutoCAD Workflow**

## **4.1 Input: Amadeus MCP → AutoCAD**

**MCP Output ที่ต้องส่งให้ AutoCAD:**

json  
`{`  
  `"project_name": "บ้านคุณสมชาย",`  
  `"circuits": [`  
    `{`  
      `"circuit_id": "C01",`  
      `"circuit_name": "Lighting - Living Room",`  
      `"loads": [`  
        `{"type": "LED_9W", "qty": 6, "location": "living_room"}`  
      `],`  
      `"total_load_va": 540,`  
      `"breaker_size": "10A",`  
      `"cable_size": "2.5 sq.mm",`  
      `"conduit_size": "16 mm"`  
    `}`  
  `],`  
  `"panel_schedule": {...},`  
  `"cable_routing": [`  
    `{`  
      `"from": "MDB",`  
      `"to": "Living Room Switch",`  
      `"cable": "2.5 sq.mm x 3C",`  
      `"conduit": "16mm PVC",`  
      `"length": 15.5`  
    `}`  
  `]`  
`}`

**AutoCAD ต้องทำ:**

1. อ่าน JSON จาก MCP  
2. วาง Block ตามตำแหน่ง `loads[].location`  
3. สร้าง Polyline เชื่อม `cable_routing[]`  
4. สร้าง Table จาก `panel_schedule`  
5. สร้าง Single Line Diagram จาก `circuits[]`  
6. Export DWG

---

## **4.2 AutoLISP Script Example (Concept)**

**ตัวอย่าง Script วาง Lighting Fixtures:**

lisp  
`(defun C:PLACE-LIGHTS (/ json-data circuits)`  
  `;; Read JSON from MCP`  
  `(setq json-data (read-json "mcp_output.json"))`  
    
  `;; Loop through circuits`  
  `(foreach circuit (get-circuits json-data)`  
    `(foreach load (get-loads circuit)`  
      `;; Insert block`  
      `(command "INSERT"`   
               `(get-block-name (load-type load))`  
               `(get-location load)`  
               `1.0  ;; scale`  
               `0    ;; rotation`  
      `)`  
      `;; Add attributes`  
      `(add-attribute "CIRCUIT" (circuit-id circuit))`  
      `(add-attribute "LOAD" (load-power load))`  
    `)`  
  `)`  
    
  `;; Create circuit lines`  
  `(draw-circuit-lines circuits)`  
    
  `(princ "\nLights placed successfully!")`  
`)`

---

## **5\. คำแนะนำเพิ่มเติมสำหรับ Freelancer**

## **5.1 Deliverables Checklist**

**ไฟล์ที่ต้องส่งมอบ:**

* DWG Files แยกตาม Discipline (A-, S-, E-, P-)  
* PDF Set (Plot มาตราส่วน 1:100, 1:50)  
* Layer State Saved (แยก Layer สำหรับ Plot)  
* Block Library (Custom blocks ที่ใช้)  
* Template Files (.DWT)  
* Plot Style Table (.CTB)  
* Font Files (ถ้าใช้ font พิเศษ)  
* Xref Files (แบบสถาปัตย์/โครงสร้าง)

---

## **5.2 Quality Control**

**ก่อนส่งมอบ ต้องเช็ค:**

* **Audit** ไฟล์ (Purge \+ Audit \+ Recover)  
* **Layer** ถูกต้องตามมาตรฐาน  
* **Text** อ่านชัดเจน ไม่เบลอ  
* **Dimension** ถูกต้อง มีหน่วย  
* **Block** ไม่มี Duplicate  
* **Xref** Path ถูกต้อง (ใช้ Relative Path)  
* **Plot** ทดสอบแล้ว scale ถูกต้อง  
* **Panel Schedule** ตัวเลขตรงกับ Calculation  
* **Single Line Diagram** ครบทุกวงจร  
* **Load Calculation** แนบเอกสารคำนวณ

---

## **5.3 Common Mistakes (ที่มักพบ)**

**ข้อผิดพลาดที่ Freelancer มักทำ:**

1. ❌ **ใช้ Layer 0 วาดทุกอย่าง** → ไม่สามารถควบคุม Visibility ได้  
2. ❌ **ไม่ Purge ก่อนส่ง** → ไฟล์ใหญ่ ช้า  
3. ❌ **Xref ใช้ Absolute Path** → เปิดไฟล์ที่เครื่องอื่นไม่ได้  
4. ❌ **Panel Schedule ทำเป็นรูป** → แก้ไขยาก ไม่สามารถ Export ข้อมูล  
5. ❌ **Single Line Diagram ไม่ตรงกับแปลน** → สับสน ก่อสร้างผิด  
6. ❌ **ไม่ใส่ Legend สัญลักษณ์** → ช่างงานอ่านไม่ออก  
7. ❌ **ไม่ระบุขนาดสาย/ท่อ** → ช่างเดาเอาเอง  
8. ❌ **Plot Scale ผิด** → แบบไม่ตรงความเป็นจริง

---

## **6\. สรุป: AutoCAD Essentials สำหรับ Amadeus**

## **สิ่งที่ Amadeus ต้องรู้/ทำได้:**

**Input:**

* รับ JSON จาก MCP (circuits, loads, cable sizing, panel schedule)

**Process:**

* แปลง JSON → AutoCAD Commands (AutoLISP/Python)  
* วาง Blocks ตามตำแหน่ง  
* สร้างเส้นวงจร (Polylines)  
* สร้าง Panel Schedule (Table)  
* สร้าง Single Line Diagram

**Output:**

* DWG Files (E-101, E-102, E-301, E-401)  
* PDF Set  
* Layer States  
* Block Library

**Standards:**

* Layer Naming: E-\[SYSTEM\]-\[TYPE\]-\[STATUS\]  
* Color/LineWeight ตามมาตรฐาน AIA  
* Text/Dimension Styles standardized  
* Block Library มี Attributes

**Quality:**

* Audit \+ Purge ก่อนส่ง  
* Xref Relative Path  
* Plot test ทุกแผ่น  
* Panel Schedule \= Table (ไม่ใช่รูป\!)

---

**ท่านนายท่านครับ นี่คือข้อมูลทั้งหมดที่เกี่ยวข้องกับ AutoCAD โดยตรงสำหรับงานออกแบบบ้าน เน้นส่วนไฟฟ้า (Electrical Drawings) ที่ Amadeus จะต้องทำงานร่วมกับ**

**ส่วนที่ไม่เกี่ยวข้อง (งานโครงสร้าง, สุขาภิบาล, 3D Perspective) ผมตัดออกแล้วครับ**

**หากต้องการ AutoLISP Script ตัวอย่างเจาะลึกเพิ่มเติม หรือ Template DWG สำหรับ Electrical Plan บอกได้เลยครับ\!** 🔧⚡📐


```