




```markdown
# 📜 CATALOG_CONTRACT – สัญญาระหว่าง amadeus.catalog, MCP, และ RAG

เอกสารนี้คือ “สัญญากลาง” ระหว่าง

- **ฐานข้อมูล**: `amadeus.catalog` + view ต่าง ๆ
- **MCP Core v2.0**: ตัวคำนวณหลัก (โหลด, สายไฟ, compliance, layout)
- **RAG / Canonical Funnel**: ตัวสร้าง `ProjectInputSpec` และตอบคำถามมาตรฐาน

---

## 1. เป้าหมายของสัญญา

1. กำหนดให้ `amadeus.catalog` เป็น **แหล่งข้อมูลหลักสุดท้าย**  
   เกี่ยวกับอุปกรณ์, สายไฟ, วงจร, กฎ, derating
2. แยกขอบเขตให้ชัด:
   - RAG: อ่าน “คำอธิบาย + ตัวอย่าง” ผ่านเอกสารใน `rag_knowledge/db/*`
   - MCP: เป็นคนเดียวที่ยิง DB และใช้ตัวเลขใน `data` คำนวณจริง
3. ทำให้การเปลี่ยน schema / เพิ่ม kind ใหม่
   สามารถทำได้โดยไม่พังระบบที่เหลือ (ผ่านเอกสาร contract นี้)

---

## 2. สถาปัตยกรรมโดยย่อ (RAG ↔ MCP ↔ DB)

### 2.1 ฝั่ง RAG (Canonical Funnel)

- รับ `ProjectRequirements` (ภาษาคน) → สร้าง `ProjectInputSpec`
- ใช้ knowledge groups:
  - `mcp_spec`
  - `catalog_schema` (รวมไฟล์นี้ + HOW_TO_USE_DB ฯลฯ)
  - `thai_standard` / `example_project`
- อ่านได้แค่เนื้อหาในเอกสาร ไม่ยิง DB ตรง  
  (ใช้ `knowledge_service` + `knowledge_index.json` เป็นตัวกลาง)

### 2.2 ฝั่ง MCP Core v2.0

- รับ `ProjectInputSpec` จาก RAG ผ่าน `/mcp_spec` API
- ใช้รหัสต่าง ๆ จาก spec เช่น
  - `template_code` (ROOM_TEMPLATE / CIRCUIT_TEMPLATE)
  - `device_code` (APPLIANCE / COMPONENT)
  - `rule_profile_id` (VALIDATION_RULE / QA_PLAN)
- ยิง query ไปยัง view ของ `amadeus.catalog` ด้านล่าง
- ใช้ข้อมูลเหล่านี้ ร่วมกับ pandapower / engine อื่น เพื่อออกแบบและตรวจสอบ

### 2.3 ฐานข้อมูล

- มีแค่ตารางหลัก `amadeus.catalog` และ view ที่หุ้ม JSON
- ใช้แนวคิด **“kind + name + data + meta”** เป็นแกนกลาง
- ถูก seed จากไฟล์ JSON/SQL ที่ควบคุมได้ (ไม่ให้ LLM แก้เอง)

---

## 3. สัญญาระดับตาราง: `amadeus.catalog`

### 3.1 โครงสร้างเชิงคอนเซปต์

- `id`              – primary key (UUID)
- `kind`            – ประเภทข้อมูล (ดูรายการ kind ใน HOW_TO_USE_DB)
- `name`            – code หลักในระบบ (unique ร่วมกับ kind)
- `description`     – ข้อความสั้นอธิบาย
- `version`         – เวอร์ชันข้อมูล
- `effective_at`    – วันที่ข้อมูลเริ่มมีผล
- `is_active`       – ใช้งานอยู่หรือไม่
- `data` (JSONB)    – รายละเอียดเชิงวิศวกรรม
- `embedding`       – vector (optional)
- `meta` (JSONB)    – tags / source / flags
- `created_at`, `updated_at` – time stamp

**สัญญา**

1. `kind + name` ต้องไม่ซ้ำ
2. `data` ต้องเก็บ field ที่ engine ต้องใช้ **อย่างมีโครงสร้างชัดเจน**
3. การเปลี่ยนโครงสร้าง JSON ใน `data`
   ต้องอัปเดตเอกสาร HOW_TO_USE_DB + CATALOG_CONTRACT พร้อมกัน

### 3.2 View ที่ผูกกับ MCP

ดูรายการเต็มใน HOW_TO_USE_DB:

- `v_components`, `v_cable_specs`, `v_circuit_templates`,
  `v_room_templates`, `v_placement_rules`, `v_validation_rules`,
  `v_geometry_filters`, `v_derating_factors`,
  `v_qa_plans`, `v_zone_bundles`, `v_panelboards`,
  `v_routing_rules`, `v_project_config`

MCP ต้องอ่านผ่าน view เหล่านี้เป็นหลัก

---

## 4. สัญญาราย `kind`

> ส่วนนี้เน้น field ที่ “engine จำเป็นต้องใช้”  
> ไม่ได้ลอก JSON ทั้งหมดมา แต่พอให้ dev เห็นว่าต้องมีอะไรขั้นต่ำ

### 4.1 `COMPONENT`

- ใช้เก็บข้อมูลชิ้นอุปกรณ์ (ปลั๊ก, สวิตช์, ดวงโคม ฯลฯ)
- Field หลักใน `data`:
  - `component_type` / `subtype`
  - `voltage_rating_v`, `current_rating_a`, `power_rating_w`
  - `phase`, `ip_rating`
  - `mount_height_mm`, `mount_type`
  - `dimension_mm` (กว้าง/สูง/ลึก)
  - `standard_reference`
  - `brand`, `model`
- **ใช้โดย**
  - MCP: คิดโหลด, ตรวจ IP, สร้าง BOM
  - Layout engine: วางตำแหน่ง, เช็กขนาด

### 4.2 `CABLE_SPEC`

- เก็บสเปกสายไฟและราคาต่อเมตร
- Field หลัก:
  - `size_mm2`, `material`, `insulation_type`, `insulation_temp_rating_c`
  - `ampacity_free_air_a`, `ampacity_in_conduit_a`
  - `resistance_ohm_per_km_20c`, `reactance_ohm_per_km`
  - `price_thb_per_m`, `price_date`
  - `standard_reference`
- **ใช้โดย**
  - MCP + pandapower: เลือกสาย / เช็ก VD / ความร้อน
  - Costing: Estimate งบประมาณสายไฟ

### 4.3 `CIRCUIT_TEMPLATE`

- เทมเพลตวงจร เช่น วงจรเต้ารับทั่วไป 20A
- Field หลัก:
  - `template_id`
  - `circuit_type`, `load_type`
  - `breaker_rating_a`, `voltage_v`, `phase`
  - `wire_size_mm2`
  - `max_load_w`, `recommended_load_w`
  - `max_outlets`
  - `dedicated_circuit` (true/false)
- **ใช้โดย**
  - MCP: ผูกห้อง / โหลด → วงจรมาตรฐานที่เหมาะสม
  - VALIDATION_RULE: ใช้ข้อมูลนี้ตรวจโหลดรวมวงจร

### 4.4 `ROOM_TEMPLATE`

- เทมเพลตห้องพร้อม base load และกฎ minimum
- Field หลัก:
  - `room_type`, `display_name`
  - `base_load.lighting_per_sqm_w`
  - `base_load.receptacles_count_per_room`
  - `base_load.receptacles_max_spacing_m`
  - `typical_appliances[]` (อ้าง `appliance_id`)
  - `compliance.min_receptacles`, `compliance.max_voltage_drop_percent`
- **ใช้โดย**
  - RAG: อ้างอิงเวลาสร้าง `ProjectInputSpec`
  - MCP: ใช้เป็น default ถ้า user ไม่ระบุรายละเอียดมาก

### 4.5 `APPLIANCE`

- รายการอุปกรณ์ไฟฟ้าตามหมวด ใช้คิดโหลดและ BOM
- Field หลัก:
  - `category`, `subcategory`
  - `power_w`, `running_current_a`, `startup_current_a`
  - `voltage_v`, `power_factor`
  - `requires_dedicated_circuit`
  - `typical_rooms`, `usage_hours_per_day`
  - `brand`, `model`, `price_thb`
- **ใช้โดย**
  - MCP: ใช้ข้อมูลโหลดจริง → ป้อนเข้า pandapower
  - RAG: ใช้อ่านสเปก เพื่อไม่แต่งโหลดเอง

### 4.6 `PLACEMENT_RULE` / `VALIDATION_RULE` / `DERATING_FACTOR`

- PLACEMENT_RULE:
  - กติกาวางอุปกรณ์ (spacing, height, avoid_zones)
- VALIDATION_RULE:
  - ตรวจแบบหลังวาง เช่น โหลดรวมวงจรไม่เกิน 80%
- DERATING_FACTOR:
  - ตาราง derating ตามอุณหภูมิ ฯลฯ

Engine ฝั่ง MCP/Validator ต้องอ่าน rule เหล่านี้จาก view ตาม kind
แล้วอิมพลีเมนต์ logic ให้ตรงกับ `parameters` ใน JSON

### 4.7 Kind อื่น ๆ

- `GEOMETRY_FILTER`  – สำหรับข้อมูลทางเรขาคณิต/พื้นที่พิเศษ
- `QA_PLAN`          – กำหนดชุด test สำหรับตรวจความครบถ้วนของ catalog
- `ZONE_BUNDLE`      – กลุ่ม zone/room ภายในโปรเจกต์
- `PANELBOARD`       – ข้อมูลตู้ไฟต่าง ๆ
- `ROUTING_RULE`     – กฎเดินสาย
- `PROJECT_CONFIG`   – config ระดับโปรเจกต์ (profile, default ฯลฯ)

รายละเอียด JSON ดูจาก seed ปัจจุบัน และปรับตามเอกสารนี้เวลาเปลี่ยน

---

## 5. การเชื่อม RAG → MCP → DB ในแง่สัญญา

### 5.1 จาก `ProjectRequirements` → `ProjectInputSpec`

- RAG อ่านเอกสาร:
  - MCP design
  - HOW_TO_USE_DB
  - CATALOG_CONTRACT
  - ตัวอย่าง `example_req_inputspec_*.md`
- RAG สร้าง `ProjectInputSpec` โดย:
  - เลือก `room_type` ให้ตรงกับ ROOM_TEMPLATE
  - ใส่ `template_code` / `device_code` จาก code ที่ระบุในเอกสาร
  - เลือก `rule_profile_id` ให้สอดคล้องกับ VALIDATION_RULE / QA_PLAN

### 5.2 จาก `ProjectInputSpec` → การ query DB

- MCP รับ `ProjectInputSpec` จาก `/mcp_spec`
- ใช้ code ที่ได้จาก RAG เป็นกุญแจในการ query view:
  - `template_code` → `v_room_templates` / `v_circuit_templates`
  - `device_code`   → `v_appliances` / `v_components`
  - `rule_profile_id` → `v_validation_rules` / `v_qa_plans`
- MCP ไม่ให้ LLM แก้ไข code เหล่านี้อีก  
  ใช้ตรง ๆ กับ DB ตามสัญญานี้

### 5.3 Trust Log

- ทุกครั้งที่เรียก `/mcp_spec`:
  - บันทึก input, docs ที่ RAG ใช้, model, output, validation result
- ใช้ trust log ตรวจย้อนหลังว่า
  - RAG เลือก code จากเอกสารถูกไหม
  - MCP ใช้ข้อมูลจาก catalog ตามสัญญาหรือเปล่า

---

## 6. สิ่งที่คาดหวังจาก CATALOG_CONTRACT

1. เวลา dev คนใหม่เข้ามา ต้องเข้าใจได้ว่า  
   “kind ไหนเอาไปใช้ตรงไหน” และ “ห้ามเปลี่ยนอะไรโดยไม่แจ้ง”
2. เวลาแก้ schema JSON ของ kind ใด kind หนึ่ง
   - ต้องอัปเดตเอกสารนี้ + HOW_TO_USE_DB
   - เพิ่ม/อัปเดต test ที่ใช้ catalog นั้น
3. RAG / MCP / DB ทำงานเป็น pipeline เดียวกันได้  
   โดยไม่ต้องเดาโครงสร้างกันเอง
