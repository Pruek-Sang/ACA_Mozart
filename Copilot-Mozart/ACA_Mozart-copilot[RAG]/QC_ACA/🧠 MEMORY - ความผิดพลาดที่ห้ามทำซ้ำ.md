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

---

## 🔴 ความผิดพลาดที่ 21: Pydantic Type Mismatch ใน API Request Model (HTTP 422)

**วันที่:** 2025-12-23

### อาการ:

Gateway ส่ง request ไป RAG แล้วได้ **HTTP 422 Unprocessable Entity**:
```json
{
  "error": "Client error '422 unknown' for url '.../api/v1/ask'",
  "status_code": 422
}
```

### สาเหตุ:

ใน `models.py` → `QueryRequest`:
```python
# ❌ ที่ผิด - ประกาศ Dict[str, str] (string เท่านั้น)
site_context: Optional[Dict[str, str]] = Field(...)
```

แต่ Gateway ส่งค่า **numeric**:
```python
# gate_way_new.py line 283
context['service_distance_m'] = distance  # distance = float!
```

Pydantic validation fails เพราะ `10.0` ไม่ใช่ `str`!

### วิธีแก้ที่ถูกต้อง:

```python
# ✅ ที่ถูก - ใช้ Dict[str, Any] รองรับทุก type
site_context: Optional[Dict[str, Any]] = Field(
    None,
    description="Site context for design calculations"
)
```

### ทำไมถึงเกิด:

1. เพิ่ม `site_context` field ใหม่ใน `QueryRequest`
2. **กำหนด type แบบ strict (`Dict[str, str]`)** โดยไม่ตรวจสอบว่า Gateway ส่งอะไรมา
3. Gateway extract `service_distance_m` เป็น `float` → Pydantic reject ทันที!

### วิธีป้องกัน:

25. **เมื่อเพิ่ม field ใหม่ใน Pydantic model:**
    - ต้อง **trace ทุก caller** ว่าส่ง data type อะไรมา
    - ถ้า field รับได้หลาย type → ใช้ `Any` หรือ `Union`
    
26. **ก่อน commit model changes:**
    ```bash
    # Test with actual Gateway payload
    curl -X POST .../api/v1/ask -d '{"query": "...", "site_context": {"service_distance_m": 10.0}}'
    ```

27. **Rule: Dict ใน API model ควรใช้ `Dict[str, Any]` ไม่ใช่ `Dict[str, str]`**
    - JSON values อาจเป็น string, number, boolean, null, array, object
    - `Dict[str, str]` = too strict สำหรับ real-world API

### บทเรียน:

| สิ่งที่ต้องจำ | เหตุผล |
|--------------|--------|
| `Dict[str, str]` = string only | Pydantic strict validation |
| `Dict[str, Any]` = flexible | ยอมรับ JSON ทุกชนิด |
| 422 = Validation error | ไม่ใช่ bug ใน logic แต่เป็น type mismatch |

---

*เพิ่มเติมเมื่อ: 2025-12-23 00:45*
*สรุป: เพิ่ม field ใน Models โดยไม่ตรวจสอบ type ที่ Gateway ส่งมา = 422 Error ทั้ง Production!*
*แก้ภายใน 2 นาที - แค่เปลี่ยน `Dict[str, str]` เป็น `Dict[str, Any]`*

---

## 🔴🔴 ความผิดพลาดที่ 22: API Contract Drift - แก้ Backend แต่ลืมแจ้ง Frontend! (สำคัญมาก!)

> **วันที่:** 2025-12-23 02:00
> **ความรุนแรง:** 💀💀 CRITICAL - Silent Failure (เงียบๆ แต่ผิดหมด)
> **Root Cause ของวัน:** Bug "0 Watts in Summary" มาจากปัญหานี้!

### อาการ:

```
รายงานการออกแบบแสดง:
┌─────────────────────────────────────┐
│ 📊 สรุปโหลดไฟฟ้า                     │
│ ⚡ กำลังไฟฟ้ารวม | 0 W              │  ← ❌ ควรเป็น 22,000W!
│ 🔌 กระแสโหลดรวม | 0.0 A            │
│ 📦 จำนวนวงจร   | 0 วงจร            │
└─────────────────────────────────────┘

แต่ข้างล่าง:
• ชั้น 1 → รวม 15,850W               │  ← ✅ มีค่าถูก!
• ชั้น 2 → รวม 6,150W                │
```

**Summary เป็น 0 แต่ Detail ถูกต้อง!** = Data มี แต่อ่านผิดที่!

### สาเหตุ (API Contract Drift):

**MCP Core (`result_builder.py`) ส่ง:**
```json
{
  "summary": {
    "total_load_va": 22000,         // ← ชื่อนี้!
    "component_count": {
      "loads": 35                    // ← ซ้อนอยู่ใน dict!
    }
  }
}
```

**RAG (`markdown_formatter.py`) คาดหวัง:**
```python
total_watts = summary.get('total_watts')    # ❌ หาไม่เจอ! (ชื่อผิด)
demand_current = summary.get('demand_current')  # ❌ ไม่มี field นี้!
num_loads = summary.get('num_loads')        # ❌ หาไม่เจอ! (path ผิด)
```

**ผลลัพธ์:** ทุก field ได้ default = `0`!

### ทำไมถึงเกิด:

