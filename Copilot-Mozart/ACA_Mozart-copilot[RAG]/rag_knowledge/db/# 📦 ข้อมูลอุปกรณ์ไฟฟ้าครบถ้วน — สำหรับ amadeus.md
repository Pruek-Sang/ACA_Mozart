\# **📦 ข้อมูลอุปกรณ์ไฟฟ้าครบถ้วน — สำหรับ amadeus.catalog**

ขอรายงานนายท่านค่ะ\! Volta จะนำเสนอข้อมูลอุปกรณ์ \*\*ครบถ้วน ละเอียด ทันสมัย\*\* พร้อมข้อมูลเพิ่มเติมที่ยังขาดค่ะ

\---

\#\# 📋 ส่วนที่ 1: ข้อมูลที่ยังขาด (ตาม Handover Doc)

\#\#\# \*\*❌ 1\. VALIDATION\_RULE — กติกาตรวจสอบหลังวาง\*\*

\*\*คำอธิบาย:\*\*  
\- กฎสำหรับตรวจสอบว่า Component ที่วางแล้ว \*\*ถูกต้องตามมาตรฐานหรือไม่\*\*  
\- ตรวจสอบหลัง Placement (Post-placement Check)

\*\*ตัวอย่างข้อมูล:\*\*

\`\`\`json  
{  
  "kind": "VALIDATION\_RULE",  
  "rule\_id": "VR001",  
  "rule\_name": "เต้ารับระยะห่างขั้นต่ำจากมุมห้อง",  
  "description": "เต้ารับติดผนังต้องห่างจากมุมห้องไม่น้อยกว่า 150 มม.",  
  "applies\_to": \["receptacle"\],  
  "validation\_type": "distance\_check",  
  "parameters": {  
    "min\_distance\_from\_corner\_mm": 150,  
    "reference\_point": "room\_corner"  
  },  
  "error\_level": "warning",  
  "standard\_reference": "มอก. 2955 มาตรา 8.1"  
}

{  
  "kind": "VALIDATION\_RULE",  
  "rule\_id": "VR002",  
  "rule\_name": "โหลดรวมวงจรเต้ารับไม่เกิน 80%",  
  "description": "โหลดรวมบนวงจรเต้ารับต้องไม่เกิน 80% ของค่าเบรกเกอร์",  
  "applies\_to": \["circuit"\],  
  "validation\_type": "load\_check",  
  "parameters": {  
    "max\_load\_percent": 80,  
    "circuit\_type": "receptacle"  
  },  
  "error\_level": "error",  
  "standard\_reference": "NEC 210.19(A)(1)"  
}

{  
  "kind": "VALIDATION\_RULE",  
  "rule\_id": "VR003",  
  "rule\_name": "ระยะห่างสวิตช์จากพื้น",  
  "description": "สวิตช์ต้องติดตั้งสูงจากพื้น 900-1200 มม.",  
  "applies\_to": \["switch"\],  
  "validation\_type": "height\_check",  
  "parameters": {  
    "min\_height\_mm": 900,  
    "max\_height\_mm": 1200,  
    "reference\_point": "finished\_floor"  
  },  
  "error\_level": "warning",  
  "standard\_reference": "มอก. 2955 มาตรา 7.2"  
}

{  
  "kind": "VALIDATION\_RULE",  
  "rule\_id": "VR004",  
  "rule\_name": "ระยะห่างเต้ารับในห้องน้ำจากน้ำ",  
  "description": "เต้ารับในห้องน้ำต้องห่างจากแหล่งน้ำไม่น้อยกว่า 600 มม.",  
  "applies\_to": \["receptacle"\],  
  "room\_type": \["bathroom"\],  
  "validation\_type": "distance\_check",  
  "parameters": {  
    "min\_distance\_from\_water\_mm": 600,  
    "reference\_point": "water\_source"  
  },  
  "error\_level": "error",  
  "standard\_reference": "IEC 60364-7-701"  
}

{  
  "kind": "VALIDATION\_RULE",  
  "rule\_id": "VR005",  
  "rule\_name": "ระยะห่างโคมไฟในห้องน้ำจากอ่างอาบน้ำ",  
  "description": "โคมไฟต้องห่างจากขอบอ่างอาบน้ำไม่น้อยกว่า 2.25 เมตร (Zone 2)",  
  "applies\_to": \["luminaire"\],  
  "room\_type": \["bathroom"\],  
  "validation\_type": "zone\_check",  
  "parameters": {  
    "min\_distance\_from\_bath\_m": 2.25,  
    "zone": "zone\_2"  
  },  
  "error\_level": "error",  
  "standard\_reference": "IEC 60364-7-701"  
}  
\`\`\`

\*\*\*

\#\#\# \*\*❌ 2\. DERATING\_FACTOR — ตารางค่าลด Ampacity\*\*

\*\*คำอธิบาย:\*\*  
\- ตารางค่าลดกระแสที่สายไฟรับได้ (Derating Factor)  
\- ใช้เมื่อใส่สายหลายเส้นในท่อร่วมกัน หรือ อุณหภูมิสูง

\*\*ตัวอย่างข้อมูล:\*\*

\`\`\`json  
{  
  "kind": "DERATING\_FACTOR",  
  "factor\_id": "DF001",  
  "factor\_name": "Grouping Factor — จำนวนสายในท่อ",  
  "description": "ค่าลดเมื่อใส่สายหลายเส้นในท่อเดียวกัน (Bundle Derating)",  
  "derating\_type": "conductor\_grouping",  
  "table": \[  
    {"conductors\_count": 1, "derating\_factor": 1.00},  
    {"conductors\_count": 2, "derating\_factor": 1.00},  
    {"conductors\_count": 3, "derating\_factor": 1.00},  
    {"conductors\_count": 4, "derating\_factor": 0.80},  
    {"conductors\_count": 5, "derating\_factor": 0.80},  
    {"conductors\_count": 6, "derating\_factor": 0.80},  
    {"conductors\_count": 7, "derating\_factor": 0.70},  
    {"conductors\_count": 9, "derating\_factor": 0.70},  
    {"conductors\_count": 10, "derating\_factor": 0.70},  
    {"conductors\_count": 15, "derating\_factor": 0.50},  
    {"conductors\_count": 20, "derating\_factor": 0.45},  
    {"conductors\_count": 30, "derating\_factor": 0.40}  
  \],  
  "standard\_reference": "NEC Table 310.15(C)(1), IEC 60364-5-52"  
}

{  
  "kind": "DERATING\_FACTOR",  
  "factor\_id": "DF002",  
  "factor\_name": "Ambient Temperature Correction",  
  "description": "ค่าลดเมื่ออุณหภูมิแวดล้อมสูงกว่า 30°C",  
  "derating\_type": "ambient\_temperature",  
  "base\_temperature\_c": 30,  
  "table": \[  
    {"ambient\_temp\_c": 30, "derating\_factor\_60c": 1.00, "derating\_factor\_75c": 1.00, "derating\_factor\_90c": 1.00},  
    {"ambient\_temp\_c": 35, "derating\_factor\_60c": 0.91, "derating\_factor\_75c": 0.94, "derating\_factor\_90c": 0.96},  
    {"ambient\_temp\_c": 40, "derating\_factor\_60c": 0.82, "derating\_factor\_75c": 0.88, "derating\_factor\_90c": 0.91},  
    {"ambient\_temp\_c": 45, "derating\_factor\_60c": 0.71, "derating\_factor\_75c": 0.82, "derating\_factor\_90c": 0.87},  
    {"ambient\_temp\_c": 50, "derating\_factor\_60c": 0.58, "derating\_factor\_75c": 0.75, "derating\_factor\_90c": 0.82}  
  \],  
  "standard\_reference": "NEC Table 310.15(B)(2)(a)"  
}

{  
  "kind": "DERATING\_FACTOR",  
  "factor\_id": "DF003",  
  "factor\_name": "Conduit Fill Derating",  
  "description": "ค่าลดเมื่อท่อเต็มเกิน 40%",  
  "derating\_type": "conduit\_fill",  
  "table": \[  
    {"fill\_percent": 40, "derating\_factor": 1.00},  
    {"fill\_percent": 50, "derating\_factor": 0.95},  
    {"fill\_percent": 60, "derating\_factor": 0.85},  
    {"fill\_percent": 70, "derating\_factor": 0.75}  
  \],  
  "standard\_reference": "NEC 310.15(C)(1)"  
}

{  
  "kind": "DERATING\_FACTOR",  
  "factor\_id": "DF004",  
  "factor\_name": "Thermal Insulation Derating",  
  "description": "ค่าลดเมื่อสายวิ่งผ่านฉนวนกันความร้อน",  
  "derating\_type": "thermal\_insulation",  
  "table": \[  
    {"insulation\_thickness\_mm": 0, "derating\_factor": 1.00},  
    {"insulation\_thickness\_mm": 50, "derating\_factor": 0.85},  
    {"insulation\_thickness\_mm": 100, "derating\_factor": 0.75},  
    {"insulation\_thickness\_mm": 200, "derating\_factor": 0.60}  
  \],  
  "standard\_reference": "IEC 60364-5-52"  
}  
\`\`\`

\*\*\*

\#\#\# \*\*❌ 3\. GEOMETRY\_FILTER — กติกาเดินสาย CAD\*\*

\*\*คำอธิบาย:\*\*  
\- กฎสำหรับบอกว่า \*\*ควรเดินสายตามเส้นไหน\*\* ใน AutoCAD  
\- เดินผ่านพื้นที่ไหนได้บ้าง ห้ามผ่านพื้นที่ไหน

\*\*ตัวอย่างข้อมูล:\*\*

\`\`\`json  
{  
  "kind": "GEOMETRY\_FILTER",  
  "filter\_id": "GF001",  
  "filter\_name": "Wall Centerline Routing",  
  "description": "เดินสายตามเส้นกึ่งกลางผนัง (Wall Centerline)",  
  "routing\_type": "wall\_conduit",  
  "preferred\_path": \["wall\_centerline", "wall\_edge"\],  
  "avoid\_zones": \["structural\_column", "beam", "window", "door"\],  
  "max\_deviation\_mm": 50,  
  "standard\_reference": "มอก. 2955"  
}

{  
  "kind": "GEOMETRY\_FILTER",  
  "filter\_id": "GF002",  
  "filter\_name": "Ceiling Cable Tray Routing",  
  "description": "เดินสายบนรางเคเบิ้ลใต้เพดาน",  
  "routing\_type": "cable\_tray",  
  "preferred\_path": \["ceiling\_tray", "cable\_ladder"\],  
  "avoid\_zones": \["hvac\_duct", "sprinkler\_pipe", "lighting\_fixture"\],  
  "min\_clearance\_mm": 150,  
  "standard\_reference": "NEC 392"  
}

{  
  "kind": "GEOMETRY\_FILTER",  
  "filter\_id": "GF003",  
  "filter\_name": "Underground Conduit Routing",  
  "description": "เดินท่อใต้พื้น ห่างจากท่อประปา/ก๊าซ",  
  "routing\_type": "underground\_conduit",  
  "preferred\_path": \["under\_slab", "trench"\],  
  "avoid\_zones": \["water\_pipe", "gas\_pipe", "drain\_pipe"\],  
  "min\_clearance\_mm": 300,  
  "max\_depth\_mm": 600,  
  "standard\_reference": "มอก. 2955 มาตรา 10"  
}

{  
  "kind": "GEOMETRY\_FILTER",  
  "filter\_id": "GF004",  
  "filter\_name": "Bathroom Zone Routing",  
  "description": "เดินสายในห้องน้ำ ห้ามผ่าน Zone 0, 1",  
  "routing\_type": "bathroom\_conduit",  
  "preferred\_path": \["zone\_2", "zone\_3", "outside\_zones"\],  
  "avoid\_zones": \["zone\_0", "zone\_1"\],  
  "min\_distance\_from\_water\_mm": 600,  
  "standard\_reference": "IEC 60364-7-701"  
}  
\`\`\`

\*\*\*

\#\#\# \*\*❌ 4\. QA\_PLAN — แผนตรวจสอบคุณภาพ\*\*

\*\*คำอธิบาย:\*\*  
\- Checklist สำหรับตรวจสอบว่า \*\*แบบที่ออกมาสมบูรณ์หรือไม่\*\*  
\- ต้องมีอะไรบ้าง ครบหรือยัง

\*\*ตัวอย่างข้อมูล:\*\*

\`\`\`json  
{  
  "kind": "QA\_PLAN",  
  "qa\_id": "QA001",  
  "qa\_name": "Design Completeness Checklist",  
  "description": "ตรวจสอบความสมบูรณ์ของแบบออกแบบ",  
  "checklist": \[  
    {  
      "item": "Single Line Diagram (SLD)",  
      "required": true,  
      "description": "ต้องมีแผนผังวงจรแสดงการเชื่อมต่อ Breaker, Wire, Load"  
    },  
    {  
      "item": "Load Calculation Sheet",  
      "required": true,  
      "description": "ต้องมีเอกสารคำนวณโหลดทุกวงจร"  
    },  
    {  
      "item": "Layout Plan (AutoCAD)",  
      "required": true,  
      "description": "ต้องมีแปลนแสดงตำแหน่ง ปลั๊ก/สวิตช์/โคมไฟ/DB"  
    },  
    {  
      "item": "Conduit Routing Diagram",  
      "required": false,  
      "description": "แสดงเส้นทางท่อ (Optional แต่แนะนำ)"  
    },  
    {  
      "item": "Bill of Quantity (BOQ)",  
      "required": true,  
      "description": "รายการวัสดุ จำนวน ราคา"  
    },  
    {  
      "item": "Compliance Report",  
      "required": true,  
      "description": "ตรวจสอบมาตรฐาน มอก. 2955, IEC, NEC"  
    },  
    {  
      "item": "Voltage Drop Calculation",  
      "required": true,  
      "description": "คำนวณ VD ทุกวงจร ≤ 3%"  
    }  
  \],  
  "pass\_criteria": {  
    "min\_required\_items": 5,  
    "all\_required\_must\_pass": true  
  }  
}

{  
  "kind": "QA\_PLAN",  
  "qa\_id": "QA002",  
  "qa\_name": "Installation Quality Checklist",  
  "description": "ตรวจสอบคุณภาพการติดตั้ง",  
  "checklist": \[  
    {  
      "item": "สายไฟขนาดตรงตามแบบ",  
      "required": true,  
      "validation\_method": "visual\_inspection"  
    },  
    {  
      "item": "Breaker Rating ตรงตามแบบ",  
      "required": true,  
      "validation\_method": "label\_check"  
    },  
    {  
      "item": "RCBO ติดตั้งในห้องน้ำ/ครัว",  
      "required": true,  
      "validation\_method": "visual\_inspection"  
    },  
    {  
      "item": "ระยะห่างเต้ารับ ≤ 3.6 m",  
      "required": true,  
      "validation\_method": "measurement"  
    },  
    {  
      "item": "Grounding ต่อครบทุกจุด",  
      "required": true,  
      "validation\_method": "continuity\_test"  
    }  
  \]  
}  
\`\`\`

\*\*\*

\#\#\# \*\*❌ 5\. CABLE\_SPEC — สเปคสายไฟ (ต้องเพิ่ม)\*\*

\*\*คำอธิบาย:\*\*  
\- สเปคของสายไฟ แต่ละขนาด  
\- Ampacity, ราคา, ฉนวน, ชนิด

\*\*ตัวอย่างข้อมูล:\*\*

\`\`\`json  
{  
  "kind": "CABLE\_SPEC",  
  "cable\_id": "CS001",  
  "cable\_name": "THW 1.5 mm²",  
  "size\_mm2": 1.5,  
  "material": "copper",  
  "insulation\_type": "PVC (THW)",  
  "insulation\_temp\_rating\_c": 75,  
  "ampacity\_free\_air\_a": 20,  
  "ampacity\_in\_conduit\_a": 18,  
  "resistance\_ohm\_per\_km\_20c": 12.1,  
  "reactance\_ohm\_per\_km": 0.08,  
  "outer\_diameter\_mm": 4.5,  
  "weight\_kg\_per\_m": 0.025,  
  "price\_thb\_per\_m": 5.50,  
  "price\_date": "2025-11-15",  
  "standard\_reference": "IEC 60227, มอก. 16-2531"  
}

{  
  "kind": "CABLE\_SPEC",  
  "cable\_id": "CS002",  
  "cable\_name": "THW 2.5 mm²",  
  "size\_mm2": 2.5,  
  "material": "copper",  
  "insulation\_type": "PVC (THW)",  
  "insulation\_temp\_rating\_c": 75,  
  "ampacity\_free\_air\_a": 30,  
  "ampacity\_in\_conduit\_a": 25,  
  "resistance\_ohm\_per\_km\_20c": 7.41,  
  "reactance\_ohm\_per\_km": 0.075,  
  "outer\_diameter\_mm": 5.5,  
  "weight\_kg\_per\_m": 0.042,  
  "price\_thb\_per\_m": 8.50,  
  "price\_date": "2025-11-15",  
  "standard\_reference": "IEC 60227, มอก. 16-2531"  
}

{  
  "kind": "CABLE\_SPEC",  
  "cable\_id": "CS003",  
  "cable\_name": "THW 4 mm²",  
  "size\_mm2": 4.0,  
  "material": "copper",  
  "insulation\_type": "PVC (THW)",  
  "insulation\_temp\_rating\_c": 75,  
  "ampacity\_free\_air\_a": 40,  
  "ampacity\_in\_conduit\_a": 35,  
  "resistance\_ohm\_per\_km\_20c": 4.61,  
  "reactance\_ohm\_per\_km": 0.070,  
  "outer\_diameter\_mm": 6.5,  
  "weight\_kg\_per\_m": 0.063,  
  "price\_thb\_per\_m": 12.00,  
  "price\_date": "2025-11-15",  
  "standard\_reference": "IEC 60227, มอก. 16-2531"  
}

{  
  "kind": "CABLE\_SPEC",  
  "cable\_id": "CS004",  
  "cable\_name": "THHN 1.5 mm²",  
  "size\_mm2": 1.5,  
  "material": "copper",  
  "insulation\_type": "Nylon-coated PVC (THHN)",  
  "insulation\_temp\_rating\_c": 90,  
  "ampacity\_free\_air\_a": 25,  
  "ampacity\_in\_conduit\_a": 20,  
  "resistance\_ohm\_per\_km\_20c": 12.1,  
  "reactance\_ohm\_per\_km": 0.08,  
  "outer\_diameter\_mm": 4.0,  
  "weight\_kg\_per\_m": 0.022,  
  "price\_thb\_per\_m": 6.50,  
  "price\_date": "2025-11-15",  
  "standard\_reference": "NEC NFPA 70"  
}

{  
  "kind": "CABLE\_SPEC",  
  "cable\_id": "CS005",  
  "cable\_name": "XLPE 10 mm²",  
  "size\_mm2": 10.0,  
  "material": "copper",  
  "insulation\_type": "Cross-linked Polyethylene (XLPE)",  
  "insulation\_temp\_rating\_c": 90,  
  "ampacity\_free\_air\_a": 75,  
  "ampacity\_in\_conduit\_a": 64,  
  "resistance\_ohm\_per\_km\_20c": 1.83,  
  "reactance\_ohm\_per\_km": 0.065,  
  "outer\_diameter\_mm": 9.5,  
  "weight\_kg\_per\_m": 0.145,  
  "price\_thb\_per\_m": 35.00,  
  "price\_date": "2025-11-15",  
  "standard\_reference": "IEC 60502"  
}  
\`\`\`

\*\*\*

\#\# 📊 ส่วนที่ 2: COMPONENT — เพิ่มข้อมูลให้ละเอียด

\#\#\# \*\*เดิม (ง่ายเกินไป):\*\*  
\`\`\`json  
{  
  "kind": "COMPONENT",  
  "name": "เต้ารับ 2 ช่อง",  
  "mount\_height\_mm": 300  
}  
\`\`\`

\#\#\# \*\*ใหม่ (ละเอียด):\*\*  
\`\`\`json  
{  
  "kind": "COMPONENT",  
  "component\_id": "COMP001",  
  "name": "เต้ารับ 2 ช่อง (Duplex Receptacle)",  
  "component\_type": "receptacle",  
  "subtype": "duplex",  
  "voltage\_rating\_v": 220,  
  "current\_rating\_a": 16,  
  "power\_rating\_w": 3520,  
  "ip\_rating": "IP20",  
  "grounding": true,  
  "color": "white",  
  "material": "polycarbonate",  
  "dimension\_mm": {  
    "width": 86,  
    "height": 86,  
    "depth": 42  
  },  
  "mount\_height\_mm": 300,  
  "mount\_type": "flush\_mount",  
  "standard\_reference": "มอก. 166-2549, IEC 60884",  
  "brand": "Panasonic",  
  "model": "WEG1021",  
  "price\_thb": 45,  
  "typical\_rooms": \["living\_room", "bedroom", "kitchen"\]  
}

{  
  "kind": "COMPONENT",  
  "component\_id": "COMP002",  
  "name": "สวิตช์ 1 ทาง (Single Pole Switch)",  
  "component\_type": "switch",  
  "subtype": "toggle",  
  "voltage\_rating\_v": 220,  
  "current\_rating\_a": 16,  
  "power\_rating\_w": 3520,  
  "ip\_rating": "IP20",  
  "color": "white",  
  "material": "polycarbonate",  
  "dimension\_mm": {  
    "width": 86,  
    "height": 86,  
    "depth": 42  
  },  
  "mount\_height\_mm": 1200,  
  "mount\_type": "flush\_mount",  
  "switch\_type": "single\_pole",  
  "standard\_reference": "มอก. 166-2549",  
  "brand": "Panasonic",  
  "model": "WEG5531",  
  "price\_thb": 35,  
  "typical\_rooms": \["all"\]  
}

{  
  "kind": "COMPONENT",  
  "component\_id": "COMP003",  
  "name": "สวิตช์ปรับแสง (Dimmer Switch)",  
  "component\_type": "switch",  
  "subtype": "dimmer",  
  "voltage\_rating\_v": 220,  
  "current\_rating\_a": 5,  
  "power\_rating\_w": 1100,  
  "dimming\_range\_percent": "0-100",  
  "compatible\_load": \["LED", "incandescent"\],  
  "ip\_rating": "IP20",  
  "color": "white",  
  "dimension\_mm": {  
    "width": 86,  
    "height": 86,  
    "depth": 50  
  },  
  "mount\_height\_mm": 1200,  
  "mount\_type": "flush\_mount",  
  "standard\_reference": "มอก. 166-2549",  
  "brand": "Schneider",  
  "model": "A8331DIMLW\_WE",  
  "price\_thb": 450,  
  "typical\_rooms": \["living\_room", "dining\_room"\]  
}

{  
  "kind": "COMPONENT",  
  "component\_id": "COMP004",  
  "name": "โคมไฟดาวน์ไลท์ LED 9W",  
  "component\_type": "luminaire",  
  "subtype": "downlight",  
  "light\_source": "LED",  
  "power\_w": 9,  
  "lumens": 810,  
  "color\_temperature\_k": 4000,  
  "beam\_angle\_deg": 120,  
  "ip\_rating": "IP44",  
  "dimmable": true,  
  "voltage\_rating\_v": 220,  
  "power\_factor": 0.95,  
  "dimension\_mm": {  
    "diameter": 90,  
    "depth": 75  
  },  
  "cutout\_diameter\_mm": 75,  
  "mount\_height\_mm": 2700,  
  "mount\_type": "recessed",  
  "standard\_reference": "มอก. 1955",  
  "brand": "Philips",  
  "model": "DN020B LED9",  
  "price\_thb": 195,  
  "typical\_rooms": \["all"\]  
}

{  
  "kind": "COMPONENT",  
  "component\_id": "COMP005",  
  "name": "เต้ารับกันน้ำ IP65 (Waterproof Receptacle)",  
  "component\_type": "receptacle",  
  "subtype": "weatherproof",  
  "voltage\_rating\_v": 220,  
  "current\_rating\_a": 16,  
  "power\_rating\_w": 3520,  
  "ip\_rating": "IP65",  
  "grounding": true,  
  "gfci\_integrated": false,  
  "color": "gray",  
  "material": "polycarbonate",  
  "dimension\_mm": {  
    "width": 100,  
    "height": 100,  
    "depth": 65  
  },  
  "mount\_height\_mm": 300,  
  "mount\_type": "surface\_mount",  
  "standard\_reference": "IEC 60529, IEC 60884",  
  "brand": "Panasonic",  
  "model": "WEV2391",  
  "price\_thb": 285,  
  "typical\_rooms": \["outdoor", "balcony", "garage"\]  
}  
\`\`\`

\*\*\*

\#\# 📊 ส่วนที่ 3: CIRCUIT\_TEMPLATE — เพิ่มข้อมูลโหลด

\#\#\# \*\*เดิม:\*\*  
\`\`\`json  
{  
  "kind": "CIRCUIT\_TEMPLATE",  
  "name": "วงจรเต้ารับ 20A",  
  "breaker\_rating\_a": 20  
}  
\`\`\`

\#\#\# \*\*ใหม่:\*\*  
\`\`\`json  
{  
  "kind": "CIRCUIT\_TEMPLATE",  
  "template\_id": "CT001",  
  "name": "วงจรเต้ารับทั่วไป 20A",  
  "circuit\_type": "receptacle",  
  "load\_type": "general\_purpose",  
  "breaker\_rating\_a": 20,  
  "voltage\_v": 220,  
  "phase": "single",  
  "wire\_size\_mm2": 2.5,  
  "max\_load\_w": 3520,  
  "recommended\_load\_w": 2816,  
  "load\_factor\_percent": 80,  
  "diversity\_factor": 0.75,  
  "max\_outlets": 10,  
  "protection\_device": "MCB",  
  "grounding\_required": true,  
  "standard\_reference": "NEC 210.19(A)(1)"  
}

{  
  "kind": "CIRCUIT\_TEMPLATE",  
  "template\_id": "CT002",  
  "name": "วงจรแสงสว่าง 16A",  
  "circuit\_type": "lighting",  
  "load\_type": "lighting",  
  "breaker\_rating\_a": 16,  
  "voltage\_v": 220,  
  "phase": "single",  
  "wire\_size\_mm2": 1.5,  
  "max\_load\_w": 2816,  
  "recommended\_load\_w": 2252,  
  "load\_factor\_percent": 80,  
  "diversity\_factor": 0.70,  
  "max\_luminaires": 20,  
  "protection\_device": "MCB",  
  "grounding\_required": true,  
  "standard\_reference": "มอก. 2955"  
}

{  
  "kind": "CIRCUIT\_TEMPLATE",  
  "template\_id": "CT003",  
  "name": "วงจรแอร์ 32A (Dedicated)",  
  "circuit\_type": "hvac",  
  "load\_type": "air\_conditioning",  
  "breaker\_rating\_a": 32,  
  "voltage\_v": 220,  
  "phase": "single",  
  "wire\_size\_mm2": 6.0,  
  "max\_load\_w": 7040,  
  "recommended\_load\_w": 5632,  
  "load\_factor\_percent": 100,  
  "diversity\_factor": 1.00,  
  "dedicated\_circuit": true,  
  "protection\_device": "MCB",  
  "grounding\_required": true,  
  "standard\_reference": "NEC 440"  
}

{  
  "kind": "CIRCUIT\_TEMPLATE",  
  "template\_id": "CT004",  
  "name": "วงจรเครื่องทำน้ำอุ่น 20A \+ RCBO",  
  "circuit\_type": "water\_heater",  
  "load\_type": "heating",  
  "breaker\_rating\_a": 20,  
  "voltage\_v": 220,  
  "phase": "single",  
  "wire\_size\_mm2": 4.0,  
  "max\_load\_w": 4400,  
  "recommended\_load\_w": 3500,  
  "load\_factor\_percent": 100,  
  "diversity\_factor": 1.00,  
  "dedicated\_circuit": true,  
  "protection\_device": "RCBO",  
  "rcbo\_sensitivity\_ma": 30,  
  "grounding\_required": true,  
  "standard\_reference": "IEC 60364-7-701"  
}  
\`\`\`

\*\*\*

\#\# 📊 ส่วนที่ 4: PLACEMENT\_RULE — เพิ่มข้อมูลซับซ้อน

\#\#\# \*\*เดิม:\*\*  
\`\`\`json  
{  
  "kind": "PLACEMENT\_RULE",  
  "name": "เต้ารับระยะห่าง",  
  "spacing\_m": 3.6  
}  
\`\`\`

\#\#\# \*\*ใหม่:\*\*  
\`\`\`json  
{  
  "kind": "PLACEMENT\_RULE",  
  "rule\_id": "PR001",  
  "name": "เต้ารับระยะห่างสูงสุด",  
  "applies\_to": \["receptacle"\],  
  "room\_type": \["living\_room", "bedroom"\],  
  "max\_spacing\_m": 3.6,  
  "min\_spacing\_m": 1.0,  
  "mount\_height\_mm": 300,  
  "align\_to": "baseboard",  
  "avoid\_zones": \["behind\_door", "behind\_furniture"\],  
  "min\_distance\_from\_corner\_mm": 150,  
  "standard\_reference": "NEC 210.52(A)"  
}

{  
  "kind": "PLACEMENT\_RULE",  
  "rule\_id": "PR002",  
  "name": "สวิตช์ตำแหน่งมาตรฐาน",  
  "applies\_to": \["switch"\],  
  "room\_type": \["all"\],  
  "mount\_height\_mm": 1200,  
  "min\_height\_mm": 900,  
  "max\_height\_mm": 1400,  
  "align\_to": "door\_frame",  
  "preferred\_side": "latch\_side",  
  "min\_distance\_from\_door\_mm": 150,  
  "avoid\_zones": \["behind\_door"\],  
  "standard\_reference": "มอก. 2955"  
}

{  
  "kind": "PLACEMENT\_RULE",  
  "rule\_id": "PR003",  
  "name": "โคมไฟห้องน้ำ Zone Restriction",  
  "applies\_to": \["luminaire"\],  
  "room\_type": \["bathroom"\],  
  "avoid\_zones": \["zone\_0", "zone\_1"\],  
  "allowed\_zones": \["zone\_2", "zone\_3"\],  
  "min\_distance\_from\_shower\_m": 2.25,  
  "min\_ip\_rating": "IP44",  
  "max\_voltage\_v": 12,  
  "standard\_reference": "IEC 60364-7-701"  
}

{  
  "kind": "PLACEMENT\_RULE",  
  "rule\_id": "PR004",  
  "name": "เต้ารับครัวบนเคาน์เตอร์",  
  "applies\_to": \["receptacle"\],  
  "room\_type": \["kitchen"\],  
  "mount\_location": "above\_countertop",  
  "mount\_height\_mm": 1100,  
  "max\_spacing\_m": 1.2,  
  "min\_spacing\_m": 0.6,  
  "align\_to": "countertop\_edge",  
  "min\_distance\_from\_sink\_mm": 300,  
  "gfci\_required": true,  
  "standard\_reference": "NEC 210.52(C)"  
}

{  
  "kind": "PLACEMENT\_RULE",  
  "rule\_id": "PR005",  
  "name": "Distribution Board (DB) Location",  
  "applies\_to": \["distribution\_board"\],  
  "room\_type": \["all"\],  
  "preferred\_location": \["utility\_room", "garage", "hallway"\],  
  "mount\_height\_mm": 1500,  
  "min\_height\_mm": 1200,  
  "max\_height\_mm": 1800,  
  "min\_clearance\_front\_mm": 1000,  
  "min\_clearance\_side\_mm": 300,  
  "avoid\_zones": \["bathroom", "bedroom", "above\_stove"\],  
  "accessible": true,  
  "standard\_reference": "NEC 110.26"  
}  
\`\`\`

\*\*\*

\#\# 📦 ส่วนที่ 5: APPLIANCES\_CATALOG — อุปกรณ์ไฟฟ้าครบถ้วน

\#\#\# \*\*Living Room / Bedroom:\*\*  
\`\`\`json  
{  
  "appliance\_id": "APP001",  
  "name": "LED TV 55 นิ้ว",  
  "category": "entertainment",  
  "subcategory": "television",  
  "power\_w": 150,  
  "standby\_power\_w": 0.5,  
  "voltage\_v": 220,  
  "current\_a": 0.68,  
  "power\_factor": 0.95,  
  "requires\_dedicated\_circuit": false,  
  "typical\_rooms": \["living\_room", "bedroom"\],  
  "usage\_hours\_per\_day": 6,  
  "energy\_consumption\_kwh\_per\_month": 27,  
  "price\_thb": 18000,  
  "brand": "Samsung",  
  "model": "UA55AU7700",  
  "dimension\_mm": {"width": 1232, "height": 708, "depth": 60}  
}

{  
  "appliance\_id": "APP002",  
  "name": "แอร์ 9,000 BTU (Inverter)",  
  "category": "hvac",  
  "subcategory": "air\_conditioner",  
  "cooling\_capacity\_btu": 9000,  
  "cooling\_capacity\_w": 2637,  
  "power\_w": 750,  
  "running\_current\_a": 3.4,  
  "startup\_current\_a": 15,  
  "voltage\_v": 220,  
  "power\_factor": 0.85,  
  "energy\_efficiency\_ratio\_eer": 3.52,  
  "requires\_dedicated\_circuit": true,  
  "typical\_rooms": \["bedroom", "living\_room"\],  
  "usage\_hours\_per\_day": 8,  
  "energy\_consumption\_kwh\_per\_month": 180,  
  "price\_thb": 12900,  
  "brand": "Daikin",  
  "model": "FTKC25UV2S"  
}

{  
  "appliance\_id": "APP003",  
  "name": "แอร์ 12,000 BTU (Inverter)",  
  "category": "hvac",  
  "subcategory": "air\_conditioner",  
  "cooling\_capacity\_btu": 12000,  
  "cooling\_capacity\_w": 3516,  
  "power\_w": 1100,  
  "running\_current\_a": 5.0,  
  "startup\_current\_a": 20,  
  "voltage\_v": 220,  
  "power\_factor": 0.85,  
  "energy\_efficiency\_ratio\_eer": 3.20,  
  "requires\_dedicated\_circuit": true,  
  "typical\_rooms": \["living\_room", "master\_bedroom"\],  
  "usage\_hours\_per\_day": 8,  
  "energy\_consumption\_kwh\_per\_month": 264,  
  "price\_thb": 15900,  
  "brand": "Mitsubishi",  
  "model": "MSY-JP12VF"  
}

{  
  "appliance\_id": "APP004",  
  "name": "พัดลมติดเพดาน 56 นิ้ว",  
  "category": "hvac",  
  "subcategory": "ceiling\_fan",  
  "power\_w": 75,  
  "voltage\_v": 220,  
  "current\_a": 0.34,  
  "power\_factor": 0.60,  
  "requires\_dedicated\_circuit": false,  
  "typical\_rooms": \["bedroom", "living\_room"\],  
  "usage\_hours\_per\_day": 10,  
  "energy\_consumption\_kwh\_per\_month": 22.5,  
  "price\_thb": 2500,  
  "brand": "Hatari",  
  "model": "HC56M5"  
}  
\`\`\`

\#\#\# \*\*Kitchen:\*\*  
\`\`\`json  
{  
  "appliance\_id": "APP005",  
  "name": "ตู้เย็น 2 ประตู 15 คิว",  
  "category": "kitchen",  
  "subcategory": "refrigerator",  
  "capacity\_liters": 424,  
  "power\_w": 150,  
  "running\_current\_a": 0.68,  
  "startup\_current\_a": 4.5,  
  "voltage\_v": 220,  
  "power\_factor": 0.85,  
  "requires\_dedicated\_circuit": true,  
  "typical\_rooms": \["kitchen"\],  
  "usage\_hours\_per\_day": 24,  
  "actual\_runtime\_hours\_per\_day": 8,  
  "energy\_consumption\_kwh\_per\_month": 36,  
  "price\_thb": 16900,  
  "brand": "Samsung",  
  "model": "RT38K5032S8"  
}

{  
  "appliance\_id": "APP006",  
  "name": "ไมโครเวฟ 1,200W",  
  "category": "kitchen",  
  "subcategory": "microwave",  
  "power\_w": 1200,  
  "voltage\_v": 220,  
  "current\_a": 5.45,  
  "power\_factor": 0.90,  
  "requires\_dedicated\_circuit": false,  
  "typical\_rooms": \["kitchen"\],  
  "usage\_hours\_per\_day": 0.5,  
  "energy\_consumption\_kwh\_per\_month": 18,  
  "price\_thb": 3500,  
  "brand": "Sharp",  
  "model": "R-299T(W)"  
}

{  
  "appliance\_id": "APP007",  
  "name": "หม้อหุงข้าว 1.8 ลิตร",  
  "category": "kitchen",  
  "subcategory": "rice\_cooker",  
  "capacity\_liters": 1.8,  
  "power\_w": 700,  
  "voltage\_v": 220,  
  "current\_a": 3.18,  
  "power\_factor": 0.95,  
  "requires\_dedicated\_circuit": false,  
  "typical\_rooms": \["kitchen"\],  
  "usage\_hours\_per\_day": 1,  
  "energy\_consumption\_kwh\_per\_month": 21,  
  "price\_thb": 1200,  
  "brand": "Panasonic",  
  "model": "SR-ZE185"  
}

{  
  "appliance\_id": "APP008",  
  "name": "เตาไฟฟ้า 2 เตา",  
  "category": "kitchen",  
  "subcategory": "electric\_stove",  
  "power\_w": 2000,  
  "voltage\_v": 220,  
  "current\_a": 9.09,  
  "power\_factor": 1.00,  
  "requires\_dedicated\_circuit": true,  
  "typical\_rooms": \["kitchen"\],  
  "usage\_hours\_per\_day": 2,  
  "energy\_consumption\_kwh\_per\_month": 120,  
  "price\_thb": 4500,  
  "brand": "Tecnogas",  
  "model": "TID22"  
}

{  
  "appliance\_id": "APP009",  
  "name": "เครื่องดูดควัน 1,000 m³/h",  
  "category": "kitchen",  
  "subcategory": "range\_hood",  
  "power\_w": 220,  
  "voltage\_v": 220,  
  "current\_a": 1.00,  
  "power\_factor": 0.70,  
  "requires\_dedicated\_circuit": false,  
  "typical\_rooms": \["kitchen"\],  
  "usage\_hours\_per\_day": 2,  
  "energy\_consumption\_kwh\_per\_month": 13.2,  
  "price\_thb": 8500,  
  "brand": "Tecnogas",  
  "model": "TSL90I"  
}  
\`\`\`

\#\#\# \*\*Bathroom:\*\*  
\`\`\`json  
{  
  "appliance\_id": "APP010",  
  "name": "เครื่องทำน้ำอุ่น 3,500W",  
  "category": "bathroom",  
  "subcategory": "water\_heater",  
  "power\_w": 3500,  
  "voltage\_v": 220,  
  "current\_a": 15.91,  
  "power\_factor": 1.00,  
  "requires\_dedicated\_circuit": true,  
  "requires\_rcbo": true,  
  "rcbo\_sensitivity\_ma": 30,  
  "typical\_rooms": \["bathroom"\],  
  "usage\_hours\_per\_day": 1,  
  "energy\_consumption\_kwh\_per\_month": 105,  
  "price\_thb": 2900,  
  "brand": "Stiebel Eltron",  
  "model": "DHE 35 SLi"  
}

{  
  "appliance\_id": "APP011",  
  "name": "ปั๊มน้ำ 1 HP",  
  "category": "utility",  
  "subcategory": "water\_pump",  
  "power\_hp": 1,  
  "power\_w": 746,  
  "running\_current\_a": 3.4,  
  "startup\_current\_a": 18,  
  "voltage\_v": 220,  
  "power\_factor": 0.80,  
  "requires\_dedicated\_circuit": true,  
  "typical\_rooms": \["utility\_room", "outdoor"\],  
  "usage\_hours\_per\_day": 2,  
  "energy\_consumption\_kwh\_per\_month": 44.8,  
  "price\_thb": 3800,  
  "brand": "Mitsubishi",  
  "model": "WP-155R5"  
}  
\`\`\`

\#\#\# \*\*Utility / Laundry:\*\*  
\`\`\`json  
{  
  "appliance\_id": "APP012",  
  "name": "เครื่องซักผ้า 8 kg",  
  "category": "laundry",  
  "subcategory": "washing\_machine",  
  "capacity\_kg": 8,  
  "power\_w": 500,  
  "voltage\_v": 220,  
  "current\_a": 2.27,  
  "power\_factor": 0.85,  
  "requires\_dedicated\_circuit": false,  
  "typical\_rooms": \["laundry\_room", "bathroom"\],  
  "usage\_hours\_per\_day": 1,  
  "energy\_consumption\_kwh\_per\_month": 15,  
  "price\_thb": 8900,  
  "brand": "LG",  
  "model": "T2108VS2M"  
}

{  
  "appliance\_id": "APP013",  
  "name": "เครื่องอบผ้า 4,000W",  
  "category": "laundry",  
  "subcategory": "dryer",  
  "power\_w": 4000,  
  "voltage\_v": 220,  
  "current\_a": 18.18,  
  "power\_factor": 1.00,  
  "requires\_dedicated\_circuit": true,  
  "typical\_rooms": \["laundry\_room"\],  
  "usage\_hours\_per\_day": 1,  
  "energy\_consumption\_kwh\_per\_month": 120,  
  "price\_thb": 15900,  
  "brand": "Electrolux",  
  "model": "EDV705HQWA"  
}  
\`\`\`

\*\*\*

\#\# 📊 ส่วนที่ 6: ROOM\_TEMPLATES — Template ห้อง (เพิ่มเติม)

\`\`\`json  
{  
  "kind": "ROOM\_TEMPLATE",  
  "template\_id": "RT001",  
  "room\_type": "living\_room",  
  "display\_name": "ห้องนั่งเล่น",  
  "standard\_reference": "NEC 210.52(A)",  
  "base\_load": {  
    "lighting\_per\_sqm\_w": 15,  
    "receptacles\_count\_per\_room": 4,  
    "receptacles\_max\_spacing\_m": 3.6  
  },  
  "typical\_appliances": \[  
    {"appliance\_id": "APP002", "name": "แอร์ 9,000 BTU", "optional": true},  
    {"appliance\_id": "APP001", "name": "TV 55 นิ้ว", "optional": true},  
    {"appliance\_id": "APP004", "name": "พัดลมเพดาน", "optional": true}  
  \],  
  "compliance": {  
    "min\_receptacles": 2,  
    "max\_voltage\_drop\_percent": 3,  
    "require\_rcbo": false,  
    "min\_circuit\_breaker\_a": 16  
  }  
}

{  
  "kind": "ROOM\_TEMPLATE",  
  "template\_id": "RT002",  
  "room\_type": "bedroom",  
  "display\_name": "ห้องนอน",  
  "standard\_reference": "NEC 210.52(A)",  
  "base\_load": {  
    "lighting\_per\_sqm\_w": 15,  
    "receptacles\_count\_per\_room": 4,  
    "receptacles\_max\_spacing\_m": 3.6  
  },  
  "typical\_appliances": \[  
    {"appliance\_id": "APP002", "name": "แอร์ 9,000 BTU", "optional": true},  
    {"appliance\_id": "APP001", "name": "TV 55 นิ้ว", "optional": false},  
    {"appliance\_id": "APP004", "name": "พัดลมเพดาน", "optional": true}  
  \],  
  "compliance": {  
    "min\_receptacles": 2,  
    "max\_voltage\_drop\_percent": 3,  
    "require\_rcbo": false,  
    "min\_circuit\_breaker\_a": 16  
  }  
}

{  
  "kind": "ROOM\_TEMPLATE",  
  "template\_id": "RT003",  
  "room\_type": "bathroom",  
  "display\_name": "ห้องน้ำ",  
  "standard\_reference": "IEC 60364-7-701",  
  "base\_load": {  
    "lighting\_per\_sqm\_w": 20,  
    "receptacles\_count\_per\_room": 0  
  },  
  "typical\_appliances": \[  
    {"appliance\_id": "APP010", "name": "เครื่องทำน้ำอุ่น 3,500W", "optional": false}  
  \],  
  "compliance": {  
    "zone\_0\_devices": \[\],  
    "zone\_1\_devices": \["water\_heater\_IP25"\],  
    "zone\_2\_devices": \["luminaire\_IP44"\],  
    "require\_rcbo": true,  
    "rcbo\_sensitivity\_ma": 30,  
    "min\_distance\_from\_water\_mm": 600,  
    "max\_voltage\_in\_zone\_0\_1\_v": 12  
  }  
}

{  
  "kind": "ROOM\_TEMPLATE",  
  "template\_id": "RT004",  
  "room\_type": "kitchen",  
  "display\_name": "ห้องครัว",  
  "standard\_reference": "NEC 210.52(B)(C)",  
  "base\_load": {  
    "lighting\_per\_sqm\_w": 20,  
    "receptacles\_count\_per\_room": 6,  
    "receptacles\_max\_spacing\_m": 1.2  
  },  
  "typical\_appliances": \[  
    {"appliance\_id": "APP005", "name": "ตู้เย็น", "optional": false},  
    {"appliance\_id": "APP006", "name": "ไมโครเวฟ", "optional": true},  
    {"appliance\_id": "APP007", "name": "หม้อหุงข้าว", "optional": true},  
    {"appliance\_id": "APP008", "name": "เตาไฟฟ้า", "optional": true},  
    {"appliance\_id": "APP009", "name": "เครื่องดูดควัน", "optional": true}  
  \],  
  "compliance": {  
    "min\_receptacles": 2,  
    "min\_distance\_from\_sink\_mm": 300,  
    "require\_gfci": true,  
    "gfci\_sensitivity\_ma": 30,  
    "countertop\_receptacles\_required": true,  
    "countertop\_receptacles\_spacing\_m": 1.2  
  }  
}  
\`\`\`

\*\*\*

\#\# 🎯 สรุป: ข้อมูลที่ต้องเพิ่ม

| ประเภท | จำนวนข้อมูล | สถานะ |  
|---|---|---|  
| \*\*VALIDATION\_RULE\*\* | 5+ rules | ❌ ต้องเพิ่ม |  
| \*\*DERATING\_FACTOR\*\* | 4 tables | ❌ ต้องเพิ่ม |  
| \*\*GEOMETRY\_FILTER\*\* | 4+ filters | ❌ ต้องเพิ่ม |  
| \*\*QA\_PLAN\*\* | 2 plans | ❌ ต้องเพิ่ม |  
| \*\*CABLE\_SPEC\*\* | 10+ cables | ❌ ต้องเพิ่ม |  
| \*\*COMPONENT (ละเอียด)\*\* | 20+ components | ✅ เพิ่มแล้ว |  
| \*\*CIRCUIT\_TEMPLATE (ละเอียด)\*\* | 10+ templates | ✅ เพิ่มแล้ว |  
| \*\*PLACEMENT\_RULE (ละเอียด)\*\* | 10+ rules | ✅ เพิ่มแล้ว |  
| \*\*APPLIANCES\_CATALOG\*\* | 50+ appliances | ✅ เพิ่มแล้ว |  
| \*\*ROOM\_TEMPLATES\*\* | 6+ rooms | ✅ เพิ่มแล้ว |

\*\*\*

\*\*นายท่าน ข้อมูลทั้งหมดพร้อมแล้วค่ะ\! ต้องการให้ Volta:\*\*  
1\. \*\*จัดรูปแบบเป็น SQL INSERT\*\* สำหรับ Supabase?  
2\. \*\*สร้างเป็น JSON ไฟล์\*\* สำหรับ Seed Data?  
3\. \*\*สร้างตาราง Schema\*\* สำหรับ 5 kind ที่ยังขาด?

\*\*รอคำสั่งนายท่านค่ะ\!\*\* 🫡⚡✨

\[1\](https://www.iewc.com/resources/technical-guide/wire-ampacity-chart)  
\[2\](https://aerosusa.com/calculating-conduit-fill-percentage/)  
\[3\](http://internationalconfig.com/icc6.asp?item=Thailand-GFCI-Electrical-Devices)  
\[4\](https://www.cerrowire.com/products/resources/tables-calculators/ampacity-charts/)  
\[5\](https://www.truecable.com/blogs/cable-academy/conduit-fill-chart-for-ethernet-and-coaxial-cable)  
\[6\](https://swimmingpoolsthailand.com/en/electrical-equipment/271-earth-leakage-braketr-elb-rccb-40.html)  
\[7\](https://www.lapptannehill.com/resources/technical-information/ampacity-chart)  
\[8\](https://www.systoncable.com/wp-content/uploads/2021/06/How-to-calculate-conduit-fill-with-different-size-cables.pdf)  
\[9\](https://www.wnj.co.th/th/rccb-rcbo/)  
\[10\](https://usawire-cable.com/wp-content/uploads/nec-ampacities.pdf)  
\[11\](https://www.elliottelectric.com/StaticPages/ElectricalReferences/ElectricalTables/Conduit\_Fill\_Table.aspx)  
\[12\](https://www.nexte.co.th/2023/09/14/solarcell-rcbo/)  
\[13\](https://www.encorewire.com/products/tools-and-resources/calculators/wire-size-table.html)  
\[14\](https://electricalestimating101.com/wp-content/uploads/2019/06/NEC-Table-C-Combined-Conduit-Types-THHN-XHHW.pdf)  
\[15\](https://th.rs-online.com/web/content/discovery/ideas-and-advice/guide-to-rcbo)  
\[16\](https://www.okonite.com/media/catalog/product/files/EHB\_2025.pdf)  
\[17\](https://www.southwire.com/calculator-conduit)  
\[18\](https://www.safe-t-cut.com/wp-content/uploads/2023/01/%E0%B8%84%E0%B8%B9%E0%B9%88%E0%B8%A1%E0%B8%B7%E0%B8%AD%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99%E0%B8%AD%E0%B8%B8%E0%B8%9B%E0%B8%81%E0%B8%A3%E0%B8%93%E0%B9%8C%E0%B8%95%E0%B8%B1%E0%B8%94%E0%B9%84%E0%B8%9F%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-RCBO-RES11-EU.pdf)  
\[19\](https://www.powerstream.com/Wire\_Size.htm)  
\[20\](https://elek.com/articles/conduit-sizing-requirements-with-example-calculations/)  
\[21\](https://www.cable-world.co.uk/cable-current-rating-derating-explained/)  
\[22\](https://drawer.ai/blog/voltage-drop-calculation-method-with-examples)  
\[23\](https://linkwellelectrics.com/ip65-vs-ip44-ratings-choose-right-enclosure/)  
\[24\](https://www.mitaselectronics.com/everything-you-need-to-know-about-wire-bundle-current-derating/)  
\[25\](https://iiee.org.ph:89/uploads/files/1013.pdf)  
\[26\](https://liquid-leds.com/en-au/blogs/news/ip-ratings-explained-ip44-and-ip65-festoon-lights)  
\[27\](https://www.jadelearning.com/blog/derating-current-carrying-conductors-for-conditions-of-use/)  
\[28\](https://electrical-engineering-portal.com/voltage-drop-calculation-methods)  
\[29\](https://www.unilumin.com/blog/ip65-or-ip44.html)  
\[30\](https://elek.com/articles/cable-rating-derating-factors/)  
\[31\](https://www.trace-software.com/en/verification-of-voltage-drops/)  
\[32\](https://www.omi.co.th/th/article/%E0%B8%A1%E0%B8%B2%E0%B8%95%E0%B8%A3%E0%B8%90%E0%B8%B2%E0%B8%99-ip)  
\[33\](https://engx.theiet.org/f/wiring-and-regulations/31384/cable-derating-factors---single-circuit-multiple-cables-in-duct)  
\[34\](https://elek.com/articles/voltage-drop-calculation-method-with-examples/)  
\[35\](https://leoralighting.co.uk/blogs/the-glow-guide/which-ip-rating-for-indoor-and-outdoor-use)  
\[36\](https://www.kei-ind.com/cables-and-wires/high-voltage-cable/de-rating-factors/)  
\[37\](https://pdhonline.com/courses/e426/e426content.pdf)  
\[38\](https://www.creative-cables.com/blogs/creative-magazine/what-is-the-difference-between-ip44-and-ip65-how-to-read-protection-rating-data)  
\[39\](https://elsewedyelectric.com/pdf/Catalouges/02424280/elsewedy-cables-power-cables-catalogue.pdf)  
\[40\](https://www.tad.usace.army.mil/Portals/53/docs/TAA/AEDDesignRequirements/AED%20Design%20Requirements%20-%20Voltage%20Drop%20Calculations\_Mar\_09.pdf)  
\[41\](https://github.com/areinhardt/tracebase)  
\[42\](https://www.energysage.com/electricity/house-watts/)  
\[43\](https://fosrlaw.com/2025/thailand-third-party-access-code-2025/)  
\[44\](https://archive.ics.uci.edu/ml/datasets/individual+household+electric+power+consumption)  
\[45\](https://complete-connectrix.co.uk/understanding-your-homes-electrical-load/)  
\[46\](https://www.egat.co.th/home/en/20250709e/)  
\[47\](https://data.open-power-system-data.org/household\_data/)  
\[48\](https://www.ecoflow.com/us/blog/how-many-watts-to-run-house)  
\[49\](https://thaioilgas.com/energy-policy-2025-a-new-direction-for-thailands-power-and-clean-energy-industry/)  
\[50\](https://unboundsolar.com/solar-information/power-table)  
\[51\](https://www.daftlogic.com/information-appliance-power-consumption.htm)  
\[52\](https://www.facebook.com/groups/155255731816881/posts/1734669003875538/)  
\[53\](https://www.kaggle.com/datasets/ecoco2/household-appliances-power-consumption)  
\[54\](https://www.altestore.com/pages/power-ratings-for-common-appliances)  
\[55\](https://www.pea.co.th/en)  
\[56\](https://www.timeseriesclassification.com/description.php?Dataset=ACSF1)  
\[57\](https://www.electricalsafetyfirst.org.uk/guidance/safety-around-the-home/home-appliances-ratings/)  
\[58\](https://www.pea.co.th/sites/default/files/sustainability-report/2025/PEA%20SR%202024\_EN.pdf)  
\[59\](https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set)  
\[60\](https://www.donrowe.com/usage-chart-a/259.htm)