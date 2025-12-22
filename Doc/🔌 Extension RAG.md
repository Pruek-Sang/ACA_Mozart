# 🔌 Extension RAG - แผนพัฒนาต่อยอด

## 📌 สรุปภาพรวม

เอกสารนี้อธิบายแผนการพัฒนา 4 ฟีเจอร์ใหม่ โดย **ไม่กระทบ code เดิมที่ทำงานอยู่**

| # | ฟีเจอร์ | ตำแหน่งที่แก้ | ความเสี่ยง Regression |
|---|--------|-------------|---------------------|
| 1 | "What If" เต้ารับห้องน้ำ | Result Builder | **ไม่มี** (แค่เพิ่มข้อความ) |
| 2 | Drag-Drop Room Visualizer | Frontend | ไม่มี (เพิ่ม component ใหม่) |
| 3 | แก้ไข Load Schedule | Frontend | ไม่มี (เพิ่ม feature ใหม่) |
| 4 | Export to CAD | Frontend + API | ไม่มี (เพิ่ม endpoint ใหม่) |

---

## 🏗️ CAD Capabilities ใน MCP Core (สรุปจากการวิจัย)

### ไฟล์หลัก: `mcp_core_v2/cad/`

| Generator | ไฟล์ | Output | หน้าที่ |
|-----------|------|--------|--------|
| **AutoLISP Writer** | `autolisp_writer.py` | `.lsp` | Base class สร้าง AutoLISP |
| **SLD Generator** | `drawing/sld_generator.py` | E-301 | Single Line Diagram |
| **Panel Schedule** | `drawing/panel_schedule_generator.py` | E-401 | ตาราง Circuit 12 คอลัมน์ |
| **Lighting Plan** | `drawing/lighting_plan_generator.py` | - | แผนไฟแสงสว่าง |
| **Power Plan** | `drawing/power_plan_generator.py` | - | แผนเต้ารับ |
| **Details** | `drawing/details_generator.py` | - | รายละเอียดเพิ่มเติม |
| **Device Placer** | `placement/device_placer.py` | - | จัดวางอุปกรณ์ |
| **Circuit Assigner** | `placement/circuit_assigner.py` | - | จัด Circuit |

### AutoLISPWriter Methods:
- `write_header()` - Header ไฟล์
- `create_layers()` - สร้าง Layers
- `draw_line()`, `draw_polyline()` - เส้น
- `insert_block()` - วาง Block
- `add_text()` - ใส่ข้อความ
- `wrap_in_function()` - Wrap เป็น defun
- `save_to_file()` - บันทึกไฟล์ .lsp

---

## 🔧 ฟีเจอร์ 1: "What If" เต้ารับห้องน้ำ (ไม่แก้ค่า แค่แสดงเปรียบเทียบ)

### ⚠️ สถานะปัจจุบัน
- `integration.py` hardcode ว่า bathroom มี **1200W receptacle**
- เต้ารับห้องน้ำรวมในวงจรเดียวกับทั้งชั้น → **MCB ไม่เปลี่ยน**
- **ไม่คุ้มที่จะแก้ MCP** - แค่ 1-2 เต้ารับไม่กระทบมาก

