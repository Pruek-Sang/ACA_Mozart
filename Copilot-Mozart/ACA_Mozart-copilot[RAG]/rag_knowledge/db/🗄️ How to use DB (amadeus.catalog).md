



เอกสารนี้อธิบายวิธีใช้ฐานข้อมูล `amadeus.catalog` และ view ต่าง ๆ
เพื่อให้ MCP / Copilot / ACA_Mozart ใช้ข้อมูลอย่างเป็นระบบและปลอดภัย

> **หลักคิดสั้น ๆ**
> - มี **ตารางหลักเดียว** คือ `amadeus.catalog` (Single Source of Truth)
> - โค้ดฝั่งแอป **เชื่อมผ่าน view มาตรฐาน** แทนการงัด JSON ตรง
> - RAG อ่าน “สัญญา” และตัวอย่างจากเอกสารใน `rag_knowledge/db/*`  
>   ไม่ยิง DB ตรง

---

## 🎯 0. เป้าหมายของฐานข้อมูลนี้

1. เก็บ **ความรู้เกี่ยวกับอุปกรณ์ไฟฟ้า / วงจร / เทมเพลต / กฎมาตรฐาน**  
   ในรูปแบบที่ MCP และเครื่องมือออกแบบใช้ได้ทันที
2. ทำตัวเป็น **แคตตาล็อกกลาง** สำหรับทุกโมดูล (MCP Core, Layout, Costing ฯลฯ)
3. ให้ RAG ใช้เป็น “แหล่งความจริง” ผ่านเอกสารอธิบาย (เช่น CATALOG_CONTRACT, HOW_TO_USE_DB ฯลฯ)
   ไม่ให้ LLM แต่งตัวเลข / กฎเอง

---

## 🏛️ 1. โครงสร้างหลักของฐานข้อมูล

### 1.1 ตารางหลัก: `amadeus.catalog`

ตารางนี้เก็บทุกชนิดของข้อมูลในระบบ โดยใช้ `kind` + `name` เป็นตัวระบุตัวตน

คอนเซปต์หลัก:

- `kind` : ประเภทของข้อมูล เช่น `COMPONENT`, `CABLE_SPEC`, `CIRCUIT_TEMPLATE`, `ROOM_TEMPLATE`, `APPLIANCE`,
  `PLACEMENT_RULE`, `VALIDATION_RULE`, `DERATING_FACTOR`, `GEOMETRY_FILTER`, `QA_PLAN`,
  `ZONE_BUNDLE`, `PANELBOARD`, `ROUTING_RULE`, `PROJECT_CONFIG`
- `name` : code หลัก เช่น  
  - `COMP-RECEPT-GEN-16A` (อุปกรณ์เต้ารับ)  
  - `CAB-THW-2P5` (สาย THW 2.5 sq.mm.)  
  - `CT-RECEPT-20A-GEN` (วงจรเต้ารับ 20A)
- `data` : JSONB รายละเอียดเชิงวิศวกรรม (rating, พิกัด, ตาราง derating ฯลฯ)
- `meta` : JSONB สำหรับ `tags`, `source`, flag ภายใน
- `embedding` : vector สำหรับงานค้นหา (ไม่บังคับใช้ทุกเคส)

แนวคิดสำคัญ:

- **ห้ามสร้างตารางใหม่ที่ซ้ำคอนเซปต์** ของ `amadeus.catalog`
- ทุกอย่างที่เป็น “ความรู้ด้านอุปกรณ์/วงจร/กฎ” ต้อง seed ผ่านตารางนี้ก่อน

---

### 1.2 🧬 View มาตรฐานที่ให้ฝั่งโค้ดใช้

เพื่อไม่ให้โค้ดไปแกะ JSON เองทุกที่ มี view มาตรฐานให้ใช้ เช่น

