# ACA_Mozart Next Step: The 80% Draft Assistant
**Date:** 2025-11-28
**Status:** Concept & Planning
**Objective:** ยกระดับ MCP จาก "เครื่องคิดเลข" สู่ "ผู้ช่วยเขียนแบบ (Draftsman Assistant)" ที่สามารถขึ้นโครงร่างแบบไฟฟ้าได้ 80% โดยอัตโนมัติ

---

## 1. The Missing Link: "การอ่านพื้นที่" (Input Understanding)
ปัจจุบัน MCP เก่งเรื่องคำนวณ แต่ยังขาด "ดวงตา (Vision)" ที่จะมองเห็นห้องและ "สมองส่วนพื้นที่ (Spatial Intelligence)" เราต้องเพิ่ม Module ใหม่เพื่ออ่านบริบททางกายภาพจากไฟล์สถาปัตยกรรม

### **Module: `DXFReader` / `GeometryParser`**
MCP ไม่ควรเดาห้องสี่เหลี่ยมเปล่าๆ แต่ควร "อ่าน" ไฟล์ DXF ที่สถาปนิกให้มาได้

#### **Logic การทำงาน:**
1.  **Read DXF:** อ่านไฟล์ `.dxf` (Text format) ซึ่งประมวลผลได้ง่ายและเร็วกว่า `.dwg`
2.  **Layer Filtering:** กรองหา Layer ที่มีความหมายทางกายภาพ:
    *   `WALL`: ผนัง (Boundary ของห้อง)
    *   `DOOR`: ประตู (จุดเข้าออก, ทิศทางการเปิด)
    *   `WINDOW`: หน้าต่าง (ห้ามวางตู้/ปลั๊กทับ)
    *   `FURNITURE`: เฟอร์นิเจอร์ (Obstacle หรือจุดที่ต้องการไฟ)
3.  **Geometry Conversion:** แปลงเส้นสายใน CAD เป็น Object ทางคณิตศาสตร์:
    *   **`Room_Polygon`**: เส้นรอบรูปปิดที่ระบุขอบเขตห้อง
    *   **`Obstacle_Rects`**: พื้นที่ห้ามวาง (No-go zones) เช่น ตู้เสื้อผ้า, เตียง
    *   **`Access_Points`**: พิกัดประตูและรัศมีวงสวิง (Swing Arc)

---

## 2. The Brain: "ตรรกะการวางตำแหน่ง" (Placement Logic)
เปลี่ยน "ข้อกำหนดทางไฟฟ้า" และ "มาตรฐาน (NEC/EIT)" ให้เป็น "Algorithm การวางตำแหน่ง" บนพื้นที่จริง

### **A. แสงสว่าง (Lighting Placement)**
*   **Input:** Room Polygon, Ceiling Height, Lux Requirement (จาก Load Calc)
*   **Algorithm:**
    1.  **Centroid Calculation:** หาจุดกึ่งกลางทางเรขาคณิตของห้อง
    2.  **Grid System:**
        *   ถ้าห้องเล็ก (< X ตร.ม.): วาง 1 จุดที่ Centroid
        *   ถ้าห้องใหญ่: แบ่ง Grid (2x2, 3x3) ตามระยะห่างที่เหมาะสม (Spacing Criteria) เพื่อให้แสงกระจายทั่ว
    3.  **Collision Check:** ตรวจสอบตำแหน่งกับ Layer `FURNITURE` (เช่น ต้องไม่ชนพัดลมเพดาน)

### **B. เต้ารับ (Receptacles Placement) - กฎ 6ft/12ft**
*   **Input:** Wall Segments (เส้นรอบรูปห้อง), Furniture Obstacles
*   **Algorithm:**
    1.  **Start Point:** เริ่มต้นเดินจากขอบวงกบประตู (Door edge)
    2.  **First Point:** วางจุดแรกภายใน 1.8 เมตร (6ft) ตามมาตรฐาน
    3.  **Next Points:** เดินเลาะตามเส้นผนัง วางจุดต่อไปทุกๆ 3.6 เมตร (12ft)
    4.  **Obstacle Avoidance:**
        *   ตรวจสอบว่าจุดที่วางทับกับ `Obstacle_Rects` (เช่น ตู้, เตียง) หรือไม่
        *   ถ้าทับ → ขยับ (Shift) ซ้าย/ขวา ให้พ้น หรือเปลี่ยน Type เป็น "ปลั๊กหัวเตียง" / "ปลั๊กซ่อน"
    5.  **Special Context:**
        *   ถ้าเจอ **Counter ครัว**: เปลี่ยน Logic เป็น "วางเหนือเคาน์เตอร์" ทุก 1.2 เมตร (4ft)
        *   ถ้าเจอ **ผนังกระจก (Window)**: ข้าม หรือเปลี่ยนเป็นปลั๊กฝังพื้น (Floor Outlet)