```
Timeline:
1. MCP Core refactor ภายใน → เปลี่ยนชื่อ total_watts → total_load_va
2. เปลี่ยน num_loads → component_count.loads
3. ไม่ได้แจ้ง RAG team / ไม่ได้ update interface doc
4. RAG ยังใช้ชื่อเก่า → .get() return None → default 0
5. ไม่มี Error เพราะ .get() ไม่ crash → Silent Failure!
```

### วิธีแก้ (Commit: 6b4c05d):

```python
# ✅ ที่ถูก - ทำให้ RAG "ปรับตัว" ได้
def _create_load_summary(self, summary: Dict) -> List[str]:
    # Try both old and new field names
    total_watts = summary.get('total_watts') or summary.get('total_load_va', 0)
    
    # Calculate if not provided
    demand_current = summary.get('demand_current')
    if demand_current is None:
        demand_current = total_watts / 230 if total_watts else 0
    
    # Handle nested dict
    component_count = summary.get('component_count') or {}
    num_loads = summary.get('num_loads') or component_count.get('loads', 0)
```

### ⚠️ ทำไม Fix นี้คือ "Sticking Plaster" (ยาปิดแผล):

**ข้อดี:**
- แก้ปัญหาได้เร็ว ไม่ต้องแก้ MCP Core
- RAG ทนทานขึ้น (resilient) ต่อการเปลี่ยนแปลง

**ข้อเสีย (Tech Debt):**
- MCP Core ยัง output schema "ไม่สะอาด"
- ถ้ามี Client ตัวที่ 3 (เช่น Mobile App) → ต้องเขียน adapter อีก!
- ไม่ได้แก้ที่ต้นเหตุ (Source) แก้ที่ปลายทาง (Consumer)

### 💀 บทเรียน (กฎเหล็กใหม่):

28. **ห้าม Refactor Backend โดยไม่ตรวจสอบ Consumer!**
    - Before changing API response field names → GREP all consumers!
    - ```bash
      grep -r "total_watts" ../Copilot-Mozart/  # หาว่าใครใช้อยู่
      ```

29. **ใช้ Shared Model Library (Long-term Fix):**
    ```
    /mozart-common/
      contracts/
        design_result.py  ← Class เดียวกัน ทั้ง MCP และ RAG import มาใช้
    ```
    - ถ้า MCP เปลี่ยนชื่อ field → RAG จะ **Build Error** ทันที (ก่อน deploy)

30. **`.get()` คืออันตรายเงียบ:**
    ```python
    # ❌ Silent failure:
    value = data.get('wrong_key')  # → None, no error!
    
    # ✅ Fail loud:
    value = data['required_key']   # → KeyError if missing
    
    # ✅ หรือ Explicit check:
    if 'required_key' not in data:
        raise ValueError("Missing required_key!")
    ```

31. **Contract Testing (Future):**
    - ใช้ Pact หรือ OpenAPI schema validation
    - ทุกครั้งที่ MCP จะ deploy → ต้อง pass contract test กับ RAG ก่อน

### Flow ที่ถูกต้อง (Ideal):

```
┌──────────────────┐     Contract Doc     ┌──────────────────┐
│    MCP Core      │◄───────────────────►│      RAG         │
│ (Producer)       │   (Shared Schema)   │  (Consumer)      │
└────────┬─────────┘                     └────────┬─────────┘
         │                                        │
         ▼                                        ▼
    result_builder.py                    markdown_formatter.py
    - Uses DesignSummary class           - Imports same class!
    - If change → tests fail →           - If mismatch → tests fail →
      CANNOT deploy until fix!             CANNOT deploy until fix!
```

### สิ่งที่ต้องทำ (Next Refactoring):

- [ ] สร้าง `mozart-common` package  
- [ ] ย้าย Models ไปไว้ใน shared package
- [ ] ให้ทั้ง MCP และ RAG import จาก package เดียวกัน
- [ ] Add Contract Test ใน CI/CD

---

*เพิ่มเติมเมื่อ: 2025-12-23 02:00*
*สรุป: แก้ Backend แต่ลืมแจ้ง Frontend = Silent Failure ทั้ง Production!*
*Root Cause: API Contract Drift - 2 services คุยกันคนละภาษา แต่ไม่มี error!*
*Fix: ทำให้ Consumer ฉลาดขึ้น (adapter pattern) แต่แผลเป็นยังอยู่ (Tech Debt)*

---

## 🚨 กฎเหล็กใหม่ (เพิ่ม 23 ธ.ค. 2024 02:00)

28. **ห้าม Refactor API response โดยไม่ grep consumers!**
29. **Long-term: ใช้ Shared Model Library**
30. **`.get()` = อันตรายเงียบ** - ใช้ explicit checks สำหรับ required fields
31. **ต้องมี Contract Testing** ในอนาคต

---

## 🔮 ถ้าพังอีก ควรเช็คตรงไหนก่อน? (Quick Debugging Guide)

เมื่อเจอปัญหาแปลกๆ ให้เรียงลำดับเช็คดังนี้:

