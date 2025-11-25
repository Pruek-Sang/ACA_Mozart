## **2.1 Required Fields (Hard Required - ห้ามขาด)**

## **2.1.1 Project Information Level**
project_info.project_name: string
  - ต้องไม่เป็น empty string
  - ความยาว: 3-200 ตัวอักษร
  - ใช้เป็นชื่อโปรเจกต์ในรายงานและ output files
  - ตัวอย่าง: "บ้านคุณสมชาย ซอยสุขุมวิท 101", "Townhome Project - Rama 9"
  - Error ถ้า: null, "", "untitled"

project_info.building_type: enum
  - ต้องเป็นค่าใน: [RESIDENTIAL_SINGLE_1F, RESIDENTIAL_SINGLE_2F, RESIDENTIAL_SINGLE_3F, TOWNHOME_2F, TOWNHOME_3F]
  - ห้ามเป็น: null, unknown, custom
  - Error ถ้า: ไม่อยู่ในรายการที่รองรับ
  - ใช้กำหนด: rule_profile, template selection, demand factor

project_info.location: object (optional แต่แนะนำ)
  - ถ้ามี: ใช้เลือก local code (เช่น กรุงเทพ vs จังหวัด)
  - ถ้าไม่มี: ใช้ default = "THAILAND_GENERAL"
## **2.1.2 Electrical System Level

electrical_system.voltage_system: enum
  - ต้องเป็นค่าใน: [TH_1PH_230V, TH_3PH_400V]
  - ปัจจุบันเปิดใช้เฉพาะ: TH_1PH_230V
  - Error ถ้า: null, "220V", "110V", custom voltage
  - ถ้าเป็น TH_3PH_400V → แจ้งเตือนว่ายังไม่เปิดใน demo

electrical_system.earthing: enum (optional with default)
  - ค่าที่รองรับ: [TT, TN_S, TN_C_S, TN_C]
  - Default behavior:
    - ถ้า voltage_system = TH_1PH_230V และไม่ระบุ → auto = "TT"
    - ถ้า voltage_system = TH_3PH_400V และไม่ระบุ → auto = "TN_S"
  - Error ถ้า: IT, custom

electrical_system.main_supply: object
  - main_supply.type: ["UTILITY_GRID"] - ต้องมี
  - main_supply.rated_current: integer - ถ้ามี ต้อง > 0
  - ถ้าไม่ระบุ rated_current → MCP จะคำนวณจากโหลดรวม + safety margin
## **2.1.3 Rooms Level**

text

`rooms: array   - ต้องมีอย่างน้อย 1 ห้อง  - Error ถ้า: [], null, undefined  - Maximum: 35 ห้อง (ตาม MCP_CAPABILITIES_AND_LIMITS) rooms[].room_id: string   - ต้องไม่ซ้ำกันภายใน array  - Format แนะนำ: "RM-xxx", "ROOM_xxx"  - ต้องไม่เป็น: null, "", duplicate rooms[].room_type: enum   - ต้องเป็นค่าที่มีใน ROOM_TEMPLATE database  - ตัวอย่าง: LIVING_ROOM, BEDROOM, KITCHEN, BATHROOM, UTILITY  - Error ถ้า: null, "unknown", custom type ที่ไม่มีใน DB  - RAG ต้อง: map คำพูดของ user เป็น room_type ที่ถูกต้อง rooms[].template_code: string (optional แต่แนะนำ)   - ถ้ามี: MCP จะใช้ template นี้โดยตรง  - ถ้าไม่มี: MCP จะเลือก template จาก room_type  - Error ถ้า: template_code ไม่มีใน DB → MCP error INVALID_TEMPLATE_CODE  - Format: "LIVING_STANDARD", "KITCHEN_HEAVY", "BEDROOM_BASIC"`

## **2.1.4 Loads Level**

text

`loads: array   - ต้องมีอย่างน้อย 1 โหลด  - Error ถ้า: [], null  - Maximum per circuit: 10 โหลด (แนะนำ) loads[].load_id: string   - ต้องไม่ซ้ำกันภายใน array  - Format: "LOAD-xxx", "L-xxx" loads[].room_id: string   - ต้อง reference ไปยัง rooms[].room_id ที่มีอยู่  - Error ถ้า: room_id ไม่มีใน rooms[] array loads[].device_code: string   - ต้องเป็น code ที่มีใน DEVICE_CATALOG  - ตัวอย่าง: "AC_12000BTU", "SOCKET_16A", "LED_DOWNLIGHT_9W"  - Error ถ้า: device_code ไม่มีใน catalog  - RAG ต้อง: แปลงคำอธิบายของ user เป็น device_code ที่ใกล้เคียง  - ห้าม: fallback เป็น "UNKNOWN" หรือ "GENERIC" loads[].qty: integer   - ต้อง ≥ 1  - ใช้คูณกับ power rating จาก catalog  - Error ถ้า: 0, null, negative loads[].power_kw: float (optional)   - ถ้ามี: override ค่าจาก catalog  - ถ้าไม่มี: ใช้ค่าจาก device_code  - Error ถ้า: ≤ 0, > 100 kW (unrealistic)`

