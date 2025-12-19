# 🔄 Changes Log: Load Balancer & Circuit Display Fix

> **เอกสารนี้อธิบาย:** การแก้ไข Bug และเพิ่ม Feature ในวันที่ 19 ธ.ค. 2025
> 
> **Commits:** `a911e92`, `0244398`, `a85ac79`

---

## 📋 สรุปปัญหาที่พบ

| ปัญหา | ไฟล์ที่เกี่ยวข้อง | สถานะ |
|-------|-----------------|-------|
| MCP Core URL เปลี่ยนหลัง redeploy | `.github/workflows/docker-build.yml` | ✅ แก้แล้ว |
| เต้ารับแสดงซ้ำทุก circuit | `service.py` | ✅ แก้แล้ว |
| แยก circuit มากเกินไป | `circuit_grouper.py` | ✅ แก้แล้ว |

---

## 1️⃣ circuit_grouper.py - Balanced Load Distribution

### 📍 ไฟล์: `mcp_core_v2/core/circuit_grouper.py`

### ❌ ก่อนแก้ (Greedy Algorithm):

```python
def _create_receptacle_circuit(self, loads: List[ElectricalLoad], floor: str):
    """ใช้ Greedy - ใส่ทีละ load จนเกิน 10 → แยกวงจรใหม่ทันที"""
    MAX_PER_CIRCUIT = 10
    chunks = []
    current_chunk = []
    current_count = 0
    
    for load in loads:
        qty = load.quantity
        if current_count + qty > MAX_PER_CIRCUIT and current_chunk:
            # ❌ แยกทันทีที่เกิน! ไม่สนว่าจะสิ้นเปลืองวงจร
            chunks.append(current_chunk)
            current_chunk = [load]
            current_count = qty
        else:
            current_chunk.append(load)
            current_count += qty
```

**ปัญหา:**
- ห้องนั่งเล่น (qty=6) + ห้องครัว (qty=6) = 12 > 10 → **แยกทันที!**
- ผลลัพธ์: 3 วงจร (6 + 9 + 4) แทนที่จะเป็น 2 วงจร (10 + 9)

### ✅ หลังแก้ (Balanced Best-Fit Algorithm):

```python
def _create_receptacle_circuit(self, loads: List[ElectricalLoad], floor: str):
    """ใช้ Balanced - คำนวณก่อน → แจกเฉลี่ย"""
    MAX_PER_CIRCUIT = 10
    
    # Step 1: นับรวมก่อน
    total_outlets = sum(load.quantity for load in loads)  # 19
    
    # Step 2: คำนวณจำนวน circuit ที่ต้องการ
    num_circuits = math.ceil(total_outlets / MAX_PER_CIRCUIT)  # 2
    
    # Step 3: สร้าง bucket และแจกเฉลี่ย
    circuits_data = [[] for _ in range(num_circuits)]
    circuit_counts = [0] * num_circuits
    
    # เรียง load ใหญ่ก่อน (Best-fit decreasing)
    sorted_loads = sorted(loads, key=lambda l: -l.quantity)
    
    for load in sorted_loads:
        # หา circuit ที่มีที่ว่างมากสุด
        best_idx = find_circuit_with_most_space()
        circuits_data[best_idx].append(load)
        circuit_counts[best_idx] += load.quantity
```

### 📊 ผลลัพธ์ที่คาดหวัง:

| ชั้น | จุด | ก่อน (Greedy) | หลัง (Balanced) |
|-----|-----|---------------|-----------------|
| 1 | 19 | 3 วงจร (6+9+4) | **2 วงจร (10+9)** |
| 2 | 10 | 2 วงจร (6+4) | **1 วงจร (10)** |
| **รวม** | 29 | **5 วงจร** | **3 วงจร** |

---

## 2️⃣ service.py - Fix Duplicate Display

### 📍 ไฟล์: `Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/service.py`

### ❌ ก่อนแก้ (แสดงซ้ำ):

```python
# Add sub-details for outlet circuits
if "เต้ารับ" in name:
    floor = extract_floor(name)
    if floor in outlets_by_floor:
        # ❌ แสดง outlets_by_floor ซ้ำทุก circuit!
        for room, qty in outlets_by_floor[floor]:
            display(f"└─ {room}: คู่×{qty}")
```

**ปัญหา:**
- ทุก circuit ที่มี "เต้ารับ ชั้น 1" จะแสดงรายละเอียด **ซ้ำกันหมด**
- วงจร 1, 2, 3 แสดง 19 จุดเหมือนกัน!

### ✅ หลังแก้ (Track ว่าแสดงแล้ว):

```python
outlets_displayed_floors = set()  # ← เพิ่ม tracking

if "เต้ารับ" in name:
    floor = extract_floor(name)
    circuit_num = extract_circuit_num(name)  # (1), (2), ...
    
    # ✅ แสดงรายละเอียดเฉพาะ circuit แรกของแต่ละชั้น
    if floor not in outlets_displayed_floors:
        for room, qty in outlets_by_floor[floor]:
            display(f"└─ {room}: คู่×{qty}")
        outlets_displayed_floors.add(floor)  # ← บันทึกว่าแสดงแล้ว
    else:
        # วงจรที่ 2+ แสดงแค่ summary
        display(f"📊 วงจรที่ {circuit_num} ({amps}A)")
```

