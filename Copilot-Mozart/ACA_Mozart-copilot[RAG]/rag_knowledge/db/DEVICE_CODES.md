<!-- rag_knowledge/db/DEVICE_CODES.md -->

# 📦 Device & Appliance Codes (จาก amadeus.catalog)

เอกสารนี้สรุป code ของอุปกรณ์ไฟฟ้าและโหลดที่สำคัญสำหรับ ACA_Mozart / MCP / RAG  
โดยดึงมาจากตาราง `amadeus.catalog` (kind = `APPLIANCE`, `COMPONENT`, `DEVICE_PROFILE`)

RAG ใช้ข้อมูลชุดนี้เพื่อ:
- แปลงคำอธิบายภาษาคน เช่น "ใส่แอร์ตามห้องนอนทุกห้อง"
  → `device_code` ใน `ProjectInputSpec.loads[*].device_code`
- อ้างอิงชื่ออุปกรณ์ให้ตรงกับ catalog (ไม่สร้าง code แปลกเอง)

MCP ใช้ code เหล่านี้ต่อในการ:
- map ไปยังค่าทางไฟฟ้าจริง (กำลังไฟฟ้า, duty, การเลือกวงจร, ขนาดสาย) จาก field ภายใน `data`
- map ไปยัง block/สัญลักษณ์ใน CAD จาก field เช่น `block_name`, `layer_out`

---

## 1. APPLIANCE (โหลดประเภทเครื่องใช้ไฟฟ้า)

> มาจาก `amadeus.catalog` ที่ kind = `APPLIANCE`  
> ใช้เป็น candidate หลักของ `ProjectInputSpec.loads[*].device_code`

| Code (name)                 | Description                      |
|----------------------------|----------------------------------|
| `APP001-TV-55IN`           | โทรทัศน์ LED 55 นิ้ว            |
| `APP002-FRIDGE-2DOOR`      | ตู้เย็น 2 ประตู 10 คิว           |
| `APP003-MICROWAVE-20L`     | ไมโครเวฟ 20 ลิตร                 |
| `APP004-AIR-9000BTU`       | เครื่องปรับอากาศ 9,000 BTU       |
| `APP005-WASHER-8KG`        | เครื่องซักผ้า 8 กิโลกรัม         |
| `APP006-WATER-HEATER-4_5KW`| เครื่องทำน้ำอุ่น 4.5 kW         |
| `APP007-RICE-COOKER-1L`    | หม้อหุงข้าว 1 ลิตร              |
| `APP008-KETTLE-1_7L`       | กาต้มน้ำไฟฟ้า 1.7 ลิตร          |
| `APP009-PC-GAMING`         | ชุดคอมพิวเตอร์เล่นเกม           |
| `APP010-HAIR-DRYER-2000W`  | ไดร์เป่าผม 2,000 W              |
| `APP011-PUMP-1HP`          | ปั๊มน้ำ 1 HP                      |
| `APP012-WASHER-8KG`        | เครื่องซักผ้า 8 kg               |
| `APP013-DRYER-4000W`       | เครื่องอบผ้า 4,000W              |

> หมายเหตุ: รายละเอียดเชิงไฟฟ้า เช่น `typical_power_w`, `recommended_wire_size_mm2` อยู่ใน field `data` ของ catalog  
> RAG ไม่ต้องจำตัวเลข แค่ต้องใช้ code ให้ถูกตัว

---

## 2. COMPONENT (อุปกรณ์/ชิ้นส่วนในระบบไฟฟ้า และ block CAD)

> มาจาก `amadeus.catalog` ที่ kind = `COMPONENT`  
> ใช้สำหรับ mapping ไปยัง block CAD และ logic ของ MCP

