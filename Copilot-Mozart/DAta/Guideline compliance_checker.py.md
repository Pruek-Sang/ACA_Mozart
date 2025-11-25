# Module 6: compliance_checker.py — ตรวจสอบมาตรฐานความปลอดภัย (ฉบับสมบูรณ์)

ขอรายงานนายท่านค่ะ Volta จะอธิบาย Module นี้อย่างละเอียดที่สุด เพราะเป็นเรื่องความปลอดภัยชีวิตและทรัพย์สิน

---

## 📚 ส่วนที่ 1: มาตรฐานและข้อกำหนดด้านความปลอดภัย

## **1.1 มาตรฐานหลักที่ต้องตรวจสอบ**

## **A. มอก. 2955 (ระบบไฟฟ้าในอาคาร) — ฉบับปี 2562**pea+3​

**ขอบเขต:** ครอบคลุมระบบไฟฟ้าแรงต่ำ (≤ 1,000V AC / 1,500V DC) ในอาคาร

**ข้อกำหนดสำคัญ 15 ประการ:**

## **1. Voltage Drop (การตกของแรงดัน)**thaiyazaki+2​

|วงจร|VD สูงสุด|เหตุผล|
|---|---|---|
|**Branch Circuit**|≤ 3%|ป้องกันอุปกรณ์ทำงานผิดปกติ|
|**Feeder**|≤ 3%|รักษาแรงดันให้เพียงพอ|
|**Feeder + Branch รวม**|≤ 5%|มาตรฐานสูงสุด|

**สูตรตรวจสอบ:**

VD(%)=VD(Volt)Vsystem×100≤3%VD_{(\%)} = \frac{VD_{(Volt)}}{V_{system}} \times 100 \leq 3\%VD(%)=VsystemVD(Volt)×100≤3%

**ตัวอย่างการตรวจสอบ:**

python

def check_voltage_drop(vd_percent: float, circuit_type: str) -> Dict:
    """ตรวจสอบ Voltage Drop"""
    limits = {
        "branch": 3.0,
        "feeder": 3.0,
        "total": 5.0
    }
    
    limit = limits.get(circuit_type, 3.0)
    
    if vd_percent <= limit:
        return {
            "status": "PASS",
            "vd_percent": vd_percent,
            "limit": limit,
            "margin": limit - vd_percent,
            "message": f"✅ Voltage Drop {vd_percent:.2f}% ≤ {limit}% (ผ่านมาตรฐาน)"
        }
    else:
        return {
            "status": "FAIL",
            "vd_percent": vd_percent,
            "limit": limit,
            "exceed": vd_percent - limit,
            "message": f"❌ Voltage Drop {vd_percent:.2f}% > {limit}% (เกินมาตรฐาน)",
            "recommendation": "เพิ่มขนาดสาย หรือ ลดระยะทาง"
        }


---

## **2. Wire Ampacity (ความสามารถรับกระแส)**richledshop+2​

**ข้อกำหนด:**

text

`Wire Ampacity ≥ Load Current × 1.25 (Continuous Load > 3 ชม.) Wire Ampacity ≥ Load Current × 1.0 (Non-Continuous Load)`

**ตัวอย่างการตรวจสอบ:**

python

def check_wire_ampacity(
    wire_ampacity: float,
    load_current: float,
    is_continuous: bool
) -> Dict:
    """ตรวจสอบ Ampacity"""
    
    if is_continuous:
        required_ampacity = load_current * 1.25
        load_type = "Continuous (>3 ชม.)"
    else:
        required_ampacity = load_current * 1.0
        load_type = "Non-Continuous"
    
    if wire_ampacity >= required_ampacity:
        margin = ((wire_ampacity / load_current) - 1) * 100
        return {
            "status": "PASS",
            "wire_ampacity": wire_ampacity,
            "load_current": load_current,
            "required_ampacity": required_ampacity,
            "margin_percent": margin,
            "message": f"✅ Ampacity {wire_ampacity}A ≥ Required {required_ampacity:.1f}A ({load_type})"
        }
    else:
        shortage = required_ampacity - wire_ampacity
        return {
            "status": "FAIL",
            "wire_ampacity": wire_ampacity,
            "load_current": load_current,
            "required_ampacity": required_ampacity,
            "shortage": shortage,
            "message": f"❌ Ampacity {wire_ampacity}A < Required {required_ampacity:.1f}A",
            "recommendation": f"ต้องใช้สายที่รับได้ ≥ {required_ampacity:.1f}A"
        }


