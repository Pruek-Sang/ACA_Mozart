# 🎭 Loading Mascot Animation
> แผนละเอียดสำหรับ Mozart Loading Indicator

---

## 🎯 Goal

แทนที่ "..." bouncing dots ด้วย **Mozart mascot หมุน + progress bar** ที่ดู premium

---

## 🖼️ Design Spec

### Mascot Requirements

| รายการ | ค่า |
|--------|-----|
| Format | PNG (transparent background) |
| Size | 80-100px |
| Style | Cute chibi / flat design |
| ตอนคิด | ตา `><` หลับ |
| ตอนเสร็จ | ตา `^_^` ยิ้ม |

### Animation Preview

```
┌─────────────────────────────────────────┐
│                                         │
│    [🎹 ><]  ← หมุน 360° ตอนโหลด         │
│                                         │
│    ⚡ กำลังคำนวณ...                     │
│    ████████████░░░░░░░░░  65%          │
│                                         │
│    💡 RAG → ⚡ MCP → 📊 Report          │
│    ───●────────────────                 │
└─────────────────────────────────────────┘
```

---

## 📁 Files to Create/Modify

### [NEW] `LoadingMascot.tsx`

```tsx
interface Props {
  progress: number;  // 0-100
  step: string;      // "กำลังค้นหา..."
}
```

**Features:**
- Mascot image with `animation: spin 2s linear infinite`
- Progress bar with gradient `#6366f1 → #a855f7`
- Step indicator (RAG → MCP → Report)

---

### [MODIFY] `ChatPane.tsx`

**Before:**
```tsx
{isTyping && (
  <div>...</div>  // bouncing dots
)}
```

**After:**
```tsx
{isTyping && (
  <LoadingMascot 
    progress={loadingProgress}
    step="กำลังค้นหาความรู้..."
  />
)}
```

---

### [MODIFY] `index.css`

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 10px #6366f1; }
  50% { box-shadow: 0 0 25px #a855f7; }
}

.mascot-thinking {
  animation: spin 2s linear infinite;
}

.progress-bar {
  background: linear-gradient(90deg, #6366f1, #a855f7);
  animation: pulse-glow 2s ease-in-out infinite;
}
```

---

### [NEW] `assets/mozart-mascot.png`

**📌 รอจาก User Gen**

---

## 📊 Progress Stages

| Stage | % | Icon | Text |
|-------|---|------|------|
| 1. RAG Query | 0-30% | 💡 | กำลังค้นหาความรู้... |
| 2. MCP Calc | 30-70% | ⚡ | กำลังคำนวณ Load... |
| 3. Report | 70-100% | 📊 | กำลังสร้างรายงาน... |

---

## ⏱️ Timeline

| Step | เวลา | ผู้รับผิดชอบ |
|------|------|------------|
| Gen รูป mascot | - | User |
| สร้าง LoadingMascot.tsx | 30 นาที | Secura |
| เพิ่ม CSS animations | 15 นาที | Secura |
| แก้ ChatPane.tsx | 10 นาที | Secura |
| Test + Commit | 5 นาที | Secura |

**รวม: ~1 ชม. (หลังได้รูป)**

---

## ✅ Definition of Done

- [ ] รูป mascot transparent PNG 100x100
- [ ] หมุนตอนโหลด
- [ ] Progress bar gradient + glow
- [ ] แสดงขั้นตอน RAG/MCP/Report
- [ ] ไม่มี "..." อีกต่อไป
