**(Mixa นึกย้อนไปที่ไฟล์ทั้งหมด แล้วชี้ไปที่ไฟล์ที่ถูกต้อง)**

**"จำได้ค่ะ! จากไฟล์ทั้งหมดที่ส่งมา ไฟล์ที่ต้องดูแลเรื่อง 'การเดินสายต้องคำนึงถึงวิธีการติดตั้ง' คือ..."**

---

## 📁 **ไฟล์หลัก: `wire_router.py`**

**"ไฟล์นี้เป็นหัวใจของการเดินสายไฟทั้งหมดค่ะ"**

### **เหตุผลที่เลือก:**

1. **หน้าที่ตรงกัน:** ไฟล์นี้มีหน้าที่เดียวคือ "การกำหนดเส้นทางเดินสายไฟ"

2. **Class ชื่อ `WireRouter`:** มี method `route_orthogonal()`, `route_power_circuit()`, `route_lighting_circuit()`

3. **ปัจจุบันทำแค่:** Orthogonal routing แบบง่ายๆ (H+V)

4. **ต้องพัฒนาเพิ่ม:** ให้คิดถึงวิธีการติดตั้งด้วย

---

## 🛠️ **ไฟล์เสริมที่ต้องแก้ไขด้วย:**

### **1. `autolisp_writer.py`**

```python

# ต้องเพิ่ม method สำหรับวาดส่วนประกอบการติดตั้ง

def draw_conduit(self, path, diameter):

"""วาดท่อร้อยสาย"""

def draw_support(self, position, support_type):

"""วาดจุดยึดท่อ"""

def add_installation_note(self, text, position):

"""เพิ่มหมายเหตุการติดตั้ง"""

```

### **2. `standard_loader.py`**

```python

# ต้องเพิ่มกฎการติดตั้งใน catalog

"CONDUIT_SIZING_RULE": {

"2.5mm² wires": "min 16mm conduit",

"4.0mm² wires": "min 20mm conduit"

}

"SUPPORT_SPACING_RULE": {

"conduit ≤20mm": "1.5m spacing",

"conduit >20mm": "2.0m spacing"

}

```

### **3. `placement_validator.py`**

```python

# ต้องเพิ่ม validation สำหรับการเดินสาย

def validate_wire_routing(self, routes, room_data):

"""ตรวจสอบว่าเส้นทางเดินสายเหมาะสมกับการติดตั้งไหม"""

# ตัวอย่าง: ตรวจสอบว่าเดินผ่านโครงสร้างที่เจาะไม่ได้

```

---

## 🎯 **สิ่งที่ต้องเพิ่มใน `wire_router.py`:**

```python

# ใน class WireRouter ต้องเพิ่ม:

class WireRouter:

def __init__(self):

# เพิ่มข้อมูลการติดตั้ง

self.installation_method = None # 'EMBEDDED', 'SURFACE', 'CONCEALED'

self.conduit_size = None

self.support_points = []

def set_installation_method(self, room_type, building_type):

"""เลือกวิธีการติดตั้งตามประเภทห้องและอาคาร"""

# ตัวอย่าง logic:

if building_type == 'new_construction':

self.installation_method = 'EMBEDDED'

elif building_type == 'renovation':

self.installation_method = 'SURFACE'

def calculate_conduit_size(self, wire_size, num_wires):

"""คำนวณขนาดท่อตามมาตรฐาน"""

# ใช้ข้อมูลจาก standard_loader.py

def generate_support_points(self, wire_path):

"""สร้างจุดยึดท่ออัตโนมัติ"""

# ทุก ๆ 1.5m สำหรับท่อเล็ก

# ทุก ๆ 2.0m สำหรับท่อใหญ่

def route_with_installation(self, start, end, obstacles=[]):

"""หาเส้นทางโดยคำนึงถึงสิ่งกีดขวางและวิธีการติดตั้ง"""

# ไม่เดินผ่านเสาหรือโครงสร้างที่เจาะไม่ได้

# หลบท่อน้ำและท่อแอร์

```

---

## 📋 **แผนการแก้ไขไฟล์ `wire_router.py`:**

```

Phase 1: เพิ่ม Installation Awareness

- เพิ่ม attribute: installation_method, conduit_type

- เพิ่ม method: set_installation_parameters()

Phase 2: ปรับปรุง Routing Algorithm

- เปลี่ยนจาก simple H+V → A* pathfinding

- รับ obstacle list (ผนัง, เสา, ท่ออื่นๆ)

Phase 3: เพิ่ม Construction Details

- สร้างจุดยึดอัตโนมัติ

- คำนวณขนาดท่อ

- กำหนดจุดเข้าออกท่อ

Phase 4: Generate Installation Notes

- หมายเหตุสำหรับช่าง

- รายการวัสดุ

- ลำดับการติดตั้ง

```

---

## 🔗 **Data Flow ใหม่ที่ต้องสร้าง:**

```

room_templates.py → wire_router.py

↓ ↓

(รูปร่างห้อง) (วิธีการติดตั้ง)

↓ ↓

wire_router.py ← standard_loader.py

↓

(เส้นทาง + ท่อ + จุดยึด)

↓

autolisp_writer.py

↓

(.lsp file)

```

---

## ⚠️ **จุดที่ต้องระวังในการแก้ไข:**

1. **อย่าแก้ `wire_router.py` แบบทิ้งของเดิม:**

```python

# ต้องเก็บ backward compatibility

def route_orthogonal(self, start, end): # วิธีเก่า (ยังใช้ได้)

...

def route_smart(self, start, end, constraints=[]): # วิธีใหม่

...

```

2. **ใช้ Interface เดิมให้ได้:**

```python

# Generator อื่นๆ ยังเรียกใช้ได้เหมือนเดิม

router = WireRouter()

routes = router.route_all_circuits(devices, panel) # ยังทำงานได้

```

3. **Test ทุกการเปลี่ยนแปลง:**

```python

# ต้องมี test สำหรับ method ใหม่

def test_conduit_sizing():

router = WireRouter()

size = router.calculate_conduit_size('2.5mm²', 4)

assert size == '20mm'

```

---

## 🎯 **สรุป:**

**"ไฟล์หลักคือ `wire_router.py`

แต่ต้องแก้ไข `autolisp_writer.py` และ `standard_loader.py` ด้วย

เพื่อให้ระบบคำนึงถึงวิธีการติดตั้งจริงในหน้างาน"**

**"นายท่านต้องการให้มิกซ่าเริ่มแก้ไขไฟล์ไหนก่อนคะ?

1. `wire_router.py` (แกนกลาง)

2. `standard_loader.py` (เพิ่มกฎ)

3. `autolisp_writer.py` (เพิ่มฟังก์ชันวาด)"**

**วิศวกรรมมีเพียงหนึ่งเดียว... และการเดินสายไฟที่ดีต้องคิดตั้งแต่ท่อ จุดยึด ไปจนถึงมือช่าง** 🔌🔧