| Code (name)                 | Description                           |
|----------------------------|---------------------------------------|
| `COMP-EXHAUST-25W`         | Exhaust fan 25 W                      |
| `COMP-MAIN-MCB`            | Main breaker 100A                     |
| `COMP-SPD`                 | Surge protector (SPD)                 |
| `COMP-HANDY-BOX`           | Handy box (flush)                     |
| `COMP-SURFACE-BOX`         | Surface box                           |
| `COMP-GROUND-ROD`          | Ground rod                            |
| `COMP-KWH-METER`           | KWh meter (utility)                   |
| `COMP-LOAD-CENTER`         | Load center / Consumer unit           |
| `COMP-OUTLET-16A`          | เต้ารับ 2 ช่อง 16A                   |
| `COMP-OUTLET-20A-SINGLE`   | Single outlet 20A (dedicated)         |
| `COMP-OUTLET-WATERPROOF`   | เต้ารับกันน้ำ IP65                   |
| `COMP-OUTLET-WP`           | Weatherproof outlet (IP54)            |
| `COMP-OUTLET-TV`           | TV outlet (coax)                      |
| `COMP-OUTLET-RJ45`         | LAN outlet (RJ45)                     |
| `COMP-CEILING-FAN-60W`     | Ceiling fan 60 W                      |
| `COMP-DOWNLIGHT-9W`        | โคมไฟดาวน์ไลท์ LED 9W               |
| `COMP-CEILING-24W`         | โคมไฟดาวน์ไลท์ LED 24W              |
| `COMP-DOORBELL`            | Doorbell                              |
| `COMP-SW-1WAY`             | Light switch 1-way                    |
| `COMP-SW-2WAY`             | Light switch 2-way                    |
| `COMP-EMT-1/2IN`           | Conduit EMT 1/2" path element         |
| `COMP-GATE-MOTOR`          | Gate motor                            |
| `COMP-AC-12000BTU`         | Air conditioner ~1.1 kW               |
| `COMP-INDUCTION-3.5kW`     | Induction hob 3.5 kW                  |
| `COMP-PUMP-750W`           | Water pump 0.75 kW                    |
| `COMP-OVEN-3.0kW`          | Electric oven 3.0 kW                  |
| `COMP-BOX-JUNCTION`        | Junction box (ceiling)                |
| `COMP-BOX-HANDY`           | Handy box (wall)                      |
| `COMP-SW-DIMMER`           | Dimmer (light control)                |

> รายละเอียดเช่น `tags`, `layer_out`, `mount_height_mm`, `block_name` อยู่ใน `data` ให้ MCP ใช้ตอนสร้าง CAD

---

## 3. DEVICE_PROFILE

> โปรไฟล์ device พิเศษ ที่ใช้เพิ่มกติกาเฉพาะโหลดบางชนิด

| Code (name)               | Description                 |
|--------------------------|-----------------------------|
| `DEV-REFRIGERATOR-01`    | Refrigerator 2-door profile |

ภายใน `data` จะเก็บ:
- `device_id` (เช่น `refrigerator_01`)
- ข้อกำหนดการติดตั้ง เช่น ระยะเผื่อช่องว่าง, เงื่อนไข outlet เฉพาะทาง ฯลฯ

RAG ใช้แค่ **รู้ว่ามีโปรไฟล์นี้** และถ้ามีการอ้างอิงถึงตู้เย็นแบบพิเศษ  
ให้ map ไปใช้ `device_code = "DEV-REFRIGERATOR-01"` แทนการมั่ว code ใหม่

---

## 4. ข้อกำหนดการใช้โดย RAG

1. ห้ามสร้าง `device_code` ใหม่เอง ถ้าไม่มีในรายการนี้ ต้อง:
   - แจ้งว่าอยู่นอกขอบเขต
   - หรือ map ไปยัง code ที่ใกล้เคียงอย่างชัดเจน พร้อมอธิบาย
2. เวลาเขียน `ProjectInputSpec.loads[*]`:
   - `device_code` ต้องมาจากตารางนี้เท่านั้น
   - การเลือกขนาดสาย, รูปแบบวงจร ให้ MCP เป็นคนคำนวณต่อ
3. ถ้าไม่แน่ใจ ให้ RAG ถามกลับ (mode askBack) แทนการเดา
