## **3.1 Overview: How MCP Reads ProjectInputSpec**

MCP อ่าน `ProjectInputSpec` แบบ **Sequential + Hierarchical**:

1. อ่าน `project_info` → ตั้งค่าบริบทโปรเจกต์
    
2. อ่าน `electrical_system` → ตั้งค่าพารามิเตอร์ไฟฟ้าพื้นฐาน
    
3. อ่าน `rooms[]` → สร้าง spatial structure
    
4. อ่าน `loads[]` → คำนวณโหลดแต่ละห้อง
    
5. อ่าน `constraints` → ใช้กฎและข้อจำกัด
    
6. **คำนวณ** → Circuit design, Cable sizing, Panel layout
    
7. **Generate** → Output BOM, Reports, Drawings
    

---

## **3.2 Project Info Section**

## **project_info.project_name**

- **ความสำคัญ**: ⭐⭐ (Medium)
    
- **MCP ใช้เพื่อ**:
    
    - ตั้งชื่อไฟล์ output (เช่น `{project_name}_SingleLineDiagram.pdf`)
        
    - แสดงใน header ของ reports
        
    - ใช้ใน metadata ของ AutoCAD drawings
        
- **ผลกระทบถ้าผิด**:
    
    - ไม่ทำให้คำนวณผิด
        
    - แต่ไฟล์ output จะมีชื่อไม่ชัดเจน
        
- **RAG ควร**:
    
    - ใช้ชื่อที่ user ให้มา ไม่ต้อง normalize มาก
        
    - เพิ่ม prefix/suffix ถ้าจำเป็น (เช่น "Project - {user_input}")
        

## **project_info.building_type**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - เลือก **default rule_profile_id** (ถ้าไม่ระบุ)
        
    - เลือก **demand factor** ตาม วสท. บทที่ 2
        
    - เลือก **template set** สำหรับห้อง (ถ้า room_type ไม่ระบุ)
        
    - กำหนด **safety margin** สำหรับ breaker sizing
        
- **ผลกระทบถ้าผิด**:
    
    - คำนวณโหลดผิด → breaker undersized/oversized
        
    - เลือก template ผิด → วงจรไม่ตรงความต้องการ
        
- **RAG ต้อง**:
    
    - Map คำพูดของ user ให้ถูกต้อง
        
    - Validate กับจำนวนชั้น (floor_level)
        
    - ถ้าไม่แน่ใจ → ขอข้อมูลเพิ่ม
        

## **project_info.location**

- **ความสำคัญ**: ⭐⭐⭐ (Medium-High)
    
- **MCP ใช้เพื่อ**:
    
    - เลือก **local code** (เช่น กทม. vs จังหวัด)
        
    - กำหนด **ambient temperature** (40°C default, บางพื้นที่อาจแตกต่าง)
        
    - Future: เลือก **utility company** (MEA vs PEA)
        
- **ผลกระทบถ้าไม่มี**:
    
    - ใช้ค่า default = "THAILAND_GENERAL"
        
    - อาจไม่ตรงกับข้อบังคับท้องถิ่น (minor)
        
- **RAG ควร**:
    
    - ถามถ้ามีข้อมูล
        
    - ไม่บังคับ แต่แนะนำให้มี
        

## **project_info.floor_area_sqm**

- **ความสำคัญ**: ⭐⭐ (Low-Medium)
    
- **MCP ใช้เพื่อ**:
    
    - Validate จำนวนห้อง (ถ้ามีค่าแปลกๆ จะ warning)
        
    - คำนวณ **power density** (W/sqm) เพื่อตรวจสอบความสมเหตุสมผล
        
- **ผลกระทบถ้าไม่มี**:
    
    - ไม่มี validation → อาจมี input ผิดปกติ
        
- **RAG ควร**:
    
    - ถามถ้ามี แต่ไม่บังคับ
        

---

## **3.3 Electrical System Section**

## **electrical_system.voltage_system**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - ตั้งค่า **base voltage** ใน pandapower network (230V หรือ 400V)
        
    - เลือก **cable rating tables** (วสท. ตาราง 5-20 vs 5-30+)
        
    - กำหนด **breaker type** (1P+N vs 3P+N)
        
    - คำนวณ **current** (I = P / V)
        
- **ผลกระทบถ้าผิด**:
    
    - คำนวณ current ผิด → cable/breaker ทั้งระบบผิด
        
    - Fatal error
        
