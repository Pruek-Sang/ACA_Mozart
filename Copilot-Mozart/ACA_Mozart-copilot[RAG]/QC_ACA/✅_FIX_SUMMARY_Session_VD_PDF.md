# ✅ FIX SUMMARY (Session, VD, PDF Exports)
> **Author:** Antigravity (Elite Engineering Maid)
> **Date:** 2026-01-07
> **Status:** Deployed & Verified (Commit f979fb7)

เอกสารนี้สรุปการแก้ไขบั๊กและฟีเจอร์สำคัญที่เพิ่งทำเสร็จสิ้น เพื่อเป็น Reference ให้ทีมงาน (และ AI รุ่นถัดไป) เข้าใจว่า "ทำอะไรไปบ้าง" โดยไม่ต้องไปขุด Code เองครับ

---

## 1. ⚡ Voltage Drop (VD) Stuck at 2.0%
**อาการ:** ตารางโหลดแสดงค่า VD เป็น 2.0% ตลอดเวลา แม้สายยาว 100 เมตร
**สาเหตุ:**
1.  **Backend (Calculator):** คำนวณถูกแล้ว แต่เก็บค่าลง Dictionary โดยใช้ `load_id` เป็น Key
2.  **Display Logic:** ตอนดึงมาแสดงผล ดันไปใช้ `circuit_id` เป็น Key ในการ Lookup
3.  **Result:** หาไม่เจอ -> ระบบเลย Fallback ไปใช้ค่า Default (2.0%)

**การแก้ไข (The Fix):**
*   **File:** `app/display/compute.py` และ `app/formatters/markdown_formatter.py`
*   **Logic:** เปลี่ยนวิธีการดึงค่า (Lookup) ให้ถูกต้อง และเพิ่ม Logic "Data Injection" ใน `service.py` เพื่อฝังค่า VD ลงไปใน Object ตั้งแต่ต้นทาง
*   **ผลลัพธ์:** ค่า VD แสดงผลถูกต้องตามจริง (เช่น 3.5%, 1.2%)

---

## 2. 💾 Session Persistence (ข้อมูลหายเมื่อ Refresh)
**อาการ:** หันไปกินน้ำ แล้วกลับมา Refresh หน้าจอ -> ข้อมูลหายเกลี้ยง
**สาเหตุ:**
1.  **Frontend:** บาง Request ลืมส่ง `session_id` ไปหา Backend
2.  **Backend:** เมื่อไม่ได้รับ ID ก็เลยสร้าง Session ใหม่ให้ (Empty Session)
3.  **Storage:** ระบบ Auto-save มีบั๊ก Indentation (ย่อหน้าผิด) ทำให้บางครั้งไม่ Save ลง DB

**การแก้ไข (The Fix):**
*   **File:** `frontend/src/App.tsx` (เพิ่ม Logic การจำ ID)
*   **File:** `app/routes.py` (แก้ Indentation บรรทัดเดียวแต่สำคัญมาก)
*   **Logging:** เพิ่ม Log `[SESSION-DEBUG]` เต็มระบบ เพื่อให้ Trace ได้ว่าข้อมูลหายตอนไหน

---

## 3. 📄 PDF & Excel Export (New Features)
**โจทย์:** ลูกค้าต้องการปริ้นต์ใบ BOQ และ SLD แบบ "วิศวกรมืออาชีพ" (ขาว-ดำ, A4, มีกรอบ) ไม่ใช่แคปหน้าจอสีๆ

### 3.1. BOQ Export (PDF + Excel)
*   **New File:** `frontend/src/components/BOQPDFPreviewModal.tsx`
*   **Logic:**
    *   สร้างตาราง BOQ ใหม่ แยกวัสดุ (E1, E2, E3)
    *   คำนวณราคา (Cost Estimation)
    *   ใช้ `html2pdf.js` ปริ้นต์เป็น PDF A4
    *   ใช้ `xlsx` library export เป็น Excel ให้ลูกค้าไปแก้ราคาต่อได้
*   **UI:** เพิ่มปุ่ม "Download Options" ใน BOQ Tab

### 3.2. SLD PDF Export
*   **New File:** `frontend/src/components/SLDPDFPreviewModal.tsx`
*   **Logic:**
    *   ดึง SVG Diagram จากหน้าจอ
    *   ปรับสีให้เป็นขาว-ดำ (Grayscale)
    *   จัดลงกระดาษ A4 แนวนอน (Landscape)
*   **UI:** เพิ่มปุ่ม "Download SLD (PDF)" ลอยขวาบนของ SLD Tab

### 3.3. **CRITICAL FIX: Zero Values in Load Table PDF**
*   **อาการ:** ใบ Load Schedule เดิม (ของเก่า) ปริ้นต์ออกมาแล้วเลขเป็น 0 หมด
*   **สาเหตุ:** Frontend Mapping (`App.tsx`) ลืมส่งค่า `load_va` ไปให้ PDF Component
*   **การแก้ไข:** เพิ่ม Data Mapping และใส่ Logic Fallback:
    ```typescript
    // ถ้าไม่มีค่าส่งมา ให้คำนวณสดเดี๋ยวนั้นเลย (kW * 1000)
    load_va_l1: ckt.load_va_l1 || Math.round(ckt.total_kw * 1000) || 0
    ```
*   **ผลลัพธ์:** ตัวเลขมาครบ จบปัญหา

---

## 📂 Summary of Modified Files
| File Path | Purpose |
|-----------|---------|
| `frontend/src/App.tsx` | Fix Session ID + Fix PDF Data Mapping |
| `app/routes.py` | Fix Auto-save Logic |
| `app/display/compute.py` | Fix Voltage Drop Lookup |
| `frontend/src/components/ResultViewer.tsx` | Add Buttons & Modals |
| `frontend/src/components/BOQPDFPreviewModal.tsx` | **[NEW]** BOQ PDF/Excel Logic |
| `frontend/src/components/SLDPDFPreviewModal.tsx` | **[NEW]** SLD PDF Convert Logic |