## **2.1.5 Constraints Level**

text

`constraints.rule_profile_id: string   - ต้องเป็นค่าที่มีใน RULE_PROFILE table  - ปัจจุบันรองรับ: "TH_RESIDENTIAL_LV"  - Future: "TH_RESIDENTIAL_MV", "TH_COMMERCIAL_LV"  - Error ถ้า: null, unknown, custom  - Default: "TH_RESIDENTIAL_LV" constraints.user_constraints: array (optional)   - เป็น array ของ flag objects  - แต่ละ flag ต้องเป็น key-value ที่ MCP รู้จัก  - ตัวอย่าง valid flags:    - split_kitchen_circuit: boolean    - rcd_for_all_outlets: boolean    - separate_ac_circuits: boolean  - Error ถ้า: flag ที่ MCP ไม่รองรับ → warning หรือ ignore`

---

## **2.2 Optional Fields with Defaults (ไม่บังคับ แต่มี default)**

## **2.2.1 Auto-Fill Behavior**

text

`electrical_system.earthing   - ถ้าไม่ระบุ + voltage_system = TH_1PH_230V    → auto = "TT"  - ถ้าไม่ระบุ + voltage_system = TH_3PH_400V    → auto = "TN_S" electrical_system.main_supply.rated_current   - ถ้าไม่ระบุ    → MCP คำนวณจากโหลดรวม × 1.25 (safety margin)    → round up ไปยังขนาด standard breaker constraints.rule_profile_id   - ถ้าไม่ระบุ    → auto = "TH_RESIDENTIAL_LV" rooms[].template_code   - ถ้าไม่ระบุ    → MCP เลือกจาก room_type + ข้อมูล loads ในห้อง    → อาจเลือกไม่ได้ → error MISSING_TEMPLATE loads[].power_kw   - ถ้าไม่ระบุ    → ใช้ค่าจาก DEVICE_CATALOG[device_code].rated_power`

## **2.2.2 Recommended but Optional**

text

`project_info.location   - แนะนำให้มี: ใช้เลือก local code  - ถ้าไม่มี: ใช้ THAILAND_GENERAL project_info.floor_area_sqm   - แนะนำให้มี: ใช้ validate จำนวนห้อง  - ถ้าไม่มี: ไม่มี validation rooms[].floor_level   - แนะนำให้มี: ใช้จัดกลุ่ม circuit ตามชั้น  - ถ้าไม่มี: ถือว่าชั้น 1 ทั้งหมด loads[].distance_from_db_m   - แนะนำให้มี: ใช้คำนวณ voltage drop  - ถ้าไม่มี: ใช้ค่า default = 15m (average)`

---

## **2.3 Hard Fail Conditions (เงื่อนไขที่ต้อง Error ทันที)**

## **2.3.1 Structural Errors**

text

`❌ rooms = [] หรือ null   → RAG ต้องไม่ส่งให้ MCP  → Response: "ProjectInputSpec ไม่สมบูรณ์: ต้องมีข้อมูลห้องอย่างน้อย 1 ห้อง" ❌ loads = [] หรือ null   → RAG ต้องไม่ส่งให้ MCP  → Response: "ProjectInputSpec ไม่สมบูรณ์: ต้องมีข้อมูลโหลดอย่างน้อย 1 โหลด" ❌ rooms[].room_type = null หรือ unknown   → RAG ต้องขอข้อมูลเพิ่มจาก user  → Response: "กรุณาระบุประเภทห้อง เช่น ห้องนั่งเล่น, ห้องนอน, ห้องครัว" ❌ duplicate room_id หรือ load_id   → RAG ต้องแก้ไข ID ให้ unique  → Generate new ID: "RM-001", "RM-002", ...`

## **2.3.2 Reference Errors**

text