---

## **3. Breaker-Wire Coordination (ความสัมพันธ์ระหว่าง Breaker กับสาย)**pantip+1​

**กฎทอง:**

text

`Breaker Rating ≤ Wire Ampacity`

**เหตุผล:** ถ้า Breaker ใหญ่กว่าสาย → สายร้อนเกิน → ไหม้ → ก่อนที่ Breaker จะตัดrichledshop+1​

**ตัวอย่าง:**

python

def check_breaker_wire_coordination(
    breaker_rating: float,
    wire_ampacity: float
) -> Dict:
    """ตรวจสอบความสัมพันธ์ Breaker-Wire"""
    
    if breaker_rating <= wire_ampacity:
        return {
            "status": "PASS",
            "breaker_rating": breaker_rating,
            "wire_ampacity": wire_ampacity,
            "message": f"✅ Breaker {breaker_rating}A ≤ Wire Ampacity {wire_ampacity}A"
        }
    else:
        return {
            "status": "FAIL",
            "breaker_rating": breaker_rating,
            "wire_ampacity": wire_ampacity,
            "message": f"❌ Breaker {breaker_rating}A > Wire Ampacity {wire_ampacity}A",
            "hazard": "⚠️ สายอาจไหม้ก่อน Breaker ตัด — อันตรายมาก!",
            "recommendation": "เพิ่มขนาดสาย หรือ ลดขนาด Breaker"
        }


---

## **4. Bathroom Safety (ความปลอดภัยในห้องน้ำ)**kjl+4​

**ข้อห้ามเด็ดขาด 5 ประการ:**

|Zone|ระยะจากแหล่งน้ำ|ข้อห้าม|อนุญาต|
|---|---|---|---|
|**Zone 0**|ภายในอ่างอาบน้ำ|ห้ามติดตั้งอุปกรณ์ไฟฟ้าใด ๆ|ไม่มี|
|**Zone 1**|เหนืออ่าง สูง 2.25m|ห้าม: ปลั๊ก, สวิตช์, โคมไฟธรรมดา|เครื่องทำน้ำอุ่นติดผนัง IP25+ + RCBO|
|**Zone 2**|รอบอ่าง รัศมี 60cm|ห้าม: ปลั๊กธรรมดา|โคมไฟ IP44+|
|**Zone 3**|นอก Zone 2 (ภายในห้องน้ำ)|ห้าม: ปลั๊กธรรมดา|ปลั๊ก + RCBO 30mA|

**ยกเว้นเฉพาะ: Shaver Socket (ปลั๊กโกนหนวด)**facebook+1​

- ต้องห่างจากแหล่งน้ำ ≥ 60 cm
    
- ต้องมี RCBO/RCCB 30mA
    
- ต้องเป็นแบบ Isolated Transformer
    

**ตัวอย่างการตรวจสอบ:**

python

