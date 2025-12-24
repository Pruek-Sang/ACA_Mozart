# 🛠️ Implementation Plan: LLM Upgrade + Audit Mode

> **วันที่:** 2025-12-24 | **เวลารวม:** 5-7 ชม.

---

## Phase 0: LLM Extraction Upgrade (2-3 ชม.)

**เป้าหมาย:** รองรับ Messy Input + ถามกลับเฉพาะตอนไม่มั่นใจ

### Flow:

```
LLM สกัด + ให้ Confidence Score
              ↓
    ┌── Confidence ≥ 0.7 ──┬── Confidence < 0.7 ──┐
    ↓                       ↓                      
 ✅ ไปต่อเลย            ❓ ถามกลับ
                        "ข้อมูลไม่ชัด: ..."
```

### 0.1 Structured Output + Confidence (1 ชม.)

```python
schema = {
    "type": "object",
    "properties": {
        "rooms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "floor": {"type": "string"},
                    "room_name": {"type": "string"},
                    "confidence": {"type": "number"},  # 🆕 0.0-1.0
                    "loads": {
                        "type": "array",
                        "items": {
                            "device": {"type": "string"},
                            "power_watts": {"type": "number"},
                            "quantity": {"type": "integer"},
                            "user_breaker": {"type": "integer"},
                            "confidence": {"type": "number"}  # 🆕 per load
                        }
                    }
                }
            }
        }
    }
}
```

### 0.2 Few-shot Examples (30 นาที)

```
Input ขยะ: "เต้ารับ ไฟ 6 4"
Output:
{
  "rooms": [{
    "floor": "1",
    "room_name": "ทั่วไป",
    "confidence": 0.6,  # ❓ ไม่มั่นใจ
    "loads": [
      {"device": "เต้ารับ", "quantity": 6, "confidence": 0.8},
      {"device": "ไฟ", "quantity": 4, "confidence": 0.5}
    ]
  }]
}
```

### 0.3 Conditional Ask-back Logic (30 นาที)

```python
def should_ask_back(extracted_data: Dict) -> Tuple[bool, str]:
    """Check if we need to ask user for clarification."""
    low_confidence_items = []
    
    for room in extracted_data.get('rooms', []):
        if room.get('confidence', 1.0) < 0.7:
            low_confidence_items.append(room['room_name'])
        for load in room.get('loads', []):
            if load.get('confidence', 1.0) < 0.7:
                low_confidence_items.append(load['device'])
    
    if low_confidence_items:
        return True, f"ไม่แน่ใจ: {', '.join(low_confidence_items)}"
    return False, ""
```

### 0.4 Test + Debug (30 นาที)

---

## Phase 2-3: Audit Mode (2-3 ชม.)

### Phase 2: Compare User vs Auto (1 ชม.)

```python
def validate_user_specs(user_specs, auto_values):
    if user_specs.get('user_breaker'):
        if user_specs['user_breaker'] < auto_values['breaker_rating']:
            return {'status': 'FAIL', 'reason': '...'}
    return {'status': 'PASS'}
```

### Phase 3: Formatter Audit Section (1-2 ชม.)

```markdown
## 🔍 Audit Report

| โหลด | ค่า User | ค่าแนะนำ | ผล |
|------|----------|----------|:--:|
| น้ำอุ่น | 16A | 20A | ❌ |
```

---

## 📁 Files to Modify

| Phase | ไฟล์ | งาน |
|:-----:|------|-----|
| 0 | `service.py` | Structured Output + Confidence |
| 0 | `service.py` | `should_ask_back()` |
| 2 | `service.py` | `validate_user_specs()` |
| 3 | `markdown_formatter.py` | Audit section |

---

## ✅ Checklist

- [ ] 0.1 Structured Output + Confidence schema
- [ ] 0.2 Few-shot examples (messy)
- [ ] 0.3 `should_ask_back()` logic
- [ ] 0.4 Test
- [ ] 2: Compare logic
- [ ] 3: Formatter Audit

---

*Updated: 2025-12-24 22:48*
