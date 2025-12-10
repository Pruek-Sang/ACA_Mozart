🎯 # MCP AutoLISP Generator - Complete Documentation

**Project:** ACA Mozart - Automated Electrical Design System  
**Date:** 2025-11-29  
**Status:** ✅ Complete MVP

---

## 📋 **Table of Contents**

1. [Phase A-D Detailed Implementation](#phase-a-d-detailed-implementation)
2. [MCP Integration](#mcp-integration)
3. [AutoLISP Generation Output](#autolisp-generation-output)
4. [Complete Workflow Diagram](#complete-workflow-diagram)
5. [Code Reference](#code-reference)
6. [Testing](#testing)

---

## 📚 1. Phase A-D Detailed Implementation

### **Phase A: Core AutoLISP + Standards (Week 1-2)**

#### **1.1 Standards Loader**
**File:** [`cad/standards/standard_loader.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/standards/standard_loader.py)

**ทำอะไร:**
- อ่านกฎและมาตรฐานจาก `catalog_rows.csv`
- รองรับ 3 มาตรฐาน: EIT (Thailand), IEC (International), NEC (USA)
- ไม่ใช้ Supabase โดยตรง (ป้องกัน dependency)

**Code สำคัญ:**
```python
def load_standards(standard_code: str = 'EIT') -> Dict[str, Any]:
    """Load standards from catalog_rows.csv"""
    # อ่านจากไฟล์แทน database
    catalog_path = find_catalog_file()
    
    # Filter by standard
    rules = filter_by_standard(data, standard_code)
    
    return {
        'placement_rules': placement_rules,
        'device_codes': device_codes,
        'validation_rules': validation_rules
    }
```

**Output:**
- กฎการวางอุปกรณ์ (outlet spacing, heights)
- รหัสอุปกรณ์ (device codes)
- กฎการตรวจสอบ (validation rules)

---

#### **1.2 AutoLISP Writer Base**
**File:** [`cad/autolisp_writer.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/autolisp_writer.py)

**ทำอะไร:**
- สร้าง AutoLISP code พื้นฐาน
- จัดการ header, footer, layers
- คำสั่งวาดพื้นฐาน: LINE, PLINE, INSERT, TEXT
- ตรวจสอบ syntax (วงเล็บสมดุล)

**Code สำคัญ:**
```python
class AutoLISPWriter:
    def write_header(self, drawing_number: str, title: str):
        """Write AutoLISP header"""
        self.code_lines.append(f";;; {drawing_number} - {title}\\n")
        # ... more header code
    
    def create_layers(self, layers: Dict[str, Dict]):
        """Create AutoCAD layers"""
        for name, props in layers.items():
            # (command "LAYER" "N" "E-DEVICE" "C" "7" ...)
    
    def draw_line(self, start: tuple, end: tuple):
        """Draw a line in AutoCAD"""
        # (command "LINE" (list x1 y1) (list x2 y2) "")
    
    def insert_block(self, block_name: str, position: tuple):
        """Insert a block (device symbol)"""
        # (command "INSERT" "OUTLET" (list x y) 1.0 0)
```

**Output:**
- Valid AutoLISP code (.lsp files)
- Balanced parentheses
- UTF-8 encoding support

---

#### **1.3 E-301 Single Line Diagram Generator**
**File:** [`cad/drawing/sld_generator.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/drawing/sld_generator.py)

**ทำอะไร:**
- สร้าง Single Line Diagram (แผนผังวงจรไฟฟ้า)
- แสดง panel → breakers → loads
- ใช้ข้อมูลจาก MCP calculations

**Code สำคัญ:**
```python
def generate(self, panel_data: Dict, mcp_result: Any, standard: str):
    """Generate E-301 Single Line Diagram"""
    
    # 1. Draw panel symbol
    self._draw_panel_symbol(panel_data)
    
    # 2. Draw circuit breakers from MCP
    for i, wire in enumerate(mcp_result.wires):
        breaker = mcp_result.breakers[i]
        self._draw_breaker(breaker)
    
    # 3. Draw connections
    self._draw_connections()
    
    # 4. Add labels (wire sizes, ratings)
    self._add_labels(mcp_result)
```

**Input from MCP:**
- `mcp_result.wires` - ขนาดสาย
- `mcp_result.breakers` - เบรกเกอร์
- `mcp_result.voltage` - แรงดัน

**Output:**
- `E-301_Single_Line_Diagram.lsp`

---

#### **1.4 E-401 Panel Schedule Generator**
**File:** [`cad/drawing/panel_schedule_generator.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/drawing/panel_schedule_generator.py)

**ทำอะไร:**
- สร้างตาราง Panel Schedule (12 คอลัมน์)
- แสดงรายการวงจร, breaker, wire size, load

**Code สำคัญ:**
```python
def generate(self, panel_id: str, circuit_list: List, mcp_result: Any):
    """Generate E-401 Panel Schedule"""
    
    # 1. Create table structure (12 columns)
    self._create_table_structure()
    
    # 2. Add header row
    columns = ['Circuit', 'Description', 'Wire Size', 'Breaker', 
               'Load (VA)', 'Phase', ...]
    
    # 3. Add circuit rows from MCP
    for circuit in circuit_list:
        self._add_circuit_row(circuit)
    
    # 4. Add totals
    total_load = sum(c['load'] for c in circuit_list)
    self._add_total_row(total_load)
```

**Input from MCP:**
- Circuit list with wire sizes
- Breaker ratings
- Load calculations

**Output:**
- `E-401_Panel_Schedule.lsp`

---

#### **1.5 Validation Framework**
**File:** [`cad/validators/lisp_validator.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/validators/lisp_validator.py)

**ทำอะไร:**
- ตรวจสอบ syntax (วงเล็บ, encoding)
- ตรวจสอบ semantic (ความสอดคล้องกับ MCP)

**Code สำคัญ:**
```python
def validate_lisp_syntax(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate AutoLISP syntax"""
    
    # 1. Check parentheses balance
    open_count = code.count('(')
    close_count = code.count(')')
    if open_count != close_count:
        errors.append("Unbalanced parentheses")
    
    # 2. Check encoding (must be UTF-8)
    
    # 3. Check basic structure
    
    return (len(errors) == 0, errors)

def validate_lisp_semantic(file_path: Path, mcp_result: Any):
    """Validate consistency with MCP results"""
    
    # Check if wire sizes in LISP match MCP calculations
    # Check if breaker ratings match
    # Check if loads are consistent
```

---

### ** Phase B: Device Placement + Room Templates (Week 3-4)**

#### **2.1 Room Templates**
**File:** [`cad/geometry/room_templates.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/geometry/room_templates.py)

**ทำอะไร:**
- กำหนด 6 ประเภทห้องมาตรฐาน
- มีข้อมูลเรขาคณิต (polygon, door, window, furniture)

**Code สำคัญ:**
```python
ROOM_TEMPLATES = {
    'bedroom': {
        'type': 'bedroom',
        'polygon': [(0,0), (4000,0), (4000,6000), (0,6000)],  # 4x6m
        'door': {
            'position': (2000, 0),
            'width': 900,
            'swing_direction': 'inward'
        },
        'windows': [
            {'position': (4000, 3000), 'width': 1500}
        ],
        'furniture': [
            {'type': 'bed', 'polygon': [(1000,2000), (3000,2000), ...]}
        ],
        'typical_outlets': 6,
        'typical_lights': 2
    },
    # ... living, kitchen, bathroom, corridor, other
}

def get_template(room_type: str) -> Dict:
    """Get room template by type"""
    return ROOM_TEMPLATES.get(room_type)
```

**ห้องทั้งหมด:**
1. Bedroom (4x6m)
2. Living Room (6x8m)
3. Kitchen (3x4m)
4. Bathroom (2.5x3m)
5. Corridor (1.5x8m)
6. Other/Generic (4x4m)

---

#### **2.2 Device Placer**
**File:** [`cad/placement/device_placer.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/placement/device_placer.py)

**ทำอะไร:**
- วางอุปกรณ์ (outlets, lights, switches) ในห้อง
- ใช้กฎจาก standards
- **Return type: dict (LOCKED)**
- **circuit = None (LOCKED - assigned in Phase D)**

**Code สำคัญ:**
```python
class DevicePlacer:
    def place_all_devices(self, room_template: Dict) -> Dict[str, Any]:
        """
        Place all devices in room
        
        CRITICAL: Return type MUST be dict!
        """
        # 1. Place outlets along walls
        outlets = self.place_receptacles(room_template)
        
        # 2. Place lights on ceiling
        lights = self.place_lights(room_template)
        
        # 3. Place switches near door
        switches = self.place_switches(room_template)
        
        # RETURN AS DICT (LOCKED REQUIREMENT)
        return {
            'outlets': outlets,      # List[Dict]
            'lights': lights,        # List[Dict]
            'switches': switches,    # List[Dict]
            'validation': {...}
        }
    
    def place_receptacles(self, room_template: Dict) -> List[Dict]:
        """Place outlets along walls"""
        
        # Get spacing rules from standards
        spacing_mm, height_mm, from_corner_mm = self._get_outlet_rules()
        
        # Walk along walls
        for wall in self._get_wall_segments(polygon):
            # Place every spacing_mm
            # Avoid doors/windows
            # Check furniture collision
            
            device = {
                'id': 'OUT-001',
                'type': 'outlet',
                'position': (x, y),
                'height': 300,  # mm from floor
                'device_code': 'OUT-16A-230V',
                'circuit': None,  # LOCKED - assigned later!
                'room': room_type
            }
```

**Algorithm:**
- **Outlets:** วางตามผนังทุก 2-3.6m, หลีกเลี่ยงประตู/หน้าต่าง/เฟอร์นิเจอร์
- **Lights:** วางบนเพดาน - centroid สำหรับห้องเล็ก, grid สำหรับห้องใหญ่
- **Switches:** วางใกล้ประตู (ด้านลูกบิด), สูง 1100mm

---

#### **2.3 Placement Validator**
**File:** [`cad/validators/placement_validator.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/validators/placement_validator.py)

**ทำอะไร:**
- คำนวณ accuracy เทียบกับ golden templates
- ตรวจสอบกฎการวาง (VR001/002/003)

**Code สำคัญ:**
```python
GOLDEN_LAYOUTS = {
    'bedroom_4x6': {
        'outlets': [
            {'position': (1000, 0), 'tolerance_mm': 100},
            {'position': (3000, 0), 'tolerance_mm': 100},
            # ...
        ],
        'lights': [...],
        'switches': [...]
    }
}

def calculate_accuracy(placed_devices: Dict, golden_template: str) -> float:
    """Calculate placement accuracy"""
    
    matched = 0
    total = 0
    
    for expected in golden['outlets']:
        # Find nearest placed device
        nearest_dist = min_distance(expected, placed_devices)
        
        if nearest_dist <= expected['tolerance_mm']:
            matched += 1
        total += 1
    
    return matched / total  # 0.0 - 1.0

def validate_placement_rules(devices: Dict) -> Dict:
    """Validate placement rules"""
    
    violations = []
    
    # VR001: Outlet height (300-1200mm)
    for outlet in devices['outlets']:
        if not (300 <= outlet['height'] <= 1200):
            violations.append("VR001 violation")
    
    # VR002: Switch height (1100-1400mm)
    # VR003: Bathroom IP44 requirement
    
    return {
        'all_rules_applied': len(violations) == 0,
        'violations': violations
    }
```

---

### **Phase C: DXF Reader + Wire Router (Week 5)**

#### **3.1 DXF Reader v1**
**File:** [`cad/dxf/dxf_reader.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/dxf/dxf_reader.py)

**ทำอะไร:**
- อ่าน DXF files (controlled templates)
- Extract room polygons, doors, windows, panels
- Map to RoomTemplate format

**Code สำคัญ:**
```python
class DXFReaderV1:
    def read_mock_dxf(self, file_path: Path) -> Dict:
        """Read mock DXF file"""
        
        # Parse layers:
        # A-ROOM-* → room polygons
        # A-DOOR-* → doors
        # A-WINDOW-* → windows
        # E-PANEL-* → panel locations
        
        return {
            'rooms': [
                {
                    'id': 'BEDROOM-01',
                    'type': 'bedroom',
                    'polygon': [(x,y), ...],
                    'door': {...},
                    'windows': [...]
                }
            ],
            'panels': [
                {'id': 'DB-1', 'position': (x,y)}
            ]
        }
    
    def map_to_room_template(self, dxf_room: Dict) -> Dict:
        """Convert DXF data to RoomTemplate format"""
        
        # Calculate area, centroid
        # Add default values
        # Make compatible with DevicePlacer
        
        return room_template
```

**Mock DXF Format:**
```
LAYER: A-ROOM-BEDROOM
POLYGON: (0,0) (4000,0) (4000,6000) (0,6000)

LAYER: A-DOOR
POINT: (2000,0) WIDTH:900

LAYER: E-PANEL-MAIN
POINT: (500,500)
```

---

#### **3.2 Wire Router**
**File:** [`cad/routing/wire_router.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/routing/wire_router.py)

**ทำอะไร:**
- เดินสายแบบ orthogonal (H+V, Manhattan-style)
- รองรับ lighting และ power circuits
- สร้าง homerun arrows ไปยัง panel

**Code สำคัญ:**
```python
class WireRouter:
    def route_orthogonal(self, start: Point, end: Point) -> List[Point]:
        """
        Route orthogonal path
        
        Algorithm: H+V (horizontal first, then vertical)
        """
        path = [
            start,
            (end[0], start[1]),  # Corner point
            end
        ]
        return path
    
    def route_lighting_circuit(self, lights, switch, panel):
        """Route lighting circuit"""
        
        routes = []
        
        # 1. Switch → each light
        for light in lights:
            path = self.route_orthogonal(switch['position'], light['position'])
            routes.append({
                'from': switch,
                'to': light,
                'path': path,
                'wire_type': 'switch_leg'
            })
        
        # 2. Switch → panel (homerun)
        homerun = self.route_orthogonal(switch['position'], panel['position'])
        routes.append({
            'from': switch,
            'to': panel,
            'path': homerun,
            'wire_type': 'homerun'  # Will get arrow
        })
        
        return routes
    
    def generate_wire_lisp(self, routes: List) -> str:
        """Generate AutoLISP for wires"""
        
        for route in routes:
            # Draw polyline
            writer.draw_polyline(route['path'])
            
            # Add homerun arrow if needed
            if route['wire_type'] == 'homerun':
                self._draw_arrow(route['path'][-1])
```

---

### **Phase D: Complete Drawings + Circuit Assignment (Week 6)**

#### **4.1 Circuit Assigner**
**File:** [`cad/placement/circuit_assigner.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/placement/circuit_assigner.py)

**ทำอะไร:**
- กำหนด circuit จาก MCP results ให้กับ devices
- Map wire sizes, breaker ratings
- **นี่คือจุดเชื่อมต่อหลักกับ MCP!**

**Code สำคัญ:**
```python
class CircuitAssigner:
    def __init__(self, mcp_result: Any):
        """Initialize with MCP calculation results"""
        self.mcp_result = mcp_result
    
    def assign_circuits_from_mcp(self, devices: Dict) -> Dict:
        """
        Assign circuits from MCP to devices
        
        CRITICAL: This connects MCP calculations to placed devices!
        """
        
        assigned_devices = {'outlets': [], 'lights': [], 'switches': []}
        
        circuit_idx = 1
        
        for outlet in devices['outlets']:
            # Get wire/breaker info from MCP
            circuit_info = self._get_circuit_info(circuit_idx, 'power')
            
            # Assign to device
            outlet['circuit'] = {
                'id': f'CKT-{circuit_idx}',
                'type': 'power',
                'wire_size': circuit_info['wire_size'],      # FROM MCP!
                'breaker_rating': circuit_info['breaker_rating'],  # FROM MCP!
                'description': f'Power Circuit {circuit_idx}'
            }
            
            assigned_devices['outlets'].append(outlet)
        
        return assigned_devices
    
    def _get_circuit_info(self, circuit_idx: int, type: str) -> Dict:
        """Get circuit info from MCP results"""
        
        if hasattr(self.mcp_result, 'wires'):
            wire = self.mcp_result.wires[circuit_idx - 1]
            breaker = self.mcp_result.breakers[circuit_idx - 1]
            
            return {
                'wire_size': f'{wire.size_mm2}mm²',
                'breaker_rating': f'{breaker.rating}A',
                'conduit_size': wire.conduit_size
            }
```

**นี่คือจุดสำคัญ:** circuit ที่เคยเป็น `None` ใน Phase B ถูกกำหนดค่าจาก MCP calculations!

---

#### **4.2 E-101 Lighting Plan Generator**
**File:** [`cad/drawing/lighting_plan_generator.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/drawing/lighting_plan_generator.py)

**ทำอะไร:**
- สร้างแบบ Lighting Plan
- แสดง lights, switches, wiring, homerun arrows

**Code สำคัญ:**
```python
def generate(self, devices: Dict, panel_position: tuple, standard: str):
    """Generate E-101 Lighting Plan"""
    
    writer = AutoLISPWriter()
    
    # 1. Create layers
    writer.create_layers({
        'E-LIGHT': {'color': 3},
        'E-SWITCH': {'color': 5},
        'E-WIRE-LIGHTING': {'color': 2}
    })
    
    # 2. Place lights
    writer.set_layer('E-LIGHT')
    for light in devices['lights']:
        writer.insert_block("LIGHT", light['position'])
        
        # Add circuit label (FROM MCP!)
        circuit = light['circuit']
        writer.add_text(circuit['id'], label_pos)
    
    # 3. Place switches
    writer.set_layer('E-SWITCH')
    for switch in devices['switches']:
        writer.insert_block("SWITCH", switch['position'])
    
    # 4. Route wiring
    router = WireRouter()
    routes = router.route_all_circuits(devices, panel)
    wire_code = router.generate_wire_lisp(routes)
    writer.code_lines.append(wire_code)
    
    # 5. Add legend
    self._add_legend(writer)
    
    return writer.get_code()
```

**Output:** `E-101_Lighting_Plan.lsp`

---

#### **4.3 E-201 Power Plan Generator**
**File:** [`cad/drawing/power_plan_generator.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/drawing/power_plan_generator.py)

**ทำอะไร:**
- สร้างแบบ Power Plan
- แสดง outlets, power wiring, circuit labels

**Code สำคัญ:**
```python
def generate(self, devices: Dict, panel_position: tuple):
    """Generate E-201 Power Plan"""
    
    # 1. Place outlets
    for outlet in devices['outlets']:
        # Determine symbol (IP44 for bathroom)
        symbol = "OUTLET_IP44" if 'IP44' in outlet['device_code'] else "OUTLET"
        writer.insert_block(symbol, outlet['position'])
        
        # Add circuit label with wire size (FROM MCP!)
        circuit = outlet['circuit']
        label = f"{circuit['id']} ({circuit['wire_size']})"
        writer.add_text(label, label_pos)
    
    # 2. Route power wiring
    router = WireRouter()
    routes = router.route_power_circuit(devices['outlets'], panel)
    wire_code = router.generate_wire_lisp(routes)
    
    return writer.get_code()
```

**Output:** `E-201_Power_Plan.lsp`

---

#### **4.4 E-501 Typical Details Generator**
**File:** [`cad/drawing/details_generator.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/cad/drawing/details_generator.py)

**ทำอะไร:**
- สร้างรายละเอียดมาตรฐาน
- mounting details, wire specs, symbol legend

**Code สำคัญ:**
```python
def generate(self, standard: str):
    """Generate E-501 Typical Details"""
    
    # 1. Draw outlet mounting detail
    self._draw_outlet_detail(writer, origin, standard)
    # Shows: wall, box, height dimension (300mm)
    
    # 2. Draw switch mounting detail
    self._draw_switch_detail(writer, origin, standard)
    # Shows: wall, box, height dimension (1100mm)
    
    # 3. Draw wire legend
    wires = [
        ("Power Circuits", "2.5mm² THW", "20A max"),
        ("Lighting Circuits", "1.5mm² THW", "10A max")
    ]
    
    # 4. Draw symbol legend
    symbols = [
        ("○", "Ceiling Light"),
        ("S", "Switch"),
        ("⊗", "Outlet"),
        ("───→", "Homerun to Panel")
    ]
    
    # 5. Add general notes
    notes = [
        "1. All dimensions in millimeters",
        "2. Wire sizes per calculations",
        f"3. Installation per {standard} standard"
    ]
```

**Output:** `E-501_Typical_Details.lsp`

---

## 🔗 2. MCP Integration

### **2.1 Integration Bridge**
**File:** [`integration.py`](file:///home/builder/Desktop/ACA_Mozart/mcp_core_v2/integration.py)

**ทำอะไร:**
- เชื่อมต่อระหว่างฝั่งคำนวณ (MCP) กับฝั่งวาดแบบ (AutoLISP)
- **นี่คือ BRIDGE หลัก!**

**Workflow:**
```python
class IntegrationBridge:
    def generate_complete_package(self, room_data: Dict):
        """Complete workflow: MCP → Devices → Circuits → Drawings"""
        
        # STEP 1: Run MCP calculations
        mcp_input = self._prepare_mcp_input(room_data)
        mcp_result = self.pipeline.execute(mcp_input)
        # Output: wire sizes, breaker ratings, voltage drop, etc.
        
        # STEP 2: Get room template and place devices
        room_template = self._get_room_template(room_data)
        placer = DevicePlacer(standard)
        devices = placer.place_all_devices(room_template)
        # Output: devices with circuit=None
        
        # STEP 3: Assign circuits from MCP to devices
        devices_with_circuits = assign_circuits(devices, mcp_result)
        # Output: devices with circuit info from MCP!
        # NOW: device['circuit'] = {
        #   'wire_size': '2.5mm²',  # FROM MCP!
        #   'breaker_rating': '16A'  # FROM MCP!
        # }
        
        # STEP 4: Route wires
        routes = route_wires(devices_with_circuits, panel_position)
        # Output: wire paths with homerun arrows
        
        # STEP 5: Generate all 5 drawings
        drawings = self._generate_all_drawings(
            devices_with_circuits,  # With MCP data!
            mcp_result,             # MCP calculations!
            panel_position
        )
        # Output: 5 .lsp files
        
        return {
            'mcp_result': mcp_result,
            'devices': devices_with_circuits,
            'routes': routes,
            'drawings': drawings
        }
```

### **2.2 How MCP Data Flows**

```
┌─────────────────────────────────────────────────────────┐
│                    MCP PIPELINE                         │
│                                                          │
│  Input: loads, voltage, distances                       │
│   ↓                                                      │
│  Calculate:                                             │
│   - Wire sizes (2.5mm², 1.5mm², etc.)                  │
│   - Breaker ratings (16A, 10A, etc.)                   │
│   - Voltage drop                                        │
│   - Derating factors                                    │
│   ↓                                                      │
│  Output: mcp_result {                                   │
│    wires: [Wire1, Wire2, ...],                         │
│    breakers: [Breaker1, Breaker2, ...],                │
│    voltage: 230                                         │
│  }                                                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ mcp_result
                 ↓
┌─────────────────────────────────────────────────────────┐
│              CIRCUIT ASSIGNER                           │
│                                                          │
│  Takes: mcp_result + devices (circuit=None)            │
│   ↓                                                      │
│  For each device:                                       │
│    device['circuit'] = {                               │
│      'wire_size': mcp_result.wires[i].size_mm2,       │
│      'breaker_rating': mcp_result.breakers[i].rating   │
│    }                                                     │
│   ↓                                                      │
│  Output: devices with MCP data assigned!               │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ devices_with_circuits
                 ↓
┌─────────────────────────────────────────────────────────┐
│           AUTOLISP GENERATORS                           │
│                                                          │
│  E-101: Uses device['circuit']['id']                   │
│  E-201: Uses device['circuit']['wire_size']   ← MCP!   │
│  E-301: Uses mcp_result.wires directly        ← MCP!   │
│  E-401: Uses mcp_result for panel schedule    ← MCP!   │
│  E-501: Standard details (no MCP data)                 │
│   ↓                                                      │
│  Output: 5 .lsp files with MCP calculations embedded!  │
└─────────────────────────────────────────────────────────┘
```

### **2.3 MCP Data in Drawings**

**ตัวอย่างใน E-201 (Power Plan):**
```lisp
;;; Generated AutoLISP code

; Outlet with circuit info FROM MCP
(command "INSERT" "OUTLET" (list 1000 2000) 1.0 0)
(command "TEXT" (list 1000 1700) 100 0 "CKT-1")
(command "TEXT" (list 1000 1550) 80 0 "2.5mm² 16A")  ← FROM MCP!
                                      ^^^^^^^^^^^^
                           Wire size and breaker from MCP calculations!
```

**ตัวอย่างใน E-401 (Panel Schedule):**
```lisp
; Panel schedule table
; Circuit | Description | Wire | Breaker | Load
;    1    | Power Ckt 1 | 2.5  |   16A   | 3680W  ← ALL FROM MCP!
;    2    | Light Ckt 1 | 1.5  |   10A   | 460W   ← ALL FROM MCP!
```

---

## 🎨 3. AutoLISP Generation Output

### **3.1 Output Format**

**AutoLISP Generation สร้างอะไร:**
- ✅ **ไฟล์ .lsp** (AutoLISP script files)
- ❌ ไม่ใช่ JSON
- ❌ ไม่ใช่ database
- ❌ ไม่ใช่ DXF (แต่รันใน AutoCAD แล้วจะสร้าง DXF ได้)

### **3.2 Output Files**

**5 ไฟล์ที่สร้าง:**
1. `E-101_Lighting_Plan.lsp` (2-3 KB)
2. `E-201_Power_Plan.lsp` (3-4 KB)
3. `E-301_Single_Line_Diagram.lsp` (3-4 KB)
4. `E-401_Panel_Schedule.lsp` (4-5 KB)
5. `E-501_Typical_Details.lsp` (3-4 KB)

**Total:** ~16-18 KB for complete electrical package

### **3.3 File Structure**

**ตัวอย่าง E-201_Power_Plan.lsp:**
```lisp
;;; E-201 - Power Plan
;;; Generated: 2025-11-29
;;; Project: Bedroom Electrical Design

;;; Define main function
(defun C:E201 ()
  (setq oldcmd (getvar "CMDECHO"))
  (setvar "CMDECHO" 0)
  
  ;;; Create layers
  (command "LAYER" "N" "E-OUTLET" "C" "7" "E-OUTLET" "")
  (command "LAYER" "N" "E-WIRE-POWER" "C" "1" "E-WIRE-POWER" "")
  (command "LAYER" "N" "E-ANNOTATION" "C" "8" "E-ANNOTATION" "")
  
  ;;; Set current layer
  (setvar "CLAYER" "E-OUTLET")
  
  ;;; Place outlets
  (command "INSERT" "OUTLET" (list 1000.0 0.0) 1.0 0)
  (command "INSERT" "OUTLET" (list 3000.0 0.0) 1.0 0)
  (command "INSERT" "OUTLET" (list 4000.0 2000.0) 1.0 0)
  ; ... more outlets
  
  ;;; Add circuit labels (FROM MCP!)
  (setvar "CLAYER" "E-ANNOTATION")
  (command "TEXT" (list 1000.0 -300.0) 100 0 "CKT-1")
  (command "TEXT" (list 1000.0 -450.0) 80 0 "2.5mm² 16A")
  ; ... more labels
  
  ;;; Route wiring
  (setvar "CLAYER" "E-WIRE-POWER")
  (command "PLINE" (list 1000.0 0.0) (list 3000.0 0.0) "")
  (command "PLINE" (list 3000.0 0.0) (list 4000.0 0.0) "")
  ; ... more wiring
  
  ;;; Add legend
  ; ...
  
  (setvar "CMDECHO" oldcmd)
  (princ "\nPower plan loaded. Type E201 to execute.")
  (princ)
)

;;; Auto-load message
(princ "\nType E201 to generate power plan")
(princ)
```

### **3.4 How to Use**

**ใน AutoCAD:**
```
1. Open AutoCAD
2. Type: APPLOAD
3. Select: E-201_Power_Plan.lsp
4. Type: E201
5. Drawing appears!
```

---

## 🔄 4. Complete Workflow Diagram

### **4.1 Overall System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG KNOWLEDGE                           │
│                                                                  │
│  catalog_rows.csv (118 rows)                                   │
│  ├─ Appliances (13 items)                                      │
│  ├─ Cable specs (9 types)                                      │
│  ├─ Derating factors (6 tables)                                │
│  ├─ Room templates (6 types)                                   │
│  ├─ Device codes (40+ items)                                   │
│  ├─ Placement rules                                            │
│  └─ Validation rules (8 rules)                                 │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ Load standards & templates
               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT STAGE                                 │
│                                                                  │
│  User provides room data (JSON or Dict):                        │
│  {                                                               │
│    "room_type": "bedroom",                                      │
│    "dimensions": {"length": 4000, "width": 6000},              │
│    "loads": [                                                   │
│      {"name": "Lighting", "watts": 200},                       │
│      {"name": "Outlets", "watts": 1800}                        │
│    ],                                                            │
│    "voltage": 230,                                              │
│    "standard": "EIT"                                            │
│  }                                                               │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────────┐
│                   STAGE 1: MCP CALCULATIONS                      │
│                   (Existing pipeline.py)                         │
│                                                                  │
│  Input: Load data                                               │
│   ↓                                                              │
│  [Load Calculator]                                              │
│   - Calculate total VA                                          │
│   - Apply demand factors                                        │
│   ↓                                                              │
│  [Wire Sizer]                                                   │
│   - Calculate wire size (2.5mm², 1.5mm²)                       │
│   - Apply derating factors                                      │
│   - Calculate voltage drop                                      │
│   ↓                                                              │
│  [Breaker Selector]                                             │
│   - Select breaker rating (16A, 10A)                           │
│   - Determine poles (1ph, 3ph)                                 │
│   ↓                                                              │
│  [Conduit Sizer]                                                │
│   - Determine conduit size                                      │
│   ↓                                                              │
│  Output: mcp_result {                                           │
│    wires: [                                                     │
│      {size_mm2: 2.5, current: 10.5, conduit: '20mm'},         │
│      {size_mm2: 1.5, current: 5.2, conduit: '16mm'}           │
│    ],                                                            │
│    breakers: [                                                  │
│      {rating: 16, poles: 1},                                   │
│      {rating: 10, poles: 1}                                    │
│    ],                                                            │
│    voltage: 230,                                                │
│    voltage_drop: 2.3%                                           │
│  }                                                               │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ mcp_result
               ↓
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 2: DEVICE PLACEMENT (Phase B)                 │
│                                                                  │
│  [Get Room Template]                                            │
│   - From predefined (6 types) OR                               │
│   - From DXF file (Phase C)                                    │
│   ↓                                                              │
│  [Device Placer]                                                │
│   - Place outlets (walls, spacing rules)                       │
│   - Place lights (ceiling, grid/centroid)                      │
│   - Place switches (near door)                                 │
│   ↓                                                              │
│  Output: devices {                                              │
│    outlets: [                                                   │
│      {id: 'OUT-001', position: (1000,0),                       │
│       circuit: None, device_code: 'OUT-16A'},                  │
│      ...                                                         │
│    ],                                                            │
│    lights: [...],                                               │
│    switches: [...]                                              │
│  }                                                               │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ devices (circuit=None)
               ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 3: CIRCUIT ASSIGNMENT (Phase D) ← KEY!            │
│                                                                  │
│  [Circuit Assigner]                                             │
│   Takes: devices + mcp_result                                  │
│   ↓                                                              │
│   For each device:                                             │
│     device['circuit'] = {                                       │
│       'id': 'CKT-1',                                            │
│       'wire_size': mcp_result.wires[i].size_mm2, ← FROM MCP!   │
│       'breaker': mcp_result.breakers[i].rating   ← FROM MCP!   │
│     }                                                            │
│   ↓                                                              │
│  Output: devices_with_circuits {                                │
│    outlets: [                                                   │
│      {id: 'OUT-001', position: (1000,0),                       │
│       circuit: {id: 'CKT-1', wire: '2.5mm²',                   │
│                 breaker: '16A'}},  ← MCP DATA!                 │
│      ...                                                         │
│    ],                                                            │
│    lights: [...],  ← Also has MCP data                         │
│    switches: [...]                                              │
│  }                                                               │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ devices_with_circuits
               ↓
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 4: WIRE ROUTING (Phase C)                     │
│                                                                  │
│  [Wire Router]                                                  │
│   - Route lighting circuits (switch → lights)                  │
│   - Route power circuits (daisy-chain outlets)                 │
│   - Generate homerun arrows (to panel)                         │
│   - Use orthogonal (H+V) algorithm                             │
│   ↓                                                              │
│  Output: routes [                                               │
│    {from: switch, to: light1, path: [(x,y),...]},              │
│    {from: switch, to: panel, path: [...],                      │
│     wire_type: 'homerun'},  ← Gets arrow                       │
│    ...                                                           │
│  ]                                                               │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ routes
               ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 5: AUTOLISP GENERATION (Phases A+D)               │
│                                                                  │
│  [E-101 Generator] ← uses devices_with_circuits + routes       │
│   ↓                                                              │
│  E-101_Lighting_Plan.lsp (2-3 KB)                              │
│   - Lights with circuit labels                                 │
│   - Switches                                                     │
│   - Wiring with homerun arrows                                 │
│   - Legend                                                       │
│                                                                  │
│  [E-201 Generator] ← uses devices_with_circuits + routes       │
│   ↓                                                              │
│  E-201_Power_Plan.lsp (3-4 KB)                                 │
│   - Outlets with circuit labels                                │
│   - Circuit info: CKT-1 (2.5mm² 16A) ← FROM MCP!              │
│   - Power wiring                                                │
│   - Legend                                                       │
│                                                                  │
│  [E-301 Generator] ← uses mcp_result directly                  │
│   ↓                                                              │
│  E-301_Single_Line_Diagram.lsp (3-4 KB)                        │
│   - Panel symbol                                                │
│   - Breakers with ratings from MCP                             │
│   - Wire sizes from MCP                                         │
│   - Load connections                                            │
│                                                                  │
│  [E-401 Generator] ← uses mcp_result for schedule              │
│   ↓                                                              │
│  E-401_Panel_Schedule.lsp (4-5 KB)                             │
│   - 12-column table                                             │
│   - Circuit list with MCP data                                 │
│   - Total loads from MCP                                        │
│                                                                  │
│  [E-501 Generator] ← standard details                          │
│   ↓                                                              │
│  E-501_Typical_Details.lsp (3-4 KB)                            │
│   - Mounting details                                            │
│   - Wire specifications                                         │
│   - Symbol legend                                               │
│                                                                  │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │ 5 .lsp files
               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT STAGE                                │
│                                                                  │
│  Complete Electrical Package:                                   │
│  ├─ E-101_Lighting_Plan.lsp                                    │
│  ├─ E-201_Power_Plan.lsp                                       │
│  ├─ E-301_Single_Line_Diagram.lsp                              │
│  ├─ E-401_Panel_Schedule.lsp                                   │
│  ├─ E-501_Typical_Details.lsp                                  │
│  └─ package_summary.json (metadata)                            │
│                                                                  │
│  Total: ~16-18 KB                                               │
│  Ready for AutoCAD import!                                      │
│                                                                  │
│  In AutoCAD:                                                    │
│    1. APPLOAD → select .lsp file                               │
│    2. Type command (E101, E201, etc.)                          │
│    3. Drawing appears with all MCP calculations embedded!      │
└─────────────────────────────────────────────────────────────────┘
```

### **4.2 Data Flow Summary**

```
JSON Input (Room Data)
  ↓
MCP Pipeline (calculations)
  ↓
mcp_result {wires, breakers, voltage}
  ↓ ←────────────┐
  ↓              │
Device Placement │ (uses standards)
  ↓              │
devices {outlets, lights, switches, circuit=None}
  ↓              │
Circuit Assigner │ ← Connects MCP data!
  ↓              │
devices_with_circuits {circuit={wire_size, breaker} FROM MCP}
  ↓              │
Wire Routing     │
  ↓              │
routes {paths, homerun arrows}
  ↓              │
AutoLISP Generators (5 files)
  ↓ ──────────all use MCP data!
5 .lsp files
  ↓
AutoCAD drawings with MCP calculations embedded!
```

---

## 📝 5. Code Reference

### **5.1 File Organization**

```
mcp_core_v2/
├─ pipeline.py                      (Existing MCP - calculations)
├─ integration.py                   (NEW - Bridge MCP ↔ AutoLISP)
│
├─ cad/                             (ALL NEW - AutoLISP generation)
│  ├─ __init__.py
│  ├─ autolisp_writer.py           (Phase A)
│  │
│  ├─ standards/                    (Phase A)
│  │  ├─ __init__.py
│  │  └─ standard_loader.py
│  │
│  ├─ drawing/                      (Phases A + D)
│  │  ├─ __init__.py
│  │  ├─ sld_generator.py          (Phase A - E-301)
│  │  ├─ panel_schedule_generator.py (Phase A - E-401)
│  │  ├─ lighting_plan_generator.py (Phase D - E-101)
│  │  ├─ power_plan_generator.py   (Phase D - E-201)
│  │  └─ details_generator.py      (Phase D - E-501)
│  │
│  ├─ validators/                   (Phases A + B)
│  │  ├─ __init__.py
│  │  ├─ lisp_validator.py         (Phase A)
│  │  └─ placement_validator.py    (Phase B)
│  │
│  ├─ geometry/                     (Phase B)
│  │  ├─ __init__.py
│  │  └─ room_templates.py
│  │
│  ├─ placement/                    (Phases B + D)
│  │  ├─ __init__.py
│  │  ├─ device_placer.py          (Phase B)
│  │  └─ circuit_assigner.py       (Phase D - MCP bridge!)
│  │
│  ├─ dxf/                          (Phase C)
│  │  ├─ __init__.py
│  │  └─ dxf_reader.py
│  │
│  ├─ routing/                      (Phase C)
│  │  ├─ __init__.py
│  │  └─ wire_router.py
│  │
│  └─ test_dxf/                     (Phase C - mock files)
│     ├─ house_1floor_simple.dxf
│     └─ house_2rooms.dxf
│
├─ test_phase_a_complete.py
├─ test_phase_b_complete.py
├─ test_phase_c_complete.py
├─ test_phase_d_complete.py
└─ test_complete_integration.py     (MCP ↔ AutoLISP test)
```

### **5.2 Key Functions**

**MCP Side:**
- `pipeline.execute()` - Run MCP calculations
- Returns: `mcp_result` with wires, breakers

**AutoLISP Side:**
- `DevicePlacer.place_all_devices()` - Place devices
- `assign_circuits()` - Assign MCP data to devices ← KEY!
- `route_wires()` - Route wiring
- `LightingPlanGenerator.generate()` - E-101
- `PowerPlanGenerator.generate()` - E-201
- `SingleLineDiagramGenerator.generate()` - E-301
- `PanelScheduleGenerator.generate()` - E-401
- `DetailsGenerator.generate()` - E-501

**Integration:**
- `generate_complete_electrical_package()` - Complete workflow!

---

## 🧪 6. Testing

### **6.1 Test Coverage**

**Total: 25 tests (24 phase tests + 1 integration)**

**Phase A:** 6/6 tests
**Phase B:** 6/6 tests
**Phase C:** 6/6 tests
**Phase D:** 6/6 tests
**Integration:** 1/1 test

**All tests passing:** ✅ 25/25

### **6.2 Integration Test Proof**

**Test:** `test_complete_integration.py`

**What it proves:**
```
✓ MCP calculations run successfully
✓ Devices placed in room
✓ Circuits assigned FROM MCP (wire sizes, breakers)
✓ Wires routed with homerun arrows
✓ All 5 drawings generated (16+ KB total)
✓ MCP data embedded in drawings
✓ Complete workflow functional
```

**Evidence:**
```
Devices: 9 outlets, 3 lights, 1 switch
Circuits: 2 (from MCP)
Circuit info: wire=2.5mm², breaker=16A ← FROM MCP!
Wire routes: 13
Drawings: 5 files (~16 KB)
```

---

## 📊 Summary

### **What We Built:**

1. ✅ **Phase A:** Standards + Base AutoLISP + E-301 + E-401
2. ✅ **Phase B:** 6 Room Templates + Device Placement
3. ✅ **Phase C:** DXF Reader + Wire Router
4. ✅ **Phase D:** Circuit Assignment + E-101 + E-201 + E-501
5. ✅ **Integration:** MCP ↔ AutoLISP Bridge

### **How It Works:**

```
User Input (JSON) 
  → MCP Calculations (wire sizes, breakers)
  → Device Placement (outlets, lights, switches)
  → Circuit Assignment (MCP data → devices) ← KEY CONNECTION!
  → Wire Routing (orthogonal paths)
  → AutoLISP Generation (5 drawing files)
  → Ready for AutoCAD!
```

### **Output:**

- **Format:** `.lsp` files (AutoLISP scripts)
- **Quantity:** 5 files per room
- **Size:** ~16-18 KB total
- **Content:** Fully detailed electrical drawings with MCP calculations embedded

### **Key Achievement:**

**การเชื่อมต่อฝั่งคำนวณ (MCP) กับฝั่ง AutoLISP สำเร็จแล้ว!**

MCP calculations (wire sizes, breakers) → ถูกนำไปใช้ใน AutoLISP drawings โดยอัตโนมัติ ผ่าน `integration.py` และ `circuit_assigner.py`!

---

**Date:** 2025-11-29  
**Status:** ✅ Complete & Ready for Production