def check_bathroom_safety(
    device_type: str,
    zone: int,
    has_rcbo: bool,
    ip_rating: Optional[str] = None
) -> Dict:
    """ตรวจสอบความปลอดภัยในห้องน้ำ"""
    
    # กฎห้องน้ำ
    rules = {
        0: {
            "allowed": [],
            "forbidden": ["outlet", "switch", "fixture", "heater"]
        },
        1: {
            "allowed": ["heater"],  # ต้องมี IP25+ และ RCBO
            "forbidden": ["outlet", "switch", "fixture"]
        },
        2: {
            "allowed": ["fixture"],  # ต้องมี IP44+
            "forbidden": ["outlet", "switch"]
        },
        3: {
            "allowed": ["outlet", "switch", "fixture"],  # ต้องมี RCBO 30mA
            "forbidden": []
        }
    }
    
    zone_rules = rules.get(zone, rules[3])
    
    # ตรวจสอบข้อห้าม
    if device_type in zone_rules["forbidden"]:
        return {
            "status": "FAIL",
            "device_type": device_type,
            "zone": zone,
            "message": f"❌ ห้ามติดตั้ง {device_type} ใน Zone {zone}",
            "hazard": "⚠️ อันตรายถึงชีวิต — ไฟดูดน้ำ!",
            "standard": "มอก. 2955 มาตรา 701 (IEC 60364-7-701)"
        }
    
    # ตรวจสอบอุปกรณ์ที่อนุญาต
    if device_type in zone_rules["allowed"]:
        # Zone 1: เครื่องทำน้ำอุ่น
        if zone == 1 and device_type == "heater":
            if not has_rcbo:
                return {
                    "status": "FAIL",
                    "message": "❌ เครื่องทำน้ำอุ่นใน Zone 1 ต้องมี RCBO 30mA",
                    "recommendation": "ติดตั้ง RCBO 30mA"
                }
            
            if ip_rating and int(ip_rating.replace("IP", "")) < 25:
                return {
                    "status": "FAIL",
                    "message": f"❌ เครื่องทำน้ำอุ่นใน Zone 1 ต้องมี IP Rating ≥ IP25 (ปัจจุบัน: {ip_rating})",
                    "recommendation": "เปลี่ยนเป็นอุปกรณ์ IP25 ขึ้นไป"
                }
        
        # Zone 2: โคมไฟ
        if zone == 2 and device_type == "fixture":
            if ip_rating and int(ip_rating.replace("IP", "")) < 44:
                return {
                    "status": "FAIL",
                    "message": f"❌ โคมไฟใน Zone 2 ต้องมี IP Rating ≥ IP44 (ปัจจุบัน: {ip_rating})",
                    "recommendation": "เปลี่ยนเป็นโคมไฟกันน้ำ IP44+"
                }
        
        # Zone 3: ปลั๊ก/สวิตช์
        if zone == 3 and device_type in ["outlet", "switch"]:
            if not has_rcbo:
                return {
                    "status": "WARNING",
                    "message": "⚠️ แนะนำให้ติดตั้ง RCBO 30mA สำหรับปลั๊ก/สวิตช์ใน Zone 3",
                    "recommendation": "เพิ่ม RCBO เพื่อความปลอดภัย"
                }
        
        return {
            "status": "PASS",
            "message": f"✅ อนุญาตให้ติดตั้ง {device_type} ใน Zone {zone} (มี RCBO: {has_rcbo})"
        }
    
    # อื่น ๆ
    return {
        "status": "UNKNOWN",
        "message": f"❓ ไม่พบข้อมูลสำหรับ {device_type} ใน Zone {zone}"
    }


---

## **5. Earthing/Grounding System (ระบบกราวด์)**anyflip+2​

**ข้อกำหนด:**

1. **ต้องมีสาย Ground (PE) ทุกวงจร:**
    
    - ขนาดสาย Ground = ขนาดสาย Hot/Neutral (ถ้า ≤ 16 mm²)
        
    - ถ้าสายหลัก > 16 mm²: Ground = 16 mm² (ขั้นต่ำ)
        