### **C. สวิตช์ (Switch Placement)**
*   **Input:** Door Block, Swing Arc
*   **Algorithm:**
    1.  หาตำแหน่งประตู
    2.  วิเคราะห์ทิศทางการเปิด (Swing Direction)
    3.  วางสวิตช์ฝั่งตรงข้ามบานพับ (Latch side) ห่างวงกบ 15-20 ซม. (Standard Offset)
    4.  ความสูงมาตรฐาน 1.20m (AFF)

---

## 3. The Veins: "การเดินสายอัตโนมัติ" (Auto-Routing)
สร้างเส้นสายไฟที่ดูเป็นธรรมชาติและประหยัดระยะทาง เพื่อลดภาระ Draftsman

### **Algorithm:**
1.  **Circuit Grouping:** จับกลุ่มอุปกรณ์ที่ใช้วงจรเดียวกัน (เช่น ไฟแสงสว่างห้องนอน 1-3 รวมเป็น 1 วงจร)
2.  **Pathfinding (MST + Heuristics):**
    *   ใช้ **Minimum Spanning Tree (MST)** หาเส้นทางที่เชื่อมทุกจุดโดยใช้สายไฟน้อยที่สุด
    *   **Heuristics:** ปรับแต่งเส้นทางให้สวยงาม:
        *   **Orthogonal:** เดินเส้นตรงหักมุม 90 องศา (สำหรับแบบ Shop Drawing)
        *   **Spline/Arc:** เดินเส้นโค้ง (สำหรับแบบ Concept/Design)
3.  **Obstacle Avoidance:** หลบเสา (Column) หรือช่องชาร์ป (Shaft) ถ้ามีข้อมูล
4.  **Homerun Generation:** สร้างสัญลักษณ์ลูกศร (Arrow) ชี้ไปยังทิศทางของตู้ Panel ที่ใกล้ที่สุด พร้อมระบุ Tag วงจร

---

## 4. The Output: "AutoLISP ที่ฉลาดขึ้น" (Smart Output)
ไม่ใช่แค่การสั่งวาดเส้น แต่เป็นการสร้าง Object ที่มีความหมาย

*   **Smart Blocks:** ใช้ Block ที่มี Attribute (เช่น `TAG=L1`, `CKT=3`, `VA=100`) เพื่อให้แก้ไขค่าได้ง่าย
*   **Layer Management:** แยก Layer อย่างชัดเจนและเป็นระบบ (เช่น `E-PWR-WALL`, `E-LGT-CEIL`, `E-WIRE-HOME`) เพื่อให้เปิด/ปิดดูแบบได้ง่าย
*   **X-Data (Advanced):** ฝังข้อมูลการคำนวณ (VA, Amp, Wire Size) ลงไปในเส้นสายไฟใน AutoCAD (BIM-lite concept)

---

## 5. Handling Real-World Chaos (การรับมือกับความไม่สมบูรณ์)
แก้ปัญหา "Garbage In, Garbage Out" และไฟล์ CAD ที่ไม่ได้มาตรฐาน

### **A. Layer Mapping Config (แก้ปัญหาชื่อ Layer แปลก)**
*   **Scan & Guess:** ระบบ Scan ชื่อ Layer ทั้งหมดและใช้ AI เดาบริบท (เช่น `A-WALL-NEW` น่าจะเป็นผนัง)
*   **User Confirmation:** ถาม User ครั้งเดียวตอนเริ่มโปรเจกต์ ("Layer ไหนคือผนัง?", "Layer ไหนคือเฟอร์?")
*   **Save Config:** บันทึกเป็น `Company_Standard.json` เพื่อใช้ซ้ำกับโปรเจกต์อื่นของบริษัทเดิม

### **B. Geometry Filtering (แก้ปัญหาไฟล์รก)**
*   **Ignore Irrelevant:** "ตาบอด" กับ Layer ที่ไม่เกี่ยว (เช่น Dimension, Text, Hatch ต้นไม้)
*   **Simplify:** รวมเส้นที่ซ้อนทับกัน (Overlapping) ให้เป็นเส้นเดียว, ตัดเส้นขยะ (Noise) ทิ้ง
*   **Bounding Box:** มอง Block เฟอร์นิเจอร์ที่ละเอียดเกินไปให้เป็นแค่กล่องสี่เหลี่ยมเพื่อเช็คการชน

