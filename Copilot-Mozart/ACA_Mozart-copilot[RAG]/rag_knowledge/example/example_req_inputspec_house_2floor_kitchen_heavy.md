# Example: 2-Floor House with Heavy Kitchen Loads

## 1. ProjectRequirements (input ฝั่งมนุษย์)

```json
{
  "project_name": "House B - 2-Floor with Heavy Kitchen",
  "building_type": "residential",
  "voltage_system": "TH_1PH_230V",
  "location": "Bangkok",
  "rooms": [
    {"name": "ห้องนั่งเล่น 1F", "type": "living_room", "area_m2": 30.0},
    {"name": "ครัว 1F", "type": "kitchen", "area_m2": 15.0},
    {"name": "ห้องน้ำ 1F", "type": "bathroom", "area_m2": 4.0},
    {"name": "ห้องนอนใหญ่ 2F", "type": "bedroom", "area_m2": 18.0},
    {"name": "ห้องนอนเล็ก 2F", "type": "bedroom", "area_m2": 12.0},
    {"name": "ห้องน้ำ 2F", "type": "bathroom", "area_m2": 5.0}
  ],
  "loads": [
    {"room_name": "ห้องนั่งเล่น 1F", "device": "AC_18000BTU", "quantity": 1},
    {"room_name": "ห้องนั่งเล่น 1F", "device": "OUTLET_16A", "quantity": 6},
    {"room_name": "ครัว 1F", "device": "INDUCTION_COOKER_3000W", "quantity": 1},
    {"room_name": "ครัว 1F", "device": "MICROWAVE_1500W", "quantity": 1},
    {"room_name": "ครัว 1F", "device": "RICE_COOKER_800W", "quantity": 1},
    {"room_name": "ครัว 1F", "device": "REFRIGERATOR_300W", "quantity": 1},
    {"room_name": "ครัว 1F", "device": "OUTLET_16A", "quantity": 8},
    {"room_name": "ห้องน้ำ 1F", "device": "WATER_HEATER_3500W", "quantity": 1},
    {"room_name": "ห้องนอนใหญ่ 2F", "device": "AC_12000BTU", "quantity": 1},
    {"room_name": "ห้องนอนใหญ่ 2F", "device": "OUTLET_16A", "quantity": 4},
    {"room_name": "ห้องนอนเล็ก 2F", "device": "AC_9000BTU", "quantity": 1},
    {"room_name": "ห้องนอนเล็ก 2F", "device": "OUTLET_16A", "quantity": 3},
    {"room_name": "ห้องน้ำ 2F", "device": "WATER_HEATER_3500W", "quantity": 1}
  ],
  "user_constraints": [
    "split_kitchen_circuit",
    "rcd_for_all_outlets",
    "separate_ac_circuits"
  ]
}
```

## 2. ProjectInputSpec (expected output สำหรับ MCP)

