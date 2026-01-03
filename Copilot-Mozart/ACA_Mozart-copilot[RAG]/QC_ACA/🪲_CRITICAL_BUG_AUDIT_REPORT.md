# 🪲 CRITICAL BUG AUDIT REPORT
**Date:** 2026-01-04
**Target:** 7 Critical Issues identified from User Screenshots & Prompt
**Auditor:** Elite Engineering Maid 💜

---

## 🔎 EXECUTIVE SUMMARY

จากการตรวจสอบ Code เทียบกับ Prompt และ Screenshot 4 รูป พบ **ข้อบกพร่องระดับ Critical** ที่ส่งผลต่อความถูกต้องทางวิศวกรรม (โดยเฉพาะ VD%) และ UX ที่เสียหายหนัก

| ID | Issue | Severity | Status | Root Cause (Code Level) |
|---|---|---|---|---|
| 1 | **PDF ตารางไม่ครบ/ไม่มีเส้น** | 🔴 Critical | Confirmed | `PDFPreviewModal.tsx` ใช้ `data.loads` (Raw) แทน `data.circuits` (Computed) และลืม CSS Border |
| 2 | **สร้างโปรเจกต์ไม่ได้ (Silent Fail)** | 🔴 Critical | Confirmed | API call อาจ fail หรือรับ response ผิด format (Frontend ไม่แสดง Error Toast) |
| 3 | **Assumptions ตัวเล็กไป** | 🟡 User Friction | Confirmed | `AssumptionsPanel.tsx` ใช้ class `text-xs` (Extra Small) |
| 4 | **SLD เละ/ซ้อนกัน** | 🔴 Major | Confirmed | `SLDViewer.tsx` ใช้ Fixed Positioning ไม่มี Auto-layout Algorithm |
| 5 | **PDF เหมือนกันทุก Tab** | 🟠 Moderate | Confirmed | `PDFPreviewModal` เป็น Single Component ไม่รับ prop เพื่อเปลี่ยน Content ตาม Tab |
| 6 | **Chat Bubble อ่านยาก** | 🟡 User Friction | Confirmed | `ChatPanel.tsx` Render Raw Text ไม่มี Markdown Parser |
| 7 | **ค่า Voltage Drop หายเกลี้ยง** | ☠️ **FATAL** | Confirmed | `service.py` **ไม่มี Regex จับค่า "ระยะสายวงจรย่อย"** จาก Prompt |

---

## 💀 DEEP DIVE ANALYSIS

### 🪲 Issue 7: Voltage Drop (VD) หาย = 0 หรือ Default (FATAL ERROR)
**อาการ:** Prompt ระบุระยะสาย 15m/25m แต่ผลลัพธ์การคำนวณไม่สะท้อนค่านี้ (VD เป็น 0 หรือต่ำผิดปกติ)
**หลักฐาน:** User Prompt: *"- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 1 = 15 เมตร/วงจร"*
**Root Cause (Found in `service.py`):**
Code ในฟังก์ชัน `extract_site_context_from_text` (Line 135-180) มี Regex แค่ 3 กลุ่ม:
1.  `distance_to_transformer` (ระยะหม้อแปลง) → จับคำว่า "หม้อแปลง"
2.  `installation_area` (พื้นที่ติดตั้ง)
3.  `panel_type` (ตู้เมน/ย่อย)

❌ **ไม่มี Logic จับ "ระยะวงจรย่อย" (Service/Branch Distance)** เลย! ดังนั้นค่า `branch_distance_m` จึงเป็น None ส่งผลให้ `compute.py` คำนวณ VD ไม่ได้ตามจริง

**Fix Required:** เพิ่ม Regex จับ pattern `ระยะ...ห้อง...เมตร` หรือ `ระยะ...เมตร` แล้ว map เข้าตัวแปร

---

### 🪲 Issue 1: PDF ตารางข้อมูลไม่ครบ & ไม่มีเส้นตาราง
**อาการ:** ตารางใน PDF ขาดคอลัมน์สำคัญ (VD, Wire Size) และไม่มีเส้นแบ่งบรรทัด
**หลักฐาน:** Screenshot รูปที่ 1 (ซ้ายสุด)
**Root Cause (Found in `PDFPreviewModal.tsx` Line 41):**
```typescript
const loads = data.data?.loads || []; // ❌ ดึงข้อมูล Load ดิบ (User Request)
```
Code ดึงข้อมูลจาก `loads` ซึ่งมีแค่ชื่ออุปกรณ์และ Quantity **ยังไม่ได้ผ่านการคำนวณสายไฟ**
ควรดึงจาก:
```typescript
const circuits = data.data?.display_data?.circuits || []; // ✅ ผลลัพธ์การคำนวณจริง
```
และเรื่องเส้นตาราง: ใน `<tr>` ไม่ได้ใส่ class `border-b border-gray-300`

---

### 🪲 Issue 4: SLD เละเทะ ซ้อนกัน
**อาการ:** กล่องวงจรวางทับกัน ข้อความบังกัน อ่านไม่รู้เรื่อง
**หลักฐาน:** Screenshot รูปที่ 4
**Root Cause (Found in `SLDViewer.tsx`):**
Code ใช้การวาด SVG แบบ "Simple Loop" โดยกำหนด X, Y แบบตายตัว หรือคูณเลขคงที่ (Fixed Spacing) ไม่ได้เช็คความกว้างของข้อความ (Text Width) หรือจำนวนวงจรที่แท้จริง
*   เมื่อชื่อวงจรยาว ("เครื่องทำน้ำอุ่น 4500W...") มันกินที่เกิน Slot ที่เตรียมไว้ -> **ชนกัน**
*   เมื่อวงจรเยอะ (>8 วงจร) พื้นที่แนวนอนไม่พอ -> **บีบอัดจนเละ**