- **RAG ต้อง**:
    
    - Default = TH_1PH_230V (ถ้า user ไม่ระบุ)
        
    - ถ้า user ขอ 3 เฟส → แจ้งว่ายังไม่เปิดใน demo
        

## **electrical_system.earthing**

- **ความสำคัญ**: ⭐⭐⭐⭐ (High)
    
- **MCP ใช้เพื่อ**:
    
    - กำหนด **grounding scheme** (TT, TN-S, ฯลฯ)
        
    - เลือก **RCD/RCBO requirement** (TT ต้องมี RCD, TN อาจไม่บังคับ)
        
    - คำนวณ **earth fault loop impedance** (future feature)
        
- **ผลกระทบถ้าไม่มี**:
    
    - ใช้ default based on voltage_system
        
    - TH_1PH_230V → TT
        
    - TH_3PH_400V → TN_S
        
- **RAG ควร**:
    
    - ไม่ต้อง force user ระบุ
        
    - แต่ต้องแจ้งให้ user รู้ว่าใช้ default อะไร
        

## **electrical_system.main_supply**

- **ความสำคัญ**: ⭐⭐⭐⭐ (High)
    
- **MCP ใช้เพื่อ**:
    
    - **main_supply.type**: ตอนนี้รองรับแค่ UTILITY_GRID
        
    - **main_supply.rated_current**: กำหนดขนาด **main breaker**
        
        - ถ้ามี → ใช้ค่านี้
            
        - ถ้าไม่มี → คำนวณจาก total load × 1.25 (safety margin) → round up ไปยัง standard size
            
    - **main_supply.phases**: 1 หรือ 3 (ต้องตรง voltage_system)
        
- **ผลกระทบถ้าไม่มี rated_current**:
    
    - MCP คำนวณเอง จากโหลดรวม
        
    - อาจเลือก breaker ใหญ่เกินไป (conservative)
        
- **RAG ควร**:
    
    - ถ้า user รู้ว่าใช้มิเตอร์ขนาดเท่าไหร่ → ให้ระบุ
        
    - ถ้าไม่รู้ → ปล่อยให้ MCP คำนวณ
        

---

## **3.4 Rooms Section**

## **rooms[].room_id**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - เป็น **primary key** สำหรับเชื่อม loads[]
        
    - สร้าง **room object** ใน internal data structure
        
    - ตั้งชื่อ **circuit labels** (เช่น "RM-01-LIGHTING", "RM-02-SOCKET")
        
- **ผลกระทบถ้าผิด/ซ้ำ**:
    
    - ซ้ำ → MCP ไม่รู้ว่าห้องไหนคือห้องไหน → crash
        
    - ไม่มี → loads ไม่รู้ว่าอยู่ห้องไหน → crash
        
- **RAG ต้อง**:
    
    - Generate unique IDs (ใช้ counter หรือ UUID)
        
    - Format: "RM-001", "RM-002", "ROOM_LIVING", ฯลฯ
        

## **rooms[].room_type**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - เลือก **ROOM_TEMPLATE** จาก database
        
    - Template มี:
        
        - typical loads (โคมไฟ, ปลั๊ก, เครื่องใช้)
            
        - circuit requirements (แยกวงจรหรือไม่)
            
        - safety requirements (RCBO, RCD)
            
    - กำหนด **circuit naming convention**
        
- **ผลกระทบถ้าผิด**:
    
    - เลือก template ผิด → วงจรไม่ตรงความต้องการ
        
    - ห้องครัวเป็น template ห้องนอน → ไม่มีวงจรพิเศษสำหรับเตา/ไมโครเวฟ
        
- **RAG ต้อง**:
    
    - Map คำพูดของ user ให้ถูก:
        
        - "ห้องนั่งเล่น" → LIVING_ROOM
            
        - "ห้องนอนใหญ่" → MASTER_BEDROOM
            
        - "ห้องครัว" → KITCHEN
            
        - "ห้องน้ำ" → BATHROOM
            

## **rooms[].template_code**

- **ความสำคัญ**: ⭐⭐⭐⭐ (High)
    
- **MCP ใช้เพื่อ**:
    
    - **ข้าม** ขั้นตอนเดา template จาก room_type
        
    - ใช้ template นี้โดยตรง
        
    - มีประโยชน์เมื่อ:
        
        - user ต้องการ custom behavior (เช่น "ห้องครัวแบบหนัก" vs "ห้องครัวแบบเบา")
            
        - room_type เดียวกันแต่ต้องการ template ต่างกัน
            