| ลำดับ | ปัญหา | สิ่งที่ต้องเช็ค |
|:-----:|-------|----------------|
| 1️⃣ | **Deployment Failure** | Cloud Run Revision ตรงกับ Commit ไหม? |
| 2️⃣ | **API Contract Drift** | Field names ตรงกันระหว่าง Producer/Consumer ไหม? |
| 3️⃣ | **LLM Extraction Failure** | Logs [CP3] บอกว่า extract ได้กี่ rooms/loads? |
| 4️⃣ | **Type Mismatch (422)** | Pydantic model รับ type ถูกไหม? |
| 5️⃣ | **Missing Files in Docker** | Dockerfile มี COPY folder ใหม่ไหม? |
| 6️⃣ | **F-String Escape** | มี `{` ใน f-string ที่ไม่ได้ escape ไหม? |

```bash
# Quick Debug Commands:
# 1. Check Cloud Run
gcloud run revisions list --service=mozart-rag --region=asia-southeast1

# 2. Check if field exists
grep -r "total_watts" app/formatters/

# 3. Check LLM logs
# ดู Cloud Run logs หา [CP3]

# 4. Check Pydantic model
grep -r "site_context" app/models.py

# 5. Check Dockerfile
grep "COPY" ../mcp_core_v2/Docker/Dockerfile
```

---

*อัพเดทล่าสุด: 2025-12-23 02:00*
*กู จะ ไม่ ทำ ผิด แบบ เดิม อีก! (รอบที่ 22 แล้ว...)*

---

## 🔴 ความผิดพลาดที่ 22: HTTP Transport Layer ไม่ส่ง Field ต่อ (24 ธ.ค. 2024)

> **วันที่เกิด:** 2025-12-24 02:00
> **ผู้ทำผิด:** AI (ทุกคนที่แก้ circuit_grouper แต่ไม่ได้แก้ api.py + mcp_client.py)
> **Commits แก้ไข:** 8ceb888, 0c87d09

### อาการ:

```
MCP Core คำนวณ grouped_circuits ถูกต้อง ✅
แต่ Formatter แสดงโหลดแยกรายการ 35 ตัว แทนที่จะเป็นวงจร 12-15 วงจร! ❌
```

### สาเหตุ (Integration Gap):

**เพิ่ม feature ในแต่ละ layer แต่ลืม HTTP transport layer!**

```
✅ circuit_grouper.py  → สร้าง grouped_circuits
✅ pipeline.py         → ส่งไป result_builder
✅ result_builder.py   → ใส่ใน DesignResult
❌ api.py              → ไม่ได้ใส่ใน HTTP response   ← ลืม!
❌ mcp_client.py       → ไม่ได้อ่านจาก response     ← ลืม!
✅ markdown_formatter.py → พร้อมใช้ (แต่ไม่เคยได้รับ)
```

### ทำไมไม่เจอ:

| เหตุการณ์ | สิ่งที่เกิด |
|---------|-----------|
| Unit Test | ผ่าน! เพราะทดสอบ `circuit_grouper` โดยตรง |
| Local Test | ผ่าน! เพราะไม่ได้ผ่าน HTTP |
| Cloud Run | ล้มเหลว! เพราะ data ต้องผ่าน HTTP API |

### วิธีแก้:

```python
# api.py - เพิ่ม field ใน DesignResultOutput
grouped_circuits: Optional[List[Dict[str, Any]]] = None

# api.py - เพิ่มใน _convert_to_output()
grouped_circuits=result.grouped_circuits if hasattr(result, 'grouped_circuits') else []

# mcp_client.py - เพิ่ม field ใน McpDesignResponse
grouped_circuits: Optional[list] = None

# mcp_client.py - เพิ่มใน design()
grouped_circuits=data.get("grouped_circuits")
```

### บทเรียน:

1. **เพิ่ม feature ต้องตามสายข้อมูลทุก layer!**
2. **HTTP API layer มักถูกลืม** เพราะ unit test ไม่ผ่าน
3. **ต้องมี E2E Test** ที่ทดสอบ flow ทั้งหมด

---

## 🔴 ความผิดพลาดที่ 23: Hardcode ค่าใน Business Logic (24 ธ.ค. 2024)

> **วันที่เกิด:** 2025-12-24 02:15
> **ผู้ทำผิด:** AI (ใครก็ตามที่ hardcode power_factor=0.85 ใน api.py)
> **Commit แก้ไข:** 6af5036

### อาการ:

```
Water Heater 4500W ได้เบรกเกอร์ 30A (ผิด)
ควรได้ 25A (ถูก)
```

### สาเหตุ:

**api.py บรรทัด 312 hardcode power_factor=0.85 สำหรับทุกโหลด!**

```python
# ❌ ผิด - Hardcode ค่า
power_factor=0.85  # Default power factor

# ✅ ถูก - ใช้ค่าที่ส่งมาจาก RAG
power_factor=load.power_factor if load.power_factor else 0.85
```

### ผลกระทบ:

| โหลด | PF ถูก | PF ผิด | ผลลัพธ์ |
|------|--------|--------|---------|
| Water Heater 4500W | 1.0 (resistive) | 0.85 | Current 23A → 30A breaker ❌ |
| Water Heater 4500W | 1.0 (resistive) | 1.0 | Current 19.57A → 25A breaker ✅ |

### บทเรียน:

1. **ห้าม hardcode ค่าที่ขึ้นกับประเภทโหลด!**
2. **ค่าที่ควรเป็น parameter:**
   - Power Factor
   - Continuous Load Factor
   - Voltage