- `amadeus.v_components`
- `amadeus.v_cable_specs`
- `amadeus.v_circuit_templates`
- `amadeus.v_room_templates`
- `amadeus.v_placement_rules`
- `amadeus.v_validation_rules`
- `amadeus.v_geometry_filters`
- `amadeus.v_derating_factors`
- `amadeus.v_qa_plans`
- `amadeus.v_zone_bundles`
- `amadeus.v_panelboards`
- `amadeus.v_routing_rules`
- `amadeus.v_project_config`

**สัญญา**

1. ฝั่งโค้ดเชื่อมผ่าน view เหล่านี้เป็นหลัก  
   ไม่อ่าน JSON ดิบจาก `amadeus.catalog` โดยตรง เว้นแต่กรณีพิเศษ
2. เวลาเพิ่มข้อมูลใหม่ → เขียน seed ลง `amadeus.catalog` → view สะท้อนข้อมูลให้เอง

---

## 🏷️ 2. กติกา `kind`, `name`, `meta`

### 2.1 รายการ `kind` ที่ใช้จริง

- `COMPONENT`           – ข้อมูลชิ้นอุปกรณ์ไฟฟ้า (ปลั๊ก, สวิตช์, ดวงโคม ฯลฯ)
- `CABLE_SPEC`          – สเปกสายไฟ (THW, THHN ฯลฯ) พร้อม ampacity, resistance, reactance, ราคา
- `CIRCUIT_TEMPLATE`    – เทมเพลตวงจรมาตรฐาน (โหลด, breaker, max_outlets ฯลฯ)
- `ROOM_TEMPLATE`       – เทมเพลตห้อง (ประเภทห้อง, base_load, typical_appliances, compliance)
- `APPLIANCE`           – อุปกรณ์ไฟฟ้าตามหมวด (ห้องนอน, ครัว ฯลฯ) พร้อม power / startup_current ฯลฯ
- `PLACEMENT_RULE`      – กติกาการวางอุปกรณ์ในแปลน (ระยะห่าง, สูงจากพื้น, zone ที่ห้ามวาง ฯลฯ)
- `VALIDATION_RULE`     – กติกาตรวจแบบหลังวาง (โหลดเกิน 80%, IP rating ไม่พอ ฯลฯ)
- `DERATING_FACTOR`     – ตาราง derating สายไฟตามอุณหภูมิ / การรวมสาย ฯลฯ
- `GEOMETRY_FILTER`     – กฎพื้นที่ / zone พิเศษเพื่อช่วย layout engine (เก็บเป็น JSON)
- `QA_PLAN`             – แผนตรวจสอบคุณภาพข้อมูลใน catalog
- `ZONE_BUNDLE`         – กลุ่ม zone/room สำหรับโปรเจกต์หนึ่ง ๆ
- `PANELBOARD`          – ข้อมูล DB/MDB/SDB ที่ใช้ในโปรเจกต์
- `ROUTING_RULE`        – กติกาเดินสาย / routing
- `PROJECT_CONFIG`      – ค่าตั้งต้นโปรเจกต์ (โพรไฟล์มาตรฐาน, safety margin ฯลฯ)

### 2.2 รูปแบบ `name` (Code)

- Prefix สื่อชนิด เช่น  
  - `COMP-...` สำหรับ COMPONENT  
  - `CAB-...` สำหรับ CABLE_SPEC  
  - `CT-...`  สำหรับ CIRCUIT_TEMPLATE
- ชื่อควรเป็นอังกฤษ snake/kebab / ตัวพิมพ์ใหญ่ผสมได้ แต่อ่านแล้วเข้าใจหน้าที่
- `kind + name` ต้องไม่ซ้ำ (มี unique constraint)

ตัวอย่าง:

- `COMP-RECEPT-GEN-16A`
- `CAB-THW-2P5`
- `CT-RECEPT-20A-GEN`

### 2.3 โครง `meta`

ทุกแถวใน `amadeus.catalog` สามารถใส่ meta เช่น

```json
{
  "tags":   ["phase1", "component", "lighting"],
  "source": "manual_seed",
  "flags":  ["draft"]
}
