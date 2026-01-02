# 🎹 ACA Mozart: AI-Powered Electrical Design System
> **"Engineering Precision meets AI Creativity"**  
> ระบบออกแบบไฟฟ้าอัตโนมัติมาตรฐาน วสท./NEC ด้วย RAG + MCP Architecture

---

## 📌 Current Status (as of 22 Dec 2024)
**Status:** 🟡 **WAITING FOR USER ACCEPTANCE TEST (UAT)**  
**Latest Deployment:** Commit `71e95da` (Artifact Registry + Dynamic Formatting)

### 🚧 What is happening right now?
เราเพิ่งทำการปรับปรุงระบบครั้งใหญ่เพื่อแก้ปัญหา **"Cloud Run รัน Image ตัวเก่า"** และ **"Output ไม่แสดงผลการคำนวณ Safety Factor"** โดยมีรายละเอียดดังนี้:

1.  **Infrastructure Upgrade:**
    *   ย้ายจาก Docker Hub -> **Google Artifact Registry** (`asia-southeast1`) เพื่อความเร็วและแก้ปัญหา Caching
    *   ใช้ **Immutable Tag Strategy** (`${{ github.sha }}`) แทน `:latest` เพื่อรับประกันว่า Code ใหม่ถูก deploy เสมอ
    *   ตั้งค่า **Cleanup Policy** อัตโนมัติ (เก็บเฉพาะ 5 เวอร์ชั่นล่าสุด) เพื่อประหยัดค่าใช้จ่าย

2.  **Core Logic Enhancement (MCP v2):**
    *   **Fixed Injectors:** แก้ไข `Dockerfile` ให้ COPY `context/` และ `catalog/` เข้าไปครบถ้วน ทำให้ Safety Injectors ทำงานได้จริง
    *   **Inputs:** `DeratingInjector` (อุณหภูมิ), `KaRatingInjector` (ระยะหม้อแปลง), `NgLinkInjector` (ตู้ Sub/Main)

3.  **Output Formatter Enhancement:**
    *   แก้ไข `service.py` ให้ดึง Warning/Notes จาก Injectors มาแสดงผลใน Load Schedule
    *   **ผลลัพธ์:** ตารางจะแสดง 10kA (ถ้าใกล้หม้อแปลง), เตือนห้ามต่อ N-G (ถ้าเป็นตู้ Sub), และเตือน Derating (ถ้าที่ร้อน)

### 🛑 Pending Tasks / Waiting For:
- [ ] **User Verification (Extreme Case):** User จะทำการทดสอบด้วย Prompt:
    > *"ออกแบบระบบไฟฟ้า... ระยะหม้อแปลง 10 เมตร, ติดตั้งตู้ Outdoor, เป็นตู้ย่อย"*
    *   **สิ่งที่ต้องคาดหวัง:** Output ต้องแสดง **10kA**, **Derating Warning**, **No N-G Link Warning**
- [ ] **Load Schedule Verification:** ตรวจสอบว่าหลังจากแยกวงจรแล้ว (Load Balance Algorithm) ค่ากระแสและขนาด Breaker ถูกต้องตามมาตรฐาน 100%

---

## 🏗️ System Architecture

### 🔄 The Flow
```mermaid
graph LR
    User[User Input] --> Gateway[Gateway Service]
    Gateway --> RAG[Mozart RAG (Brain)]
    RAG --1. Extract Context--> RAG
    RAG --2. Send Reqs--> MCP[MCP Core (Calculator)]
    MCP --3. Inject Rules (kA/Derate)--> MCP
    MCP --4. Calculate Load/Wire--> MCP
    MCP --5. Result JSON--> RAG
    RAG --6. Format Table--> User
```

### 🧩 Services
1.  **Gateway (`Dockerfile.gateway`):** ด่านหน้า Routing, ตัด ML libraries ออกให้เบา, ใช้ `requirements_gateway.txt`
2.  **Mozart RAG (`Dockerfile` in `Copilot-Mozart`):** สมองหลัก, Extract Site Context, คุม Conversation
3.  **MCP Core (`mcp_core_v2`):** เครื่องคิดเลขวิศวกรรม, Load Schedule, Circuit Grouping, Safety Injectors
4.  **Frontend (`frontend_UI_UX`):** React Chat UI (กำลังรอการรื้อใหม่เหลือแค่ Login/Security)

---

## 🚀 CI/CD Pipeline (GitHub Actions)

เราใช้ **Strict Immutable Deployment Strategy**:
1.  **Build:** Docker Image ถูกสร้างแยก Layer (Dependencies cached)
2.  **Push:** ส่งไป **Artifact Registry** (`asia-southeast1-docker.pkg.dev/...`) โดยแปะ Tag เป็น **Commit SHA**
3.  **Deploy:** สั่ง Cloud Run ให้ update โดยระบุ **SHAs Tag** เจาะจง (แก้ปัญหา Caching 100%)

---

## 📂 Project Structure for AI Assistants

ถ้าคุณคือ AI ที่มารับช่วงต่อ กรุณาอ่านตรงนี้:

*   **`mcp_core_v2/`**: หัวใจสำคัญ
    *   `context/`: ที่อยู่ของ Injectors (`derating_injector.py`, `ka_rating_injector.py`, ...) **ห้ามลืม COPY folder นี้ใน Dockerfile**
    *   `core/circuit_grouper.py`: Logic การจัดกลุ่มวงจร (Grouping) และ Load Balance
    *   `pipeline.py`: ตัวเรียกใช้งานทั้งหมด
*   **`Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/service.py`**: ตัวสร้าง Output Text ตารางสวยๆ ถ้าจะแก้ข้อความ Output ให้แก้ที่นี่ (`_format_design_result_as_text`)
*   **`.github/workflows/docker-build.yml`**: หัวใจของ CI/CD เช็คตรงนี้ถ้า Deploy ไม่ผ่าน

---

## 📜 Standards Reference
*   **EIT Standard 2001-56:** มาตรฐานการติดตั้งทางไฟฟ้าสำหรับประเทศไทย
*   **NEC 2023:** National Electrical Code (US)
*   **IEC 60364:** International Electrotechnical Commission

---
*Last Updated: 2025-12-22 by Dockera (AI Assistant)*
# Force rebuild - Fri Jan  2 11:16:39 PM +07 2026
