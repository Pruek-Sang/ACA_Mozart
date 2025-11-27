## **1.1 Scope และขอบเขตการทำงาน (What MCP Does)**

## **รองรับ (Supported)**

- **ประเภทอาคาร**: บ้านพักอาศัยในประเทศไทยเท่านั้น (Thai Residential Buildings Only)
    
    - บ้านเดี่ยว 1 ชั้น (Single-story detached house)
        
    - บ้านเดี่ยว 2-3 ชั้น (2-3 story detached house)
        
    - ทาวน์เฮ้าส์/ทาวน์โฮม 2-3 ชั้น (Townhouse/Townhome)
        
    - บ้านแฝด (Semi-detached house)
        
- **ระบบไฟฟ้า**:
    
    - แรงดันต่ำ (Low Voltage: LV) เท่านั้น
        
    - 1 เฟส 230V (TH_1PH_230V) - ระบบหลัก
        
    - 3 เฟส 400V (TH_3PH_400V) - รองรับแต่ยังไม่เปิดใช้งานใน demo
        
- **ระบบต่อลงดิน (Earthing System)**:
    
    - TT (Terra-Terra) สำหรับ 1 เฟส - มาตรฐานในไทย
        
    - TN-S (Terra-Neutral Separate) สำหรับ 3 เฟส - รองรับแต่ยังไม่เปิดใช้
        
- **มาตรฐานที่ใช้**:
    
    - มาตรฐานการติดตั้งทางไฟฟ้าสำหรับประเทศไทย (วสท. 2564)
        
    - IEC 60364 (เฉพาะส่วนที่เกี่ยวข้อง)
        
    - มอก.11-2553 (สายไฟฟ้า)
        
    - พ.ร.บ. ควบคุมอาคาร พ.ศ. 2522
        

## **ไม่รองรับ (NOT Supported)**

- โรงงานอุตสาหกรรม (Industrial/Factory)
    
- อาคารสูง/คอนโดมิเนียม (High-rise/Condominium)
    
- อาคารพาณิชย์ขนาดใหญ่ (Large commercial buildings)
    
- ระบบแรงสูง (Medium Voltage: MV 22kV/33kV)
    
- ระบบ standalone (Solar + Battery ที่ไม่ต่อกับการไฟฟ้า)
    

---

## **1.2 Building Types รายละเอียด (Supported building_type)**

## **RESIDENTIAL_SINGLE_1F**

- **คำอธิบาย**: บ้านเดี่ยว 1 ชั้น
    
- **พื้นที่ใช้สอย**: 60-200 ตร.ม.
    
- **จำนวนห้องสูงสุด**: 15 ห้อง
    
- **โหลดรวมสูงสุด**: 15 kVA (ประมาณ 65A @ 230V)
    
- **จำนวนวงจรโดยประมาณ**: 8-20 circuits
    
- **ตัวอย่าง**: บ้านชั้นเดียว 2-3 ห้องนอน
    

## **RESIDENTIAL_SINGLE_2F**

- **คำอธิบาย**: บ้านเดี่ยว 2 ชั้น
    
- **พื้นที่ใช้สอย**: 100-350 ตร.ม.
    
- **จำนวนห้องสูงสุด**: 25 ห้อง
    
- **โหลดรวมสูงสุด**: 25 kVA (ประมาณ 100A @ 230V)
    
- **จำนวนวงจรโดยประมาณ**: 12-35 circuits
    
- **ตัวอย่าง**: บ้าน 3-4 ห้องนอน มีห้องทำงาน
    

## **RESIDENTIAL_SINGLE_3F**

- **คำอธิบาย**: บ้านเดี่ยว 3 ชั้น
    
- **พื้นที่ใช้สอย**: 150-500 ตร.ม.
    
- **จำนวนห้องสูงสุด**: 35 ห้อง
    
- **โหลดรวมสูงสุด**: 35 kVA (ประมาณ 150A @ 230V)
    
- **จำนวนวงจรโดยประมาณ**: 18-50 circuits
    
- **ตัวอย่าง**: บ้าน 4-5 ห้องนอน หลายห้องน้ำ
    

## **TOWNHOME_2F**

- **คำอธิบาย**: ทาวน์เฮ้าส์/ทาวน์โฮม 2 ชั้น
    
- **พื้นที่ใช้สอย**: 80-180 ตร.ม.
    
- **จำนวนห้องสูงสุด**: 18 ห้อง
    
- **โหลดรวมสูงสุด**: 20 kVA (ประมาณ 85A @ 230V)
    
- **จำนวนวงจรโดยประมาณ**: 10-28 circuits
    
- **ตัวอย่าง**: ทาวน์โฮม 3 ห้องนอน
    

## **TOWNHOME_3F**

