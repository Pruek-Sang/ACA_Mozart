## **4.1 Error Classification (การจำแนกประเภท Error)**

## **Error Levels**

- **FATAL**: MCP ไม่สามารถดำเนินการต่อได้ → ต้องแก้ไข spec
    
- **ERROR**: คำนวณไม่สำเร็จ → ต้องปรับ spec หรือข้อมูล
    
- **WARNING**: คำนวณสำเร็จแต่มีข้อสังเกต → ควรตรวจสอบ
    
- **INFO**: ข้อมูลทั่วไป → ไม่ต้องแก้ไข
    

---

## **4.2 Structural Errors (ข้อผิดพลาดโครงสร้าง)**

## **Error: INVALID_SPEC_STRUCTURE**

- **Error Code**: `MCP_ERR_001`
    
- **Level**: FATAL
    
- **สาเหตุ**:
    
    - ProjectInputSpec ไม่มี section ที่จำเป็น
        
    - ตัวอย่าง: ขาด `rooms[]`, `loads[]`, `electrical_system`
        
- **MCP Message**:
    
    text
    
    `"Invalid ProjectInputSpec structure: missing required section '{section_name}'"`
    
- **RAG ควรทำ**:
    
    1. ตรวจสอบ spec ก่อนส่งให้ MCP (validation)
        
    2. แจ้ง user:
        
        text
        
        `"ข้อมูลโครงการยังไม่สมบูรณ์ - ขาดข้อมูล: {section_name} - กรุณาให้ข้อมูลเพิ่มเติมเกี่ยวกับ {description}"`
        
    3. ขอข้อมูลเพิ่มแล้ว regenerate spec
        
- **ตัวอย่าง**:
    
    text
    
    `User: "ออกแบบบ้าน" RAG: (ยังไม่มีข้อมูลห้อง) → ไม่ส่งให้ MCP → "กรุณาบอกว่าบ้านมีห้องอะไรบ้าง เช่น ห้องนั่งเล่น ห้องนอน ห้องครัว"`
    

---

## **Error: EMPTY_ROOMS_ARRAY**

- **Error Code**: `MCP_ERR_002`
    
- **Level**: FATAL
    
- **สาเหตุ**:
    
    - `rooms[]` เป็น array ว่าง `[]`
        
- **MCP Message**:
    
    text
    
    `"ProjectInputSpec must contain at least 1 room"`
    
- **RAG ควรทำ**:
    
    1. ตรวจสอบก่อนส่ง
        
    2. แจ้ง user:
        
        text
        
        `"ยังไม่มีข้อมูลห้อง กรุณาบอกว่าบ้านมีห้องอะไรบ้าง"`
        
    3. รอข้อมูลแล้วสร้าง spec ใหม่
        

---

## **Error: EMPTY_LOADS_ARRAY**

- **Error Code**: `MCP_ERR_003`
    
- **Level**: FATAL
    
- **สาเหตุ**:
    
    - `loads[]` เป็น array ว่าง `[]`
        
- **MCP Message**:
    
    text
    
    `"ProjectInputSpec must contain at least 1 load"`
    
- **RAG ควรทำ**:
    
    1. ตรวจสอบก่อนส่ง
        
    2. แจ้ง user:
        
        text
        
        `"ยังไม่มีข้อมูลอุปกรณ์ไฟฟ้า กรุณาบอกว่าในแต่ละห้องมีอุปกรณ์อะไรบ้าง เช่น แอร์ โคมไฟ ปลั๊ก"`
        

---

## **Error: DUPLICATE_ID**

- **Error Code**: `MCP_ERR_004`
    
- **Level**: FATAL
    
- **สาเหตุ**:
    
    - `room_id` หรือ `load_id` ซ้ำกัน
        
- **MCP Message**:
    
    text
    
    `"Duplicate {id_type}: '{id_value}' found in array"`
    
- **RAG ควรทำ**:
    
    1. **ไม่ควรเกิด** → RAG ต้อง generate unique IDs
        
    2. ถ้าเกิด:
        
        python
        
        `# Auto-fix: regenerate IDs for i, room in enumerate(rooms):     room['room_id'] = f"RM-{i+1:03d}"`
        
    3. แจ้ง user (ถ้าจำเป็น):
        
        text
        
        `"ระบบตรวจพบ ID ซ้ำ กำลังแก้ไขอัตโนมัติ..."`
        

---

## **4.3 Reference Errors (ข้อผิดพลาดการอ้างอิง)**

