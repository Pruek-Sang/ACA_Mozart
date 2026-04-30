# 🎹 ACA Mozart
> **AI-Powered Electrical Design System** | NLP → Load Schedule → AutoLISP

---

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| 💬 **NLP Chat Interface** | พิมพ์ภาษาไทย → ออกแบบไฟฟ้า | ✅ Live |
| ⚡ **MCP Core** | คำนวณ Load, Breaker, Wire sizing | ✅ Live |
| 📊 **Load Schedule** | สร้างตาราง BOQ มาตรฐาน วสท. | ✅ Live |
| 🏠 **Floor Plan** | วาง Layout อุปกรณ์ไฟฟ้า | ✅ Live |
| 📄 **PDF Export** | ส่งออกรายงานพร้อมใช้ | ✅ Live |

---

## 🚀 Premium Features (Coming Soon)

| Feature | Description |
|---------|-------------|
| 🎭 **Mozart Mascot** | Loading animation พร้อม progress indicator |
| 📜 **White Label** | อัปโหลดโลโก้+ลายเซ็นบริษัท |
| ✅ **Compliance Audit** | ตรวจเกณฑ์ วสท./NEC อัตโนมัติ |
| 🔲 **QR Verification** | สแกนตรวจสอบเอกสารต้นฉบับ |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Frontend (React + Tailwind)            │
├─────────────────────────────────────────┤
│  Gateway (FastAPI)                      │
├─────────────────────────────────────────┤
│  Mozart RAG         │   MCP Core v2     │
│  (Gemini + FAISS)   │   (Electrical)    │
└─────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
ACA_Mozart/
├── Copilot-Mozart/          # RAG + Frontend
│   └── ACA_Mozart-copilot[RAG]/
│       ├── app/             # RAG Service
│       ├── frontend_UI_UX/  # React Chat UI
│       └── rag_knowledge/   # Knowledge Base
├── mcp_core_v2/             # Electrical Calculations
│   └── core/                # Circuit Logic
└── README.md
```

---

## 🛠️ Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI
- **AI/ML**: Google Gemini, FAISS
- **Standards**: วสท. 2001-56, NEC 2023, IEC 60364

---

## 📜 License

© 2024 ACA Team. All rights reserved.
