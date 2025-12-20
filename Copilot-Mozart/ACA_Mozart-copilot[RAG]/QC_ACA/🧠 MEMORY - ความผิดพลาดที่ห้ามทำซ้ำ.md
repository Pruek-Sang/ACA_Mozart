# 🧠 MEMORY - ความผิดพลาดที่ห้ามทำซ้ำเด็ดขาด

> **Secura's Iron Memory** - บทเรียนจากการ deploy 16-17 ธ.ค. 2024

---

## 🔴 ความผิดพลาดที่ 1: Docker BuildX ไม่เห็นไฟล์ที่สร้างระหว่าง Workflow

**อาการ:**
- npm build สร้าง `index-DOKn6az9.js` (ใหม่)
- แต่ Docker image มี `index-CnOwg21W.js` (เก่า)

**สาเหตุ:**
`docker/build-push-action@v5` ใช้ remote builder ไม่ใช่ local filesystem โดยตรง

**วิธีแก้ที่ถูกต้อง:**
```yaml
# ใช้ native docker build แทน BuildX
docker build -f ./Dockerfile.frontend-cloudrun .
```

---

## 🔴 ความผิดพลาดที่ 2: Path `[RAG]` ทำให้ Docker COPY พัง

**อาการ:**
```
ERROR: lstat /Copilot-Mozart: no such file or directory
```

**สาเหตุ:**
Docker ตีความ `[RAG]` เป็น glob pattern (character class)

**วิธีแก้ที่ถูกต้อง:**
```yaml
# Copy ไป simple path ก่อน Docker build
cp -r "./Copilot-Mozart/ACA_Mozart-copilot[RAG]/..." ./frontend-src
```

```dockerfile
# ใน Dockerfile ใช้ simple path
COPY frontend-src/ ./
```

---

## 🔴 ความผิดพลาดที่ 3: ให้คำสั่งเดิมซ้ำๆ โดยไม่วิเคราะห์

**อาการ:**
- Deploy ซ้ำ 2-3 ครั้ง แต่ผลลัพธ์ไม่เปลี่ยน

**บทเรียน:**
```
ถ้าให้คำสั่งเดิม 2 ครั้งแล้วไม่ผ่าน:
→ หยุด
→ วิเคราะห์ใหม่
→ หาปัญหาที่ลึกกว่า
→ ให้คำสั่ง CHECK ก่อน deploy อีกครั้ง
```

---

## 🔴 ความผิดพลาดที่ 4: แก้ไม่ครบ เจอปัญหาใหม่ทันที

**อาการ:**
- แก้ปัญหา #1 ด้วย multi-stage Dockerfile
- ลืมว่า Dockerfile ยังมี path `[RAG]` → เจอปัญหา #2 ทันที

**บทเรียน:**
```
ก่อนแก้ไขใดๆ ต้องตรวจสอบ:
1. ไฟล์นี้มี path/config อะไรบ้าง?
2. การแก้จะกระทบไฟล์อื่นไหม?
3. Test ให้ครบก่อน commit
```

---

## 🔴 ความผิดพลาดที่ 5: ไม่มี Fallback Plan

**บทเรียน:**
```
ทุกครั้งที่ให้ solution ต้องบอก:
- "ถ้านี่ไม่ได้ ให้ check: XYZ"
- "ปัญหาอื่นที่อาจเกิด: ABC"
- "ไฟล์ที่ควรตรวจสอบต่อ: 1, 2, 3"
```

---

## ✅ คำสั่ง CHECK ที่ต้องให้ทุกครั้งหลัง Deploy

```bash
# 1. ดู images ทั้งหมดพร้อม creation time
gcloud artifacts docker images list <registry> --include-tags --format="table(package,tags,createTime)"

# 2. Check ว่า frontend serve files อะไร
curl -s "https://frontend-xxx.run.app/" | grep -o 'assets/index-[^"]*\.\(js\|css\)'

# 3. Check ว่า JS ไม่มี localhost:8000
JS_FILE=$(curl -s "https://frontend-xxx.run.app/" | grep -o 'assets/index-[^"]*\.js')
curl -s "https://frontend-xxx.run.app/$JS_FILE" | grep "localhost:8000" && echo "❌ ยังมี localhost" || echo "✅ ไม่มี localhost"

# 4. Check Cloud Run revisions
gcloud run revisions list --service=frontend --region=asia-southeast1
```

---

## ⚠️ Checklist ก่อน Push ทุกครั้ง

- [ ] ตรวจสอบว่าไฟล์ทั้งหมดที่แก้ถูก stage (`git status`)
- [ ] ตรวจสอบว่า Dockerfile ไม่มี path ที่มี `[` หรือ `]`
- [ ] ตรวจสอบว่า workflow copy files ไป simple path ก่อน Docker build
- [ ] ตรวจสอบว่า .env.production มี Gateway URL ถูกต้อง
- [ ] ตรวจสอบว่า nginx config listen port ถูกต้อง

