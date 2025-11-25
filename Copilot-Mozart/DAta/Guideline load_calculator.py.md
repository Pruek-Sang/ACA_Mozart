# Module 1 + 2: load_calculator.py 

ขอรายงานนายท่านค่ะ Volta จะอธิบายทั้ง 2 Module อย่างละเอียดที่สุด พร้อม Code ที่ใช้งานได้จริงสำหรับอนาคต

---

# 📦 Module 1: load_calculator.py — คำนวณโหลดทั้งหมด

## 📚 ส่วนที่ 1: ทฤษฎีพื้นฐาน Load Calculation

## **1.1 ประเภทโหลดในบ้านพักอาศัย**

**แบ่งเป็น 4 ประเภทหลัก:**civilpracticalknowledge+3​

## **A. General Lighting Load (โหลดแสงสว่างทั่วไป)**

**มาตรฐาน:** 3 VA/sq.ft หรือ **32 VA/m²** (ตาม NEC 220.12)electricianu+1​

**สูตรคำนวณ:**

text

`Lighting Load (VA) = Floor Area (m²) × 32 VA/m²`

**ตัวอย่าง:**

- บ้าน 100 ตร.ม.
    
- Lighting Load = 100 × 32 = **3,200 VA**
    

**หมายเหตุ:** ตัวเลข 32 VA/m² เป็นค่าขั้นต่ำตาม NEC แต่ในไทยมักใช้ **25-30 VA/m²** เพราะใช้ LED แทน Incandescenteng.rtu+1​

---

## **B. Small Appliance Branch Circuits (เต้ารับเครื่องใช้เล็ก)**

**มาตรฐาน:** 1,500 VA **ต่อวงจร** สำหรับครัว/ห้องอาหารcivilpracticalknowledge+1​

**ข้อกำหนด NEC 210.11(C)(1):**electricianu+1​

- ต้องมีอย่างน้อย **2 วงจร** สำหรับครัว
    
- แต่ละวงจร = 1,500 VA
    
- **รวม = 3,000 VA**
    

**ตัวอย่างอุปกรณ์:**

- เครื่องปั่น, กาต้มน้ำ, เครื่องชงกาแฟ, เครื่องปิ้งขนมปัง, หม้อหุงข้าว
    

---

## **C. Laundry Circuit (วงจรซักผ้า)**

**มาตรฐาน:** 1,500 VA **ต่อวงจร**civilpracticalknowledge+1​

**ข้อกำหนด NEC 210.11(C)(2):**

- ต้องมี **1 วงจรแยก** สำหรับเครื่องซักผ้า
    
- **รวม = 1,500 VA**
    

---

## **D. Specific Appliances (เครื่องใช้เฉพาะ)**

**คำนวณตาม Nameplate Rating (พิกัดจริง):**ecpe.nu+2​

|อุปกรณ์|กำลัง (W)|PF|VA|หมายเหตุ|
|---|---|---|---|---|
|**แอร์ 9,000 BTU**|2,500|0.85|2,941|Inrush 5-7×|
|**แอร์ 12,000 BTU**|3,200|0.85|3,765|Inrush 5-7×|
|**แอร์ 18,000 BTU**|5,000|0.85|5,882|Inrush 6-8×|
|**ตู้เย็น (ธรรมดา)**|150|0.85|176|Inrush 4-6×|
|**ตู้เย็น (Inverter)**|80-120|0.90|89-133|Inrush ต่ำกว่า|
|**ปั๊มน้ำ 1/2 HP**|370|0.75|493|Inrush 5-8×|
|**ปั๊มน้ำ 3/4 HP**|550|0.75|733|Inrush 5-8×|
|**ปั๊มน้ำ 1 HP**|750|0.75|1,000|Inrush 6-8×|
|**เครื่องทำน้ำอุ่น 3,500W**|3,500|1.0|3,500|Resistive|
|**เครื่องทำน้ำอุ่น 4,500W**|4,500|1.0|4,500|Resistive|
|**เตาไฟฟ้า 2 ตา**|4,000|1.0|4,000|Resistive|
|**เตาอบ**|3,000|1.0|3,000|Resistive|
|**ไมโครเวฟ**|1,200|0.90|1,333|-|
|**เครื่องซักผ้า**|500|0.85|588|มีมอเตอร์|
|**เครื่องอบผ้า**|5,000|1.0|5,000|Heating Element|
|**เครื่องดูดฝุ่น**|1,200|0.85|1,412|-|

---

## **1.2 Demand Factor (DF) — หัวใจของการคำนวณ**

