# 📜 API Contract: Mozart Backend ↔ Frontend

> **Updated:** 2025-12-28 | **Owner:** Nexia (Backend AI)

---

## 📖 เอกสารนี้คืออะไร? (อธิบายแบบภาษาคน)

**คิดซะว่า Backend กับ Frontend คือ 2 คนที่คุยกันผ่านโทรศัพท์**
- **Backend** = พ่อครัว (ทำอาหาร = คำนวณไฟฟ้า)
- **Frontend** = พนักงานเสิร์ฟ (รับออเดอร์จากลูกค้า = รับ input จาก User)

**เอกสารนี้คือ "เมนูอาหาร"** ที่บอกว่า:
- ❓ ถ้าอยากได้อาหาร X → ต้องสั่งยังไง (ส่ง Request หน้าตาแบบไหน)
- ✅ พ่อครัวจะส่งอาหารหน้าตายังไงกลับมา (Response หน้าตาแบบไหน)

---

## 📋 สรุปสิ่งที่อยู่ในเอกสารนี้

| หมวด | มีอะไรบ้าง |
|------|-----------|
| **คำสั่งหลัก (Public API)** | Chat, ออกแบบไฟฟ้า, สร้าง Session |
| **ข้อมูลสถานที่** | ระยะหม้อแปลง, พื้นที่ติดตั้ง, ประเภทตู้ไฟ |
| **รหัสอุปกรณ์** | แอร์, เครื่องทำน้ำอุ่น, ปลั๊ก, ไฟ |
| **ข้อผิดพลาด** | Error Code ต่างๆ (400, 422, 429) |
| **การแปลงชื่อ** | Python ใช้ `snake_case`, TypeScript ใช้ `camelCase` |

---

## 🔍 วิเคราะห์: ครบถ้วนแล้วหรือยัง?

### ✅ API ที่รวมไว้แล้ว (สำหรับ User/Frontend):
| API | ทำอะไร |
|-----|--------|
| `/api/v1/ask` | Chat หลัก (พิมพ์คุย + ออกแบบ) |
| `/api/v1/design` | ออกแบบระบบไฟฟ้า (Full Flow) |
| `/api/v1/session/*` | จัดการ Session + Site Context |

### ⚠️ API ที่ยังไม่ได้รวม (Admin API):
| API | ทำอะไร | ทำไมไม่รวม |
|-----|--------|-----------|
| `/api/v1/ingest` | อัปโหลดเอกสารเข้า Knowledge Base | สำหรับ Admin เท่านั้น |
| `/api/v1/delete` | ลบเอกสาร | สำหรับ Admin เท่านั้น |
| `/api/v1/retrieve_raw` | Debug Vector Search | สำหรับ Dev เท่านั้น |

---

## 🔧 แผนการจัดการ Admin API

### ปัญหาปัจจุบัน:
- Admin API ปนอยู่กับ Public API (URL เดียวกัน `/api/v1/`)
- ไม่มี Auth แยก (ใครก็เรียกได้)

### สิ่งที่ควรทำ (TODO):
| ขั้นตอน | อะไร | ไฟล์ที่แก้ | ผลกระทบ |
|---------|-----|----------|---------|
| **1** | เปลี่ยน URL เป็น `/api/v1/admin/*` | `routes.py` (3 บรรทัด) | 🟢 LOW |
| **2** | สร้าง Admin Middleware | `app/middleware/` (ไฟล์ใหม่) | 🟢 LOW |
| **3** | สร้างเอกสาร Admin | `QC_ACA/API_Contract_Admin.md` (ไฟล์ใหม่) | 🟢 LOW |

### ควรทำตอนนี้ไหม?
❌ **ยังไม่ต้อง** — เพราะ:
- Admin API ไม่ได้ถูกใช้โดย User/Frontend (ไม่เสี่ยง)
- ค่อยทำตอนทำ Admin Panel หรือ Security Hardening

---

---

## 🎯 Quick Summary