- **ผลกระทบถ้ามี**:
    
    - MCP จะใช้ template นี้เลย ไม่เดา
        
    - ถ้า template_code ไม่มีใน DB → error INVALID_TEMPLATE_CODE
        
- **ผลกระทบถ้าไม่มี**:
    
    - MCP เลือก template จาก room_type + ข้อมูล loads ในห้อง
        
    - อาจเลือกไม่ได้ (ถ้า room_type ไม่ชัด) → error MISSING_TEMPLATE
        
- **RAG ควร**:
    
    - ถ้า user ระบุแบบละเอียด (เช่น "ห้องครัวมีเตาไฟฟ้า + ไมโครเวฟ") → ใช้ template_code = "KITCHEN_HEAVY"
        
    - ถ้า user ไม่ละเอียด → ปล่อยว่างให้ MCP เลือก
        

## **rooms[].floor_level**

- **ความสำคัญ**: ⭐⭐⭐ (Medium)
    
- **MCP ใช้เพื่อ**:
    
    - จัดกลุ่ม **circuit distribution** (แยก DB ตามชั้น)
        
    - คำนวณ **cable length** (ถ้ามี vertical distance)
        
    - สร้าง **panel layout** แยกตามชั้น
        
- **ผลกระทบถ้าไม่มี**:
    
    - ถือว่าชั้น 1 ทั้งหมด
        
    - อาจทำให้ cable length estimation ไม่แม่น
        
- **RAG ควร**:
    
    - ถาม user ถ้าเป็นบ้าน 2-3 ชั้น
        
    - ถ้าไม่รู้ → ปล่อยเป็น null หรือ default = 1
        

## **rooms[].area_sqm**

- **ความสำคัญ**: ⭐⭐ (Low)
    
- **MCP ใช้เพื่อ**:
    
    - Validate ความสมเหตุสมผลของโหลด (W/sqm)
        
    - คำนวณ **lighting density** (ถ้ามี future feature)
        
- **ผลกระทบถ้าไม่มี**:
    
    - ไม่มี validation
        
- **RAG ควร**:
    
    - ไม่บังคับ
        

---

## **3.5 Loads Section**

## **loads[].load_id**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - เป็น **primary key** ของโหลด
        
    - ใช้ใน **circuit assignment** (load นี้อยู่วงจรไหน)
        
    - ใช้ใน **BOM** (รายการอุปกรณ์)
        
- **ผลกระทบถ้าผิด/ซ้ำ**:
    
    - ซ้ำ → MCP ไม่รู้ว่าโหลดไหนคือโหลดไหน → crash
        
- **RAG ต้อง**:
    
    - Generate unique IDs
        

## **loads[].room_id**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - **เชื่อมโยง** load เข้ากับ room
        
    - คำนวณ **total load per room**
        
    - จัดกลุ่ม **circuit** ตามห้อง
        
- **ผลกระทบถ้าผิด**:
    
    - room_id ไม่มีใน rooms[] → error INVALID_ROOM_REFERENCE
        
    - โหลดหลุดจากห้อง → ไม่รู้ว่าอยู่ไหน
        
- **RAG ต้อง**:
    
    - ตรวจสอบว่า room_id มีอยู่จริง
        

## **loads[].device_code**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - **Map** ไปยัง DEVICE_CATALOG table:
        
        - `rated_power` (kW)
            
        - `power_factor` (cos φ)
            
        - `load_type` (RESISTIVE, INDUCTIVE, MOTOR)
            
        - `category` (LIGHTING, APPLIANCE, HVAC)
            
    - คำนวณ **apparent power** (kVA) = kW / power_factor
        
    - เลือก **circuit type** (lighting, socket, dedicated)
        
- **ผลกระทบถ้าผิด**:
    
    - device_code ไม่มีใน catalog → error UNKNOWN_DEVICE_CODE
        
    - คำนวณโหลดผิด → cable/breaker ผิด
        
- **RAG ต้อง**:
    
    - แปลงคำอธิบายของ user เป็น device_code ที่ถูกต้อง
        
    - ตัวอย่าง:
        
        - "แอร์ 12000 BTU" → "AC_12000BTU"
            
        - "ปลั๊ก 16A" → "SOCKET_16A"
            
        - "โคมไฟ LED 9W" → "LED_DOWNLIGHT_9W"
            
    - ถ้าแปลงไม่ได้ → ขอข้อมูลเพิ่ม
        

## **loads[].qty**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - คูณกับ `rated_power` จาก catalog
        
    - `total_power = rated_power × qty`
        
- **ผลกระทบถ้าผิด**:
    
    - qty = 0 → โหลดหาย
        
    - qty ติดลบ → error
        