- **คำอธิบาย**: ทาวน์เฮ้าส์/ทาวน์โฮม 3 ชั้น
    
- **พื้นที่ใช้สอย**: 120-250 ตร.ม.
    
- **จำนวนห้องสูงสุด**: 25 ห้อง
    
- **โหลดรวมสูงสุด**: 28 kVA (ประมาณ 120A @ 230V)
    
- **จำนวนวงจรโดยประมาณ**: 14-40 circuits
    
- **ตัวอย่าง**: ทาวน์โฮม 4 ห้องนอน มี rooftop
    

---

## **1.3 Voltage & Earthing Systems**

## **TH_1PH_230V + TT (Primary System)**

- **แรงดัน**: 230V AC, 50Hz, Single Phase
    
- **ระบบต่อลงดิน**: TT (Terra-Terra)
    
    - หลักดินแยกอิสระที่ฝั่งผู้ใช้
        
    - ความต้านทานดิน ≤ 5Ω
        
    - ต้องมี RCD/RCBO ป้องกันไฟรั่ว
        
- **มิเตอร์มาตรฐาน**: 5(15)A, 15(45)A, 30(100)A
    
- **เมนเบรกเกอร์**: 32A, 40A, 50A, 63A, 80A, 100A
    
- **สถานะ**: **เปิดใช้งานเต็มรูปแบบ**
    

## **TH_3PH_400V + TN-S (Future Support)**

- **แรงดัน**: 400V AC, 50Hz, 3 Phase 4 Wire (R-Y-B-N)
    
- **ระบบต่อลงดิน**: TN-S (Terra-Neutral Separate)
    
    - สาย PE แยกจาก N ตลอดทาง
        
    - ต่อลงดินที่ Transformer + MDB
        
- **มิเตอร์มาตรฐาน**: 30(100)A, 50(150)A
    
- **เมนเบรกเกอร์**: 3P 63A, 80A, 100A, 125A
    
- **สถานะ**: **รองรับแต่ยังไม่เปิดใช้ใน demo**
    
- **เหตุผล**: ต้องทดสอบ load balancing algorithm ก่อน
    

---

## **1.4 Current Limitations (ข้อจำกัดปัจจุบัน)**

## **ข้อจำกัดด้านโหลด**

- **Total Apparent Power สูงสุด**: 35 kVA (ประมาณ 150A @ 230V)
    
    - เกินนี้ควรใช้ 3 เฟสหรือแบ่งเป็นหลาย MDB
        
- **Peak Demand Factor**: คำนวณจาก วสท. 2564 บทที่ 2
    
    - ห้องแรก: 100%
        
    - ห้องที่ 2-3: 35%
        
    - ห้องที่ 4+: 25%
        
- **Power Factor**: ใช้ค่าเฉลี่ย 0.85-0.95 ตาม load type
    

## **ข้อจำกัดด้านจำนวน**

- **Maximum Circuits**: 50 วงจร (ตามขนาดตู้ DB ที่ใหญ่ที่สุด)
    
- **Maximum Rooms**: 35 ห้อง
    
- **Maximum Loads per Circuit**: 10 โหลด (เกินนี้ควรแยกวงจร)
    
- **Maximum Distance**: 100 เมตร (เกินนี้ต้องคำนวณ Voltage Drop แบบพิเศษ)
    

## **ข้อจำกัดด้าน Database**

- **Device Code**: รองรับเฉพาะ device_code ที่มีใน catalog
    
    - ถ้าไม่มี → RAG ต้องแปลงเป็น semantic code ที่ใกล้เคียง
        
    - ไม่มี fallback = ต้อง error ทันที
        
- **Room Template**: รองรับเฉพาะ room_type ที่มีใน ROOM_TEMPLATE table
    
    - ถ้าไม่มี template → RAG ต้องขอข้อมูลเพิ่ม
        
    - ห้ามสร้าง template ใหม่แบบอัตโนมัติ
        
- **Rule Profile**: รองรับเฉพาะ `TH_RESIDENTIAL_LV` ในปัจจุบัน
    
    - Future: อาจมี `TH_RESIDENTIAL_MV`, `TH_COMMERCIAL_LV`
        

---

## **1.5 Features NOT Supported Yet (สิ่งที่ยังไม่รองรับ)**

## **การคำนวณขั้นสูง**

- ❌ **Short-Circuit Coordination**: ยังไม่คำนวณกระแสลัดวงจร (Ic)
    
    - ใช้ค่า default: Main CB = 10kA, Sub CB = 6kA
        
- ❌ **Selectivity Analysis**: ยังไม่คำนวณ discrimination ระหว่าง breaker
    
- ❌ **Harmonic Analysis**: ยังไม่คำนวณ harmonic distortion
    
- ❌ **Voltage Unbalance**: ยังไม่คำนวณ unbalance ในระบบ 3 เฟส
    