---

## 🚨 กฎเหล็กของ Secura

1. **ห้ามให้คำสั่งเดิมซ้ำ 2 ครั้ง** โดยไม่วิเคราะห์
2. **ห้ามแก้ไขโดยไม่ตรวจสอบ impact** กับไฟล์อื่น
3. **ต้องมี CHECK command** หลังทุก deploy
4. **ต้องมี fallback plan** ทุกครั้ง
5. **ห้าม regression** สิ่งที่ทำงานดีอยู่แล้ว

---

*Memory ฉบับนี้สร้างเมื่อ: 2025-12-18*
*อัพเดทเมื่อ: 2025-12-19*
*เพื่อป้องกันไม่ให้ทำผิดพลาดซ้ำอีก*

---

## 🔴 ความผิดพลาดที่ 6: Cloud Run URL เปลี่ยนแต่ไม่อัพเดท

**อาการ:**
- `⚠️ MCP Core ไม่พร้อมใช้งาน`
- Services deploy สำเร็จแต่เชื่อมต่อกันไม่ได้

**สาเหตุ:**
- Cloud Run URL เปลี่ยนเมื่อ recreate service
- ENV ของ mozart-rag ยังชี้ไป URL เก่า
- `mcp-core-rc5mtgajza-as.a.run.app` ≠ `mcp-core-203658178245.asia-southeast1.run.app`

**วิธีแก้ที่ถูกต้อง:**
```yaml
# ใน workflow หลัง deploy MCP Core
MCP_URL=$(gcloud run services describe mcp-core --format='value(status.url)')
gcloud run services update mozart-rag --update-env-vars="MCP_CORE_URL=$MCP_URL"
```

**บทเรียน:**
1. Cloud Run URL ไม่ fixed → ต้อง auto-update ทุกครั้ง
2. Service dependencies ต้อง update หลัง deploy
3. ใส่ health check ก่อน+หลัง update

---

## ✅ Service Dependencies ที่ต้องจำ

```
Frontend → Gateway → RAG → MCP Core
  (80)     (8000)   (8080)   (5001)
```

| Service | ต้องรู้ URL ของ | ENV |
|---------|---------------|-----
| Frontend | Gateway | VITE_GATEWAY_URL |
| Gateway | RAG | MOZART_ENDPOINT |
| RAG | MCP Core | MCP_CORE_URL |

---

## 🔴 ความผิดพลาดที่ 7: Path Trigger ไม่ครอบคลุม

**อาการ:**
- แก้ code ใน `mcp_core_v2/` แล้ว push
- GitHub Actions **ไม่ trigger**
- Cloud Run ยังใช้ image เก่า

**สาเหตุ:**
- `paths:` ใน workflow ไม่มี `mcp_core_v2/**`
- Workflow trigger เฉพาะ `Copilot-Mozart/**`

**วิธีแก้ที่ถูกต้อง:**
```yaml
# .github/workflows/docker-build.yml
paths:
  - 'Copilot-Mozart/**'    # RAG, Gateway, Frontend
  - 'mcp_core_v2/**'       # MCP Core ← เพิ่มนี้!
  - 'scripts/**'           # Build scripts
  - '.github/workflows/**' # Workflow changes
```

**บทเรียน:**
1. ตรวจสอบ `paths:` ทุกครั้งที่เพิ่ม directory ใหม่
2. ถ้า CI/CD ไม่ trigger → เช็ค paths ก่อน
3. ใช้ `workflow_dispatch:` เพื่อ manual trigger ได้

---

## 🔴 ความผิดพลาดที่ 8: นับจุดเต้ารับผิดมาตรฐาน

**อาการ:**
- 19 outlets → 3-4 circuits (ควรเป็น 2)
- ผลลัพธ์ MCB มากเกินไป

**สาเหตุ:**
- นับ `quantity` (ช่องเสียบ) แทน outlet box (กล่อง)
- Duplex (คู่) ถูกนับเป็น 2 จุดแทน 1 จุด

**มาตรฐาน วสท. 2564:**
- 1-3 ช่องเสียบในกล่องเดียว = **1 จุด** (180 VA)
- 4+ ช่องเสียบในกล่องเดียว = **2 จุด** (360 VA)

**วิธีแก้ที่ถูกต้อง:**
```python
# นับ outlet boxes ไม่ใช่ receptacles
for load in loads:
    qty = load.quantity if hasattr(load, 'quantity') else 1
    points = 2 if qty >= 4 else 1  # วสท. 2564
```

**บทเรียน:**
1. อ่านมาตรฐานให้ชัดก่อน implement
2. "จุด" ในภาษาไทย = outlet box ไม่ใช่ receptacle
3. ต้อง test กับ case จริง (duplex outlets)

---

## 🔴 ความผิดพลาดที่ 9: Hardcoded Values ที่ขัดแย้งกับมาตรฐาน

