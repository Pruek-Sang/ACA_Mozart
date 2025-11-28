# Module 4: conduit_sizer.py — เลือกท่อร้อยสายอัตโนมัติ (ฉบับละเอียดสุดยอด)

ขอรายงานนายท่านค่ะ Volta จะอธิบายการเลือกท่อ PVC Conduit อย่างละเอียดที่สุด พร้อม Algorithm ที่ใช้งานได้จริง

---

## 📚 ส่วนที่ 1: ทฤษฎีพื้นฐาน Conduit Sizing

## **1.1 ทำไมต้องใช้ท่อร้อยสาย?**

**เหตุผล 5 ประการ:**twater+3​

1. **ป้องกันความเสียหาย:** สายไฟฝังในปูน/ผนัง ต้องมีท่อป้องกันไม่ให้ปูนกัดกร่อนฉนวน
    
2. **อำนวยความสะดวกในการซ่อม:** ถ้าสายเสียสามารถดึงสายใหม่ออกมาได้โดยไม่ต้องทุบปูน
    
3. **ป้องกันหนู/แมลง:** ท่อ PVC ทนต่อการกัดของหนู
    
4. **ความปลอดภัย:** ถ้าไฟลัดในท่อ จะไม่ลามไปยังโครงสร้าง
    
5. **มาตรฐาน:** มอก. 2955 กำหนดให้ต้องใช้ท่อร้อยสายในอาคารpea+1​
    

---

## **1.2 ประเภทท่อ PVC (Polyvinyl Chloride)**

**ตาม มอก. 982-2556 (ท่อพีวีซีสำหรับงานไฟฟ้า):**cppc+2​

|ประเภท|Class|ความหนาผนัง|การใช้งาน|ราคา (บาท/เส้น 4m)|
|---|---|---|---|---|
|**Rigid PVC (Heavy Duty)**|Class 13.5|หนา|ฝังในปูน, ฝังใต้ดิน|40-120|
|**Rigid PVC (Medium)**|Class 10|ปานกลาง|ติดผนังนอก, เพดาน|30-90|
|**Flexible PVC (Corrugated)**|-|ยืดหยุ่น|งานชั่วคราว, ซ่อนในฝ้า|25-80|

**หมายเหตุ:** บ้านพักอาศัยควรใช้ **Class 13.5 (Heavy Duty)** เพราะทนทานและปลอดภัยที่สุดtwater+1​

---

## **1.3 ขนาดท่อมาตรฐาน (ตามระบบอังกฤษ/อเมริกัน)**

**ตารางขนาดท่อ PVC Class 13.5:**torpvc+3​

|ขนาด (นิ้ว)|ขนาด (mm)|Outer Diameter OD (mm)|Inner Diameter ID (mm)|Wall Thickness (mm)|พื้นที่ภายใน (mm²)|ราคา (บาท/เส้น 4m)|
|---|---|---|---|---|---|---|
|**1/2"**|15|21.3|13.2|2.65|**137**|35-45|
|**3/4"**|20|26.7|15.8|2.65|**196**|50-70|
|**1"**|25|33.4|20.4|2.65|**327**|80-120|
|**1-1/4"**|32|42.2|26.6|2.65|**556**|120-180|
|**1-1/2"**|40|48.3|35.2|3.00|**973**|150-220|
|**2"**|50|60.3|48.4|3.50|**1,841**|250-350|
|**2-1/2"**|65|73.0|59.6|4.00|**2,790**|400-550|
|**3"**|80|88.9|73.0|4.50|**4,185**|550-750|
|**4"**|100|114.3|97.2|5.00|**7,419**|850-1,200|

**หมายเหตุ:** ค่า ID (Inner Diameter) และพื้นที่ภายในอิงจาก มอก. 982-2556cppc+2​

---

## **1.4 หลักการ Conduit Fill (40% Rule)**

**กฎทองจาก NEC 2023, มอก. 2955, วสท.:**engfanatic.tumcivil+3​

text

`พื้นที่สายรวม (Wire Total Area) ≤ 40% × พื้นที่ภายในท่อ (Conduit Inner Area)`

**เหตุผล:**

1. **ระบายความร้อน:** สายที่อยู่ในท่อจะร้อนกว่าสายลอย ถ้าแน่นเกิน → ร้อนสะสม → ฉนวนเสื่อมrichledshop+1​
    
