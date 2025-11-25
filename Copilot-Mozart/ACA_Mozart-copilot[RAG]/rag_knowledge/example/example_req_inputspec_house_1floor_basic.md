# Example: Basic 1-Floor House (2BR, 1Bath)

## 1. ProjectRequirements (input ฝั่งมนุษย์)

```json
{
  "project_name": "House A - Basic",
  "building_type": "residential",
  "voltage_system": "TH_1PH_230V",
  "location": "Bangkok",
  "rooms": [
    {"name": "ห้องนั่งเล่น", "type": "living_room", "area_m2": 25.0},
    {"name": "ห้องนอนใหญ่", "type": "bedroom", "area_m2": 15.0},
    {"name": "ห้องนอนเล็ก", "type": "bedroom", "area_m2": 12.0},
    {"name": "ห้องน้ำ", "type": "bathroom", "area_m2": 5.0},
    {"name": "ครัว", "type": "kitchen", "area_m2": 10.0}
  ],
  "loads": [
    {"room_name": "ห้องนั่งเล่น", "device": "AC_12000BTU", "quantity": 1},
    {"room_name": "ห้องนั่งเล่น", "device": "OUTLET_16A", "quantity": 4},
    {"room_name": "ห้องนอนใหญ่", "device": "AC_9000BTU", "quantity": 1},
    {"room_name": "ห้องนอนใหญ่", "device": "OUTLET_16A", "quantity": 3},
    {"room_name": "ห้องนอนเล็ก", "device": "OUTLET_16A", "quantity": 2},
    {"room_name": "ห้องน้ำ", "device": "WATER_HEATER_3500W", "quantity": 1},
    {"room_name": "ครัว", "device": "OUTLET_16A", "quantity": 4},
    {"room_name": "ครัว", "device": "REFRIGERATOR_200W", "quantity": 1}
  ],
  "user_constraints": [
    "rcd_for_all_outlets"
  ]
}
```

## 2. ProjectInputSpec (expected output สำหรับ MCP)

```json
{
  "project_info": {
    "project_name": "House A - Basic",
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
      "name": "ห้องนั่งเล่น",
      "room_type": "LIVING",
      "template_code": "ROOMT-LIVING-STD",
      "area_m2": 25.0
    },
    {
      "room_id": "R2",
      "name": "ห้องนอนใหญ่",
      "room_type": "BEDROOM",
      "template_code": "ROOMT-BEDROOM-STD",
      "area_m2": 15.0
    },
    {
      "room_id": "R3",
      "name": "ห้องนอนเล็ก",
      "room_type": "BEDROOM",
      "template_code": "ROOMT-BEDROOM-STD",
      "area_m2": 12.0
    },
    {
      "room_id": "R4",
      "name": "ห้องน้ำ",
      "room_type": "BATHROOM",
      "template_code": "ROOMT-BATHROOM-STD",
      "area_m2": 5.0
    },
    {
      "room_id": "R5",
      "name": "ครัว",
      "room_type": "KITCHEN",
      "template_code": "ROOMT-KITCHEN-STD",
      "area_m2": 10.0
    }
  ],
  "loads": [
    {
      "load_id": "L1",
      "room_id": "R1",
      "device_code": "AC-12000BTU",
      "qty": 1,
      "notes": "Living room air conditioner"
    },
    {
      "load_id": "L2",
      "room_id": "R1",
      "device_code": "SOCKET-16A",
      "qty": 4,
      "notes": "Living room outlets"
    },
    {
      "load_id": "L3",
      "room_id": "R2",
      "device_code": "AC-9000BTU",
      "qty": 1,
      "notes": "Master bedroom AC"
    },
    {
      "load_id": "L4",
      "room_id": "R2",
      "device_code": "SOCKET-16A",
      "qty": 3,
      "notes": "Master bedroom outlets"
    },
    {
      "load_id": "L5",
      "room_id": "R3",
      "device_code": "SOCKET-16A",
      "qty": 2,
      "notes": "Second bedroom outlets"
    },
    {
      "load_id": "L6",
      "room_id": "R4",
      "device_code": "HEATER-3500W",
      "qty": 1,
      "notes": "Water heater"
    },
    {
      "load_id": "L7",
      "room_id": "R5",
      "device_code": "SOCKET-16A",
      "qty": 4,
      "notes": "Kitchen outlets"
    },
    {
      "load_id": "L8",
      "room_id": "R5",
      "device_code": "REFRIG-200W",
      "qty": 1,
      "notes": "Refrigerator"
    }
  ],
  "constraints": {
    "rule_profile_id": "TH_RESIDENTIAL_LV",
    "user_constraints": [
      "rcd_for_all_outlets"
    ]
  }
}
```

## 3. Notes

### Mapping Rules Applied
- **Room Types**: 
  - `living_room` → `LIVING` (template: `ROOMT-LIVING-STD`)
  - `bedroom` → `BEDROOM` (template: `ROOMT-BEDROOM-STD`)
  - `bathroom` → `BATHROOM` (template: `ROOMT-BATHROOM-STD`)
  - `kitchen` → `KITCHEN` (template: `ROOMT-KITCHEN-STD`)

- **Device Codes**:
  - `AC_12000BTU` → `AC-12000BTU`
  - `AC_9000BTU` → `AC-9000BTU`
  - `OUTLET_16A` → `SOCKET-16A`
  - `WATER_HEATER_3500W` → `HEATER-3500W`
  - `REFRIGERATOR_200W` → `REFRIG-200W`

### Business Rules
1. **Room IDs**: Sequential `R1`, `R2`, etc.
2. **Load IDs**: Sequential `L1`, `L2`, etc.
3. **Load-Room Linking**: Each load references a room via `room_id`
4. **RCD Constraint**: Preserved in `user_constraints` for MCP to implement
5. **Rule Profile**: Default to `TH_RESIDENTIAL_LV` for Thai residential projects
6. **Earthing**: Default to `TT` system for Thai residential

### Why This Example?
This represents the **sanity check** case:
- Simple structure
- Common residential scenario
- All required fields present
- No edge cases
- Should always pass validation