| Endpoint | Method | ทำอะไร | Priority |
|----------|--------|--------|----------|
| `/api/v1/ask` | POST | Chat + Design Intent Detection | ⭐ HIGH |
| `/api/v1/design` | POST | Full Electrical Design (End-to-End) | ⭐ HIGH |
| `/api/v1/session/start` | POST | Start New Session | ⭐ HIGH |
| `/api/v1/session/{id}/site` | GET/POST | Site Context Questions | MEDIUM |
| `/api/v1/mcp_spec` | POST | Generate MCP Spec (Raw) | LOW |

---

## 📌 ENDPOINT 1: `/api/v1/ask` (Main Chat)

### 🔹 Request (POST)

```json
{
  "query": "ออกแบบบ้าน 2 ชั้น ห้องนอน ห้องน้ำ ห้องครัว",
  "context_hint": [],
  "language": "th",
  "site_context": {
    "distance_to_transformer": "less_than_50m",
    "installation_area": "indoor",
    "panel_type": "main"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | ✅ YES | User's question/command |
| `context_hint` | `string[]` | ❌ | Knowledge folders to search |
| `language` | `"th"` or `"en"` | ❌ | Default: `"th"` |
| `site_context` | `object` | ❌ | Site context (see below) |

### 🔹 Response (200 OK)

```json
{
  "answer": "# รายงานออกแบบระบบไฟฟ้า\n\n## ตารางโหลด...",
  "sources": [
    {"file": "วสท_2564.pdf", "section": "ข้อ 5.1", "score": 0.89}
  ],
  "confidence": "High",
  "grounding_status": "Fully Grounded",
  "metadata": {
    "llm_model": "gemini-1.5-pro",
    "retrieved_docs": ["doc_1", "doc_2"],
    "readable_report": "# Load Schedule\n\n| Room | Device | Power |...",
    "autolisp_code": "(defun c:DRAW_SLD...)"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `string` | **Markdown response** (render ได้เลย) |
| `sources` | `SourceRef[]` | References used |
| `confidence` | `"High"`, `"Medium"`, `"Low"` | Confidence level |
| `metadata.readable_report` | `string` | Design report (Markdown) |
| `metadata.autolisp_code` | `string` (nullable) | AutoLISP code for CAD |

---

## 📌 ENDPOINT 2: `/api/v1/design` (Full Design)

### 🔹 Request (POST)

```json
{
  "project_name": "บ้านคุณสมชาย",
  "building_type": "residential",
  "voltage_system": "TH_1PH_230V",
  "rooms": [
    {"name": "ห้องนอน 1", "type": "bedroom", "floor": 2}
  ],
  "loads": [
    {
      "room_name": "ห้องนอน 1",
      "device": "AC-12000BTU",
      "quantity": 1,
      "floor": 2,
      "branch_distance_m": 15
    }
  ],
  "site_context": {
    "distance_to_transformer": "less_than_50m",
    "installation_area": "indoor",
    "panel_type": "main",
    "conduit_grouping": "1"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_name` | `string` | ✅ | Project name |
| `building_type` | `string` | ✅ | `"residential"`, `"commercial"` |
| `voltage_system` | `string` | ✅ | `"TH_1PH_230V"`, `"TH_3PH_380V"` |
| `rooms` | `RoomInput[]` | ✅ | List of rooms |
| `loads` | `LoadInput[]` | ✅ | List of electrical loads |
| `site_context` | `SiteContext` | ✅ | **Required!** See below |

### 🔹 Response (200 OK)

Full design result with calculations, warnings, and recommendations.

---

## 📌 SITE CONTEXT (Required Fields)

> ⚠️ **CRITICAL:** ถ้าไม่ส่ง site_context จะได้ warning หรือ error

| Field Name | Values | Description |
|------------|--------|-------------|
| `distance_to_transformer` | `"less_than_50m"`, `"50_100m"`, `"more_than_100m"` | ระยะหม้อแปลง (กระทบ kA rating) |
| `installation_area` | `"indoor"`, `"high_temp"`, `"outdoor"`, `"underground"` | พื้นที่ติดตั้ง (กระทบ Derating) |
| `panel_type` | `"main"`, `"sub"` | ตู้เมน/ตู้ย่อย (กระทบ N-G Link) |
| `conduit_grouping` | `"1"`, `"2-3"`, `"4-6"` | จำนวนสายในท่อ (กระทบ Derating) |

---

## 📌 ENDPOINT 3: `/api/v1/session/start`

### 🔹 Request (POST)
No body required.

### 🔹 Response (200 OK)

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-12-28T15:00:00Z",
  "message": "Session created"
}
```

**Use this `session_id` in subsequent calls** (query param or header).

---

## 📌 LOAD INPUT (สำหรับ loads array)

```json
{
  "room_name": "ห้องครัว",
  "device": "INDUCTION-3000W",
  "quantity": 1,
  "power_kw": 3.0,
  "floor": 1,
  "branch_distance_m": 12
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `room_name` | `string` | ✅ | ชื่อห้อง |
| `device` | `string` | ✅ | รหัสอุปกรณ์ (ดู Device Catalog) |
| `quantity` | `int` | ❌ | จำนวน (default: 1) |
| `power_kw` | `float` | ❌ | กำลังไฟ (ถ้ารู้) |
| `floor` | `int` | ❌ | ชั้น (default: 1) |
| `branch_distance_m` | `float` | ❌ | ระยะจากตู้ไฟ (meters) |

---

## 📌 DEVICE CODES (ตัวอย่าง)

| Device Code | Description | Power |
|-------------|-------------|-------|
| `AC-12000BTU` | เครื่องปรับอากาศ 12000 BTU | ~1.4 kW |
| `AC-18000BTU` | เครื่องปรับอากาศ 18000 BTU | ~2.0 kW |
| `HEATER-4500W` | เครื่องทำน้ำอุ่น 4500W | 4.5 kW |
| `INDUCTION-3000W` | เตาแม่เหล็กไฟฟ้า | 3.0 kW |
| `OUTLET-16A` | ปลั๊กไฟ 16A | 0.18 kW/จุด |
| `LIGHT-10W` | หลอดไฟ 10W | 0.01 kW |

---

## ⚠️ ERROR RESPONSES

| HTTP Code | Meaning | Example |
|-----------|---------|---------|
| `400` | Bad Request (Invalid JSON) | `{"error": "Invalid JSON"}` |
| `422` | Missing/Invalid Fields | `{"error": "...", "missing_fields": ["site_context"]}` |
| `429` | Rate Limit Exceeded | `{"error": "Rate limit exceeded", "retry_after": 60}` |
| `503` | Backend Unavailable | `{"error": "MCP Core unavailable"}` |

---

## 🔀 FIELD NAME MAPPING (Snake vs Camel)

> **Backend ใช้ `snake_case`** — Frontend ต้องแปลงเอง

| Backend (Python/JSON) | Frontend (TypeScript) |
|-----------------------|-----------------------|
| `distance_to_transformer` | `distanceToTransformer` |
| `installation_area` | `installationArea` |
| `branch_distance_m` | `branchDistanceM` |
| `room_name` | `roomName` |

**Recommendation:** ใช้ Axios Response Transformer หรือ Manual Mapping.

---

## 📋 Checklist for Frontend Dev

- [ ] ใช้ `POST` ไม่ใช่ `GET` สำหรับ `/ask` และ `/design`
- [ ] ส่ง `Content-Type: application/json`
- [ ] ส่ง `site_context` ครบทุก field (ถ้าจะ `/design`)
- [ ] Handle 422 error และแสดง `missing_fields`
- [ ] Render `answer` เป็น Markdown
- [ ] Map snake_case → camelCase ถ้าต้องการ

---

> **Document Owner:** Nexia (Backend AI)
> **For:** Frontend Team (Serena/Others)
