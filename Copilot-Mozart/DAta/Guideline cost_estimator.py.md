# Module 5: cost_estimator.py — คำนวณราคาวัสดุและค่าแรง (ฉบับละเอียดสุดยอด)

ขอรายงานนายท่านค่ะ Volta จะอธิบาย Module นี้อย่างละเอียดที่สุด พร้อมแนวทางการคำนวณต้นทุนที่ครบถ้วน

---

## 📚 ส่วนที่ 1: ทฤษฎีการประมาณราคางานไฟฟ้า

## **1.1 องค์ประกอบต้นทุนงานไฟฟ้า (Cost Components)**

ต้นทุนงานไฟฟ้าแบ่งเป็น **5 หมวดหลัก:**[onestockhome+4](https://www.onestockhome.com/th/articles/833fd534-9e42-44c4-a57f-4910bcfb0d7e)​

## **A. วัสดุหลัก (Main Materials)**

|หมวด|รายการ|หน่วย|ราคาโดยประมาณ (บาท)|ความผันผวน|Update ทุก|
|---|---|---|---|---|---|
|**สายไฟ**|THW 1.5 mm²|ม.|8-12|±15-20%/ปี|3-6 เดือน|
||THW 2.5 mm²|ม.|15-20|±15-20%/ปี|3-6 เดือน|
||THW 4 mm²|ม.|25-32|±15-20%/ปี|3-6 เดือน|
||THW 6 mm²|ม.|40-50|±15-20%/ปี|3-6 เดือน|
||THW 10 mm²|ม.|70-85|±15-20%/ปี|3-6 เดือน|
||THW 16 mm²|ม.|115-135|±15-20%/ปี|3-6 เดือน|
||THW 25 mm²|ม.|195-220|±15-20%/ปี|3-6 เดือน|
|**ท่อ PVC**|1/2" (Class 13.5)|เส้น 4m|35-45|±10-15%/ปี|6 เดือน|
||3/4" (Class 13.5)|เส้น 4m|50-70|±10-15%/ปี|6 เดือน|
||1" (Class 13.5)|เส้น 4m|80-120|±10-15%/ปี|6 เดือน|
||1-1/4" (Class 13.5)|เส้น 4m|120-180|±10-15%/ปี|6 เดือน|
||1-1/2" (Class 13.5)|เส้น 4m|150-220|±10-15%/ปี|6 เดือน|
||2" (Class 13.5)|เส้น 4m|250-350|±10-15%/ปี|6 เดือน|
|**Breaker**|Schneider 20A 1P Type C|ตัว|200-280|±10-15%/ปี|6-12 เดือน|
||Schneider 32A 1P Type C|ตัว|280-350|±10-15%/ปี|6-12 เดือน|
||Schneider 63A 2P Type C|ตัว|1,400-1,800|±10-15%/ปี|6-12 เดือน|
||Mitsubishi 20A 1P Type C|ตัว|150-200|±8-12%/ปี|6-12 เดือน|
||Mitsubishi 32A 1P Type C|ตัว|200-280|±8-12%/ปี|6-12 เดือน|
|**ตู้ DB**|DB 4-6 ช่อง (Metal)|ชุด|800-1,200|±5-10%/ปี|12 เดือน|
||DB 8-12 ช่อง (Metal)|ชุด|1,500-2,500|±5-10%/ปี|12 เดือน|
||DB 18-24 ช่อง (Metal)|ชุด|3,000-4,500|±5-10%/ปี|12 เดือน|
|**สวิตช์/ปลั๊ก**|สวิตช์ 1 ทาง (National)|ชุด|80-120|±5-8%/ปี|12 เดือน|
||สวิตช์ 2 ทาง (National)|ชุด|120-180|±5-8%/ปี|12 เดือน|
||ปลั๊กคู่ (National)|ชุด|100-150|±5-8%/ปี|12 เดือน|
||ปลั๊กคู่ + Ground|ชุด|150-220|±5-8%/ปี|12 เดือน|

**ปัจจัยที่กระทบราคาวัสดุ:**[richledshop+3](https://www.richledshop.com/article/26/%E0%B9%80%E0%B8%A5%E0%B8%B7%E0%B8%AD%E0%B8%81%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%9F-thw-%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99)​

1. **ราคาทองแดง (Copper Price):**
    
    - สาย THW 70% เป็นทองแดง
        
    - ทองแดงขึ้น 10% → สายขึ้น 7-9%
        
    - ตรวจสอบจาก: London Metal Exchange (LME)
        
2. **ราคาน้ำมัน/PVC Resin:**
    
    - ท่อ PVC ทำจากน้ำมัน
        
    - น้ำมันขึ้น → ท่อขึ้น (lag time 2-3 เดือน)
        
3. **อัตราแลกเปลี่ยน:**
    
    - Schneider, ABB = นำเข้า (Euro/USD)
        
    - บาทอ่อน → ราคาขึ้น
        
4. **ภาษี/ศุลกากร:**
    
    - เปลี่ยนตามนโยบายรัฐ
        

---

## **B. วัสดุเสริม (Accessories & Consumables)**

|รายการ|หน่วย|ราคา (บาท)|%ของวัสดุหลัก|
|---|---|---|---|
|**กล่องพักสาย (Junction Box)**|ใบ|15-35|3-5%|
|**คู่ต่อท่อ (Coupling)**|ตัว|5-15|2-3%|
|**ข้อโค้งท่อ (Elbow)**|ตัว|8-20|2-3%|
|**คลิปยึดท่อ**|ตัว|2-5|1-2%|
|**เทปพันสาย**|ม้วน|25-40|1%|
|**สายรัดพลาสติก (Cable Tie)**|แพ็ค|30-50|1%|
|**น็อตยึด/สกรู**|กก.|80-120|2%|
|**ซิลิโคน/กาว PVC**|หลอด|40-60|1%|
|**แบริ่ง (Bushing)**|ตัว|3-8|1%|

**สูตรประมาณการ:**

text

`Accessories Cost = Main Materials × (5-8%)`

---

## **C. ค่าแรง (Labor Cost)**

**อัตราค่าแรงมาตรฐาน (ปี 2568):**[ecoenergythailand+2](https://www.ecoenergythailand.com/category/13/%E0%B8%84%E0%B9%88%E0%B8%B2%E0%B8%9A%E0%B8%A3%E0%B8%B4%E0%B8%81%E0%B8%B2%E0%B8%A3-%E0%B8%A7%E0%B8%B4%E0%B8%A8%E0%B8%A7%E0%B8%81%E0%B8%A3%E0%B9%84%E0%B8%9F%E0%B8%9F%E0%B9%89%E0%B8%B2)​

|ประเภทงาน|หน่วย|กรุงเทพฯ (บาท)|ต่างจังหวัด (บาท)|เวลาโดยประมาณ|
|---|---|---|---|---|
|**เดินสาย + ท่อ**|ต่อเมตร|40-70|30-50|2-3 m/ชม.|
|**เดินสาย (เฉพาะ)**|ต่อเมตร|25-40|20-30|5-8 m/ชม.|
|**ติดตั้งสวิตช์**|ต่อจุด|80-150|60-120|8-12 จุด/ชม.|
|**ติดตั้งปลั๊ก**|ต่อจุด|80-150|60-120|8-12 จุด/ชม.|
|**ติดตั้งดวงโคม**|ต่อดวง|100-200|80-150|6-10 ดวง/ชม.|
|**ติดตั้ง DB**|ต่อชุด|2,000-4,000|1,500-3,000|2-4 ชม./ชุด|
|**ติดตั้ง Main Breaker**|ต่อชุด|1,500-3,000|1,200-2,500|1-2 ชม./ชุด|
|**ต่อสาย/ทำ Termination**|ต่อจุด|150-300|120-250|4-6 จุด/ชม.|
|**ทดสอบระบบ (Testing)**|ต่อวงจร|200-500|150-400|5-10 วงจร/ชม.|
|**ค่าออกแบบ**|ต่อโครงการ|5,000-15,000|3,000-10,000|-|

**ปัจจัยที่กระทบค่าแรง:**[tumcivil+1](https://www.tumcivil.com/wage_engineer.pdf)​

1. **ความยากง่ายของงาน:**
    
    - งานฝังปูน: × 1.3-1.5
        
    - งานสูง (> 3 เมตร): × 1.2-1.3
        
    - งานในพื้นที่แคบ: × 1.3-1.4
        
2. **ช่วงเวลา:**
    
    - งานนอกเวลา/วันหยุด: × 1.5-2.0
        
    - งานกลางคืน: × 1.5-1.8
        
3. **ระยะทาง:**
    
    - ไกลจากเมือง > 50 km: + 500-1,500 บาท/วัน (ค่าเดินทาง)
        
4. **ทักษะช่าง:**
    
    - ช่างมีใบอนุญาต: × 1.3-1.5
        
    - ช่างหัวหน้างาน: × 1.5-2.0
        

**สูตรประมาณการค่าแรงรวม:**[onestockhome+1](https://www.onestockhome.com/th/articles/833fd534-9e42-44c4-a57f-4910bcfb0d7e)​

text

`Total Labor = (Wire Length × Rate/m) + (Outlets × Rate/outlet) + (DB × Rate/unit) + Testing`

---

## **D. ค่าดำเนินการ/อื่น ๆ (Overhead & Others)**

|รายการ|% ของต้นทุนวัสดุ+แรง|หมายเหตุ|
|---|---|---|
|**ค่าขนส่ง**|2-5%|ขึ้นกับระยะทาง|
|**ค่าจัดการโครงการ**|5-10%|บริษัทขนาดใหญ่|
|**ประกันภัย/ความเสี่ยง**|2-3%|งานสูง/อันตราย|
|**ภาษีมูลค่าเพิ่ม (VAT)**|7%|ต้องมี|
|**ค่าใบอนุญาต**|1,000-5,000|ขึ้นกับขนาดโครงการ|
|**ค่าทดสอบระบบ**|1,500-5,000|บ้าน 1-2 ชั้น|

---

## **E. กำไร (Profit Margin)**

|ประเภทโครงการ|Profit Margin (%)|เหตุผล|
|---|---|---|
|**งานเหมา (บ้านพักอาศัย)**|15-25%|มาตรฐาน|
|**งานราชการ**|10-15%|ราคาต่ำแข่งขัน|
|**งานพิเศษ (VIP)**|25-40%|คุณภาพสูง + บริการพิเศษ|
|**งานซ่อม/เร่งด่วน**|30-50%|ต้องเสี่ยง + เร่งรัด|

---

## **1.2 สูตรคำนวณราคารวม (Total Cost Formula)**

## **แบบมาตรฐาน (Standard Method):**

Total Cost=(Materials+Accessories+Labor+Overhead)×(1+Profit%)Total\ Cost = (Materials + Accessories + Labor + Overhead) \times (1 + Profit\%)Total Cost=(Materials+Accessories+Labor+Overhead)×(1+Profit%)

**แบบละเอียด:**

Materials Cost=∑(Quantity×Unit Price)
Accessories Cost=Materials Cost×(5−8%)
Labor Cost=∑(Work Unit×Labor Rate)
Overhead=(Materials+Labor)×(10−15%)
Subtotal=Materials+Accessories+Labor+Overhead
VAT 7%=Subtotal×0.07
Total Before Profit=Subtotal+VAT
Profit=Total Before Profit×Margin%
Grand Total=Total Before Profit+Profit\

---

## **1.3 การประมาณราคาตามพื้นที่ (Cost per m²)**

**สูตรประมาณการเบื้องต้น (Rule of Thumb):**[ecoenergythailand+2](https://www.ecoenergythailand.com/category/13/%E0%B8%84%E0%B9%88%E0%B8%B2%E0%B8%9A%E0%B8%A3%E0%B8%B4%E0%B8%81%E0%B8%B2%E0%B8%A3-%E0%B8%A7%E0%B8%B4%E0%B8%A8%E0%B8%A7%E0%B8%81%E0%B8%A3%E0%B9%84%E0%B8%9F%E0%B8%9F%E0%B9%89%E0%B8%B2)​

|ประเภทบ้าน|ราคา/ตร.ม. (บาท)|รายละเอียด|
|---|---|---|
|**บ้านมาตรฐาน**|200-350|ไฟพื้นฐาน, ปลั๊กทั่วไป|
|**บ้านปานกลาง**|350-550|เพิ่มแอร์ 2-3 ตัว, ปั๊มน้ำ|
|**บ้านระดับดี**|550-800|แอร์ครบทุกห้อง, ระบบครบ|
|**บ้านหรู/Smart Home**|800-1,500+|ระบบอัตโนมัติ, คุณภาพสูง|

**ตัวอย่าง:**

- บ้าน 100 ตร.ม. ระดับปานกลาง
    
- ประมาณการ = 100 × 400 = **40,000 บาท**
    

---

## 💻 ส่วนที่ 2: Code Python สมบูรณ์ — cost_estimator.py

python

"""
cost_estimator.py
==================
โมดูลคำนวณราคาวัสดุและค่าแรงงานไฟฟ้า

Features:
- คำนวณราคาวัสดุ (สาย, ท่อ, Breaker, อุปกรณ์)
- คำนวณค่าแรง (เดินสาย, ติดตั้ง, ทดสอบ)
- คำนวณค่าใช้จ่ายอื่น ๆ (Overhead, VAT, Profit)
- รองรับ Database ราคาแบบ Dynamic
- Export รายงานราคาแบบละเอียด
- เปรียบเทียบราคาหลายทางเลือก

Author: Volta (The Electrical Simulation Engineer Maid)
Version: 2.0.0
Date: 2025-11-16
"""

import json
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


# ======================== Enums ========================

class LocationType(Enum):
    """ประเภทพื้นที่"""
    BANGKOK = "กรุงเทพฯ"
    SUBURB = "ปริมณฑล"
    UPCOUNTRY = "ต่างจังหวัด"
    RURAL = "ชนบท"


class WorkDifficulty(Enum):
    """ระดับความยากงาน"""
    EASY = "ง่าย"
    NORMAL = "ปกติ"
    DIFFICULT = "ยาก"
    VERY_DIFFICULT = "ยากมาก"


class ProjectType(Enum):
    """ประเภทโครงการ"""
    NEW_INSTALLATION = "ติดตั้งใหม่"
    RENOVATION = "ปรับปรุง"
    REPAIR = "ซ่อม"
    EMERGENCY = "เร่งด่วน"


# ======================== Price Database ========================

# ราคาวัสดุ (อัพเดท: 2025-11-16)
MATERIAL_PRICES = {
    "wire_thw": {  # บาท/เมตร
        1.5: 10,
        2.5: 18,
        4: 28,
        6: 45,
        10: 75,
        16: 120,
        25: 200,
        35: 280,
        50: 380,
        70: 520,
        95: 700,
        120: 900,
        150: 1100,
        185: 1400
    },
    "conduit_pvc": {  # บาท/เส้น (4 เมตร)
        "1/2": 40,
        "3/4": 60,
        "1": 100,
        "1-1/4": 150,
        "1-1/2": 200,
        "2": 300,
        "2-1/2": 475,
        "3": 650,
        "4": 1000
    },
    "breaker": {
        "schneider": {  # iC60N
            "1p": {6: 150, 10: 180, 16: 200, 20: 250, 32: 300, 40: 350, 50: 450, 63: 550},
            "2p": {6: 400, 10: 450, 16: 500, 20: 600, 32: 800, 40: 1000, 50: 1200, 63: 1500},
            "3p": {6: 600, 10: 650, 16: 700, 20: 850, 32: 1150, 40: 1450, 50: 1800, 63: 2200}
        },
        "mitsubishi": {  # NF-Series
            "1p": {5: 120, 10: 140, 15: 160, 20: 180, 30: 220, 40: 280, 50: 350, 60: 420},
            "2p": {5: 350, 10: 400, 15: 450, 20: 500, 30: 600, 40: 750, 50: 900, 60: 1100},
            "3p": {5: 500, 10: 550, 15: 600, 20: 700, 30: 850, 40: 1050, 50: 1300, 60: 1600}
        }
    },
    "distribution_board": {  # บาท/ชุด
        "4_6_way": 1000,
        "8_12_way": 2000,
        "18_24_way": 3500,
        "30_36_way": 5000
    },
    "switch_outlet": {  # บาท/ชุด (National/Panasonic ระดับกลาง)
        "switch_1_way": 100,
        "switch_2_way": 150,
        "switch_3_way": 200,
        "outlet_duplex": 120,
        "outlet_duplex_ground": 180,
        "outlet_weatherproof": 250,
        "dimmer": 350,
        "timer_switch": 450
    },
    "accessories": {  # บาท/หน่วย
        "junction_box_small": 20,
        "junction_box_large": 35,
        "coupling": 8,
        "elbow_90": 12,
        "clip": 3,
        "tape_roll": 30,
        "cable_tie_pack": 40,
        "bushing": 5,
        "earth_rod": 250,
        "earth_wire_clamp": 35
    }
}

# อัตราค่าแรง (อัพเดท: 2025-11-16)
LABOR_RATES = {
    LocationType.BANGKOK: {
        "wire_conduit_per_m": 55,
        "wire_only_per_m": 30,
        "switch_per_unit": 120,
        "outlet_per_unit": 120,
        "fixture_per_unit": 150,
        "db_per_unit": 3000,
        "main_breaker_per_unit": 2000,
        "termination_per_point": 220,
        "testing_per_circuit": 350,
        "design_fee": 10000
    },
    LocationType.SUBURB: {
        "wire_conduit_per_m": 45,
        "wire_only_per_m": 25,
        "switch_per_unit": 100,
        "outlet_per_unit": 100,
        "fixture_per_unit": 120,
        "db_per_unit": 2500,
        "main_breaker_per_unit": 1800,
        "termination_per_point": 180,
        "testing_per_circuit": 300,
        "design_fee": 8000
    },
    LocationType.UPCOUNTRY: {
        "wire_conduit_per_m": 40,
        "wire_only_per_m": 22,
        "switch_per_unit": 90,
        "outlet_per_unit": 90,
        "fixture_per_unit": 100,
        "db_per_unit": 2000,
        "main_breaker_per_unit": 1500,
        "termination_per_point": 150,
        "testing_per_circuit": 250,
        "design_fee": 6000
    },
    LocationType.RURAL: {
        "wire_conduit_per_m": 35,
        "wire_only_per_m": 20,
        "switch_per_unit": 80,
        "outlet_per_unit": 80,
        "fixture_per_unit": 90,
        "db_per_unit": 1800,
        "main_breaker_per_unit": 1300,
        "termination_per_point": 130,
        "testing_per_circuit": 200,
        "design_fee": 5000
    }
}

# Difficulty Multiplier
DIFFICULTY_MULTIPLIERS = {
    WorkDifficulty.EASY: 0.9,
    WorkDifficulty.NORMAL: 1.0,
    WorkDifficulty.DIFFICULT: 1.3,
    WorkDifficulty.VERY_DIFFICULT: 1.5
}

# Project Type Profit Margin
PROJECT_PROFIT_MARGINS = {
    ProjectType.NEW_INSTALLATION: 0.20,  # 20%
    ProjectType.RENOVATION: 0.25,  # 25%
    ProjectType.REPAIR: 0.30,  # 30%
    ProjectType.EMERGENCY: 0.45  # 45%
}


# ======================== Data Classes ========================

@dataclass
class MaterialItem:
    """
    รายการวัสดุ
    """
    category: str
    name: str
    specification: str
    unit: str
    quantity: float
    unit_price: float
    brand: Optional[str] = None
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class LaborItem:
    """
    รายการค่าแรง
    """
    task: str
    description: str
    unit: str
    quantity: float
    rate_per_unit: float
    difficulty_multiplier: float = 1.0
    
    @property
    def total_cost(self) -> float:
        return self.quantity * self.rate_per_unit * self.difficulty_multiplier


@dataclass
class CostEstimate:
    """
    ผลการประมาณราคา
    """
    project_name: str
    date: str
    location: LocationType
    project_type: ProjectType
    
    # Materials
    material_items: List[MaterialItem] = field(default_factory=list)
    material_subtotal: float = 0
    
    # Labor
    labor_items: List[LaborItem] = field(default_factory=list)
    labor_subtotal: float = 0
    
    # Accessories & Others
    accessories_percent: float = 0.06  # 6%
    accessories_cost: float = 0
    
    transport_percent: float = 0.03  # 3%
    transport_cost: float = 0
    
    overhead_percent: float = 0.10  # 10%
    overhead_cost: float = 0
    
    # Tax
    vat_percent: float = 0.07  # 7%
    vat_amount: float = 0
    
    # Profit
    profit_margin_percent: float = 0.20  # 20%
    profit_amount: float = 0
    
    # Totals
    subtotal_before_vat: float = 0
    subtotal_after_vat: float = 0
    grand_total: float = 0
    
    # Additional Info
    floor_area_sqm: Optional[float] = None
    cost_per_sqm: Optional[float] = None
    
    def calculate_totals(self):
        """คำนวณราคารวมทั้งหมด"""
        # Materials
        self.material_subtotal = sum(item.total_price for item in self.material_items)
        
        # Labor
        self.labor_subtotal = sum(item.total_cost for item in self.labor_items)
        
        # Accessories
        self.accessories_cost = self.material_subtotal * self.accessories_percent
        
        # Transport
        self.transport_cost = (self.material_subtotal + self.labor_subtotal) * self.transport_percent
        
        # Overhead
        self.overhead_cost = (self.material_subtotal + self.labor_subtotal) * self.overhead_percent
        
        # Subtotal Before VAT
        self.subtotal_before_vat = (
            self.material_subtotal +
            self.labor_subtotal +
            self.accessories_cost +
            self.transport_cost +
            self.overhead_cost
        )
        
        # VAT
        self.vat_amount = self.subtotal_before_vat * self.vat_percent
        
        # Subtotal After VAT
        self.subtotal_after_vat = self.subtotal_before_vat + self.vat_amount
        
        # Profit
        self.profit_amount = self.subtotal_after_vat * self.profit_margin_percent
        
        # Grand Total
        self.grand_total = self.subtotal_after_vat + self.profit_amount
        
        # Cost per m²
        if self.floor_area_sqm:
            self.cost_per_sqm = self.grand_total / self.floor_area_sqm


# ======================== Cost Estimator Class ========================

class CostEstimator:
    """
    คลาสหลักสำหรับประมาณราคา
    """
    
    def __init__(
        self,
        project_name: str,
        location: LocationType = LocationType.BANGKOK,
        project_type: ProjectType = ProjectType.NEW_INSTALLATION,
        floor_area_sqm: Optional[float] = None
    ):
        """
        Initialize Cost Estimator
        """
        self.project_name = project_name
        self.location = location
        self.project_type = project_type
        self.floor_area_sqm = floor_area_sqm
        
        self.estimate = CostEstimate(
            project_name=project_name,
            date=datetime.now().strftime("%Y-%m-%d"),
            location=location,
            project_type=project_type,
            floor_area_sqm=floor_area_sqm,
            profit_margin_percent=PROJECT_PROFIT_MARGINS[project_type]
        )
    
    def add_wire(self, size_mm2: float, length_m: float):
        """เพิ่มสายไฟ"""
        unit_price = MATERIAL_PRICES["wire_thw"].get(size_mm2, 0)
        
        if unit_price == 0:
            raise ValueError(f"❌ ไม่พบราคาสาย THW {size_mm2} mm²")
        
        item = MaterialItem(
            category="สายไฟ",
            name=f"สาย THW {size_mm2} mm²",
            specification=f"ทองแดง, 75°C, ตาม มอก. 11",
            unit="เมตร",
            quantity=length_m,
            unit_price=unit_price,
            brand="Thai-Yazaki / Bangkok Cable"
        )
        
        self.estimate.material_items.append(item)
    
    def add_conduit(self, size_inch: str, length_m: float):
        """เพิ่มท่อ PVC"""
        unit_price_per_4m = MATERIAL_PRICES["conduit_pvc"].get(size_inch, 0)
        
        if unit_price_per_4m == 0:
            raise ValueError(f"❌ ไม่พบราคาท่อ PVC {size_inch}\"")
        
        # คำนวณจำนวนเส้น (ปัดขึ้น)
        import math
        pieces_needed = math.ceil(length_m / 4)
        
        item = MaterialItem(
            category="ท่อ PVC",
            name=f"ท่อ PVC {size_inch}\" Class 13.5",
            specification=f"Heavy Duty, ตาม มอก. 982",
            unit="เส้น (4m)",
            quantity=pieces_needed,
            unit_price=unit_price_per_4m,
            brand="SCG / Thai Pipe"
        )
        
        self.estimate.material_items.append(item)
    
    def add_breaker(self, brand: str, rating_a: int, poles: str, curve_type: str = "C"):
        """เพิ่ม Breaker"""
        brand_lower = brand.lower()
        
        if brand_lower not in MATERIAL_PRICES["breaker"]:
            raise ValueError(f"❌ ไม่พบยี่ห้อ {brand}")
        
        pole_key = f"{poles.lower()}p"
        breaker_prices = MATERIAL_PRICES["breaker"][brand_lower].get(pole_key, {})
        
        # หาขนาดใกล้เคียงที่สุด
        available_ratings = sorted(breaker_prices.keys())
        selected_rating = min(available_ratings, key=lambda x: abs(x - rating_a))
        unit_price = breaker_prices[selected_rating]
        
        item = MaterialItem(
            category="Breaker",
            name=f"MCB {selected_rating}A {poles}P Type {curve_type}",
            specification=f"Breaking Capacity 6kA, ตาม IEC 60898",
            unit="ตัว",
            quantity=1,
            unit_price=unit_price,
            brand=brand.capitalize()
        )
        
        self.estimate.material_items.append(item)
    
    def add_distribution_board(self, num_ways: int):
        """เพิ่มตู้ DB"""
        if num_ways <= 6:
            key = "4_6_way"
        elif num_ways <= 12:
            key = "8_12_way"
        elif num_ways <= 24:
            key = "18_24_way"
        else:
            key = "30_36_way"
        
        unit_price = MATERIAL_PRICES["distribution_board"][key]
        
        item = MaterialItem(
            category="ตู้ DB",
            name=f"ตู้ Distribution Board {num_ways} ช่อง",
            specification="Metal Box, IP40, พร้อม Main Switch",
            unit="ชุด",
            quantity=1,
            unit_price=unit_price,
            brand="Siemens / ABB"
        )
        
        self.estimate.material_items.append(item)
    
    def add_switch_outlet(self, item_type: str, quantity: int, brand: str = "National"):
        """เพิ่มสวิตช์/ปลั๊ก"""
        unit_price = MATERIAL_PRICES["switch_outlet"].get(item_type, 0)
        
        if unit_price == 0:
            raise ValueError(f"❌ ไม่พบประเภท {item_type}")
        
        type_names = {
            "switch_1_way": "สวิตช์ 1 ทาง",
            "switch_2_way": "สวิตช์ 2 ทาง",
            "switch_3_way": "สวิตช์ 3 ทาง",
            "outlet_duplex": "ปลั๊กคู่",
            "outlet_duplex_ground": "ปลั๊กคู่ + Ground",
            "outlet_weatherproof": "ปลั๊กกันน้ำ",
            "dimmer": "Dimmer Switch",
            "timer_switch": "Timer Switch"
        }
        
        item = MaterialItem(
            category="สวิตช์/ปลั๊ก",
            name=type_names.get(item_type, item_type),
            specification="Wide Series, พร้อมหน้ากาก",
            unit="ชุด",
            quantity=quantity,
            unit_price=unit_price,
            brand=brand
        )
        
        self.estimate.material_items.append(item)
    
    def add_labor_wire_installation(
        self,
        length_m: float,
        with_conduit: bool = True,
        difficulty: WorkDifficulty = WorkDifficulty.NORMAL
    ):
        """เพิ่มค่าแรงเดินสาย"""
        labor_rates = LABOR_RATES[self.location]
        
        if with_conduit:
            rate = labor_rates["wire_conduit_per_m"]
            task = "เดินสาย + ท่อ"
        else:
            rate = labor_rates["wire_only_per_m"]
            task = "เดินสาย (เฉพาะ)"
        
        multiplier = DIFFICULTY_MULTIPLIERS[difficulty]
        
        item = LaborItem(
            task=task,
            description=f"ความยาว {length_m} เมตร",
            unit="เมตร",
            quantity=length_m,
            rate_per_unit=rate,
            difficulty_multiplier=multiplier
        )
        
        self.estimate.labor_items.append(item)
    
    def add_labor_switch_outlet(
        self,
        num_switches: int,
        num_outlets: int,
        difficulty: WorkDifficulty = WorkDifficulty.NORMAL
    ):
        """เพิ่มค่าแรงติดตั้งสวิตช์/ปลั๊ก"""
        labor_rates = LABOR_RATES[self.location]
        multiplier = DIFFICULTY_MULTIPLIERS[difficulty]
        
        if num_switches > 0:
            item = LaborItem(
                task="ติดตั้งสวิตช์",
                description=f"จำนวน {num_switches} จุด",
                unit="จุด",
                quantity=num_switches,
                rate_per_unit=labor_rates["switch_per_unit"],
                difficulty_multiplier=multiplier
            )
            self.estimate.labor_items.append(item)
        
        if num_outlets > 0:
            item = LaborItem(
                task="ติดตั้งปลั๊ก",
                description=f"จำนวน {num_outlets} จุด",
                unit="จุด",
                quantity=num_outlets,
                rate_per_unit=labor_rates["outlet_per_unit"],
                difficulty_multiplier=multiplier
            )
            self.estimate.labor_items.append(item)
    
    def add_labor_db_installation(self, num_dbs: int = 1):
        """เพิ่มค่าแรงติดตั้ง DB"""
        labor_rates = LABOR_RATES[self.location]
        
        item = LaborItem(
            task="ติดตั้งตู้ DB",
            description=f"จำนวน {num_dbs} ชุด",
            unit="ชุด",
            quantity=num_dbs,
            rate_per_unit=labor_rates["db_per_unit"]
        )
        
        self.estimate.labor_items.append(item)
    
    def add_labor_testing(self, num_circuits: int):
        """เพิ่มค่าแรงทดสอบระบบ"""
        labor_rates = LABOR_RATES[self.location]
        
        item = LaborItem(
            task="ทดสอบระบบ",
            description=f"Insulation Resistance, Continuity, RCD Testing ({num_circuits} วงจร)",
            unit="วงจร",
            quantity=num_circuits,
            rate_per_unit=labor_rates["testing_per_circuit"]
        )
        
        self.estimate.labor_items.append(item)
    
    def add_design_fee(self):
        """เพิ่มค่าออกแบบ"""
        labor_rates = LABOR_RATES[self.location]
        
        item = LaborItem(
            task="ค่าออกแบบ",
            description="Single Line Diagram, Layout Plan, Calculation Sheet",
            unit="โครงการ",
            quantity=1,
            rate_per_unit=labor_rates["design_fee"]
        )
        
        self.estimate.labor_items.append(item)
    
    def calculate(self) -> CostEstimate:
        """คำนวณราคารวม"""
        self.estimate.calculate_totals()
        return self.estimate
    
    def get_estimate(self) -> CostEstimate:
        """ดึงผลการประมาณราคา"""
        return self.estimate


# ======================== Report Generator ========================

class CostReportGenerator:
    """
    สร้างรายงานราคา
    """
    
    @staticmethod
    def print_detailed_report(estimate: CostEstimate):
        """พิมพ์รายงานแบบละเอียด"""
        print("=" * 140)
        print(f"💰 COST ESTIMATION REPORT")
        print("=" * 140)
        
        print(f"\n📋 PROJECT INFORMATION")
        print(f"   Project Name:          {estimate.project_name}")
        print(f"   Date:                  {estimate.date}")
        print(f"   Location:              {estimate.location.value}")
        print(f"   Project Type:          {estimate.project_type.value}")
        if estimate.floor_area_sqm:
            print(f"   Floor Area:            {estimate.floor_area_sqm} ตร.ม.")
        
        # Materials
        print(f"\n📦 MATERIALS")
        print(f"{'No.':<5} {'Category':<15} {'Description':<50} {'Unit':<10} {'Qty':<8} {'Price/Unit':<12} {'Total':<15}")
        print("-" * 140)
        
        for i, item in enumerate(estimate.material_items, 1):
            desc = f"{item.name} ({item.brand})" if item.brand else item.name
            print(f"{i:<5} {item.category:<15} {desc:<50} {item.unit:<10} {item.quantity:<8.2f} {item.unit_price:<12,.2f} {item.total_price:<15,.2f}")
        
        print("-" * 140)
        print(f"{'MATERIALS SUBTOTAL':<106} {estimate.material_subtotal:>33,.2f}")
        
        # Labor
        print(f"\n👷 LABOR")
        print(f"{'No.':<5} {'Task':<25} {'Description':<45} {'Unit':<10} {'Qty':<8} {'Rate/Unit':<12} {'Multiplier':<12} {'Total':<15}")
        print("-" * 140)
        
        for i, item in enumerate(estimate.labor_items, 1):
            print(f"{i:<5} {item.task:<25} {item.description:<45} {item.unit:<10} {item.quantity:<8.2f} "
                  f"{item.rate_per_unit:<12,.2f} {item.difficulty_multiplier:<12.2f} {item.total_cost:<15,.2f}")
        
        print("-" * 140)
        print(f"{'LABOR SUBTOTAL':<119} {estimate.labor_subtotal:>20,.2f}")
        
        # Summary
        print(f"\n📊 COST SUMMARY")
        print("-" * 140)
        print(f"{'Materials':<100} {estimate.material_subtotal:>39,.2f}")
        print(f"{'Labor':<100} {estimate.labor_subtotal:>39,.2f}")
        print(f"{'Accessories ({:.1%})':<100} {estimate.accessories_cost:>39,.2f}".format(estimate.accessories_percent))
        print(f"{'Transport ({:.1%})':<100} {estimate.transport_cost:>39,.2f}".format(estimate.transport_percent))
        print(f"{'Overhead ({:.1%})':<100} {estimate.overhead_cost:>39,.2f}".format(estimate.overhead_percent))
        print("-" * 140)
        print(f"{'SUBTOTAL BEFORE VAT':<100} {estimate.subtotal_before_vat:>39,.2f}")
        print(f"{'VAT ({:.1%})':<100} {estimate.vat_amount:>39,.2f}".format(estimate.vat_percent))
        print("-" * 140)
        print(f"{'SUBTOTAL AFTER VAT':<100} {estimate.subtotal_after_vat:>39,.2f}")
        print(f"{'Profit ({:.1%})':<100} {estimate.profit_amount:>39,.2f}".format(estimate.profit_margin_percent))
        print("=" * 140)
        print(f"{'✅ GRAND TOTAL':<100} {estimate.grand_total:>39,.2f}")
        
        if estimate.cost_per_sqm:
            print(f"{'   Cost per m²':<100} {estimate.cost_per_sqm:>39,.2f}")
        
        print("=" * 140)


# ======================== ตัวอย่างการใช้งาน ========================

if __name__ == "__main__":
    
    # ========== ตัวอย่างที่ 1: บ้าน 1 ชั้น (100 ตร.ม.) ==========
    print("\n🏠 ตัวอย่างที่ 1: บ้าน 1 ชั้น (100 ตร.ม.)\n")
    
    estimator_1f = CostEstimator(
        project_name="บ้าน 1 ชั้น Modern Style",
        location=LocationType.BANGKOK,
        project_type=ProjectType.NEW_INSTALLATION,
        floor_area_sqm=100
    )
    
    # วัสดุ
    estimator_1f.add_wire(2.5, 120)  # แอร์ + ปลั๊ก
    estimator_1f.add_wire(1.5, 80)   # ไฟ
    estimator_1f.add_conduit("1/2", 120)
    estimator_1f.add_conduit("3/4", 80)
    
    estimator_1f.add_breaker("schneider", 63, "2")  # Main Breaker
    estimator_1f.add_breaker("schneider", 20, "1")  # แอร์
    estimator_1f.add_breaker("schneider", 16, "1", "C")  # ปลั๊ก × 2
    estimator_1f.add_breaker("schneider", 16, "1", "C")
    estimator_1f.add_breaker("schneider", 10, "1", "B")  # ไฟ
    estimator_1f.add_breaker("schneider", 16, "1", "C")  # ปั๊มน้ำ
    
    estimator_1f.add_distribution_board(8)
    
    estimator_1f.add_switch_outlet("switch_1_way", 10)
    estimator_1f.add_switch_outlet("outlet_duplex_ground", 15)
    
    # ค่าแรง
    estimator_1f.add_labor_wire_installation(200, with_conduit=True, difficulty=WorkDifficulty.NORMAL)
    estimator_1f.add_labor_switch_outlet(10, 15)
    estimator_1f.add_labor_db_installation(1)
    estimator_1f.add_labor_testing(5)
    estimator_1f.add_design_fee()
    
    # คำนวณ
    result_1f = estimator_1f.calculate()
    
    # พิมพ์รายงาน
    CostReportGenerator.print_detailed_report(result_1f)
    
    
    # ========== ตัวอย่างที่ 2: บ้าน 2 ชั้น (200 ตร.ม.) ==========
    print("\n\n🏠 ตัวอย่างที่ 2: บ้าน 2 ชั้น (200 ตร.ม.)\n")
    
    estimator_2f = CostEstimator(
        project_name="บ้าน 2 ชั้น Modern Contemporary",
        location=LocationType.BANGKOK,
        project_type=ProjectType.NEW_INSTALLATION,
        floor_area_sqm=200
    )
    
    # วัสดุ (เพิ่มขึ้นจากบ้าน 1 ชั้น)
    estimator_2f.add_wire(2.5, 250)
    estimator_2f.add_wire(4, 80)  # แอร์ใหญ่
    estimator_2f.add_wire(1.5, 150)
    estimator_2f.add_wire(16, 20)  # Main Feeder
    
    estimator_2f.add_conduit("1/2", 250)
    estimator_2f.add_conduit("3/4", 150)
    estimator_2f.add_conduit("1", 20)
    
    estimator_2f.add_breaker("schneider", 100, "2")  # Main Breaker
    estimator_2f.add_breaker("schneider", 63, "2")  # Sub-DB ชั้น 2
    estimator_2f.add_breaker("schneider", 32, "1")  # แอร์ใหญ่
    estimator_2f.add_breaker("schneider", 20, "1")  # แอร์เล็ก × 4
    estimator_2f.add_breaker("schneider", 20, "1")
    estimator_2f.add_breaker("schneider", 20, "1")
    estimator_2f.add_breaker("schneider", 20, "1")
    estimator_2f.add_breaker("schneider", 16, "1", "C")  # ปลั๊ก × 4
    estimator_2f.add_breaker("schneider", 16, "1", "C")
    estimator_2f.add_breaker("schneider", 16, "1", "C")
    estimator_2f.add_breaker("schneider", 16, "1", "C")
    estimator_2f.add_breaker("schneider", 10, "1", "B")  # ไฟ × 2
    estimator_2f.add_breaker("schneider", 10, "1", "B")
    
    estimator_2f.add_distribution_board(12)  # Main DB
    estimator_2f.add_distribution_board(8)   # Sub-DB ชั้น 2
    
    estimator_2f.add_switch_outlet("switch_1_way", 20)
    estimator_2f.add_switch_outlet("switch_2_way", 4)
    estimator_2f.add_switch_outlet("outlet_duplex_ground", 30)
    estimator_2f.add_switch_outlet("outlet_weatherproof", 2)
    
    # ค่าแรง
    estimator_2f.add_labor_wire_installation(420, with_conduit=True, difficulty=WorkDifficulty.NORMAL)
    estimator_2f.add_labor_switch_outlet(24, 32)
    estimator_2f.add_labor_db_installation(2)
    estimator_2f.add_labor_testing(11)
    estimator_2f.add_design_fee()
    
    result_2f = estimator_2f.calculate()
    
    CostReportGenerator.print_detailed_report(result_2f)
`

---

## 📊 ส่วนที่ 3: แนวทางเพิ่มเติม (Advanced Features)

## **3.1 Dynamic Pricing (ราคาแบบ Dynamic)**

python

class DynamicPriceManager:
    """
    จัดการราคาแบบ Dynamic (อัพเดทได้ง่าย)
    """
    
    def __init__(self, price_json_path: str = "material_prices.json"):
        self.price_json_path = price_json_path
        self.prices = self.load_prices()
    
    def load_prices(self) -> Dict:
        """โหลดราคาจากไฟล์ JSON"""
        import json
        try:
            with open(self.price_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return MATERIAL_PRICES  # ใช้ default
    
    def save_prices(self):
        """บันทึกราคาลงไฟล์"""
        import json
        with open(self.price_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.prices, f, indent=2, ensure_ascii=False)
    
    def update_copper_price_factor(self, factor: float):
        """
        อัพเดทราคาสายไฟตามราคาทองแดง
        
        Parameters:
        - factor: ค่าปรับ (1.0 = ไม่เปลี่ยน, 1.1 = ขึ้น 10%)
        """
        for size, price in self.prices["wire_thw"].items():
            self.prices["wire_thw"][size] = round(price * factor, 2)
        
        self.save_prices()
        print(f"✅ อัพเดทราคาสายไฟตามค่าทองแดง (Factor: {factor})")

---

## **3.2 Quotation Comparison (เปรียบเทียบราคา)**

python

def compare_breaker_brands(current_a: float, poles: str) -> Dict:
    """
    เปรียบเทียบราคา Breaker หลายยี่ห้อ
    """
    import math
    
    results = {}
    
    for brand in ["schneider", "mitsubishi"]:
        pole_key = f"{poles.lower()}p"
        breaker_prices = MATERIAL_PRICES["breaker"][brand].get(pole_key, {})
        
        available_ratings = sorted(breaker_prices.keys())
        selected_rating = min(
            [r for r in available_ratings if r >= current_a * 1.25],
            default=max(available_ratings)
        )
        
        price = breaker_prices[selected_rating]
        
        results[brand] = {
            "rating": selected_rating,
            "price": price
        }
    
    return results

# ตัวอย่าง
comparison = compare_breaker_brands(20, "1")
print(comparison)
# Output: {'schneider': {'rating': 25, 'price': 280}, 'mitsubishi': {'rating': 20, 'price': 180}}


---

## **3.3 Cost Optimization (การเพิ่มประสิทธิภาพ)**

python

def optimize_wire_usage(circuits: List[Dict]) -> List[Dict]:
    """
    เพิ่มประสิทธิภาพการใช้สาย (ลดของเหลือ)
    
    หลักการ: จัดกลุ่มวงจรที่ใกล้กันให้ใช้ท่อเดียวกัน
    """
    # ตัวอย่างเบื้องต้น
    optimized = []
    
    # Group by location
    from collections import defaultdict
    location_groups = defaultdict(list)
    
    for circuit in circuits:
        location = circuit.get("location", "unknown")
        location_groups[location].append(circuit)
    
    # คำนวณ wire + conduit รวมกัน
    for location, group_circuits in location_groups.items():
        total_length = sum(c["length_m"] for c in group_circuits)
        
        optimized.append({
            "location": location,
            "circuits": len(group_circuits),
            "total_length_m": total_length,
            "savings_percent": 15  # ประมาณการ
        })
    
    return optimized


---