### 📊 ผลลัพธ์ที่คาดหวัง:

**ก่อน:**
```
│ 7 │ 🔌 เต้ารับ ชั้น 1 (1) │ 11.4 │
│   │  └─ ห้องนั่งเล่น: คู่×6    │
│   │  └─ ห้องครัว: คู่×6       │
│   │  └─ ... (7 ห้อง)          │
│   │  📊 รวม: 19จุด (14.9A)    │
│ 8 │ 🔌 เต้ารับ ชั้น 1 (2) │ 10.2 │
│   │  └─ ห้องนั่งเล่น: คู่×6    │  ← ❌ ซ้ำ!
│   │  └─ ห้องครัว: คู่×6       │  ← ❌ ซ้ำ!
│   │  └─ ... (ทั้ง 7 ห้องซ้ำ)   │
│ 9 │ 🔌 เต้ารับ ชั้น 1 (3) │  4.1 │
│   │  └─ ... (ซ้ำอีก!)          │  ← ❌ ซ้ำ!
```

**หลัง:**
```
│ 7 │ 🔌 เต้ารับ ชั้น 1 (1) │ 11.4 │
│   │  └─ ห้องนั่งเล่น: คู่×6    │
│   │  └─ ห้องครัว: คู่×6       │
│   │  └─ ... (7 ห้อง)          │
│   │  📊 รวม: 19จุด (11.4A)    │
│ 8 │ 🔌 เต้ารับ ชั้น 1 (2) │  7.8 │
│   │  📊 วงจรที่ 2 (7.8A)      │  ← ✅ สรุปอย่างเดียว
```

---

## 3️⃣ docker-build.yml - Auto-Update MCP URL

### 📍 ไฟล์: `.github/workflows/docker-build.yml`

### ❌ ก่อนแก้ (Manual):

```yaml
# หลัง deploy ไม่มีการ update URL
- name: Deploy MCP Core
  run: gcloud run deploy mcp-core ...

- name: Deploy Mozart RAG
  run: gcloud run deploy mozart-rag ...
# ❌ ถ้า MCP URL เปลี่ยน → RAG ยังชี้ไป URL เก่า → พัง!
```

### ✅ หลังแก้ (Auto-Update):

```yaml
- name: Deploy MCP Core
  run: gcloud run deploy mcp-core ...

# ✅ เพิ่ม step auto-update
- name: 🔗 Update Service URLs & Health Check
  run: |
    # 1. ดึง URL ของ MCP Core ที่ deploy ใหม่
    MCP_URL=$(gcloud run services describe mcp-core \
      --format='value(status.url)')
    
    # 2. Health check
    curl -sf "$MCP_URL/health" && echo "✅ MCP Core: HEALTHY"
    
    # 3. Update RAG อัตโนมัติ
    gcloud run services update mozart-rag \
      --update-env-vars="MCP_CORE_URL=$MCP_URL"
    
    echo "✅ RAG updated → $MCP_URL"

# ✅ Fallback ถ้า fail
- name: 🚨 Fallback Diagnostics
  if: failure()
  run: |
    gcloud run services list
    echo "# Manual fix:"
    echo "gcloud run services update mozart-rag --update-env-vars='MCP_CORE_URL=<URL>'"
```

### 📊 ผลลัพธ์ที่คาดหวัง:

| Scenario | ก่อน | หลัง |
|----------|-----|------|
| Deploy ครั้งแรก | ✅ ตั้ง URL มือ | ✅ ตั้ง URL มือ (ครั้งเดียว) |
| Deploy ครั้งที่ 2+ | ❌ ต้องแก้มือ | ✅ **อัตโนมัติ** |
| URL เปลี่ยน | ❌ พัง! | ✅ **อัพเดทให้เอง** |

---

## 📐 3-Phase Flag (Future Ready)

### เพิ่มใน `circuit_grouper.py`:

```python
class CircuitGrouper:
    # === 3-Phase Load Balancing (Future Feature) ===
    # Set to True to enable balancing loads across L1/L2/L3 phases
    # Currently False for standard 1-phase residential designs
    ENABLE_3PHASE_BALANCE = False
```

**ใช้ตอนไหน:**
- ปัจจุบัน: `False` (1-phase บ้านพักอาศัย)
- อนาคต: เปลี่ยนเป็น `True` สำหรับ 3-phase commercial

---

## 📦 MCB Count Summary

| สถานะ | Dedicated | Lighting | Receptacle | Spare | **รวม** |
|-------|-----------|----------|------------|-------|--------|
| ก่อนแก้ | 4 | 2 | 5 | 2 | **13** |
| **หลังแก้** | 4 | 2 | **3** | 2 | **11** |

---

*เอกสารนี้สร้างเมื่อ: 2025-12-19*
*สำหรับอ้างอิงการแก้ไขในอนาคต*
