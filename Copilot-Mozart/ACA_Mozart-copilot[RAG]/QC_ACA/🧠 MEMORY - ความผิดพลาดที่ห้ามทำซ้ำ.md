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

---

## 🔴 ความผิดพลาดที่ 13: LLM Extraction ไม่ Robust (21 ธ.ค. 2024 02:00)

**อาการ:**
- ผู้ใช้ส่ง input ยาว (3000+ chars) ละเอียด แต่ได้ Load Schedule เปล่า
- LLM อาจ return `{"rooms": [], "loads": []}` โดยไม่มี error
- Code ตรวจแค่ `if loads:` → True (เพราะ {} ก็ truthy)

**สาเหตุหลายจุด:**

### 1. Validation ไม่รัดกุม
```python
# ❌ ก่อน (ผิด)
if loads:  # {} = truthy = ผ่าน!

# ✅ หลัง (ถูก)
if loads and loads.get("rooms") and not loads.get("error"):
```

### 2. ไม่มี Checkpoint Logging
- ไม่รู้ว่า LLM extract ได้กี่ rooms/loads
- ไม่รู้ว่าหลุดตรงไหน

### 3. LLM Prompt ไม่ Multilingual
- รับแค่ไทย ถ้าผู้ใช้ผสมหลายภาษาอาจล้มเหลว

### 4. Gateway ไม่ Validate Response
- Return `response.json()` ตรงๆ โดยไม่เช็ค

**วิธีแก้:** (Commit: 1fef3c7, 4c967e2, 7db7dd7, f42aa75, 5f79f10)

1. **เพิ่ม Checkpoint Logging:**
   - [CP1] Gateway entry
   - [CP3] LLM extraction result
   - [CP4] Conversion input/output
   - [CP6] Build design entry
   - [CP7] Pipeline entry/circuits

2. **แก้ Validation ให้เข้มงวด:**
   ```python
   has_rooms = loads and loads.get("rooms")
   has_loads = loads and loads.get("loads")
   has_error = loads and "error" in loads
   
   if (has_rooms or has_loads) and not has_error:
       # proceed
   else:
       # return error with debug info
   ```

3. **Gateway Validate Response:**
   - Check grounding_status
   - Log warning ถ้า EXTRACTION_FAILED
   - Log warning ถ้า empty answer

**บทเรียน:**

1. **`if obj:` ไม่เพียงพอ** - ต้อง check content ด้วย
2. **ทุก function ต้องมี checkpoint log** เพื่อ debug
3. **Error ต้องไม่เงียบ** - ต้องมี message กลับมาเสมอ
4. **LLM ไม่ 100% reliable** - ต้องมี validation + default

---

## 🔴 ความผิดพลาดที่ 14: ไม่ Multilingual (21 ธ.ค. 2024 05:00)

**อาการ:**
- User พิมพ์ผสม Thai/English/typos
- LLM extraction ล้มเหลวหรือได้ผลไม่ถูกต้อง

**สาเหตุ:**
- LLM prompt สอนแค่ภาษาไทย
- ไม่มี fuzzy matching หลายภาษา

**วิธีแก้:**
1. เพิ่มคำสั่งใน prompt ให้รับทุกภาษา
2. เพิ่มตัวอย่าง multilingual
3. เพิ่ม fuzzy matching keywords หลายภาษา

**บทเรียน:**

1. **User ไม่พิมพ์สะอาด** - ต้อง handle typos
2. **Mixed language เป็นเรื่องปกติ** - AC, bedroom, ห้องนอน
3. **LLM (Gemini) รับหลายภาษาได้** - แค่สอนใน prompt

---

## 🚨 กฎเหล็กใหม่ (เพิ่ม 21 ธ.ค. 2024)

6. **ห้าม `if obj:` โดยไม่เช็ค content** - ใช้ `if obj and obj.get("key")`
7. **ทุก function ต้องมี checkpoint log** - [CPx] format
8. **LLM extraction ต้องมี:
   - Logging ก่อน/หลัง
   - Validation เข้มงวด
   - Default fallback
   - Multilingual support
9. **Debug info ต้องอยู่ใน error message** - ไม่ใช่แค่ "ผิดพลาด"
10. **ก่อนแก้ต้องทำ plan** - impact analysis + regression check

