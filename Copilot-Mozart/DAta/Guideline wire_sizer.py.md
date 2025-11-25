# Module 2: wire_sizer.py — เลือกขนาดสาย + Voltage Drop Check (ฉบับสมบูรณ์)

ขอรายงานนายท่านค่ะ Volta จะอธิบาย Module 2 อย่างละเอียดที่สุด พร้อม Code ครบถ้วน

---

## 📚 ส่วนที่ 1: ทฤษฎีเชิงลึก Wire Sizing

## **1.1 ปัจจัย 3 ประการในการเลือกสาย**

การเลือกขนาดสายไฟต้องพิจารณา **3 ปัจจัยหลัก** พร้อมกัน:thaiyazaki+4​

## **A. Ampacity (ความสามารถรับกระแส)**

**คำนิยาม:** กระแสไฟฟ้าสูงสุดที่สายรับได้โดยไม่ร้อนเกิน (ไม่เกินอุณหภูมิที่ฉนวนทนได้)richledshop+2​

**กฎทอง NEC 310.15:**

text

`Wire Ampacity ≥ Load Current × 1.25 (Continuous Load)`

**อุณหภูมิฉนวนสาย:**

- **TW (Thermoplastic Wet):** 60°C — ไม่แนะนำแล้ว
    
- **THW (Thermoplastic Heat & Water):** **75°C** — มาตรฐานไทย
    
- **THHN/THWN:** 90°C — ใช้ในอุตสาหกรรม
    

**ตารางละเอียด Ampacity สาย THW (ทองแดง, 75°C) ตาม มอก. 11-2553:**pantip+3​

|ขนาดสาย (mm²)|AWG Equivalent|หน้าตัดจริง (mm²)|Conductor Dia. (mm)|Insulation Thickness (mm)|Outer Dia. OD (mm)|Ampacity ในท่อ @ 30°C (A)|Ampacity ลอย @ 30°C (A)|Ampacity ในท่อ @ 40°C (A)|Resistance @ 20°C (Ω/km)|Resistance @ 75°C (Ω/km)|
|---|---|---|---|---|---|---|---|---|---|---|
|**1.5**|15-16|1.5|1.38|1.0|3.4|**20**|25|18|12.1|14.5|
|**2.5**|13-14|2.5|1.78|1.15|4.1|**27**|35|24|7.41|8.90|
|**4**|11-12|4.0|2.26|1.30|4.9|**37**|50|33|4.61|5.53|
|**6**|10|6.0|2.76|1.50|5.8|**48**|65|43|3.08|3.70|
|**10**|8|10.0|3.57|2.00|7.6|**50**|70|45|1.83|2.20|
|**16**|6|16.0|4.52|2.40|9.3|**68**|95|61|1.15|1.38|
|**25**|4|25.0|5.64|3.40|12.5|**89**|119|80|0.727|0.872|
|**35**|2|35.0|6.68|3.90|14.5|**111**|148|100|0.524|0.629|
|**50**|1|50.0|7.98|4.50|17.0|**134**|179|121|0.387|0.464|
|**70**|1/0|70.0|9.45|5.30|20.0|**171**|229|154|0.268|0.322|
|**95**|2/0|95.0|11.0|6.00|23.0|**207**|277|186|0.193|0.232|
|**120**|3/0|120.0|12.4|6.50|25.4|**239**|319|215|0.153|0.184|
|**150**|4/0|150.0|13.8|7.00|27.8|**272**|364|245|0.124|0.149|
|**185**|250 kcmil|185.0|15.4|7.50|30.4|**314**|420|283|0.0991|0.119|

**หมายเหตุสำคัญ:**

- **Ampacity @ 30°C:** ใช้สำหรับที่ติดแอร์ (ภายในอาคาร)
    
- **Ampacity @ 40°C:** ใช้สำหรับนอกอาคาร (แดดร้อน)
    
- **Resistance @ 75°C:** ใช้คำนวณ Voltage Drop เพราะสายร้อนจริง ๆbangkokcable+2​
    

---

## **B. Voltage Drop (VD) — การตกของแรงดัน**

**คำนิยาม:** ความแตกต่างแรงดันระหว่างจุดต้นทาง (DB) กับจุดปลายทาง (โหลด)scribd+3​

**สูตรพื้นฐาน (AC Single Phase, 220V):**bangkokcable+3​

VD(Volt)=2×L×I×R×cos⁡θ+2×L×I×X×sin⁡θ1000VD_{(Volt)} = \frac{2 \times L \times I \times R \times \cos\theta + 2 \times L \times I \times X \times \sin\theta}{1000}VD(Volt)=10002×L×I×R×cosθ+2×L×I×X×sinθ

**ในทางปฏิบัติ (Resistive/Low Inductive Load):**

VD(Volt)=2×L×I×R1000VD_{(Volt)} = \frac{2 \times L \times I \times R}{1000}VD(Volt)=10002×L×I×R VD(%)=VD(Volt)Vsystem×100VD_{(\%)} = \frac{VD_{(Volt)}}{V_{system}} \times 100VD(%)=VsystemVD(Volt)×100

**โดยที่:**

- 2×2 \times2× = สายไป-กลับ (Hot + Neutral)
    
- LLL = ความยาวสาย (เมตร) — **one-way distance**
    
- III = กระแสโหลด (Ampere)
    
- RRR = ความต้านทาน @ 75°C (Ω/km)
    
- XXX = Reactance (Ω/km) — มักละเลยได้สำหรับสายขนาดเล็ก
    
- cos⁡θ\cos\thetacosθ = Power Factor
    
- VsystemV_{system}Vsystem = แรงดันระบบ (220V)
    

**สูตรสำหรับ Three Phase (380V):**thaiyazaki+1​

VD(Volt)=3×L×I×R1000VD_{(Volt)} = \frac{\sqrt{3} \times L \times I \times R}{1000}VD(Volt)=10003×L×I×R VD(%)=VD(Volt)380×100VD_{(\%)} = \frac{VD_{(Volt)}}{380} \times 100VD(%)=380VD(Volt)×100

---

**มาตรฐาน Voltage Drop:**pea+3​