3. **Grep หา pattern นี้เพื่อเช็ค:**
   ```bash
   grep -r "= 0.85\|= 230\|= 1.25" --include="*.py"
   ```

---

## 🚨 กฎเหล็กใหม่ (เพิ่ม 24 ธ.ค. 2024)

32. **เพิ่ม field ใน Core ต้องตามสายข้อมูล:**
    - [ ] Core model (DesignResult)
    - [ ] API output (DesignResultOutput)  ← มักลืม!
    - [ ] HTTP client (McpDesignResponse) ← มักลืม!
    - [ ] Formatter/Display

33. **ห้าม hardcode ค่าที่ขึ้นกับประเภทโหลด!**
    - Power Factor → ใช้ dict lookup by load_type
    - Voltage → รับจาก request
    - Continuous Factor → กำหนดตาม circuit_type

34. **ต้องมี E2E Test ที่ทดสอบ HTTP layer:**
    ```python
    # tests/test_e2e_data_flow.py
    def test_grouped_circuits_in_response():
        # ส่ง request ผ่าน HTTP
        # ตรวจว่า response มี grouped_circuits
    ```

---

## 🔮 ถ้าพังอีก ควรเช็คตรงไหนก่อน? (Quick Debugging Guide - อัพเดท)

เมื่อเจอปัญหาแปลกๆ ให้เรียงลำดับเช็คดังนี้:

| ลำดับ | ปัญหา | สิ่งที่ต้องเช็ค |
|:-----:|-------|----------------|
| 1️⃣ | **Deployment Failure** | Cloud Run Revision ตรงกับ Commit ไหม? |
| 2️⃣ | **API Contract Drift** | Field names ตรงกันระหว่าง Producer/Consumer ไหม? |
| 3️⃣ | **HTTP Field Missing** | api.py + mcp_client.py มี field ครบไหม? ← ใหม่! |
| 4️⃣ | **Hardcoded Values** | มี hardcode ค่าที่ควรเป็น parameter ไหม? ← ใหม่! |
| 5️⃣ | **LLM Extraction Failure** | Logs [CP3] บอกว่า extract ได้กี่ rooms/loads? |
| 6️⃣ | **Type Mismatch (422)** | Pydantic model รับ type ถูกไหม? |
| 7️⃣ | **Missing Files in Docker** | Dockerfile มี COPY folder ใหม่ไหม? |
| 8️⃣ | **F-String Escape** | มี `{` ใน f-string ที่ไม่ได้ escape ไหม? |

```bash
# Quick Debug Commands:
# 1. Check Cloud Run
gcloud run revisions list --service=mozart-rag --region=asia-southeast1

# 2. Check HTTP field transfer (NEW!)
grep "grouped_circuits" mcp_core_v2/api.py Copilot-Mozart/ACA_Mozart-copilot\[RAG\]/app/mcp_client.py

# 3. Check hardcoded values (NEW!)
grep -r "= 0.85\|= 230\|= 1.25" --include="*.py" | grep -v venv | grep -v test

# 4. Check Pydantic model
grep -r "site_context" app/models.py

# 5. Check Dockerfile
grep "COPY" ../mcp_core_v2/Docker/Dockerfile
```

---

*อัพเดทล่าสุด: 2025-12-24 02:48*
*กู จะ ไม่ ทำ ผิด แบบ เดิม อีก! (รอบที่ 24 แล้ว...)*

---

## 🔴 ความผิดพลาดที่ 24: Dataclass ไม่ Serialize เป็น JSON (24 ธ.ค. 2024 03:30)

> **วันที่เกิด:** 2025-12-24 03:30
> **ผู้ทำผิด:** AI (ใครก็ตามที่สร้าง GroupedCircuit dataclass โดยไม่มี to_dict)
> **Commit แก้ไข:** ac6c950

### อาการ:

```
grouped_circuits ใน API output = [] หรือ None
ทั้งที่ MCP Core คำนวณถูกต้อง!
Formatter เห็น empty → Fallback ไปแสดง 35 loads แทน
```

### สาเหตุ:

**`group_loads()` return `Dict[str, GroupedCircuit]` แต่ API คาดหวัง `List[Dict]`!**

```python
# ❌ ก่อน (พัง)
def group_loads(...) -> Dict[str, GroupedCircuit]:
    return self.circuits  # Python objects!

# ✅ หลัง (ใช้งานได้)
def group_loads(...) -> List[Dict[str, Any]]:
    return [circuit.to_dict() for circuit in self.circuits.values()]
```

**Pydantic Behavior:**
- เจอ type mismatch (Object ≠ Dict)
- **Silent fail** → return `None` หรือ `[]`
- ไม่มี Error message!

### บทเรียน:

1. **Dataclass ต้องมี `to_dict()` method** ถ้าจะส่งผ่าน API
2. **ตรวจสอบ Return Type** ให้ตรงกับ API contract
3. **Pydantic ไม่ serialize Python objects อัตโนมัติ** (ต้องเป็น dict)

---

## 🚨 กฎเหล็กใหม่ (เพิ่ม 24 ธ.ค. 2024 03:30)

35. **Class ที่จะส่งผ่าน API ต้องมี:**
    - `to_dict()` method
    - หรือใช้ Pydantic BaseModel (ไม่ใช่ dataclass)