`❌ loads[].room_id ไม่มีใน rooms[]   → RAG ต้องไม่ส่งให้ MCP  → Error: "โหลด '{load_id}' อ้างอิงไปยังห้อง '{room_id}' ที่ไม่มีอยู่" ❌ loads[].device_code ไม่มีใน DEVICE_CATALOG   → RAG ต้อง:    1. พยายามแปลงเป็น semantic code ที่ใกล้เคียง    2. ถ้าแปลงไม่ได้ → ขอข้อมูลเพิ่มจาก user  → Error: "ไม่พบอุปกรณ์ '{device_code}' ในระบบ กรุณาอธิบายเพิ่มเติม" ❌ constraints.rule_profile_id ไม่มีใน RULE_PROFILE   → RAG ต้องใช้ default = "TH_RESIDENTIAL_LV"  → Warning: "ใช้ rule profile มาตรฐานแทน"`

## **2.3.3 Range/Limit Errors**

text

`❌ จำนวนห้อง > 35   → RAG ต้องไม่ส่งให้ MCP  → Response: "MCP รองรับบ้านขนาดสูงสุด 35 ห้อง กรุณาแบ่งเป็นหลาย MDB" ❌ จำนวนวงจร > 50   → RAG ต้องไม่ส่งให้ MCP  → Response: "จำนวนวงจรเกินขีดจำกัด 50 วงจร กรุณาปรับแผนการออกแบบ" ❌ โหลดรวม > 35 kVA   → RAG ต้องแจ้งเตือน  → Response: "โหลดรวมเกิน 35 kVA แนะนำใช้ระบบ 3 เฟสหรือแบ่ง MDB" ❌ loads[].power_kw > 100 kW   → RAG ต้อง validate  → Response: "โหลด '{load_id}' มีค่า power เกิน 100 kW ผิดปกติ กรุณาตรวจสอบ"`

## **2.3.4 Validation Logic Errors**

text

`❌ building_type = RESIDENTIAL_SINGLE_1F แต่ floor_level > 1   → RAG ต้อง validate  → Error: "บ้าน 1 ชั้น ไม่ควรมีห้องที่ floor_level > 1" ❌ voltage_system = TH_1PH_230V แต่ earthing = TN_C   → RAG ต้อง warning  → Warning: "TN-C ไม่แนะนำสำหรับ 1 เฟส ควรใช้ TT" ❌ room_type = BATHROOM แต่ไม่มี RCBO flag   → RAG ต้อง auto-add flag  → Auto-fix: เพิ่ม user_constraints: {rcbo_for_bathroom: true}`

---

## **2.4 Data Normalization Rules (กฎการ Normalize ข้อมูล)**

## **2.4.1 String Normalization**

text

`project_name:   - Trim whitespace  - ตัดตัวอักษรพิเศษที่ไม่ต้องการ  - แปลง " (quote) เป็น ' (single quote) ถ้าจำเป็น room_id, load_id:   - ตัวพิมพ์ใหญ่ทั้งหมด (uppercase)  - แทนที่ space ด้วย underscore  - ตัวอย่าง: "room 1" → "ROOM_1" device_code:   - ตัวพิมพ์ใหญ่ทั้งหมด  - ตัวอย่าง: "ac_12000btu" → "AC_12000BTU"`

## **2.4.2 Numeric Normalization**

text

`power_kw:   - Round เป็นทศนิยม 2 ตำแหน่ง  - ตัวอย่าง: 1.2345 → 1.23 qty:   - Round เป็นจำนวนเต็ม  - ตัวอย่าง: 2.5 → 3 distance_from_db_m:   - Round เป็นทศนิยม 1 ตำแหน่ง  - ตัวอย่าง: 15.67 → 15.7`

## **2.4.3 Enum Normalization**

text

`building_type:   - Map คำพูดของ user:    "บ้านชั้นเดียว" → RESIDENTIAL_SINGLE_1F    "บ้าน 2 ชั้น" → RESIDENTIAL_SINGLE_2F    "ทาวน์เฮ้าส์" → TOWNHOME_2F room_type:   - Map คำพูดของ user:    "ห้องนั่งเล่น" → LIVING_ROOM    "ห้องนอน" → BEDROOM    "ห้องครัว" → KITCHEN    "ห้องน้ำ" → BATHROOM voltage_system:   - Map คำพูดของ user:    "1 เฟส", "230V" → TH_1PH_230V    "3 เฟส", "400V" → TH_3PH_400V`

---

## **2.5 Pre-Validation Checklist (เช็คก่อนส่งให้ MCP)**

## **ขั้นตอน Validation ใน RAG**

text

