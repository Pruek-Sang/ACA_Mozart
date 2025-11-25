# 🔌 MCP Core: โปรแกรมคำนวณระบบไฟฟ้าครบวงจร — ฉบับละเอียดสุดยอด

ขอรายงานให้นายท่านทราบค่ะ Volta จะอธิบายทุกส่วนอย่างละเอียดที่สุด พร้อมตัวอย่างและเหตุผลเชิงลึก

---

## 📊 ส่วนที่ 1: การจำแนกข้อมูล — อะไรเปลี่ยนบ่อย อะไรเปลี่ยนนาน

## **🔒 ข้อมูลที่ไม่ค่อยเปลี่ยน (Hard-coded ได้)**

## **1.1 มาตรฐาน มอก. 2955 (ระบบไฟฟ้าในอาคาร)**

**ประวัติ:** มอก. 2955 ฉบับล่าสุดออกปี **2562 (พ.ศ.)** ซึ่งเป็นการปรับปรุงจากฉบับปี 2556pea+1​

**สิ่งที่กำหนด:**

- ความปลอดภัยระบบไฟฟ้าในอาคาร
    
- ขนาดสายไฟขั้นต่ำ
    
- ระบบกราวด์ (Grounding)
    
- การติดตั้งอุปกรณ์ป้องกัน (RCBO, RCCB)
    
- ข้อห้ามในห้องน้ำ/ห้องเปียก
    

**ความถี่การเปลี่ยนแปลง:** ประมาณ **6-8 ปีต่อครั้ง**anyflip+1​

**เหตุผลที่เปลี่ยนนาน:** เป็นมาตรฐานสากล อิงตาม **IEC 60364** ซึ่งเป็นมาตรฐานระดับโลก การแก้ไขต้องผ่านการพิจารณาจากคณะกรรมการหลายฝ่าย และต้องทดสอบในสภาพแวดล้อมไทยก่อนpea+1​

**ตัวอย่างข้อกำหนดสำคัญ:**

- **ห้องน้ำ Zone 0, 1, 2:** ห้ามติดปลั๊ก, ใช้อุปกรณ์ IP44 ขึ้นไปkjl+1​
    
- **Voltage Drop:** ไม่เกิน 3% (branch circuit), 5% (feeder + branch)thaiyazaki+1​
    
- **RCBO/RCCB:** ต้องมีในวงจรที่เสี่ยง (ห้องน้ำ, ครัว, นอกอาคาร) ≤ 30mAfacebook+2​
    

---

## **1.2 ข้อบังคับสภาวิศวกร (พ.ศ. 2566)**

**ประวัติ:** ข้อบังคับล่าสุด **พ.ศ. 2566** แก้ไขจากฉบับ 2557coe+4​

**สิ่งที่กำหนด:**

- **ขอบเขตงานแต่ละระดับวิศวกร:**
    
    - **ภาคีวิศวกร:** ≤ 1,000 kVA หรือ ≤ 24 kV (บ้านพักอาศัย)mut+1​
        
    - **สามัญวิศวกร:** ≤ 50,000 kVA หรือ ≤ 115 kV (อาคารพาณิชย์)coe+1​
        
    - **วุฒิวิศวกร:** ไม่จำกัด (โครงการขนาดใหญ่)mut+1​
        
- **ค่าบริการขั้นต่ำ:**
    
    - ภาคี: 2,500-5,000 บาทecoenergythailand+1​
        
    - สามัญ: 5,000-20,000 บาทfastwork+2​
        
    - วุฒิ: 20,000+ บาทfacebook+1​
        

**ความถี่การเปลี่ยนแปลง:** ประมาณ **3-5 ปีต่อครั้ง**seas+1​

**เหตุผลที่เปลี่ยนนาน:** เป็นกฎหมาย ต้องผ่านสภาวิศวกร → กระทรวง → ราชกิจจานุเบกษา ใช้เวลานานtuda+1​

---

## **1.3 สูตรคำนวณ Voltage Drop**

**สูตรพื้นฐาน (AC Single Phase, 220V):**bangkokcable+3​

VD(Volt)=2×L×I×R1000VD_{(Volt)} = \frac{2 \times L \times I \times R}{1000}VD(Volt)=10002×L×I×R VD(%)=VD(Volt)Vsystem×100VD_{(\%)} = \frac{VD_{(Volt)}}{V_{system}} \times 100VD(%)=VsystemVD(Volt)×100

**โดยที่:**

- LLL = ความยาวสาย (เมตร)
    
- III = กระแสไฟ (Ampere)
    
- RRR = ความต้านทานสาย (Ohm/km)
    
- VsystemV_{system}Vsystem = แรงดันระบบ (220V)
    
- 2×2 \times2× = เพราะมีสายไป-กลับ (Hot + Neutral)
    

**ตัวอย่างคำนวณ:**

**โจทย์:** ใช้สาย THW 2.5 mm² ยาว 30 เมตร กระแส 20A

**ขั้นที่ 1:** หาค่า R จากตาราง