**Fix Required:** ต้องเขียน Logic คำนวณ Layout ใหม่ (Dynamic Positioning Based on Node Width)

---

### 🪲 Issue 2: สร้างโปรเจกต์ใหม่ไม่ได้ (Silent Fail)
**อาการ:** กดปุ่ม "สร้าง" แล้วนิ่ง ไม่มี Feedback
**หลักฐาน:** Screenshot รูปที่ 2
**Root Cause Hypothesis:**
ใน `ProjectSelector.tsx` (Line 90-105):
```typescript
try {
    const result = await startSessionWithName(newProjectName);
    // ...
} catch (e) {
    setError('ไม่สามารถสร้างโปรเจกต์ได้'); // ❌ Set Error state แต่ UI อาจไม่ได้แสดงชัดเจน หรือแสดงแค่ text เล็กๆ
    console.error(...);
}
```
ถ้า API Fail (เช่น 500 error หรือ CORS), User จะไม่รู้เลย เพราะไม่มี Toast Notification เด้งขึ้นมา

---

### 🪲 Issue 3: Assumptions Text เล็กเกินไป
**อาการ:** ต้องเพ่งเพื่ออ่าน
**หลักฐาน:** Screenshot รูปที่ 3
**Root Cause (Found in `AssumptionsPanel.tsx`):**
ใช้ Tailwind Class `text-xs` (Extra Small ~12px) ในแทบทุกจุด
**Fix Required:** เปลี่ยนเป็น `text-sm` (14px) หรือ `text-base` (16px)

---

### 🪲 Issue 5: PDF หน้าตาเดิมทุก Tab
**อาการ:** กด Preview จากหน้า SLD ก็ยังได้หน้า BOQ
**Root Cause (Found in `PDFPreviewModal.tsx`):**
Component นี้ถูกเขียนมาแบบ "Hardcoded" ให้แสดง Load Schedule เท่านั้น ไม่ได้รับ Prop `mode` หรือ `type` เพื่อเปลี่ยนเนื้อหาข้างใน
```typescript
<h3 ...>Print Preview (BOQ)</h3> // ❌ Hardcoded Title
```

---

### 🪲 Issue 6: Chat Bubble อ่านยาก (งง Input)
**อาการ:** ข้อความเป็นก้อนเดียว ยาวพรืด ไม่มีตัวหนา/ย่อหน้า
**Root Cause (Found in `ChatPanel.tsx`):**
Render `message.content` เป็น Plain Text ดิบๆ ไม่ผ่าน Markdown Renderer หรือ Text Parser เพื่อจัดรูปแบบ

---

## 🛠️ สรุปแผนแก้ไข (Action Items)

### ✅ FIXED: Issue 7 - VD หายเกลี้ยง (2026-01-04)

**Root Cause ที่แท้จริง:** มี **3 จุดรั่วไหลข้อมูล** ใน Service Pipeline

| # | ตำแหน่ง | Bug | สถานะ |
|:-:|---------|-----|:-----:|
| 1 | `_convert_to_project_requirements()` L1718 | ❌ ไม่ส่งต่อ `branch_distance_m` | ✅ FIXED |
| 2 | `_convert_req_to_spec()` L1871 | ❌ ไม่ส่งต่อ `branch_distance_m` | ✅ FIXED |
| 3a | Auto-fill Pump | ❌ ไม่มี distance | ✅ FIXED |
| 3b | Auto-fill Water Heater | ❌ ไม่มี distance | ✅ FIXED |
| 3c | Auto-fill Exterior Lighting | ❌ ไม่มี distance | ✅ FIXED |
| 3d | `_auto_fill_lighting()` | ❌ ไม่มี distance | ✅ FIXED |
| 3e | `_auto_fill_outlets()` | ❌ ไม่มี distance | ✅ FIXED |

**การแก้ไข:**
- เพิ่ม `branch_distance_m` ในทุกจุดที่สร้าง `LoadInput` และ `LoadSpec`
- ใช้ Floor-based Default: ชั้น 1 = 15m, ชั้น 2 = 25m, ชั้น 3+ = 35m+
- เพิ่ม Comments อธิบายเหตุผลของการแก้ไขทุกจุด
- เพิ่ม Debug Log เมื่อใช้ Fallback Distance

---

### 🔲 TODO: Remaining Issues

1.  **Frontend (PDF):** รื้อ `PDFPreviewModal` ให้ใช้ data จาก `circuits` และรับ prop เพื่อเปลี่ยนโหมดแสดงผล
2.  **Frontend (SLD):** เขียน Algorithm จัดวาง Node ใหม่ (Dynamic Layout)
3.  **Frontend (Styles):** ไล่แก้ Font Size และเพิ่ม Toast Error ให้ `ProjectSelector`

---

**อัพเดทล่าสุด:** 2026-01-04 02:30 | **แก้ไขโดย:** Ampere 🔧