**อาการ:**
- ห้องน้ำโหลด 1200W (แทนที่จะเป็น 180 VA)
- แก้ใน `mcp_adapter` แล้วแต่ผลลัพธ์ไม่เปลี่ยน

**สาเหตุ:**
- มีการ **Hardcode** `bathroom_load_w = 1200` ใน `service.py` (Result Builder)
- logic แยกอยู่คนละที่กับ calculation core

**วิธีแก้ที่ถูกต้อง:**
1. ใช้ค่ามาตรฐานเดียวกันทั้งระบบ (Global Constant)
2. อย่า hardcode ตัวเลขใน Display Logic
3. `1 outlet = 180 VA` (วสท. 2564)

**บทเรียน:**
1. ถ้าแก้ที่ต้นทางแล้วไม่หาย → เช็ค Display Logic ว่ามี hardcode ไหม
2. Search codebase หาตัวเลขที่น่าสงสัย (freq grep search)

---

## 🔴 ความผิดพลาดที่ 10: Stateful Singleton ใน Pipeline

**อาการ:**
- `CircuitGrouper` เก็บ state (`self.circuits`)
- ถูก initialize ครั้งเดียวใน `pipeline.py` (`__init__`)
- ถ้า reuse pipeline → state เก่าค้าง!

**สาเหตุ:**
- ใช้ Singleton pattern หรือ Init-once กับ Class ที่มี state สะสม
- `get_circuit_grouper()` คืนค่า global instance (เดิม)

**วิธีแก้ที่ถูกต้อง:**
- เปลี่ยนเป็น **Factory Pattern** ที่สร้าง instance ใหม่ทุก request
- `grouper = get_circuit_grouper(num_floors=...)` ใน `execute()`

**บทเรียน:**
1. Class ที่มี List/Dict accumulation ห้ามเป็น Singleton
2. Pipeline ควรสร้าง helper class ใหม่ทุก request (Fresh Scope)

---

## 🔴 ความผิดพลาดที่ 11: Diversity Factor ไม่ Conditional

**อาการ:**
- ใช้ Diversity Factor 0.4 กับบ้านพักอาศัย (ผิดมาตรฐาน)
- กระแสเต้ารับต่ำเกินจริง (19 จุด เหลือ 7A)

**มาตรฐาน วสท.:**
- **อาคารสูง/ทั่วไป (≥10 ชั้น):** ใช้ Diversity Factor 0.4 สำหรับเต้ารับ
- **บ้านพักอาศัย (<10 ชั้น):** คิด 100% (ไม่ใช้ Diversity Factor)

**วิธีแก้:**
- เพิ่ม `is_high_rise` flag และ `num_floors` check
- `if is_high_rise: apply_diversity else: full_load`

**บทเรียน:**
1. มาตรฐานไฟฟ้ามีข้อยกเว้นตามประเภทอาคาร
2. อย่าใช้ factor เดียวครอบจักรวาล

---

## 🔴 ความผิดพลาดที่ 12: Load Schedule แสดงแต่ Spare Circuits (21 ธ.ค. 2024)

**อาการ:**
- ผู้ใช้ส่ง request ผ่าน Gateway (ข้อความละเอียดมาก)
- Load Schedule ที่ได้มีแค่ Spare circuits เปล่าๆ
- ไม่มี Error message กลับมา

**สาเหตุ (2 จุด):**
1. `_build_design_response()` ใน `service.py` **ไม่ validate** ว่า rooms/loads ว่างหรือไม่
   - เมื่อ LLM extraction ล้มเหลว → rooms/loads ว่าง → ส่งไป MCP โดยตรง
   - MCP สร้าง Panel ที่มีแค่ Spare circuits (ไม่มี load)
   
2. `process_ask()` เมื่อ `_extract_loads_from_text()` return empty:
   - เดิม: Fall back to Q&A flow (ซึ่งอาจคืน Load Schedule เปล่า)
   - **ควรจะ**: Return error message ที่ชัดเจน

**วิธีแก้:**
1. เพิ่ม validation ใน `_build_design_response()` ก่อนบรรทัด 1437:
   ```python
   if not req.rooms or len(req.rooms) == 0:
       return StandardResponse(
           answer="⚠️ ข้อมูลไม่ครบถ้วน...",
           grounding_status="INSUFFICIENT_DATA"
       )
   ```

2. แก้ `process_ask()` ไม่ให้ fall back to Q&A:
   ```python
   else:
       # Return error instead of fallback
       return StandardResponse(
           answer="⚠️ ไม่สามารถดึงข้อมูลจากคำขอได้...",
           grounding_status="EXTRACTION_FAILED"
       )
   ```

**บทเรียน:**
1. **ทุก function ที่รับ input ต้องมี validation** ก่อนประมวลผล
2. **ห้าม silent fallback** เมื่อเกิดปัญหา - ต้อง return error message ที่ชัดเจน
3. **LLM extraction อาจล้มเหลว** ต้องมี fallback plan ที่เหมาะสม

