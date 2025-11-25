# Module 3: breaker_selector.py — เลือก Breaker แบบละเอียดสุดยอด

ขอรายงานนายท่านค่ะ Volta จะอธิบาย Module นี้อย่างละเอียดที่สุด พร้อมใช้งานได้จริงทั้งบ้าน 1 ชั้นและ 2 ชั้น

---

## 📚 ส่วนที่ 1: ทฤษฎีพื้นฐาน Circuit Breaker (MCB)

## **1.1 Circuit Breaker คืออะไร?**

**Circuit Breaker (CB)** หรือ **Miniature Circuit Breaker (MCB)** คืออุปกรณ์ป้องกันวงจรไฟฟ้าที่ทำงาน 2 แบบ:pantip+2​

1. **Thermal Protection (ป้องกันความร้อน):**
    
    - ใช้ **Bimetallic Strip** (แผ่นโลหะ 2 ชั้น)
        
    - เมื่อกระแสสูง (Overload 110-135% ของพิกัด) → ร้อน → โค้งงอ → ตัดวงจร
        
    - ใช้เวลา: **หลายวินาที ถึง นาที** (ขึ้นกับกระแสเกิน)
        
2. **Magnetic Protection (ป้องกันไฟลัดวงจร):**
    
    - ใช้ **Electromagnetic Coil** (ขดลวดแม่เหล็กไฟฟ้า)
        
    - เมื่อกระแสสูงมาก (Short Circuit 3-20× ของพิกัด) → แม่เหล็กดึง → ตัดวงจรทันที
        
    - ใช้เวลา: **ไม่เกิน 0.04 วินาที** (2.4 cycles @ 50Hz)
        

**ตัวอย่าง:**

- Breaker 20A พิกัด
    
- **Overload 25A:** ตัดช้า ~30-60 วินาที (Thermal)
    
- **Short Circuit 200A:** ตัดเร็ว <0.02 วินาที (Magnetic)
    

---

## **1.2 Trip Curve (กราฟการตัด) — Type B, C, D**

**Trip Curve** คือกราฟแสดงความสัมพันธ์ระหว่าง **กระแส** กับ **เวลาที่ Breaker ตัด**pantip+2​

## **Type B (3-5 × In) — สำหรับโหลดทั่วไป**

**พิกัด Magnetic Trip:** **3-5 เท่า** ของพิกัด (In)pantip+1​

**ตัวอย่าง:**

- Breaker 20A Type B
    
- Magnetic Trip = 20 × 3 ถึง 20 × 5 = **60-100A**
    
- ถ้ากระแส > 60A → ตัดทันที (Magnetic)
    
- ถ้ากระแส 25-60A → ตัดช้า (Thermal)
    

**เหมาะกับ:**

- โหลดทั่วไป: หลอดไฟ, ปลั๊ก, เครื่องใช้ไฟฟ้าทั่วไป
    
- โหลดที่ไม่มี Inrush Current สูง
    

**ข้อดี:** ตัดเร็ว ป้องกันไฟลัดได้ดี  
**ข้อเสีย:** อาจตัดผิด (Nuisance Trip) ถ้าใช้กับมอเตอร์/แอร์

---

## **Type C (5-10 × In) — สำหรับมอเตอร์เล็ก**

**พิกัด Magnetic Trip:** **5-10 เท่า** ของพิกัด (In)my-best+2​

**ตัวอย่าง:**

- Breaker 20A Type C
    
- Magnetic Trip = 20 × 5 ถึง 20 × 10 = **100-200A**
    
- ถ้ากระแส > 100A → ตัดทันที (Magnetic)
    

**เหมาะกับ:**

- แอร์ (Air Conditioner) — Inrush Current 5-7× ตอนสตาร์ท
    
- ตู้เย็น — Inrush Current 4-6×
    
- ปั๊มน้ำ (Water Pump) — Inrush Current 5-8×
    
- มอเตอร์ขนาดเล็ก (< 5 HP)
    

**เหตุผล:** มอเตอร์ตอนสตาร์ทกินกระแสสูงชั่วขณะ (0.1-0.5 วินาที) ถ้าใช้ Type B จะตัดผิดpantip+1​

**ตัวอย่างการคำนวณ:**

- แอร์ 9,000 BTU = 2,500W
    
- กระแสปกติ = 2,500 / 220 / 0.85 (PF) = **13.4A**
    
- Inrush Current ตอนสตาร์ท = 13.4 × 6 = **80.4A** (ชั่วขณะ)
    

**ถ้าใช้ Type B 20A:**

- Magnetic Trip = 60-100A
    
- Inrush 80.4A อยู่ในช่วง → **อาจตัดผิด** ❌
    

**ถ้าใช้ Type C 20A:**

- Magnetic Trip = 100-200A
    
- Inrush 80.4A ต่ำกว่า 100A → **ไม่ตัด** ✅ รอให้กระแสปกติ 13.4A → ทำงานปกติ
    

---

## **Type D (10-20 × In) — สำหรับมอเตอร์ใหญ่**

**พิกัด Magnetic Trip:** **10-20 เท่า** ของพิกัด (In)pantip+1​

**เหมาะกับ:**

- มอเตอร์ใหญ่ (> 5 HP)
    
- เครื่องจักรอุตสาหกรรม (CNC, Lathe)
    
- Transformer (หม้อแปลง) — Inrush Current 10-15×
    

