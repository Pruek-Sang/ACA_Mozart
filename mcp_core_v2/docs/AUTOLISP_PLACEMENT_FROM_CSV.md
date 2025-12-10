# 🏠 คู่มือการวางอุปกรณ์และสร้าง AutoLISP (ตรงกับ catalog_rows.csv ทุกอย่าง)
**เอกสารฉบับนี้สร้างจากข้อมูลจริงใน catalog_rows.csv - ไม่มีการสมมติใดๆ**
**Date:** 2025-12-03
**Total Rules:** 110 items

---

## 📑 สารบัญ

1. [ภาพรวมข้อมูล](#ภาพรวมข้อมูล)
2. [PLACEMENT_RULE - กฎการวาง](#placement_rule)
3. [VALIDATION_RULE - กฎตรวจสอบ](#validation_rule)
4. [GEOMETRY_FILTER - กรองเส้นทาง](#geometry_filter)
5. [COMPONENT - อุปกรณ์](#component)
6. [ROOM_TEMPLATE - เทมเพลตห้อง](#room_template)
7. [CABLE_SPEC - ข้อมูลสาย](#cable_spec)
8. [DERATING_FACTOR - ค่าลดกระแส](#derating_factor)
9. [CIRCUIT_TEMPLATE - เทมเพลตวงจร](#circuit_template)
10. [APPLIANCE - เครื่องใช้ไฟฟ้า](#appliance)
11. [วิธีใช้ข้อมูลนี้ใน Code](#วิธีใช้)

---

## ภาพรวมข้อมูล

| ประเภทข้อมูล | จำนวน | คำอธิบาย |
|--------------|--------|----------|
| APPLIANCE | 13 | เครื่องใช้ไฟฟ้า |
| CABLE_SPEC | 6 | ข้อมูลสายไฟ (THW, XLPE) |
| CIRCUIT_TEMPLATE | 7 | เทมเพลตวงจร |
| COMPONENT | 31 | อุปกรณ์ไฟฟ้า (ปลั๊ก, โคมไฟ, สวิตช์) |
| DERATING_FACTOR | 6 | ค่าลดกระแส (อุณหภูมิ, การจับกลุ่ม) |
| DEVICE_PROFILE | 1 | โปรไฟล์อุปกรณ์ |
| ELECTRICAL_STANDARD | 1 | มาตรฐานไฟฟ้า |
| GEOMETRY_FILTER | 5 | กรองเส้นทางเดินสาย |
| PANELBOARD | 1 | ตู้ไฟ |
| PLACEMENT_RULE | 7 | กฎการวางอุปกรณ์ในห้อง |
| PROJECT_CONFIG | 1 | การตั้งค่าโปรเจกต์ |
| QA_PLAN | 3 | แผนตรวจสอบคุณภาพ |
| ROOM_TEMPLATE | 7 | เทมเพลตห้อง (ห้องนอน, ครัว, ห้องน้ำ) |
| ROUTING_RULE | 1 | กฎเดินสาย |
| VALIDATION_RULE | 11 | กฎตรวจสอบความถูกต้อง |
| ZONE_BUNDLE | 9 | ชุดอุปกรณ์ตามโซน |

---

## PLACEMENT_RULE

กฎการวางอุปกรณ์ในห้องต่างๆ (จาก catalog_rows.csv)

### RULE-BATH-OUTLET

**ID:** `84fe1a04-fdd1-4408-a046-2b0dab14dccf`

**กลยุทธ์การวาง:** PERIMETER_ALONG_WALL

**ใช้กับโซน:** BATHROOM

**อุปกรณ์:** `COMP-OUTLET-WP`

**ค่า Offset:**

- from_floor: 300 mm
- from_corner: 200 mm

**สูตรนับจำนวน:**

- ประเภท: PER_LENGTH
- จำนวนต่ำสุด: 1
- หน่วยความยาว: 4 m
- จำนวนต่อหน่วย: 1

**ระดับบังคับ:** HARD

---

### RULE-ROOM-OUTLET

**ID:** `879f8206-6411-4315-91e3-587af9a53ddc`

**กลยุทธ์การวาง:** PERIMETER_ALONG_WALL

**ใช้กับโซน:** BEDROOM, LIVING, GENERAL

**อุปกรณ์:** `COMP-OUTLET-16A`

**ค่า Offset:**

- from_floor: 300 mm
- from_corner: 200 mm

**สูตรนับจำนวน:**

- ประเภท: PER_LENGTH
- จำนวนต่ำสุด: 2
- หน่วยความยาว: 3 m
- จำนวนต่อหน่วย: 1

**ระดับบังคับ:** SOFT

---

### RULE-DOOR-SWITCH

**ID:** `9e96f7a9-46b8-4516-868d-855027842cb7`

**กลยุทธ์การวาง:** DOOR_SWITCH

**ใช้กับโซน:** BEDROOM, LIVING, KITCHEN, OFFICE

**อุปกรณ์:** `COMP-SW-1WAY`

**ค่า Offset:**

- from_jamb: 150 mm
- from_floor: 1100 mm

**ระดับบังคับ:** SOFT

---

### RULE-BATHROOM-OUTLET

**ID:** `9ec90318-6b83-48ec-985f-a05ae043f9c4`

**อุปกรณ์:** `COMP-OUTLET-WATERPROOF`

**กฎการวาง:**

- ห้อง: bathroom
- ต้องมี GFCI: ✅ ใช่
- IP Rating ต่ำสุด: IP44
- ห่างจากน้ำ: อย่างน้อย 600 mm

**ระดับบังคับ:** HARD

---

### RULE-ROOM-LIGHTING

**ID:** `c6d60af3-e2b5-4d59-b015-e024c9fb68c4`

**อุปกรณ์:** `COMP-CEILING-24W`

**กฎการวาง:**

- ห้อง: all

**ระดับบังคับ:** SOFT

---

### RULE-KITCHEN-OUTLET

**ID:** `d671a229-085c-47d2-b427-238046ee0451`

**อุปกรณ์:** `COMP-OUTLET-16A`

**กฎการวาง:**

- ห้อง: kitchen
- ห่างจากซิงค์: อย่างน้อย 300 mm
- ระยะห่างสูงสุด: 1.2 m
- ระยะห่างต่ำสุด: 0.6 m
- ตำแหน่งติดตั้ง: above_countertop

**ระดับบังคับ:** HARD

---

### RULE-LIVING-OUTLET

**ID:** `f96c4259-edf7-4342-a91e-52ed22bbc7e8`

**อุปกรณ์:** `COMP-OUTLET-16A`

**กฎการวาง:**

- ห้อง: living_room, bedroom
- ระยะห่างสูงสุด: 3.6 m
- ระยะห่างต่ำสุด: 1 m
- ห่างจากมุม: อย่างน้อย 150 mm

**ระดับบังคับ:** SOFT

---

## VALIDATION_RULE

กฎตรวจสอบความถูกต้อง

### VALID-OUTLET-MIN-HEIGHT

**ID:** `12976361-b2fc-4ab2-bec1-49e0d92a8791`

**Rule ID:** `VR001`

**Logic:**

- ประเภท: numeric_range
- ใช้กับ: COMPONENT, PLACEMENT_RULE
- Field เป้าหมาย: `attributes.mount_height_mm`
- ระดับ Error: ERROR
- พารามิเตอร์:
  - max_value_mm: 1200
  - min_value_mm: 300
- มาตรฐานอ้างอิง: EIT / กฟน./กฟภ. คู่มือออกแบบระบบไฟฟ้า

---

### VAL-CLEARANCE

**ID:** `3cd482fa-d867-4db5-b040-9c7d35fe1f9c`

**Logic:**


---

### VALID-CIRCUIT-VDROP-3PCT

**ID:** `3f6d7d36-4a2d-4160-ace0-e6735de43d8d`

**Rule ID:** `VR004`

**Logic:**

- ประเภท: voltage_drop_check
- ใช้กับ: CIRCUIT_TEMPLATE, ROUTE_PLAN
- ระดับ Error: ERROR
- พารามิเตอร์:
  - base_voltage_v: 230
  - max_voltage_drop_pct: 3
- มาตรฐานอ้างอิง: IEC 60364-5-52 / Voltage drop

---

### VAL-LAYER-LIGHT

**ID:** `575423d5-f92b-4f56-8c00-a095301610a1`

**Logic:**


---

### VALID-SWITCH-HEIGHT-RANGE

**ID:** `5ab77976-b3fb-4d6f-b38e-aedbf8282173`

**Rule ID:** `VR002`

**Logic:**

- ประเภท: numeric_range
- ใช้กับ: COMPONENT, PLACEMENT_RULE
- Field เป้าหมาย: `attributes.mount_height_mm`
- ระดับ Error: WARNING
- พารามิเตอร์:
  - max_value_mm: 1400
  - min_value_mm: 1100
- มาตรฐานอ้างอิง: EIT / ทางปฏิบัติทั่วไปอาคารพักอาศัย

---

### VALID-CIRCUIT-LOAD-80PCT

**ID:** `638eacc9-4ffb-4b40-a0ae-1e0cd5370198`

**Rule ID:** `VR005`

**Logic:**

- ประเภท: ratio_limit
- ใช้กับ: CIRCUIT_TEMPLATE
- ระดับ Error: WARNING
- พารามิเตอร์:
  - max_load_pct_of_breaker: 80
- มาตรฐานอ้างอิง: การออกแบบทั่วไป / good engineering practice

---

### VALID-BATHROOM-OUTLET-ZONE

**ID:** `659147fe-f54e-4b9a-8f2a-ba42c043a8d2`

**Rule ID:** `VR003`

**Logic:**

- ประเภท: compound_check
- ใช้กับ: COMPONENT, PLACEMENT_RULE
- ระดับ Error: ERROR
- พารามิเตอร์:
  - min_ip_rating: IP44
  - min_distance_from_water_mm: 600
- มาตรฐานอ้างอิง: IEC 60364-7-701 / ห้องน้ำ

---

### VAL-VD-230V

**ID:** `9d3c940f-2b6e-4362-9309-3fe2fca4cceb`

**Logic:**


---

### VAL-VD-400V-3P

**ID:** `a40eb85d-1054-47eb-ada0-ed53f9b83726`

**Logic:**


---

### VAL-LAYER-SWITCH

**ID:** `b8b5b538-7b7b-4b5d-b1cd-b65f0bd0e673`

**Logic:**


---

### VAL-LAYER-OUTLET

**ID:** `c0796503-ae14-4e6d-bc9c-445ffb4cfcd6`

**Logic:**


---

## COMPONENT

อุปกรณ์ไฟฟ้าทั้งหมด

| ชื่อ | Block Name | Layer Out | Mount Height (mm) | Rated (A/W) |
|------|------------|-----------|-------------------|-------------|
| Air conditioner ~1.1 kW | `E_AC_12000` | `E-HEAVY-GEN` | 2200 | 1100W |
| โคมไฟดาวน์ไลท์ LED 24W | `DOWNLIGHT_LED_24W` | `ELECTRICAL_LIGHTING` | 2700 | - |
| Ceiling fan 60 W | `E_CEILING_FAN_60W` | `E-LIGHT-GEN` | 2600 | 60W |
| Dimmer | `E_DIMMER` | `E-SWITCH-GEN` | 1100 | - |
| Doorbell | `E_DOORBELL` | `E-LOWVOLT-GEN` | 1400 | - |
| โคมไฟดาวน์ไลท์ LED 9W | `DOWNLIGHT_LED_9W` | `ELECTRICAL_LIGHTING` | 2700 | - |
| Conduit EMT 1/2" path element | `E_CONDUIT_EMT12` | `E-CONDUIT-GEN` | 2600 | - |
| Exhaust fan 25 W | `E_EXHAUST_25W` | `E-LIGHT-GEN` | 2200 | 25W |
| Gate motor | `E_GATE_MOTOR` | `E-HEAVY-GEN` | 0 | 500W |
| Ground rod | `E_GROUND_ROD` | `E-GROUND-GEN` | 0 | - |
| Handy box (flush) | `E_BOX_HANDY` | `E-BOX-GEN` | 300 | - |
| Induction hob 3.5 kW | `E_HOB_3K5` | `E-HEAVY-GEN` | 900 | 3500W |
| Junction box (ceiling) | `E_BOX_JB` | `E-BOX-GEN` | 2600 | - |
| KWh meter (utility) | `E_KWH_METER` | `E-METER-GEN` | 1600 | 100A |
| Load center / Consumer unit | `E_LOAD_CENTER` | `E-PANEL-GEN` | 1600 | 100A |
| Main breaker 100A | `E_MAIN_MCB` | `E-PANEL-GEN` | 1600 | 100A |
| เต้ารับ 2 ช่อง 16A | `OUTLET_16A_2GANG` | `ELECTRICAL_OUTLETS` | 300 | - |
| Single outlet 20A (dedicated) | `E_OUTLET_20A` | `E-OUTLET-GEN` | 300 | 20A |
| LAN outlet (RJ45) | `E_OUTLET_RJ45` | `E-LOWVOLT-GEN` | 300 | - |
| TV outlet (coax) | `E_OUTLET_TV` | `E-LOWVOLT-GEN` | 300 | - |
| เต้ารับกันน้ำ IP65 | `OUTLET_WATERPROOF_IP65` | `ELECTRICAL_OUTLETS` | 300 | - |
| Weatherproof outlet (IP54) | `E_OUTLET_WP` | `E-OUTLET-GEN` | 300 | 16A |
| Electric oven 3.0 kW | `E_OVEN_3K0` | `E-HEAVY-GEN` | 900 | 3000W |
| Water pump 0.75 kW | `E_PUMP_750W` | `E-HEAVY-GEN` | 0 | 750W |
| Surge protector (SPD) | `E_SPD` | `E-PANEL-GEN` | 1600 | - |
| Surface box | `E_BOX_SURFACE` | `E-BOX-GEN` | 300 | - |
| Light switch 1-way | `E_SWITCH_1WAY` | `E-SWITCH-GEN` | 1100 | - |
| Light switch 2-way | `E_SWITCH_2WAY` | `E-SWITCH-GEN` | 1100 | - |
| สวิตช์ 1 ทาง | `SWITCH_1GANG` | `ELECTRICAL_SWITCHES` | 1200 | - |
| Wall lamp 12W ~1000 lm | `E_WALL_LAMP_12W` | `E-LIGHT-GEN` | 1600 | 12W |
| Instant water heater 3.5 kW | `E_WATER_HEATER_3K5` | `E-HEAVY-GEN` | 1500 | 3500W |

---

## ROOM_TEMPLATE

เทมเพลตห้องต่างๆ

### Template ห้องน้ำมาตรฐาน

**Template Code:** `RT004`

**ประเภทห้อง:** bathroom

**เครื่องใช้มาตรฐาน:**

- APP006-WATER-HEATER-4_5KW
- APP010-HAIR-DRYER-2000W

---

### Template ห้องนั่งเล่นมาตรฐาน

**Template Code:** `RT002`

**ประเภทห้อง:** living_room

**เครื่องใช้มาตรฐาน:**

- APP001-TV-55IN

---

### Template ห้องครัวมาตรฐาน

**Template Code:** `RT003`

**ประเภทห้อง:** kitchen

**เครื่องใช้มาตรฐาน:**

- APP002-FRIDGE-2DOOR
- APP003-MICROWAVE-20L
- APP007-RICE-COOKER-1L
- APP008-KETTLE-1_7L

---

### Template ห้องซักผ้า

**Template ID:** `RT006`

**ประเภทห้อง:** laundry_room

**เครื่องใช้ทั่วไป:**

- เครื่องซักผ้า 8 kg
- เครื่องอบผ้า 4,000W (ตัวเลือก)

**ข้อกำหนดตามมาตรฐาน:**

- require_rcbo: True
- min_receptacles: 2
- rcbo_sensitivity_ma: 30
- max_voltage_drop_percent: 3

---

### Template ห้องยูทิลิตี้ / ปั๊มน้ำ

**Template ID:** `RT005`

**ประเภทห้อง:** utility_room

**เครื่องใช้ทั่วไป:**

- ปั๊มน้ำ 1 HP

**ข้อกำหนดตามมาตรฐาน:**

- require_rcbo: True
- min_receptacles: 1
- rcbo_sensitivity_ma: 30
- max_voltage_drop_percent: 3

---

### Template ห้องนอนมาตรฐาน

**Template Code:** `RT001`

**ประเภทห้อง:** bedroom

**เครื่องใช้มาตรฐาน:**

- APP001-TV-55IN
- APP009-PC-GAMING

---

### Template: สระว่ายน้ำ (Swimming Pool)

**Template ID:** `RT_POOL001`

**ประเภทห้อง:** swimming_pool

**ข้อกำหนดตามมาตรฐาน:**

- bonding_points: ['pool_reinforcing_steel', 'metal_pool_shell', 'metal_fittings', 'metal_handrails', 'metal_ladders', 'metal_diving_board', 'pump_motor', 'metal_conduit', 'pool_water_via_bonding_lug']
- bonding_required: True
- gfci_test_monthly: True
- gfci_sensitivity_ma: 30
- transformer_location: min_1.5m_from_pool_outside_zone_2
- bonding_grid_required: True
- gfci_protection_required: True
- overhead_clearance_min_m: 7.5
- bonding_conductor_min_mm2: 6
- emergency_shutoff_accessible: True
- transformer_isolation_required: True
- underwater_lighting_max_voltage_v: 12
- grounding_electrode_system_required: True
- receptacles_min_distance_from_pool_m: 3

---

## CABLE_SPEC

ข้อมูลสายไฟทั้งหมด

| Cable ID | Size (mm²) | Insulation | Ampacity (A) | Resistance (Ω/km@20°C) | Price (฿/m) |
|----------|------------|------------|--------------|------------------------|-------------|
| CS001 | 1.5 | PVC-THW | 18 | 12.1 | 5.5 |
| CS004 | 1.5 | Nylon-coated PVC (THHN) | 20 | 12.1 | 6.5 |
| CS002 | 2.5 | PVC-THW | 24 | 7.41 | 8.5 |
| CS004 | 4 | PVC-THW | 32 | 4.61 | 13 |
| CS005 | 10 | XLPE | 64 | 1.83 | 45 |
| CS005 | 10 | Cross-linked Polyethylene (XLPE) | 64 | 1.83 | 35 |

---

## DERATING_FACTOR

ค่าลดกระแสตามเงื่อนไขต่างๆ

### ค่าลดกระแสเมื่อสายวิ่งผ่านฉนวนกันความร้อน

**Factor ID:** `DF004`

**ประเภท:** thermal_insulation

**มาตรฐาน:** IEC 60364-5-52

**ตารางค่าลด:**

| derating_factor | insulation_thickness_mm |
|---|---|
| 1 | 0 |
| 0.85 | 50 |
| 0.75 | 100 |
| 0.6 | 200 |

---

### ตัวคูณลดกระแสเมื่อฝังดินตามค่าความต้านทานความร้อนของดิน

**Factor ID:** `DF003`

**ประเภท:** soil_burial

**มาตรฐาน:** IEC 60287 / IEC 60364-5-52

**ตารางค่าลด:**

| factor | soil_resistivity_km_per_w |
|---|---|
| 1 | 1 |
| 0.9 | 1.5 |
| 0.8 | 2 |
| 0.7 | 2.5 |

---

### Ambient Temperature Correction (DF002)

**Factor ID:** `DF002`

**ประเภท:** ambient_temperature

**มาตรฐาน:** NEC Table 310.15(B)(2)(a)

**ตารางค่าลด:**

| ambient_temp_c | derating_factor_60c | derating_factor_75c | derating_factor_90c |
|---|---|---|---|
| 30 | 1 | 1 | 1 |
| 35 | 0.91 | 0.94 | 0.96 |
| 40 | 0.82 | 0.88 | 0.91 |
| 45 | 0.71 | 0.82 | 0.87 |
| 50 | 0.58 | 0.75 | 0.82 |

---

### ตัวคูณลดกระแสตามอุณหภูมิโดยรอบ

**Factor ID:** `DF002`

**ประเภท:** ambient_temperature

**มาตรฐาน:** IEC 60364-5-52 Table B.52.x

**ตารางค่าลด:**

| factor | max_temp_c | min_temp_c |
|---|---|---|
| 1 | 40 | 30 |
| 0.94 | 45 | 41 |
| 0.88 | 50 | 46 |
| 0.82 | 55 | 51 |
| 0.76 | 60 | 56 |
| 0.61 | 70 | 61 |

---

### Thermal Insulation Derating (DF004)

**Factor ID:** `DF004`

**ประเภท:** thermal_insulation

**มาตรฐาน:** IEC 60364-5-52

**ตารางค่าลด:**

| derating_factor | insulation_thickness_mm |
|---|---|
| 1 | 0 |
| 0.85 | 50 |
| 0.75 | 100 |
| 0.6 | 200 |

---

### ตัวคูณลดกระแส เมื่อเดินหลายสายร่วมท่อ/ราง

**Factor ID:** `DF001`

**ประเภท:** conductor_grouping

**มาตรฐาน:** IEC 60364-5-52 / EIT

**ตารางค่าลด:**

| factor | max_conductors | min_conductors |
|---|---|---|
| 1 | 3 | 1 |
| 0.8 | 6 | 4 |
| 0.7 | 9 | 7 |
| 0.5 | 20 | 10 |
| 0.4 | 30 | 21 |

---

## GEOMETRY_FILTER

กรองเส้นทางเดินสาย

### หลีกเลี่ยงการเดินท่อใน Zone 1 และ Zone 2 ของห้องน้ำ

**Filter ID:** `GF004`

**ประเภทการเดินสาย:** bathroom

**รวม Entity:** BATHROOM_WALL, BATHROOM_CEILING

**ไม่รวม Entity:** BATHROOM_ZONE1, BATHROOM_ZONE2

**หลีกเลี่ยงโซน:** BATHROOM_ZONE0, BATHROOM_ZONE1, BATHROOM_ZONE2

**เส้นทางที่แนะนำ:** ZONE3_ONLY

**ค่าเบี่ยงเบนสูงสุด:** 100 mm

---

### กรองเส้นทางท่อเดินตามผนัง

**Filter ID:** `GF002`

**ประเภทการเดินสาย:** wall_conduit

**รวม Entity:** WALL_AXIS, WALL_FACE

**ไม่รวม Entity:** WINDOW, DOOR, COLUMN

**หลีกเลี่ยงโซน:** OPENING, STRUCT_COLUMN

**เส้นทางที่แนะนำ:** WALL_AXIS

**ค่าเบี่ยงเบนสูงสุด:** 50 mm

---

### Whitelist entities for walls

**รวม Entity:** LINE, LWPOLYLINE, ARC

**ไม่รวม Entity:** TEXT, MTEXT, DIMENSION, HATCH

---

### กรองเส้นทางเดินสายบนฝ้าเพดาน

**Filter ID:** `GF001`

**ประเภทการเดินสาย:** ceiling

**รวม Entity:** CEILING_GRID, CABLE_TRAY, CABLE_LADDER

**ไม่รวม Entity:** STRUCT_COLUMN, STRUCT_BEAM, SKYLIGHT

**หลีกเลี่ยงโซน:** NO-ROUTE-ZONE

**เส้นทางที่แนะนำ:** CEILING_GRID, CABLE_TRAY

**ค่าเบี่ยงเบนสูงสุด:** 300 mm

---

### กรองเส้นทางราง/ท่อใต้ดิน

**Filter ID:** `GF003`

**ประเภทการเดินสาย:** underground

**รวม Entity:** TRENCH_CENTERLINE

**ไม่รวม Entity:** BUILDING_FOOTPRINT, PILE_CAP

**หลีกเลี่ยงโซน:** FOUNDATION_ZONE

**เส้นทางที่แนะนำ:** TRENCH_CENTERLINE

**ค่าเบี่ยงเบนสูงสุด:** 500 mm

---

