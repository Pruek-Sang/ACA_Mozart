# 🐞 Debug Summary: ทำไม Input ครบ แต่ได้แค่ Spare Circuits?
> **Date:** 2025-12-22
> **Author:** AI Team (Valida & Nexia)
> **Status:** ✅ SOLVED

---

## 🎯 1. อาการของปัญหา (The Symptom)

User ส่ง input เข้ามาครบถ้วน:
> *"บ้าน 2 ชั้น... หม้อแปลง 50 เมตร ติดตั้งในบ้าน เป็นตู้เมน..."*

**สิ่งที่ควรจะเป็น:**
- ระบบรับ `site_context` (ระยะทาง / พื้นที่ / ประเภทตู้)
- ระบบคำนวณ Derating Factors, kA Ratings, N-G Link
- ออกแบบตู้ไฟที่ถูกต้อง (ไม่ใช่ Spare)

**สิ่งที่เกิดขึ้นจริง (Production):**
- ได้รับตู้ไฟที่มีแต่ลูกย่อย **Spare** ❌
- ไม่มี `site_context` ถูกนำไปใช้ในขั้นตอนคำนวณ
- Logs แจ้งว่า `Missing site_context` หรือบางทีเงียบไปเฉยๆ

---

## 🌀 2. ทำไมเราถึง "วนลูป" อยู่ตั้งนาน? (The Loop)

เราวนเวียนแก้ปัญหาอยู่นาน เพราะเรา **"มองข้ามจุดตาย"**:

1.  **🔍 เรามัวแต่ดู Code Logic:**
    - เช็ค `service.py`: *Extraction ถูกไหม?* → ถูก ✅
    - เช็ค `mcp_adapter.py`: *ส่ง context ไปไหม?* → ส่ง ✅
    - เช็ค `pipeline.py`: *เรียก injectors ไหม?* → เรียก ✅ (ใน Code)
    
2.  **📉 เรามัวแต่โทษ Gateway/Router:**
    - นึกว่า Gateway ส่งผิด path (`/ask` vs `/design`)
    - นึกว่า Prompt ผิด เลยแก้ Prompt ไปหลายรอบ
    
3.  **🙈 จุดบอด (Blind Spot):**
    - เราเช็ค Code ใน **GitHub Repo** (มีไฟล์ครบ)
    - แต่เราลืมเช็ค **Docker Build Process** (สิ่งที่ Deploy จริง)

---

## 💀 3. สาเหตุที่แท้จริง (The Root Cause)

**"Code มีอยู่จริง แต่มันไม่ได้ไปอยู่บน Server!"**

เราได้สร้าง Features ใหม่ที่สำคัญมาก:
- `mcp_core_v2/context/` (เก็บ Logic การคำนวณ Derating / Safety)
- `mcp_core_v2/catalog/` (เก็บไฟล์ราคา `prices.csv`)

**แต่ใน `mcp_core_v2/Docker/Dockerfile`:**
```dockerfile
# BEFORE (สิ่งที่ Production ใช้อยู่)
COPY models/ ./models/
COPY core/ ./core/
# ...
# ❌ ไม่มี context/
# ❌ ไม่มี catalog/
```

**ผลลัพธ์:**
- เมื่อ Cloud Run พยายามรัน `import context` → **ImportError** หรือ ข้าม Logic นี้ไปเงียบๆ (Fail Silently)
- เมื่อไม่มี Logic → ระบบเลยคำนวณไม่ได้ → **fallback เป็น Default/Spare**

---

## 🛠️ 4. เราแก้อะไรไปบ้าง? (The Fixes)

### ✅ 1. แก้ Root Cause (Critical)
เพิ่มบรรทัดที่หายไปใน `Dockerfile` ของ MCP Core:
```dockerfile
# mcp_core_v2/Docker/Dockerfile

# 🆕 For Site Context Logic in production
COPY context/ ./context/ 

# 🆕 For BOQ Pricing
COPY catalog/ ./catalog/
```

### ✅ 2. แก้ปัญหา Deployment Caching (Optimization)
- ย้าย **Gateway** จาก Docker Hub (ที่ชอบ Cache ผิดๆ) ไปใช้ **Artifact Registry** ของ Google
- ทำให้มั่นใจว่า Code ใหม่ถูก Deploy จริงๆ ไม่ใช่ Image เก่าค้าง

### ✅ 3. ลดขนาด Gateway (Efficiency)
- สร้าง `requirements_gateway.txt` ใหม่ (ตัด ML Library หนักๆ 4GB ออก)
- Gateway เหลือขนาดแค่ **~50MB** (เบาและเร็วขึ้นมาก)

---

## 🧠 5. บทเรียนสำหรับเพื่อน AI (AI-to-AI Note)

เพื่อนเอ๋ย... ถ้าเจ้าเจออาการแบบนี้:
1. **Local Works** (Code เจ้าถูก Logic เจ้าเป๊ะ)
2. **Production Fails** (แต่พอ Deploy แล้วพัง)
3. **Logs are Weird** (Logs หายไป หรือ Error แบบหาไฟล์ไม่เจอ)

**🛑 จงหยุดดู Code... แล้วไปดู `Dockerfile` เดี๋ยวนี้!**

> "การสร้าง Folder ใหม่ใน Project ไม่ได้แปลว่ามันจะไปอยู่ใน Docker เองโดยอัตโนมัติ เจ้าต้อง `COPY` มันเข้าไปด้วย!"

---

### 📝 Checklist สำหรับครั้งหน้า:
- [ ] ฉันสร้าง Folder/Module ใหม่หรือเปล่า?
- [ ] ถ้าใช่... ฉันเพิ่ม `COPY` ใน Dockerfile หรือยัง?
- [ ] ฉันเช็ค Cloud Run Logs หา `ImportError` หรือยัง?

**จบการรายงาน.** 🫡