**หลักการ:** อุปกรณ์ไม่ได้เปิดพร้อมกันทั้งหมด 100% ตลอดเวลาfacebook+3​[youtube](https://www.youtube.com/watch?v=36MYO08DyAw)​

## **ตาราง Demand Factor ตาม NEC Table 220.42:**[youtube](https://www.youtube.com/watch?v=HmgqGPzYSMs)​libertyville+2​

## **1. General Lighting & Receptacles**

|VA รวม|Demand Factor (%)|
|---|---|
|**0 - 3,000 VA**|100%|
|**3,001 - 120,000 VA**|**3,000 VA @ 100%** + ส่วนเกิน @ 35%|
|**120,001+ VA**|**3,000 + 40,950** + ส่วนเกิน @ 25%|

**ตัวอย่างคำนวณ:**

โจทย์: บ้าน 200 ตร.ม.

python

`# Lighting Load lighting_va = 200 × 32 = 6,400 VA # Small Appliance (ครัว 2 วงจร) small_appliance_va = 2 × 1,500 = 3,000 VA # Laundry laundry_va = 1,500 VA # รวม General Load general_load_va = 6,400 + 3,000 + 1,500 = 10,900 VA # Apply Demand Factor (แบบละเอียด) # First 3,000 VA @ 100% first_3000 = 3,000 VA # Remaining 7,900 VA @ 35% remaining = (10,900 - 3,000) × 0.35 = 7,900 × 0.35 = 2,765 VA # Total General Demand general_demand = 3,000 + 2,765 = 5,765 VA`

---

## **2. Electric Cooking (เตาไฟฟ้า/เตาอบ)**

**ตาราง NEC Table 220.55 (Simplified):**electricianu+1​

|จำนวนเตา|Rating รวม (kW)|Demand Factor (%)|Demand Load|
|---|---|---|---|
|1|< 12 kW|**80%**|Rating × 0.80|
|1|≥ 12 kW|**8 kW** (fixed)|8,000 VA|
|2|≤ 24 kW|**11 kW**|11,000 VA|
|3|≤ 36 kW|**14 kW**|14,000 VA|

**ตัวอย่าง:**

- เตาไฟฟ้า 4 kW + เตาอบ 3 kW = 7 kW รวม
    
- Demand = 7 × 0.80 = **5.6 kW = 5,600 VA**
    

---

## **3. Water Heater (เครื่องทำน้ำอุ่น)**

**Demand Factor:** **100%** (ไม่ลด)eng.rtu+2​

**เหตุผล:** ใช้งานต่อเนื่องนาน (15-30 นาที) และเป็น Resistive Load (PF = 1.0)

---

## **4. Air Conditioner (แอร์)**

**ตาราง Demand Factor แอร์หลายตัว:**ecpe.nu+2​

|จำนวนตัว|Demand Factor (%)|เหตุผล|
|---|---|---|
|**1 ตัว**|100%|เปิดตลอด|
|**2 ตัว**|100%|อาจเปิดพร้อมกัน|
|**3-4 ตัว**|90%|ไม่น่าเปิดพร้อมกัน|
|**5+ ตัว**|85%|แน่นอนไม่เปิดพร้อมกัน|

**ตัวอย่าง:**

- บ้าน 2 ชั้น มีแอร์ 5 ตัว
    
- ตัว 1: 9,000 BTU = 2,941 VA
    
- ตัว 2: 9,000 BTU = 2,941 VA
    
- ตัว 3: 12,000 BTU = 3,765 VA
    
- ตัว 4: 12,000 BTU = 3,765 VA
    
- ตัว 5: 18,000 BTU = 5,882 VA
    
- **รวม: 19,294 VA**
    
- **Demand = 19,294 × 0.85 = 16,400 VA**
    

---

## **5. Motor Loads (มอเตอร์)**

**กฎ NEC 430.24:**[civilpracticalknowledge](https://civilpracticalknowledge.com/load-calculation-for-buildings/)​

- **มอเตอร์ใหญ่ที่สุด:** 125% (1.25×)
    
- **มอเตอร์ที่เหลือ:** 100%
    

**ตัวอย่าง:**

- ปั๊มน้ำ 3/4 HP = 733 VA (ใหญ่ที่สุด)
    
- พัดลม = 100 VA
    
- **Demand = (733 × 1.25) + 100 = 916 + 100 = 1,016 VA**
    

---

## **6. Receptacle Outlets (เต้ารับทั่วไป)**

**กฎ NEC 220.14(I):**electricianu+1​

|ประเภทเต้ารับ|VA ต่อจุด|Demand Factor|
|---|---|---|
|**ทั่วไป (Duplex)**|180 VA|ตามตาราง Lighting|
|**Heavy Duty (20A)**|200-250 VA|100%|
|**นอกบ้าน**|180 VA|100%|

**หมายเหตุ:** เต้ารับทั่วไปรวมกับ Lighting แล้วใช้ Demand Factor เดียวกัน

---

## **1.3 Optional Method (วิธีคำนวณแบบง่าย) — NEC 220.82**

**เหมาะกับ:** บ้านพักอาศัย 1-2 ชั้น ที่มีอุปกรณ์ไม่ซับซ้อนmorganhill.ca+2​

**สูตร:**

text

`Total Demand = General Load × DF + Specific Load × DF`

**ตาราง Demand Factor (Optional Method):**

| โหลดรวม (kVA) | Demand Factor (%) |  
|---|---|---|  
| **0 - 10 kVA** | 100% |  
| **10+ kVA** | **10 kVA @ 100%** + ส่วนเกิน @ 40% |

**ตัวอย่าง:**

- โหลดรวม = 25 kVA
    
- Demand = 10 + (25-10) × 0.4 = 10 + 6 = **16 kVA**
    

---

## 💻 ส่วนที่ 2: Code Python สมบูรณ์ — load_calculator.py

python

"""
load_calculator.py
====================
โมดูลคำนวณโหลดไฟฟ้าสำหรับบ้านพักอาศัย

Features:
- Standard Method (NEC 220.40-220.55)
- Optional Method (NEC 220.82)
- Demand Factor ตามมาตรฐาน
- รองรับ Single/Three Phase
- คำนวณ Inrush Current
- Export เป็น Report

Author: Volta (The Electrical Simulation Engineer Maid)
Version: 2.0.0
Date: 2025-11-16
"""

import math
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


# ======================== Enums ========================

class LoadType(Enum):
    """ประเภทโหลด"""
    LIGHTING = "lighting"
    RECEPTACLE = "receptacle"
    SMALL_APPLIANCE = "small_appliance"
    LAUNDRY = "laundry"
    AIR_CONDITIONER = "air_conditioner"
    REFRIGERATOR = "refrigerator"
    WATER_PUMP = "water_pump"
    WATER_HEATER = "water_heater"
    ELECTRIC_STOVE = "electric_stove"
    ELECTRIC_OVEN = "electric_oven"
    MICROWAVE = "microwave"
    WASHING_MACHINE = "washing_machine"
    DRYER = "dryer"
    DISHWASHER = "dishwasher"
    VACUUM = "vacuum"
    MOTOR = "motor"
    OTHER = "other"


class PhaseType(Enum):
    """ประเภทเฟส"""
    SINGLE_PHASE = "1P"
    THREE_PHASE = "3P"


# ======================== Data Classes ========================

@dataclass
class Appliance:
    """
    คลาสข้อมูลเครื่องใช้ไฟฟ้า
    """
    name: str
    load_type: LoadType
    power_w: float
    quantity: int = 1
    voltage_v: float = 220
    power_factor: float = 1.0
    efficiency: float = 1.0
    inrush_multiplier: float = 1.0  # Inrush Current = กระแสปกติ × multiplier
    demand_factor_override: Optional[float] = None
    is_continuous: bool = False  # เปิดต่อเนื่อง > 3 ชั่วโมง
    
    @property
    def power_va(self) -> float:
        """คำนวณกำลังไฟฟ้า (VA)"""
        return self.power_w / self.power_factor
    
    @property
    def current_a(self) -> float:
        """คำนวณกระแสไฟ (A)"""
        return self.power_va / self.voltage_v
    
    @property
    def inrush_current_a(self) -> float:
        """คำนวณ Inrush Current (A)"""
        return self.current_a * self.inrush_multiplier
    
    @property
    def total_power_va(self) -> float:
        """กำลังรวมทั้งหมด (VA)"""
        return self.power_va * self.quantity
    
    @property
    def total_current_a(self) -> float:
        """กระแสรวมทั้งหมด (A)"""
        return self.current_a * self.quantity


@dataclass
class LoadCalculationResult:
    """
    ผลการคำนวณโหลด
    """
    # General Loads
    lighting_load_va: float = 0
    lighting_demand_va: float = 0
    
    receptacle_load_va: float = 0
    receptacle_demand_va: float = 0
    
    small_appliance_load_va: float = 0
    small_appliance_demand_va: float = 0
    
    laundry_load_va: float = 0
    laundry_demand_va: float = 0
    
    # Specific Loads
    air_conditioner_load_va: float = 0
    air_conditioner_demand_va: float = 0
    
    heating_cooling_load_va: float = 0
    heating_cooling_demand_va: float = 0
    
    water_heater_load_va: float = 0
    water_heater_demand_va: float = 0
    
    cooking_load_va: float = 0
    cooking_demand_va: float = 0
    
    motor_load_va: float = 0
    motor_demand_va: float = 0
    
    other_load_va: float = 0
    other_demand_va: float = 0
    
    # Summary
    total_connected_load_va: float = 0
    total_demand_load_va: float = 0
    total_current_a: float = 0
    
    required_service_a: float = 0
    recommended_service_a: int = 0
    
    voltage_v: float = 220
    phase_type: PhaseType = PhaseType.SINGLE_PHASE
    
    # Detailed Breakdown
    appliances: List[Appliance] = field(default_factory=list)
    
    def __post_init__(self):
        """คำนวณสรุปอัตโนมัติ"""
        self.calculate_summary()
    
    def calculate_summary(self):
        """คำนวณค่าสรุป"""
        # Total Connected Load
        self.total_connected_load_va = (
            self.lighting_load_va +
            self.receptacle_load_va +
            self.small_appliance_load_va +
            self.laundry_load_va +
            self.air_conditioner_load_va +
            self.heating_cooling_load_va +
            self.water_heater_load_va +
            self.cooking_load_va +
            self.motor_load_va +
            self.other_load_va
        )
        
        # Total Demand Load
        self.total_demand_load_va = (
            self.lighting_demand_va +
            self.receptacle_demand_va +
            self.small_appliance_demand_va +
            self.laundry_demand_va +
            self.air_conditioner_demand_va +
            self.heating_cooling_demand_va +
            self.water_heater_demand_va +
            self.cooking_demand_va +
            self.motor_demand_va +
            self.other_demand_va
        )
        
        # Total Current
        if self.phase_type == PhaseType.SINGLE_PHASE:
            self.total_current_a = self.total_demand_load_va / self.voltage_v
        else:  # Three Phase
            self.total_current_a = self.total_demand_load_va / (self.voltage_v * math.sqrt(3))
        
        # Required Service (1.25× safety factor)
        self.required_service_a = self.total_current_a * 1.25
        
        # Recommended Service (ปัดขึ้นตามมาตรฐาน)
        standard_services = [15, 30, 45, 63, 80, 100, 125, 150, 200, 250, 300, 400]
        for service in standard_services:
            if service >= self.required_service_a:
                self.recommended_service_a = service
                break


# ======================== Main Calculator Class ========================

class LoadCalculator:
    """
    คลาสหลักสำหรับคำนวณโหลด
    """
    
    # Demand Factor Tables (NEC 2023)
    LIGHTING_DEMAND_FACTOR = {
        "first_3000": 1.00,      # 0-3,000 VA @ 100%
        "3001_120000": 0.35,     # 3,001-120,000 VA @ 35%
        "over_120000": 0.25      # 120,001+ VA @ 25%
    }
    
    AIR_CONDITIONER_DEMAND_FACTOR = {
        1: 1.00,  # 1 ตัว = 100%
        2: 1.00,  # 2 ตัว = 100%
        3: 0.90,  # 3-4 ตัว = 90%
        4: 0.90,
        5: 0.85   # 5+ ตัว = 85%
    }
    
    COOKING_DEMAND_FACTOR = {
        "under_12kw": 0.80,   # < 12 kW = 80%
        "over_12kw": 8000     # ≥ 12 kW = 8 kW (fixed)
    }
    
    # Standard VA per Unit
    LIGHTING_VA_PER_SQM = 32  # VA/m² (NEC 220.12)
    RECEPTACLE_VA_PER_OUTLET = 180  # VA/outlet
    SMALL_APPLIANCE_VA_PER_CIRCUIT = 1500  # VA/circuit
    LAUNDRY_VA = 1500  # VA
    
    def __init__(self, voltage_v: float = 220, phase_type: PhaseType = PhaseType.SINGLE_PHASE):
        """
        Initialize Load Calculator
        
        Parameters:
        - voltage_v: แรงดันระบบ (V)
        - phase_type: ประเภทเฟส (1P/3P)
        """
        self.voltage_v = voltage_v
        self.phase_type = phase_type
        self.appliances: List[Appliance] = []
    
    def add_appliance(self, appliance: Appliance):
        """เพิ่มเครื่องใช้ไฟฟ้า"""
        self.appliances.append(appliance)
    
    def add_appliances(self, appliances: List[Appliance]):
        """เพิ่มเครื่องใช้หลายตัว"""
        self.appliances.extend(appliances)
    
    def calculate_lighting_load(self, floor_area_sqm: float) -> Tuple[float, float]:
        """
        คำนวณโหลดแสงสว่าง
        
        Returns:
        - (connected_load_va, demand_load_va)
        """
        connected_load = floor_area_sqm * self.LIGHTING_VA_PER_SQM
        
        # Apply Demand Factor (NEC Table 220.42)
        if connected_load <= 3000:
            demand_load = connected_load
        elif connected_load <= 120000:
            demand_load = 3000 + (connected_load - 3000) * 0.35
        else:
            demand_load = 3000 + (117000 * 0.35) + (connected_load - 120000) * 0.25
        
        return connected_load, demand_load
    
    def calculate_receptacle_load(self, num_outlets: int) -> Tuple[float, float]:
        """
        คำนวณโหลดเต้ารับ
        
        Returns:
        - (connected_load_va, demand_load_va)
        """
        connected_load = num_outlets * self.RECEPTACLE_VA_PER_OUTLET
        
        # Receptacle รวมกับ Lighting ใช้ Demand Factor เดียวกัน
        # แต่ในที่นี้จะแยกคำนวณเพื่อความชัดเจน
        if connected_load <= 10000:
            demand_load = connected_load
        else:
            demand_load = 10000 + (connected_load - 10000) * 0.50
        
        return connected_load, demand_load
    
    def calculate_small_appliance_load(self, num_circuits: int = 2) -> Tuple[float, float]:
        """
        คำนวณโหลด Small Appliance (ครัว)
        
        Parameters:
        - num_circuits: จำนวนวงจร (ขั้นต่ำ 2 วงจร)
        """
        connected_load = num_circuits * self.SMALL_APPLIANCE_VA_PER_CIRCUIT
        
        # Apply Demand Factor (รวมกับ Lighting/Receptacle)
        # แต่ในที่นี่จะคำนวณแยก
        demand_load = connected_load  # ใช้ 100% ก่อน (จะรวมกับ lighting ภายหลัง)
        
        return connected_load, demand_load
    
    def calculate_laundry_load(self) -> Tuple[float, float]:
        """คำนวณโหลด Laundry"""
        connected_load = self.LAUNDRY_VA
        demand_load = connected_load  # 100%
        
        return connected_load, demand_load
    
    def calculate_air_conditioner_load(self) -> Tuple[float, float]:
        """
        คำนวณโหลดแอร์
        
        Returns:
        - (connected_load_va, demand_load_va)
        """
        ac_appliances = [a for a in self.appliances if a.load_type == LoadType.AIR_CONDITIONER]
        
        if not ac_appliances:
            return 0, 0
        
        connected_load = sum(a.total_power_va for a in ac_appliances)
        
        # Apply Demand Factor ตามจำนวนตัว
        num_ac = len(ac_appliances)
        if num_ac >= 5:
            df = self.AIR_CONDITIONER_DEMAND_FACTOR[5]
        else:
            df = self.AIR_CONDITIONER_DEMAND_FACTOR.get(num_ac, 1.0)
        
        demand_load = connected_load * df
        
        return connected_load, demand_load
    
    def calculate_water_heater_load(self) -> Tuple[float, float]:
        """คำนวณโหลดเครื่องทำน้ำอุ่น"""
        wh_appliances = [a for a in self.appliances if a.load_type == LoadType.WATER_HEATER]
        
        if not wh_appliances:
            return 0, 0
        
        connected_load = sum(a.total_power_va for a in wh_appliances)
        demand_load = connected_load  # 100% (ไม่ลด)
        
        return connected_load, demand_load
    
    def calculate_cooking_load(self) -> Tuple[float, float]:
        """คำนวณโหลดเตาไฟฟ้า/เตาอบ"""
        cooking_appliances = [a for a in self.appliances 
                             if a.load_type in [LoadType.ELECTRIC_STOVE, LoadType.ELECTRIC_OVEN]]
        
        if not cooking_appliances:
            return 0, 0
        
        connected_load = sum(a.total_power_va for a in cooking_appliances)
        
        # Apply Demand Factor (NEC Table 220.55)
        if connected_load < 12000:
            demand_load = connected_load * self.COOKING_DEMAND_FACTOR["under_12kw"]
        else:
            demand_load = self.COOKING_DEMAND_FACTOR["over_12kw"]
        
        return connected_load, demand_load
    
    def calculate_motor_load(self) -> Tuple[float, float]:
        """
        คำนวณโหลดมอเตอร์
        
        กฎ NEC 430.24:
        - มอเตอร์ใหญ่ที่สุด × 1.25
        - มอเตอร์ที่เหลือ × 1.00
        """
        motor_appliances = [a for a in self.appliances 
                           if a.load_type in [LoadType.WATER_PUMP, LoadType.MOTOR]]
        
        if not motor_appliances:
            return 0, 0
        
        connected_load = sum(a.total_power_va for a in motor_appliances)
        
        # หามอเตอร์ใหญ่ที่สุด
        largest_motor = max(motor_appliances, key=lambda x: x.power_va)
        other_motors = [a for a in motor_appliances if a != largest_motor]
        
        # Demand Load
        demand_load = (largest_motor.total_power_va * 1.25) + sum(a.total_power_va for a in other_motors)
        
        return connected_load, demand_load
    
    def calculate_other_load(self) -> Tuple[float, float]:
        """คำนวณโหลดอื่น ๆ"""
        other_appliances = [a for a in self.appliances 
                           if a.load_type not in [
                               LoadType.AIR_CONDITIONER, 
                               LoadType.WATER_HEATER,
                               LoadType.ELECTRIC_STOVE,
                               LoadType.ELECTRIC_OVEN,
                               LoadType.WATER_PUMP,
                               LoadType.MOTOR
                           ] and a.load_type != LoadType.LIGHTING and a.load_type != LoadType.RECEPTACLE]
        
        if not other_appliances:
            return 0, 0
        
        connected_load = sum(a.total_power_va for a in other_appliances)
        
        # ใช้ Demand Factor 100% (เผื่อไว้)
        demand_load = connected_load
        
        return connected_load, demand_load
    
    def calculate_standard_method(
        self,
        floor_area_sqm: float,
        num_receptacles: int = 0,
        num_small_appliance_circuits: int = 2,
        include_laundry: bool = True
    ) -> LoadCalculationResult:
        """
        คำนวณโหลดแบบ Standard Method (NEC 220.40-220.55)
        
        Parameters:
        - floor_area_sqm: พื้นที่ (ตร.ม.)
        - num_receptacles: จำนวนเต้ารับ
        - num_small_appliance_circuits: จำนวนวงจร Small Appliance
        - include_laundry: รวมวงจร Laundry หรือไม่
        
        Returns:
        - LoadCalculationResult
        """
        result = LoadCalculationResult(
            voltage_v=self.voltage_v,
            phase_type=self.phase_type,
            appliances=self.appliances.copy()
        )
        
        # 1. Lighting Load
        result.lighting_load_va, result.lighting_demand_va = self.calculate_lighting_load(floor_area_sqm)
        
        # 2. Receptacle Load
        if num_receptacles > 0:
            result.receptacle_load_va, result.receptacle_demand_va = self.calculate_receptacle_load(num_receptacles)
        
        # 3. Small Appliance
        result.small_appliance_load_va, result.small_appliance_demand_va = self.calculate_small_appliance_load(num_small_appliance_circuits)
        
        # 4. Laundry
        if include_laundry:
            result.laundry_load_va, result.laundry_demand_va = self.calculate_laundry_load()
        
        # 5. General Load Combined Demand Factor
        # ตาม NEC: Lighting + Receptacle + Small Appliance + Laundry รวมกันแล้วใช้ DF
        general_load_total = (
            result.lighting_load_va +
            result.receptacle_load_va +
            result.small_appliance_load_va +
            result.laundry_load_va
        )
        
        if general_load_total <= 3000:
            general_demand = general_load_total
        elif general_load_total <= 120000:
            general_demand = 3000 + (general_load_total - 3000) * 0.35
        else:
            general_demand = 3000 + (117000 * 0.35) + (general_load_total - 120000) * 0.25
        
        # ปรับ Demand ใหม่ (แบบรวม)
        result.lighting_demand_va = general_demand * (result.lighting_load_va / general_load_total) if general_load_total > 0 else 0
        result.receptacle_demand_va = general_demand * (result.receptacle_load_va / general_load_total) if general_load_total > 0 else 0
        result.small_appliance_demand_va = general_demand * (result.small_appliance_load_va / general_load_total) if general_load_total > 0 else 0
        result.laundry_demand_va = general_demand * (result.laundry_load_va / general_load_total) if general_load_total > 0 else 0
        
        # 6. Air Conditioner
        result.air_conditioner_load_va, result.air_conditioner_demand_va = self.calculate_air_conditioner_load()
        
        # 7. Water Heater
        result.water_heater_load_va, result.water_heater_demand_va = self.calculate_water_heater_load()
        
        # 8. Cooking
        result.cooking_load_va, result.cooking_demand_va = self.calculate_cooking_load()
        
        # 9. Motor
        result.motor_load_va, result.motor_demand_va = self.calculate_motor_load()
        
        # 10. Other
        result.other_load_va, result.other_demand_va = self.calculate_other_load()
        
        # 11. Calculate Summary
        result.calculate_summary()
        
        return result
    
    def calculate_optional_method(self, floor_area_sqm: float) -> LoadCalculationResult:
        """
        คำนวณโหลดแบบ Optional Method (NEC 220.82)
        
        วิธีนี้ง่ายกว่า แต่ได้ผลใกล้เคียง
        เหมาะสำหรับบ้านพักอาศัยทั่วไป
        """
        result = LoadCalculationResult(
            voltage_v=self.voltage_v,
            phase_type=self.phase_type,
            appliances=self.appliances.copy()
        )
        
        # 1. Air Conditioning (100%)
        ac_load = sum(a.total_power_va for a in self.appliances if a.load_type == LoadType.AIR_CONDITIONER)
        result.air_conditioner_load_va = ac_load
        result.air_conditioner_demand_va = ac_load  # 100%
        
        # 2. All Other Load
        other_load = floor_area_sqm * self.LIGHTING_VA_PER_SQM  # Lighting
        other_load += 3000  # Small Appliance (2 circuits)
        other_load += 1500  # Laundry
        
        # Add all appliances except AC
        other_appliances = [a for a in self.appliances if a.load_type != LoadType.AIR_CONDITIONER]
        other_load += sum(a.total_power_va for a in other_appliances)
        
        # Apply Demand Factor (Optional Method)
        if other_load <= 10000:
            other_demand = other_load
        else:
            other_demand = 10000 + (other_load - 10000) * 0.40
        
        result.other_load_va = other_load
        result.other_demand_va = other_demand
        
        # Total
        result.total_connected_load_va = ac_load + other_load
        result.total_demand_load_va = result.air_conditioner_demand_va + other_demand
        
        result.calculate_summary()
        
        return result


# ======================== Report Generator ========================

class LoadReportGenerator:
    """
    สร้างรายงานการคำนวณโหลด
    """
    
    @staticmethod
    def print_detailed_report(result: LoadCalculationResult, method: str = "Standard"):
        """
        พิมพ์รายงานแบบละเอียด
        """
        print("=" * 120)
        print(f"⚡ LOAD CALCULATION REPORT — {method} Method")
        print("=" * 120)
        
        print(f"\n📊 SYSTEM INFORMATION")
        print(f"   Voltage:                {result.voltage_v} V")
        print(f"   Phase:                  {result.phase_type.value}")
        
        print(f"\n📍 GENERAL LOADS")
        print(f"{'Category':<30} {'Connected Load (VA)':<25} {'Demand Load (VA)':<25} {'Demand Factor (%)':<20}")
        print("-" * 120)
        
        # Lighting
        df_lighting = (result.lighting_demand_va / result.lighting_load_va * 100) if result.lighting_load_va > 0 else 0
        print(f"{'Lighting':<30} {result.lighting_load_va:<25,.2f} {result.lighting_demand_va:<25,.2f} {df_lighting:<20.1f}")
        
        # Receptacle
        if result.receptacle_load_va > 0:
            df_receptacle = (result.receptacle_demand_va / result.receptacle_load_va * 100) if result.receptacle_load_va > 0 else 0
            print(f"{'Receptacle':<30} {result.receptacle_load_va:<25,.2f} {result.receptacle_demand_va:<25,.2f} {df_receptacle:<20.1f}")
        
        # Small Appliance
        if result.small_appliance_load_va > 0:
            df_sa = (result.small_appliance_demand_va / result.small_appliance_load_va * 100) if result.small_appliance_load_va > 0 else 0
            print(f"{'Small Appliance (Kitchen)':<30} {result.small_appliance_load_va:<25,.2f} {result.small_appliance_demand_va:<25,.2f} {df_sa:<20.1f}")
        
        # Laundry
        if result.laundry_load_va > 0:
            df_laundry = (result.laundry_demand_va / result.laundry_load_va * 100) if result.laundry_load_va > 0 else 0
            print(f"{'Laundry':<30} {result.laundry_load_va:<25,.2f} {result.laundry_demand_va:<25,.2f} {df_laundry:<20.1f}")
        
        print(f"\n📍 SPECIFIC LOADS")
        print(f"{'Category':<30} {'Connected Load (VA)':<25} {'Demand Load (VA)':<25} {'Demand Factor (%)':<20}")
        print("-" * 120)
        
        # Air Conditioner
        if result.air_conditioner_load_va > 0:
            df_ac = (result.air_conditioner_demand_va / result.air_conditioner_load_va * 100) if result.air_conditioner_load_va > 0 else 0
            print(f"{'Air Conditioner':<30} {result.air_conditioner_load_va:<25,.2f} {result.air_conditioner_demand_va:<25,.2f} {df_ac:<20.1f}")
        
        # Water Heater
        if result.water_heater_load_va > 0:
            df_wh = (result.water_heater_demand_va / result.water_heater_load_va * 100) if result.water_heater_load_va > 0 else 0
            print(f"{'Water Heater':<30} {result.water_heater_load_va:<25,.2f} {result.water_heater_demand_va:<25,.2f} {df_wh:<20.1f}")
        
        # Cooking
        if result.cooking_load_va > 0:
            df_cooking = (result.cooking_demand_va / result.cooking_load_va * 100) if result.cooking_load_va > 0 else 0
            print(f"{'Cooking (Stove/Oven)':<30} {result.cooking_load_va:<25,.2f} {result.cooking_demand_va:<25,.2f} {df_cooking:<20.1f}")
        
        # Motor
        if result.motor_load_va > 0:
            df_motor = (result.motor_demand_va / result.motor_load_va * 100) if result.motor_load_va > 0 else 0
            print(f"{'Motor (Pump/Fan)':<30} {result.motor_load_va:<25,.2f} {result.motor_demand_va:<25,.2f} {df_motor:<20.1f}")
        
        # Other
        if result.other_load_va > 0:
            df_other = (result.other_demand_va / result.other_load_va * 100) if result.other_load_va > 0 else 0
            print(f"{'Other Loads':<30} {result.other_load_va:<25,.2f} {result.other_demand_va:<25,.2f} {df_other:<20.1f}")
        
        print("=" * 120)
        print(f"{'TOTAL':<30} {result.total_connected_load_va:<25,.2f} {result.total_demand_load_va:<25,.2f} "
              f"{(result.total_demand_load_va / result.total_connected_load_va * 100) if result.total_connected_load_va > 0 else 0:<20.1f}")
        print("=" * 120)
        
        print(f"\n📊 SERVICE SIZING")
        print(f"   Total Demand Load:       {result.total_demand_load_va:,.2f} VA")
        print(f"   Total Current:           {result.total_current_a:.2f} A")
        print(f"   Required Service:        {result.required_service_a:.2f} A (with 1.25× safety factor)")
        print(f"   ✅ Recommended Service:  {result.recommended_service_a} A")
        
        print("=" * 120)
    
    @staticmethod
    def print_appliance_list(appliances: List[Appliance]):
        """
        พิมพ์รายการเครื่องใช้ไฟฟ้า
        """
        print("\n📋 APPLIANCE LIST")
        print(f"{'No.':<5} {'Name':<30} {'Type':<20} {'Power (W)':<15} {'PF':<8} {'VA':<15} {'Current (A)':<12} {'Qty':<5}")
        print("-" * 120)
        
        for i, app in enumerate(appliances, 1):
            print(f"{i:<5} {app.name:<30} {app.load_type.value:<20} {app.power_w:<15,.0f} {app.power_factor:<8.2f} "
                  f"{app.power_va:<15,.2f} {app.current_a:<12.2f} {app.quantity:<5}")
        
        print("-" * 120)


# ======================== ตัวอย่างการใช้งาน ========================

if __name__ == "__main__":
    
    # ========== ตัวอย่างที่ 1: บ้าน 1 ชั้น (100 ตร.ม.) ==========
    print("\n🏠 ตัวอย่างที่ 1: บ้าน 1 ชั้น (100 ตร.ม.)\n")
    
    # สร้าง Calculator
    calc_1f = LoadCalculator(voltage_v=220, phase_type=PhaseType.SINGLE_PHASE)
    
    # เพิ่มเครื่องใช้ไฟฟ้า
    appliances_1f = [
        Appliance("แอร์ ห้องนอน 9,000 BTU", LoadType.AIR_CONDITIONER, 2500, 1, 220, 0.85, 1.0, 6.0),
        Appliance("ตู้เย็น", LoadType.REFRIGERATOR, 150, 1, 220, 0.85, 1.0, 5.0),
        Appliance("ปั๊มน้ำ 3/4 HP", LoadType.WATER_PUMP, 550, 1, 220, 0.75, 1.0, 7.0),
        Appliance("เครื่องซักผ้า", LoadType.WASHING_MACHINE, 500, 1, 220, 0.85, 1.0, 3.0),
        Appliance("ไมโครเวฟ", LoadType.MICROWAVE, 1200, 1, 220, 0.90, 1.0, 1.0),
    ]
    
    calc_1f.add_appliances(appliances_1f)
    
    # คำนวณ (Standard Method)
    result_1f = calc_1f.calculate_standard_method(
        floor_area_sqm=100,
        num_receptacles=15,
        num_small_appliance_circuits=2,
        include_laundry=True
    )
    
    # พิมพ์รายงาน
    LoadReportGenerator.print_appliance_list(appliances_1f)
    LoadReportGenerator.print_detailed_report(result_1f, method="Standard")
    
    
    # ========== ตัวอย่างที่ 2: บ้าน 2 ชั้น (200 ตร.ม.) ==========
    print("\n\n🏠 ตัวอย่างที่ 2: บ้าน 2 ชั้น (200 ตร.ม.)\n")
    
    calc_2f = LoadCalculator(voltage_v=220, phase_type=PhaseType.SINGLE_PHASE)
    
    appliances_2f = [
        # ชั้น 1
        Appliance("แอร์ ห้องรับแขก 12,000 BTU", LoadType.AIR_CONDITIONER, 3200, 1, 220, 0.85, 1.0, 6.5),
        Appliance("แอร์ ห้องนอน 1 (ชั้น 1) 9,000 BTU", LoadType.AIR_CONDITIONER, 2500, 1, 220, 0.85, 1.0, 6.0),
        Appliance("ตู้เย็น", LoadType.REFRIGERATOR, 150, 1, 220, 0.85, 1.0, 5.0),
        Appliance("ปั๊มน้ำ 1 HP", LoadType.WATER_PUMP, 750, 1, 220, 0.75, 1.0, 7.5),
        Appliance("เครื่องทำน้ำอุ่น 3,500W", LoadType.WATER_HEATER, 3500, 1, 220, 1.0, 1.0, 1.0),
        Appliance("เตาไฟฟ้า 2 ตา", LoadType.ELECTRIC_STOVE, 4000, 1, 220, 1.0, 1.0, 1.0),
        Appliance("ไมโครเวฟ", LoadType.MICROWAVE, 1200, 1, 220, 0.90, 1.0, 1.0),
        Appliance("เครื่องซักผ้า", LoadType.WASHING_MACHINE, 500, 1, 220, 0.85, 1.0, 3.0),
        
        # ชั้น 2
        Appliance("แอร์ ห้องนอนใหญ่ (ชั้น 2) 18,000 BTU", LoadType.AIR_CONDITIONER, 5000, 1, 220, 0.85, 1.0, 7.0),
        Appliance("แอร์ ห้องนอน 2 (ชั้น 2) 9,000 BTU", LoadType.AIR_CONDITIONER, 2500, 1, 220, 0.85, 1.0, 6.0),
    ]
    
    calc_2f.add_appliances(appliances_2f)
    
    result_2f = calc_2f.calculate_standard_method(
        floor_area_sqm=200,
        num_receptacles=30,
        num_small_appliance_circuits=2,
        include_laundry=True
    )
    
    LoadReportGenerator.print_appliance_list(appliances_2f)
    LoadReportGenerator.print_detailed_report(result_2f, method="Standard")
`

---