---

*เพิ่มเติมเมื่อ: 2025-12-21 05:30*
*กู จะ ไม่ ทำ ผิด แบบ เดิม อีก!*

---

## 🔴 ความผิดพลาดที่ 15: Cloud Run Cache Docker Hub Images (21 ธ.ค. 2024 23:00)

**อาการ:**
- GitHub Actions build+deploy "สำเร็จ" ✅
- แต่ Cloud Run ใช้ **image เดิม** ❌
- Code ใหม่ไม่ทำงาน

**สาเหตุ:**
- Cloud Run ดึง Docker Hub ผ่าน `mirror.gcr.io` (proxy cache)
- Cache ไม่ invalidate ทันทีเมื่อ push ใหม่
- Deploy บอกสำเร็จ แต่ดึง image เก่ามา!

**หลักฐาน:**
```bash
# Deploy command ใช้
docker.io/acatest01/mozart-rag:383bbaa...

# Cloud Run ดึงจริง
mirror.gcr.io/acatest01/mozart-rag@sha256:8e56bc30... # ← image เก่า!
```

**วิธีแก้:** (Commit: 045258b)
```yaml
# docker-build.yml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    no-cache: true  # ← บังคับ fresh build ทุกครั้ง!
    # ลบ cache-from / cache-to ออก
```

**บทเรียน:**

1. **Docker Hub + Cloud Run = อาจมี cache issue**
2. **Deploy "สำเร็จ" ไม่ได้หมายความว่า ใช้ image ใหม่!**
3. **ตรวจ image digest** ด้วย `gcloud run revisions describe`
4. **Artifact Registry ไม่มีปัญหานี้** (อยู่ GCP เดียวกัน)

---

## 🔴 ความผิดพลาดที่ 16: `no-cache: true` ไม่แก้ปัญหา mirror.gcr.io (22 ธ.ค. 2024 00:20)

**อาการ:**
- ใส่ `no-cache: true` ใน docker-build.yml แล้ว (commit 045258b)
- GitHub Actions build ใหม่ + push สำเร็จ ✅
- **แต่ Cloud Run ยังใช้ image เก่าเหมือนเดิม!** ❌

**สาเหตุที่แท้จริง:**
- `no-cache: true` แก้แค่ **Docker build layer cache** (ฝั่ง GitHub Actions)
- **ไม่ได้แก้** Cloud Run pulling cache จาก `mirror.gcr.io`
- `mirror.gcr.io` เป็น Google proxy cache สำหรับ Docker Hub
- Cache level นี้อยู่นอกเหนือการควบคุมของ workflow

**หลักฐาน:**
```bash
# Docker Hub (ล่าสุด)
sha256:33c5e96399fb3237154bd911d961c919e01569115be6bd9ba4436ebbda0d7214

# Cloud Run (ใช้จริง) - ยังเป็นตัวเก่า!
mirror.gcr.io/acatest01/mozart-rag@sha256:cfbd991f436c8c1bfc8ea15e7e707fe88d09070c38b0b1ffbf41dc2f0b49ce74
```

**วิธีแก้ที่ถูกต้อง:** (Commit: b11e2fb)
```yaml
# ย้ายจาก Docker Hub → Artifact Registry
# ก่อน (Docker Hub - มีปัญหา cache):
docker.io/acatest01/mozart-rag

# หลัง (Artifact Registry - ไม่มีปัญหา):
asia-southeast1-docker.pkg.dev/gen-lang-client-0658701327/mozart/mozart-rag
```

**ผู้รับผิดชอบ:**
- **ระบบ (Google):** mirror.gcr.io cache behavior ไม่ documented ชัดเจน
- **AI (Valida):** ไม่เข้าใจว่า `no-cache` แก้ได้แค่ build time ไม่ใช่ pull time
- **User:** ไม่มีความผิด - เชื่อตามที่ AI แนะนำ

**บทเรียน:**

1. **`no-cache: true` แก้ได้แค่ build cache ไม่ใช่ registry cache**
2. **Docker Hub + Cloud Run = ให้ใช้ Artifact Registry แทนเสมอ!**
3. **ต้องตรวจ image digest ทุกครั้ง** หลัง deploy
4. **อย่าเชื่อว่า "deploy สำเร็จ" = ใช้ code ใหม่**