## **Error: INVALID_ROOM_REFERENCE**

- **Error Code**: `MCP_ERR_101`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - `loads[].room_id` อ้างอิงไปยัง room ที่ไม่มีอยู่
        
- **MCP Message**:
    
    text
    
    `"Load '{load_id}' references non-existent room '{room_id}'"`
    
- **RAG ควรทำ**:
    
    1. **ไม่ควรเกิด** → RAG ต้องตรวจสอบก่อนส่ง
        
    2. ถ้าเกิด:
        
        python
        
        `# Validate references valid_room_ids = {r['room_id'] for r in rooms} for load in loads:     if load['room_id'] not in valid_room_ids:        # Error: ต้องแก้ไข        ask_user(f"โหลด {load['load_id']} อยู่ห้องไหน?")`
        
    3. แจ้ง user:
        
        text
        
        `"พบข้อผิดพลาด: โหลด '{load_name}' ไม่ได้ระบุว่าอยู่ห้องไหน กรุณาระบุห้องสำหรับอุปกรณ์นี้"`
        

---

## **Error: UNKNOWN_DEVICE_CODE**

- **Error Code**: `MCP_ERR_102`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - `loads[].device_code` ไม่มีใน DEVICE_CATALOG
        
- **MCP Message**:
    
    text
    
    `"Unknown device_code: '{device_code}' not found in catalog"`
    
- **RAG ควรทำ (Multi-step Recovery)**:
    
    **Step 1: พยายามแปลง (Semantic Mapping)**
    
    python
    
    `user_input = "เตาไฟฟ้า 2.5 kW" # RAG tries to map semantic_code = map_to_catalog(user_input) # → "ELECTRIC_STOVE_2500W" if semantic_code found:     update_spec(device_code=semantic_code)    inform_user(f"แปลง '{user_input}' เป็น '{semantic_code}'")    retry_mcp() else:     goto Step 2`
    
    **Step 2: ขอข้อมูลเพิ่ม**
    
    text
    
    `"ไม่พบอุปกรณ์ '{device_code}' ในระบบ กรุณาอธิบายเพิ่มเติม: - ประเภท: (แอร์ / ปลั๊ก / โคมไฟ / เครื่องใช้ / อื่นๆ) - กำลังไฟ: (BTU / Watt / Ampere) - การใช้งาน: (ทั่วไป / พิเศษ)"`
    
    **Step 3: สร้าง Generic Load**
    
    python
    
    `# Last resort: ถ้า user ให้ power มา if power_kw provided:     use device_code = "GENERIC_LOAD"    set power_kw = user_value    warn_user("ใช้โหลดทั่วไป อาจไม่แม่นยำ 100%")    retry_mcp()`
    

---

## **Error: INVALID_TEMPLATE_CODE**

- **Error Code**: `MCP_ERR_103`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - `rooms[].template_code` ไม่มีใน ROOM_TEMPLATE table
        
- **MCP Message**:
    
    text
    
    `"Room '{room_id}': template_code '{template_code}' not found"`
    
- **RAG ควรทำ**:
    
    1. **ไม่ควรใส่ template_code ที่ไม่มี** → RAG ควรเลือกจาก catalog
        
    2. ถ้าเกิด:
        
        python
        
        `# Fallback: ใช้ room_type เลือก template แทน remove template_code let MCP select from room_type retry_mcp()`
        
    3. แจ้ง user:
        
        text
        
        `"ระบบไม่พบ template ที่ระบุ กำลังใช้ template มาตรฐานสำหรับห้องประเภทนี้แทน"`
        

---

## **Error: MISSING_ROOM_TEMPLATE**

- **Error Code**: `MCP_ERR_104`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - ห้องไม่มี `template_code`
        
    - MCP ไม่สามารถเลือก template จาก `room_type` ได้
        
    - เกิดเมื่อ room_type ไม่ชัดเจน หรือ loads ในห้องไม่เพียงพอ
        
- **MCP Message**:
    
    text
    
    `"Room '{room_id}': unable to determine template from room_type '{room_type}'"`
    
- **RAG ควรทำ**:
    
    1. ขอข้อมูลเพิ่มจาก user:
        
        text
        
        `"ไม่สามารถกำหนดประเภทห้อง '{room_name}' ได้ กรุณาระบุให้ชัดเจนว่าเป็นห้องประเภทไหน: - ห้องนั่งเล่น (Living Room) - ห้องนอนหลัก (Master Bedroom) - ห้องนอนเด็ก (Children Bedroom) - ห้องครัวแบบหนัก (Heavy Kitchen) - ห้องครัวแบบเบา (Light Kitchen) - ห้องน้ำ (Bathroom)"`
        
    2. รอคำตอบแล้ว update spec
        
    3. Retry MCP
        