36. **ตรวจสอบ Return Type ก่อน Deploy:**
    ```bash
    grep -n "def.*->" file.py | grep -v "Dict\|List\|str\|int"
    ```

---

*อัพเดทล่าสุด: 2025-12-24 03:30*
*กู จะ ไม่ ทำ ผิด แบบ เดิม อีก! (รอบที่ 25 แล้ว...)*

---

## 🔴 ความผิดพลาดที่ 21: Formatter Slicing Limit ทำให้ข้อมูลสำคัญหาย (27 ธ.ค. 2024)

> **อาการ:**
> - ระบบคำนวณถูก (kA Warning ถูกสร้างใน logs)
> - Data Flow ถูกต้อง (RAG -> MCP -> RAG)
> - **แต่ Warning ไม่แสดงในผลลัพธ์สุดท้าย!**

**สาเหตุ:**
Formatter มีการจำกัดจำนวนการแสดงผล (Slicing) โดยไม่จัดลำดับความสำคัญ:
```python
# ❌ Original Code (Bug)
for warn in warnings[:5]:  # แสดงแค่ 5 ตัวแรก
    lines.append(f"- ⚠️ {warn}")
```
- Warnings ที่ไม่สำคัญ (VD info, AFCI) ถมเต็ม 5 ช่องแรก
- Critical Warning (kA Safety) ถูก append ทีหลัง (index 29) -> **ถูกตัดทิ้ง!**

**วิธีแก้:**
1. **Prioritize Critical Items:** กรองหาคำสำคัญ (kA, อันตราย, RCBO) แล้วแสดงพวกนี้ก่อน
2. **Consolidate Repetitive Items:** รวม warning ที่ซ้ำกัน (เช่น "VD 18 วงจร ใช้ระยะ default") เป็นบรรทัดเดียว

**กฎเหล็ก:**
22. **ถ้าข้อมูลมีใน Log แต่หายใน UI -> เช็ค Display Loop/Slicing Limit ([:X]) ทันที!**
    - ห้ามใช้ `[:Limit]` กับข้อมูลความปลอดภัยโดยไม่ sort/filter ก่อนเสมอ

---

## 🔴 ความผิดพลาดที่ 22: React Hooks Violation - Regression Bug (1 ม.ค. 2026)