---

## 🔴 ความผิดพลาดที่ 17: ไม่ตั้ง Cleanup Policy สำหรับ Artifact Registry (22 ธ.ค. 2024 00:45)

**อาการ:**
- Push images ไป Artifact Registry หลายครั้ง
- Repository size: 1,046 MB (1 GB) - เกิน Free Tier (500 MB)!
- ไม่มี auto-delete สำหรับ images เก่า

**สาเหตุ:**
- ย้ายไป Artifact Registry แต่ **ลืมตั้ง Cleanup Policy**
- ทุก build push image ใหม่ แต่ไม่ลบอันเก่า
- Images สะสมไปเรื่อยๆ

**ผู้รับผิดชอบ:**
- **AI (Valida):** ลืมคิดเรื่อง storage management ตอนย้าย registry
- **User:** ไม่มีความผิด - ถามตามหลัง

**วิธีแก้:**
```bash
# สร้าง cleanup-policy.json
[
  {"name": "keep-minimum-versions", "action": {"type": "Keep"}, 
   "mostRecentVersions": {"keepCount": 5}},
  {"name": "delete-old-untagged", "action": {"type": "Delete"},
   "condition": {"olderThan": "604800s", "tagState": "UNTAGGED"}}
]

# Apply policy
gcloud artifacts repositories set-cleanup-policies mozart \
  --location=asia-southeast1 --policy=cleanup-policy.json
```

**บทเรียน:**

1. **ย้าย registry ต้องคิดเรื่อง cleanup ด้วย!**
2. **Artifact Registry ไม่มี default cleanup** - ต้องตั้งเอง
3. **ตรวจ repository size** หลังใช้งานสักพัก
4. **กฎ: keep 5 + delete untagged after 7 days** = ประหยัดเงิน

---

## 🚨 กฎเหล็กใหม่ (เพิ่ม 22 ธ.ค. 2024)

11. **Docker Hub + Cloud Run = ห้ามใช้!** → ใช้ Artifact Registry เสมอ
12. **`no-cache: true` ไม่แก้ปัญหา mirror cache** → ต้องย้าย registry
13. **ย้าย registry ต้องตั้ง Cleanup Policy ทันที**
14. **ตรวจ image digest ทุกครั้งหลัง deploy:**
    ```bash
    gcloud run revisions describe <revision> --format="value(spec.containers[0].image)"
    ```
15. **Check repository size เป็นประจำ:**
    ```bash
    gcloud artifacts repositories describe mozart --location=asia-southeast1
    ```

---

*เพิ่มเติมเมื่อ: 2025-12-22 00:50*
*สรุป: ปัญหาวันนี้อยู่ที่ระบบ (mirror.gcr.io cache) + AI (ไม่รู้ว่า no-cache ไม่พอ + ลืมตั้ง cleanup)*
*User ไม่มีความผิด - ทำตามที่ AI แนะนำ*

---

## 🔴 ความผิดพลาดที่ 18: GitHub Actions Build แต่ไม่ Deploy (22 ธ.ค. 2024 01:08)

**อาการ:**
- ย้าย RAG ไป Artifact Registry แล้ว ✅
- GitHub Actions build + push สำเร็จ ✅
- **แต่ Cloud Run ยังใช้ image เก่า!** ❌
- ต้อง manual deploy ถึงจะได้ image ใหม่

**หลักฐาน:**
```bash
# Cloud Run ใช้ (เก่า)
asia-southeast1-docker.pkg.dev/.../mozart-rag:b11e2fb...

# Artifact Registry มี (ใหม่)
asia-southeast1-docker.pkg.dev/.../mozart-rag:0a07975...
```

**สาเหตุที่แท้จริง:**

1. **Workflow มี `needs: [build-gateway, build-frontend, build-mcp-core, build-rag]`**
   - ถ้า build ตัวใดตัวหนึ่ง fail → deploy job ไม่รันเลย!

2. **Deploy jobs มี `continue-on-error: true`**
   - ถ้า deploy fail ก็ไม่แจ้ง error!
   - Workflow ยัง show "Success" ทั้งที่ deploy ไม่ได้!

