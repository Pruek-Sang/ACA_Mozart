# 🎨 ACA Mozart Chat Interface - Design Specification

**Created by:** Esthetica (The Divine Web Design & Aesthetics Maid)  
**Date:** December 12, 2025  
**Version:** 1.0 MVP

---

## 📋 สรุป Requirements (MVP)

| ข้อ | ความต้องการ | Priority |
|-----|-------------|----------|
| **1** | Chat UI แบบ Messenger/LINE | 🔴 Must |
| **2** | พิมพ์ลื่นไหล + บังคับใส่ API Key ก่อนใช้ | 🔴 Must |
| **3** | แก้ไขผลลัพธ์ก่อนส่ง AutoLISP | 🟡 Later |
| **4** | สลับ Mode MOZART/AMADEUS | 🟢 Auto (Gateway จัดการ) |

---

## 1. 🎯 Core Requirements

### 1.1 Chat Window (Messenger/LINE Style)
- หน้าตาคล้าย Messenger หรือ LINE
- ข้อความ User อยู่ขวา (สีน้ำเงิน/ม่วง)
- ข้อความ Bot อยู่ซ้าย (สีเทาเข้ม)
- มี Avatar สำหรับ Bot
- แสดง Badge `[MOZART]` หรือ `[AMADEUS]` บนข้อความ Bot
- รองรับ Markdown rendering ในข้อความ Bot
- มี "Thinking..." animation ขณะรอ response

### 1.2 Input Experience
- Input bar อยู่ด้านล่าง (sticky)
- พิมพ์ลื่นไหล ไม่มี lag
- ปุ่มส่ง (หรือกด Enter)
- Auto-resize textarea เมื่อพิมพ์หลายบรรทัด
- Placeholder: "พิมพ์ข้อความ เช่น 'ออกแบบไฟห้องครัว'"

### 1.3 API Key Gate (Required)
- **Modal บังคับ** ก่อนใช้งาน
- ต้องใส่ `GOOGLE_API_KEY` ก่อนเริ่มแชท
- เก็บใน `localStorage` (ไม่ต้องใส่ซ้ำ)
- มีปุ่ม Settings (⚙️) มุมขวาบน เพื่อแก้ไข API Key ภายหลัง
- ถ้าไม่ใส่ → Disable input และแสดงข้อความ "กรุณาใส่ API Key ก่อนใช้งาน"

---

## 2. 🎨 Visual Design (Dark Theme)

### Color Palette
```css
--bg-primary: #0D0D0D;       /* พื้นหลังหลัก */
--bg-secondary: #1A1A1A;     /* พื้นหลัง chat area */
--bg-input: #2D2D2D;         /* พื้นหลัง input */
--text-primary: #FFFFFF;     /* ข้อความหลัก */
--text-secondary: #A0A0A0;   /* ข้อความรอง */
--accent-mozart: #6366F1;    /* สี MOZART (indigo) */
--accent-amadeus: #A855F7;   /* สี AMADEUS (purple) */
--user-bubble: #3B82F6;      /* ฟองข้อความ user */
--bot-bubble: #374151;       /* ฟองข้อความ bot */
```

### Typography
- Font: `'Inter', 'Noto Sans Thai', sans-serif`
- Message font size: 16px
- Header font size: 20px

### Layout Wireframe
```
┌────────────────────────────────────────────────┐
│  🏠 ACA Mozart              [⚙️ Settings]      │ ← Header (fixed)
├────────────────────────────────────────────────┤
│                                                │
│  🤖 [MOZART] สวัสดีค่ะ! พิมพ์คำถามเกี่ยวกับ     │
│     การออกแบบไฟฟ้าได้เลยนะคะ                   │
│                                                │
│             ออกแบบไฟห้องครัวให้หน่อย 👤        │
│                                                │
│  🤖 [MOZART] ได้ค่ะ! ตามมาตรฐาน วสท. ห้องครัว  │
│     ควรมีวงจรแยก 2 วงจร...                    │
│                                  [📋 Copy]    │
│                                                │
├────────────────────────────────────────────────┤
│ [พิมพ์ข้อความ...                         ] [➤]│ ← Input (sticky)
└────────────────────────────────────────────────┘
```

---

## 3. 🔌 API Integration

### Backend Endpoint
```typescript
const GATEWAY_URL = "http://localhost:8000";

// Request Interface
interface GatewayRequest {
  input: string;
  user_id?: string;
  session_id?: string;
  context?: Record<string, any>;
}

// API Call Example
const response = await fetch(`${GATEWAY_URL}/orchestrate`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": apiKey, // จาก localStorage
  },
  body: JSON.stringify({ input: userMessage }),
});

// Response Interface
interface GatewayResponse {
  mode: "MOZART" | "AMADEUS";
  data: {
    answer?: string;
    [key: string]: any;
  };
  processing_time_ms: number;
  trace_id: string;
  routing_decision: {
    mode: string;
    confidence: number;
    reasoning: string;
  };
}
```