### ✅ วิธีแก้ที่เลือก: แสดง "What If" Section

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚡ LOAD SUMMARY (สรุปโหลด)                                      │
├─────────────────────────────────────────────────────────────────┤
│  โหลดรวม (Connected Load)  :     19,560 W (19.6 kW)          │
│  กระแสโหลด (Demand Current):       81.5 A                      │
├─────────────────────────────────────────────────────────────────┤
│  💡 หากไม่ใส่เต้ารับในห้องน้ำ:                                  │
│     โหลดรวม: 18,360 W (-1,200W)                               │
│     กระแส: 76.5A (-5A)                                        │
└─────────────────────────────────────────────────────────────────┘
```

### ตำแหน่งที่ต้องแก้
- **ไม่แก้ MCP Core** ❌
- **แก้ที่ Result Builder** (ไฟล์ที่สร้าง text output)
- เพิ่มบรรทัด "What If" ใน LOAD SUMMARY section

### ผลกระทบ
- ❌ ไม่เปลี่ยน MCB size (ยังคง 15A)
- ❌ ไม่เปลี่ยน Wire size (ยังคง 2.5mm²)
- ✅ แสดงข้อมูลเปรียบเทียบให้ผู้ใช้ตัดสินใจ
- ✅ **Regression Risk = 0** (แค่เพิ่มข้อความ)


---

## 🎮 ฟีเจอร์ 2: Drag-Drop Room Visualizer (ฝั่งขวา)

### Concept
```
┌─────────────────────────────────────────────┐
│  ชั้น 2                                    │
│  ┌─────────┬─────────┬─────────┐          │
│  │ ห้องนอน1 │ ห้องนอน2 │   กำแพง  │          │
│  ├─────────┼─────────┼─────────┤          │
│  │ ห้องน้ำ  │ห้องเก็บของ│   กำแพง  │          │
│  └─────────┴─────────┴─────────┘          │
├─────────────────────────────────────────────┤
│  ชั้น 1                                    │
│  ┌─────────┬─────────┬─────────┐          │
│  │ห้องนั่งเล่น│ ห้องครัว │   โรงรถ  │          │
│  ├─────────┼─────────┼─────────┤          │
│  │  ห้องน้ำ │ห้องเก็บของ│   กำแพง  │          │
│  └─────────┴─────────┴─────────┘          │
└─────────────────────────────────────────────┘
```

### Logic
1. รับ JSON จาก Gateway (ชื่อห้อง + ชั้น)
2. แสดง 2 กล่องใหญ่ (ชั้น 1, ชั้น 2) แต่ละกล่องมี 6 ช่อง (3×2)
3. ช่องที่ไม่มีห้อง → แสดง "กำแพง"
4. ลาก-วางสลับตำแหน่งได้อิสระ
5. **ไม่กระทบค่าคำนวณฝั่งซ้าย**

### ไฟล์ใหม่ที่ต้องสร้าง
```
frontend_UI_UX/mozart-chat/src/features/floorplan/
├── DragDropGrid.tsx        ← NEW: Component drag-drop grid
├── FloorBox.tsx            ← NEW: กล่อง 6 ช่อง
├── RoomCard.tsx            ← NEW: การ์ดห้องที่ลากได้
└── FloorPlanVisualizer.tsx ← MODIFY: รวม DragDropGrid
```

### ไม่กระทบ
- `useChat.ts` - ไม่แก้
- `layout.logic.ts` - ใช้เฉพาะ room data ไม่แก้ logic
- Chat pane ฝั่งซ้าย - ไม่เกี่ยว

---

## 📝 ฟีเจอร์ 3: แก้ไข Load Schedule

### Concept
```
│   1 │ 🚿 HEATER-4500W in ห้อ... │   [23.0] │  ← คลิกแก้ได้
```

### Logic
1. แปลง text table เป็น editable fields
2. คลิกที่ค่าตัวเลข → เปิด input field
3. แก้ไขแล้วกด Enter → บันทึก (local state เท่านั้น)
4. **ไม่คำนวณซ้ำ** - แค่เปลี่ยนค่าที่แสดง

### ไฟล์ใหม่ที่ต้องสร้าง
```
frontend_UI_UX/mozart-chat/src/features/loadschedule/
├── EditableLoadTable.tsx   ← NEW: ตาราง editable
├── EditableCell.tsx        ← NEW: cell ที่คลิกแก้ได้
└── loadScheduleParser.ts   ← NEW: parse text → structured data
```

### ไม่กระทบ
- MCP Core - ไม่แก้
- Gateway - ไม่แก้
- ค่าคำนวณ - ไม่คำนวณซ้ำ

---

## 📤 ฟีเจอร์ 4: Export to CAD Folder

### Concept
```
[Load Schedule แก้ไขแล้ว] → [ปุ่ม "ส่งไป CAD"] → cad/ folder
```

### Logic
1. ปุ่ม "Export to CAD" ใน UI
2. กดแล้วส่ง JSON ไป API endpoint `/api/export-cad`
3. Gateway/RAG เขียนไฟล์ JSON ลง `cad/` folder
4. MCP อ่านจาก `cad/` แล้วสร้าง AutoLISP

### ไฟล์ที่ต้องเพิ่ม/แก้
```
# Frontend
├── ExportButton.tsx        ← NEW: ปุ่ม export

# Gateway
├── gate_way_new.py         ← ADD: endpoint /api/export-cad

# Folder structure
├── cad/
│   └── project_XXXXX.json  ← OUTPUT: JSON for AutoLISP
```

### ไม่กระทบ
- Chat flow เดิม - ไม่เกี่ยว
- MCP calculation - ไม่แก้ (แค่เพิ่ม input)

---

## 🛡️ แผนป้องกัน Regression

### หลักการ: แยก New กับ Old ออกจากกัน

| สิ่งที่ทำ | วิธีป้องกัน |
|---------|-----------|
| เพิ่ม component ใหม่ | สร้างไฟล์ใหม่ ไม่แก้ไฟล์เก่า |
| แก้ logic MCP | เพิ่ม condition ไม่ลบ code เดิม |
| เพิ่ม API endpoint | สร้าง route ใหม่ ไม่แก้ route เก่า |

### Checklist ก่อนแก้ทุกครั้ง

- [ ] ไฟล์นี้มีคนอื่นใช้ไหม?
- [ ] ถ้าแก้แล้ว feature เดิมยังทำงานไหม?
- [ ] มี unit test ครอบคลุมไหม?
- [ ] ทดสอบ flow เดิมหลังแก้ไหม?

---

## 📋 ลำดับการทำงาน

### Phase 1: "What If" เต้ารับห้องน้ำ (ง่ายสุด)
```
1. หา Result Builder ที่สร้าง LOAD SUMMARY text
2. เพิ่มบรรทัด "หากไม่ใส่เต้ารับในห้องน้ำ: ..."
3. คำนวณ: โหลดปัจจุบัน - 1200W
4. ไม่ต้องทดสอบ Regression (แค่เพิ่มข้อความ)
```

### Phase 2: Drag-Drop Visualizer
```
1. สร้าง component ใหม่ DragDropGrid
2. รับ room data จาก Gateway response
3. แสดง grid 3×2 per floor
4. Implement drag-drop logic
```

### Phase 3: Editable Load Schedule
```
1. Parse text table เป็น structured data
2. สร้าง EditableCell component
3. Handle edit events
4. Keep local state only
```

### Phase 4: Export to CAD
```
1. เพิ่ม endpoint ใน Gateway
2. สร้าง ExportButton component
3. เขียน JSON ไป cad/ folder
```

---

## ⚠️ สิ่งที่ต้องระวัง

1. **ห้ามแก้ `useChat.ts`** ถ้าไม่จำเป็น - มันเชื่อมหลาย components
2. **ห้ามแก้ `gate_way_new.py` routing เดิม** - เพิ่ม route ใหม่เท่านั้น
3. **ห้ามแก้ MCP calculation logic** ยกเว้น bathroom exclusion
4. **ทดสอบ end-to-end หลังทุก phase**

---

*สร้างเมื่อ: 2025-12-17 02:58*
*เพื่อวางแผนพัฒนาต่อยอดอย่างปลอดภัย*