- **RAG ต้อง**:
    
    - qty ≥ 1 เสมอ
        

## **loads[].power_kw**

- **ความสำคัญ**: ⭐⭐⭐⭐ (High)
    
- **MCP ใช้เพื่อ**:
    
    - **Override** ค่า rated_power จาก catalog
        
    - มีประโยชน์เมื่อ:
        
        - user รู้กำลังไฟแน่นอน (เช่น เตาไฟฟ้า 5 kW)
            
        - device_code ใน catalog เป็นค่าเฉลี่ย แต่ user ใช้รุ่นพิเศษ
            
- **ผลกระทบถ้ามี**:
    
    - MCP ใช้ค่านี้แทน catalog
        
- **ผลกระทบถ้าไม่มี**:
    
    - MCP ใช้ค่าจาก catalog[device_code]
        
- **RAG ควร**:
    
    - ถ้า user ระบุกำลังไฟชัดเจน → ใส่ power_kw
        
    - ถ้าไม่ระบุ → ปล่อยว่างให้ MCP ใช้ catalog
        

## **loads[].distance_from_db_m**

- **ความสำคัญ**: ⭐⭐⭐ (Medium)
    
- **MCP ใช้เพื่อ**:
    
    - คำนวณ **voltage drop** (V = I × R, R = ρ × L / A)
        
    - เลือกขนาดสายที่ใหญ่ขึ้นถ้า distance ยาว
        
- **ผลกระทบถ้าไม่มี**:
    
    - ใช้ค่า default = 15m (average distance in typical house)
        
    - อาจไม่แม่นถ้า distance จริงยาวมาก
        
- **RAG ควร**:
    
    - ถ้า user มีแบบสถาปัตย์ → ประมาณระยะ
        
    - ถ้าไม่รู้ → ปล่อยให้ MCP ใช้ default
        

---

## **3.6 Constraints Section**

## **constraints.rule_profile_id**

- **ความสำคัญ**: ⭐⭐⭐⭐⭐ (Critical)
    
- **MCP ใช้เพื่อ**:
    
    - เลือก **ชุดกฎ** ทั้งหมด:
        
        - วสท. 2564 (Thai standard)
            
        - IEC 60364 (International standard)
            
        - Local codes (กรุงเทพ, จังหวัด)
            
    - กำหนด:
        
        - **Demand factor** (ตาราง วสท. บทที่ 2)
            
        - **Cable derating factor** (ตาราง วสท. 5-8)
            
        - **Voltage drop limit** (3% for lighting, 5% for motor)
            
        - **Earth resistance limit** (≤ 5Ω)
            
        - **RCBO requirements** (ห้องน้ำ, ห้องครัว)
            
- **ผลกระทบถ้าผิด**:
    
    - ใช้กฎผิด → อาจไม่ผ่านมาตรฐาน
        
- **RAG ต้อง**:
    
    - Default = "TH_RESIDENTIAL_LV"
        
    - ถ้า user ขอมาตรฐานอื่น → ตรวจสอบว่ามีใน DB
        

## **constraints.user_constraints[]**

- **ความสำคัญ**: ⭐⭐⭐ (Medium-High)
    
- **MCP ใช้เพื่อ**:
    
    - **ปรับแต่ง** พฤติกรรมที่เกินมาตรฐาน
        
    - ตัวอย่าง flags:
        
        - **split_kitchen_circuit: boolean**
            
            - true → แยกวงจรครัว (เตา, ไมโครเวฟ, ตู้เย็น) เป็นวงจรต่างหาก
                
            - false → รวมวงจรเดียว (ถ้าโหลดไม่เกิน)
                
        - **rcd_for_all_outlets: boolean**
            
            - true → ปลั๊กทุกจุดต้องมี RCBO
                
            - false → เฉพาะห้องน้ำ/ครัว (ตามมาตรฐาน)
                
        - **separate_ac_circuits: boolean**
            
            - true → แอร์แต่ละตัวแยกวงจร
                
            - false → อาจรวมได้ (ถ้าโหลดไม่เกิน)
                
        - **emergency_circuits: boolean**
            
            - true → มีวงจรฉุกเฉิน (ไฟสำรอง)
                
            - false → ไม่มี
                
- **ผลกระทบถ้ามี**:
    
    - MCP ปรับพฤติกรรมตาม flags
        
    - จำนวนวงจรอาจเพิ่มขึ้น
        
    - ต้นทุนเพิ่มขึ้น
        