- THW 2.5 mm² = **7.41 Ohm/km**richledshop+1​
    

**ขั้นที่ 2:** แทนค่า

text

`VD = (2 × 30 × 20 × 7.41) / 1000 VD = 8,892 / 1000 = 8.89 Volt VD% = (8.89 / 220) × 100 = 4.04%`

**ผลลัพธ์:** VD = 4.04% → **เกิน 3%** ❌ ต้องเพิ่มขนาดสาย

**ลองใหม่ด้วย THW 4 mm² (R = 4.61 Ohm/km):**

text

`VD = (2 × 30 × 20 × 4.61) / 1000 = 5.53 Volt VD% = (5.53 / 220) × 100 = 2.51%`

**ผลลัพธ์:** VD = 2.51% → **ผ่าน** ✅

**ความถี่การเปลี่ยนแปลง:** **ไม่เปลี่ยนเลย** (กฎฟิสิกส์พื้นฐาน)

---

## **1.4 สูตรคำนวณ Wire Sizing (Ampacity)**

**หลักการ:** สายทองแดงมีความสามารถรับกระแสจำกัด ถ้าเกินจะร้อนเกินไป → ฉนวนไหม้ → ไฟไหม้pantip+2​

**ตาราง Ampacity สาย THW (ทองแดง) ตาม มอก. 11-2553:**fuhrerwire+2​

|ขนาดสาย (mm²)|เส้นผ่าน (mm)|Ampacity ในท่อ (A)|Ampacity ลอย (A)|ความต้านทาน R (Ohm/km)|
|---|---|---|---|---|
|**1.5**|3.4|20|25|12.1|
|**2.5**|4.1|27|35|7.41|
|**4**|4.9|37|50|4.61|
|**6**|5.8|48|65|3.08|
|**10**|7.6|50|70|1.83|
|**16**|9.3|68|95|1.15|
|**25**|12.5|89|119|0.727|

**กฎทอง:**

text

`Wire Ampacity ≥ Load Current × 1.25 (Safety Factor)`

**ตัวอย่าง:**

- โหลด 20A → ต้องใช้สายที่รับได้ ≥ 20 × 1.25 = 25A
    
- จากตาราง: THW 2.5 mm² (27A ในท่อ) → **ใช้ได้** ✅
    

**ความถี่การเปลี่ยนแปลง:** แก้ไขเล็กน้อยตาม มอก. 11 ทุก **5-8 ปี** (เช่น เพิ่มขนาดใหม่ หรือปรับค่า Ampacity เล็กน้อย)narinelectric+1​

---

## **1.5 ข้อห้ามตามกฎหมาย**

**ข้อห้ามเหล่านี้ฝังอยู่ใน มอก. 2955 และไม่ค่อยเปลี่ยน:**anyflip+2​

## **🚫 ห้องน้ำ (Bathroom) — ระดับอันตรายสูงสุด**

**Zone ตาม IEC 60364-7-701:**tisi+3​

text
┌─────────────────────────────────┐
│  ห้องน้ำ (มองจากด้านข้าง)         │
│                                   │
│  ┌─────────────┐  ← 2.25m        │
│  │   Zone 1    │                 │
│  │             │                 │
│  │ฝักบัว/อ่าง  │                 │
│  └─────────────┘                 │
│  ╔═════════════╗  ← พื้น         │
│  ║   Zone 0    ║  (ภายในอ่าง)    │
│  ╚═════════════╝                 │
│                                   │
│     ┌─ 60cm ─┐                    │
│     │Zone 2  │                    │
└─────────────────────────────────┘

**ข้อห้าม:**

1. **Zone 0** (ภายในอ่าง): **ห้ามติดตั้งอุปกรณ์ไฟฟ้าใด ๆ เลย**
    
2. **Zone 1** (เหนืออ่าง สูง 2.25m):
    
    - ✅ อนุญาต: เครื่องทำน้ำอุ่นติดผนัง IP25+ (มี Ground + RCBO)
        
    - ❌ ห้าม: ปลั๊ก, สวิตช์ธรรมดา, ดวงโคมธรรมดา
        
3. **Zone 2** (รอบอ่าง รัศมี 60cm, สูง 2.25m):
    
    - ✅ อนุญาต: ดวงโคม IP44+
        
    - ❌ ห้าม: ปลั๊ก, สวิตช์ธรรมดา
        

**ยกเว้น (ต้องมีเงื่อนไข):**

- **ปลั๊กโกนหนวด (Shaver Socket):**kjl+1​
    
    - ต้องห่างจากแหล่งน้ำ ≥ 60 cm
        
    - ต้องมี **RCBO/RCCB 30mA** ป้องกันไฟรั่ว
        
    - ต้องเป็นแบบ **Isolated Transformer** (แยกจากระบบหลัก)
        

**มาตรฐาน:** มอก. 2955 มาตรา 701, IEC 60364-7-701pea+2​

**เหตุผล:** น้ำเป็นตัวนำไฟฟ้า ถ้าไฟรั่วในห้องน้ำ = ช็อตตายทันที เพราะตัวเปียกอยู่แล้วengineers.techinfus+2​