3. **Commit ที่แก้ MEMORY/docs ไม่ได้ trigger rebuild ทุก service**
   - Workflow มี `paths:` filter
   - ถ้าแก้เฉพาะ docs → อาจไม่ trigger build

**ผู้รับผิดชอบ:**
- **AI (Valida):** ไม่ได้ตรวจสอบว่า workflow deploy job ทำงานจริงไหม
- **Workflow Design:** `continue-on-error: true` ปิดบัง error

**วิธีแก้:**

```yaml
# ลบ continue-on-error หรือเปลี่ยนเป็น false
- name: 🚀 Deploy Mozart RAG to Cloud Run
  id: deploy-rag
  # continue-on-error: true  ← ลบออก!
  run: |
    gcloud run deploy mozart-rag ...
```

**บทเรียน:**

1. **`continue-on-error: true` = ปิดบัง failure!** → ใช้อย่างระวัง
2. **ตรวจ Cloud Run revision ทุกครั้งหลัง deploy** ไม่ใช่แค่ดู workflow status
3. **Artifact Registry แก้ได้แค่ cache issue** ไม่ได้แก้ deploy failure!
4. **Manual deploy ยังจำเป็น** ถ้า workflow มีปัญหา

---

## 🚨 กฎเหล็กใหม่ (เพิ่ม 22 ธ.ค. 2024 01:10)

16. **หลัง push ต้องตรวจ:**
    - [ ] GitHub Actions workflow สำเร็จ?
    - [ ] Deploy job รันหรือเปล่า?
    - [ ] Cloud Run revision ใหม่หรือยัง?
    - [ ] Image tag ตรงกับ commit SHA?

17. **`continue-on-error: true` = อันตราย!**
    - Fail silently = ไม่รู้ว่าพัง
    - ใช้เมื่อจำเป็นจริงๆ เท่านั้น

18. **คำสั่งยืนยัน deployment:**
    ```bash
    # ตรวจ image ที่ Cloud Run ใช้
    gcloud run services describe <service> --region=asia-southeast1 \
      --format="value(spec.template.spec.containers[0].image)"
    
    # เปรียบเทียบกับ commit ล่าสุด
    git log --oneline -1
    ```

---

*เพิ่มเติมเมื่อ: 2025-12-22 01:10*
*สรุป: Artifact Registry แก้ cache issue แต่ไม่ได้แก้ deploy failure!*
*ต้องตรวจสอบ Cloud Run revision ทุกครั้ง ไม่ใช่แค่ดู workflow status*

---

## 🔴🔴🔴 ความผิดพลาดที่ 19: สร้าง Folder ใหม่แต่ลืม COPY เข้า Docker!

> **วันที่:** 2025-12-22 02:24 (ค้นพบ Root Cause!)
> **ความรุนแรง:** 💀 CRITICAL - ทำให้ features หายไปใน Production

### อาการ:

```
User ส่ง request ครบถ้วน (มี site_context: "หม้อแปลง 50 เมตร ติดตั้งในบ้าน เป็นตู้เมน")
                ↓
แต่ได้ผลลัพธ์แค่ Spare Circuits เปล่าๆ!
                ↓
Injectors (Derating, kA Rating, N-G Link) ไม่ทำงาน
```

### สาเหตุ:

**สร้าง `mcp_core_v2/context/` folder ใหม่ที่มี inject files:**
```
context/
├── __init__.py
├── derating_injector.py
├── ka_rating_injector.py
└── ng_link_injector.py
```

**แต่ลืมแก้ `Dockerfile` ให้ COPY folder นี้เข้าไป!**

```dockerfile
# มีแค่:
COPY models/ ./models/
COPY core/ ./core/
COPY dal/ ./dal/
COPY db/ ./db/
COPY cad/ ./cad/
# ❌ ขาด: COPY context/ ./context/
```

**Docker image ไม่มี context/ folder** → **Python ImportError หรือ skip inject logic!**

### ผู้รับผิดชอบ:

| ใคร | ความผิด |
|-----|---------|
| **AI (Nexia)** | สร้าง folder ใหม่ แต่ไม่ได้ update Dockerfile |
| **Human** | ไม่ได้ตรวจสอบว่า files ใหม่ถูก include ใน Docker หรือไม่ |
| **AI (Valida)** | ตรวจ logs นานแต่ไม่เช็ค Dockerfile เลย (2 ชม.+!) |