```json
{
  "project_info": {
    "project_name": "House B - 2-Floor with Heavy Kitchen",
    "building_type": "RESIDENTIAL",
    "spec_version": "2.0"
  },
  "electrical_system": {
    "voltage_system": "TH_1PH_230V",
    "earthing": "TT"
  },
  "rooms": [
    {
      "room_id": "R1",
      "name": "ห้องนั่งเล่น 1F",
      "room_type": "LIVING",
      "template_code": "ROOMT-LIVING-LARGE",
      "area_m2": 30.0
    },
    {
      "room_id": "R2",
      "name": "ครัว 1F",
      "room_type": "KITCHEN",
      "template_code": "ROOMT-KITCHEN-HEAVY",
      "area_m2": 15.0
    },
    {
      "room_id": "R3",
      "name": "ห้องน้ำ 1F",
      "room_type": "BATHROOM",
      "template_code": "ROOMT-BATHROOM-STD",
      "area_m2": 4.0
    },
    {
      "room_id": "R4",
      "name": "ห้องนอนใหญ่ 2F",
      "room_type": "BEDROOM",
      "template_code": "ROOMT-BEDROOM-STD",
      "area_m2": 18.0
    },
    {
      "room_id": "R5",
      "name": "ห้องนอนเล็ก 2F",
      "room_type": "BEDROOM",
      "template_code": "ROOMT-BEDROOM-STD",
      "area_m2": 12.0
    },
    {
      "room_id": "R6",
      "name": "ห้องน้ำ 2F",
      "room_type": "BATHROOM",
      "template_code": "ROOMT-BATHROOM-STD",
      "area_m2": 5.0
    }
  ],
  "loads": [
    {
      "load_id": "L1",
      "room_id": "R1",
      "device_code": "AC-18000BTU",
      "qty": 1,
      "notes": "Large living room AC"
    },
    {
      "load_id": "L2",
      "room_id": "R1",
      "device_code": "SOCKET-16A",
      "qty": 6,
      "notes": "Living room outlets"
    },
    {
      "load_id": "L3",
      "room_id": "R2",
      "device_code": "INDUCTION-3000W",
      "qty": 1,
      "notes": "Induction cooker - high load"
    },
    {
      "load_id": "L4",
      "room_id": "R2",
      "device_code": "MICROWAVE-1500W",
      "qty": 1,
      "notes": "Microwave oven"
    },
    {
      "load_id": "L5",
      "room_id": "R2",
      "device_code": "RICECOOK-800W",
      "qty": 1,
      "notes": "Rice cooker"
    },
    {
      "load_id": "L6",
      "room_id": "R2",
      "device_code": "REFRIG-300W",
      "qty": 1,
      "notes": "Refrigerator"
    },
    {
      "load_id": "L7",
      "room_id": "R2",
      "device_code": "SOCKET-16A",
      "qty": 8,
      "notes": "Kitchen outlets - many appliances"
    },
    {
      "load_id": "L8",
      "room_id": "R3",
      "device_code": "HEATER-3500W",
      "qty": 1,
      "notes": "Water heater 1F"
    },
    {
      "load_id": "L9",
      "room_id": "R4",
      "device_code": "AC-12000BTU",
      "qty": 1,
      "notes": "Master bedroom AC"
    },
    {
      "load_id": "L10",
      "room_id": "R4",
      "device_code": "SOCKET-16A",
      "qty": 4,
      "notes": "Master bedroom outlets"
    },
    {
      "load_id": "L11",
      "room_id": "R5",
      "device_code": "AC-9000BTU",
      "qty": 1,
      "notes": "Second bedroom AC"
    },
    {
      "load_id": "L12",
      "room_id": "R5",
      "device_code": "SOCKET-16A",
      "qty": 3,
      "notes": "Second bedroom outlets"
    },
    {
      "load_id": "L13",
      "room_id": "R6",
      "device_code": "HEATER-3500W",
      "qty": 1,
      "notes": "Water heater 2F"
    }
  ],
  "constraints": {
    "rule_profile_id": "TH_RESIDENTIAL_LV",
    "user_constraints": [
      "split_kitchen_circuit",
      "rcd_for_all_outlets",
      "separate_ac_circuits"
    ]
  }
}
```

## 3. Notes

### Special Considerations for Heavy Kitchen

**Why "ROOMT-KITCHEN-HEAVY"?**
- Kitchen has multiple high-power appliances (induction 3kW, microwave 1.5kW)
- Total kitchen load exceeds typical residential kitchen
- Template signals MCP to allocate dedicated circuits

**Split Kitchen Circuit Constraint:**
- The `split_kitchen_circuit` constraint tells MCP to:
  - Separate heavy appliances (induction, microwave) into dedicated circuits
  - Separate general outlets from appliance circuits
  - This prevents overloading and improves safety

### Device Code Mapping (Extended)
- `INDUCTION_COOKER_3000W` → `INDUCTION-3000W`
- `MICROWAVE_1500W` → `MICROWAVE-1500W`
- `RICE_COOKER_800W` → `RICECOOK-800W`
- `REFRIGERATOR_300W` → `REFRIG-300W`
- `AC_18000BTU` → `AC-18000BTU`

### Business Rules Enforced
1. **Multi-Floor Support**: Rooms labeled with floor info (1F, 2F)
2. **Heavy Load Detection**: Kitchen flagged as HEAVY based on device types
3. **Constraint Propagation**: All 3 constraints passed to MCP for circuit design
4. **Template Selection**: 
   - `ROOMT-LIVING-LARGE` for 30m² living room (vs STD for <25m²)
   - `ROOMT-KITCHEN-HEAVY` for high-power kitchen loads

### Why This Example?
Tests RAG's ability to:
- Handle complex multi-floor scenarios
- Recognize heavy load patterns
- Map constraints appropriately
- Select appropriate templates based on load characteristics
- This is a **realistic residential project** that requires smart circuit planning
