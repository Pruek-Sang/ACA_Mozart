### 2.1 การดูว่าอุปกรณ์ต้องใช้วงจรแยกหรือไม่

- ใช้ field `requires_dedicated_circuit` จาก kind `APPLIANCE`
    
- ใช้ร่วมกับ `CIRCUIT_TEMPLATE.dedicated_circuit`
    

**Contract:**

- ถ้า `APPLIANCE.requires_dedicated_circuit == true`  
    → MCP ต้อง map โหลดนั้นกับวงจรที่ `CIRCUIT_TEMPLATE.dedicated_circuit == true`
    
- ถ้า `requires_dedicated_circuit == false`  
    → MCP สามารถจัดรวมกับวงจรทั่วไปได้ (ภายใต้กฎโหลดและจำนวนเต้ารับ)
    

### 2.2 การคำนวณโหลดและกระแสเริ่มต้น

- ใช้ `power_w`, `running_current_a`, `startup_current_a`, `usage_hours_per_day`  
    จาก `APPLIANCE`
    
- ใช้ `current_rating_a`, `power_rating_w` จาก `COMPONENT`
    
- Logic การคำนวณโหลด / demand factor / diversity factor  
    ถูกอิมพลีเมนต์ใน MCP Core v2.0, ไม่อยู่ใน RAG
    

**Contract:**

- MCP ต้องถือว่า **ค่าเหล่านี้มาจาก catalog เป็นแหล่งจริง**
    
- ถ้าต้องเปลี่ยนตัวเลข → ทำผ่านการแก้ seed ที่ `amadeus.catalog` เท่านั้น
    

### 2.3 การเชื่อมกับมาตรฐาน

- Field `standard_reference` ในแต่ละ kind (เช่น CABLE_SPEC, COMPONENT, VALIDATION_RULE)  
    ชี้ไปยังมาตรฐานที่ใช้อ้างอิง เช่น มอก. หรือ IEC
    
- ใช้เพื่อ:
    
    - แสดงใน report
        
    - ให้ RAG ใช้อ้างอิงตอนตรวจ compliance เพิ่มเติม
        

---

## 3. Logic เฉพาะแบรนด์/รุ่น (สถานะปัจจุบัน)

> เอกสารนี้ตั้งใจให้เป็นที่รวม “ข้อบังคับด้าน brand/model”  
> ที่เกินจากข้อมูลโหลด / พิกัดมาตรฐานปกติ

จากข้อมูลใน DB ปัจจุบัน:

- ตาราง APPLIANCE และ COMPONENT มี field `brand`, `model`, `price_thb` แล้ว
    
- แต่ยัง **ไม่มี rule กลาง** ที่บังคับว่า
    
    - โปรเจกต์หนึ่งต้องใช้ยี่ห้อเดียวกันทุกชิ้น
        
    - หรืออุปกรณ์บางชนิดต้องใช้เฉพาะยี่ห้อใด
        

ดังนั้น **สถานะเริ่มต้น**:

1. `brand` / `model` ใช้เพื่อ:
    
    - แสดงใน Bill of Materials / BOM
        
    - ผูกกับข้อมูลราคา (จากไฟล์ seed)
        
2. การเลือกใช้รุ่นไหน
    
    - อยู่ที่ layer MCP / Tool ภายนอก (เช่น UI ให้ผู้ใช้เลือก)
        
    - หากจะมีกติกาพิเศษ เช่น
        
        - “งานโครงการประเภท A ต้องใช้เฉพาะ Samsung”
            
        - “งานห้องนอนต้องใช้พัดลม Hatari เท่านั้น”
            
    - ให้บันทึก rule เหล่านั้นเพิ่มในไฟล์นี้ (เวอร์ชันถัดไป)
        

---

## 4. แนวทางการใช้งานโดย MCP

1. ดึงข้อมูลจาก
    
    - `amadeus.v_appliances` (เมื่อมี)
        
    - หรือดึงตรงจาก `amadeus.catalog` where `kind = 'APPLIANCE'`
        
2. Map โหลดจาก `ProjectInputSpec` → `appliance_id` / `component` code
    
3. ใช้ field:
    
    - `requires_dedicated_circuit` → ตัดสินใจว่าจะใช้ circuit template แบบ dedicated หรือไม่
        
    - `power_w`, `startup_current_a` → กำหนดโหลดที่ส่งเข้า pandapower
        
    - `brand`, `model`, `price_thb` → สร้าง BOM และ report
        

---

## 5. สิ่งที่คาดหวังจากไฟล์นี้

- ให้ dev ทุกคนรู้ว่าตัวเลขใน APPLIANCE/COMPONENT “ถูกใช้ยังไง”
    
- ถ้ามี policy ด้าน brand/model เพิ่ม → เขียนต่อยอดในเอกสารนี้  
    แทนการฝังไว้ในโค้ดแบบกระจัดกระจาย