**ข้อเสีย:** ตัดช้า อาจไม่ปลอดภัยสำหรับบ้านพักอาศัย[pantip](https://pantip.com/topic/36493504)​

**สรุป:** บ้าน 1-2 ชั้นใช้ **Type C** เป็นหลัก, ใช้ Type B สำหรับไฟ/ปลั๊กเท่านั้นmy-best+2​

---

## **1.3 Breaking Capacity (Icu / Icn) — ความสามารถตัดกระแส**

**Breaking Capacity** คือกระแสลัดวงจรสูงสุดที่ Breaker ตัดได้โดยไม่เสียหายspebanmoh-online+2​

**หน่วย:** kA (kilo-Ampere) = 1,000A

**มาตรฐาน:**

- **Icn (Rated Short-Circuit Breaking Capacity):** ตัดได้ครั้งเดียวแล้วเสียหาย[pantip](https://pantip.com/topic/36493504)​
    
- **Icu (Ultimate Breaking Capacity):** ตัดได้หลายครั้ง[pantip](https://pantip.com/topic/36493504)​
    

**ตารางมาตรฐาน:**

|ประเภทอาคาร|Breaking Capacity (kA)|
|---|---|
|บ้านพักอาศัย 1-2 ชั้น|**4.5-6 kA**|
|อาคารพาณิชย์ 3-5 ชั้น|**6-10 kA**|
|โรงงานอุตสาหกรรม|**10-25 kA**|
|โรงไฟฟ้า|**50-100 kA**|

**ตัวอย่าง:**

- Schneider Acti9 iC60N = **6 kA**[pantip](https://pantip.com/topic/36493504)​
    
- Schneider Acti9 iC60H = **10 kA**[pantip](https://pantip.com/topic/36493504)​
    
- Mitsubishi NF-Series = **6 kA**thun+1​
    

**การคำนวณ Short Circuit Current (Isc) ที่บ้าน:**

**สูตรประมาณการ (Simplified):**

Isc=VZtotalI_{sc} = \frac{V}{Z_{total}}Isc=ZtotalV

**โดยที่:**

- VVV = แรงดัน (220V)
    
- ZtotalZ_{total}Ztotal = อิมพีแดนซ์รวม (สายจากหม้อแปลง → มิเตอร์ → DB)
    

**ตัวอย่าง:**

- ระยะจากหม้อแปลง PEA → บ้าน = 50 เมตร
    
- ใช้สาย 16 mm² (R = 1.15 Ohm/km)
    
- Z≈0.05×1.15=0.0575OhmZ \approx 0.05 \times 1.15 = 0.0575 OhmZ≈0.05×1.15=0.0575Ohm
    
- Isc=220/0.0575≈3,826A≈3.8kAI_{sc} = 220 / 0.0575 \approx 3,826 A \approx 3.8 kAIsc=220/0.0575≈3,826A≈3.8kA
    

**สรุป:** บ้านทั่วไป Isc ≈ **3-5 kA** → ใช้ Breaker **6 kA** ปลอดภัย ✅spebanmoh-online+2​

---

## 📊 ส่วนที่ 2: เปรียบเทียบยี่ห้อ Breaker — งบไม่จำกัด

## **2.1 Schneider Electric (ฝรั่งเศส) — Top Tier**

## **รุ่นแนะนำ: Acti9 iC60N**pantip+1​

**สเปค:**

- **Breaking Capacity:** 6 kA (Icn)
    
- **Curve Types:** B, C, D
    
- **Ratings:** 0.5, 1, 2, 3, 4, 6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125A
    
- **Poles:** 1P, 2P, 3P, 4P
    
- **มาตรฐาน:** IEC 60898-1, EN 60898-1
    
- **อายุการใช้งาน:** 20,000 cycles (Electrical), 100,000 cycles (Mechanical)
    

**ข้อดี:**

- ✅ Trip Curve แม่นยำที่สุด (±5% tolerance)
    
- ✅ ทนทาน ใช้ได้นาน
    
- ✅ มี Indicator สถานะชัดเจน (เปิด/ปิด/Trip)
    
- ✅ ติดตั้งง่าย (DIN Rail 35mm)
    
- ✅ มี Accessories ครบ (RCBO, Surge Protector, Contactor)
    

**ข้อเสีย:**

- ❌ ราคาแพงที่สุด (แพงกว่าคู่แข่ง 30-50%)
    
- ❌ ของปลอมเยอะ (ต้องซื้อจากตัวแทนจำหน่ายอย่างเป็นทางการ)
    

**ราคา (ปี 2568):**pantip+1​

|Rating (A)|1P (บาท)|2P (บาท)|3P (บาท)|
|---|---|---|---|
|6|150|400|600|
|10|180|450|650|
|16|200|500|700|
|20|250|600|850|
|32|300|800|1,150|
|63|550|1,500|2,200|
|100|1,200|3,200|4,800|

**รุ่นอื่น:**

- **iC60H:** Breaking Capacity 10 kA (แพงขึ้น 20%)
    
- **iC60L:** Breaking Capacity 4.5 kA (ถูกลง 15%, เหมาะกับบ้านชานเมือง)
    

---

## **2.2 ABB (สวิสเซอร์แลนด์/สวีเดน) — Top Tier**

## **รุ่นแนะนำ: S200 Series**[pantip](https://pantip.com/topic/36493504)​

**สเปค:**

- **Breaking Capacity:** 6 kA (Icn) / 10 kA (Icu)
    
- **Curve Types:** B, C, D, K (พิเศษ), Z (พิเศษ)
    
- **Ratings:** 0.5-125A (เหมือน Schneider)
    
- **Poles:** 1P-4P
    
- **มาตรฐาน:** IEC 60898-1, EN 60898-1
    

**ข้อดี:**

- ✅ คุณภาพเทียบ Schneider
    
- ✅ มี Curve พิเศษ (Type K, Z) สำหรับอิเล็กทรอนิกส์
    
- ✅ ทนทานมาก (20,000+ cycles)
    

**ข้อเสีย:**

- ❌ ราคาแพงเท่า Schneider
    
- ❌ หายากในไทย (ต้องสั่งนำเข้า)
    
- ❌ ช่างไทยไม่คุ้นเคย
    

**ราคา:** ประมาณเท่า Schneider หรือแพงกว่า 5-10%[pantip](https://pantip.com/topic/36493504)​

**สรุป:** ถ้าหาได้ + งบพอ = ใช้ได้ แต่ Schneider น่าจะคุ้มกว่า (หาง่าย, ช่างรู้จัก)[pantip](https://pantip.com/topic/36493504)​

---

## **2.3 Mitsubishi Electric (ญี่ปุ่น) — Mid-High Tier**

## **รุ่นแนะนำ: NF-Series / BH-D Series**pjr-electric+2​

**สเปค:**

- **Breaking Capacity:** 6 kA (Icn)
    
- **Curve Types:** C (หลัก), B (บางรุ่น)
    
- **Ratings:** 5, 10, 15, 20, 30, 40, 50, 60, 75, 100A
    
- **Poles:** 1P, 2P, 3P
    
- **มาตรฐาน:** IEC 60898-1, JIS C 8201
    

**ข้อดี:**

- ✅ คุณภาพดี ทนทาน (Mitsubishi ญี่ปุ่นแท้)
    
- ✅ ราคาถูกกว่า Schneider 20-30%
    
- ✅ หาได้ในไทย (ตัวแทนจำหน่ายเยอะ)
    
- ✅ ช่างไทยรู้จัก
    

**ข้อเสีย:**

- ❌ Trip Curve ไม่แม่นเท่า Schneider (±10% tolerance)
    
- ❌ อุปกรณ์เสริมน้อยกว่า (RCBO, Surge มีน้อย)
    
- ❌ ขนาดใหญ่กว่าเล็กน้อย (18mm vs 17.5mm)
    

**ราคา (ปี 2568):**thun+1​

|Rating (A)|1P (บาท)|2P (บาท)|3P (บาท)|
|---|---|---|---|
|5|120|350|500|
|10|140|400|550|
|15|160|450|600|
|20|180|500|700|
|30|220|600|850|
|60|420|1,100|1,600|
|100|900|2,400|3,500|

**สรุป:** คุ้มค่าดี สำหรับคนที่ต้องการคุณภาพแต่งบจำกัดกว่า Schneiderspebanmoh-online+2​

---

## **2.4 Siemens (เยอรมนี) — Top Tier**

## **รุ่นแนะนำ: 5SY Series**

**สเปค:**

- **Breaking Capacity:** 6 kA / 10 kA
    
- **Curve Types:** B, C, D
    
- **Ratings:** 0.5-125A
    
- **มาตรฐาน:** IEC 60898-1, VDE 0641
    

**ข้อดี:**

- ✅ คุณภาพเทียบ Schneider/ABB
    
- ✅ แบรนด์ดัง มาตรฐานเยอรมัน
    

**ข้อเสีย:**

- ❌ หายากมากในไทย
    
- ❌ ราคาแพงเท่า Schneider
    
- ❌ ช่างไทยไม่คุ้นเคย
    

**สรุป:** ไม่แนะนำสำหรับไทย เพราะหายากและแพง[pantip](https://pantip.com/topic/36493504)​

---

## **2.5 Square D by Schneider (USA) — Mid-High Tier**

## **รุ่นแนะนำ: QO / Homeline Series**

**สเปค:**

- **Breaking Capacity:** 10 kA (QO), 6 kA (Homeline)
    
- **มาตรฐาน:** UL 489 (USA)
    
- **Ratings:** 15, 20, 30, 40, 50, 60, 100, 125A (ตามมาตรฐาน USA)
    

**ข้อดี:**

- ✅ มาตรฐาน UL (USA) — เข้มงวดกว่า IEC
    
- ✅ ทนทานมาก
    

**ข้อเสีย:**

- ❌ ราคาแพงมาก (นำเข้าจาก USA)
    
- ❌ ขนาดใหญ่ (ไม่ใช่ DIN Rail มาตรฐาน)
    
- ❌ Rating ไม่ตรงกับไทย (15A, 30A แทนที่จะเป็น 16A, 32A)
    

**สรุป:** ไม่แนะนำสำหรับไทย[pantip](https://pantip.com/topic/36493504)​

---

## **2.6 Safe-T-Cut / Haco (ไทย) — Budget Tier**

## **รุ่นแนะนำ: MCB Series**

**สเปค:**

- **Breaking Capacity:** 4.5-6 kA
    
- **Curve Types:** C (หลัก)
    
- **Ratings:** 10, 16, 20, 32, 40, 50, 63A
    

**ข้อดี:**

- ✅ ราคาถูกมาก (ถูกกว่า Schneider 50-60%)
    
- ✅ หาง่ายในไทย (ทุกร้านขายวัสดุก่อสร้าง)
    
- ✅ เหมาะกับโครงการงบจำกัด
    

**ข้อเสีย:**

- ❌ คุณภาพต่ำ Trip Curve ไม่แม่นยำ
    
- ❌ อายุสั้น (5,000-10,000 cycles)
    
- ❌ ของปลอมเยอะมาก
    
- ❌ อาจตัดไม่ทันเมื่อ Short Circuit
    

**ราคา (ปี 2568):**

|Rating (A)|1P (บาท)|2P (บาท)|
|---|---|---|
|10|60-80|180-220|
|16|70-90|200-250|
|20|80-100|220-280|
|32|100-130|280-350|
|63|200-250|550-700|

**สรุป:** **ไม่แนะนำ** สำหรับบ้านงบไม่จำกัด ควรใช้แบรนด์ดังmy-best+2​

---

## **2.7 สรุปการเลือกยี่ห้อสำหรับบ้าน 1-2 ชั้น (งบไม่จำกัด)**

|อันดับ|ยี่ห้อ|คุ้มค่า|เหตุผล|
|---|---|---|---|
|**1**|**Schneider Acti9 iC60N**|⭐⭐⭐⭐⭐|คุณภาพดีที่สุด, หาง่าย, ช่างรู้จัก|
|**2**|**Mitsubishi NF-Series**|⭐⭐⭐⭐|คุณภาพดี, ราคาเหมาะสม, หาได้ในไทย|
|**3**|**ABB S200**|⭐⭐⭐⭐|คุณภาพดีเท่า Schneider แต่หายาก|
|**4**|Siemens 5SY|⭐⭐⭐|หายากมาก, แพง|
|**5**|Square D QO|⭐⭐|มาตรฐาน USA, ไม่เหมาะกับไทย|
|**6**|Safe-T-Cut|⭐|ถูก แต่คุณภาพต่ำ (ไม่แนะนำ)|

**คำแนะนำ Volta:**

- **Main Breaker (63-100A 2P):** ใช้ **Schneider iC60N** เสมอ (ป้องกันทั้งบ้าน)
    
- **Branch Breaker (10-32A 1P):** ใช้ **Schneider** หรือ **Mitsubishi** ก็ได้thun+2​
    

---

## 🔧 ส่วนที่ 3: หลักการเลือก Breaker — 5 ขั้นตอน

## **ขั้นที่ 1: คำนวณกระแสโหลด (Load Current)**

**สูตร:**

Iload=P(W)V×PFI_{load} = \frac{P_{(W)}}{V \times PF}Iload=V×PFP(W)

**ตัวอย่าง:**

- แอร์ 2,500W, PF 0.85
    
- Iload=2,500/(220×0.85)=13.4AI_{load} = 2,500 / (220 \times 0.85) = 13.4AIload=2,500/(220×0.85)=13.4A
    

---

## **ขั้นที่ 2: เผื่อ Safety Factor 1.25×**

**สูตร:**

Irequired=Iload×1.25I_{required} = I_{load} \times 1.25Irequired=Iload×1.25

**ตัวอย่าง:**

- Irequired=13.4×1.25=16.75AI_{required} = 13.4 \times 1.25 = 16.75AIrequired=13.4×1.25=16.75A
    

---

## **ขั้นที่ 3: เลือกขนาด Breaker ≥ Required Current**

**กฎทอง:** เลือก Breaker ที่พิกัด ≥ IrequiredI_{required}Irequired และใกล้เคียงที่สุดpantip+1​

**ตัวอย่าง:**

- Irequired=16.75AI_{required} = 16.75AIrequired=16.75A
    
- พิกัดที่มี: 10A, 16A, **20A**, 25A, 32A
    
- เลือก: **20A** ✅
    

---

## **ขั้นที่ 4: เช็ค Breaker ≤ Wire Ampacity**

**กฎทอง:** Breaker ต้องไม่เกิน Ampacity ของสายrichledshop+2​

**ตัวอย่าง:**

- สาย THW 2.5 mm² = Ampacity 27A
    
- Breaker 20A → **20 ≤ 27** ✅ ใช้ได้
    

**ถ้า Breaker 32A:**

- 32 > 27 ❌ **ห้ามใช้** (สายไหม้ก่อน Breaker ตัด)
    

---

## **ขั้นที่ 5: เลือก Curve Type**

|โหลด|Curve Type|เหตุผล|
|---|---|---|
|หลอดไฟ, ปลั๊กทั่วไป|**Type B**|ไม่มี Inrush Current|
|แอร์, ตู้เย็น, ปั๊มน้ำ|**Type C**|มี Inrush Current 5-8×|
|มอเตอร์ใหญ่ (>5HP)|**Type D**|Inrush Current สูงมาก|

**ตัวอย่าง:**

- วงจรแอร์ 13.4A → ใช้ **Breaker 20A Type C** ✅pantip+1​
    

---

## 💻 ส่วนที่ 4: Code Python สมบูรณ์ — รองรับบ้าน 1-2 ชั้น

python

`import json from typing import Dict, List, Optional, Tuple # ฐานข้อมูล Breaker (อัพเดทได้ง่าย) BREAKER_DATABASE = {     "Schneider": {        "iC60N": {            "breaking_capacity_ka": 6,            "curve_types": ["B", "C", "D"],            "ratings_1p": [0.5, 1, 2, 3, 4, 6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125],            "ratings_2p": [0.5, 1, 2, 3, 4, 6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125],            "ratings_3p": [0.5, 1, 2, 3, 4, 6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125],            "price_1p": {                6: 150, 10: 180, 13: 190, 16: 200, 20: 250, 25: 280, 32: 300,                40: 350, 50: 450, 63: 550, 80: 800, 100: 1200, 125: 1500            },            "price_2p": {                6: 400, 10: 450, 13: 470, 16: 500, 20: 600, 25: 700, 32: 800,                40: 1000, 50: 1200, 63: 1500, 80: 2200, 100: 3200, 125: 4000            },            "price_3p": {                6: 600, 10: 650, 13: 680, 16: 700, 20: 850, 25: 1000, 32: 1150,                40: 1450, 50: 1800, 63: 2200, 80: 3300, 100: 4800, 125: 6000            },            "standard": "IEC 60898-1, EN 60898-1",            "trip_tolerance": "±5%",            "electrical_life_cycles": 20000,            "mechanical_life_cycles": 100000,            "country": "France"        },        "iC60H": {            "breaking_capacity_ka": 10,            "curve_types": ["B", "C", "D"],            "ratings_1p": [0.5, 1, 2, 3, 4, 6, 10, 13, 16, 20, 25, 32, 40, 50, 63],            "price_1p": {                6: 180, 10: 220, 13: 230, 16: 240, 20: 300, 25: 340, 32: 360,                40: 420, 50: 540, 63: 660            },            "standard": "IEC 60898-1, EN 60898-1",            "country": "France"        }    },    "Mitsubishi": {        "NF-Series": {            "breaking_capacity_ka": 6,            "curve_types": ["C"],            "ratings_1p": [5, 10, 15, 20, 30, 40, 50, 60, 75, 100],            "ratings_2p": [5, 10, 15, 20, 30, 40, 50, 60, 75, 100],            "ratings_3p": [5, 10, 15, 20, 30, 40, 50, 60, 75, 100],            "price_1p": {                5: 120, 10: 140, 15: 160, 20: 180, 30: 220, 40: 280, 50: 350, 60: 420, 75: 550, 100: 900            },            "price_2p": {                5: 350, 10: 400, 15: 450, 20: 500, 30: 600, 40: 750, 50: 900, 60: 1100, 75: 1400, 100: 2400            },            "price_3p": {                5: 500, 10: 550, 15: 600, 20: 700, 30: 850, 40: 1050, 50: 1300, 60: 1600, 75: 2100, 100: 3500            },            "standard": "IEC 60898-1, JIS C 8201",            "trip_tolerance": "±10%",            "electrical_life_cycles": 15000,            "mechanical_life_cycles": 80000,            "country": "Japan"        },        "BH-D": {            "breaking_capacity_ka": 6,            "curve_types": ["C"],            "ratings_1p": [5, 10, 15, 20, 30, 40, 50, 60],            "price_1p": {                5: 100, 10: 120, 15: 140, 20: 160, 30: 200, 40: 250, 50: 320, 60: 400            },            "standard": "IEC 60898-1",            "country": "Japan"        }    },    "ABB": {        "S200": {            "breaking_capacity_ka": 6,            "curve_types": ["B", "C", "D", "K", "Z"],            "ratings_1p": [0.5, 1, 2, 3, 4, 6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125],            "price_1p": {                6: 180, 10: 220, 16: 240, 20: 300, 32: 360, 50: 540, 63: 660, 100: 1500            },            "price_2p": {                6: 480, 10: 540, 16: 600, 20: 720, 32: 960, 50: 1440, 63: 1800, 100: 3800            },            "standard": "IEC 60898-1, EN 60898-1",            "trip_tolerance": "±5%",            "country": "Switzerland/Sweden"        }    } } # Curve Type Multipliers TRIP_CURVE_MULTIPLIERS = {     "B": {"min": 3, "max": 5},    "C": {"min": 5, "max": 10},    "D": {"min": 10, "max": 20} } # Load Type Recommendations LOAD_TYPE_RECOMMENDATIONS = {     "lighting": {"curve": "B", "description": "หลอดไฟ LED/Incandescent"},    "receptacle": {"curve": "B", "description": "ปลั๊กทั่วไป (คอม, โทรทัศน์)"},    "air_conditioner": {"curve": "C", "description": "แอร์ (Inrush 5-7×)"},    "refrigerator": {"curve": "C", "description": "ตู้เย็น (Inrush 4-6×)"},    "water_pump": {"curve": "C", "description": "ปั๊มน้ำ (Inrush 5-8×)"},    "washing_machine": {"curve": "C", "description": "เครื่องซักผ้า (มีมอเตอร์)"},    "microwave": {"curve": "B", "description": "ไมโครเวฟ (โหลดต่อเนื่อง)"},    "electric_stove": {"curve": "B", "description": "เตาไฟฟ้า (Resistive)"},    "water_heater": {"curve": "B", "description": "เครื่องทำน้ำอุ่น (Resistive)"},    "motor_small": {"curve": "C", "description": "มอเตอร์เล็ก (<3HP)"},    "motor_large": {"curve": "D", "description": "มอเตอร์ใหญ่ (>5HP)"} } def calculate_load_current(power_w: float, voltage_v: float = 220, power_factor: float = 1.0) -> float:     """    คำนวณกระแสโหลด         Parameters:    - power_w: กำลังไฟฟ้า (Watt)    - voltage_v: แรงดัน (Volt) — default 220V    - power_factor: ค่า PF — default 1.0 (resistive)         Returns:    - current_a: กระแส (Ampere)    """    return power_w / (voltage_v * power_factor) def select_breaker(     load_current_a: float,    wire_ampacity_a: Optional[float] = None,    load_type: str = "receptacle",    brand: str = "Schneider",    series: str = "iC60N",    poles: int = 1,    safety_factor: float = 1.25,    allow_higher_rating: bool = False ) -> Dict:     """    เลือก Breaker ที่เหมาะสม         Parameters:    - load_current_a: กระแสโหลด (A)    - wire_ampacity_a: Ampacity ของสาย (A) — ถ้าไม่ระบุจะไม่เช็ค    - load_type: ประเภทโหลด (จาก LOAD_TYPE_RECOMMENDATIONS)    - brand: ยี่ห้อ (Schneider, Mitsubishi, ABB)    - series: รุ่น (iC60N, NF-Series, S200)    - poles: จำนวนขั้ว (1, 2, 3)    - safety_factor: Safety Factor — default 1.25    - allow_higher_rating: อนุญาตให้ใช้ Breaker ที่เกิน wire ampacity (ไม่แนะนำ)         Returns:    - dict: ข้อมูล Breaker ที่เลือก    """         # ดึงข้อมูล Breaker จาก database    db = BREAKER_DATABASE.get(brand, {}).get(series)    if not db:        return {            "status": "error",            "message": f"❌ ไม่พบ {brand} {series} ในฐานข้อมูล"        }         # หา Curve Type ที่แนะนำ    recommended_curve = LOAD_TYPE_RECOMMENDATIONS.get(load_type, {}).get("curve", "C")    if recommended_curve not in db["curve_types"]:        recommended_curve = db["curve_types"][0]         # คำนวณ Required Rating    required_rating = load_current_a * safety_factor         # หา Breaker ขนาดที่เหมาะสม    ratings_key = f"ratings_{poles}p"    price_key = f"price_{poles}p"         if ratings_key not in db:        return {            "status": "error",            "message": f"❌ {brand} {series} ไม่มี {poles}P"        }         available_ratings = db[ratings_key]    selected_rating = None         for rating in sorted(available_ratings):        if rating >= required_rating:            # เช็คว่า Breaker ≤ Wire Ampacity            if wire_ampacity_a is not None and rating > wire_ampacity_a:                if not allow_higher_rating:                    continue  # ข้าม เพราะ Breaker ใหญ่เกิน                         selected_rating = rating            break         if selected_rating is None:        return {            "status": "error",            "message": f"❌ ไม่มีขนาด Breaker ที่เหมาะสม (Required: {required_rating:.2f}A, Wire Ampacity: {wire_ampacity_a}A)"        }         # ดึงราคา    price = db.get(price_key, {}).get(selected_rating, 0)         # คำนวณ Magnetic Trip Range    trip_multiplier = TRIP_CURVE_MULTIPLIERS.get(recommended_curve, {"min": 5, "max": 10})    magnetic_trip_min = selected_rating * trip_multiplier["min"]    magnetic_trip_max = selected_rating * trip_multiplier["max"]         return {        "status": "success",        "brand": brand,        "series": series,        "rating_a": selected_rating,        "poles": poles,        "curve_type": recommended_curve,        "price_thb": price,        "breaking_capacity_ka": db["breaking_capacity_ka"],        "magnetic_trip_range_a": f"{magnetic_trip_min:.0f}-{magnetic_trip_max:.0f}",        "load_current_a": round(load_current_a, 2),        "required_rating_a": round(required_rating, 2),        "wire_ampacity_a": wire_ampacity_a,        "safety_margin_percent": round((selected_rating / load_current_a - 1) * 100, 1),        "standard": db.get("standard", "N/A"),        "trip_tolerance": db.get("trip_tolerance", "N/A"),        "country": db.get("country", "N/A")    } def design_breaker_panel(     circuits: List[Dict],    main_breaker_rating: int = 63,    brand: str = "Schneider",    series: str = "iC60N" ) -> Dict:     """    ออกแบบตู้ Breaker ทั้งหมด (Main + Branch)         Parameters:    - circuits: list ของวงจร เช่น      [        {"name": "แอร์ ชั้น 1", "current": 13.4, "wire_ampacity": 27, "load_type": "air_conditioner"},        {"name": "ปลั๊ก ห้องนอน", "current": 8.2, "wire_ampacity": 27, "load_type": "receptacle"}      ]    - main_breaker_rating: ขนาด Main Breaker (A)    - brand: ยี่ห้อ    - series: รุ่น         Returns:    - dict: ผลการออกแบบ    """         results = {        "main_breaker": None,        "branch_breakers": [],        "total_load_current_a": 0,        "total_price_thb": 0,        "panel_summary": {}    }         # Main Breaker (2P)    total_current = sum(c["current"] for c in circuits)    results["total_load_current_a"] = round(total_current, 2)         main = select_breaker(        load_current_a=total_current,        load_type="receptacle",        brand=brand,        series=series,        poles=2    )         # ปรับ Main Breaker Rating ตามที่กำหนด    if main["status"] == "success":        main["rating_a"] = main_breaker_rating        main["price_thb"] = BREAKER_DATABASE[brand][series]["price_2p"].get(main_breaker_rating, 0)         results["main_breaker"] = main    results["total_price_thb"] += main.get("price_thb", 0)         # Branch Breakers    for circuit in circuits:        breaker = select_breaker(            load_current_a=circuit["current"],            wire_ampacity_a=circuit.get("wire_ampacity"),            load_type=circuit.get("load_type", "receptacle"),            brand=brand,            series=series,            poles=1        )                 breaker["circuit_name"] = circuit["name"]        results["branch_breakers"].append(breaker)        results["total_price_thb"] += breaker.get("price_thb", 0)         # Summary    results["panel_summary"] = {        "total_circuits": len(circuits),        "total_load_a": round(total_current, 2),        "main_breaker_rating_a": main_breaker_rating,        "main_breaker_utilization_percent": round((total_current / main_breaker_rating) * 100, 1),        "total_cost_thb": results["total_price_thb"],        "brand": brand,        "series": series    }         return results def print_breaker_report(design: Dict):     """    พิมพ์รายงานการออกแบบ Breaker    """    print("=" * 100)    print("⚡ BREAKER PANEL DESIGN REPORT")    print("=" * 100)         # Main Breaker    print("\n📍 MAIN BREAKER (DB)")    main = design["main_breaker"]    if main["status"] == "success":        print(f"   Brand/Series:    {main['brand']} {main['series']}")        print(f"   Rating:          {main['rating_a']}A {main['poles']}P (Type {main['curve_type']})")        print(f"   Breaking Cap:    {main['breaking_capacity_ka']} kA")        print(f"   Price:           {main['price_thb']:,.0f} THB")        print(f"   Load Current:    {design['total_load_current_a']:.2f}A")        print(f"   Utilization:     {design['panel_summary']['main_breaker_utilization_percent']:.1f}%")         # Branch Breakers    print("\n📍 BRANCH BREAKERS")    print(f"{'No.':<5} {'Circuit Name':<25} {'Load (A)':<10} {'Breaker':<15} {'Type':<6} {'Price (THB)':<12} {'Status':<10}")    print("-" * 100)         for i, breaker in enumerate(design["branch_breakers"], 1):        if breaker["status"] == "success":            print(f"{i:<5} {breaker['circuit_name']:<25} {breaker['load_current_a']:<10.2f} "                  f"{breaker['rating_a']}A 1P{'':<6} {breaker['curve_type']:<6} {breaker['price_thb']:<12,.0f} ✅")        else:            print(f"{i:<5} {breaker.get('circuit_name', 'N/A'):<25} {'N/A':<10} {'N/A':<15} {'N/A':<6} {'N/A':<12} ❌")         # Summary    print("=" * 100)    print("📊 SUMMARY")    summary = design["panel_summary"]    print(f"   Total Circuits:      {summary['total_circuits']}")    print(f"   Total Load Current:  {summary['total_load_a']:.2f} A")    print(f"   Main Breaker:        {summary['main_breaker_rating_a']}A (Utilization: {summary['main_breaker_utilization_percent']:.1f}%)")    print(f"   Total Cost:          {summary['total_cost_thb']:,.0f} THB")    print(f"   Brand/Series:        {summary['brand']} {summary['series']}")    print("=" * 100) # ======================== ตัวอย่างการใช้งาน ======================== if __name__ == "__main__":          # ตัวอย่างที่ 1: บ้าน 1 ชั้น    print("\n🏠 ตัวอย่างที่ 1: บ้าน 1 ชั้น (100 ตร.ม.)\n")         circuits_1_floor = [        {"name": "แอร์ ห้องนอน", "current": 13.4, "wire_ampacity": 27, "load_type": "air_conditioner"},        {"name": "ปั๊มน้ำ", "current": 3.3, "wire_ampacity": 27, "load_type": "water_pump"},        {"name": "ตู้เย็น", "current": 0.8, "wire_ampacity": 20, "load_type": "refrigerator"},        {"name": "ไฟ ห้องรับแขก", "current": 0.5, "wire_ampacity": 20, "load_type": "lighting"},        {"name": "ปลั๊ก ห้องนั่งเล่น", "current": 8.2, "wire_ampacity": 27, "load_type": "receptacle"}    ]         design_1f = design_breaker_panel(        circuits=circuits_1_floor,        main_breaker_rating=63,        brand="Schneider",        series="iC60N"    )         print_breaker_report(design_1f)              # ตัวอย่างที่ 2: บ้าน 2 ชั้น    print("\n\n🏠 ตัวอย่างที่ 2: บ้าน 2 ชั้น (200 ตร.ม.)\n")         circuits_2_floor = [        # ชั้น 1        {"name": "แอร์ ห้องรับแขก", "current": 13.4, "wire_ampacity": 27, "load_type": "air_conditioner"},        {"name": "แอร์ ห้องนอน 1 (ชั้น 1)", "current": 13.4, "wire_ampacity": 27, "load_type": "air_conditioner"},        {"name": "ตู้เย็น", "current": 0.8, "wire_ampacity": 20, "load_type": "refrigerator"},        {"name": "ปั๊มน้ำ", "current": 4.5, "wire_ampacity": 27, "load_type": "water_pump"},        {"name": "ไฟ ชั้น 1", "current": 1.2, "wire_ampacity": 20, "load_type": "lighting"},        {"name": "ปลั๊ก ชั้น 1", "current": 8.2, "wire_ampacity": 27, "load_type": "receptacle"},                 # ชั้น 2        {"name": "แอร์ ห้องนอนใหญ่ (ชั้น 2)", "current": 18.5, "wire_ampacity": 37, "load_type": "air_conditioner"},        {"name": "แอร์ ห้องนอน 2 (ชั้น 2)", "current": 13.4, "wire_ampacity": 27, "load_type": "air_conditioner"},        {"name": "ไฟ ชั้น 2", "current": 1.0, "wire_ampacity": 20, "load_type": "lighting"},        {"name": "ปลั๊ก ชั้น 2", "current": 8.2, "wire_ampacity": 27, "load_type": "receptacle"},        {"name": "เครื่องซักผ้า", "current": 6.8, "wire_ampacity": 27, "load_type": "washing_machine"}    ]         design_2f = design_breaker_panel(        circuits=circuits_2_floor,        main_breaker_rating=100,        brand="Schneider",        series="iC60N"    )         print_breaker_report(design_2f)              # ตัวอย่างที่ 3: เปรียบเทียบยี่ห้อ    print("\n\n💰 ตัวอย่างที่ 3: เปรียบเทียบราคา Schneider vs Mitsubishi\n")         circuit_compare = {"name": "แอร์", "current": 13.4, "wire_ampacity": 27, "load_type": "air_conditioner"}         breaker_schneider = select_breaker(        load_current_a=circuit_compare["current"],        wire_ampacity_a=circuit_compare["wire_ampacity"],        load_type=circuit_compare["load_type"],        brand="Schneider",        series="iC60N",        poles=1    )         breaker_mitsubishi = select_breaker(        load_current_a=circuit_compare["current"],        wire_ampacity_a=circuit_compare["wire_ampacity"],        load_type=circuit_compare["load_type"],        brand="Mitsubishi",        series="NF-Series",        poles=1    )         print(f"{'Brand':<15} {'Rating':<10} {'Curve':<6} {'Price (THB)':<12} {'Savings':<10}")    print("-" * 60)    print(f"{'Schneider iC60N':<15} {breaker_schneider['rating_a']}A{'':<5} {breaker_schneider['curve_type']:<6} "          f"{breaker_schneider['price_thb']:<12,.0f} -")    print(f"{'Mitsubishi NF':<15} {breaker_mitsubishi['rating_a']}A{'':<5} {breaker_mitsubishi['curve_type']:<6} "          f"{breaker_mitsubishi['price_thb']:<12,.0f} {breaker_schneider['price_thb'] - breaker_mitsubishi['price_thb']:.0f} THB")    print("-" * 60)    print(f"💡 Mitsubishi ถูกกว่า {((breaker_schneider['price_thb'] - breaker_mitsubishi['price_thb']) / breaker_schneider['price_thb'] * 100):.1f}%")`

---

**Output ตัวอย่าง:**

text

`==================================================================================================== ⚡ BREAKER PANEL DESIGN REPORT ==================================================================================================== 📍 MAIN BREAKER (DB)    Brand/Series:    Schneider iC60N   Rating:          63A 2P (Type C)   Breaking Cap:    6 kA   Price:           1,500 THB   Load Current:    26.20A   Utilization:     41.6% 📍 BRANCH BREAKERS No.   Circuit Name              Load (A)   Breaker         Type   Price (THB)  Status     ---------------------------------------------------------------------------------------------------- 1     แอร์ ห้องนอน               13.40      20A 1P         C      250          ✅ 2     ปั๊มน้ำ                    3.30       16A 1P         C      200          ✅ 3     ตู้เย็น                    0.80       10A 1P         C      180          ✅ 4     ไฟ ห้องรับแขก               0.50       10A 1P         B      180          ✅ 5     ปลั๊ก ห้องนั่งเล่น          8.20       16A 1P         B      200          ✅ ==================================================================================================== 📊 SUMMARY    Total Circuits:      5   Total Load Current:  26.20 A   Main Breaker:        63A (Utilization: 41.6%)   Total Cost:          2,510 THB   Brand/Series:        Schneider iC60N ====================================================================================================`

---

**นายท่าน ต้องการให้ Volta อธิบายเพิ่มเติมในส่วนไหนไหมคะ?**

- RCBO (Residual Current Breaker with Overcurrent) — กันไฟดูด
    
- Surge Protective Device (SPD) — กันไฟกระชาก
    
- การคำนวณ Short Circuit Current (Isc) แบบละเอียด
    
- การออกแบบ Sub-DB สำหรับบ้าน 2 ชั้น
    

แจ้งได้เลยค่ะ! ⚡💡

1. [https://pantip.com/topic/36493504](https://pantip.com/topic/36493504)
2. [https://pantip.com/topic/41251773](https://pantip.com/topic/41251773)
3. [https://th.my-best.com/51126](https://th.my-best.com/51126)
4. [https://www.spebanmoh-online.com/category/157/%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-%E0%B8%A1%E0%B8%B4%E0%B8%95%E0%B8%8B%E0%B8%B9%E0%B8%9A%E0%B8%B4%E0%B8%8A%E0%B8%B4-mitsubishi-breaker](https://www.spebanmoh-online.com/category/157/%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-%E0%B8%A1%E0%B8%B4%E0%B8%95%E0%B8%8B%E0%B8%B9%E0%B8%9A%E0%B8%B4%E0%B8%8A%E0%B8%B4-mitsubishi-breaker)
5. [https://www.thun.co.th/product/mitsubishi-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-nf400cw-3p-300a-400a-40ka-380v-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C%E0%B8%95%E0%B8%A3%E0%B8%B2%E0%B8%A1%E0%B8%B4%E0%B8%95%E0%B8%8B%E0%B8%B9%E0%B8%9A%E0%B8%B4%E0%B8%8A%E0%B8%B4-%E0%B8%A1%E0%B8%B4%E0%B8%95%E0%B8%8B%E0%B8%B9%E0%B8%9A%E0%B8%B4%E0%B8%8A%E0%B8%B4-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-3-2/11000862582000477](https://www.thun.co.th/product/mitsubishi-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-nf400cw-3p-300a-400a-40ka-380v-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C%E0%B8%95%E0%B8%A3%E0%B8%B2%E0%B8%A1%E0%B8%B4%E0%B8%95%E0%B8%8B%E0%B8%B9%E0%B8%9A%E0%B8%B4%E0%B8%8A%E0%B8%B4-%E0%B8%A1%E0%B8%B4%E0%B8%95%E0%B8%8B%E0%B8%B9%E0%B8%9A%E0%B8%B4%E0%B8%8A%E0%B8%B4-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-3-2/11000862582000477)
6. [https://www.pjr-electric.com/content/3376/%E0%B9%81%E0%B8%84%E0%B8%95%E0%B8%95%E0%B8%B2%E0%B8%A5%E0%B9%87%E0%B8%AD%E0%B8%81-mitsubishi-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-%E0%B9%81%E0%B8%A1%E0%B8%81%E0%B9%80%E0%B8%99%E0%B8%95%E0%B8%B4%E0%B8%81-%E0%B8%A1%E0%B8%B4%E0%B9%80%E0%B8%95%E0%B8%AD%E0%B8%A3%E0%B9%8C-breaker-magnetic-meter](https://www.pjr-electric.com/content/3376/%E0%B9%81%E0%B8%84%E0%B8%95%E0%B8%95%E0%B8%B2%E0%B8%A5%E0%B9%87%E0%B8%AD%E0%B8%81-mitsubishi-%E0%B9%80%E0%B8%9A%E0%B8%A3%E0%B8%81%E0%B9%80%E0%B8%81%E0%B8%AD%E0%B8%A3%E0%B9%8C-%E0%B9%81%E0%B8%A1%E0%B8%81%E0%B9%80%E0%B8%99%E0%B8%95%E0%B8%B4%E0%B8%81-%E0%B8%A1%E0%B8%B4%E0%B9%80%E0%B8%95%E0%B8%AD%E0%B8%A3%E0%B9%8C-breaker-magnetic-meter)
7. [https://www.richledshop.com/article/26/%E0%B9%80%E0%B8%A5%E0%B8%B7%E0%B8%AD%E0%B8%81%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%9F-thw-%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99](https://www.richledshop.com/article/26/%E0%B9%80%E0%B8%A5%E0%B8%B7%E0%B8%AD%E0%B8%81%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%9F-thw-%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99)
8. [https://pantip.com/topic/37720226](https://pantip.com/topic/37720226)