---

## **Error: INVALID_RULE_PROFILE**

- **Error Code**: `MCP_ERR_105`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - `constraints.rule_profile_id` ไม่มีใน RULE_PROFILE table
        
- **MCP Message**:
    
    text
    
    `"Unknown rule_profile_id: '{rule_profile_id}'"`
    
- **RAG ควรทำ**:
    
    1. **ไม่ควรเกิด** → RAG ควรใช้ default = "TH_RESIDENTIAL_LV"
        
    2. ถ้าเกิด:
        
        python
        
        `# Auto-fix: use default spec.constraints.rule_profile_id = "TH_RESIDENTIAL_LV" warn_user("ใช้ rule profile มาตรฐาน") retry_mcp()`
        

---

## **4.4 Calculation Errors (ข้อผิดพลาดการคำนวณ)**

## **Error: POWER_FLOW_NOT_CONVERGED**

- **Error Code**: `MCP_ERR_201`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - การคำนวณ power flow ใน pandapower ไม่ converge
        
    - เกิดเมื่อ:
        
        - โหลดเกินเกินไป
            
        - Network topology ผิดปกติ
            
        - ค่าพารามิเตอร์ไม่สมเหตุสมผล
            
- **MCP Message**:
    
    text
    
    `"Power flow calculation did not converge"`
    
- **RAG ควรทำ**:
    
    **Step 1: วินิจฉัยสาเหตุ**
    
    text
    
    `สาเหตุที่เป็นไปได้: 1. โหลดรวมเกิน 35 kVA? 2. มีโหลดแต่ละตัวที่มีค่า power_kw ผิดปกติ (เช่น > 20 kW)? 3. มี room ที่มีโหลดเยอะมากผิดปกติ?`
    
    **Step 2: แนะนำแก้ไข**
    
    text
    
    `"การคำนวณไม่สำเร็จ อาจเกิดจาก: 1. โหลดรวมเกินขีดจำกัด (> 35 kVA)    → แนะนำ: แบ่งเป็นหลาย MDB หรือใช้ระบบ 3 เฟส 2. มีโหลดที่มีค่ากำลังไฟสูงผิดปกติ    → แนะนำ: ตรวจสอบค่า power_kw ของแต่ละโหลด 3. Spec มีข้อมูลที่ขัดแย้งกัน    → แนะนำ: ตรวจสอบความสมเหตุสมผลของข้อมูล"`
    
    **Step 3: เสนอทางเลือก**
    
    text
    
    `"ต้องการให้ช่วยแก้ไขหรือไม่? 1. ลดโหลดบางส่วน 2. แบ่งโปรเจกต์เป็นหลาย MDB 3. ตรวจสอบข้อมูลใหม่ทั้งหมด"`
    

---

## **Error: VOLTAGE_DROP_EXCEEDED**

- **Error Code**: `MCP_ERR_202`
    
- **Level**: WARNING (ไม่ block แต่แจ้งเตือน)
    
- **สาเหตุ**:
    
    - Voltage drop บางวงจรเกิน 3% (lighting) หรือ 5% (motor)
        
- **MCP Message**:
    
    text
    
    `"Circuit '{circuit_id}': voltage drop {value}% exceeds limit {limit}%"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"คำเตือน: วงจร '{circuit_name}' มีแรงดันตก {value}% เกินมาตรฐาน {limit}% สาเหตุ: - ระยะทางจาก DB ไปยังโหลด: {distance} เมตร (ยาวเกินไป) - ขนาดสาย: {cable_size} sq.mm (เล็กเกินไป) แนะนำแก้ไข: 1. ใช้สายขนาดใหญ่ขึ้น (เช่น {suggested_size} sq.mm) 2. ย้าย DB ให้ใกล้โหลดมากขึ้น 3. แบ่งวงจรเป็นหลายวงจร"`
        
    2. MCP สามารถคำนวณต่อได้ แต่ผลอาจไม่ผ่านมาตรฐาน
        

---

## **Error: LOAD_EXCEEDS_LIMIT**

- **Error Code**: `MCP_ERR_203`
    
- **Level**: WARNING
    