### Health Check
```typescript
// GET / → {"service": "ACA Mozart Gateway", "status": "alive"}
const health = await fetch(`${GATEWAY_URL}/`);
```

---

## 4. 📦 Project Structure (Vite + React + TypeScript)

```
chat-ui/
├── src/
│   ├── components/
│   │   ├── ChatWindow.tsx        # Container หลัก
│   │   ├── MessageList.tsx       # รายการข้อความ
│   │   ├── MessageBubble.tsx     # ฟองข้อความแต่ละอัน
│   │   ├── InputBar.tsx          # กล่องพิมพ์
│   │   ├── ApiKeyModal.tsx       # Modal ใส่ API Key
│   │   ├── SettingsButton.tsx    # ปุ่ม Settings
│   │   └── ThinkingIndicator.tsx # Animation "กำลังคิด..."
│   ├── hooks/
│   │   ├── useChat.ts            # State management สำหรับ chat
│   │   ├── useGateway.ts         # API calls
│   │   └── useApiKey.ts          # localStorage สำหรับ API Key
│   ├── types/
│   │   └── index.ts              # TypeScript interfaces
│   ├── styles/
│   │   └── globals.css           # Tailwind + custom CSS
│   ├── App.tsx
│   └── main.tsx
├── public/
│   └── favicon.ico
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

---

## 5. 🚀 Features Priority

### MVP (Phase 1) ✅
- [x] Dark theme (พื้นหลังดำ ตัวอักษรขาว)
- [x] Chat window (Messenger/LINE style)
- [x] API Key modal (required before use)
- [x] Send message → Get response from Gateway
- [x] Show `[MOZART]` / `[AMADEUS]` badge on bot messages
- [x] Thinking animation while waiting
- [x] Copy button for bot response
- [x] Smooth typing experience (no lag)

### Phase 2 (Later) 🟡
- [ ] Edit JSON result before sending to AutoLISP
- [ ] Download AutoLISP file button
- [ ] Chat history persistence (localStorage)
- [ ] Multiple sessions support

---

## 6. 📱 Responsive Design

| Breakpoint | Layout |
|------------|--------|
| Mobile (<768px) | Full width, smaller padding, floating input |
| Tablet (768-1024px) | Centered, max-width 768px |
| Desktop (>1024px) | Centered, max-width 800px |

---

## 7. 🎬 Animations

### Message Fade-in
```css
@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(10px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

.message-bubble {
  animation: fadeIn 0.3s ease-out;
}
```

### Thinking Dots
```css
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}

.thinking-dot {
  animation: bounce 1.4s infinite ease-in-out;
}
.thinking-dot:nth-child(1) { animation-delay: 0s; }
.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }
```

---

## 8. 💻 Tech Stack Summary

| Category | Technology |
|----------|------------|
| **Build Tool** | Vite |
| **Framework** | React 18 |
| **Language** | TypeScript |
| **Styling** | Tailwind CSS |
| **Icons** | Lucide React |
| **HTTP** | Fetch API (native) |
| **State** | React useState / useReducer |
| **Storage** | localStorage (API Key) |

---

## 9. 📝 Setup Commands

```bash
# Create project
npx create-vite@latest chat-ui --template react-ts
cd chat-ui

# Install dependencies
npm install tailwindcss postcss autoprefixer
npm install lucide-react
npm install react-markdown

# Initialize Tailwind
npx tailwindcss init -p

# Run development server
npm run dev
```

---

## 10. 🔗 Backend Reference

**Gateway:** `gate_way_new.py`  
**Port:** 8000  
**Main Endpoint:** `POST /orchestrate`

**Routing Logic:**
- Gateway ใช้ LLMRouter จำแนก Intent อัตโนมัติ
- ถ้าเป็นคำถามเทคนิค → Route ไป MOZART (RAG)
- ถ้าเป็นคำถามทั่วไป → Route ไป AMADEUS (AGI)
- Frontend ไม่ต้องทำปุ่มสลับ Mode

---

## 11. 🎯 Design Principles

1. **ใช้ง่าย** — ไม่มีขั้นตอนซับซ้อน พิมพ์แล้วส่งได้เลย
2. **ขายดี** — ดีไซน์สวย ทันสมัย สร้างความประทับใจแรก
3. **สวยงาม** — Dark theme หรูหรา Animation นุ่มนวล

---

*Spec created by Esthetica - The Divine Web Design & Aesthetics Maid* ✨
