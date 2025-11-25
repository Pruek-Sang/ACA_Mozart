## **5.1 Purpose (วัตถุประสงค์)**

ไฟล์นี้แสดง **ตัวอย่างการทำงานจริง** ของระบบตั้งแต่ต้นจนจบ:

1. User Requirements (สิ่งที่ user บอก)
    
2. ProjectInputSpec (Spec ที่ RAG สร้าง)
    
3. MCP Output Summary (ผลลัพธ์ที่ MCP คืนมา)
    
4. Notes & Lessons Learned
    

ช่วยให้ RAG "เห็นภาพปลายทาง" ว่า spec แบบไหนทำให้ MCP ทำงานได้ดี

---

## **5.2 Case 1: บ้านเดี่ยว 1 ชั้น 2 ห้องนอน (Small House)**

## **1. User Requirements (Input)**

"ออกแบบไฟฟ้าบ้านเดี่ยว 1 ชั้น
มีห้องนั่งเล่น 1 ห้อง
ห้องนอน 2 ห้อง
ห้องครัว 1 ห้อง
ห้องน้ำ 2 ห้อง

อุปกรณ์:
- แอร์ 12000 BTU x 3 ตัว
- ตู้เย็น 1 ตัว
- โคมไฟ LED ห้องละ 4 ดวง
- ปลั๊กไฟห้องละ 4 จุด
- เครื่องทำน้ำอุ่น 1 ตัว"

## **2. ProjectInputSpec (RAG Generated)**

{
  "project_info": {
    "project_name": "บ้านเดี่ยว 1 ชั้น คุณสมชาย",
    "building_type": "RESIDENTIAL_SINGLE_1F",
    "location": "THAILAND_GENERAL",
    "floor_area_sqm": 120
  },
  "electrical_system": {
    "voltage_system": "TH_1PH_230V",
    "earthing": "TT",
    "main_supply": {
      "type": "UTILITY_GRID",
      "phases": 1
    }
  },
  "rooms": [
    {
      "room_id": "RM-001",
      "room_type": "LIVING_ROOM",
      "floor_level": 1
    },
    {
      "room_id": "RM-002",
      "room_type": "MASTER_BEDROOM",
      "floor_level": 1
    },
    {
      "room_id": "RM-003",
      "room_type": "BEDROOM",
      "floor_level": 1
    },
    {
      "room_id": "RM-004",
      "room_type": "KITCHEN",
      "floor_level": 1
    },
    {
      "room_id": "RM-005",
      "room_type": "BATHROOM",
      "floor_level": 1
    },
    {
      "room_id": "RM-006",
      "room_type": "BATHROOM",
      "floor_level": 1
    }
  ],
  "loads": [
    {"load_id": "L-001", "room_id": "RM-001", "device_code": "AC_12000BTU", "qty": 1},
    {"load_id": "L-002", "room_id": "RM-001", "device_code": "LED_DOWNLIGHT_9W", "qty": 4},
    {"load_id": "L-003", "room_id": "RM-001", "device_code": "SOCKET_16A", "qty": 4},
    {"load_id": "L-004", "room_id": "RM-002", "device_code": "AC_12000BTU", "qty": 1},
    {"load_id": "L-005", "room_id": "RM-002", "device_code": "LED_DOWNLIGHT_9W", "qty": 4},
    {"load_id": "L-006", "room_id": "RM-002", "device_code": "SOCKET_16A", "qty": 4},
    {"load_id": "L-007", "room_id": "RM-003", "device_code": "AC_12000BTU", "qty": 1},
    {"load_id": "L-008", "room_id": "RM-003", "device_code": "LED_DOWNLIGHT_9W", "qty": 4},
    {"load_id": "L-009", "room_id": "RM-003", "device_code": "SOCKET_16A", "qty": 4},
    {"load_id": "L-010", "room_id": "RM-004", "device_code": "REFRIGERATOR_200W", "qty": 1},
    {"load_id": "L-011", "room_id": "RM-004", "device_code": "LED_DOWNLIGHT_9W", "qty": 4},
    {"load_id": "L-012", "room_id": "RM-004", "device_code": "SOCKET_16A", "qty": 4},
    {"load_id": "L-013", "room_id": "RM-005", "device_code": "WATER_HEATER_3500W", "qty": 1},
    {"load_id": "L-014", "room_id": "RM-005", "device_code": "LED_DOWNLIGHT_9W", "qty": 2},
    {"load_id": "L-015", "room_id": "RM-005", "device_code": "SOCKET_16A_WP", "qty": 1},
    {"load_id": "L-016", "room_id": "RM-006", "device_code": "LED_DOWNLIGHT_9W", "qty": 2},
    {"load_id": "L-017", "room_id": "RM-006", "device_code": "SOCKET_16A_WP", "qty": 1}
  ],
  "constraints": {
    "rule_profile_id": "TH_RESIDENTIAL_LV",
    "user_constraints": [
      {"rcbo_for_bathroom": true},
      {"separate_ac_circuits": true}
    ]
  }
}

## **5.3 Case 2: บ้านเดี่ยว 2 ชั้น 3 ห้องนอน (Medium House)**

## **1. User Requirements**

"ออกแบบบ้าน 2 ชั้น พื้นที่ 180 ตร.ม.

ชั้น 1:
- ห้องนั่งเล่น + ห้องรับแขก
- ห้องครัว
- ห้องน้ำ 1 ห้อง
- ห้องซักผ้า