## **ระบบพิเศษ**

- ❌ **Lightning Protection (LPS)**: ยังไม่ออกแบบระบบป้องกันฟ้าผ่า (IEC 62305)
    
- ❌ **Fire Alarm System**: ยังไม่รวมวงจรแจ้งเหตุเพลิงไหม้
    
- ❌ **CCTV & Security**: ยังไม่รวมวงจรกล้องวงจรปิด
    
- ❌ **Building Automation**: ยังไม่รวม smart home / BMS
    
- ❌ **Emergency Power**: ยังไม่ออกแบบระบบไฟฉุกเฉิน/UPS
    

## **การออกแบบรายละเอียด**

- ❌ **Underground Cable Design**: ยังไม่คำนวณสายใต้ดินแบบละเอียด
    
    - ใช้ตาราง วสท. 5-23 แบบง่าย
        
- ❌ **Detailed Lighting Design**: ยังไม่คำนวณ lux level, uniformity
    
    - ใช้ template โหลดแสงสว่างแบบคร่าวๆ
        
- ❌ **Cable Tray Sizing**: ยังไม่คำนวณขนาด Cable Tray
    
- ❌ **Conduit Fill Optimization**: ใช้ Fill Factor แบบ conservative (40% max)
    

## **มาตรฐานพิเศษ**

- ❌ **ATEX/Hazardous Area**: ยังไม่รองรับพื้นที่เสี่ยงระเบิด
    
- ❌ **Medical Facilities**: ยังไม่รองรับโรงพยาบาล (IT earthing system)
    
- ❌ **Data Center**: ยังไม่รองรับห้อง Server แบบพิเศษ
    

---

## **1.6 How RAG Should Use This Document**

## **ขั้นตอนการใช้งาน**

1. **ตรวจสอบ building_type**: ก่อนสร้าง ProjectInputSpec
    
    - ถ้า user ขอโรงงาน → ปฏิเสธทันที
        
    - ถ้าขอบ้าน 4 ชั้น → แจ้งว่ารองรับแค่ 3 ชั้น
        
2. **ตรวจสอบ voltage_system**: ก่อนกำหนด electrical_system
    
    - ถ้า user ขอ 3 เฟส → แจ้งว่ายังไม่เปิดใช้ใน demo
        
    - Default เป็น TH_1PH_230V + TT
        
3. **ตรวจสอบโหลดรวม**: ก่อนส่งให้ MCP
    
    - ถ้าเกิน 35 kVA → แนะนำแยก MDB หรือใช้ 3 เฟส
        
4. **ตรวจสอบจำนวน**: circuits, rooms, loads
    
    - ถ้าเกินขีดจำกัด → แจ้ง user ให้ลดหรือแบ่งโซน
        

## **Error Response Templates**

text

`User: "ออกแบบโรงงาน 500 kVA" RAG: "ขออภัย MCP นี้รองรับเฉพาะบ้านพักอาศัย (Residential) ไม่รองรับโรงงานอุตสาหกรรม" User: "บ้าน 3 เฟส 400V" RAG: "ระบบ 3 เฟส 400V รองรับแล้ว แต่ยังไม่เปิดใช้ใน demo version นี้ ปัจจุบันใช้ได้เฉพาะ 1 เฟส 230V" User: "บ้าน 50 ห้อง" RAG: "MCP รองรับบ้านขนาดสูงสุด 35 ห้อง กรณีของท่านอาจต้องแบ่งเป็นหลาย MDB หรือปรึกษาวิศวกร"`

## **Default Behaviors**

- ถ้า user ไม่ระบุ building_type → ใช้ `RESIDENTIAL_SINGLE_2F` (ทั่วไปที่สุด)
    
- ถ้า user ไม่ระบุ voltage_system → ใช้ `TH_1PH_230V`
    
- ถ้า user ไม่ระบุ earthing → ใช้ `TT`
    
- ถ้า user ไม่ระบุ rule_profile_id → ใช้ `TH_RESIDENTIAL_LV`
    

---

## **1.7 Version & Roadmap**

## **Current Version: v1.0 (Demo)**

- รองรับบ้านพักอาศัย 1 เฟสเท่านั้น
    
- มาตรฐาน วสท. 2564 core features
    

## **Planned Features (v2.0)**

- เปิดใช้งาน 3 เฟส 400V พร้อม load balancing
    
- คำนวณ Short-Circuit และ Selectivity
    
- รองรับ underground cable design แบบละเอียด
    
- เพิ่ม building_type: อพาร์ทเมนต์ขนาดเล็ก
    

## **Future Considerations (v3.0+)**

- Lightning Protection System (IEC 62305)
    
- Lighting Design แบบละเอียด (lux calculation)
    
- Integration กับ BIM/Revit
    
- Solar + Battery System