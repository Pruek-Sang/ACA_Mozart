# Example: Incomplete Data (Error Handling Case)

## 1. ProjectRequirements (input ฝั่งมนุษย์ - ข้อมูลไม่ครบ)

```json
{
  "project_name": "House C - Incomplete",
  "building_type": "residential",
  "voltage_system": "TH_1PH_230V",
  "location": "Bangkok",
  "rooms": [
    {"name": "ห้องนั่งเล่น", "type": "living_room", "area_m2": 20.0},
    {"name": "ห้องนอน 1", "area_m2": 15.0},
    {"name": "ห้องอเนกประสงค์"},
    {"name": "ห้องน้ำ", "type": "bathroom"}
  ],
  "loads": [
    {"room_name": "ห้องนั่งเล่น", "device": "AC_12000BTU", "quantity": 1},
    {"room_name": "ห้องที่ไม่มีอยู่", "device": "OUTLET_16A", "quantity": 3},
    {"device": "OUTLET_16A", "quantity": 5}
  ],
  "user_constraints": []
}
```

## 2. Expected Behavior

### ตามนโยบาย Error Policy (Phase 5 ของ HOW_TO_FIX_RAG_v2)

**กรณีที่ 1: Pre-validation Check (ก่อนเรียก LLM)**

RAG Service ต้องตรวจสอบก่อนเรียก LLM:

```json
{
  "status": 400,
  "error": "Insufficient project requirements",
  "detail": "Missing critical information",
  "validation_errors": [
    "Room 'ห้องนอน 1' missing field: type",
    "Room 'ห้องอเนกประสงค์' missing fields: type, area_m2",
    "Room 'ห้องน้ำ' missing field: area_m2",
    "Load references non-existent room: 'ห้องที่ไม่มีอยู่'",
    "Load missing field: room_name (index 2)"
  ],
  "required_fields": {
    "room": ["name", "type"],
    "load": ["room_name", "device", "quantity"]
  },
  "suggestion": "Please provide complete room types and ensure all loads reference existing rooms"
}
```

**กรณีที่ 2: LLM Inference Mode (ถ้านโยบายอนุญาตให้ LLM เดา)**

ถ้าระบบกำหนดให้ LLM พยายามเติมข้อมูล:

```json
{
  "project_input": {
    "project_info": {
      "project_name": "House C - Incomplete",
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
        "area_m2": 20.0
      },
      {
        "room_id": "R2",
        "name": "ห้องนอน 1",
        "room_type": "BEDROOM_INFERRED",
        "template_code": "ROOMT-BEDROOM-STD",
        "area_m2": 15.0
      },
      {
        "room_id": "R3",
        "name": "ห้องอเนกประสงค์",
        "room_type": "MULTIPURPOSE_INFERRED",
        "template_code": "ROOMT-GENERIC-STD",
        "area_m2": null
      },
      {
        "room_id": "R4",
        "name": "ห้องน้ำ",
        "room_type": "BATHROOM",
        "template_code": "ROOMT-BATHROOM-STD",
        "area_m2": null
      }
    ],
    "loads": [
      {
        "load_id": "L1",
        "room_id": "R1",
        "device_code": "AC-12000BTU",
        "qty": 1,
        "notes": "OK - complete"
      },
      {
        "load_id": "L2_INVALID",
        "room_id": "UNKNOWN",
        "device_code": "SOCKET-16A",
        "qty": 3,
        "notes": "ERROR: room 'ห้องที่ไม่มีอยู่' not found - skipped"
      },
      {
        "load_id": "L3_INCOMPLETE",
        "room_id": "UNKNOWN",
        "device_code": "SOCKET-16A",
        "qty": 5,
        "notes": "WARNING: no room_name specified - assigned to UNKNOWN"
      }
    ],
    "constraints": {
      "rule_profile_id": "TH_RESIDENTIAL_LV",
      "user_constraints": []
    }
  },
  "standards_profile": {
    "rule_profile_id": "TH_RESIDENTIAL_LV",
    "notes": "Generated with incomplete data - contains inferences"
  },
  "llm_metadata": {
    "model": "gemini-1.5-pro",
    "retrieved_docs": ["DOC_MCP_CONTRACT"],
    "temperature": 0.0,
    "timestamp": "2025-11-24T02:00:00Z"
  },
  "warnings": [
    "Room 'ห้องนอน 1' type inferred from name pattern",
    "Room 'ห้องอเนกประสงค์' type inferred as MULTIPURPOSE",
    "Room 'ห้องน้ำ' and 'ห้องอเนกประสงค์' missing area - may affect calculations",
    "Load L2 references invalid room - should be removed or corrected",
    "Load L3 missing room assignment - cannot be properly routed"
  ]
}
```

## 3. Notes

### Error Policy Options

**แนวทาง A: Strict Validation (แนะนำ)**
- ตรวจสอบก่อนเรียก LLM
- คืน HTTP 400 พร้อมรายละเอียดที่ขาด
- ประหยัด LLM calls
- ผู้ใช้ได้รับ feedback ชัดเจน

**แนวทาง B: LLM Inference**
- ให้ LLM พยายามเติมข้อมูล
- ต้องส่ง warnings กลับไปด้วย
- เสี่ยงต่อการเดาผิด
- เหมาะกับ UI แบบ conversational ที่จะถามตอบต่อ

### Recommended Implementation

```python
def validate_requirements(req: ProjectRequirements) -> List[str]:
    """
    Pre-validate requirements before calling LLM
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check rooms
    room_names = set()
    for i, room in enumerate(req.rooms):
        if not room.type:
            errors.append(f"Room '{room.name}' missing field: type")
        if not room.area_m2:
            errors.append(f"Room '{room.name}' missing field: area_m2")
        room_names.add(room.name)
    
    # Check loads
    for i, load in enumerate(req.loads):
        if not load.room_name:
            errors.append(f"Load (index {i}) missing field: room_name")
        elif load.room_name not in room_names:
            errors.append(f"Load references non-existent room: '{load.room_name}'")
        
        if not load.device:
            errors.append(f"Load (index {i}) missing field: device")
    
    return errors
```

### Why This Example?

Tests:
1. **Pre-validation logic** - Can RAG detect incomplete data before wasting LLM calls?
2. **Error messaging** - Does API return helpful errors?
3. **Policy enforcement** - Does system follow strict vs lenient mode?
4. **Trust logging** - Even failed requests should be logged
5. **User experience** - Clear feedback helps users fix their input

### Integration with Trust Log

Even for failed validation, create trust record:
```python
trust_record = McpSpecTrustRecord(
    request_id=str(uuid.uuid4()),
    project_requirements=req.model_dump(),
    retrieved_doc_ids=[],  # No retrieval happened
    llm_model="N/A",
    raw_llm_output="",
    parse_success=False,
    validation_errors=errors,
    project_input=None,
    forwarded_to_mcp=False
)
trust_logger.log_mcp_spec(trust_record)
```

This helps analyze:
- What kind of incomplete data users submit?
- Which fields are most often missing?
- Pattern for improving UI/UX
