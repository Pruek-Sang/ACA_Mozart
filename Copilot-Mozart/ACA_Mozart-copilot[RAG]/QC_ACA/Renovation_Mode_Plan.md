# 🔧 Renovation Mode MVP - Implementation Plan

## 1. เป้าหมาย

**User Story:**
> "บ้านเก่ามิเตอร์ 15A อยากเพิ่มแอร์ 2 ตัว" → Mozart บอก Checklist + ต้องอัพเกรดมิเตอร์มั้ย

**ไม่พยายามรู้ทุกอย่างเกี่ยวกับบ้านเดิม** → ถามน้อย คำนวณแค่ส่วนเพิ่ม

---

## 2. User Flow

```
┌─────────────────────────────────────────────────────────┐
│  User: "บ้านมิเตอร์ 15A มีแอร์ 1 ตัว อยากเพิ่มน้ำอุ่น"   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  [Intent Detection]                                      │
│  Keywords: "เพิ่ม", "ต่อเติม", "อัพเกรด", "มีอยู่แล้ว"    │
│  → mode = "RENOVATION"                                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  [LLM Extract]                                           │
│  - existing_meter: "15A"                                 │
│  - existing_loads: [{device: "AC-12000BTU", qty: 1}]     │
│  - new_loads: [{device: "HEATER-4500W", qty: 1}]         │
│  - room_additions: []                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  [Calculate]                                             │
│  - existing_load_va: 1,200                               │
│  - new_load_va: 4,500                                    │
│  - total_after: 5,700                                    │
│  - meter_capacity: 3,500 (15A × ~230V)                   │
│  - verdict: "UPGRADE_REQUIRED"                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  [Output - Checklist Style]                              │
│  ⚠️ ต้องอัพเกรดมิเตอร์: 15A → 30A                        │
│  🔧 สิ่งที่ต้องซื้อ/ทำ:                                    │
│     1. ขอเพิ่มมิเตอร์ กฟน./กฟภ.                           │
│     2. RCBO 20A + สาย 4mm² สำหรับน้ำอุ่น                  │
│  💰 ประมาณราคา: ~8,000 บาท                               │
│  ⚠️ Disclaimer: ให้ช่างตรวจสอบตู้ก่อนติดตั้ง              │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Data Models

### 3.1 RenovationRequest (Input)

```python
class RenovationRequest(BaseModel):
    """Input for Renovation Mode"""
    # ข้อมูลบ้านเดิม (ถามน้อย)
    existing_meter: Optional[str] = None  # "5A", "15A", "30A", "50A", "ไม่รู้"
    existing_loads: List[LoadInput] = []  # โหลดใหญ่ที่มีอยู่ (แอร์, น้ำอุ่น)
    
    # สิ่งที่ต้องการเพิ่ม
    new_loads: List[LoadInput] = []       # อุปกรณ์ที่ระบุตรงๆ
    room_additions: List[str] = []        # ห้องที่ต่อเติม เช่น "โรงรถ", "ห้องนอน"
    
    # Context
    raw_query: str                        # Query ดิบจาก User
```

### 3.2 RenovationResult (Output)

```python
class RenovationResult(BaseModel):
    """Output for Renovation Mode"""
    # Summary
    existing_load_va: float
    new_load_va: float
    total_after_va: float
    
    # Meter Analysis
    current_meter: str                    # "15A"
    meter_capacity_va: float              # 3,500
    recommended_meter: Optional[str]       # "30A" or None if OK
    upgrade_required: bool
    
    # Checklist
    checklist: List[ChecklistItem]
    
    # Cost Estimate
    estimated_cost_min: int
    estimated_cost_max: int
    
    # Disclaimer
    disclaimer: str = "กรุณาให้ช่างไฟตรวจสอบตู้ MDB ก่อนติดตั้ง"
```

### 3.3 ChecklistItem

```python
class ChecklistItem(BaseModel):
    """Single item in renovation checklist"""
    category: str       # "meter", "breaker", "wire", "labor"
    action: str         # "ขอเพิ่มมิเตอร์ 30A"
    details: str        # "ติดต่อ กฟน./กฟภ. พื้นที่"
    cost_min: int
    cost_max: int
    priority: int       # 1 = ต้องทำ, 2 = แนะนำ, 3 = Optional
```

---

## 4. Room Templates

```python
ROOM_TEMPLATES = {
    "โรงรถ": {
        "loads": [
            {"device": "LIGHT-LED-20W", "qty": 2},
            {"device": "SOCKET-16A", "qty": 2},
        ],
        "optional": [
            {"device": "EV-CHARGER-7KW", "qty": 1, "note": "ถ้ามีรถไฟฟ้า"},
        ]
    },
    "ห้องนอน": {
        "loads": [
            {"device": "LIGHT-LED-20W", "qty": 2},
            {"device": "SOCKET-16A", "qty": 3},
            {"device": "AC-12000BTU", "qty": 1},
        ]
    },
    "ห้องน้ำ": {
        "loads": [
            {"device": "LIGHT-LED-10W", "qty": 1},
            {"device": "FAN-EXHAUST-25W", "qty": 1},
        ],
        "optional": [
            {"device": "HEATER-4500W", "qty": 1, "note": "ถ้าต้องการน้ำอุ่น"},
        ]
    },
    "ห้องครัว": {
        "loads": [
            {"device": "LIGHT-LED-20W", "qty": 3},
            {"device": "SOCKET-16A", "qty": 4},
            {"device": "REFRIG-300W", "qty": 1},
        ],
        "optional": [
            {"device": "INDUCTION-3000W", "qty": 1},
            {"device": "MICROWAVE-1500W", "qty": 1},
        ]
    },
    "ระเบียง": {
        "loads": [
            {"device": "LIGHT-LED-10W", "qty": 2},
            {"device": "SOCKET-16A", "qty": 1},
        ]
    },
}
```

---

## 5. Meter Capacity Table

```python
METER_CAPACITY = {
    "5A": {"va": 1150, "typical": "บ้านเล็ก ไม่มีแอร์"},
    "15A": {"va": 3450, "typical": "บ้านทั่วไป แอร์ 1-2 ตัว"},
    "30A": {"va": 6900, "typical": "บ้าน 2 ชั้น แอร์ 3+ ตัว"},
    "50A": {"va": 11500, "typical": "บ้านใหญ่ หรือ 3 เฟส"},
}