### **C. Revision Cloud & Non-Destructive (แก้ปัญหา AI ผิดพลาด)**
*   **Non-Destructive:** สร้าง Layer ใหม่ของ MCP เท่านั้น (`MCP-*`) ไม่ลบหรือแก้ไข Layer เดิมของลูกค้า
*   **Confidence Score & Revision Clouds:**
    *   จุดไหนที่ AI ไม่มั่นใจ (เช่น มุมห้องซับซ้อน, เฟอร์นิเจอร์แน่น) → วาด **"เมฆสีแดง (Revision Cloud)"** ใน Layer `MCP-REVIEW`
    *   Draftsman เปิดไฟล์มา → ปิด Layer อื่น → ดูเมฆแดง → แก้ไขจุดนั้นก่อน
*   **Dynamic Blocks:** อุปกรณ์มี Grip ให้ Flip (กลับด้าน) ได้ง่าย กรณีวางผิดฝั่ง

---

## 6. Critical Pitfalls & Risks (ข้อควรระวังสำคัญ) ⚠️

### **A. Scale & Units (หน่วยวัด)**
*   **ความเสี่ยง:** ไฟล์หน่วย mm vs m vs inch ทำให้สเกลเพี้ยน (วางปลั๊กห่าง 3 กม. หรือ Block เล็กเท่ามด)
*   **ทางแก้:** ระบบ **Auto-detect Unit** (เช่น เช็คความกว้างประตู ถ้า = 0.9 คือ m, = 900 คือ mm) หรือบังคับ User ระบุหน่วยก่อน Process

### **B. Z-Axis / Levels (ระดับความสูง)**
*   **ความเสี่ยง:** ใน 2D มองไม่เห็นความสูง อาจวางปลั๊กพื้นทับปลั๊กผนัง หรือวางปลั๊กชนหน้าต่างสูงถึงพื้น
*   **ทางแก้:**
    *   ระบุ Attribute ระดับความสูง (AFF)
    *   Check Stacking: ถ้าตำแหน่ง X,Y ตรงกัน ต้องขยับ Offset ให้เห็นชัดเจนในแปลน

### **C. Coordinate Systems (ระบบพิกัด)**
*   **ความเสี่ยง:** User หมุนแกน (UCS) หรือจุด Origin อยู่ไกลมาก (UTM Coordinates) ทำให้ Insert Block ผิดตำแหน่งหรือเพี้ยน
*   **ทางแก้:** Reset UCS เป็น World ก่อนเสมอ และพิจารณาใช้ Relative Coordinates

### **D. Liability (ความรับผิดชอบทางกฎหมาย)**
*   **ความเสี่ยง:** นำแบบไปสร้างจริงโดยไม่ตรวจ แล้วเกิดความเสียหาย
*   **ทางแก้:**
    *   ใส่ **Disclaimer** ชัดเจน: "DRAFT FOR ASSISTANCE ONLY"
    *   ใส่ **Watermark** จนกว่าจะผ่านการตรวจสอบโดยวิศวกร

---

## 7. สรุป Workflow (The "Safe" Workflow)
1.  **Upload:** User ส่งไฟล์ DXF + Load Schedule
2.  **Map:** ระบบถามจับคู่ Layer (Wall, Door, Furniture)
3.  **Process:**
    *   AI กรองขยะ → สร้าง Geometry
    *   วางอุปกรณ์ตาม Logic (Placement)
    *   ลากสาย (Routing)
    *   **Mark จุดเสี่ยงด้วย Revision Cloud**
4.  **Output:** ไฟล์ AutoLISP (.lsp)
5.  **Draftsman:**
    *   Run Script ใน AutoCAD
    *   **ตรวจเมฆแดง** → แก้ไข
    *   **Flip Block** ที่กลับด้าน
    *   **จบงาน 80% ในเวลาอันสั้น**

---
*เอกสารนี้รวบรวมแนวคิดเพื่อการพัฒนาต่อยอดระบบ ACA_Mozart ให้เป็นผู้ช่วยอัจฉริยะที่ทำงานร่วมกับมนุษย์ได้อย่างมีประสิทธิภาพสูงสุด*