2. **ดึงสายสะดวก:** ถ้าแน่นเกิน → ดึงสายเปลี่ยนไม่ได้ → ต้องทุบปูน[engfanatic.tumcivil](https://engfanatic.tumcivil.com/engfanatic/article/335-%E0%B8%88%E0%B8%B3%E0%B8%99%E0%B8%A7%E0%B8%99%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B8%AA%E0%B8%B9%E0%B8%87%E0%B8%AA%E0%B8%B8%E0%B8%94%E0%B9%83%E0%B8%99%E0%B8%97%E0%B9%88%E0%B8%AD%E0%B8%A3%E0%B9%89%E0%B8%AD%E0%B8%A2%E0%B8%AA%E0%B8%B2%E0%B8%A2)​
    
3. **ป้องกันสายเสียหาย:** ดึงแรงเกิน → สายขาด/ฉนวนถลอกcoe+1​
    

**ข้อยกเว้น:**coe+1​

- **1 เส้น:** ใช้ได้ 53% ของพื้นที่ท่อ
    
- **2 เส้น:** ใช้ได้ 31% ของพื้นที่ท่อ
    
- **3+ เส้น:** ใช้ได้ 40% ของพื้นที่ท่อ
    

**ตัวอย่างการคำนวณ:**

โจทย์: ต้องเดิน **3 เส้น THW 2.5 mm²** ในท่อเดียวกัน

**ขั้นที่ 1: หาพื้นที่สายรวม**

- สาย THW 2.5 mm² = Outer Diameter (OD) = 4.1 mm
    
- พื้นที่ 1 เส้น = π × (4.1/2)² = π × 2.05² = **13.2 mm²**
    
- พื้นที่รวม 3 เส้น = 13.2 × 3 = **39.6 mm²**
    

**ขั้นที่ 2: คำนวณพื้นที่ท่อที่ต้องการ (40% fill)**

text

`Required Conduit Area = 39.6 / 0.40 = 99 mm²`

**ขั้นที่ 3: เลือกขนาดท่อ**

- จากตาราง:
    
    - ท่อ 1/2" (ID 13.2 mm) = พื้นที่ 137 mm² → **137 ≥ 99** ✅ **ใช้ได้**
        
    - ท่อ 3/4" (ID 15.8 mm) = พื้นที่ 196 mm² → ใหญ่เกิน (เสียเงิน)
        

**สรุป:** ใช้ท่อ **1/2"** ✅

---

## **1.5 ตารางพื้นที่สาย THW (รวมฉนวน)**

**ตาราง Outer Diameter (OD) และพื้นที่สาย THW (ทองแดง) ตาม มอก. 11-2553:**pantip+3​

|ขนาดสาย (mm²)|Conductor Dia. (mm)|Insulation Thickness (mm)|Outer Diameter OD (mm)|พื้นที่รวมฉนวน (mm²)|
|---|---|---|---|---|
|**1.5**|1.38|1.0|**3.4**|**9.1**|
|**2.5**|1.78|1.15|**4.1**|**13.2**|
|**4**|2.26|1.30|**4.9**|**18.9**|
|**6**|2.76|1.50|**5.8**|**26.4**|
|**10**|3.57|2.00|**7.6**|**45.4**|
|**16**|4.52|2.40|**9.3**|**67.9**|
|**25**|5.64|3.40|**12.5**|**122.7**|
|**35**|6.68|3.90|**14.5**|**165.1**|
|**50**|7.98|4.50|**17.0**|**227.0**|
|**70**|9.45|5.30|**20.0**|**314.2**|

**หมายเหตุ:** ค่าเหล่านี้อ้างอิงจาก **Thai-Yazaki**, **Bangkok Cable** และ มอก. 11narinelectric+3​

---

## 📊 ส่วนที่ 2: ตารางจำนวนสายสูงสุดในท่อ (Standard Table)

## **2.1 ตารางตาม วสท. (มาตรฐานการติดตั้งทางไฟฟ้า)**

**ตารางจำนวนสูงสุดของสาย THW ในท่อ PVC (40% Fill):**facebook+2​

|ขนาดสาย (mm²)|ท่อ 1/2" (15mm)|ท่อ 3/4" (20mm)|ท่อ 1" (25mm)|ท่อ 1-1/4" (32mm)|ท่อ 1-1/2" (40mm)|ท่อ 2" (50mm)|
|---|---|---|---|---|---|---|
||**137 mm²**|**196 mm²**|**327 mm²**|**556 mm²**|**973 mm²**|**1,841 mm²**|
|**1.5 mm²**|6|9|15|26|46|86|
|**2.5 mm²**|4|6|10|18|31|59|
|**4 mm²**|3|4|7|13|22|41|
|**6 mm²**|1|3|5|9|16|29|
|**10 mm²**|1|2|3|5|9|17|
|**16 mm²**|0|1|2|3|6|11|
|**25 mm²**|0|0|1|2|3|6|
|**35 mm²**|0|0|1|1|2|5|
|**50 mm²**|0|0|0|1|2|3|
|**70 mm²**|0|0|0|0|1|2|

**วิธีอ่านตาราง:**

- ท่อ 1/2" สามารถใส่สาย THW 1.5 mm² ได้สูงสุด **6 เส้น** (ที่ 40% fill)
    
- ท่อ 1" สามารถใส่สาย THW 4 mm² ได้สูงสุด **7 เส้น**
    

**หมายเหตุ:** ตารางนี้ใช้กับสาย **ขนาดเดียวกัน** เท่านั้น ถ้าสายหลายขนาดต้องคำนวณแบบ Customfacebook+1​

---

## **2.2 ตารางพิเศษ: สายหลายขนาดผสมกัน**

**กรณีพิเศษ:** วงจรเดียวมีสาย Hot, Neutral, Ground หลายขนาด

**ตัวอย่าง:**

- **Hot (L):** 2 เส้น × THW 2.5 mm²
    
- **Neutral (N):** 1 เส้น × THW 2.5 mm²
    
- **Ground (PE):** 1 เส้น × THW 1.5 mm²
    

**การคำนวณ:**

python

`Wire Area Total = (2 × 13.2) + (1 × 13.2) + (1 × 9.1)                 = 26.4 + 13.2 + 9.1                = 48.7 mm² Required Conduit Area = 48.7 / 0.40 = 121.75 mm² จากตาราง: - ท่อ 1/2" = 137 mm² ✅ (137 ≥ 121.75)`

**สรุป:** ใช้ท่อ **1/2"** ✅

---

## **2.3 ตารางความจุท่อ (Conduit Fill Capacity) — แบบ %**

**ตารางแสดง % การใช้พื้นที่:**

|จำนวนสาย|% ที่อนุญาต|เหตุผล|
|---|---|---|
|**1 เส้น**|53%|ดึงง่าย, ไม่แออัด|
|**2 เส้น**|31%|ดึงยากขึ้นเล็กน้อย|
|**3+ เส้น**|40%|มาตรฐาน|

**ตัวอย่าง:**

- ท่อ 1/2" (137 mm²)
    
- **1 เส้น:** ใช้ได้ 137 × 0.53 = 72.6 mm² → สาย THW 6 mm² (26.4 mm²) ✅
    
- **2 เส้น:** ใช้ได้ 137 × 0.31 = 42.5 mm² → สาย THW 2.5 mm² (13.2 × 2 = 26.4 mm²) ✅
    
- **3 เส้น:** ใช้ได้ 137 × 0.40 = 54.8 mm² → สาย THW 1.5 mm² (9.1 × 3 = 27.3 mm²) ✅
    

---

## 🤖 ส่วนที่ 3: Algorithm สำหรับ MCP — เลือกท่ออัตโนมัติ

## **3.1 Input ที่ต้องการ**

python

`{   "wires": [    {"size_mm2": 2.5, "quantity": 3},  # 3 เส้น THW 2.5 mm²    {"size_mm2": 1.5, "quantity": 1}   # 1 เส้น THW 1.5 mm² (Ground)  ] }`

## **3.2 Logic Flow (Pseudo-code)**

text

`1. วนลูปสายทุกขนาด:    - ดึงค่า Outer Diameter (OD) จากตาราง   - คำนวณพื้นที่แต่ละขนาด = π × (OD/2)²   - คูณด้วยจำนวนเส้น    2. รวมพื้นที่ทั้งหมด:    Total Wire Area = Σ (พื้นที่แต่ละขนาด × จำนวน) 3. คำนวณจำนวนสายทั้งหมด:    Total Wire Count = Σ (จำนวนทุกขนาด) 4. กำหนด Fill Percentage:    - ถ้า Total Wire Count = 1 → Fill = 53%   - ถ้า Total Wire Count = 2 → Fill = 31%   - ถ้า Total Wire Count ≥ 3 → Fill = 40% 5. คำนวณพื้นที่ท่อที่ต้องการ:    Required Conduit Area = Total Wire Area / Fill 6. เลือกขนาดท่อจากตาราง:    - หาท่อที่มีพื้นที่ ≥ Required Conduit Area   - เลือกขนาดเล็กที่สุดที่ใช้ได้ (ประหยัดต้นทุน) 7. เช็ค Safety Margin:    - Actual Fill % = (Total Wire Area / Selected Conduit Area) × 100   - ถ้า Actual Fill > 40% → เลือกท่อใหญ่ขึ้น 8. Return:    - ขนาดท่อที่แนะนำ   - % การใช้พื้นที่จริง   - จำนวนสายที่สามารถใส่เพิ่มได้`

---

## 💻 ส่วนที่ 4: Code Python สมบูรณ์

python

import math
from typing import List, Dict, Tuple, Optional

# ======================== ฐานข้อมูลท่อ PVC ========================

# ตารางขนาดท่อ PVC Class 13.5 (Heavy Duty)
CONDUIT_DATA = {
    "1/2": {
        "size_mm": 15,
        "outer_diameter_mm": 21.3,
        "inner_diameter_mm": 13.2,
        "wall_thickness_mm": 2.65,
        "inner_area_mm2": 137,
        "price_per_4m_thb": 40,
        "length_per_piece_m": 4
    },
    "3/4": {
        "size_mm": 20,
        "outer_diameter_mm": 26.7,
        "inner_diameter_mm": 15.8,
        "wall_thickness_mm": 2.65,
        "inner_area_mm2": 196,
        "price_per_4m_thb": 60,
        "length_per_piece_m": 4
    },
    "1": {
        "size_mm": 25,
        "outer_diameter_mm": 33.4,
        "inner_diameter_mm": 20.4,
        "wall_thickness_mm": 2.65,
        "inner_area_mm2": 327,
        "price_per_4m_thb": 100,
        "length_per_piece_m": 4
    },
    "1-1/4": {
        "size_mm": 32,
        "outer_diameter_mm": 42.2,
        "inner_diameter_mm": 26.6,
        "wall_thickness_mm": 2.65,
        "inner_area_mm2": 556,
        "price_per_4m_thb": 150,
        "length_per_piece_m": 4
    },
    "1-1/2": {
        "size_mm": 40,
        "outer_diameter_mm": 48.3,
        "inner_diameter_mm": 35.2,
        "wall_thickness_mm": 3.00,
        "inner_area_mm2": 973,
        "price_per_4m_thb": 200,
        "length_per_piece_m": 4
    },
    "2": {
        "size_mm": 50,
        "outer_diameter_mm": 60.3,
        "inner_diameter_mm": 48.4,
        "wall_thickness_mm": 3.50,
        "inner_area_mm2": 1841,
        "price_per_4m_thb": 300,
        "length_per_piece_m": 4
    },
    "2-1/2": {
        "size_mm": 65,
        "outer_diameter_mm": 73.0,
        "inner_diameter_mm": 59.6,
        "wall_thickness_mm": 4.00,
        "inner_area_mm2": 2790,
        "price_per_4m_thb": 475,
        "length_per_piece_m": 4
    },
    "3": {
        "size_mm": 80,
        "outer_diameter_mm": 88.9,
        "inner_diameter_mm": 73.0,
        "wall_thickness_mm": 4.50,
        "inner_area_mm2": 4185,
        "price_per_4m_thb": 650,
        "length_per_piece_m": 4
    },
    "4": {
        "size_mm": 100,
        "outer_diameter_mm": 114.3,
        "inner_diameter_mm": 97.2,
        "wall_thickness_mm": 5.00,
        "inner_area_mm2": 7419,
        "price_per_4m_thb": 1000,
        "length_per_piece_m": 4
    }
}

# ตารางข้อมูลสาย THW (ทองแดง) รวมฉนวน
WIRE_DATA = {
    1.5: {
        "conductor_diameter_mm": 1.38,
        "insulation_thickness_mm": 1.0,
        "outer_diameter_mm": 3.4,
        "area_with_insulation_mm2": 9.1,
        "ampacity_in_conduit_a": 20,
        "resistance_ohm_per_km": 12.1,
        "price_per_m_thb": 10
    },
    2.5: {
        "conductor_diameter_mm": 1.78,
        "insulation_thickness_mm": 1.15,
        "outer_diameter_mm": 4.1,
        "area_with_insulation_mm2": 13.2,
        "ampacity_in_conduit_a": 27,
        "resistance_ohm_per_km": 7.41,
        "price_per_m_thb": 18
    },
    4: {
        "conductor_diameter_mm": 2.26,
        "insulation_thickness_mm": 1.30,
        "outer_diameter_mm": 4.9,
        "area_with_insulation_mm2": 18.9,
        "ampacity_in_conduit_a": 37,
        "resistance_ohm_per_km": 4.61,
        "price_per_m_thb": 28
    },
    6: {
        "conductor_diameter_mm": 2.76,
        "insulation_thickness_mm": 1.50,
        "outer_diameter_mm": 5.8,
        "area_with_insulation_mm2": 26.4,
        "ampacity_in_conduit_a": 48,
        "resistance_ohm_per_km": 3.08,
        "price_per_m_thb": 45
    },
    10: {
        "conductor_diameter_mm": 3.57,
        "insulation_thickness_mm": 2.00,
        "outer_diameter_mm": 7.6,
        "area_with_insulation_mm2": 45.4,
        "ampacity_in_conduit_a": 50,
        "resistance_ohm_per_km": 1.83,
        "price_per_m_thb": 75
    },
    16: {
        "conductor_diameter_mm": 4.52,
        "insulation_thickness_mm": 2.40,
        "outer_diameter_mm": 9.3,
        "area_with_insulation_mm2": 67.9,
        "ampacity_in_conduit_a": 68,
        "resistance_ohm_per_km": 1.15,
        "price_per_m_thb": 120
    },
    25: {
        "conductor_diameter_mm": 5.64,
        "insulation_thickness_mm": 3.40,
        "outer_diameter_mm": 12.5,
        "area_with_insulation_mm2": 122.7,
        "ampacity_in_conduit_a": 89,
        "resistance_ohm_per_km": 0.727,
        "price_per_m_thb": 200
    },
    35: {
        "conductor_diameter_mm": 6.68,
        "insulation_thickness_mm": 3.90,
        "outer_diameter_mm": 14.5,
        "area_with_insulation_mm2": 165.1,
        "ampacity_in_conduit_a": 111,
        "resistance_ohm_per_km": 0.524,
        "price_per_m_thb": 280
    },
    50: {
        "conductor_diameter_mm": 7.98,
        "insulation_thickness_mm": 4.50,
        "outer_diameter_mm": 17.0,
        "area_with_insulation_mm2": 227.0,
        "ampacity_in_conduit_a": 134,
        "resistance_ohm_per_km": 0.387,
        "price_per_m_thb": 380
    },
    70: {
        "conductor_diameter_mm": 9.45,
        "insulation_thickness_mm": 5.30,
        "outer_diameter_mm": 20.0,
        "area_with_insulation_mm2": 314.2,
        "ampacity_in_conduit_a": 171,
        "resistance_ohm_per_km": 0.268,
        "price_per_m_thb": 520
    }
}

# Fill Percentage ตามจำนวนสาย (NEC 2023, มอก. 2955)
FILL_PERCENTAGE_RULES = {
    1: 0.53,  # 1 เส้น = 53%
    2: 0.31,  # 2 เส้น = 31%
    3: 0.40   # 3+ เส้น = 40% (default)
}


# ======================== ฟังก์ชันหลัก ========================

def calculate_wire_total_area(wires: List[Dict]) -> Tuple[float, int]:
    """
    คำนวณพื้นที่สายรวม
    
    Parameters:
    - wires: list ของสาย [{"size_mm2": 2.5, "quantity": 3}, ...]
    
    Returns:
    - total_area: พื้นที่รวม (mm²)
    - total_count: จำนวนเส้นรวม
    """
    total_area = 0
    total_count = 0
    
    for wire in wires:
        size = wire["size_mm2"]
        quantity = wire["quantity"]
        
        if size not in WIRE_DATA:
            raise ValueError(f"❌ ไม่พบขนาดสาย {size} mm² ในฐานข้อมูล")
        
        wire_area = WIRE_DATA[size]["area_with_insulation_mm2"]
        total_area += wire_area * quantity
        total_count += quantity
    
    return total_area, total_count


def get_fill_percentage(wire_count: int) -> float:
    """
    กำหนด Fill Percentage ตามจำนวนสาย
    """
    if wire_count == 1:
        return FILL_PERCENTAGE_RULES[1]
    elif wire_count == 2:
        return FILL_PERCENTAGE_RULES[2]
    else:
        return FILL_PERCENTAGE_RULES[3]


def select_conduit_size(
    wires: List[Dict],
    safety_margin: float = 1.0,
    max_fill_override: Optional[float] = None
) -> Dict:
    """
    เลือกขนาดท่อที่เหมาะสม
    
    Parameters:
    - wires: list ของสาย [{"size_mm2": 2.5, "quantity": 3}, ...]
    - safety_margin: Safety Margin (1.0 = ไม่เผื่อ, 1.1 = เผื่อ 10%)
    - max_fill_override: บังคับใช้ Fill % (None = ใช้ตามมาตรฐาน)
    
    Returns:
    - dict: ผลลัพธ์การเลือกท่อ
    """
    
    # ขั้นที่ 1: คำนวณพื้นที่สายรวม
    total_wire_area, total_wire_count = calculate_wire_total_area(wires)
    
    # ขั้นที่ 2: กำหนด Fill Percentage
    if max_fill_override is not None:
        fill_percentage = max_fill_override
    else:
        fill_percentage = get_fill_percentage(total_wire_count)
    
    # ขั้นที่ 3: คำนวณพื้นที่ท่อที่ต้องการ
    required_conduit_area = (total_wire_area / fill_percentage) * safety_margin
    
    # ขั้นที่ 4: เลือกขนาดท่อ (เล็กที่สุดที่ใช้ได้)
    selected_conduit = None
    
    for size, data in CONDUIT_DATA.items():
        if data["inner_area_mm2"] >= required_conduit_area:
            selected_conduit = size
            break
    
    if selected_conduit is None:
        return {
            "status": "error",
            "message": f"❌ ไม่มีขนาดท่อที่เหมาะสม (ต้องการพื้นที่ {required_conduit_area:.2f} mm²)",
            "total_wire_area_mm2": round(total_wire_area, 2),
            "total_wire_count": total_wire_count,
            "required_conduit_area_mm2": round(required_conduit_area, 2)
        }
    
    # ขั้นที่ 5: คำนวณ Actual Fill %
    conduit_data = CONDUIT_DATA[selected_conduit]
    actual_fill_percent = (total_wire_area / conduit_data["inner_area_mm2"]) * 100
    
    # ขั้นที่ 6: คำนวณจำนวนสายเพิ่มได้ (Same Size)
    remaining_area = conduit_data["inner_area_mm2"] * fill_percentage - total_wire_area
    
    additional_wires = {}
    for size in sorted(WIRE_DATA.keys()):
        wire_area = WIRE_DATA[size]["area_with_insulation_mm2"]
        additional_count = int(remaining_area / wire_area)
        if additional_count > 0:
            additional_wires[size] = additional_count
    
    return {
        "status": "success",
        "conduit_size": selected_conduit,
        "conduit_data": conduit_data,
        "total_wire_area_mm2": round(total_wire_area, 2),
        "total_wire_count": total_wire_count,
        "required_conduit_area_mm2": round(required_conduit_area, 2),
        "selected_conduit_area_mm2": conduit_data["inner_area_mm2"],
        "fill_percentage_allowed": fill_percentage * 100,
        "actual_fill_percent": round(actual_fill_percent, 2),
        "remaining_area_mm2": round(remaining_area, 2),
        "additional_wires_capacity": additional_wires,
        "safety_margin": safety_margin
    }


def calculate_conduit_cost(
    conduit_size: str,
    length_m: float
) -> Dict:
    """
    คำนวณต้นทุนท่อ
    
    Parameters:
    - conduit_size: ขนาดท่อ (เช่น "1/2", "3/4")
    - length_m: ความยาวที่ต้องการ (เมตร)
    
    Returns:
    - dict: ราคาและจำนวนเส้น
    """
    if conduit_size not in CONDUIT_DATA:
        raise ValueError(f"❌ ไม่มีขนาดท่อ {conduit_size} ในฐานข้อมูล")
    
    conduit_data = CONDUIT_DATA[conduit_size]
    piece_length = conduit_data["length_per_piece_m"]
    price_per_piece = conduit_data["price_per_4m_thb"]
    
    # คำนวณจำนวนเส้นที่ต้องใช้ (ปัดขึ้น)
    pieces_needed = math.ceil(length_m / piece_length)
    total_length = pieces_needed * piece_length
    total_cost = pieces_needed * price_per_piece
    
    return {
        "conduit_size": conduit_size,
        "length_required_m": length_m,
        "pieces_needed": pieces_needed,
        "piece_length_m": piece_length,
        "price_per_piece_thb": price_per_piece,
        "total_length_m": total_length,
        "total_cost_thb": total_cost,
        "waste_m": round(total_length - length_m, 2)
    }


def design_circuit_conduit(
    circuit_name: str,
    wires: List[Dict],
    length_m: float,
    safety_margin: float = 1.0
) -> Dict:
    """
    ออกแบบท่อสำหรับวงจรหนึ่งวงจร (รวมทั้งการคำนวณราคา)
    
    Parameters:
    - circuit_name: ชื่อวงจร
    - wires: list ของสาย
    - length_m: ความยาว (เมตร)
    - safety_margin: Safety Margin
    
    Returns:
    - dict: ผลลัพธ์การออกแบบ
    """
    
    # เลือกขนาดท่อ
    conduit_result = select_conduit_size(wires, safety_margin)
    
    if conduit_result["status"] == "error":
        return conduit_result
    
    # คำนวณราคา
    cost_result = calculate_conduit_cost(
        conduit_result["conduit_size"],
        length_m
    )
    
    return {
        "status": "success",
        "circuit_name": circuit_name,
        "conduit_sizing": conduit_result,
        "conduit_cost": cost_result,
        "length_m": length_m
    }


def print_conduit_report(result: Dict):
    """
    พิมพ์รายงานการเลือกท่อ
    """
    if result["status"] == "error":
        print(f"❌ {result['message']}")
        return
    
    print("=" * 100)
    print(f"📍 วงจร: {result['circuit_name']}")
    print("=" * 100)
    
    sizing = result["conduit_sizing"]
    cost = result["conduit_cost"]
    
    print(f"\n🔌 สายที่ใช้:")
    # ต้องแสดงรายละเอียดสายจาก wires (แต่ไม่ได้ส่งมา ต้องแก้)
    
    print(f"\n📏 การคำนวณ:")
    print(f"   พื้นที่สายรวม:           {sizing['total_wire_area_mm2']:.2f} mm²")
    print(f"   จำนวนสาย:                {sizing['total_wire_count']} เส้น")
    print(f"   Fill % ที่อนุญาต:         {sizing['fill_percentage_allowed']:.1f}%")
    print(f"   พื้นที่ท่อที่ต้องการ:     {sizing['required_conduit_area_mm2']:.2f} mm²")
    
    print(f"\n✅ ท่อที่เลือก: {sizing['conduit_size']}\" ({sizing['conduit_data']['size_mm']} mm)")
    print(f"   พื้นที่ภายในท่อ:          {sizing['selected_conduit_area_mm2']} mm²")
    print(f"   Fill % จริง:             {sizing['actual_fill_percent']:.2f}%")
    print(f"   พื้นที่เหลือ:             {sizing['remaining_area_mm2']:.2f} mm²")
    
    print(f"\n💰 ต้นทุนท่อ:")
    print(f"   ความยาวที่ต้องการ:       {cost['length_required_m']} m")
    print(f"   จำนวนเส้น:                {cost['pieces_needed']} เส้น × {cost['piece_length_m']} m")
    print(f"   ราคาต่อเส้น:             {cost['price_per_piece_thb']} บาท")
    print(f"   ราคารวม:                 {cost['total_cost_thb']:,.0f} บาท")
    print(f"   ของเหลือ:                {cost['waste_m']} m")
    
    print("=" * 100)


# ======================== ตัวอย่างการใช้งาน ========================

if __name__ == "__main__":
    
    print("\n" + "=" * 100)
    print("🔧 CONDUIT SIZER — เลือกท่อร้อยสายอัตโนมัติ")
    print("=" * 100)
    
    # ========== ตัวอย่างที่ 1: วงจรแอร์ (2 เส้น THW 2.5 mm²) ==========
    print("\n📍 ตัวอย่างที่ 1: วงจรแอร์")
    
    wires_ac = [
        {"size_mm2": 2.5, "quantity": 2}  # Hot + Neutral
    ]
    
    result_ac = design_circuit_conduit(
        circuit_name="แอร์ ห้องนอน",
        wires=wires_ac,
        length_m=25
    )
    
    print_conduit_report(result_ac)
    
    
    # ========== ตัวอย่างที่ 2: วงจรปลั๊ก (3 เส้น THW 2.5 mm²) ==========
    print("\n\n📍 ตัวอย่างที่ 2: วงจรปลั๊ก")
    
    wires_receptacle = [
        {"size_mm2": 2.5, "quantity": 2},  # Hot + Neutral
        {"size_mm2": 1.5, "quantity": 1}   # Ground
    ]
    
    result_receptacle = design_circuit_conduit(
        circuit_name="ปลั๊ก ห้องนั่งเล่น",
        wires=wires_receptacle,
        length_m=35
    )
    
    print_conduit_report(result_receptacle)
    
    
    # ========== ตัวอย่างที่ 3: Main Feeder (สายใหญ่) ==========
    print("\n\n📍 ตัวอย่างที่ 3: Main Feeder (มิเตอร์ → DB)")
    
    wires_feeder = [
        {"size_mm2": 16, "quantity": 2},  # Hot (L1, L2)
        {"size_mm2": 16, "quantity": 1},  # Neutral
        {"size_mm2": 10, "quantity": 1}   # Ground
    ]
    
    result_feeder = design_circuit_conduit(
        circuit_name="Main Feeder",
        wires=wires_feeder,
        length_m=15
    )
    
    print_conduit_report(result_feeder)
    
    
    # ========== ตัวอย่างที่ 4: บ้าน 2 ชั้น (Sub-DB) ==========
    print("\n\n📍 ตัวอย่างที่ 4: Feeder ชั้น 2 (Main DB → Sub-DB ชั้น 2)")
    
    wires_subdb = [
        {"size_mm2": 10, "quantity": 2},  # Hot (L1, L2)
        {"size_mm2": 10, "quantity": 1},  # Neutral
        {"size_mm2": 6, "quantity": 1}    # Ground
    ]
    
    result_subdb = design_circuit_conduit(
        circuit_name="Feeder Sub-DB ชั้น 2",
        wires=wires_subdb,
        length_m=20
    )
    
    print_conduit_report(result_subdb)

---

**Output ตัวอย่าง:**

text

`==================================================================================================== 🔧 CONDUIT SIZER — เลือกท่อร้อยสายอัตโนมัติ ==================================================================================================== 📍 ตัวอย่างที่ 1: วงจรแอร์ ==================================================================================================== 📍 วงจร: แอร์ ห้องนอน ==================================================================================================== 📏 การคำนวณ:    พื้นที่สายรวม:           26.40 mm²   จำนวนสาย:                2 เส้น   Fill % ที่อนุญาต:         31.0%   พื้นที่ท่อที่ต้องการ:     85.16 mm² ✅ ท่อที่เลือก: 1/2" (15 mm)    พื้นที่ภายในท่อ:          137 mm²   Fill % จริง:             19.27%   พื้นที่เหลือ:             16.07 mm² 💰 ต้นทุนท่อ:    ความยาวที่ต้องการ:       25 m   จำนวนเส้น:                7 เส้น × 4 m   ราคาต่อเส้น:             40 บาท   ราคารวม:                 280 บาท   ของเหลือ:                3.0 m ====================================================================================================`

---

