# 📜 API Contract: Mozart Admin Layer (Backend ↔ Admin)

> **เอกสารนี้คือ "เมนูลับ"** สำหรับ Admin/System Use เท่านั้น ห้ามเผยแพร่ให้ User
> **Updated:** 2025-12-28 | **Owner:** Nexia (Backend AI)
> **Status:** Protected by `X-Admin-Key` Middleware

---

## 🔐 Authentication (Security First)

**ทุก Request** ที่จะเรียก API ในเอกสารนี้ ต้องแนบ Header:

```http
X-Admin-Key: <YOUR_SECRET_KEY>
```

- **Default (Dev):** `REDACTED_ADMIN_KEY`
- **Prod:** ตั้งค่าผ่าน Environment Variable `ADMIN_API_KEY`
- ถ้าไม่แนบ หรือ Key ผิด → จะได้รับ `401 Unauthorized`

---

## 📌 ENDPOINT 1: `/api/v1/admin/ingest` (Upload Docs)

### 🔹 Request (POST)

```json
{
  "file_path": "/absolute/path/to/document.pdf"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | `string` | ✅ | Absolute path ของไฟล์ใน Server ที่จะ Ingest |

### 🔹 Response (200 OK)

```json
{
  "status": "Ingestion queued",
  "path": "/absolute/path/to/document.pdf"
}
```
*Note:* การทำงานเป็น Background Task (Fire-and-Forget)

---

## 📌 ENDPOINT 2: `/api/v1/admin/delete` (Remove Docs)

### 🔹 Request (POST)

```json
{
  "source_path": "manual_v1.pdf"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_path` | `string` | ✅ | ชื่อไฟล์หรือ Path pattern ที่ต้องการลบจาก Vector DB |

### 🔹 Response (200 OK)

```json
{
  "status": "Deleted",
  "source_path": "manual_v1.pdf"
}
```

---

## 📌 ENDPOINT 3: `/api/v1/admin/retrieve_raw` (Debug Search)

### 🔹 Request (POST)

```json
{
  "query": "สายไฟ THW",
  "top_k": 5,
  "filters": {"folder": "standard"}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | ✅ | คำค้นหา |
| `top_k` | `int` | ❌ | จำนวนผลลัพธ์ (Default: 5) |
| `filters` | `dict` | ❌ | Filter metadata |

### 🔹 Response (200 OK)

Returns raw list of `SourceRef` objects from Vector DB.

---

## ⚠️ ERROR RESPONSES

| HTTP Code | Meaning | Reason |
|-----------|---------|--------|
| `401` | Unauthorized | Key ผิด หรือ ไม่ได้ส่ง Header |
| `400` | Bad Request | File Not Found (Ingest) |
| `500` | Server Error | Vector DB Down |

---