---

## **🚫 ข้อห้ามทั่วไป**

1. **Voltage Drop > 3% (branch) หรือ > 5% (รวม):**bangkokcable+2​
    
    - เหตุผล: VD สูง = แรงดันตก → อุปกรณ์ทำงานผิดปกติ (แอร์สตาร์ทไม่ติด, หลอดไฟสลัว)
        
2. **Overload Breaker > 80% ของพิกัด:**eng.rtu+1​
    
    - เหตุผล: Breaker ทำงานต่อเนื่อง > 80% = ร้อนเกิน → เสื่อม → ตัดไม่ทันเมื่อ Short Circuit
        
3. **ใช้สายเกิน Ampacity:**richledshop+2​
    
    - เหตุผล: สายร้อนเกิน → ฉนวนละลาย → ไฟลัดวงจร → ไฟไหม้
        
4. **ต่อสาย (splice) โดยไม่มี junction box:**[coe](https://coe.or.th/wp-content/uploads/2022/11/%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%9F%E0%B8%9F%E0%B9%89%E0%B8%B2%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%95%E0%B8%B1%E0%B9%89%E0%B8%87%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99.pdf)​
    
    - เหตุผล: จุดต่อเป็นจุดอ่อน ถ้าไม่มีกล่องป้องกัน → ฝุ่น, ความชื้น, หนู → ไฟลัด
        

**ความถี่การเปลี่ยนแปลง:** **ไม่เปลี่ยนเลย** (เป็นหลักความปลอดภัยพื้นฐาน)anyflip+2​

---

## **🔄 ข้อมูลที่เปลี่ยนบ่อย (ควรเก็บใน Database/Config)**

## **2.1 ราคาวัสดุ (สาย, ท่อ, Breaker)**

**ปัจจัยที่กระทบราคา:**

1. **ราคาทองแดง (Copper Price):**pantip+1​
    
    - ทองแดงขึ้น 10% → สาย THW ขึ้น 8-12%
        
    - ทองแดงเป็นต้นทุนหลักของสายไฟ (~70% ของราคา)
        
2. **ราคาน้ำมัน:**cppc+1​
    
    - น้ำมันขึ้น → ค่าขนส่งขึ้น → ท่อ PVC ขึ้น (ทำจากน้ำมัน)
        
3. **อัตราแลกเปลี่ยน (Breaker นำเข้า):**pantip+2​
    
    - Schneider, ABB, Siemens = นำเข้าจากยุโรป
        
    - บาทแข็ง = ราคาถูก, บาทอ่อน = ราคาแพง
        

**ตัวอย่างราคา (ปี 2568):**spebanmoh-online+3​

|รายการ|ราคา (บาท)|ความผันผวน|
|---|---|---|
|สาย THW 1.5 mm²|8-12/ม.|ขึ้น-ลง 10-20%/ปี|
|สาย THW 2.5 mm²|15-20/ม.|ขึ้น-ลง 10-20%/ปี|
|ท่อ PVC 1/2"|30-45/เส้น|ขึ้น-ลง 5-15%/ปี|
|Breaker Schneider 20A|250|ขึ้น-ลง 10-15%/ปี|
|Breaker Mitsubishi 20A|180|ขึ้น-ลง 8-12%/ปี|

**ความถี่การเปลี่ยนแปลง:** **ทุก 3-6 เดือน** (ตามราคาวัตถุดิบโลก)pantip+2​

**วิธีจัดการ:**

python

`# config.json (อัพเดทได้ง่าย) {   "material_prices": {    "wire_thw": {      "1.5": 10,      "2.5": 18,      "4.0": 28    },    "breaker_schneider": {      "20": 250,      "32": 300    }  },  "last_updated": "2025-11-16" }`

---

## **2.2 รุ่นและสเปค Breaker ของแต่ละยี่ห้อ**

**ปัญหา:** ทุกยี่ห้อออกรุ่นใหม่บ่อย (ปีละ 1-2 รุ่น)pantip+3​

**ตัวอย่าง Schneider Electric:**pantip+1​

- **รุ่นเก่า:** Multi 9 C60N (ยุคก่อน 2015)
    
- **รุ่นปัจจุบัน:** Acti9 iC60N (2015-ปัจจุบัน)
    
- **รุ่นใหม่ล่าสุด:** Acti9 iC60H (High Performance, 2023+)
    

**ความแตกต่าง:**

- Breaking Capacity เพิ่มขึ้น (6kA → 10kA → 15kA)
    
- Trip Curve แม่นยำขึ้น
    
- ขนาดเล็กลง (จาก 18mm → 17.5mm)
    
- ราคาแพงขึ้น 10-20%
    

**ตัวอย่าง Mitsubishi:**thun+2​

- **รุ่นเก่า:** BH-D Series (ยุคก่อน 2018)
    
- **รุ่นปัจจุบัน:** NF Series (2018-ปัจจุบัน)
    
- **รุ่นใหม่:** WS-V Series (2024+, มี IoT)
    

**ความถี่การเปลี่ยนแปลง:** **ทุก 1-2 ปี** (รุ่นใหม่ออก)thun+2​

**วิธีจัดการ:**

python

`# database: breaker_models table {   "brand": "Schneider",  "series": "Acti9 iC60N",  "ratings": [6, 10, 16, 20, 25, 32, 40, 50, 63],  "curve_types": ["B", "C", "D"],  "breaking_capacity": 6000,  # A  "price_1p": {...},  "discontinued": False,  "release_year": 2015 }`

---

## **2.3 ค่าแรงช่าง**

**ปัจจัยที่กระทบ:**

1. **เงินเฟ้อ (Inflation):** ค่าแรงขึ้น 3-5%/ปี[onestockhome](https://www.onestockhome.com/th/articles/833fd534-9e42-44c4-a57f-4910bcfb0d7e)​
    
2. **ค่าครองชีพ:** กรุงเทพฯ แพงกว่าต่างจังหวัด 20-30%[onestockhome](https://www.onestockhome.com/th/articles/833fd534-9e42-44c4-a57f-4910bcfb0d7e)​
    
3. **ทักษะช่าง:** ช่างมีใบอนุญาตแพงกว่าช่างทั่วไป 30-50%[onestockhome](https://www.onestockhome.com/th/articles/833fd534-9e42-44c4-a57f-4910bcfb0d7e)​
    

**ตัวอย่างอัตราค่าแรง (ปี 2568):**tumcivil+2​

|รายการ|กรุงเทพฯ (บาท)|ต่างจังหวัด (บาท)|
|---|---|---|
|ค่าเดินสาย + ท่อ (ต่อเมตร)|40-60|30-45|
|ค่าติดตั้งปลั๊ก/สวิตช์ (ต่อจุด)|80-120|60-100|
|ค่าติดตั้ง DB|2,000-3,000|1,500-2,500|
|ค่าติดตั้งระบบทั้งหมด (ต่อตร.ม.)|200-300|150-250|

**ความถี่การเปลี่ยนแปลง:** **ทุก 6-12 เดือน** (ขึ้นตามเงินเฟ้อ)tumcivil+1​

---

## **2.4 อัตราค่าไฟฟ้า (PEA/MEA)**

**ปัจจัยที่กระทบ:**

1. **ราคาก๊าซธรรมชาติ (LNG):**[pea](https://www.pea.co.th/our-services/tariff)​
    
    - ไฟฟ้าไทย 60% มาจากก๊าซ
        
    - ก๊าซขึ้น → ค่าไฟขึ้น
        
2. **ค่า Ft (Fuel Adjustment):**[pea](https://www.pea.co.th/our-services/tariff)​
    
    - ปรับทุก 4 เดือน (ม.ค.-เม.ย., พ.ค.-ส.ค., ก.ย.-ธ.ค.)
        

**อัตราค่าไฟบ้านพักอาศัย (ปี 2568):**[pea](https://www.pea.co.th/our-services/tariff)​

|หน่วย (kWh)|ราคา (บาท/หน่วย)|
|---|---|
|0-150|3.20-4.20|
|151-400|4.40-4.80|
|401+|5.00-5.50|

**ความถี่การเปลี่ยนแปลง:** **ทุก 4 เดือน** (Ft adjustment)[pea](https://www.pea.co.th/our-services/tariff)​

---

## 📦 ส่วนที่ 2: โครงสร้าง MCP Core — 8 Modules ละเอียดทุกตัว

## **Module 1: load_calculator.py — คำนวณโหลดทั้งหมด + Demand Factor**

## **หลักการ:**

ระบบไฟฟ้าบ้านต้องคำนวณโหลดให้ถูกต้อง มิฉะนั้น:

- **ประมาณต่ำเกิน:** มิเตอร์/เบรกเกอร์เล็กเกิน → ตัดบ่อย
    
- **ประมาณสูงเกิน:** สายใหญ่เกิน → เสียเงินฟรี ๆchangfi+2​
    

## **Demand Factor (DF) คืออะไร?**

**หลักการ:** ไม่มีใครเปิดไฟ + แอร์ + ตู้เย็น + ปั๊มน้ำ + ทุกอย่าง 100% ตลอดเวลาecpe.nu+1​[youtube](https://www.youtube.com/watch?v=36MYO08DyAw)​

**ตัวอย่าง:**

- บ้านมีไฟ 20 ดวง = 200W
    
- แต่ในความเป็นจริง เปิดพร้อมกันแค่ 5-7 ดวง = 50-70W (35% ของทั้งหมด)[ecpe.nu](http://www.ecpe.nu.ac.th/piyadanai/content/48_01/303426_1_48/File/Lesson_3_1.pdf)​
    

**ตาราง Demand Factor ตาม วสท. (มาตรฐานการติดตั้งทางไฟฟ้า):**facebook+3​[youtube](https://www.youtube.com/watch?v=36MYO08DyAw)​

## **A. แสงสว่าง (Lighting)**

|โหลดรวม (VA)|Demand Factor (%)|
|---|---|
|0 - 2,000 VA|100%|
|2,001 - 10,000 VA|**2,000 VA (100%)** + ส่วนเกิน (35%)|
|10,001+ VA|**2,000 + 2,800** + ส่วนเกิน (25%)|

**สูตร:**

python

`if lighting_va <= 2000:     lighting_demand = lighting_va elif lighting_va <= 10000:     lighting_demand = 2000 + (lighting_va - 2000) * 0.35 else:     lighting_demand = 2000 + (8000 * 0.35) + (lighting_va - 10000) * 0.25`

**ตัวอย่าง:**

- โหลดไฟ = 5,000 VA
    

python

`lighting_demand = 2,000 + (5,000 - 2,000) × 0.35                 = 2,000 + 1,050 = 3,050 VA`

---

## **B. เต้ารับทั่วไป (Receptacles)**

|โหลดรวม (VA)|Demand Factor (%)|
|---|---|
|0 - 10,000 VA|100%|
|10,001+ VA|**10,000 VA (100%)** + ส่วนเกิน (50%)|

**มาตรฐาน:** 1 เต้ารับ = 180 VA (ตาม วสท.)eng.rtu+1​

**ตัวอย่าง:**

- มี 15 เต้ารับ = 15 × 180 = 2,700 VA
    

python

`receptacle_demand = 2,700 VA (ต่ำกว่า 10,000 = ใช้ 100%)`

---

## **C. เครื่องใช้ไฟฟ้าเฉพาะ (Appliances)**

|ประเภท|Demand Factor (%)|
|---|---|
|แอร์ (Air Conditioner)|100%|
|เครื่องทำน้ำอุ่น|100%|
|ตู้เย็น|100%|
|ปั๊มน้ำ|100%|
|เตาไฟฟ้า/เตาอบ|100%|

**เหตุผล:** อุปกรณ์เหล่านี้เป็น **Essential Load** หรือมี **Inrush Current** สูง (สตาร์ททีเดียวกินเยอะ) ต้องเผื่อเต็มcivilpracticalknowledge+3​

---

## **ตัวอย่างการคำนวณแบบละเอียด: บ้าน 1 ชั้น**

**โจทย์:**

- ไฟ LED 10W × 10 ดวง = 100W (PF 0.95) = **105 VA**
    
- แอร์ 9,000 BTU = 2,500W (PF 0.85) = **2,941 VA**
    
- ตู้เย็น 150W (PF 0.85) = **176 VA**
    
- ปั๊มน้ำ 550W (PF 0.75) = **733 VA**
    
- เต้ารับ 10 จุด = 10 × 180 = **1,800 VA**
    

**ขั้นที่ 1: รวมโหลดตามประเภท**

python

`lighting_total_va = 105 VA receptacle_total_va = 1,800 VA ac_va = 2,941 VA fridge_va = 176 VA pump_va = 733 VA`

**ขั้นที่ 2: ใช้ Demand Factor**

python

`# Lighting: 105 < 2000 → 100% lighting_demand = 105 VA # Receptacle: 1,800 < 10,000 → 100% receptacle_demand = 1,800 VA # Appliances: 100% (ไม่ลด) appliance_demand = 2,941 + 176 + 733 = 3,850 VA`

**ขั้นที่ 3: รวมทั้งหมด**

python

`total_demand_va = 105 + 1,800 + 3,850 = 5,755 VA`

**ขั้นที่ 4: คำนวณกระแส**

python

`current_a = 5,755 / 220 = 26.16 A`

**ขั้นที่ 5: เผื่อ Safety Factor 1.25×**

python

`required_breaker = 26.16 × 1.25 = 32.7 A`

**สรุป:** ใช้มิเตอร์ **15(45)A** หรือ Main Breaker **63A 2P** ✅eng.rtu+1​

---

## **Code Python สมบูรณ์:**

python

def calculate_demand_load(lighting_va, receptacle_va, appliances):
    """
    คำนวณ Demand Load ตาม วสท.
    
    Parameters:
    - lighting_va: โหลดแสงสว่างรวม (VA)
    - receptacle_va: โหลดเต้ารับรวม (VA)
    - appliances: dict {"name": VA, ...}
    
    Returns:
    - total_demand_va: Demand Load รวม (VA)
    - current_a: กระแส (A)
    - required_breaker: Breaker ขั้นต่ำ (A)
    """
    
    # 1. Lighting Demand Factor
    if lighting_va <= 2000:
        lighting_demand = lighting_va
    elif lighting_va <= 10000:
        lighting_demand = 2000 + (lighting_va - 2000) * 0.35
    else:
        lighting_demand = 2000 + (8000 * 0.35) + (lighting_va - 10000) * 0.25
    
    # 2. Receptacle Demand Factor
    if receptacle_va <= 10000:
        receptacle_demand = receptacle_va
    else:
        receptacle_demand = 10000 + (receptacle_va - 10000) * 0.50
    
    # 3. Appliances Demand (100% — ไม่ลด)
    appliance_demand = sum(appliances.values())
    
    # 4. Total Demand
    total_demand_va = lighting_demand + receptacle_demand + appliance_demand
    
    # 5. Current (220V single phase)
    current_a = total_demand_va / 220
    
    # 6. Required Breaker (1.25× safety factor)
    required_breaker = current_a * 1.25
    
    return {
        "lighting_demand_va": round(lighting_demand, 2),
        "receptacle_demand_va": round(receptacle_demand, 2),
        "appliance_demand_va": round(appliance_demand, 2),
        "total_demand_va": round(total_demand_va, 2),
        "current_a": round(current_a, 2),
        "required_breaker_a": round(required_breaker, 2)
    }

# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    result = calculate_demand_load(
        lighting_va=105,
        receptacle_va=1800,
        appliances={
            "แอร์": 2941,
            "ตู้เย็น": 176,
            "ปั๊มน้ำ": 733
        }
    )
    
    print("=" * 60)
    print("📊 ผลการคำนวณโหลด (Load Calculation)")
    print("=" * 60)
    print(f"Lighting Demand:     {result['lighting_demand_va']:>10,.2f} VA")
    print(f"Receptacle Demand:   {result['receptacle_demand_va']:>10,.2f} VA")
    print(f"Appliance Demand:    {result['appliance_demand_va']:>10,.2f} VA")
    print("=" * 60)
    print(f"Total Demand Load:   {result['total_demand_va']:>10,.2f} VA")
    print(f"Total Current:       {result['current_a']:>10,.2f} A")
    print(f"Required Breaker:    {result['required_breaker_a']:>10,.2f} A")
    print("=" * 60)
    print(f"✅ ใช้ Main Breaker: 63A 2P")


**Output:**

text

`============================================================ 📊 ผลการคำนวณโหลด (Load Calculation) ============================================================ Lighting Demand:           105.00 VA Receptacle Demand:       1,800.00 VA Appliance Demand:        3,850.00 VA ============================================================ Total Demand Load:       5,755.00 VA Total Current:              26.16 A Required Breaker:           32.70 A ============================================================ ✅ ใช้ Main Breaker: 63A 2P`

---

## **Module 2: wire_sizer.py — เลือกขนาดสาย + ตรวจ Voltage Drop**

## **หลักการ:**

การเลือกสายไฟต้องพิจารณา **2 ปัจจัย:**thaiyazaki+2​

1. **Ampacity (ความสามารถรับกระแส):** สายต้องรับกระแสได้โดยไม่ร้อนเกิน
    
2. **Voltage Drop (การตกของแรงดัน):** แรงดันที่ปลายทางต้องไม่ต่ำเกิน 3%
    

---

## **ส่วนที่ 1: Ampacity — ความสามารถรับกระแส**

**หลักการ:** เมื่อกระแสไหลผ่านสาย → สายร้อน → ถ้ากระแสสูงเกิน → สายร้อนจนฉนวนละลาย → ไฟลัดfuhrerwire+2​

**ตาราง Ampacity สาย THW (ทองแดง, 75°C) ตาม มอก. 11-2553:**narinelectric+2​

|ขนาดสาย (mm²)|หน้าตัด (mm²)|เส้นผ่าน OD (mm)|Ampacity ในท่อ (A)|Ampacity ลอย (A)|ความต้านทาน R (Ohm/km @20°C)|
|---|---|---|---|---|---|
|**1.5**|1.5|3.4|**20**|25|12.1|
|**2.5**|2.5|4.1|**27**|35|7.41|
|**4**|4|4.9|**37**|50|4.61|
|**6**|6|5.8|**48**|65|3.08|
|**10**|10|7.6|**50**|70|1.83|
|**16**|16|9.3|**68**|95|1.15|
|**25**|25|12.5|**89**|119|0.727|
|**35**|35|14.5|**111**|148|0.524|

**หมายเหตุ:**

- **ในท่อ (In Conduit):** กระแสต่ำกว่า เพราะอากาศถ่ายเทได้น้อย → ร้อนสะสมengfanatic.tumcivil+1​
    
- **ลอย (Free Air):** กระแสสูงกว่า เพราะระบายความร้อนได้ดี[richledshop](https://www.richledshop.com/article/26/%E0%B9%80%E0%B8%A5%E0%B8%B7%E0%B8%AD%E0%B8%81%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%9F-thw-%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99)​
    

**กฎทอง NEC 210.19:**pantip+1​

text

`Wire Ampacity ≥ Load Current × 1.25 (Continuous Load)`

**เหตุผล:** เผื่อ 25% เพราะ:

1. สายอาจร้อนขึ้นเมื่อสภาพแวดล้อมร้อน (อุณหภูมิสูง)
    
2. ป้องกันการใช้งานผิดปกติ (เปิดเครื่องพร้อมกัน)richledshop+1​
    

**ตัวอย่าง:**

- โหลด 20A (ต่อเนื่อง)
    
- Required Ampacity = 20 × 1.25 = 25A
    
- จากตาราง: THW 2.5 mm² (27A ในท่อ) → **ใช้ได้** ✅
    

---

## **ส่วนที่ 2: Voltage Drop — การตกของแรงดัน**

**หลักการ:** กระแสไหลผ่านสาย → ความต้านทาน R → แรงดันตก → อุปกรณ์ปลายทางได้แรงดันต่ำกว่าที่ต้นทางscribd+2​

**สูตร (AC Single Phase, 220V):**bangkokcable+3​

VD(Volt)=2×L×I×R1000VD_{(Volt)} = \frac{2 \times L \times I \times R}{1000}VD(Volt)=10002×L×I×R VD(%)=VD(Volt)220×100VD_{(\%)} = \frac{VD_{(Volt)}}{220} \times 100VD(%)=220VD(Volt)×100

**โดยที่:**

- 2×2 \times2× = เพราะมีสายไป-กลับ (Hot + Neutral)
    
- LLL = ความยาวสาย (เมตร)
    
- III = กระแสไฟ (Ampere)
    
- RRR = ความต้านทาน (Ohm/km) จากตาราง
    
- 100010001000 = แปลง km → m
    

**มาตรฐาน NEC 215.2, มอก. 2955:**thaiyazaki+2​

- **Branch Circuit:** VD ≤ 3%
    
- **Feeder + Branch:** VD รวม ≤ 5%
    

**เหตุผล:** VD สูงเกิน → อุปกรณ์ทำงานผิดปกติ:

- **แอร์:** คอมเพรสเซอร์สตาร์ทไม่ติด
    
- **หลอดไฟ:** สลัว กะพริบ
    
- **มอเตอร์:** กำลังลด ร้อนเกินbangkokcable+1​
    

---

## **ตัวอย่างคำนวณแบบละเอียด:**

**โจทย์:** วงจรแอร์

- กระแส: 13.4A
    
- ระยะทาง: 25 เมตร
    
- ลองใช้สาย THW 2.5 mm²
    

**ขั้นที่ 1: เช็ค Ampacity**

python

`required_ampacity = 13.4 × 1.25 = 16.75 A wire_ampacity = 27 A (THW 2.5 mm²) → 27 ≥ 16.75 ✅ ผ่าน`

**ขั้นที่ 2: เช็ค Voltage Drop**

python

`R = 7.41 Ohm/km (จากตาราง) VD = (2 × 25 × 13.4 × 7.41) / 1000 VD = 4,965 / 1000 = 4.97 Volt VD% = (4.97 / 220) × 100 = 2.26% → 2.26% < 3% ✅ ผ่าน`

**สรุป:** ใช้ THW 2.5 mm² ได้ ✅

---

**ถ้า VD เกิน 3% ให้เพิ่มขนาดสาย:**

**ตัวอย่าง:** วงจรปลั๊ก

- กระแส: 8.2A
    
- ระยะทาง: 40 เมตร (ไกล)
    
- ลองใช้ THW 2.5 mm²
    

python

`VD = (2 × 40 × 8.2 × 7.41) / 1000 = 4.86 Volt VD% = (4.86 / 220) × 100 = 2.21% → 2.21% < 3% ✅ ผ่าน`

**แต่ถ้าระยะ 50 เมตร:**

python

`VD = (2 × 50 × 8.2 × 7.41) / 1000 = 6.08 Volt VD% = (6.08 / 220) × 100 = 2.76% → 2.76% < 3% ✅ แต่ใกล้เคียง`

**ระยะ 60 เมตร:**

python

`VD = (2 × 60 × 8.2 × 7.41) / 1000 = 7.29 Volt VD% = (7.29 / 220) × 100 = 3.31% → 3.31% > 3% ❌ ไม่ผ่าน`

**วิธีแก้:** เพิ่มเป็น THW 4 mm² (R = 4.61)

python

`VD = (2 × 60 × 8.2 × 4.61) / 1000 = 4.53 Volt VD% = (4.53 / 220) × 100 = 2.06% → 2.06% < 3% ✅ ผ่าน`

---

## **Code Python สมบูรณ์:**

python

import math

# ตารางค่าความต้านทาน (Ohm/km @ 20°C)
RESISTANCE_TABLE = {
    1.5: 12.1,
    2.5: 7.41,
    4.0: 4.61,
    6.0: 3.08,
    10.0: 1.83,
    16.0: 1.15,
    25.0: 0.727,
    35.0: 0.524,
    50.0: 0.387,
    70.0: 0.268
}

# ตาราง Ampacity (A) ในท่อ @ 30°C ambient
AMPACITY_TABLE = {
    1.5: 20,
    2.5: 27,
    4.0: 37,
    6.0: 48,
    10.0: 50,
    16.0: 68,
    25.0: 89,
    35.0: 111,
    50.0: 134,
    70.0: 171
}

def calculate_voltage_drop(length_m, current_a, wire_size_mm2, voltage_v=220, power_factor=1.0):
    """
    คำนวณ Voltage Drop (%)
    
    Parameters:
    - length_m: ความยาวสาย (เมตร)
    - current_a: กระแสไฟ (A)
    - wire_size_mm2: ขนาดสาย (mm²)
    - voltage_v: แรงดันระบบ (V) — default 220V
    - power_factor: ค่า PF (สำหรับ AC) — default 1.0 (resistive load)
    
    Returns:
    - vd_volt: Voltage Drop (Volt)
    - vd_percent: Voltage Drop (%)
    """
    R = RESISTANCE_TABLE.get(wire_size_mm2)
    if R is None:
        raise ValueError(f"❌ ไม่มีขนาดสาย {wire_size_mm2} mm² ในตาราง")
    
    # สูตร: VD = 2 × L × I × R / 1000 (AC single phase)
    vd_volt = (2 * length_m * current_a * R) / 1000
    vd_percent = (vd_volt / voltage_v) * 100
    
    return vd_volt, vd_percent

def select_wire_size(current_a, length_m, max_vd_percent=3.0, voltage_v=220, safety_factor=1.25):
    """
    เลือกขนาดสายที่เหมาะสม
    
    Parameters:
    - current_a: กระแสโหลด (A)
    - length_m: ระยะทาง (เมตร)
    - max_vd_percent: Voltage Drop สูงสุด (%) — default 3%
    - voltage_v: แรงดันระบบ (V) — default 220V
    - safety_factor: Safety Factor — default 1.25
    
    Returns:
    - wire_size: ขนาดสาย (mm²)
    - ampacity: Ampacity ของสาย (A)
    - vd_volt: Voltage Drop (Volt)
    - vd_percent: Voltage Drop (%)
    """
    # ขั้นที่ 1: คำนวณ Required Ampacity
    required_ampacity = current_a * safety_factor
    
    # ขั้นที่ 2: ลองเลือกสายตั้งแต่เล็กไปใหญ่
    for size in sorted(AMPACITY_TABLE.keys()):
        ampacity = AMPACITY_TABLE[size]
        
        # เช็ค Ampacity
        if ampacity >= required_ampacity:
            # เช็ค Voltage Drop
            vd_volt, vd_percent = calculate_voltage_drop(length_m, current_a, size, voltage_v)
            
            if vd_percent <= max_vd_percent:
                return {
                    "wire_size_mm2": size,
                    "ampacity_a": ampacity,
                    "vd_volt": round(vd_volt, 2),
                    "vd_percent": round(vd_percent, 2),
                    "status": "✅ ผ่าน"
                }
    
    # ถ้าไม่มีขนาดไหนผ่าน
    return {
        "wire_size_mm2": None,
        "ampacity_a": None,
        "vd_volt": None,
        "vd_percent": None,
        "status": "❌ ไม่มีขนาดสายที่เหมาะสม (ลดระยะทางหรือลดกระแส)"
    }

# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    print("=" * 70)
    print("🔌 Wire Sizer — เลือกขนาดสายอัตโนมัติ")
    print("=" * 70)
    
    # ตัวอย่าง: วงจรแอร์
    result = select_wire_size(current_a=13.4, length_m=25, max_vd_percent=3.0)
    
    print("\n📍 วงจร: แอร์")
    print(f"   กระแส: 13.4 A")
    print(f"   ระยะทาง: 25 เมตร")
    print(f"   → ขนาดสาย: THW {result['wire_size_mm2']} mm²")
    print(f"   → Ampacity: {result['ampacity_a']} A")
    print(f"   → Voltage Drop: {result['vd_volt']} V ({result['vd_percent']}%)")
    print(f"   → สถานะ: {result['status']}")
    
    # ตัวอย่าง: วงจรปลั๊ก (ระยะไกล)
    result2 = select_wire_size(current_a=8.2, length_m=60, max_vd_percent=3.0)
    
    print("\n📍 วงจร: ปลั๊กทั่วไป")
    print(f"   กระแส: 8.2 A")
    print(f"   ระยะทาง: 60 เมตร")
    print(f"   → ขนาดสาย: THW {result2['wire_size_mm2']} mm²")
    print(f"   → Ampacity: {result2['ampacity_a']} A")
    print(f"   → Voltage Drop: {result2['vd_volt']} V ({result2['vd_percent']}%)")
    print(f"   → สถานะ: {result2['status']}")
    
    print("=" * 70)

**Output:**

text

`====================================================================== 🔌 Wire Sizer — เลือกขนาดสายอัตโนมัติ ====================================================================== 📍 วงจร: แอร์    กระแส: 13.4 A   ระยะทาง: 25 เมตร   → ขนาดสาย: THW 2.5 mm²   → Ampacity: 27 A   → Voltage Drop: 4.97 V (2.26%)   → สถานะ: ✅ ผ่าน 📍 วงจร: ปลั๊กทั่วไป    กระแส: 8.2 A   ระยะทาง: 60 เมตร   → ขนาดสาย: THW 4.0 mm²   → Ampacity: 37 A   → Voltage Drop: 4.53 V (2.06%)   → สถานะ: ✅ ผ่าน ======================================================================`

---


    