> **อาการ:**
> - User เปิดเว็บแล้วเจอ "เกิดข้อผิดพลาดในการแสดงผล" (ErrorBoundary)
> - Console: **"Rendered more hooks than during the previous render"** (React Error #310)
> - Production พังหลังจาก deploy Compact Table feature

**ผู้ทำผิด:** AI (Estrella/Antigravity)

### สาเหตุ:

Estrella แก้ code Compact Table แล้ว **ย้าย useCallback ไปผิดที่:**

```tsx
// ❌ หลัง Estrella แก้ (ผิด!)
function ResultViewer() {
  const [activeTab, setActiveTab] = useState('table');  // hook 1
  
  if (isLoading) return <Loading />;  // ← early return ก่อน hook 2!
  if (!data) return <Empty />;
  
  const handleDownloadExcel = useCallback(...);  // ← hook 2 หลัง early return!
}
```

**ผลลัพธ์:**

| Render ครั้งที่ | สถานะ | Hooks ที่เรียก |
|:---------------:|-------|:--------------:|
| 1 | `isLoading = true` | **1** (useState) |
| 2 | `data = มีค่า` | **2** (useState + useCallback) |

**React เห็นจำนวน hooks ไม่เท่ากัน → CRASH!**

### ทำไม npm build ไม่จับ:

- `npm run build` เช็คแค่ TypeScript syntax
- **ไม่ได้ run React จริง** → ไม่เห็น hooks order issue
- **ไม่มี ESLint hooks rules ใน CI** ← Root cause ของการหลุด Production!

### วิธีแก้:

```tsx
// ✅ ถูกต้อง: hooks ทั้งหมดก่อน early returns
function ResultViewer() {
  const [activeTab, setActiveTab] = useState('table');
  const handleDownloadExcel = useCallback(...);  // ← ย้ายขึ้นมา!
  
  if (isLoading) return <Loading />;
  if (!data) return <Empty />;
  // ... render
}
```

### Prevention ที่เพิ่มแล้ว:

1. **ESLint + React Hooks Plugin** (`react-hooks/rules-of-hooks: error`)
2. **Frontend Lint Job ใน CI** (ต้องผ่านก่อน build)
3. **Unit Tests** (Vitest + React Testing Library)
4. **Hooks Stability Tests** (ทดสอบ re-render ไม่ crash)

### 🚨 กฎเหล็กใหม่:

37. **React Hooks ต้องอยู่ก่อน early returns เสมอ!**
    - useState, useCallback, useMemo, useEffect ต้องอยู่บนสุดของ function
    - อย่า put hooks หลัง `if (...) return`

38. **แก้ Frontend ต้อง:**
    - [ ] รัน `npm run lint` ก่อน commit
    - [ ] เปิด browser ดูจริงก่อน push
    - [ ] มี unit tests สำหรับ component สำคัญ

39. **npm build ผ่าน ≠ Code ถูกต้อง!**
    - Build เช็คแค่ syntax
    - ต้องมี ESLint + Tests ด้วย

---

*เพิ่มเติมเมื่อ: 2026-01-01 22:00*
*สรุป: Regression Bug ที่ Estrella สร้างขึ้นเองตอนแก้ code โดยไม่ test ใน browser ก่อน push!*
*ความผิดของ Estrella 100% - ไม่ใช่ปัญหาระบบหรือ user*

---

## 🔴 ความผิดพลาดที่ 40: Supabase Query Syntax (Error #310)

**อาการ:**
- Frontend แสดง "Error #310"
- Health check บอก `supabase: "error"`
- Pytest error: `table not found`

**สาเหตุ:**
ใช้ syntax ผิด: `client.table("mozart.sessions")`

**วิธีแก้:**
```python
# ❌ WRONG
client.table("mozart.sessions").select("*")

# ✅ CORRECT
client.schema("mozart").table("sessions").select("*")
```

**ไฟล์ที่ต้องแก้:**
- `app/context/supabase_client.py` (line 80-83)
- `app/routes.py` (line 147-149)

---

## 🔴 ความผิดพลาดที่ 41: Deploy สำเร็จแต่ App พัง

**อาการ:**
- GitHub Actions Deploy: ✅
- Health check: 200 OK
- แต่ใช้งานจริงไม่ได้!

**สาเหตุ:**
Health check เดิมแค่เช็ค `status: alive` แต่ไม่ validate Supabase connection

**วิธีแก้:**
1. เพิ่ม Smoke Test หลัง deploy
2. ต้อง assert `supabase: "connected"` ไม่ใช่แค่ status
3. เพิ่ม Auto-Rollback ถ้า smoke fail

**ไฟล์ใหม่:**
- `tests/test_smoke_production.py`
- `.github/workflows/docker-build.yml` (smoke-test, rollback jobs)

---

## 🔴 ความผิดพลาดที่ 42: AI รับงานต่อแล้วหา Bug ไม่เจอ

**อาการ:**
- AI ใหม่มา debug แต่ไม่รู้จะเริ่มจากไหน
- พยายาม fix random โดยไม่เข้าใจ architecture

**สาเหตุ:**
ไม่มี documentation สำหรับ debugging

**วิธีแก้:**
อ่านไฟล์เหล่านี้ก่อน debug:
1. `QC_ACA/CI_CD_Debugging_Guide.md` ← Quick diagnosis
2. `QC_ACA/Blackbox_Workflow_Architecture.md` ← Data flow
3. `QC_ACA/🧠 MEMORY - ความผิดพลาดที่ห้ามทำซ้ำ.md` ← ไฟล์นี้!

---

*เพิ่มเติมเมื่อ: 2026-01-02 00:26*
*สรุป: เพิ่ม CI/CD Testing + Debugging Guide สำหรับ AI/Dev handover*

---

## 🔴🔴🔴 ความผิดพลาดที่ 43: Typo ในชื่อตัวแปร → Silent Failure (6 ม.ค. 2026)

> **วันที่เกิด:** 2026-01-06 00:08
> **ผู้ค้นพบ:** Enigma (The Anomaly Hunter)
> **ความรุนแรง:** 💀💀💀 CATASTROPHIC - ทำให้ VD ผิดทุก request!
> **Commit แก้ไข:** TBD

### อาการ:

```
- VD% = 2.0 ทุกวงจร (เหมือนกันหมด)
- "36 วงจร ใช้ระยะ Default" แม้ผู้ใช้ระบุ 15m/25m
- Local Tests ผ่านหมด แต่ Production พัง
- The Paradox: ทุก Code Path ดูเหมือนถูก แต่ผลลัพธ์ผิด
```

### สาเหตุ (TYPO!):

**`service.py` Line 922:**
```python
# ❌ BEFORE (WRONG!)
li_floor_distances = extracted.get("floor_distances", {})
if llm_floor_distances:  # ← llm_floor_distances ไม่เคยถูกประกาศ!
    floor_distances = {int(k): float(v) for k, v in llm_floor_distances.items() if v}
```

**ปัญหา:**
- Line 922 กำหนดค่าให้ `li_floor_distances` (prefix `li_`)
- Line 923-926 ใช้ `llm_floor_distances` (prefix `llm_`) ซึ่ง **ไม่มีอยู่จริง!**
- Python throw `NameError` ทุกครั้ง → ถูก catch โดย `try-except` → return error object
- Caller ignore error → ใช้ partial data หรือ fallback → **VD ผิดทุก request!**

### ทำไม Local Tests ผ่าน?

1. Tests อาจไม่ได้ทดสอบ path นี้โดยเฉพาะ
2. Tests อาจ mock LLM response ที่ไม่มี `floor_distances`
3. Try-except ปิดบัง error → ไม่มี crash ให้เห็น

### วิธีแก้:

```python
# ✅ AFTER (CORRECT!)
llm_floor_distances = extracted.get("floor_distances", {})  # เปลี่ยน li_ → llm_
if llm_floor_distances:
    floor_distances = {int(k): float(v) for k, v in llm_floor_distances.items() if v}
```

### 💀 บทเรียน (กฎเหล็กใหม่):

40. **TYPO คือฆาตกรเงียบ!**
    - ชื่อตัวแปรที่คล้ายกัน (`li_` vs `llm_`) อันตรายมาก
    - IDE ช่วยได้ถ้าเปิด strict type checking / undefined variable warning

41. **Try-Except ปิดบัง NameError!**
    - Catch `Exception` กว้างเกินไป → silent failure
    - ควร catch เฉพาะ exception ที่คาดหวัง (e.g., `json.JSONDecodeError`)

42. **ถ้า Local Tests ผ่านแต่ Production พัง:**
    - ตรวจสอบตัวแปรที่ใช้ใน if/else blocks
    - ดูว่ามี typo หรือ undefined variable หรือไม่
    - ใช้ IDE/Linter ที่จับ undefined variables (pylint, mypy)

43. **Naming Convention สำคัญ:**
    - อย่าใช้ prefix ที่คล้ายกัน (`li_`, `ll_`, `llm_`)
    - ใช้ชื่อที่ชัดเจนและแตกต่างกันชัด

### Quick Debug Command:

```bash
# หา undefined variable ด้วย pylint
pylint --disable=all --enable=E0602 app/service.py  # E0602 = undefined-variable
```

---

*เพิ่มเติมเมื่อ: 2026-01-06 00:08*
*ค้นพบโดย: Enigma (The Anomaly Hunter)*
*สรุป: Typo "li_" vs "llm_" ใน try-except block = Silent Failure ทำให้ VD ผิดทุก request!*

---

## 🔴 ความผิดพลาดที่ 33: VD KEY MISMATCH - wire_sizing keyed by load.id, lookup by circuit_id

> **วันที่:** 2026-01-07
> **ความรุนแรง:** 💀 CRITICAL - VD แสดง 2.0% ตลอด (ค่า default)

### อาการ:

- VD คำนวณถูกต้องใน `pipeline.py`
- แต่หน้าเว็บแสดง 2.0% ทุกวงจร (fallback default)

### สาเหตุ:

**Key Mismatch ระหว่าง Data Structures!**

```python
# pipeline.py สร้าง wire_sizing:
wire_sizing["load_1"] = {..., "voltage_drop_percent": 1.23}  # keyed by LOAD ID
wire_sizing["load_2"] = {..., "voltage_drop_percent": 2.45}

# compute.py พยายาม lookup:
vd = wire_sizing.get("ckt_1")  # ❌ ใช้ CIRCUIT ID → ไม่เจอ!
vd = 2.0  # fallback default
```

### วิธีแก้:

1. **สร้าง injection layer ใน `service.py`:**
   ```python
   def _inject_vd_to_circuits():
       for ckt in grouped_circuits:
           for load in ckt['loads']:
               if load['id'] in wire_sizing:
                   ckt['voltage_drop_percent'] = wire_sizing[load['id']]['voltage_drop_percent']
   ```

2. **แก้ `compute.py` ให้อ่านจาก circuit โดยตรง:**
   ```python
   vd = circuit.get('voltage_drop_percent', 2.0)  # อ่านจาก injected value
   ```

### 💀 บทเรียน:

44. **ตรวจสอบ KEY ของ Dict ให้ตรงกัน!**
    - `load.id` ≠ `circuit_id`
    - ต้อง map ให้ถูกก่อน lookup

45. **ถ้าค่าเป็น default ตลอด = Key lookup ผิด**
    - เช็ค `.get()` ว่าใช้ key อะไร
    - เช็คว่า source dict มี key นั้นจริงไหม

---

## 🔴 ความผิดพลาดที่ 34: SUPABASE SCHEMA MISMATCH - Backend ส่ง column ที่ไม่มี

> **วันที่:** 2026-01-07
> **ความรุนแรง:** 💀 CRITICAL - Session ไม่ถูก persist

### อาการ:

- กดสร้าง Project ใหม่ → "สำเร็จ" แต่จริงๆ ไม่ได้ save
- Refresh หน้า → ข้อมูลหาย

### สาเหตุ:

**Backend Code ส่ง `project_name` แต่ Supabase ไม่มี column!**

```
Cloud Log:
❌ Failed to create session: 
   {'message': "Could not find the 'project_name' column", 'code': 'PGRST204'}
```

Backend fallback ไป in-memory → ข้อมูลหายเมื่อ Cloud Run restart

### วิธีแก้:

```sql
ALTER TABLE mozart.sessions 
ADD COLUMN IF NOT EXISTS project_name TEXT DEFAULT 'บ้านนายสมหญิง';
```

### 💀 บทเรียน:

46. **Schema ใน DB ต้องตรงกับ Code!**
    - เพิ่ม field ใน code → ต้องเพิ่ม column ใน DB ด้วย

47. **Supabase ≠ MongoDB (ไม่ auto-create column)**
    - PostgreSQL ต้อง ALTER TABLE เอง

48. **ถ้า Cloud Log มี PGRST204 = Column Missing**
    - ตรวจ DB schema ก่อน
    - ไม่ใช่ปัญหา code logic

---

## 🔴 ความผิดพลาดที่ 35: AUDIT WARNING นับผิด - Loop ผ่าน load.id แต่แสดงจำนวน circuits

> **วันที่:** 2026-01-07
> **ความรุนแรง:** ⚠️ MEDIUM - ข้อความสับสน

### อาการ:

- แสดง "36 วงจร ใช้ระยะ Default" แต่จริงมี 10 วงจร
- ชื่อวงจรตัด "INDUCTION-3000W in ห" (ตัดที่ 20 chars)

### สาเหตุ:

1. **นับ load.id (36 ตัว) แทน circuit_id (10 ตัว)**
2. **Hardcoded truncation `[:20]`**

### วิธีแก้:

```python
# สร้าง lookup: load_id → circuit_name
load_to_circuit = {}
for ckt in grouped_circuits:
    for load in ckt['loads']:
        load_to_circuit[load['id']] = ckt['circuit_name']

# นับ unique circuits
default_circuits = set()
for load_id, w in wire_sizing.items():
    if w.get('distance_source') == 'default_table':
        default_circuits.add(load_to_circuit.get(load_id))
```

### 💀 บทเรียน:

49. **นับ unique ต้องใช้ `set()` ไม่ใช่ `list.append()`**

50. **Truncation ต้อง configurable หรือไม่มีเลย**
    - `[:20]` ใน Thai text = ตัดกลางคำ!

---

## 🚨 กฎเหล็กใหม่ (เพิ่ม 2026-01-07)

44. **Dict Key ต้องตรงกัน:** `load.id` ≠ `circuit_id` - verify ก่อน lookup
45. **ค่า default ตลอด = Key mismatch** - เช็ค `.get()` key
46. **Supabase Schema = Manual Update** - ALTER TABLE เมื่อเพิ่ม field
47. **PGRST204 = Column Missing** - ไม่ใช่ code bug
48. **Cloud Run In-Memory = ข้อมูลหาย** - ต้อง persist DB
49. **นับ unique = ใช้ set()** - ไม่ใช่ list
50. **Thai text truncation = อันตราย** - ตัดกลางคำ

---

*เพิ่มเติมเมื่อ: 2026-01-07 00:02*
*สรุป: VD key mismatch + Supabase schema missing + Audit count bug - 3 ปัญหาที่เกี่ยวข้องกับ data structure mismatch!*

---

## 🔴 ความผิดพลาดที่ 29 (Session War): ห้ามข้าม Architecture Review (Gateway Trap)

> **วันที่เกิด:** 2026-01-10
> **บทเรียนราคาแพง:** เสียเวลาแก้ Session Persistence นานมาก เพราะลืม Gateway

**อาการ:**
- Frontend ส่ง Header/Params ถูกต้อง
- Backend (Service) ไม่ได้รับค่า หรือได้รับเป็น None
- Debug Frontend อยู่นานว่าทำไมส่งไม่ไป
- **ลืมว่ามีตัวกลาง (Gateway) ขวางอยู่!**

**สาเหตุ:**
- ระบบเรามี **API Gateway** คั่นกลางระหว่าง Frontend และ Backend
- Gateway ไม่ได้ถูก config ให้ **Forward** headers หรือ models ที่เปลี่ยนไป
- ทีม Dev มัวแต่แก้ endpoint ปลายทาง (Service) กับต้นทาง (Frontend) โดยข้ามการดู Architecture Diagram

**วิธีแก้:**
- ต้องอัปเดต Gateway ให้ Forward Parameters/Headers ใหม่เสมอ
- เพิ่ม Route/Model ใน Gateway ให้ตรงกับ Backend

**🚨 กฎเหล็กใหม่:**
51. **ห้ามข้าม step การดู Architecture Diagram เด็ดขาด**
52. **ถ้ามี Gateway → ทุกการแก้ API Backend ต้องแก้ Gateway ด้วยเสมอ**
53. **Frontend ถูก → Backend ผิด = เช็ค Gateway 100%**

---

## 🔴 ความผิดพลาดที่ 29: CRUD EDIT ไม่ทำงาน - ลืม Write-through Pattern

> **วันที่เกิด:** 2026-01-13
> **ผู้ทำผิด:** AI (ไม่ได้เพิ่ม update_design หลัง CREATE)

**อาการ:**
- User พิมพ์ "เพิ่มแอร์" หลัง CREATE → ระบบสร้าง design ใหม่ทั้งหมด
- EDIT mode ไม่ merge กับ design เก่า
- Cloud Log: `[EDIT_INTENT] session has no existing design → Falling back to CREATE mode`

**สาเหตุ:**
- หลัง CREATE: `routes.py` เรียก `set_mcp_response()` (save ผลคำนวณ) ✅
- **แต่ไม่ได้เรียก `update_design(loads=...)` (save loads)** ❌
- ทำให้ `session.loads = []` → EDIT mode เห็นว่าไม่มี design → fallback CREATE

**วิธีแก้:**
```python
# หลัง set_mcp_response() เพิ่ม:
display_data = metadata.get("display_data", {})
if circuits := display_data.get("circuits"):
    loads = [{"device": c["circuit_name"], "room_name": c.get("room", "")} for c in circuits]
    await session_injector.update_design(session_id, loads=loads)
    logger.info(f"✅ [AUTO-SAVE-DESIGN] Saved {len(loads)} loads")
```

**🚨 กฎเหล็กใหม่:**
54. **Write-through Pattern: หลังคำนวณต้อง SAVE ทั้ง result และ source data**
55. **ถ้า EDIT fallback → ตรวจว่า CREATE save ข้อมูลครบหรือไม่**
56. **Cloud Log `[AUTO-SAVE-DESIGN]` ต้องเห็นหลังทุก CREATE**

---

*เพิ่มเติมเมื่อ: 2026-01-13 03:50*

