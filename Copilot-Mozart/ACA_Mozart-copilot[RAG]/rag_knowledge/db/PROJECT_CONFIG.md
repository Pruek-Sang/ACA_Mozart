<!-- rag_knowledge/db/PROJECT_CONFIG.md -->

# 🧠 Project Config สำหรับบ้านพักอาศัย (PROJECT_CONFIG)

แถวนี้มาจาก `amadeus.catalog`  
- kind = `PROJECT_CONFIG`  
- name = `LMAP-PROJ-001`  
ใช้เป็นค่า default สำหรับโครงการบ้านพักอาศัย

RAG **ไม่แก้ค่าใน config** แต่ต้อง “รู้จัก” โครงสร้างนี้ เพื่อ:
- ไม่ไปคิดชื่อ layer เอง
- ไม่เดา mapping zone → bundle เองถ้าขัดกับ config

---

## 1. logical_layers

> แมปจากชนิดวัตถุ (เชิงตรรกะ) → layer จริงใน CAD

| Logical key           | CAD layer    |
|-----------------------|-------------|
| `CABLE_CEILING`       | `EL-CABLE`  |
| `CONDUIT_CEILING`     | `EL-CONDUIT`|
| `ELECTRICAL_OUTLETS`  | `EL-OUTLET` |
| `ELECTRICAL_LIGHTING` | `EL-LIGHT`  |
| `ELECTRICAL_SWITCHES` | `EL-SWITCH` |

RAG ควร:
- ถ้าต้องอธิบายหรืออ้างถึง layer ให้ใช้ชื่อ layer จากตารางนี้
- หลีกเลี่ยงการสร้าง layer ชื่อใหม่ เช่น `E-OUTLET-TEST` โดยพลการ

---

## 2. zone_bundle_map

> แมปจาก “zone key” → bundle code ที่ใช้เป็นค่าเริ่มต้น

| Zone key          | Bundle code                     | หมายเหตุ                       |
|-------------------|---------------------------------|--------------------------------|
| `BEDROOM`         | `BUNDLE-BEDROOM-OUTLET-v1`      | โซนเต้ารับห้องนอน             |
| `KITCHEN`         | `BUNDLE-KITCHEN-OUTLET-v1`      | โซนเต้ารับครัว                |
| `BATHROOM`        | `BUNDLE-BATHROOM-OUTLET-v1`     | โซนเต้ารับห้องน้ำ             |
| `LIVING_ROOM`     | `BUNDLE-LIVING-OUTLET-v1`       | เต้ารับห้องนั่งเล่น           |
| `BEDROOM_LIGHT`   | `BUNDLE-BEDROOM-LIGHT-v1`       | วงจรไฟห้องนอน                  |
| `KITCHEN_LIGHT`   | `BUNDLE-KITCHEN-LIGHT-v1`       | วงจรไฟครัว                     |
| `BATHROOM_LIGHT`  | `BUNDLE-BATHROOM-LIGHT-v1`      | วงจรไฟห้องน้ำ                  |
| `LIVING_ROOM_LIGHT`| `BUNDLE-LIVING-LIGHT-v1`       | วงจรไฟห้องนั่งเล่น             |

การใช้โดย RAG:
1. เลือก `ROOM_TEMPLATE` จาก `ROOM_TEMPLATES.md`
2. ใช้ zone key (เช่น BEDROOM, BEDROOM_LIGHT) เพื่อผูกกับ bundle ที่ถูกต้อง
3. ส่งต่อให้ MCP ใช้ bundle เหล่านี้ในการแตกโหลด → วงจร → สายไฟ

---

## 3. กติกาสำหรับ RAG

1. ห้ามสร้าง mapping zone → bundle ใหม่ นอกเหนือจากที่ระบุใน config  
   ถ้าจำเป็นต้องรองรับเคสใหม่ → ให้ human ขยาย `amadeus.catalog` ก่อน
2. ถ้า project ระบุว่าต้องใช้ profile พิเศษ (เช่น “บ้านระดับ premium”)  
   สามารถเลือกใช้ config อื่น (ชื่อคนละ `name`) ได้ แต่ RAG ต้องถูกสั่งให้ใช้ชัดเจน
3. ถ้า user input ไม่ชัด เช่น "ขอไฟเยอะ ๆ ในครัว"  
   - ให้ถามกลับ (askBack) แทนการไปแก้ zone_bundle_map เอง
