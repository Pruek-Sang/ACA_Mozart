# 🎨 Mozart Chat Frontend - Functionality Spec

> **Version:** 1.0.0  
> **Last Updated:** December 2024  
> **Project:** ACA Mozart - Text-to-Design Electrical System

---

## 🎯 Overview

Mozart Chat เป็น **Split-View Chat Interface** สำหรับระบบออกแบบไฟฟ้าอัตโนมัติ ประกอบด้วย:

- **Left Pane (40%):** Chat Interface สำหรับสนทนากับ AI
- **Right Pane (60%):** JSON Editor สำหรับดู/แก้ไขข้อมูลก่อนส่งคำนวณ

---

## ✨ Features & Capabilities

### 1. Chat Interface (Left Pane)

| Feature | Description | Status |
|---------|-------------|--------|
| **Send Message** | พิมพ์คำถามและกด Enter หรือปุ่ม Send | ✅ |
| **Receive Response** | แสดงคำตอบจาก MOZART (RAG) หรือ AMADEUS (AGI) | ✅ |
| **Mode Badge** | แสดง Badge สีบอกว่าคำตอบมาจากใคร (MOZART=Indigo, AMADEUS=Purple) | ✅ |
| **Copy Message** | ปุ่ม Copy บน Message Bubble | ✅ |
| **Quick Chips** | ปุ่มลัดคำถามยอดนิยม (ออกแบบไฟครัว, คำนวณ Voltage Drop, ฯลฯ) | ✅ |
| **Typing Indicator** | แสดง Animation ขณะ AI กำลังตอบ | ✅ |
| **Clear Chat** | ปุ่มล้างประวัติสนทนา | ✅ |
| **Auto-Scroll** | เลื่อนลงอัตโนมัติเมื่อมีข้อความใหม่ | ✅ |

### 2. JSON Editor (Right Pane)

| Feature | Description | Status |
|---------|-------------|--------|
| **Display JSON** | แสดง JSON ที่ RAG ส่งกลับมาแบบ Syntax Highlight | ✅ |
| **Edit JSON** | แก้ไขค่าใน JSON ได้โดยตรง | ✅ |
| **Validation** | ตรวจสอบว่า JSON ถูกต้องหรือไม่ (แสดงขอบแดงถ้าผิด) | ✅ |
| **Send to MCP** | ปุ่มส่ง JSON ที่แก้ไขแล้วไปยัง MCP Core | 🔜 (Pending) |

### 3. Authentication

| Feature | Description | Status |
|---------|-------------|--------|
| **API Key Modal** | แสดง Popup ให้กรอก API Key ครั้งแรก | ✅ |
| **Connection Test** | ทดสอบเชื่อมต่อ Gateway ก่อนเข้าใช้งาน | ✅ |
| **Persist Key** | เก็บ API Key ใน localStorage | ✅ |
| **Settings Button** | ปุ่มเปิด Modal เพื่อเปลี่ยน API Key | ✅ |

---

## 📤 Expected Outputs

### 1. Chat Response (From Gateway)

**Input:** User พิมพ์ "ออกแบบไฟห้องครัว"

**Expected Output:**
```json
{
  "mode": "MOZART",
  "data": {
    "answer": "สำหรับห้องครัวขนาด 3x4 เมตร แนะนำ...",
    "project_name": "Kitchen Electrical Design",
    "rooms": [
      {
        "name": "ครัว",
        "width": 3,
        "length": 4,
        "loads": [...]
      }
    ]
  },
  "routing_decision": {
    "mode": "MOZART",
    "confidence": 0.95
  }
}
```

### 2. JSON Editor Display

เมื่อ Response มี structured data (rooms, loads, etc.) → แสดงใน JSON Editor ด้านขวาโดยอัตโนมัติ

### 3. Send to MCP (Expected)

**Input:** User กดปุ่ม "Send to MCP"

**Expected Output:**
```json
{
  "status": "success",
  "autolisp_file": "kitchen_design.lsp",
  "calculations": {
    "total_load": 3500,
    "recommended_breaker": "20A",
    "wire_size": "2.5 sqmm"
  }
}
```

---

## 🎨 Design System

### Colors (Dark Theme)

| Token | Hex | Usage |
|-------|-----|-------|
| `bgPrimary` | `#0D0D0D` | Main Background |
| `bgSecondary` | `#1A1A1A` | Header, Footer |
| `bgInput` | `#2D2D2D` | Input Fields |
| `accentMozart` | `#6366F1` | MOZART Mode (Indigo) |
| `accentAmadeus` | `#A855F7` | AMADEUS Mode (Purple) |
| `userBubble` | `#3B82F6` | User Message (Blue) |
| `botBubble` | `#374151` | Bot Message (Gray) |

### Typography

- **Font Family:** Inter, Noto Sans Thai
- **Message Text:** 14px
- **Header Title:** 18px, Semi-bold

---

## 📁 File Structure

```
mozart-chat/
├── src/
│   ├── config/api.config.ts    # Gateway URL, Theme
│   ├── types/gateway.ts        # TypeScript Interfaces
│   ├── services/gateway.ts     # API Calls
│   ├── hooks/useChat.ts        # Chat State Management
│   └── components/
│       ├── App.tsx             # Main Layout (Split View)
│       ├── Header.tsx          # Header with Clear/Settings
│       ├── ChatPane.tsx        # Chat Messages Container
│       ├── MessageBubble.tsx   # Individual Message
│       ├── InputBar.tsx        # Text Input + Send Button
│       ├── QuickChips.tsx      # Quick Action Buttons
│       ├── ApiKeyModal.tsx     # Authentication Modal
│       └── JSONEditorPane.tsx  # JSON Editor (Right Pane)
```

---

## 🔗 Integration Points

| Integration | Endpoint | Port |
|-------------|----------|------|
| **Gateway** | `/orchestrate` | 8000 |
| **Health Check** | `/` | 8000 |
| **MCP Core** | `/calculate` (via Gateway) | 5001 |

---

## 🚀 How to Run

### Development
```bash
cd frontend_UI_UX/mozart-chat
npm install
npm run dev
# Open http://localhost:5173/
```

### Production Build
```bash
npm run build
# Output: dist/ folder
```

---

## ⚠️ Known Limitations

1. **MCP Integration:** ปุ่ม "Send to MCP" ยังไม่เชื่อมต่อจริง (Mock only)
2. **Markdown Rendering:** ใช้ Simple Formatter (ไม่ใช่ Full Markdown Parser)
3. **Mobile:** ยังไม่ Responsive สำหรับหน้าจอเล็ก

---

## 🔜 Future Enhancements

- [ ] Full MCP Core Integration
- [ ] Markdown with `react-markdown`
- [ ] Collapsible JSON Editor
- [ ] Export to PDF/Excel
- [ ] Mobile Responsive Design