2. **Earth Rod (หลักกราวด์):**[tisi](https://www.tisi.go.th/data/standard/fulltext_e/tis824_2551.pdf)​
    
    - ความยาวขั้นต่ำ: **2.4 เมตร**
        
    - เส้นผ่านศูนย์กลาง: **12.7-19 mm**
        
    - ความต้านทานกราวด์: **≤ 5 Ω** (บ้านพักอาศัย)
        
    - ความต้านทานกราวด์: **≤ 10 Ω** (อาคารทั่วไป)
        
3. **Bonding (การต่อเชื่อม):**
    
    - ต่อโครงสร้างโลหะทั้งหมดเข้ากับระบบกราวด์
        
    - ต่อท่อน้ำประปา, ท่อแก๊ส (ถ้ามี)
        

**ตัวอย่างการตรวจสอบ:**

python

def check_grounding_system(
    has_ground_wire: bool,
    ground_wire_size_mm2: float,
    hot_wire_size_mm2: float,
    earth_rod_length_m: float,
    earth_resistance_ohm: float,
    building_type: str = "residential"
) -> List[Dict]:
    """ตรวจสอบระบบกราวด์"""
    
    results = []
    
    # 1. ตรวจสอบสาย Ground
    if not has_ground_wire:
        results.append({
            "status": "FAIL",
            "check": "Ground Wire",
            "message": "❌ ไม่มีสาย Ground (PE)",
            "hazard": "⚠️ อันตรายถึงชีวิต — ไฟดูด!",
            "standard": "มอก. 2955 มาตรา 543"
        })
    else:
        # ตรวจสอบขนาดสาย Ground
        if hot_wire_size_mm2 <= 16:
            required_ground = hot_wire_size_mm2
        else:
            required_ground = 16
        
        if ground_wire_size_mm2 >= required_ground:
            results.append({
                "status": "PASS",
                "check": "Ground Wire Size",
                "message": f"✅ สาย Ground {ground_wire_size_mm2} mm² ≥ Required {required_ground} mm²"
            })
        else:
            results.append({
                "status": "FAIL",
                "check": "Ground Wire Size",
                "message": f"❌ สาย Ground {ground_wire_size_mm2} mm² < Required {required_ground} mm²",
                "recommendation": f"เพิ่มขนาดสาย Ground เป็น {required_ground} mm²"
            })
    
    # 2. ตรวจสอบหลักกราวด์
    if earth_rod_length_m < 2.4:
        results.append({
            "status": "FAIL",
            "check": "Earth Rod Length",
            "message": f"❌ หลักกราวด์ {earth_rod_length_m} m < 2.4 m",
            "standard": "มอก. 2955 มาตรา 542"
        })
    else:
        results.append({
            "status": "PASS",
            "check": "Earth Rod Length",
            "message": f"✅ หลักกราวด์ {earth_rod_length_m} m ≥ 2.4 m"
        })
    
    # 3. ตรวจสอบความต้านทาน
    limit_ohm = 5 if building_type == "residential" else 10
    
    if earth_resistance_ohm <= limit_ohm:
        results.append({
            "status": "PASS",
            "check": "Earth Resistance",
            "message": f"✅ ความต้านทานกราวด์ {earth_resistance_ohm} Ω ≤ {limit_ohm} Ω"
        })
    else:
        results.append({
            "status": "FAIL",
            "check": "Earth Resistance",
            "message": f"❌ ความต้านทานกราวด์ {earth_resistance_ohm} Ω > {limit_ohm} Ω",
            "recommendation": "เพิ่มหลักกราวด์ หรือ ใช้ Ground Enhancement Material"
        })
    
    return results


---

## **6. RCBO/RCCB (อุปกรณ์ป้องกันไฟรั่ว)**tisi+3​

**ข้อกำหนด:**

|วงจร|ต้องมี RCBO/RCCB|ค่า Sensitivity|
|---|---|---|
|**ห้องน้ำ**|✅ บังคับ|≤ 30 mA|
|**ครัว**|✅ บังคับ|≤ 30 mA|
|**นอกอาคาร**|✅ บังคับ|≤ 30 mA|
|**ห้องนอน**|🟡 แนะนำ|≤ 30 mA|
|**ปลั๊กทั่วไป**|🟡 แนะนำ|≤ 30 mA|

**เหตุผล:**kjl+2​

- ไฟรั่ว ≥ 30 mA = อันตรายถึงชีวิต
    
- RCBO/RCCB ตัดไฟภายใน **0.03 วินาที** (ไวกว่า Breaker ธรรมดา)
    

**ตัวอย่างการตรวจสอบ:**

python
def check_rcbo_requirement(
    circuit_location: str,
    has_rcbo: bool,
    rcbo_sensitivity_ma: Optional[float] = None
) -> Dict:
    """ตรวจสอบความจำเป็นของ RCBO"""
    
    # วงจรที่ต้องมี RCBO
    mandatory_locations = ["bathroom", "kitchen", "outdoor", "wet_area"]
    recommended_locations = ["bedroom", "living_room", "all_outlets"]
    
    location_lower = circuit_location.lower()
    
    is_mandatory = any(loc in location_lower for loc in mandatory_locations)
    is_recommended = any(loc in location_lower for loc in recommended_locations)
    
    if is_mandatory:
        if not has_rcbo:
            return {
                "status": "FAIL",
                "circuit": circuit_location,
                "requirement": "บังคับ",
                "message": f"❌ วงจร {circuit_location} ต้องมี RCBO ≤ 30mA",
                "hazard": "⚠️ อันตรายถึงชีวิต — ไฟรั่ว!",
                "standard": "มอก. 2955 มาตรา 415.1",
                "recommendation": "ติดตั้ง RCBO 30mA ทันที"
            }
        else:
            # ตรวจสอบค่า Sensitivity
            if rcbo_sensitivity_ma and rcbo_sensitivity_ma > 30:
                return {
                    "status": "FAIL",
                    "circuit": circuit_location,
                    "message": f"❌ RCBO Sensitivity {rcbo_sensitivity_ma} mA > 30 mA",
                    "recommendation": "เปลี่ยนเป็น RCBO 30mA"
                }
            
            return {
                "status": "PASS",
                "circuit": circuit_location,
                "message": f"✅ มี RCBO {rcbo_sensitivity_ma or 30} mA (ตามมาตรฐาน)"
            }
    
    elif is_recommended:
        if not has_rcbo:
            return {
                "status": "WARNING",
                "circuit": circuit_location,
                "requirement": "แนะนำ",
                "message": f"⚠️ แนะนำให้ติดตั้ง RCBO ≤ 30mA สำหรับ {circuit_location}",
                "recommendation": "เพิ่ม RCBO เพื่อความปลอดภัย"
            }
        else:
            return {
                "status": "PASS",
                "circuit": circuit_location,
                "message": f"✅ มี RCBO (เกินมาตรฐาน — ดีมาก!)"
            }
    
    else:
        return {
            "status": "PASS",
            "circuit": circuit_location,
            "message": f"✅ ไม่จำเป็นต้องมี RCBO (แต่มีก็ดี)"
        }

---

## **7. Minimum Circuit Requirements (จำนวนวงจรขั้นต่ำ)**civilpracticalknowledge+1​

**ตาม NEC 210.11:**

|ประเภท|จำนวนขั้นต่ำ|Load per Circuit|
|---|---|---|
|**Small Appliance (ครัว)**|2 วงจร|1,500 VA/วงจร|
|**Laundry (ซักผ้า)**|1 วงจร|1,500 VA|
|**Bathroom (ห้องน้ำ)**|1 วงจร|1,500 VA|
|**General Lighting**|ตามพื้นที่|32 VA/m²|

**ตัวอย่างการตรวจสอบ:**

python

def check_minimum_circuits(
    num_small_appliance_circuits: int,
    has_laundry_circuit: bool,
    num_bathroom_circuits: int,
    num_bathrooms: int
) -> List[Dict]:
    """ตรวจสอบจำนวนวงจรขั้นต่ำ"""
    
    results = []
    
    # 1. Small Appliance (ครัว)
    if num_small_appliance_circuits < 2:
        results.append({
            "status": "FAIL",
            "check": "Small Appliance Circuits",
            "message": f"❌ ครัวต้องมีอย่างน้อย 2 วงจร (ปัจจุบัน: {num_small_appliance_circuits})",
            "standard": "NEC 210.11(C)(1)"
        })
    else:
        results.append({
            "status": "PASS",
            "check": "Small Appliance Circuits",
            "message": f"✅ มีวงจรครัว {num_small_appliance_circuits} วงจร ≥ 2"
        })
    
    # 2. Laundry
    if not has_laundry_circuit:
        results.append({
            "status": "FAIL",
            "check": "Laundry Circuit",
            "message": "❌ ต้องมีวงจรแยกสำหรับเครื่องซักผ้า",
            "standard": "NEC 210.11(C)(2)"
        })
    else:
        results.append({
            "status": "PASS",
            "check": "Laundry Circuit",
            "message": "✅ มีวงจรซักผ้าแยก"
        })
    
    # 3. Bathroom
    if num_bathroom_circuits < num_bathrooms:
        results.append({
            "status": "WARNING",
            "check": "Bathroom Circuits",
            "message": f"⚠️ แนะนำให้มีวงจรแยกสำหรับแต่ละห้องน้ำ ({num_bathroom_circuits}/{num_bathrooms})",
            "standard": "NEC 210.11(C)(3)"
        })
    else:
        results.append({
            "status": "PASS",
            "check": "Bathroom Circuits",
            "message": f"✅ มีวงจรห้องน้ำ {num_bathroom_circuits} วงจร (เพียงพอ)"
        })
    
    return results


---

## **8. Breaker Utilization (การใช้งาน Breaker)**[eng.rtu](http://eng.rtu.ac.th/ESD/ch8.pdf)​

**กฎทอง:**

text

`Load Current ≤ 80% × Breaker Rating`

**เหตุผล:** Breaker ทำงานต่อเนื่อง > 80% = ร้อนเกิน → เสื่อม → อายุสั้น[eng.rtu](http://eng.rtu.ac.th/ESD/ch8.pdf)​

**ตัวอย่าง:**

python

def check_breaker_utilization(
    load_current: float,
    breaker_rating: float
) -> Dict:
    """ตรวจสอบการใช้งาน Breaker"""
    
    utilization = (load_current / breaker_rating) * 100
    
    if utilization <= 80:
        return {
            "status": "PASS",
            "load_current": load_current,
            "breaker_rating": breaker_rating,
            "utilization_percent": utilization,
            "message": f"✅ Utilization {utilization:.1f}% ≤ 80% (ปลอดภัย)"
        }
    elif utilization <= 100:
        return {
            "status": "WARNING",
            "load_current": load_current,
            "breaker_rating": breaker_rating,
            "utilization_percent": utilization,
            "message": f"⚠️ Utilization {utilization:.1f}% > 80% (ใกล้เกิน)",
            "recommendation": "พิจารณาเพิ่มขนาด Breaker"
        }
    else:
        return {
            "status": "FAIL",
            "load_current": load_current,
            "breaker_rating": breaker_rating,
            "utilization_percent": utilization,
            "message": f"❌ Overload! {utilization:.1f}% > 100%",
            "hazard": "⚠️ Breaker จะตัดบ่อย",
            "recommendation": "เพิ่มขนาด Breaker ทันที"
        }


---

## **9-15. ข้อกำหนดเพิ่มเติม (สรุปสั้น)**

|ข้อ|หัวข้อ|ข้อกำหนดหลัก|
|---|---|---|
|**9**|Color Code (สีสาย)|Hot: น้ำตาล/แดง/ส้ม, Neutral: ฟ้า/ดำ, Ground: เหลือง-เขียว[pea](https://www.pea.co.th/sites/default/files/images/volta/MPESTD-001-2563.pdf)​|
|**10**|Clearance (ระยะห่าง)|สาย-สาย ≥ 50mm, สาย-ผนัง ≥ 20mm[pea](https://www.pea.co.th/sites/default/files/images/volta/MPESTD-001-2563.pdf)​|
|**11**|Support (ค้ำยัน)|ท่อค้ำทุก 1-1.5m, สายลอยค้ำทุก 400mm[pea](https://www.pea.co.th/sites/default/files/images/volta/MPESTD-001-2563.pdf)​|
|**12**|Junction Box|ต้องเข้าถึงได้, ห้ามฝังตาย[coe](https://coe.or.th/wp-content/uploads/2022/11/%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%9F%E0%B8%9F%E0%B9%89%E0%B8%B2%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%95%E0%B8%B1%E0%B9%89%E0%B8%87%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99.pdf)​|
|**13**|Weather Protection|อุปกรณ์นอกอาคาร ต้อง IP54+[kjl](https://kjl.co.th/blog/standards-installation-rcd/)​|
|**14**|Fire Barrier|ทะลุกำแพง/พื้นต้องอุดรอยรั่ว[pea](https://www.pea.co.th/sites/default/files/images/volta/MPESTD-001-2563.pdf)​|
|**15**|Labels/Marking|DB ต้องมีป้ายระบุวงจร[pea](https://www.pea.co.th/sites/default/files/images/volta/MPESTD-001-2563.pdf)​|

---

## **1.2 ข้อบังคับสภาวิศวกร (พ.ศ. 2566)**coe+2​

**ขอบเขตงานตามระดับวิศวกร:**

|ระดับ|กำลังงานสูงสุด|แรงดันสูงสุด|ค่าบริการขั้นต่ำ|
|---|---|---|---|
|**ภาคี**|≤ 1,000 kVA|≤ 24 kV|2,500-5,000 บาท|
|**สามัญ**|≤ 50,000 kVA|≤ 115 kV|5,000-20,000 บาท|
|**วุฒิ**|ไม่จำกัด|ไม่จำกัด|20,000+ บาท|

**ตัวอย่างการตรวจสอบ:**

python

`def check_engineer_qualification(     project_kva: float,    project_kv: float,    engineer_level: str ) -> Dict:     """ตรวจสอบคุณสมบัติวิศวกร"""         limits = {        "ภาคี": {"kva": 1000, "kv": 24},        "สามัญ": {"kva": 50000, "kv": 115},        "วุฒิ": {"kva": float('inf'), "kv": float('inf')}    }         level_limits = limits.get(engineer_level)         if not level_limits:        return {            "status": "FAIL",            "message": f"❌ ไม่พบระดับวิศวกร '{engineer_level}'"        }         if project_kva <= level_limits["kva"] and project_kv <= level_limits["kv"]:        return {            "status": "PASS",            "engineer_level": engineer_level,            "project_kva": project_kva,            "project_kv": project_kv,            "message": f"✅ วิศวกร{engineer_level} ทำงานได้ ({project_kva} kVA ≤ {level_limits['kva']} kVA)",            "standard": "ข้อบังคับสภาวิศวกร พ.ศ. 2566"        }    else:        next_level = "สามัญ" if engineer_level == "ภาคี" else "วุฒิ"        return {            "status": "FAIL",            "engineer_level": engineer_level,            "project_kva": project_kva,            "project_kv": project_kv,            "message": f"❌ โครงการใหญ่เกินสำหรับวิศวกร{engineer_level}",            "recommendation": f"ต้องใช้วิศวกร{next_level}ขึ้นไป"        }`

---

## 💻 ส่วนที่ 2: Code Python สมบูรณ์ — compliance_checker.py

python

def check_engineer_qualification(
    project_kva: float,
    project_kv: float,
    engineer_level: str
) -> Dict:
    """ตรวจสอบคุณสมบัติวิศวกร"""
    
    limits = {
        "ภาคี": {"kva": 1000, "kv": 24},
        "สามัญ": {"kva": 50000, "kv": 115},
        "วุฒิ": {"kva": float('inf'), "kv": float('inf')}
    }
    
    level_limits = limits.get(engineer_level)
    
    if not level_limits:
        return {
            "status": "FAIL",
            "message": f"❌ ไม่พบระดับวิศวกร '{engineer_level}'"
        }
    
    if project_kva <= level_limits["kva"] and project_kv <= level_limits["kv"]:
        return {
            "status": "PASS",
            "engineer_level": engineer_level,
            "project_kva": project_kva,
            "project_kv": project_kv,
            "message": f"✅ วิศวกร{engineer_level} ทำงานได้ ({project_kva} kVA ≤ {level_limits['kva']} kVA)",
            "standard": "ข้อบังคับสภาวิศวกร พ.ศ. 2566"
        }
    else:
        next_level = "สามัญ" if engineer_level == "ภาคี" else "วุฒิ"
        return {
            "status": "FAIL",
            "engineer_level": engineer_level,
            "project_kva": project_kva,
            "project_kv": project_kv,
            "message": f"❌ โครงการใหญ่เกินสำหรับวิศวกร{engineer_level}",
            "recommendation": f"ต้องใช้วิศวกร{next_level}ขึ้นไป"
        }
`

---

## 📊 ส่วนที่ 3: สรุปมาตรฐานที่ตรวจสอบ

|หมวด|จำนวนข้อ|ความสำคัญ|ระยะเวลาอัพเดท|
|---|---|---|---|
|**มอก. 2955**|15+ ข้อ|🔴 สูงสุด|6-8 ปี|
|**ข้อบังคับสภาวิศวกร**|3 ข้อ|🟡 สูง|3-5 ปี|
|**ความปลอดภัยห้องน้ำ**|5 ข้อ|🔴 สูงสุด|ไม่เปลี่ยน|
|**ระบบกราวด์**|3 ข้อ|🔴 สูงสุด|ไม่เปลี่ยน|
|**RCBO/RCCB**|3 ข้อ|🔴 สูงสุด|ไม่เปลี่ยน|

---