### วิธีแก้:

```dockerfile
# เพิ่มใน mcp_core_v2/Docker/Dockerfile:
COPY context/ ./context/
```

### 💀 บทเรียน (กฎเหล็กใหม่):

19. **ทุกครั้งที่สร้าง folder/module ใหม่ → ต้อง update Dockerfile!**
    ```bash
    # ตรวจสอบ:
    grep "COPY.*/" Dockerfile
    ls -la <project>/
    # ถ้า folder ใน ls ไม่มีใน COPY → ต้องเพิ่ม!
    ```

20. **Python ImportError บน Cloud Run = ลืม COPY ใน Docker**
    - Local ทำงานได้ ≠ Docker ทำงานได้
    - ต้องทดสอบ Docker image ก่อน deploy!

21. **Checklist ก่อน push:**
    - [ ] สร้าง folder ใหม่หรือไม่?
    - [ ] ถ้าใช่ → update Dockerfile แล้วหรือยัง?
    - [ ] Build Docker local แล้วทดสอบหรือยัง?

---

*เพิ่มเติมเมื่อ: 2025-12-22 02:24*
*สรุป: สร้าง folder ใหม่แต่ลืม COPY ใน Dockerfile = Features หายไปทั้ง Production!*
*2 ชั่วโมง+ หาสาเหตุ เพราะมัวแต่ดู logs/code ไม่ได้ดู Dockerfile!*

---

## 🔴 ความผิดพลาดที่ 20: F-String Escape ใน Prompt - `{` vs `{{`

> **วันที่เกิด:** 2025-12-22 23:11
> **ผู้ทำผิด:** AI (Sophia/Antigravity)
> **Commit ที่พัง:** 2c2d830
> **Hotfix:** d782239

### อาการ:

```
❌ Invalid format specifier ' "ชื่อห้อง", "type": "ประเภท..." ' for object of type 'str'
```

ระบบพังทันทีเมื่อ user ส่ง request!

### สาเหตุ:

AI แก้ไข JSON example ใน **f-string prompt** ของ `service.py`:

```python
# ❌ ทำไปผิด (ใช้ single brace)
extraction_prompt = f"""
...
"rooms": [
    {
      "name": "ชื่อห้อง",   # <-- Python คิดว่านี่คือ variable format!
      "type": "..."
    }
]
"""

# ✅ ที่ถูก (ต้อง escape double brace)
extraction_prompt = f"""
...
"rooms": [
    {{"name": "ชื่อห้อง", "type": "..."}}  # <-- Escaped braces
]
"""
```

### ทำไมถึงเกิด:

1. AI ต้องการทำให้ JSON example อ่านง่ายขึ้น → แยกเป็นหลายบรรทัด
2. **ลืมว่าอยู่ใน f-string** → ไม่ได้ escape `{` เป็น `{{`
3. Python ตีความ `{"name": ...}` เป็น format specifier → Error!

### วิธีป้องกัน:

22. **ทุกครั้งที่แก้ไข f-string ที่มี JSON/dict:**
    - ต้องใช้ `{{` และ `}}` แทน `{` และ `}`
    - หรือใช้ `str.format()` / Template strings แทน f-string
    
23. **ก่อน commit code ที่มี f-string:**
    ```bash
    # ทดสอบ syntax ก่อน
    python -c "from app.service import RagService"
    ```
    
24. **Rule: ถ้า f-string มี JSON example → ย่อเป็นบรรทัดเดียว**
    - หลายบรรทัด = หลาย `{` = หลายโอกาสลืม escape

### บทเรียน:

| สิ่งที่ต้องจำ | เหตุผล |
|--------------|--------|
| `{` ใน f-string = variable | Python syntax rule |
| `{{` ใน f-string = literal `{` | Escape sequence |
| แก้ prompt = ต้อง test ทันที | ไม่มี compile-time check |

---

*เพิ่มเติมเมื่อ: 2025-12-22 23:14*
*สรุป: แก้ JSON example ใน f-string prompt แต่ลืม escape braces = ระบบพังทั้ง Production!*
*แก้ภายใน 3 นาที แต่ไม่ควรเกิดตั้งแต่แรก!*
