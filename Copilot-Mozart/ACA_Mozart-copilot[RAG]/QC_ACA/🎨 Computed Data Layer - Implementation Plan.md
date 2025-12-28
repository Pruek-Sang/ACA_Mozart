# 🎨 Computed Data Layer - Implementation Plan

> **เอกสารนี้สำหรับ:** Developer ที่ต้องการเข้าใจและ implement ระบบ Computed Data Layer
> **สถานะ:** 📋 Planning Phase
> **สร้างเมื่อ:** 2025-12-29

---

## 📖 สารบัญ

1. [แนวคิดและปัญหาที่ต้องการแก้](#-แนวคิดและปัญหาที่ต้องการแก้)
2. [เป้าหมายของ Computed Data Layer](#-เป้าหมายของ-computed-data-layer)
3. [Architecture Overview](#-architecture-overview)
4. [Implementation Details](#-implementation-details)
5. [Data Flow Diagram](#-data-flow-diagram)
6. [ไฟล์ที่ต้องสร้าง/แก้ไข](#-ไฟล์ที่ต้องสร้างแก้ไข)
7. [ตัวอย่างโค้ด](#-ตัวอย่างโค้ด)

---

## 🧠 แนวคิดและปัญหาที่ต้องการแก้

### ปัญหาปัจจุบัน

ในระบบ Mozart ปัจจุบัน การแสดงผลมีปัญหาดังนี้:

```
┌─────────────────────────────────────────────────────────────────┐
│  ปัญหา: Markdown Formatter คำนวณค่าภายในตัวเอง                  │
│                                                                  │
│  result (จาก MCP) ──→ markdown_formatter.py ──→ Markdown        │
│                              │                                   │
│                        คำนวณที่นี่:                              │
│                        - total_watts = sum(...)                 │
│                        - demand_current = X / 230               │
│                        - floor_totals = {...}                   │
│                              │                                   │
│                              ↓                                   │
│                    ค่าหายไป! ไม่ได้เก็บ!                        │
│                                                                  │
│  ถ้าเราต้องการสร้าง SLD หรือ BOQ:                               │
│  - SLD ต้องคำนวณใหม่ → ค่าอาจไม่ตรง!                           │
│  - BOQ ต้องคำนวณใหม่ → ค่าอาจไม่ตรง!                           │
└─────────────────────────────────────────────────────────────────┘
```

**ปัญหาหลัก:**
1. **ไม่มี Single Source of Truth** - แต่ละ output คำนวณเอง
2. **ค่าอาจไม่ตรงกัน** - Markdown, SLD, BOQ อาจแสดงค่าต่างกัน
3. **ยากต่อการเพิ่ม output ใหม่** - ต้อง copy logic การคำนวณ
4. **ยากต่อการ test** - ต้อง test การคำนวณซ้ำในหลายที่

### ทำไมต้องแก้?

เมื่อ User แก้ข้อมูล (เช่น เพิ่มแอร์):
- **ความคาดหวัง:** ทุก output (Markdown, SLD, BOQ) ต้องอัพเดทพร้อมกันและแสดงค่าเดียวกัน
- **ความเป็นจริง (ปัจจุบัน):** ถ้าแต่ละ output คำนวณเอง → ค่าอาจคลาดเคลื่อน

---

## 🎯 เป้าหมายของ Computed Data Layer

### เราต้องการอะไร?

1. **Single Source of Truth** - คำนวณครั้งเดียว ทุก output ใช้ค่าเดียวกัน
2. **Consistency** - Markdown, SLD, BOQ แสดงค่าตรงกัน 100%
3. **Flexibility** - เพิ่ม output ใหม่ได้ง่าย (PDF, DXF, Excel)
4. **Maintainability** - แก้การคำนวณที่เดียว → ทุก output อัพเดท
5. **Testability** - Test การคำนวณแยกจากการ render

### หลักการ: "Compute Once, Render Many"

```
                    📦 DisplayData (Computed Once)
                              │
           ┌──────────────────┼──────────────────┐
           ↓                  ↓                  ↓
      📄 Markdown        🖼️ SLD             📊 BOQ
      (Render)           (Render)           (Render)
      ไม่คำนวณ           ไม่คำนวณ           ไม่คำนวณ
```

---

## 🏗️ Architecture Overview

### Design Decision: อ่านจาก `mcp_response`

เราเลือกให้ `compute.py` อ่านข้อมูลจาก `mcp_response` (ฝั่ง RAG) แทนที่จะแก้ `result_builder` (ฝั่ง MCP Core)

**เหตุผล:**
1. `mcp_response` มีข้อมูลจาก `result_builder` ครบถ้วนอยู่แล้ว
2. ไม่ต้องแก้ไข MCP Core (ลด scope และลดความเสี่ยง)
3. แยก concerns ชัดเจน:
   - **MCP Core** = คำนวณค่าทางไฟฟ้า (breaker, wire, VD)
   - **RAG** = คำนวณค่าสำหรับแสดงผล (totals, summaries)

### แผนภาพ Separation of Concerns

```
┌─────────────────────────────────────────────────────────────────┐
│  MCP Core (ไม่แก้ไข)                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ pipeline.py → result_builder.py → DesignResult             │ │
│  │                                                            │ │
│  │ คำนวณค่าทางไฟฟ้า:                                          │ │
│  │ - breaker_selections (เบรกเกอร์)                           │ │
│  │ - wire_sizing (สายไฟ)                                      │ │
│  │ - voltage_drop (VD%)                                       │ │
│  │ - grouped_circuits (วงจรรวมกลุ่ม)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
                     mcp_response (ข้อมูลครบ)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  RAG Service (แก้ไขที่นี่)                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ compute.py                                                 │ │
│  │                                                            │ │
│  │ คำนวณค่าสำหรับแสดงผล:                                      │ │
│  │ - total_watts (รวมวัตต์)                                   │ │
│  │ - demand_current (กระแส)                                   │ │
│  │ - floor_totals (รวมตามชั้น)                                │ │
│  │ - main_breaker_size (ขนาดเมนเบรกเกอร์)                     │ │
│  │ - breaker_summary (สรุปเบรกเกอร์)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓                                   │
│                     📦 DisplayData                              │
│                             ↓                                   │
│  ┌─────────────────┬─────────────────┬──────────────────────┐  │
│  │ markdown_render │ sld_renderer    │ boq_renderer         │  │
│  │ (อ่านอย่างเดียว) │ (อ่านอย่างเดียว) │ (อนาคต)              │  │
│  └────────┬────────┴────────┬────────┴──────────────────────┘  │
│           ↓                 ↓                                   │
│      📄 Markdown       🖼️ SLD JSON                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Details

### โครงสร้างโฟลเดอร์ใหม่

```
app/
├── display/                      ← 🆕 โฟลเดอร์ใหม่
│   ├── __init__.py
│   ├── compute.py               ← คำนวณ DisplayData
│   ├── markdown_renderer.py     ← Render Markdown จาก DisplayData
│   ├── sld_renderer.py          ← Render SLD JSON จาก DisplayData
│   └── boq_renderer.py          ← (อนาคต) Render BOQ
│
├── formatters/
│   └── markdown_formatter.py    ← จะ deprecate หลังจาก migrate
│
└── service.py                   ← เรียก compute → render
```

### ขั้นตอนการ implement

| Phase | งาน | รายละเอียด |
|-------|-----|-----------|
| 1 | สร้าง `compute.py` | ย้ายการคำนวณจาก markdown_formatter.py มาที่นี่ |
| 2 | สร้าง `markdown_renderer.py` | Render Markdown จาก DisplayData (ไม่คำนวณ) |
| 3 | สร้าง `sld_renderer.py` | Render SLD JSON จาก DisplayData |
| 4 | แก้ `service.py` | เรียก compute → render ทั้งสอง |
| 5 | Update `AnswerMetadata` | เพิ่ม field `sld_data` |
| 6 | (Optional) Deprecate `markdown_formatter.py` | เมื่อ migrate เสร็จ |

---

## 🔗 Data Flow Diagram

### Before (ปัจจุบัน)

```
MCP Core                                  RAG Service
┌───────────────────┐                    ┌───────────────────────────┐
│ result_builder    │ ──mcp_response──→  │ markdown_formatter        │
│ (คำนวณไฟฟ้า)      │                    │ (คำนวณ totals + render)   │
└───────────────────┘                    └────────────┬──────────────┘
                                                      ↓
                                                 📄 Markdown
                                                 
❌ ถ้าต้องการ SLD → ต้องคำนวณใหม่ → ค่าอาจไม่ตรง!
```

### After (หลัง implement)

```
MCP Core                                  RAG Service
┌───────────────────┐                    ┌───────────────────────────┐
│ result_builder    │ ──mcp_response──→  │ compute.py                │
│ (คำนวณไฟฟ้า)      │                    │ (คำนวณ totals ครั้งเดียว) │
└───────────────────┘                    └────────────┬──────────────┘
                                                      ↓
                                              📦 DisplayData
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    ↓                 ↓                 ↓
                             markdown_render     sld_renderer     boq_renderer
                             (อ่านอย่างเดียว)    (อ่านอย่างเดียว)  (อนาคต)
                                    ↓                 ↓
                              📄 Markdown        🖼️ SLD JSON
                              
✅ ทุก output ใช้ค่าเดียวกัน!
```

---

## 📁 ไฟล์ที่ต้องสร้าง/แก้ไข

### ไฟล์ใหม่

| ไฟล์ | หน้าที่ | Complexity |
|------|--------|------------|
| `app/display/__init__.py` | Package init | 🟢 ง่าย |
| `app/display/compute.py` | คำนวณ DisplayData | 🟡 กลาง |
| `app/display/markdown_renderer.py` | Render Markdown | 🟡 กลาง |
| `app/display/sld_renderer.py` | Render SLD JSON | 🟡 กลาง |

### ไฟล์ที่ต้องแก้ไข

| ไฟล์ | การเปลี่ยนแปลง |
|------|---------------|
| `app/service.py` | เรียก compute → render แทน markdown_formatter |
| `app/models/contracts.py` | เพิ่ม `sld_data: Optional[Dict]` ใน `AnswerMetadata` |

### ไฟล์ที่จะ deprecate (ภายหลัง)

| ไฟล์ | หมายเหตุ |
|------|---------|
| `app/formatters/markdown_formatter.py` | เก็บไว้ชั่วคราวเพื่อ backward compatibility |

---

## 💻 ตัวอย่างโค้ด

### `app/display/compute.py`

```python
"""
Compute Display Data - Single Source of Truth for Display Calculations

หลักการ: Compute Once, Render Many
- คำนวณค่าทั้งหมดที่นี่ครั้งเดียว
- ทุก renderer อ่านจาก DisplayData
- ห้าม renderer คำนวณเอง!
"""
from typing import Dict, Any, List
import math

def round_up(value: float, decimals: int = 0) -> float:
    """Round up to specified decimal places."""
    if decimals == 0:
        return math.ceil(value)
    multiplier = 10 ** decimals
    return math.ceil(value * multiplier) / multiplier


def compute_display_data(mcp_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    คำนวณค่าทั้งหมดสำหรับแสดงผล
    
    Args:
        mcp_result: ผลลัพธ์จาก MCP Core (mcp_response.to_dict())
        
    Returns:
        DisplayData dict ที่มีค่าคำนวณครบถ้วน
    """
    if not mcp_result:
        return {}
    
    summary = mcp_result.get('summary') or {}
    grouped_circuits = mcp_result.get('grouped_circuits') or []
    wire_sizing = mcp_result.get('wire_sizing') or {}
    
    # === คำนวณ Total Power ===
    total_watts = sum(c.get('total_watts', 0) for c in grouped_circuits)
    if not total_watts:
        # Fallback to summary
        total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
    total_watts = round_up(total_watts)
    
    # === คำนวณ Demand Current ===
    demand_current = summary.get('demand_current')
    if demand_current is None:
        demand_current = total_watts / 230 if total_watts else 0
    demand_current = round_up(demand_current, 1)
    
    # === คำนวณ Design Current (×1.25) ===
    design_current = round_up(demand_current * 1.25, 1)
    
    # === คำนวณ Main Breaker Size ===
    if demand_current <= 15:
        main_breaker = "16A/1P"
        meter_size = "5(15)A"
        main_wire = "4 mm²"
    elif demand_current <= 45:
        main_breaker = "50A/2P"
        meter_size = "15(45)A"
        main_wire = "10 mm²"
    elif demand_current <= 100:
        main_breaker = "100A/2P"
        meter_size = "30(100)A"
        main_wire = "25 mm²"
    else:
        main_breaker = "125A/2P"
        meter_size = "CT Meter"
        main_wire = "50 mm²"
    
    # === คำนวณ Floor Totals ===
    floor_totals = {}
    for circuit in grouped_circuits:
        floor = str(circuit.get('floor', '1'))
        if floor not in floor_totals:
            floor_totals[floor] = {'watts': 0, 'circuits': []}
        floor_totals[floor]['watts'] += circuit.get('total_watts', 0)
        floor_totals[floor]['circuits'].append(circuit)
    
    # Round floor totals
    for floor in floor_totals:
        floor_totals[floor]['watts'] = round_up(floor_totals[floor]['watts'])
    
    # === คำนวณ Breaker Summary ===
    breaker_summary = {}
    for circuit in grouped_circuits:
        rating = circuit.get('breaker_rating', 15)
        poles = circuit.get('breaker_poles', 1)
        key = f"{rating}A/{poles}P"
        if key not in breaker_summary:
            breaker_summary[key] = {'count': 0, 'circuits': []}
        breaker_summary[key]['count'] += 1
        breaker_summary[key]['circuits'].append(
            circuit.get('circuit_name', circuit.get('name', 'Unknown'))
        )
    
    return {
        # Basic totals
        'total_watts': total_watts,
        'total_kw': total_watts / 1000,
        'demand_current': demand_current,
        'design_current': design_current,
        
        # Main equipment
        'main_breaker': main_breaker,
        'meter_size': meter_size,
        'main_wire': main_wire,
        
        # Grouped data
        'floor_totals': floor_totals,
        'breaker_summary': breaker_summary,
        'circuits': grouped_circuits,
        'circuit_count': len(grouped_circuits),
        
        # Raw data (for renderers that need it)
        'wire_sizing': wire_sizing,
        'warnings': mcp_result.get('warnings', []),
        'errors': mcp_result.get('errors', []),
        'project_name': mcp_result.get('project_name', 'ไม่ระบุ'),
    }
```

### `app/display/markdown_renderer.py`

```python
"""
Markdown Renderer - Render DisplayData to Markdown

หลักการ: อ่านอย่างเดียว ห้ามคำนวณ!
ทุกค่าต้องมาจาก display_data
"""
from typing import Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo


def render_markdown(display_data: Dict[str, Any]) -> str:
    """
    Render DisplayData to Markdown string.
    
    ⚠️ ห้ามคำนวณค่าใดๆ ในฟังก์ชันนี้!
    ทุกค่าต้องมาจาก display_data
    """
    if not display_data:
        return "❌ ไม่มีข้อมูลสำหรับแสดงผล"
    
    lines = []
    today = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y")
    
    # Header
    lines.append("# ตารางโหลดไฟฟ้า (Load Schedule)")
    lines.append("")
    lines.append(f"**โครงการ:** {display_data['project_name']}")
    lines.append(f"**วันที่:** {today}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Summary - อ่านจาก display_data (ไม่คำนวณ!)
    lines.append("## สรุปภาพรวม")
    lines.append("")
    lines.append("| รายการ | ค่า |")
    lines.append("|--------|-----|")
    lines.append(f"| โหลดรวม | {display_data['total_watts']:,.0f} W ({display_data['total_kw']:.1f} kW) |")
    lines.append(f"| กระแสรวม | {display_data['demand_current']:.1f} A |")
    lines.append(f"| Design Current (×1.25) | {display_data['design_current']:.1f} A |")
    lines.append("")
    
    # Main Equipment - อ่านจาก display_data
    lines.append("## อุปกรณ์หลัก")
    lines.append("")
    lines.append("| อุปกรณ์ | ขนาด |")
    lines.append("|---------|------|")
    lines.append(f"| มิเตอร์ไฟฟ้า | {display_data['meter_size']} |")
    lines.append(f"| สายเมน (THW) | {display_data['main_wire']} |")
    lines.append(f"| Main Breaker | {display_data['main_breaker']} |")
    lines.append("")
    
    # ... (ส่วนที่เหลือของ markdown)
    
    return "\n".join(lines)
```

### `app/display/sld_renderer.py`

```python
"""
SLD Renderer - Render DisplayData to SLD JSON

หลักการ: อ่านอย่างเดียว ห้ามคำนวณ!
ใช้ค่าเดียวกับ Markdown Renderer
"""
from typing import Dict, Any, List


def render_sld(display_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render DisplayData to SLD JSON structure.
    
    ⚠️ ใช้ค่าจาก display_data เท่านั้น
    ค่า total_kw, main_breaker จะตรงกับ Markdown 100%
    """
    if not display_data:
        return None
    
    nodes: List[Dict] = []
    edges: List[Dict] = []
    
    # Main Breaker Node - ใช้ค่าจาก display_data
    nodes.append({
        "id": "MAIN",
        "type": "main_breaker",
        "label": f"Main Breaker {display_data['main_breaker']}",
        "rating": display_data['main_breaker'],
        "x": 0,
        "y": 0
    })
    
    # Circuit Nodes
    y_pos = 100
    for circuit in display_data.get('circuits', []):
        ckt_id = circuit.get('circuit_id') or circuit.get('name', f'C{y_pos}')
        
        nodes.append({
            "id": ckt_id,
            "type": "circuit",
            "label": circuit.get('circuit_name', circuit.get('name', 'Unknown')),
            "rating": f"{circuit.get('breaker_rating', 15)}A",
            "x": 150,
            "y": y_pos
        })
        
        edges.append({
            "from": "MAIN",
            "to": ckt_id,
            "wire_size": f"{circuit.get('wire_size', '2.5')}mm²"
        })
        
        y_pos += 60
    
    return {
        "nodes": nodes,
        "edges": edges,
        "total_load_kw": display_data['total_kw'],  # ค่าเดียวกับ Markdown!
        "main_breaker": display_data['main_breaker'],  # ค่าเดียวกับ Markdown!
        "circuit_count": display_data['circuit_count'],
    }
```

### การเรียกใช้ใน `service.py`

```python
# บรรทัด ~1940 ใน service.py

from app.display.compute import compute_display_data
from app.display.markdown_renderer import render_markdown
from app.display.sld_renderer import render_sld

# 1. รับ result จาก MCP
result = mcp_response.to_dict()

# 2. คำนวณ DisplayData ครั้งเดียว
display_data = compute_display_data(result)

# 3. Render ทุก output จาก DisplayData เดียวกัน
formatted_text = render_markdown(display_data)
sld_data = render_sld(display_data)

# 4. Return ทั้งคู่
return StandardResponse(
    answer=formatted_text,
    metadata=AnswerMetadata(
        readable_report=formatted_text,
        sld_data=sld_data,  # 🆕 เพิ่ม field นี้
    )
)
```

---

## ✅ สรุปประโยชน์

| ข้อดี | คำอธิบาย |
|-------|---------|
| **Consistency** | Markdown และ SLD ใช้ค่าเดียวกัน 100% |
| **Flexibility** | เพิ่ม output ใหม่ง่าย (BOQ, PDF, Excel) |
| **Maintainability** | แก้ compute.py ที่เดียว → ทุก output อัพเดท |
| **Testability** | Test compute แยก, test render แยก |
| **No Regression** | เพิ่มใหม่ทั้งหมด ไม่ลบ code เดิม |

---

*Plan สร้างโดย Nexia | 2025-12-29*