|ประเภทวงจร|VD สูงสุด (%)|มาตรฐาน|
|---|---|---|
|**Branch Circuit**|**3%**|NEC 210.19(A), มอก. 2955|
|**Feeder**|**3%**|NEC 215.2|
|**Feeder + Branch รวม**|**5%**|NEC 215.2(A)(3)|
|**มอเตอร์ตอนสตาร์ท**|**15%** (ชั่วขณะ)|NEC 430.24|

**เหตุผล VD ต้องต่ำ:**bangkokcable+1​

1. **แอร์:** VD > 5% → คอมเพรสเซอร์สตาร์ทไม่ติด → เบรกเกอร์ตัด
    
2. **หลอดไฟ:** VD > 3% → สลัว, กะพริบ
    
3. **มอเตอร์:** VD สูง → Torque ลด, ร้อนเกิน, อายุสั้น
    
4. **อุปกรณ์อิเล็กทรอนิกส์:** VD สูง → ทำงานผิดปกติ, เสียหาย
    

---

## **C. Short Circuit Protection (การป้องกันไฟลัดวงจร)**

**หลักการ:** สายต้องทนกระแส Short Circuit ได้โดยไม่ไหม้ก่อน Breaker ตัดrichledshop+1​

**สูตรหน้าตัดสายขั้นต่ำ (Adiabatic Equation):**[richledshop](https://www.richledshop.com/article/26/%E0%B9%80%E0%B8%A5%E0%B8%B7%E0%B8%AD%E0%B8%81%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%9F-thw-%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99)​

Amin=Isc×tKA_{min} = \frac{I_{sc} \times \sqrt{t}}{K}Amin=KIsc×t

**โดยที่:**

- AminA_{min}Amin = หน้าตัดสายขั้นต่ำ (mm²)
    
- IscI_{sc}Isc = Short Circuit Current (A)
    
- ttt = เวลาที่ Breaker ตัด (วินาที) — มักใช้ 0.1-5 วินาที
    
- KKK = ค่าคงที่ของวัสดุ
    
    - **ทองแดง (Copper) THW 75°C:** K = 115
        
    - **อลูมิเนียม (Aluminum) 75°C:** K = 76
        

**ตัวอย่างการคำนวณ:**

โจทย์: Short Circuit Current = 3,000A, Breaker ตัดใน 0.2 วินาที

python

`A_min = (3000 × √0.2) / 115 A_min = (3000 × 0.447) / 115 A_min = 1,341 / 115 A_min = 11.66 mm²`

**สรุป:** ต้องใช้สายอย่างน้อย **16 mm²** ขึ้นไป ✅

---

## **1.2 Derating Factor (ปัจจัยลดค่า Ampacity)**

**Ampacity ในตารางมาตรฐานอิงที่:**engfanatic.tumcivil+2​

- อุณหภูมิโดยรอบ (Ambient) = **30°C**
    
- จำนวนสายในท่อ = **≤ 3 เส้น**
    

**ถ้าเงื่อนไขเปลี่ยนต้อง Derate:**

## **A. Temperature Correction Factor**

**ตารางตาม NEC Table 310.15(B)(2)(a):**pantip+1​

|อุณหภูมิโดยรอบ (°C)|Correction Factor (สาย 75°C)|
|---|---|
|**≤ 30°C**|1.00|
|**31-35°C**|0.94|
|**36-40°C**|0.88|
|**41-45°C**|0.82|
|**46-50°C**|0.75|
|**51-55°C**|0.67|
|**56-60°C**|0.58|
|**61-70°C**|0.33|

**ตัวอย่าง:**

- สาย THW 2.5 mm² = Ampacity 27A @ 30°C
    
- ติดตั้งที่หลังคา (อุณหภูมิ 45°C)
    
- **Derated Ampacity = 27 × 0.82 = 22.14A**
    

---

## **B. Conductor Bundling Adjustment Factor**

**ตารางตาม NEC Table 310.15(B)(3)(a):**engfanatic.tumcivil+2​

|จำนวนสายใน Conduit (Conductors)|Adjustment Factor|
|---|---|
|**1-3**|1.00|
|**4-6**|0.80|
|**7-9**|0.70|
|**10-20**|0.50|
|**21-30**|0.45|
|**31-40**|0.40|
|**41+**|0.35|

**หมายเหตุ:** นับเฉพาะสาย **Hot + Neutral** ไม่นับ **Ground**[engfanatic.tumcivil](https://engfanatic.tumcivil.com/engfanatic/article/335-%E0%B8%88%E0%B8%B3%E0%B8%99%E0%B8%A7%E0%B8%99%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B8%AA%E0%B8%B9%E0%B8%87%E0%B8%AA%E0%B8%B8%E0%B8%94%E0%B9%83%E0%B8%99%E0%B8%97%E0%B9%88%E0%B8%AD%E0%B8%A3%E0%B9%89%E0%B8%AD%E0%B8%A2%E0%B8%AA%E0%B8%B2%E0%B8%A2)​

**ตัวอย่าง:**

- ท่อ 1 เส้นมีสาย 6 เส้น (3 Hot + 3 Neutral)
    
- สาย THW 2.5 mm² = 27A @ 30°C
    
- **Derated Ampacity = 27 × 0.80 = 21.6A**
    

---

## **C. Combined Derating**

**สูตรรวม:**

Ampacityderated=Ampacitybase×Temperature Factor×Bundling FactorAmpacity_{derated} = Ampacity_{base} \times Temperature\ Factor \times Bundling\ FactorAmpacityderated=Ampacitybase×Temperature Factor×Bundling Factor

**ตัวอย่าง:**

- สาย THW 4 mm² = 37A (base)
    
- ติดตั้งนอกอาคาร (40°C) → Temp Factor = 0.88
    
- มีสาย 5 เส้นในท่อ → Bundling Factor = 0.80
    
- **Ampacity = 37 × 0.88 × 0.80 = 26.05A**
    

---

## **1.3 การคำนวณ Voltage Drop แบบละเอียด (พิจารณา Power Factor)**

**สูตรเต็ม (กรณี Inductive Load เช่น มอเตอร์/แอร์):**scribd+2​

VD(Volt)=I×[R×cos⁡θ+X×sin⁡θ]×2L1000VD_{(Volt)} = I \times \left[ R \times \cos\theta + X \times \sin\theta \right] \times \frac{2L}{1000}VD(Volt)=I×[R×cosθ+X×sinθ]×10002L

**โดยที่:**

- RRR = Resistance (Ω/km)
    
- XXX = Reactance (Ω/km) — ประมาณ 0.1-0.2 Ω/km สำหรับสายขนาดเล็ก
    
- cos⁡θ\cos\thetacosθ = Power Factor
    
- sin⁡θ=1−cos⁡2θ\sin\theta = \sqrt{1 - \cos^2\theta}sinθ=1−cos2θ
    

**ตัวอย่าง:**

โจทย์: แอร์ 13.4A, PF 0.85, สาย THW 2.5 mm², ระยะ 30m

python

`# ค่าคงที่ R = 8.90  # Ω/km @ 75°C X = 0.15  # Ω/km (ประมาณการ) PF = 0.85 cos_theta = 0.85 sin_theta = sqrt(1 - 0.85²) = sqrt(0.2775) = 0.527 # คำนวณ VD VD_volt = 13.4 × [(8.90 × 0.85) + (0.15 × 0.527)] × (2 × 30 / 1000) VD_volt = 13.4 × [7.565 + 0.079] × 0.06 VD_volt = 13.4 × 7.644 × 0.06 VD_volt = 6.14 Volt VD_percent = (6.14 / 220) × 100 = 2.79%`

**สรุป:** VD = 2.79% < 3% ✅ **ใช้ได้**

---

## **1.4 สูตรคำนวณระยะทางสูงสุด (Maximum Distance)**

**กลับสูตร VD เพื่อหาระยะสูงสุด:**thaiyazaki+1​

Lmax=VD(%)×Vsystem×10002×I×R×100L_{max} = \frac{VD_{(\%)} \times V_{system} \times 1000}{2 \times I \times R \times 100}Lmax=2×I×R×100VD(%)×Vsystem×1000

**ตัวอย่าง:**

โจทย์: ต้องการ VD ≤ 3%, กระแส 20A, สาย THW 2.5 mm²

python

`L_max = (3 × 220 × 1000) / (2 × 20 × 8.90 × 100) L_max = 660,000 / 35,600 L_max = 18.54 เมตร`

**สรุป:** สาย THW 2.5 mm² ที่กระแส 20A ใช้ได้ไกลสุด **18.5 เมตร** (ถ้าเกินต้องเพิ่มขนาด)bangkokcable+1​

---

## 💻 ส่วนที่ 2: Code Python สมบูรณ์ — wire_sizer.py

python

"""
wire_sizer.py
==============
โมดูลเลือกขนาดสายไฟ + ตรวจสอบ Voltage Drop

Features:
- คำนวณ Ampacity พร้อม Derating
- คำนวณ Voltage Drop (Single/Three Phase)
- คำนวณ Short Circuit Withstand
- แนะนำขนาดสายอัตโนมัติ
- พิจารณา Power Factor
- รองรับ Continuous/Non-Continuous Load
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

class WireType(Enum):
    """ประเภทสาย"""
    THW = "THW"  # Thermoplastic Heat & Water (75°C)
    THHN = "THHN"  # Thermoplastic High Heat Nylon (90°C)
    THWN = "THWN"  # Thermoplastic Heat & Water Nylon (75°C/90°C)
    NYY = "NYY"  # PVC Insulated Cable (70°C)


class ConductorMaterial(Enum):
    """วัสดุตัวนำ"""
    COPPER = "Copper"
    ALUMINUM = "Aluminum"


class InstallationMethod(Enum):
    """วิธีการติดตั้ง"""
    IN_CONDUIT = "in_conduit"
    FREE_AIR = "free_air"
    DIRECT_BURIED = "direct_buried"
    IN_CABLE_TRAY = "in_cable_tray"


class PhaseType(Enum):
    """ประเภทเฟส"""
    SINGLE_PHASE = "1P"
    THREE_PHASE = "3P"


# ======================== Wire Database ========================

WIRE_DATA_THW_COPPER = {
    # size_mm2: {properties}
    1.5: {
        "awg_equivalent": "15-16 AWG",
        "conductor_area_mm2": 1.5,
        "conductor_diameter_mm": 1.38,
        "insulation_thickness_mm": 1.0,
        "outer_diameter_mm": 3.4,
        "area_with_insulation_mm2": 9.1,
        "ampacity_in_conduit_30c": 20,
        "ampacity_free_air_30c": 25,
        "ampacity_in_conduit_40c": 18,
        "resistance_20c_ohm_per_km": 12.1,
        "resistance_75c_ohm_per_km": 14.5,
        "reactance_ohm_per_km": 0.12,
        "price_per_m_thb": 10
    },
    2.5: {
        "awg_equivalent": "13-14 AWG",
        "conductor_area_mm2": 2.5,
        "conductor_diameter_mm": 1.78,
        "insulation_thickness_mm": 1.15,
        "outer_diameter_mm": 4.1,
        "area_with_insulation_mm2": 13.2,
        "ampacity_in_conduit_30c": 27,
        "ampacity_free_air_30c": 35,
        "ampacity_in_conduit_40c": 24,
        "resistance_20c_ohm_per_km": 7.41,
        "resistance_75c_ohm_per_km": 8.90,
        "reactance_ohm_per_km": 0.11,
        "price_per_m_thb": 18
    },
    4: {
        "awg_equivalent": "11-12 AWG",
        "conductor_area_mm2": 4.0,
        "conductor_diameter_mm": 2.26,
        "insulation_thickness_mm": 1.30,
        "outer_diameter_mm": 4.9,
        "area_with_insulation_mm2": 18.9,
        "ampacity_in_conduit_30c": 37,
        "ampacity_free_air_30c": 50,
        "ampacity_in_conduit_40c": 33,
        "resistance_20c_ohm_per_km": 4.61,
        "resistance_75c_ohm_per_km": 5.53,
        "reactance_ohm_per_km": 0.10,
        "price_per_m_thb": 28
    },
    6: {
        "awg_equivalent": "10 AWG",
        "conductor_area_mm2": 6.0,
        "conductor_diameter_mm": 2.76,
        "insulation_thickness_mm": 1.50,
        "outer_diameter_mm": 5.8,
        "area_with_insulation_mm2": 26.4,
        "ampacity_in_conduit_30c": 48,
        "ampacity_free_air_30c": 65,
        "ampacity_in_conduit_40c": 43,
        "resistance_20c_ohm_per_km": 3.08,
        "resistance_75c_ohm_per_km": 3.70,
        "reactance_ohm_per_km": 0.095,
        "price_per_m_thb": 45
    },
    10: {
        "awg_equivalent": "8 AWG",
        "conductor_area_mm2": 10.0,
        "conductor_diameter_mm": 3.57,
        "insulation_thickness_mm": 2.00,
        "outer_diameter_mm": 7.6,
        "area_with_insulation_mm2": 45.4,
        "ampacity_in_conduit_30c": 50,
        "ampacity_free_air_30c": 70,
        "ampacity_in_conduit_40c": 45,
        "resistance_20c_ohm_per_km": 1.83,
        "resistance_75c_ohm_per_km": 2.20,
        "reactance_ohm_per_km": 0.090,
        "price_per_m_thb": 75
    },
    16: {
        "awg_equivalent": "6 AWG",
        "conductor_area_mm2": 16.0,
        "conductor_diameter_mm": 4.52,
        "insulation_thickness_mm": 2.40,
        "outer_diameter_mm": 9.3,
        "area_with_insulation_mm2": 67.9,
        "ampacity_in_conduit_30c": 68,
        "ampacity_free_air_30c": 95,
        "ampacity_in_conduit_40c": 61,
        "resistance_20c_ohm_per_km": 1.15,
        "resistance_75c_ohm_per_km": 1.38,
        "reactance_ohm_per_km": 0.085,
        "price_per_m_thb": 120
    },
    25: {
        "awg_equivalent": "4 AWG",
        "conductor_area_mm2": 25.0,
        "conductor_diameter_mm": 5.64,
        "insulation_thickness_mm": 3.40,
        "outer_diameter_mm": 12.5,
        "area_with_insulation_mm2": 122.7,
        "ampacity_in_conduit_30c": 89,
        "ampacity_free_air_30c": 119,
        "ampacity_in_conduit_40c": 80,
        "resistance_20c_ohm_per_km": 0.727,
        "resistance_75c_ohm_per_km": 0.872,
        "reactance_ohm_per_km": 0.080,
        "price_per_m_thb": 200
    },
    35: {
        "awg_equivalent": "2 AWG",
        "conductor_area_mm2": 35.0,
        "conductor_diameter_mm": 6.68,
        "insulation_thickness_mm": 3.90,
        "outer_diameter_mm": 14.5,
        "area_with_insulation_mm2": 165.1,
        "ampacity_in_conduit_30c": 111,
        "ampacity_free_air_30c": 148,
        "ampacity_in_conduit_40c": 100,
        "resistance_20c_ohm_per_km": 0.524,
        "resistance_75c_ohm_per_km": 0.629,
        "reactance_ohm_per_km": 0.078,
        "price_per_m_thb": 280
    },
    50: {
        "awg_equivalent": "1 AWG",
        "conductor_area_mm2": 50.0,
        "conductor_diameter_mm": 7.98,
        "insulation_thickness_mm": 4.50,
        "outer_diameter_mm": 17.0,
        "area_with_insulation_mm2": 227.0,
        "ampacity_in_conduit_30c": 134,
        "ampacity_free_air_30c": 179,
        "ampacity_in_conduit_40c": 121,
        "resistance_20c_ohm_per_km": 0.387,
        "resistance_75c_ohm_per_km": 0.464,
        "reactance_ohm_per_km": 0.075,
        "price_per_m_thb": 380
    },
    70: {
        "awg_equivalent": "1/0 AWG",
        "conductor_area_mm2": 70.0,
        "conductor_diameter_mm": 9.45,
        "insulation_thickness_mm": 5.30,
        "outer_diameter_mm": 20.0,
        "area_with_insulation_mm2": 314.2,
        "ampacity_in_conduit_30c": 171,
        "ampacity_free_air_30c": 229,
        "ampacity_in_conduit_40c": 154,
        "resistance_20c_ohm_per_km": 0.268,
        "resistance_75c_ohm_per_km": 0.322,
        "reactance_ohm_per_km": 0.073,
        "price_per_m_thb": 520
    },
    95: {
        "awg_equivalent": "2/0 AWG",
        "conductor_area_mm2": 95.0,
        "conductor_diameter_mm": 11.0,
        "insulation_thickness_mm": 6.00,
        "outer_diameter_mm": 23.0,
        "area_with_insulation_mm2": 415.5,
        "ampacity_in_conduit_30c": 207,
        "ampacity_free_air_30c": 277,
        "ampacity_in_conduit_40c": 186,
        "resistance_20c_ohm_per_km": 0.193,
        "resistance_75c_ohm_per_km": 0.232,
        "reactance_ohm_per_km": 0.071,
        "price_per_m_thb": 700
    },
    120: {
        "awg_equivalent": "3/0 AWG",
        "conductor_area_mm2": 120.0,
        "conductor_diameter_mm": 12.4,
        "insulation_thickness_mm": 6.50,
        "outer_diameter_mm": 25.4,
        "area_with_insulation_mm2": 506.7,
        "ampacity_in_conduit_30c": 239,
        "ampacity_free_air_30c": 319,
        "ampacity_in_conduit_40c": 215,
        "resistance_20c_ohm_per_km": 0.153,
        "resistance_75c_ohm_per_km": 0.184,
        "reactance_ohm_per_km": 0.069,
        "price_per_m_thb": 900
    },
    150: {
        "awg_equivalent": "4/0 AWG",
        "conductor_area_mm2": 150.0,
        "conductor_diameter_mm": 13.8,
        "insulation_thickness_mm": 7.00,
        "outer_diameter_mm": 27.8,
        "area_with_insulation_mm2": 607.0,
        "ampacity_in_conduit_30c": 272,
        "ampacity_free_air_30c": 364,
        "ampacity_in_conduit_40c": 245,
        "resistance_20c_ohm_per_km": 0.124,
        "resistance_75c_ohm_per_km": 0.149,
        "reactance_ohm_per_km": 0.068,
        "price_per_m_thb": 1100
    },
    185: {
        "awg_equivalent": "250 kcmil",
        "conductor_area_mm2": 185.0,
        "conductor_diameter_mm": 15.4,
        "insulation_thickness_mm": 7.50,
        "outer_diameter_mm": 30.4,
        "area_with_insulation_mm2": 726.3,
        "ampacity_in_conduit_30c": 314,
        "ampacity_free_air_30c": 420,
        "ampacity_in_conduit_40c": 283,
        "resistance_20c_ohm_per_km": 0.0991,
        "resistance_75c_ohm_per_km": 0.119,
        "reactance_ohm_per_km": 0.067,
        "price_per_m_thb": 1400
    }
}

# Temperature Correction Factors (NEC Table 310.15(B)(2)(a))
TEMPERATURE_CORRECTION_FACTORS = {
    # ambient_temp_c: factor for 75°C wire
    25: 1.05,
    30: 1.00,
    31: 0.99,
    32: 0.97,
    33: 0.96,
    34: 0.95,
    35: 0.94,
    36: 0.92,
    37: 0.91,
    38: 0.90,
    39: 0.89,
    40: 0.88,
    41: 0.86,
    42: 0.85,
    43: 0.84,
    44: 0.83,
    45: 0.82,
    46: 0.80,
    47: 0.79,
    48: 0.77,
    49: 0.76,
    50: 0.75,
    55: 0.67,
    60: 0.58,
    65: 0.47,
    70: 0.33
}

# Conductor Bundling Adjustment Factors (NEC Table 310.15(B)(3)(a))
BUNDLING_ADJUSTMENT_FACTORS = {
    # num_current_carrying_conductors: factor
    1: 1.00,
    2: 1.00,
    3: 1.00,
    4: 0.80,
    5: 0.80,
    6: 0.80,
    7: 0.70,
    8: 0.70,
    9: 0.70,
    10: 0.50,
    15: 0.50,
    20: 0.50,
    21: 0.45,
    25: 0.45,
    30: 0.45,
    31: 0.40,
    35: 0.40,
    40: 0.40,
    41: 0.35
}

# Short Circuit Withstand Constants (K value)
SHORT_CIRCUIT_K_VALUES = {
    "Copper_75C": 115,
    "Copper_90C": 143,
    "Aluminum_75C": 76,
    "Aluminum_90C": 94
}


# ======================== Data Classes ========================

@dataclass
class WireSizingResult:
    """
    ผลการเลือกขนาดสาย
    """
    # Input Parameters
    load_current_a: float
    length_m: float
    voltage_v: float
    phase_type: PhaseType
    power_factor: float
    
    # Wire Selection
    selected_size_mm2: float
    wire_data: Dict
    
    # Ampacity Checking
    base_ampacity_a: float
    derated_ampacity_a: float
    temperature_factor: float
    bundling_factor: float
    required_ampacity_a: float
    ampacity_margin_percent: float
    ampacity_status: str  # "PASS" or "FAIL"
    
    # Voltage Drop Checking
    resistance_ohm_per_km: float
    reactance_ohm_per_km: float
    vd_volt: float
    vd_percent: float
    vd_limit_percent: float
    vd_status: str  # "PASS" or "FAIL"
    
    # Short Circuit Checking
    short_circuit_current_a: Optional[float] = None
    breaker_time_s: Optional[float] = None
    min_wire_size_sc_mm2: Optional[float] = None
    sc_status: Optional[str] = None
    
    # Cost
    wire_cost_per_m_thb: float = 0
    total_wire_cost_thb: float = 0
    
    # Overall Status
    overall_status: str = "PASS"
    recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """คำนวณค่าที่เหลือ"""
        self.total_wire_cost_thb = self.wire_cost_per_m_thb * self.length_m
        
        # Overall Status
        if self.ampacity_status == "FAIL" or self.vd_status == "FAIL":
            self.overall_status = "FAIL"
        elif self.sc_status == "FAIL":
            self.overall_status = "FAIL"


# ======================== Main Wire Sizer Class ========================

class WireSizer:
    """
    คลาสหลักสำหรับเลือกขนาดสาย
    """
    
    def __init__(
        self,
        wire_database: Dict = None,
        conductor_material: ConductorMaterial = ConductorMaterial.COPPER,
        wire_type: WireType = WireType.THW
    ):
        """
        Initialize Wire Sizer
        
        Parameters:
        - wire_database: ฐานข้อมูลสาย (default: WIRE_DATA_THW_COPPER)
        - conductor_material: วัสดุตัวนำ
        - wire_type: ประเภทสาย
        """
        self.wire_database = wire_database or WIRE_DATA_THW_COPPER
        self.conductor_material = conductor_material
        self.wire_type = wire_type
    
    def get_temperature_correction_factor(self, ambient_temp_c: float) -> float:
        """
        หา Temperature Correction Factor
        
        Parameters:
        - ambient_temp_c: อุณหภูมิโดยรอบ (°C)
        
        Returns:
        - correction_factor
        """
        # หาค่าใกล้เคียงที่สุด
        temps = sorted(TEMPERATURE_CORRECTION_FACTORS.keys())
        
        if ambient_temp_c <= temps[0]:
            return TEMPERATURE_CORRECTION_FACTORS[temps[0]]
        elif ambient_temp_c >= temps[-1]:
            return TEMPERATURE_CORRECTION_FACTORS[temps[-1]]
        else:
            # Linear interpolation
            for i in range(len(temps) - 1):
                if temps[i] <= ambient_temp_c <= temps[i+1]:
                    t1, t2 = temps[i], temps[i+1]
                    f1, f2 = TEMPERATURE_CORRECTION_FACTORS[t1], TEMPERATURE_CORRECTION_FACTORS[t2]
                    factor = f1 + (f2 - f1) * (ambient_temp_c - t1) / (t2 - t1)
                    return factor
        
        return 1.00
    
    def get_bundling_adjustment_factor(self, num_conductors: int) -> float:
        """
        หา Bundling Adjustment Factor
        
        Parameters:
        - num_conductors: จำนวนสายที่นำกระแส (ไม่รวม Ground)
        
        Returns:
        - adjustment_factor
        """
        conductors = sorted(BUNDLING_ADJUSTMENT_FACTORS.keys())
        
        if num_conductors <= 3:
            return 1.00
        
        for i in range(len(conductors)):
            if num_conductors <= conductors[i]:
                return BUNDLING_ADJUSTMENT_FACTORS[conductors[i]]
        
        return 0.35  # default สำหรับ > 40 เส้น
    
    def calculate_derated_ampacity(
        self,
        base_ampacity_a: float,
        ambient_temp_c: float = 30,
        num_conductors: int = 3
    ) -> Tuple[float, float, float]:
        """
        คำนวณ Ampacity หลัง Derate
        
        Returns:
        - (derated_ampacity, temp_factor, bundling_factor)
        """
        temp_factor = self.get_temperature_correction_factor(ambient_temp_c)
        bundling_factor = self.get_bundling_adjustment_factor(num_conductors)
        
        derated_ampacity = base_ampacity_a * temp_factor * bundling_factor
        
        return derated_ampacity, temp_factor, bundling_factor
    
    def calculate_voltage_drop(
        self,
        current_a: float,
        length_m: float,
        resistance_ohm_per_km: float,
        reactance_ohm_per_km: float,
        voltage_v: float,
        power_factor: float,
        phase_type: PhaseType
    ) -> Tuple[float, float]:
        """
        คำนวณ Voltage Drop
        
        Returns:
        - (vd_volt, vd_percent)
        """
        R = resistance_ohm_per_km
        X = reactance_ohm_per_km
        cos_theta = power_factor
        sin_theta = math.sqrt(1 - cos_theta**2) if cos_theta < 1.0 else 0.0
        
        if phase_type == PhaseType.SINGLE_PHASE:
            # VD = 2 × L × I × (R×cosθ + X×sinθ) / 1000
            vd_volt = (2 * length_m * current_a * (R * cos_theta + X * sin_theta)) / 1000
        else:  # THREE_PHASE
            # VD = √3 × L × I × (R×cosθ + X×sinθ) / 1000
            vd_volt = (math.sqrt(3) * length_m * current_a * (R * cos_theta + X * sin_theta)) / 1000
        
        vd_percent = (vd_volt / voltage_v) * 100
        
        return vd_volt, vd_percent
    
    def calculate_short_circuit_withstand(
        self,
        short_circuit_current_a: float,
        breaker_time_s: float
    ) -> float:
        """
        คำนวณหน้าตัดสายขั้นต่ำสำหรับทน Short Circuit
        
        Formula: A_min = (I_sc × √t) / K
        
        Returns:
        - min_wire_size_mm2
        """
        K = SHORT_CIRCUIT_K_VALUES["Copper_75C"]  # default
        
        A_min = (short_circuit_current_a * math.sqrt(breaker_time_s)) / K
        
        return A_min
    
    def select_wire_size(
        self,
        load_current_a: float,
        length_m: float,
        voltage_v: float = 220,
        phase_type: PhaseType = PhaseType.SINGLE_PHASE,
        power_factor: float = 1.0,
        is_continuous: bool = False,
        vd_limit_percent: float = 3.0,
        ambient_temp_c: float = 30,
        num_conductors: int = 3,
        installation_method: InstallationMethod = InstallationMethod.IN_CONDUIT,
        short_circuit_current_a: Optional[float] = None,
        breaker_time_s: float = 0.2,
        safety_factor: float = 1.25
    ) -> WireSizingResult:
        """
        เลือกขนาดสายอัตโนมัติ
        
        Parameters:
        - load_current_a: กระแสโหลด (A)
        - length_m: ความยาวสาย (เมตร) — one-way
        - voltage_v: แรงดันระบบ (V)
        - phase_type: 1P หรือ 3P
        - power_factor: ค่า PF
        - is_continuous: โหลดต่อเนื่อง (> 3 ชม.)
        - vd_limit_percent: Voltage Drop สูงสุด (%)
        - ambient_temp_c: อุณหภูมิโดยรอบ (°C)
        - num_conductors: จำนวนสายในท่อ
        - installation_method: วิธีติดตั้ง
        - short_circuit_current_a: กระแส Short Circuit (A)
        - breaker_time_s: เวลา Breaker ตัด (วินาที)
        - safety_factor: Safety Factor (default 1.25)
        
        Returns:
        - WireSizingResult
        """
        
        # คำนวณ Required Ampacity
        if is_continuous:
            required_ampacity = load_current_a * safety_factor
        else:
            required_ampacity = load_current_a * 1.0
        
        # คำนวณ Min Wire Size สำหรับ Short Circuit (ถ้ามี)
        min_wire_size_sc = None
        if short_circuit_current_a:
            min_wire_size_sc = self.calculate_short_circuit_withstand(
                short_circuit_current_a,
                breaker_time_s
            )
        
        # ลองเลือกสายตั้งแต่เล็กไปใหญ่
        for size_mm2 in sorted(self.wire_database.keys()):
            wire_data = self.wire_database[size_mm2]
            
            # เลือก Ampacity ตาม Installation Method
            if installation_method == InstallationMethod.IN_CONDUIT:
                if ambient_temp_c <= 30:
                    base_ampacity = wire_data["ampacity_in_conduit_30c"]
                else:
                    base_ampacity = wire_data["ampacity_in_conduit_40c"]
            else:  # FREE_AIR
                base_ampacity = wire_data["ampacity_free_air_30c"]
            
            # Derate Ampacity
            derated_ampacity, temp_factor, bundling_factor = self.calculate_derated_ampacity(
                base_ampacity,
                ambient_temp_c,
                num_conductors
            )
            
            # เช็ค Ampacity
            if derated_ampacity < required_ampacity:
                continue  # สายเล็กเกิน ลองขนาดใหญ่ขึ้น
            
            # เช็ค Short Circuit (ถ้ามี)
            if min_wire_size_sc and size_mm2 < min_wire_size_sc:
                continue  # ไม่ทน Short Circuit
            
            # เช็ค Voltage Drop
            R = wire_data["resistance_75c_ohm_per_km"]
            X = wire_data["reactance_ohm_per_km"]
            
            vd_volt, vd_percent = self.calculate_voltage_drop(
                load_current_a,
                length_m,
                R,
                X,
                voltage_v,
                power_factor,
                phase_type
            )
            
            if vd_percent > vd_limit_percent:
                continue  # VD เกิน ลองขนาดใหญ่ขึ้น
            
            # ✅ เจอขนาดที่ใช้ได้แล้ว
            ampacity_margin = ((derated_ampacity / load_current_a) - 1) * 100
            
            result = WireSizingResult(
                load_current_a=load_current_a,
                length_m=length_m,
                voltage_v=voltage_v,
                phase_type=phase_type,
                power_factor=power_factor,
                selected_size_mm2=size_mm2,
                wire_data=wire_data,
                base_ampacity_a=base_ampacity,
                derated_ampacity_a=derated_ampacity,
                temperature_factor=temp_factor,
                bundling_factor=bundling_factor,
                required_ampacity_a=required_ampacity,
                ampacity_margin_percent=ampacity_margin,
                ampacity_status="PASS",
                resistance_ohm_per_km=R,
                reactance_ohm_per_km=X,
                vd_volt=vd_volt,
                vd_percent=vd_percent,
                vd_limit_percent=vd_limit_percent,
                vd_status="PASS",
                short_circuit_current_a=short_circuit_current_a,
                breaker_time_s=breaker_time_s,
                min_wire_size_sc_mm2=min_wire_size_sc,
                sc_status="PASS" if min_wire_size_sc else None,
                wire_cost_per_m_thb=wire_data["price_per_m_thb"],
                overall_status="PASS"
            )
            
            # เพิ่ม Recommendations
            if ampacity_margin < 10:
                result.recommendations.append("⚠️ Ampacity Margin ต่ำ (< 10%) — พิจารณาเพิ่มขนาดสาย")
            
            if vd_percent > vd_limit_percent * 0.8:
                result.recommendations.append(f"⚠️ Voltage Drop ใกล้ขีดจำกัด ({vd_percent:.2f}% / {vd_limit_percent}%)")
            
            return result
        
        # ถ้าไม่เจอขนาดไหนเลย
        return WireSizingResult(
            load_current_a=load_current_a,
            length_m=length_m,
            voltage_v=voltage_v,
            phase_type=phase_type,
            power_factor=power_factor,
            selected_size_mm2=0,
            wire_data={},
            base_ampacity_a=0,
            derated_ampacity_a=0,
            temperature_factor=0,
            bundling_factor=0,
            required_ampacity_a=required_ampacity,
            ampacity_margin_percent=0,
            ampacity_status="FAIL",
            resistance_ohm_per_km=0,
            reactance_ohm_per_km=0,
            vd_volt=0,
            vd_percent=0,
            vd_limit_percent=vd_limit_percent,
            vd_status="FAIL",
            overall_status="FAIL",
            recommendations=["❌ ไม่พบขนาดสายที่เหมาะสม — ลดระยะทาง หรือแยกวงจร"]
        )
    
    def calculate_maximum_distance(
        self,
        wire_size_mm2: float,
        load_current_a: float,
        voltage_v: float = 220,
        vd_limit_percent: float = 3.0,
        power_factor: float = 1.0,
        phase_type: PhaseType = PhaseType.SINGLE_PHASE
    ) -> float:
        """
        คำนวณระยะทางสูงสุดที่ใช้สายได้
        
        Returns:
        - max_distance_m
        """
        if wire_size_mm2 not in self.wire_database:
            raise ValueError(f"❌ ไม่พบขนาดสาย {wire_size_mm2} mm²")
        
        wire_data = self.wire_database[wire_size_mm2]
        R = wire_data["resistance_75c_ohm_per_km"]
        X = wire_data["reactance_ohm_per_km"]
        
        cos_theta = power_factor
        sin_theta = math.sqrt(1 - cos_theta**2) if cos_theta < 1.0 else 0.0
        
        Z_effective = R * cos_theta + X * sin_theta
        
        vd_volt_limit = (vd_limit_percent / 100) * voltage_v
        
        if phase_type == PhaseType.SINGLE_PHASE:
            # VD = 2 × L × I × Z / 1000
            # L = VD × 1000 / (2 × I × Z)
            max_distance = (vd_volt_limit * 1000) / (2 * load_current_a * Z_effective)
        else:  # THREE_PHASE
            # L = VD × 1000 / (√3 × I × Z)
            max_distance = (vd_volt_limit * 1000) / (math.sqrt(3) * load_current_a * Z_effective)
        
        return max_distance


# ======================== Report Generator ========================

class WireSizingReportGenerator:
    """
    สร้างรายงานการเลือกสาย
    """
    
    @staticmethod
    def print_detailed_report(result: WireSizingResult):
        """
        พิมพ์รายงานแบบละเอียด
        """
        print("=" * 120)
        print("🔌 WIRE SIZING REPORT")
        print("=" * 120)
        
        print(f"\n📊 INPUT PARAMETERS")
        print(f"   Load Current:              {result.load_current_a:.2f} A")
        print(f"   Length (one-way):          {result.length_m} m")
        print(f"   Voltage:                   {result.voltage_v} V")
        print(f"   Phase:                     {result.phase_type.value}")
        print(f"   Power Factor:              {result.power_factor:.2f}")
        
        if result.overall_status == "FAIL":
            print(f"\n❌ STATUS: {result.overall_status}")
            for rec in result.recommendations:
                print(f"   {rec}")
            print("=" * 120)
            return
        
        print(f"\n✅ SELECTED WIRE: THW {result.selected_size_mm2} mm² ({result.wire_data['awg_equivalent']})")
        
        print(f"\n📏 AMPACITY CHECKING")
        print(f"   Base Ampacity:             {result.base_ampacity_a} A")
        print(f"   Temperature Factor:        {result.temperature_factor:.3f}")
        print(f"   Bundling Factor:           {result.bundling_factor:.3f}")
        print(f"   Derated Ampacity:          {result.derated_ampacity_a:.2f} A")
        print(f"   Required Ampacity:         {result.required_ampacity_a:.2f} A")
        print(f"   Margin:                    {result.ampacity_margin_percent:.1f}%")
        print(f"   Status:                    ✅ {result.ampacity_status}")
        
        print(f"\n⚡ VOLTAGE DROP CHECKING")
        print(f"   Resistance @ 75°C:         {result.resistance_ohm_per_km:.4f} Ω/km")
        print(f"   Reactance:                 {result.reactance_ohm_per_km:.4f} Ω/km")
        print(f"   Voltage Drop:              {result.vd_volt:.3f} V ({result.vd_percent:.2f}%)")
        print(f"   Limit:                     {result.vd_limit_percent}%")
        print(f"   Status:                    ✅ {result.vd_status}")
        
        if result.short_circuit_current_a:
            print(f"\n⚠️ SHORT CIRCUIT CHECKING")
            print(f"   Short Circuit Current:     {result.short_circuit_current_a:,.0f} A")
            print(f"   Breaker Time:              {result.breaker_time_s} s")
            print(f"   Min Wire Size (SC):        {result.min_wire_size_sc_mm2:.2f} mm²")
            print(f"   Selected Size:             {result.selected_size_mm2} mm²")
            print(f"   Status:                    ✅ {result.sc_status}")
        
        print(f"\n💰 COST ESTIMATION")
        print(f"   Price per meter:           {result.wire_cost_per_m_thb:.2f} THB/m")
        print(f"   Total Length:              {result.length_m} m")
        print(f"   Total Cost:                {result.total_wire_cost_thb:,.2f} THB")
        
        if result.recommendations:
            print(f"\n📌 RECOMMENDATIONS")
            for rec in result.recommendations:
                print(f"   {rec}")
        
        print("=" * 120)


# ======================== ตัวอย่างการใช้งาน ========================

if __name__ == "__main__":
    
    # สร้าง Wire Sizer
    sizer = WireSizer()
    
    # ========== ตัวอย่างที่ 1: วงจรแอร์ ==========
    print("\n📍 ตัวอย่างที่ 1: วงจรแอร์ 9,000 BTU\n")
    
    result_ac = sizer.select_wire_size(
        load_current_a=13.4,
        length_m=25,
        voltage_v=220,
        phase_type=PhaseType.SINGLE_PHASE,
        power_factor=0.85,
        is_continuous=True,
        vd_limit_percent=3.0,
        ambient_temp_c=35,
        num_conductors=2
    )
    
    WireSizingReportGenerator.print_detailed_report(result_ac)
    
    
    # ========== ตัวอย่างที่ 2: Main Feeder (บ้าน 2 ชั้น) ==========
    print("\n\n📍 ตัวอย่างที่ 2: Main Feeder (มิเตอร์ → Main DB)\n")
    
    result_feeder = sizer.select_wire_size(
        load_current_a=89.2,  # จาก Load Calculation
        length_m=15,
        voltage_v=220,
        phase_type=PhaseType.SINGLE_PHASE,
        power_factor=0.90,
        is_continuous=True,
        vd_limit_percent=2.0,  # Feeder ควรต่ำกว่า 2%
        ambient_temp_c=30,
        num_conductors=2,
        short_circuit_current_a=4000,
        breaker_time_s=0.2
    )
    
    WireSizingReportGenerator.print_detailed_report(result_feeder)
    
    
    # ========== ตัวอย่างที่ 3: คำนวณระยะสูงสุด ==========
    print("\n\n📍 ตัวอย่างที่ 3: คำนวณระยะทางสูงสุด (สาย THW 2.5 mm², กระแส 20A)\n")
    
    max_dist = sizer.calculate_maximum_distance(
        wire_size_mm2=2.5,
        load_current_a=20,
        voltage_v=220,
        vd_limit_percent=3.0,
        power_factor=1.0,
        phase_type=PhaseType.SINGLE_PHASE
    )
    
    print(f"✅ ระยะทางสูงสุด: {max_dist:.2f} เมตร (ที่ VD = 3%)")
    print("=" * 120)
    
    
    # ========== ตัวอย่างที่ 4: วงจรปลั๊ก (ระยะไกล) ==========
    print("\n\n📍 ตัวอย่างที่ 4: วงจรปลั๊กทั่วไป (ระยะ 50m)\n")
    
    result_receptacle = sizer.select_wire_size(
        load_current_a=8.2,
        length_m=50,
        voltage_v=220,
        phase_type=PhaseType.SINGLE_PHASE,
        power_factor=1.0,
        is_continuous=False,
        vd_limit_percent=3.0,
        ambient_temp_c=30,
        num_conductors=3  # Hot + Neutral + Ground
    )
    
    WireSizingReportGenerator.print_detailed_report(result_receptacle)
`

---

## 📋 สรุป Key Features ของ wire_sizer.py

## **✅ ฟีเจอร์ครบถ้วน:**

1. **Ampacity Calculation พร้อม Derating:**
    
    - Temperature Correction Factor
        
    - Bundling Adjustment Factor
        
    - รองรับ Continuous/Non-Continuous Load
        
2. **Voltage Drop Calculation:**
    
    - พิจารณา Power Factor
        
    - พิจารณา Reactance
        
    - รองรับ Single Phase + Three Phase
        
3. **Short Circuit Withstand:**
    
    - คำนวณขนาดสายขั้นต่ำที่ทน SC
        
    - ใช้ Adiabatic Equation
        
4. **Automatic Wire Selection:**
    
    - เลือกขนาดเล็กที่สุดที่ผ่านทุกเงื่อนไข
        
    - แจ้งเตือนถ้าใกล้ขีดจำกัด
        
5. **Maximum Distance Calculator:**
    
    - คำนวณกลับจาก VD → หาระยะสูงสุด
        
6. **Cost Estimation:**
    
    - คำนวณราคาอัตโนมัติ
        

---


    

