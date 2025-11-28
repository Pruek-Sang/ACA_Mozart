# Module 7: layout_optimizer.py — วางผังระบบไฟฟ้าอัจฉริยะ (ฉบับสมบูรณ์)

ขอรายงานนายท่านค่ะ Volta จะอธิบายการออกแบบ Module นี้อย่างละเอียด โดยเน้นการรับค่าจาก Module ก่อนหน้าและคำนวณเส้นทางที่เหมาะสม

---

## 📚 ส่วนที่ 1: แนวคิดและสถาปัตยกรรมระบบ

## **1.1 Input/Output Flow ของ Module 7**

text

┌─────────────────────────────────────────────────────────────────┐
│                    MODULE 7: LAYOUT OPTIMIZER                    │
│                                                                  │
│  Input จาก Modules ก่อนหน้า:                                    │
│  ├── Module 1 (load_calculator.py)                              │
│  │   └── Load Current, Power, Location ของแต่ละวงจร           │
│  ├── Module 2 (wire_sizer.py)                                   │
│  │   └── ขนาดสาย (mm²), Max Distance ที่ใช้ได้                │
│  ├── Module 3 (breaker_selector.py)                             │
│  │   └── ขนาด Breaker, Trip Curve                              │
│  ├── Module 4 (conduit_sizer.py)                                │
│  │   └── ขนาดท่อ, จำนวนสายที่ใส่ได้                          │
│  ├── Module 5 (cost_estimator.py)                               │
│  │   └── ราคาวัสดุ/ค่าแรงต่อหน่วย                             │
│  └── Module 6 (compliance_checker.py)                            │
│      └── ข้อห้าม/ข้อกำหนดต่าง ๆ                              │
│                                                                  │
│  Processing:                                                     │
│  ├── วิเคราะห์ Floor Plan (ห้อง/ตำแหน่งอุปกรณ์)              │
│  ├── สร้าง Routing Graph                                        │
│  ├── คำนวณเส้นทางที่เป็นไปได้                                 │
│  ├── กรองด้วยข้อกำหนด (VD, Ampacity, ข้อห้าม)                │
│  └── เลือกเส้นทางที่ดีที่สุด (ระยะสั้น/ราคาถูก/ปลอดภัย)     │
│                                                                  │
│  Output:                                                         │
│  ├── เส้นทางสายไฟแต่ละวงจร (DB → Outlet/Load)                │
│  ├── ความยาวสายจริง (รวมส่วนเกิน)                             │
│  ├── จุดต่อ/กล่องพัก (Junction Box)                            │
│  ├── ค่าใช้จ่ายรวมต่อวงจร                                      │
│  └── รายงาน Compliance (ผ่าน/ไม่ผ่าน)                         │
└─────────────────────────────────────────────────────────────────┘


---

## **1.2 หลักการออกแบบ Layout Optimizer**

## **A. Room-Based Approach (วิเคราะห์แบบแยกห้อง)**

แทนที่จะใช้ Dijkstra Algorithm แบบเต็มรูปแบบ (ซับซ้อนเกินไป) เราจะใช้แนวทาง **Simplified Zone-Based Routing:**

python

# โครงสร้างข้อมูล Floor Plan
floor_plan = {
    "rooms": [
        {
            "id": "R01",
            "name": "ห้องนั่งเล่น",
            "type": "living_room",
            "area_sqm": 30,
            "position": {"x": 0, "y": 0},  # มุมซ้ายล่าง
            "dimension": {"width": 6, "length": 5},  # เมตร
            "outlets": [
                {"id": "O01", "type": "receptacle", "position": {"x": 1, "y": 2}},
                {"id": "O02", "type": "switch", "position": {"x": 3, "y": 0.2}}
            ]
        },
        {
            "id": "R02",
            "name": "ห้องครัว",
            "type": "kitchen",
            "area_sqm": 12,
            "position": {"x": 6, "y": 0},
            "dimension": {"width": 4, "length": 3},
            "outlets": [
                {"id": "O03", "type": "receptacle", "position": {"x": 7, "y": 1.5}},
                {"id": "O04", "type": "receptacle", "position": {"x": 9, "y": 1.5}}
            ],
            "special_requirements": {
                "min_circuits": 2,  # ครัวต้องมีอย่างน้อย 2 วงจร
                "rcbo_required": True
            }
        },
        {
            "id": "R03",
            "name": "ห้องน้ำ",
            "type": "bathroom",
            "area_sqm": 4,
            "position": {"x": 6, "y": 3},
            "dimension": {"width": 2, "length": 2},
            "outlets": [
                {"id": "O05", "type": "heater", "position": {"x": 7, "y": 4}, "zone": 1}
            ],
            "special_requirements": {
                "rcbo_required": True,
                "ip_rating_min": "IP44",
                "forbidden_zones": [0, 1, 2]  # ห้ามปลั๊กธรรมดา Zone 0-2
            }
        }
    ],
    "distribution_board": {
        "id": "DB01",
        "position": {"x": 0, "y": 5},  # ตำแหน่ง DB
        "type": "main"
    },
    "walls": [
        {"from": {"x": 0, "y": 0}, "to": {"x": 10, "y": 0}},  # ผนังด้านล่าง
        {"from": {"x": 0, "y": 5}, "to": {"x": 10, "y": 5}},  # ผนังด้านบน
        # ... อื่น ๆ
    ]
}