`1. ✅ Structure Check    □ project_info มีครบ?   □ electrical_system มีครบ?   □ rooms[] มีอย่างน้อย 1?   □ loads[] มีอย่างน้อย 1?   □ constraints มีครบ? 2. ✅ Field Type Check    □ string fields ไม่เป็น null/empty?   □ enum fields อยู่ใน allowed values?   □ integer fields เป็นจำนวนเต็มบวก?   □ float fields เป็นตัวเลขที่สมเหตุสมผล? 3. ✅ Reference Integrity Check    □ loads[].room_id มีอยู่จริงใน rooms[]?   □ loads[].device_code มีใน catalog?   □ constraints.rule_profile_id มีใน DB? 4. ✅ Range Check    □ จำนวนห้อง ≤ 35?   □ จำนวนวงจร ≤ 50 (ถ้าคำนวณได้)?   □ โหลดรวม ≤ 35 kVA?   □ power_kw แต่ละโหลด ≤ 100 kW? 5. ✅ Logic Check    □ building_type vs floor_level สอดคล้องกัน?   □ voltage_system vs earthing สอดคล้องกัน?   □ room_type = BATHROOM มี RCBO?   □ room_type = KITCHEN มีวงจรพิเศษ? 6. ✅ Completeness Check    □ ข้อมูลครบพอให้ MCP คำนวณได้?   □ มี template_code หรือ room_type ที่เลือก template ได้?   □ มี device_code ที่ valid ทั้งหมด?`

---

## **2.6 Error Response Strategy (กลยุทธ์การตอบ Error)**

## **2.6.1 Missing Required Field**

text

`RAG Response: "ProjectInputSpec ยังไม่สมบูรณ์: - ขาดข้อมูล: {field_name} - คำอธิบาย: {field_description} - กรุณาให้ข้อมูล: {prompt_for_user}" ตัวอย่าง: "ProjectInputSpec ยังไม่สมบูรณ์: - ขาดข้อมูล: rooms[0].room_type - คำอธิบาย: ประเภทของห้อง (ห้องนั่งเล่น, ห้องนอน, ฯลฯ) - กรุณาระบุว่าห้องนี้เป็นห้องประเภทใด"`

## **2.6.2 Invalid Reference**

text

`RAG Response: "พบข้อผิดพลาดในข้อมูล: - โหลด '{load_id}' อ้างอิงไปยังห้อง '{room_id}' ที่ไม่มีอยู่ - กรุณาตรวจสอบข้อมูลห้องและโหลดให้ถูกต้อง"`

## **2.6.3 Unknown Device Code**

text

`RAG Response (Step 1 - Try to Map): "ไม่พบอุปกรณ์ '{device_code}' ในระบบ กำลังพยายามแปลงเป็นรหัสที่ใกล้เคียง..." RAG Response (Step 2 - Success): "แปลง '{user_input}' เป็น '{semantic_code}' สำเร็จ" RAG Response (Step 2 - Fail): "ไม่สามารถระบุอุปกรณ์ได้ กรุณาอธิบายเพิ่มเติมเกี่ยวกับ: - ประเภทอุปกรณ์ (แอร์, ปลั๊ก, โคมไฟ, ฯลฯ) - ขนาด/กำลังไฟ (BTU, Watt, Ampere) - การใช้งาน (ทั่วไป, พิเศษ)"`

## **2.6.4 Limit Exceeded**

text

`RAG Response: "โครงการของท่านมีขนาดเกินขีดจำกัดของ MCP: - {parameter}: {value} (สูงสุดที่รองรับ: {limit}) - แนะนำ: {suggestion}" ตัวอย่าง: "โครงการของท่านมีขนาดเกินขีดจำกัดของ MCP: - จำนวนห้อง: 42 ห้อง (สูงสุดที่รองรับ: 35 ห้อง) - แนะนำ: แบ่งเป็นหลาย MDB หรือจัดกลุ่มห้องใหม่"`

---

## **2.7 Future Enhancements (การพัฒนาในอนาคต)**

## **Planned Validations**

- ✅ Cross-field validation (เช่น floor_area vs จำนวนห้อง)
    
- ✅ Power density check (kVA/sqm ควรอยู่ใน range ที่สมเหตุสมผล)
    
- ✅ Circuit count estimation (ประมาณจำนวนวงจรก่อนส่ง MCP)
    
- ✅ Cost estimation (ประมาณราคาคร่าวๆ ก่อน)
    

## **Planned Auto-Fixes**

- ✅ Auto-generate missing IDs
    
- ✅ Auto-map unknown device_code ด้วย AI
    
- ✅ Auto-add required constraints (เช่น RCBO for bathroom)
    
- ✅ Auto-balance load distribution
    

---