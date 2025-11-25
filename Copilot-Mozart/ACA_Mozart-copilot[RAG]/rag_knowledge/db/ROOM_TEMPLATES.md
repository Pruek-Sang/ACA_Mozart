<!-- rag_knowledge/db/ROOM_TEMPLATES.md -->

# 🧩 Room Templates (ROOM_TEMPLATE จาก amadeus.catalog)

เอกสารนี้สรุป Template ห้องมาตรฐานที่ใช้ในระบบออกแบบไฟฟ้าบ้านพักอาศัยของ ACA_Mozart  
โดยอ้างอิงจากตาราง `amadeus.catalog` (kind = `ROOM_TEMPLATE`) และ mapping bundle ที่เกี่ยวข้อง

RAG ใช้ข้อมูลชุดนี้เพื่อ:
- แปลงคำบรรยายห้องแบบภาษาคน → `room_type` + `template_code` ใน `ProjectInputSpec.rooms[*]`
- เลือก `default_zone_bundles` ให้ตรงกับประเภทห้อง (เช่น ห้องน้ำ → BUNDLE-BATHROOM-* )

---

## 1. รายการ Room Template ปัจจุบัน

| Template code         | Room type       | Description                                 | Default zone bundles                                      |
|-----------------------|-----------------|---------------------------------------------|-----------------------------------------------------------|
| `RT-BATHROOM-STD`     | `bathroom`      | Template ห้องน้ำมาตรฐาน                    | `BUNDLE-BATHROOM-OUTLET-v1`, `BUNDLE-BATHROOM-LIGHT-v1`   |
| `RT-LIVING-STD`       | `living_room`   | Template ห้องนั่งเล่นมาตรฐาน               | `BUNDLE-LIVING-OUTLET-v1`, `BUNDLE-LIVING-LIGHT-v1`       |
| `RT-KITCHEN-STD`      | `kitchen`       | Template ห้องครัวมาตรฐาน                   | `BUNDLE-KITCHEN-OUTLET-v1`, `BUNDLE-KITCHEN-LIGHT-v1`     |
| `RT-BEDROOM-STD`      | `bedroom`       | Template ห้องนอนมาตรฐาน                    | `BUNDLE-BEDROOM-OUTLET-v1`, `BUNDLE-BEDROOM-LIGHT-v1`     |
| `RT006-LAUNDRY-ROOM`  | `laundry_room`  | Template ห้องซักผ้า                         | -                                                         |
| `RT005-UTILITY-ROOM`  | `utility_room`  | Template ห้องยูทิลิตี้ / ปั๊มน้ำ           | -                                                         |
| `ROOMT-SWIMMING-POOL` | `swimming_pool` | Template: สระว่ายน้ำ (Swimming Pool)       | -                                                         |

> ห้องที่ไม่มี `default_zone_bundles` จะใช้กติกาใน field `base_load` + รายการ `appliances[]` ใน `data`  
> เพื่อให้ MCP แตกโหลดออกเป็นวงจรทีหลัง

---

## 2. ความสัมพันธ์กับ ZONE_BUNDLE

- ชื่อ bundle ในคอลัมน์ **Default zone bundles** link ไปยังแถว kind = `ZONE_BUNDLE`
- ตัวอย่าง:
  - `BUNDLE-BEDROOM-OUTLET-v1` → เต้ารับมาตรฐานห้องนอน
  - `BUNDLE-BEDROOM-LIGHT-v1` → วงจรไฟสว่างห้องนอน
  - `BUNDLE-KITCHEN-OUTLET-v1` → เต้ารับครัว ฯลฯ
- MCP ใช้ bundle เหล่านี้ร่วมกับ:
  - `CIRCUIT_TEMPLATE` → รูปแบบวงจรมาตรฐาน
  - `CABLE_SPEC` → ขนาดสาย / ประเภทสาย
  - `PLACEMENT_RULE` → ตำแหน่งวางอุปกรณ์ในแบบ CAD

---

## 3. วิธีใช้โดย RAG ตอนสร้าง ProjectInputSpec

เมื่อได้รับ `ProjectRequirements` เช่น:
> "บ้าน 2 ชั้น ชั้นล่างมี 1 ห้องนั่งเล่น 1 ครัว 1 ห้องน้ำ  
>  ชั้นบนมี 3 ห้องนอน 2 ห้องน้ำ"

RAG ควร:
1. Map ภาษาคน → `room_type` ตามตาราง:
   - "ห้องนอน" → `bedroom` → ใช้ `RT-BEDROOM-STD`
   - "ห้องน้ำ" → `bathroom` → ใช้ `RT-BATHROOM-STD`
   - "ห้องครัว" → `kitchen` → ใช้ `RT-KITCHEN-STD`
2. ใส่ใน `ProjectInputSpec.rooms[*]`:
   - `room_type` = ค่าในตาราง
   - `template_code` = template code เช่น `RT-BEDROOM-STD`
3. ให้ MCP ไปแตก bundle / วงจร จาก template + zone_bundle_map ต่อ  
   RAG ห้ามสร้าง bundle เองนอกเหนือจากที่มีในเอกสารนี้ + `PROJECT_CONFIG.md`