ชั้น 2:
- ห้องนอนใหญ่ 1 ห้อง (มีห้องน้ำในตัว)
- ห้องนอนเล็ก 2 ห้อง
- ห้องน้ำ 1 ห้อง

อุปกรณ์:
- แอร์ 18000 BTU x 1 (ห้องนั่งเล่น)
- แอร์ 12000 BTU x 3 (ห้องนอน)
- เตาไฟฟ้า 3000W
- เครื่องซักผ้า 800W
- เครื่องทำน้ำอุ่น 3500W x 2
- ตู้เย็น 200W
- โคมไฟ LED ห้องละ 4-6 ดวง
- ปลั๊กห้องละ 4-8 จุด"

## **2. ProjectInputSpec (Simplified)**

{
  "project_info": {
    "project_name": "บ้าน 2 ชั้น คุณนภา",
    "building_type": "RESIDENTIAL_SINGLE_2F",
    "floor_area_sqm": 180
  },
  "electrical_system": {
    "voltage_system": "TH_1PH_230V",
    "earthing": "TT"
  },
  "rooms": [
    // ชั้น 1: 4 ห้อง
    {"room_id": "RM-101", "room_type": "LIVING_ROOM", "floor_level": 1},
    {"room_id": "RM-102", "room_type": "KITCHEN", "floor_level": 1},
    {"room_id": "RM-103", "room_type": "BATHROOM", "floor_level": 1},
    {"room_id": "RM-104", "room_type": "UTILITY", "floor_level": 1},
    // ชั้น 2: 4 ห้อง
    {"room_id": "RM-201", "room_type": "MASTER_BEDROOM", "floor_level": 2},
    {"room_id": "RM-202", "room_type": "BEDROOM", "floor_level": 2},
    {"room_id": "RM-203", "room_type": "BEDROOM", "floor_level": 2},
    {"room_id": "RM-204", "room_type": "BATHROOM", "floor_level": 2}
  ],
  "loads": [
    // Total: 25 loads (simplified)
    {"load_id": "L-001", "room_id": "RM-101", "device_code": "AC_18000BTU", "qty": 1},
    {"load_id": "L-002", "room_id": "RM-102", "device_code": "ELECTRIC_STOVE_3000W", "qty": 1},
    // ... etc
  ],
  "constraints": {
    "rule_profile_id": "TH_RESIDENTIAL_LV",
    "user_constraints": [
      {"split_kitchen_circuit": true},
      {"separate_ac_circuits": true},
      {"rcbo_for_bathroom": true}
    ]
  }
}

## **3. MCP Output Summary**

{
  "status": "SUCCESS",
  "summary": {
    "total_circuits": 20,
    "total_load_kw": 21.8,
    "total_apparent_power_kva": 24.5,
    "main_breaker": "2P-80A",
    "panel_board": "24-way DIN Rail Consumer Unit",
    "estimated_cost_thb": 285000
  },
  "circuits": [
    {"id": "C01", "name": "MAIN", "breaker": "2P-80A"},
    // ชั้น 1
    {"id": "C02", "name": "RM-101-AC-18K", "breaker": "1P-32A-RCBO", "load_a": 26.0},
    {"id": "C03", "name": "LIGHTING-FLOOR1", "breaker": "1P-16A-MCB"},
    {"id": "C04", "name": "SOCKET-FLOOR1-1", "breaker": "1P-20A-RCBO"},
    {"id": "C05", "name": "SOCKET-FLOOR1-2", "breaker": "1P-20A-RCBO"},
    {"id": "C06", "name": "RM-102-STOVE", "breaker": "1P-20A-RCBO", "load_a": 13.0},
    {"id": "C07", "name": "RM-102-FRIDGE", "breaker": "1P-16A-MCB"},
    {"id": "C08", "name": "RM-103-HEATER", "breaker": "1P-20A-RCBO", "load_a": 15.2},
    {"id": "C09", "name": "RM-104-WASHER", "breaker": "1P-16A-RCBO", "load_a": 3.5},
    // ชั้น 2
    {"id": "C10", "name": "RM-201-AC", "breaker": "1P-20A-RCBO", "load_a": 16.5},
    {"id": "C11", "name": "RM-202-AC", "breaker": "1P-20A-RCBO", "load_a": 16.5},
    {"id": "C12", "name": "RM-203-AC", "breaker": "1P-20A-RCBO", "load_a": 16.5},
    {"id": "C13", "name": "LIGHTING-FLOOR2", "breaker": "1P-16A-MCB"},
    {"id": "C14", "name": "SOCKET-FLOOR2-1", "breaker": "1P-20A-RCBO"},
    {"id": "C15", "name": "SOCKET-FLOOR2-2", "breaker": "1P-20A-RCBO"},
    {"id": "C16", "name": "RM-201-EN-HEATER", "breaker": "1P-20A-RCBO", "load_a": 15.2},
    {"id": "C17", "name": "RM-204-BATH", "breaker": "1P-16A-RCBO"}
  ],
  "cables": {
    "main_cable": "NYY 2C x 25 sq.mm",
    "floor1_distribution": "THW 4-6 sq.mm",
    "floor2_distribution": "THW 4-6 sq.mm"
  },
  "compliance": {
    "vst_2564": "PASS",
    "voltage_drop_max": "2.9%",
    "load_balance": "GOOD (floor1: 45%, floor2: 55%)"
  }
}