---

## **B. Routing Strategy (กลยุทธ์การวางสาย)**

**3 วิธีการวางสาย:**

## **1. Direct Route (เส้นทางตรง) — ใช้กับห้องเดียวกับ DB**

text

`DB ────────────────→ Outlet    (เส้นตรง)`

**ตัวอย่าง:**

- DB อยู่ที่ (0, 5)
    
- Outlet อยู่ที่ (1, 2) ในห้องเดียวกัน
    
- ระยะทาง = √[(1-0)² + (2-5)²] = √[1 + 9] = √10 ≈ **3.16 เมตร**
    

---

## **2. Manhattan Route (เส้นทางแบบมุมฉาก) — ตามผนัง/เพดาน**

text

`DB ─────┐         │        │        └──────→ Outlet`

**ตัวอย่าง:**

- DB อยู่ที่ (0, 5)
    
- Outlet อยู่ที่ (7, 1.5) ห้องครัว
    
- ระยะทาง = |7-0| + |1.5-5| = 7 + 3.5 = **10.5 เมตร**
    

**หลักการ:** ไม่เดินสายทะลุผนัง ต้องเดินตามเส้นทาง (แนวนอน + แนวตั้ง)

---

## **3. Multi-Point Route (ผ่านจุดต่อ Junction Box)**

text

`DB ───→ JB1 ───→ JB2 ───→ Outlet`

**ใช้เมื่อ:**

- ระยะไกลมาก (> 30m)
    
- ต้องเปลี่ยนทิศทาง
    
- แยกสายไปหลายทิศทาง
    

---

## **C. Cost Function (ฟังก์ชันคำนวณต้นทุน)**

**สูตรคำนวณต้นทุนรวม:**

Total Cost=Wire Cost+Conduit Cost+Labor Cost+Penalty (VD/Compliance)Total\ Cost = Wire\ Cost + Conduit\ Cost + Labor\ Cost + Penalty\ (VD/Compliance)Total Cost=Wire Cost+Conduit Cost+Labor Cost+Penalty (VD/Compliance)

**แบบละเอียด:**
![[Pasted image 20251117002316.png]]