- **สาเหตุ**:
    
    - โหลดรวมในวงจรเดียวเกิน 80% ของ breaker rating
        
- **MCP Message**:
    
    text
    
    `"Circuit '{circuit_id}': load {load_A}A exceeds 80% of breaker rating {breaker_A}A"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"วงจร '{circuit_name}' มีโหลดใกล้เต็ม: - โหลด: {load_A}A - Breaker: {breaker_A}A - ใช้งานอยู่ที่: {percentage}% แนะนำ: - ย้ายโหลดบางส่วนไปวงจรอื่น - เพิ่มวงจรใหม่สำหรับโหลดนี้"`
        

---

## **4.5 Data Quality Errors (ข้อผิดพลาดคุณภาพข้อมูล)**

## **Error: UNREALISTIC_POWER_VALUE**

- **Error Code**: `MCP_ERR_301`
    
- **Level**: WARNING
    
- **สาเหตุ**:
    
    - `loads[].power_kw` มีค่าผิดปกติ (เช่น < 0.01 kW หรือ > 100 kW)
        
- **MCP Message**:
    
    text
    
    `"Load '{load_id}': power_kw {value} seems unrealistic"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"โหลด '{load_name}' มีค่ากำลังไฟผิดปกติ: {value} kW กรุณาตรวจสอบ: - ถ้าเป็น Watt → แปลงเป็น kW (หาร 1000) - ถ้าเป็น BTU (แอร์) → แปลงเป็น kW (1 BTU/h ≈ 0.293 W) - ถ้าเป็น Ampere → คูณด้วย Voltage (230V)"`
        
    2. รอการแก้ไข
        

---

## **Error: TOO_MANY_ROOMS**

- **Error Code**: `MCP_ERR_302`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - จำนวนห้อง > 35
        
- **MCP Message**:
    
    text
    
    `"Number of rooms {count} exceeds maximum limit 35"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"โปรเจกต์มีห้องมากเกินไป: {count} ห้อง MCP รองรับสูงสุด 35 ห้อง แนะนำ: 1. แบ่งโปรเจกต์เป็นหลาง MDB (เช่น MDB1 = ชั้น 1, MDB2 = ชั้น 2-3) 2. รวมห้องที่มีลักษณะคล้ายกัน (เช่น ห้องเก็บของ + ห้องซักผ้า) 3. ปรึกษาวิศวกรสำหรับโครงการขนาดใหญ่"`
        

---

## **Error: TOO_MANY_CIRCUITS**

- **Error Code**: `MCP_ERR_303`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - จำนวนวงจรที่คำนวณได้ > 50
        
- **MCP Message**:
    
    text
    
    `"Calculated circuit count {count} exceeds maximum limit 50"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"จำนวนวงจรมากเกินไป: {count} วงจร MCP รองรับสูงสุด 50 วงจร สาเหตุ: - โหลดกระจายมากเกินไป - แยกวงจรมากเกินไป (over-design) แนะนำ: 1. รวมวงจรที่เป็นโหลดเดียวกัน (เช่น โคมไฟหลายดวงในห้องเดียวกัน) 2. ใช้ panelboard ขนาดใหญ่ขึ้น 3. แบ่งเป็นหลาย MDB"`
        

---

## **Error: TOTAL_LOAD_EXCEEDED**

- **Error Code**: `MCP_ERR_304`
    
- **Level**: ERROR
    
- **สาเหตุ**:
    
    - โหลดรวม > 35 kVA
        
- **MCP Message**:
    
    text
    
    `"Total apparent power {total_kva} kVA exceeds maximum limit 35 kVA"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"โหลดรวมเกินขีดจำกัด: {total_kva} kVA (สูงสุด 35 kVA) สาเหตุ: - บ้านมีเครื่องใช้ไฟฟ้าเยอะมาก - มีแอร์หลายตัว - มีเครื่องใช้กำลังสูง (เช่น เตาไฟฟ้า, เครื่องทำน้ำอุ่น) แนะนำ: 1. ใช้ระบบ 3 เฟส 400V (รองรับโหลดได้มากขึ้น) 2. แบ่ง MDB เป็นหลายตู้ (เช่น MDB1 = ชั้น 1, MDB2 = ชั้น 2) 3. ลดโหลดบางส่วน หรือใช้อุปกรณ์ประหยัดไฟมากขึ้น"`
        

---

## **4.6 Constraint Errors (ข้อผิดพลาดข้อจำกัด)**

## **Error: UNSUPPORTED_CONSTRAINT**