def recommend_meter(total_va: float) -> str:
    """เลือกมิเตอร์ที่เหมาะสม (เผื่อ 30%)"""
    required = total_va * 1.3
    for meter, info in METER_CAPACITY.items():
        if required <= info["va"]:
            return meter
    return "ติดต่อ กฟน./กฟภ. (เกินพิกัดมาตรฐาน)"
```

---

## 6. Files to Create/Modify

### 6.1 New Files

| File | Description |
|------|-------------|
| `app/renovation/models.py` | Data models for Renovation Mode |
| `app/renovation/calculator.py` | Core calculation logic |
| `app/renovation/templates.py` | Room templates |
| `app/renovation/renderer.py` | Format output as Checklist |

### 6.2 Modified Files

| File | Changes |
|------|---------|
| `app/service.py` | Add intent detection for RENOVATION mode |
| `app/routes.py` | (Optional) Add `/api/v1/renovate` endpoint |

---

## 7. Implementation Phases

### Phase 1: Core Logic (Day 1)
- [ ] Create `app/renovation/` folder structure
- [ ] Implement `RenovationRequest` / `RenovationResult` models
- [ ] Implement meter capacity calculation
- [ ] Implement room templates

### Phase 2: LLM Integration (Day 1-2)
- [ ] Update `_extract_loads_from_text` prompt for RENOVATION intent
- [ ] Extract existing_meter, existing_loads, new_loads, room_additions
- [ ] Handle "ต่อเติมโรงรถ" → expand to template loads

### Phase 3: Output Formatting (Day 2)
- [ ] Create Checklist renderer (Markdown)
- [ ] Add cost estimation (hardcoded ranges for MVP)
- [ ] Add disclaimer

### Phase 4: Integration (Day 2)
- [ ] Add intent detection in `_detect_design_intent`
- [ ] Route RENOVATION intent to new handler
- [ ] Return Checklist output instead of Load Table

---

## 8. Example Conversations

### 8.1 Simple Addition
```
User: "บ้านมิเตอร์ 15A อยากเพิ่มน้ำอุ่น"

Mozart:
📊 วิเคราะห์:
- มิเตอร์ปัจจุบัน: 15A (~3,500W)
- น้ำอุ่นใหม่: +4,500W

⚠️ เกินพิกัดมิเตอร์! ต้องอัพเกรด

🔧 สิ่งที่ต้องทำ:
1. ☐ ขอเพิ่มมิเตอร์: 15A → 30A (~2,000 บาท)
2. ☐ ซื้อ RCBO 20A (~500 บาท)
3. ☐ สาย THW 4mm² ~20m (~400 บาท)

💰 ประมาณการ: 3,000-5,000 บาท (ไม่รวมค่าแรง)

⚠️ กรุณาให้ช่างไฟตรวจสอบตู้ MDB ก่อนติดตั้ง
```

### 8.2 Room Addition
```
User: "ต่อเติมโรงรถ อยากติด EV Charger ด้วย"

Mozart:
🚗 โรงรถ (มาตรฐาน):
- ไฟ LED 20W × 2 = 40W
- เต้ารับ 16A × 2 = 360VA
- EV Charger 7kW = 7,000W

📊 รวมโหลดเพิ่ม: 7,400W

⚠️ EV Charger ต้องวงจรเฉพาะ!

🔧 สิ่งที่ต้องทำ:
1. ☐ ตรวจสอบมิเตอร์ปัจจุบัน (ต้อง ≥30A)
2. ☐ เพิ่มวงจร EV Charger: RCBO 32A + สาย 6mm²
3. ☐ เพิ่มวงจรไฟ+เต้ารับ: MCB 16A + สาย 2.5mm²

💰 ประมาณการ: 15,000-25,000 บาท (ไม่รวม EV Charger)

⚠️ กรุณาให้ช่างไฟตรวจสอบตู้ MDB ก่อนติดตั้ง
```

---

## 9. Verification Plan

### Manual Testing
1. ทดสอบ: "บ้านมิเตอร์ 15A อยากเพิ่มแอร์ 2 ตัว"
2. ทดสอบ: "ต่อเติมโรงรถ"
3. ทดสอบ: "เพิ่มห้องน้ำ พร้อมน้ำอุ่น"
4. ทดสอบ: Edge case - "ไม่รู้มิเตอร์เท่าไหร่"

### Success Criteria
- [ ] Intent detected correctly (RENOVATION vs FULL_DESIGN)
- [ ] Meter upgrade warning shows when appropriate
- [ ] Checklist format renders correctly
- [ ] Room templates expand correctly
- [ ] Disclaimer always present

---

## 10. Timeline

| Day | Tasks |
|-----|-------|
| **Day 1** | Core models + Calculator + Templates |
| **Day 2** | LLM prompt update + Output formatting |
| **Day 3** | Integration + Testing + Bug fixes |

**รวม: ~3 วัน**