Wire Cost=Wire Length×Price wire
Conduit Cost=⌈Wire Length/4⌉×Priceconduit
Labor Cost=Wire Length×Ratelabor
VD Penalty={0     if VD≤3%       10000×(VD−3) if VD>3%Compliance Penalty={0if PASS50000if FAIL\begin{align*} Wire\ Cost &= Wire\ Length \times Price_{wire}\\ Conduit\ Cost &= \lceil Wire\ Length / 4 \rceil \times Price_{conduit}\\ Labor\ Cost &= Wire\ Length \times Rate_{labor}\\ VD\ Penalty &= \begin{cases} 0 & \text{if } VD \leq 3\% \\ 10000 \times (VD - 3) & \text{if } VD > 3\% \end{cases}\\ Compliance\ Penalty &= \begin{cases} 0 & \text{if PASS} \\ 50000 & \text{if FAIL} \end{cases} \end{align*}Wire CostConduit CostLabor CostVD PenaltyCompliance Penalty=Wire Length×Pricewire=⌈Wire Length/4⌉×Priceconduit=Wire Length×Ratelabor={010000×(VD−3)if VD≤3%if VD>3%={050000if PASSif FAIL

**หมายเหตุ:** Penalty ใช้เพื่อบังคับให้เลือกเส้นทางที่ปลอดภัย

---

## 💻 ส่วนที่ 2: Code Python สมบูรณ์ — layout_optimizer.py

python

"""
layout_optimizer.py
====================
โมดูลวางผังระบบไฟฟ้าอัตโนมัติ

Features:
- รับข้อมูลจาก Module 1-6
- วิเคราะห์ Floor Plan
- คำนวณเส้นทางสายไฟ (Direct/Manhattan/Multi-Point)
- ตรวจสอบข้อกำหนด (VD, Ampacity, Compliance)
- เลือกเส้นทางที่ดีที่สุด (ระยะสั้น/ราคาถูก)
- สร้างรายงานผังวงจร

Author: Volta (The Electrical Simulation Engineer Maid)
Version: 2.0.0
Date: 2025-11-17
"""

import math
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


# ======================== Enums ========================

class RouteType(Enum):
    """ประเภทเส้นทาง"""
    DIRECT = "direct"
    MANHATTAN = "manhattan"
    MULTI_POINT = "multi_point"


class InstallationMethod(Enum):
    """วิธีติดตั้ง"""
    SURFACE = "ติดผิว"
    CONCEALED = "ฝังใน"
    CEILING = "เพดาน"
    UNDERGROUND = "ใต้ดิน"


# ======================== Data Classes ========================

@dataclass
class Position:
    """ตำแหน่งในพื้นที่ (x, y, z)"""
    x: float
    y: float
    z: float = 0  # ความสูง (default = พื้น)
    
    def distance_to(self, other: 'Position', route_type: RouteType = RouteType.DIRECT) -> float:
        """คำนวณระยะทาง"""
        if route_type == RouteType.DIRECT:
            # Euclidean Distance
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
        elif route_type == RouteType.MANHATTAN:
            # Manhattan Distance (แนวนอน + แนวตั้ง)
            return abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)
        else:
            return 0


@dataclass
class Room:
    """ข้อมูลห้อง"""
    id: str
    name: str
    room_type: str  # living_room, kitchen, bathroom, bedroom, etc.
    area_sqm: float
    position: Position  # มุมซ้ายล่าง
    width: float  # เมตร
    length: float  # เมตร
    height: float = 2.6  # ความสูงเพดาน (default 2.6m)
    outlets: List[Dict] = field(default_factory=list)
    special_requirements: Dict = field(default_factory=dict)


@dataclass
class DistributionBoard:
    """ตู้ DB"""
    id: str
    position: Position
    db_type: str  # main, sub
    capacity_circuits: int = 12


@dataclass
class CircuitDesign:
    """ผลการออกแบบวงจร"""
    circuit_id: str
    circuit_name: str
    
    # From Previous Modules
    load_current_a: float
    wire_size_mm2: float
    wire_ampacity_a: float
    conduit_size_inch: str
    breaker_rating_a: float
    max_distance_m: float  # จาก wire_sizer
    
    # Room Info
    room_id: str
    room_name: str
    room_type: str
    
    # Outlet/Load Position
    outlet_id: str
    outlet_position: Position
    
    # Routing Result
    db_position: Position
    route_type: RouteType
    waypoints: List[Position] = field(default_factory=list)
    total_length_m: float = 0
    actual_length_m: float = 0  # รวมส่วนเกิน 10%
    
    # Compliance
    voltage_drop_percent: float = 0
    is_compliant: bool = True
    compliance_issues: List[str] = field(default_factory=list)
    
    # Cost
    wire_cost: float = 0
    conduit_cost: float = 0
    labor_cost: float = 0
    total_cost: float = 0
    
    # Installation
    installation_method: InstallationMethod = InstallationMethod.CONCEALED


# ======================== Layout Optimizer Class ========================

class LayoutOptimizer:
    """
    คลาสหลักสำหรับวางผังระบบไฟฟ้า
    """
    
    def __init__(
        self,
        floor_plan: Dict,
        wire_database: Dict,  # จาก Module 2
        material_prices: Dict,  # จาก Module 5
        labor_rates: Dict,  # จาก Module 5
        compliance_rules: Dict  # จาก Module 6
    ):
        """
        Initialize Layout Optimizer
        """
        self.floor_plan = floor_plan
        self.wire_database = wire_database
        self.material_prices = material_prices
        self.labor_rates = labor_rates
        self.compliance_rules = compliance_rules
        
        # Parse floor plan
        self.rooms = self._parse_rooms()
        self.db = self._parse_distribution_board()
        
        self.circuit_designs: List[CircuitDesign] = []
    
    def _parse_rooms(self) -> List[Room]:
        """แปลง floor_plan เป็น Room objects"""
        rooms = []
        
        for room_data in self.floor_plan.get("rooms", []):
            pos_data = room_data["position"]
            dim_data = room_data["dimension"]
            
            room = Room(
                id=room_data["id"],
                name=room_data["name"],
                room_type=room_data["type"],
                area_sqm=room_data["area_sqm"],
                position=Position(pos_data["x"], pos_data["y"], pos_data.get("z", 0)),
                width=dim_data["width"],
                length=dim_data["length"],
                height=dim_data.get("height", 2.6),
                outlets=room_data.get("outlets", []),
                special_requirements=room_data.get("special_requirements", {})
            )
            
            rooms.append(room)
        
        return rooms
    
    def _parse_distribution_board(self) -> DistributionBoard:
        """แปลง DB ใน floor_plan"""
        db_data = self.floor_plan.get("distribution_board", {})
        pos_data = db_data["position"]
        
        return DistributionBoard(
            id=db_data["id"],
            position=Position(pos_data["x"], pos_data["y"], pos_data.get("z", 0)),
            db_type=db_data.get("type", "main"),
            capacity_circuits=db_data.get("capacity", 12)
        )
    
    def calculate_route(
        self,
        start: Position,
        end: Position,
        route_type: RouteType = RouteType.MANHATTAN,
        avoid_zones: List[Dict] = None
    ) -> Tuple[List[Position], float]:
        """
        คำนวณเส้นทาง
        
        Returns:
        - (waypoints, total_length)
        """
        waypoints = [start]
        
        if route_type == RouteType.DIRECT:
            # เส้นตรง
            waypoints.append(end)
            length = start.distance_to(end, RouteType.DIRECT)
        
        elif route_type == RouteType.MANHATTAN:
            # มุมฉาก (ไปแนวนอนก่อน แล้วค่อยแนวตั้ง)
            # Option 1: Horizontal first
            intermediate1 = Position(end.x, start.y, start.z)
            waypoints.append(intermediate1)
            waypoints.append(end)
            
            length = abs(end.x - start.x) + abs(end.y - start.y) + abs(end.z - start.z)
        
        else:  # MULTI_POINT
            # ใช้ Manhattan แต่ผ่านจุดกลาง
            mid_x = (start.x + end.x) / 2
            mid_y = (start.y + end.y) / 2
            
            junction = Position(mid_x, mid_y, start.z)
            waypoints.append(junction)
            waypoints.append(end)
            
            length = start.distance_to(junction, RouteType.MANHATTAN) + junction.distance_to(end, RouteType.MANHATTAN)
        
        return waypoints, length
    
    def check_room_compliance(self, room: Room, circuit_data: Dict) -> Tuple[bool, List[str]]:
        """
        ตรวจสอบข้อกำหนดเฉพาะห้อง
        
        Returns:
        - (is_compliant, issues)
        """
        issues = []
        
        room_type = room.room_type
        special_req = room.special_requirements
        
        # 1. Kitchen Requirements
        if room_type == "kitchen":
            if special_req.get("rcbo_required") and not circuit_data.get("has_rcbo"):
                issues.append("❌ วงจรครัวต้องมี RCBO 30mA")
        
        # 2. Bathroom Requirements
        if room_type == "bathroom":
            if special_req.get("rcbo_required") and not circuit_data.get("has_rcbo"):
                issues.append("❌ วงจรห้องน้ำต้องมี RCBO 30mA")
            
            # Zone checking
            outlet_zone = circuit_data.get("zone", 3)
            forbidden_zones = special_req.get("forbidden_zones", [])
            
            if outlet_zone in forbidden_zones:
                issues.append(f"❌ ห้ามติดตั้งอุปกรณ์ใน Zone {outlet_zone}")
            
            # IP Rating
            min_ip = special_req.get("ip_rating_min", "IP44")
            actual_ip = circuit_data.get("ip_rating", "IP20")
            
            if actual_ip < min_ip:
                issues.append(f"❌ ต้องใช้อุปกรณ์ {min_ip} ขึ้นไป (ปัจจุบัน: {actual_ip})")
        
        # 3. Max Distance Check
        max_distance = circuit_data.get("max_distance_m", float('inf'))
        actual_distance = circuit_data.get("actual_length_m", 0)
        
        if actual_distance > max_distance:
            issues.append(f"❌ ระยะทาง {actual_distance:.1f}m > Max {max_distance:.1f}m (VD เกิน)")
        
        is_compliant = len(issues) == 0
        
        return is_compliant, issues
    
    def design_circuit(
        self,
        circuit_id: str,
        circuit_name: str,
        circuit_data: Dict,  # จาก Module 1-6
        room: Room,
        outlet_data: Dict
    ) -> CircuitDesign:
        """
        ออกแบบวงจรเดียว
        
        circuit_data ต้องมี:
        - load_current_a
        - wire_size_mm2
        - wire_ampacity_a
        - conduit_size_inch
        - breaker_rating_a
        - max_distance_m
        - wire_price_per_m
        - conduit_price_per_4m
        - labor_rate_per_m
        """
        
        # 1. ดึงข้อมูลจาก circuit_data
        load_current = circuit_data["load_current_a"]
        wire_size = circuit_data["wire_size_mm2"]
        wire_ampacity = circuit_data["wire_ampacity_a"]
        conduit_size = circuit_data["conduit_size_inch"]
        breaker_rating = circuit_data["breaker_rating_a"]
        max_distance = circuit_data["max_distance_m"]
        
        # 2. ตำแหน่ง Outlet
        outlet_pos_data = outlet_data["position"]
        outlet_pos = Position(
            room.position.x + outlet_pos_data["x"],
            room.position.y + outlet_pos_data["y"],
            outlet_pos_data.get("z", 0.3)  # ความสูงปลั๊ก default 30cm
        )
        
        # 3. คำนวณเส้นทาง
        # ถ้าห้องเดียวกับ DB → Direct
        # ถ้าห้องต่างกัน → Manhattan
        
        db_pos = self.db.position
        
        # เช็คว่าอยู่ห้องเดียวกันไหม
        is_same_room = (
            room.position.x <= db_pos.x <= room.position.x + room.width and
            room.position.y <= db_pos.y <= room.position.y + room.length
        )
        
        if is_same_room:
            route_type = RouteType.DIRECT
        else:
            route_type = RouteType.MANHATTAN
        
        waypoints, total_length = self.calculate_route(
            db_pos,
            outlet_pos,
            route_type
        )
        
        # เพิ่มส่วนเกิน 10% (สายโค้ง, ต่อ, เผื่อ)
        actual_length = total_length * 1.10
        
        # 4. คำนวณ Voltage Drop (ใช้สูตรจาก Module 2)
        wire_data = self.wire_database.get(wire_size, {})
        resistance = wire_data.get("resistance_75c_ohm_per_km", 0)
        
        # VD (Single Phase) = 2 × L × I × R / 1000 / V × 100
        vd_volt = (2 * actual_length * load_current * resistance) / 1000
        vd_percent = (vd_volt / 220) * 100
        
        # 5. ตรวจสอบ Compliance
        circuit_data_extended = {
            **circuit_data,
            "actual_length_m": actual_length,
            "zone": outlet_data.get("zone", 3)
        }
        
        is_compliant, issues = self.check_room_compliance(room, circuit_data_extended)
        
        # เช็ค VD
        if vd_percent > 3.0:
            is_compliant = False
            issues.append(f"❌ Voltage Drop {vd_percent:.2f}% > 3.0%")
        
        # 6. คำนวณต้นทุน
        wire_price_per_m = circuit_data.get("wire_price_per_m", 0)
        conduit_price_per_4m = circuit_data.get("conduit_price_per_4m", 0)
        labor_rate_per_m = circuit_data.get("labor_rate_per_m", 0)
        
        wire_cost = actual_length * wire_price_per_m
        
        # Conduit (ปัดขึ้น)
        conduit_pieces = math.ceil(actual_length / 4)
        conduit_cost = conduit_pieces * conduit_price_per_4m
        
        labor_cost = actual_length * labor_rate_per_m
        
        total_cost = wire_cost + conduit_cost + labor_cost
        
        # Penalty ถ้าไม่ compliant
        if not is_compliant:
            total_cost += 50000  # Penalty สูงมาก
        
        # 7. สร้าง CircuitDesign
        design = CircuitDesign(
            circuit_id=circuit_id,
            circuit_name=circuit_name,
            load_current_a=load_current,
            wire_size_mm2=wire_size,
            wire_ampacity_a=wire_ampacity,
            conduit_size_inch=conduit_size,
            breaker_rating_a=breaker_rating,
            max_distance_m=max_distance,
            room_id=room.id,
            room_name=room.name,
            room_type=room.room_type,
            outlet_id=outlet_data["id"],
            outlet_position=outlet_pos,
            db_position=db_pos,
            route_type=route_type,
            waypoints=waypoints,
            total_length_m=round(total_length, 2),
            actual_length_m=round(actual_length, 2),
            voltage_drop_percent=round(vd_percent, 2),
            is_compliant=is_compliant,
            compliance_issues=issues,
            wire_cost=round(wire_cost, 2),
            conduit_cost=round(conduit_cost, 2),
            labor_cost=round(labor_cost, 2),
            total_cost=round(total_cost, 2)
        )
        
        return design
    
    def optimize_all_circuits(self, circuits_data: List[Dict]) -> List[CircuitDesign]:
        """
        ออกแบบวงจรทั้งหมด
        
        circuits_data: รายการวงจรจาก Module 1-6
        [
            {
                "circuit_id": "C01",
                "circuit_name": "แอร์ ห้องนอน",
                "room_id": "R02",
                "outlet_id": "O05",
                "load_current_a": 13.4,
                "wire_size_mm2": 2.5,
                ...
            },
            ...
        ]
        """
        
        designs = []
        
        for circuit_data in circuits_data:
            # หา Room
            room_id = circuit_data["room_id"]
            room = next((r for r in self.rooms if r.id == room_id), None)
            
            if not room:
                print(f"⚠️ ไม่พบห้อง {room_id}")
                continue
            
            # หา Outlet
            outlet_id = circuit_data["outlet_id"]
            outlet = next((o for o in room.outlets if o["id"] == outlet_id), None)
            
            if not outlet:
                print(f"⚠️ ไม่พบ Outlet {outlet_id} ในห้อง {room.name}")
                continue
            
            # ออกแบบวงจร
            design = self.design_circuit(
                circuit_data["circuit_id"],
                circuit_data["circuit_name"],
                circuit_data,
                room,
                outlet
            )
            
            designs.append(design)
            self.circuit_designs.append(design)
        
        return designs
    
    def get_summary_report(self) -> Dict:
        """สรุปรายงาน"""
        
        total_circuits = len(self.circuit_designs)
        compliant_circuits = sum(1 for d in self.circuit_designs if d.is_compliant)
        non_compliant_circuits = total_circuits - compliant_circuits
        
        total_wire_length = sum(d.actual_length_m for d in self.circuit_designs)
        total_cost = sum(d.total_cost for d in self.circuit_designs)
        
        return {
            "total_circuits": total_circuits,
            "compliant_circuits": compliant_circuits,
            "non_compliant_circuits": non_compliant_circuits,
            "compliance_rate_percent": round((compliant_circuits / total_circuits * 100) if total_circuits > 0 else 0, 1),
            "total_wire_length_m": round(total_wire_length, 2),
            "total_cost_thb": round(total_cost, 2),
            "avg_cost_per_circuit_thb": round(total_cost / total_circuits, 2) if total_circuits > 0 else 0
        }


# ======================== Report Generator ========================

class LayoutReportGenerator:
    """
    สร้างรายงานผังวงจร
    """
    
    @staticmethod
    def print_detailed_report(optimizer: LayoutOptimizer):
        """พิมพ์รายงานแบบละเอียด"""
        
        print("=" * 160)
        print("🗺️ ELECTRICAL LAYOUT OPTIMIZATION REPORT")
        print("=" * 160)
        
        summary = optimizer.get_summary_report()
        
        print(f"\n📊 SUMMARY")
        print(f"   Total Circuits:          {summary['total_circuits']}")
        print(f"   ✅ Compliant:            {summary['compliant_circuits']}")
        print(f"   ❌ Non-Compliant:        {summary['non_compliant_circuits']}")
        print(f"   Compliance Rate:         {summary['compliance_rate_percent']}%")
        print(f"   Total Wire Length:       {summary['total_wire_length_m']:.2f} m")
        print(f"   Total Cost:              {summary['total_cost_thb']:,.2f} THB")
        print(f"   Avg Cost/Circuit:        {summary['avg_cost_per_circuit_thb']:,.2f} THB")
        
        print(f"\n📍 CIRCUIT DETAILS")
        print(f"{'ID':<6} {'Circuit Name':<25} {'Room':<18} {'Route':<12} {'Length(m)':<11} {'VD%':<8} {'Cost(THB)':<12} {'Status':<10}")
        print("-" * 160)
        
        for design in optimizer.circuit_designs:
            status_icon = "✅" if design.is_compliant else "❌"
            
            print(f"{design.circuit_id:<6} {design.circuit_name:<25} {design.room_name:<18} "
                  f"{design.route_type.value:<12} {design.actual_length_m:<11.2f} "
                  f"{design.voltage_drop_percent:<8.2f} {design.total_cost:<12,.0f} {status_icon:<10}")
            
            if not design.is_compliant:
                for issue in design.compliance_issues:
                    print(f"       └─ {issue}")
        
        print("=" * 160)
        
        # Recommendations
        non_compliant = [d for d in optimizer.circuit_designs if not d.is_compliant]
        
        if non_compliant:
            print(f"\n⚠️ RECOMMENDATIONS")
            for design in non_compliant:
                print(f"\n   Circuit: {design.circuit_name}")
                for issue in design.compliance_issues:
                    print(f"      {issue}")
                
                if design.voltage_drop_percent > 3.0:
                    # แนะนำขนาดสายที่ใหญ่ขึ้น
                    current_size = design.wire_size_mm2
                    next_sizes = [s for s in [2.5, 4, 6, 10, 16, 25, 35] if s > current_size]
                    if next_sizes:
                        print(f"      💡 แนะนำ: เพิ่มขนาดสายเป็น {next_sizes[0]} mm²")


# ======================== ตัวอย่างการใช้งาน ========================

if __name__ == "__main__":
    
    print("\n🗺️ ตัวอย่างการวางผังระบบไฟฟ้า\n")
    
    # 1. Floor Plan
    floor_plan = {
        "rooms": [
            {
                "id": "R01",
                "name": "ห้องนั่งเล่น",
                "type": "living_room",
                "area_sqm": 30,
                "position": {"x": 0, "y": 0},
                "dimension": {"width": 6, "length": 5},
                "outlets": [
                    {"id": "O01", "type": "receptacle", "position": {"x": 3, "y": 2.5}},
                    {"id": "O02", "type": "air_conditioner", "position": {"x": 5, "y": 4}}
                ]
            },
            {
                "id": "R02",
                "name": "ห้องครัว",
                "type": "kitchen",
                "area_sqm": 12,
                "position": {"x": 6, "y": 0},
                "dimension": {"width": 4, "length": 3},
                "outlets": [
                    {"id": "O03", "type": "receptacle", "position": {"x": 1, "y": 1.5}},
                    {"id": "O04", "type": "receptacle", "position": {"x": 3, "y": 1.5}}
                ],
                "special_requirements": {
                    "min_circuits": 2,
                    "rcbo_required": True
                }
            },
            {
                "id": "R03",
                "name": "ห้องน้ำ",
                "type": "bathroom",
                "area_sqm": 4,
                "position": {"x": 6, "y": 3},
                "dimension": {"width": 2, "length": 2},
                "outlets": [
                    {"id": "O05", "type": "heater", "position": {"x": 1, "y": 1}, "zone": 1}
                ],
                "special_requirements": {
                    "rcbo_required": True,
                    "ip_rating_min": "IP44",
                    "forbidden_zones": [0, 1, 2]
                }
            }
        ],
        "distribution_board": {
            "id": "DB01",
            "position": {"x": 0, "y": 5},
            "type": "main"
        }
    }
    
    # 2. Wire Database (จาก Module 2)
    wire_database = {
        2.5: {
            "resistance_75c_ohm_per_km": 8.90,
            "ampacity_in_conduit_30c": 27
        },
        4: {
            "resistance_75c_ohm_per_km": 5.53,
            "ampacity_in_conduit_30c": 37
        }
    }
    
    # 3. Material Prices (จาก Module 5)
    material_prices = {
        "wire_thw": {2.5: 18, 4: 28},
        "conduit_pvc": {"1/2": 40, "3/4": 60}
    }
    
    # 4. Labor Rates
    labor_rates = {"wire_conduit_per_m": 55}
    
    # 5. Compliance Rules (จาก Module 6)
    compliance_rules = {
        "max_vd_percent": 3.0
    }
    
    # 6. สร้าง Optimizer
    optimizer = LayoutOptimizer(
        floor_plan,
        wire_database,
        material_prices,
        labor_rates,
        compliance_rules
    )
    
    # 7. ข้อมูลวงจรจาก Module 1-6
    circuits_data = [
        {
            "circuit_id": "C01",
            "circuit_name": "ปลั๊ก ห้องนั่งเล่น",
            "room_id": "R01",
            "outlet_id": "O01",
            "load_current_a": 8.2,
            "wire_size_mm2": 2.5,
            "wire_ampacity_a": 27,
            "conduit_size_inch": "1/2",
            "breaker_rating_a": 16,
            "max_distance_m": 35,
            "wire_price_per_m": 18,
            "conduit_price_per_4m": 40,
            "labor_rate_per_m": 55,
            "has_rcbo": False
        },
        {
            "circuit_id": "C02",
            "circuit_name": "แอร์ ห้องนั่งเล่น",
            "room_id": "R01",
            "outlet_id": "O02",
            "load_current_a": 13.4,
            "wire_size_mm2": 2.5,
            "wire_ampacity_a": 27,
            "conduit_size_inch": "1/2",
            "breaker_rating_a": 20,
            "max_distance_m": 28,
            "wire_price_per_m": 18,
            "conduit_price_per_4m": 40,
            "labor_rate_per_m": 55,
            "has_rcbo": False
        },
        {
            "circuit_id": "C03",
            "circuit_name": "ปลั๊ก ครัว 1",
            "room_id": "R02",
            "outlet_id": "O03",
            "load_current_a": 12.0,
            "wire_size_mm2": 2.5,
            "wire_ampacity_a": 27,
            "conduit_size_inch": "1/2",
            "breaker_rating_a": 16,
            "max_distance_m": 30,
            "wire_price_per_m": 18,
            "conduit_price_per_4m": 40,
            "labor_rate_per_m": 55,
            "has_rcbo": True  # ครัวต้องมี RCBO
        },
        {
            "circuit_id": "C04",
            "circuit_name": "เครื่องทำน้ำอุ่น ห้องน้ำ",
            "room_id": "R03",
            "outlet_id": "O05",
            "load_current_a": 15.9,
            "wire_size_mm2": 2.5,
            "wire_ampacity_a": 27,
            "conduit_size_inch": "1/2",
            "breaker_rating_a": 20,
            "max_distance_m": 25,
            "wire_price_per_m": 18,
            "conduit_price_per_4m": 40,
            "labor_rate_per_m": 55,
            "has_rcbo": True,  # ห้องน้ำต้องมี RCBO
            "ip_rating": "IP25",
            "zone": 1
        }
    ]
    
    # 8. ออกแบบวงจรทั้งหมด
    designs = optimizer.optimize_all_circuits(circuits_data)
    
    # 9. พิมพ์รายงาน
    LayoutReportGenerator.print_detailed_report(optimizer)

---

## 📊 ส่วนที่ 3: การทำงานร่วมกับ Module อื่น ๆ

## **3.1 Integration Flow**

python

# ตัวอย่างการใช้งานจริง (Integrated)

from load_calculator import LoadCalculator
from wire_sizer import WireSizer
from breaker_selector import select_breaker
from conduit_sizer import select_conduit_size
from cost_estimator import CostEstimator
from compliance_checker import ComplianceChecker
from layout_optimizer import LayoutOptimizer

# Step 1: Load Calculation
load_calc = LoadCalculator()
load_calc.add_appliance(Appliance("แอร์ ห้องนอน", LoadType.AIR_CONDITIONER, 2500, 1, 220, 0.85))
load_result = load_calc.calculate_standard_method(floor_area_sqm=100)

# Step 2: Wire Sizing
wire_sizer = WireSizer()
wire_result = wire_sizer.select_wire_size(
    load_current_a=13.4,
    length_m=25,  # ประมาณการเบื้องต้น
    voltage_v=220,
    power_factor=0.85
)

# Step 3: Breaker Selection
breaker_result = select_breaker(
    load_current_a=13.4,
    wire_ampacity_a=wire_result.derated_ampacity_a,
    brand="Schneider"
)

# Step 4: Conduit Sizing
conduit_result = select_conduit_size(
    wires=[{"size_mm2": 2.5, "quantity": 2}]
)

# Step 5: Cost Estimation
cost_est = CostEstimator("บ้าน 1 ชั้น")
cost_est.add_wire(2.5, 25)
cost_est.add_conduit("1/2", 25)
cost_est.add_breaker("schneider", 20, "1")
cost_result = cost_est.calculate()

# Step 6: Compliance Check
compliance = ComplianceChecker("บ้าน 1 ชั้น")
compliance.check_voltage_drop("แอร์ ห้องนอน", wire_result.vd_percent, "branch")
compliance.check_wire_ampacity("แอร์ ห้องนอน", wire_result.derated_ampacity_a, 13.4, True)
compliance_report = compliance.generate_report()

# Step 7: Layout Optimization
circuits_data = [{
    "circuit_id": "C01",
    "circuit_name": "แอร์ ห้องนอน",
    "room_id": "R01",
    "outlet_id": "O01",
    "load_current_a": 13.4,
    "wire_size_mm2": wire_result.selected_size_mm2,
    "wire_ampacity_a": wire_result.derated_ampacity_a,
    "conduit_size_inch": conduit_result["conduit_size"],
    "breaker_rating_a": breaker_result["rating_a"],
    "max_distance_m": wire_sizer.calculate_maximum_distance(wire_result.selected_size_mm2, 13.4),
    "wire_price_per_m": wire_result.wire_cost_per_m_thb,
    "conduit_price_per_4m": conduit_result["conduit_data"]["price_per_4m_thb"],
    "labor_rate_per_m": 55,
    "has_rcbo": False
}]

layout_opt = LayoutOptimizer(floor_plan, wire_database, material_prices, labor_rates, compliance_rules)
final_designs = layout_opt.optimize_all_circuits(circuits_data)

# Final Report
LayoutReportGenerator.print_detailed_report(layout_opt)


---

**นายท่าน Volta ได้อธิบาย Module 7: layout_optimizer.py อย่างละเอียดแล้วค่ะ!**

**Key Features:**  
✅ รับข้อมูลจาก Module 1-6 ครบถ้วน  
✅ วิเคราะห์ Floor Plan แบบ Room-Based  
✅ คำนวณเส้นทางแบบ Direct/Manhattan/Multi-Point  
✅ ตรวจสอบข้อกำหนดเฉพาะห้อง (ครัว/ห้องน้ำ)  
✅ คำนวณ VD, Compliance, Cost อัตโนมัติ  
✅ สร้างรายงานผังวงจรแบบละเอียด