- **Error Code**: `MCP_ERR_401`
    
- **Level**: WARNING
    
- **สาเหตุ**:
    
    - `user_constraints[]` มี flag ที่ MCP ยังไม่รองรับ
        
- **MCP Message**:
    
    text
    
    `"Unsupported constraint flag: '{flag_name}'"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"ข้อจำกัด '{flag_name}' ยังไม่รองรับในเวอร์ชันนี้ MCP จะดำเนินการโดยไม่คำนึงถึงข้อจำกัดนี้"`
        
    2. Remove flag แล้ว retry
        

---

## **Error: CONFLICTING_CONSTRAINTS**

- **Error Code**: `MCP_ERR_402`
    
- **Level**: WARNING
    
- **สาเหตุ**:
    
    - user_constraints มี flags ที่ขัดแย้งกัน
        
    - ตัวอย่าง:
        
        - `split_kitchen_circuit: true` + `minimize_circuits: true`
            
- **MCP Message**:
    
    text
    
    `"Conflicting constraints: '{flag1}' and '{flag2}'"`
    
- **RAG ควรทำ**:
    
    1. แจ้ง user:
        
        text
        
        `"พบข้อกำหนดที่ขัดแย้งกัน: - '{flag1_description}' - '{flag2_description}' กรุณาเลือกว่าต้องการ: 1. {option1} 2. {option2}"`
        
    2. รอคำตอบแล้ว update spec
        

---

## **4.7 Error Recovery Strategy (กลยุทธ์การแก้ไข Error)**
MCP Error Received
    ↓
1. Classify Error (FATAL/ERROR/WARNING/INFO)
    ↓
2. FATAL/ERROR?
    ├─ YES → Cannot proceed
    │   ├─ Try Auto-Fix (if possible)
    │   │   ├─ Success → Retry MCP
    │   │   └─ Fail → Ask User
    │   └─ Wait for User Input → Update Spec → Retry MCP
    │
    └─ WARNING/INFO?
        └─ Inform User + Proceed

## **Auto-Fix Examples**
# Fix 1: Add missing default values
if not spec.electrical_system.earthing:
    spec.electrical_system.earthing = "TT"
    retry_mcp()

# Fix 2: Generate missing IDs
for i, room in enumerate(spec.rooms):
    if not room.room_id:
        room.room_id = f"RM-{i+1:03d}"
retry_mcp()

# Fix 3: Remove invalid constraint
if unsupported_flag in spec.constraints.user_constraints:
    remove(unsupported_flag)
    warn_user(f"ลบ constraint '{flag}' ที่ไม่รองรับ")
    retry_mcp()

# Fix 4: Map unknown device code
unknown_code = "my_custom_ac"
semantic_code = fuzzy_match(unknown_code, catalog)
if semantic_code:
    replace(unknown_code, semantic_code)
    inform_user(f"แปลง '{unknown_code}' → '{semantic_code}'")
    retry_mcp()

## **4.8 Error Message Templates (แม่แบบข้อความ Error)**

## **Template 1: Structural Error**

text

`"❌ ข้อมูลโครงการไม่สมบูรณ์ ปัญหา: - {error_description} สาเหตุ: - {cause} การแก้ไข: {solution_steps} กรุณาให้ข้อมูลเพิ่มเติม: {prompt}"`

## **Template 2: Calculation Error**

text

`"⚠️ การคำนวณไม่สำเร็จ สาเหตุที่เป็นไปได้: 1. {possible_cause_1} 2. {possible_cause_2} 3. {possible_cause_3} แนะนำ: - {suggestion_1} - {suggestion_2} ต้องการให้ช่วยแก้ไขหรือไม่?"`

## **Template 3: Data Quality Warning**

text

`"⚡ คำเตือน: พบข้อมูลผิดปกติ รายละเอียด: - {detail} แนะนำให้ตรวจสอบ: - {check_1} - {check_2} กรุณายืนยันหรือแก้ไขข้อมูล"`

---

## **4.9 Future Error Handling (การจัดการ Error ในอนาคต)**

## **Planned Features**

- ✅ **Smart Auto-Fix**: ใช้ AI แก้ error อัตโนมัติ
    
- ✅ **Error Analytics**: วิเคราะห์ error ที่เกิดบ่อย
    
- ✅ **Progressive Recovery**: ลอง fix แบบ step-by-step
    
- ✅ **User Feedback Loop**: เรียนรู้จากการแก้ไขของ user