- **ผลกระทบถ้าไม่มี**:
    
    - ใช้พฤติกรรม default ตามมาตรฐาน
        
- **RAG ควร**:
    
    - ถ้า user มีความต้องการพิเศษ → เพิ่ม flags
        
    - ถ้าไม่มี → ปล่อยว่าง
        

---

## **3.7 Field Priority Matrix (ตารางความสำคัญของ Field)**

|Field|Importance|Impact if Wrong|RAG Action|
|---|---|---|---|
|`project_name`|⭐⭐|File naming only|Accept user input|
|`building_type`|⭐⭐⭐⭐⭐|Wrong load calc|Must validate|
|`voltage_system`|⭐⭐⭐⭐⭐|Fatal error|Default to 1PH|
|`earthing`|⭐⭐⭐⭐|Wrong RCD req|Auto-default|
|`room_id`|⭐⭐⭐⭐⭐|Broken references|Must be unique|
|`room_type`|⭐⭐⭐⭐⭐|Wrong template|Must map correctly|
|`template_code`|⭐⭐⭐⭐|Wrong behavior|Optional but powerful|
|`device_code`|⭐⭐⭐⭐⭐|Wrong load calc|Must map or ask|
|`qty`|⭐⭐⭐⭐⭐|Wrong total load|Must be ≥ 1|
|`power_kw`|⭐⭐⭐⭐|Override catalog|Optional override|
|`rule_profile_id`|⭐⭐⭐⭐⭐|Wrong standards|Default = TH_RES|

## **3.8 RAG Decision Trees (ต้นไม้การตัดสินใจ)**

## **Tree 1: When to Ask User vs Auto-Fill**

Field missing?
├─ Critical field (⭐⭐⭐⭐⭐)?
│  ├─ Can auto-generate? (e.g. room_id)
│  │  └─ YES → Auto-generate
│  └─ Can't auto-generate? (e.g. room_type)
│     └─ NO → ASK USER
│
└─ Non-critical field (⭐⭐⭐ or less)?
   ├─ Has default value?
   │  └─ YES → Use default
   └─ No default?
      └─ SKIP (optional)
## **Tree 2: When to Map vs Ask**
User input unclear?
├─ Can map with high confidence? (>80%)
│  └─ YES → Map automatically + inform user
│
├─ Can map with medium confidence? (50-80%)
│  └─ YES → Map + ask for confirmation
│
└─ Can't map? (<50%)
   └─ NO → ASK USER for clarification
## **Tree 3: When to Error vs Warning vs Ignore**
Invalid value detected?
├─ Critical field?
│  └─ YES → ERROR (block spec generation)
│
├─ High impact field?
│  └─ YES → WARNING (proceed with caution)
│
└─ Low impact field?
   └─ YES → IGNORE or INFO (no impact)
## **3.9 Common Pitfalls & How to Avoid**

## **Pitfall 1: ใส่ device_code ที่ไม่มีใน catalog**

❌ Bad:
loads: [
  {device_code: "my_custom_load", power_kw: 2.5}
]

✅ Good:
loads: [
  {device_code: "APPLIANCE_2500W", power_kw: 2.5}
]
หรือ
✅ Better: RAG แปลงก่อน
User: "เตาไฟฟ้า 2.5 kW"
RAG maps to: device_code = "ELECTRIC_STOVE_2500W"

## **Pitfall 2: room_id ไม่ตรงระหว่าง rooms[] กับ loads[]**
❌ Bad:
rooms: [{room_id: "RM-01"}]
loads: [{room_id: "ROOM-01"}] // ไม่ตรงกัน

✅ Good:
rooms: [{room_id: "RM-01"}]
loads: [{room_id: "RM-01"}] // ตรงกัน

## **Pitfall 3: building_type vs floor_level ขัดแย้ง**

❌ Bad:
building_type: "RESIDENTIAL_SINGLE_1F"
rooms: [
  {floor_level: 2} // ขัดแย้ง
]

✅ Good:
building_type: "RESIDENTIAL_SINGLE_2F"
rooms: [
  {floor_level: 1},
  {floor_level: 2}
]

## **Pitfall 4: โหลดรวมเกินขีดจำกัดแต่ไม่เตือน**

❌ Bad:
// Total = 50 kVA (เกิน 35 kVA)
→ RAG ส่งให้ MCP เลย
→ MCP error

✅ Good:
// RAG คำนวณโหลดรวมก่อน
if total > 35 kVA:
  warn_user("โหลดเกิน 35 kVA แนะนำแบ่ง MDB")
