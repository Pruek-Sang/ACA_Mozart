# **1\. ภาพรวมโปรเจกต์: เรากำลังสร้างอะไรเจ้าค่ะนายท่าน**

## **1.1 วิสัยทัศน์ระบบโดยรวมเจ้าค่ะนายท่าน**

เรากำลังสร้างระบบชื่อ **ACA\_Mozart \+ Amadeus** ที่เป้าหมายคือให้ผู้ใช้ “พิมพ์ภาษาคนธรรมดา” เพื่อขอให้ออกแบบระบบไฟฟ้าอาคาร แล้วระบบจะสร้างผลลัพธ์วิศวกรรมเต็มรูปแบบให้โดยอัตโนมัติเจ้าค่ะนายท่าน

ผลลัพธ์ในฝั่งสุดท้ายจะเป็นของประมาณนี้เจ้าค่ะนายท่าน

* แบบไฟฟ้า (DXF/DWG overlay) สำหรับ CAD เจ้าค่ะนายท่าน

* สเปกอุปกรณ์ (สาย, เบรกเกอร์, ท่อ, ฯลฯ) ที่สอดคล้องมาตรฐานไทย/สากลเจ้าค่ะนายท่าน

* รายงานคำนวณ / BOQ / Check compliance ตาม standard profile ที่เลือกเจ้าค่ะนายท่าน

โปรเจกต์ถูกแบ่งเป็น 3 ตัวหลักเจ้าค่ะนายท่าน

1. **Gateway**

   * เป็น “จุดที่ user คุยจริง” ผ่าน API หรือ UI เจ้าค่ะนายท่าน

   * แปลคำพูดของ user → ตัดสินใจว่าจะเรียก RAG / MCP / AGI ตัวไหนต่อไปเจ้าค่ะนายท่าน

2. **ACA\_Mozart-copilot (RAG Service ใหม่)**

   * เป็น “Spec Engine” ไม่ใช่เครื่องคำนวณไฟฟ้าเจ้าค่ะนายท่าน

   * รับภาษาคน/Requirement ที่ถูกจัดโครงแล้ว → แปลงเป็น JSON Spec ที่ MCP เข้าใจได้ “แบบ strict ตาม schema” เจ้าค่ะนายท่าน

3. **ACA\_Mozart (MCP Core / Amadeus ฝั่งวิศวกรรม)**

   * เป็น “Engineering Heart” ที่คำนวณไฟฟ้าจริง using pandapower และโมดูลไทยเจ้าค่ะนายท่าน

   * รับ Spec จาก RAG → คำนวณ, optimize, ตรวจมาตรฐาน → คืนผลลัพธ์ไฟล์วิศวกรรมเจ้าค่ะนายท่าน

ดังนั้นฟังก์ชันใหญ่ของระบบคือเจ้าค่ะนายท่าน

**NLP → Spec → Power System Design** เจ้าค่ะนายท่าน

---

# **2\. ตัวละครหลักและบทบาทในระบบเจ้าค่ะนายท่าน**

## **2.1 Gateway (ไฟล์ตระกูล `gate_way_new.py`) เจ้าค่ะนายท่าน**

**บทบาท**เจ้าค่ะนายท่าน

* เป็น “คนหน้าเคาน์เตอร์” ที่ user เห็นหน้าเจ้าค่ะนายท่าน

* รับข้อความจาก user (รวมถึงปุ่ม/โหมดจาก UI ถ้ามี) แล้วตัดสินใจว่าควรส่งไปที่ service ไหนต่อเจ้าค่ะนายท่าน

**หน้าที่หลัก**เจ้าค่ะนายท่าน

1. **Intent Routing**

   * ใช้ LLM หรือ rule เพื่อตัดสินว่า user กำลังทำอะไร เช่นเจ้าค่ะนายท่าน

     1. ถามความรู้ (Q\&A) → ส่งไป RAG `/api/v1/ask` เจ้าค่ะนายท่าน

     2. ขอออกแบบระบบ → เข้ากระบวนการเก็บ requirement แล้วเรียก `/api/v1/mcp_spec` เจ้าค่ะนายท่าน

     3. ขอให้ AGI วิเคราะห์ซับซ้อน → ส่งไป Amadeus/AGI โดยตรงเจ้าค่ะนายท่าน

2. **Dialogue / Slot-Filling (ฝั่ง design)**

   * ถ้า user ยังให้ข้อมูลไม่ครบ (`ProjectRequirements` ยังไม่พร้อม) Gateway ต้องถามเก็บ slot เพิ่ม เช่นเจ้าค่ะนายท่าน

     1. ประเภทอาคาร, จำนวนชั้น, พื้นที่ห้อง, โหลดหลัก, มาตรฐานที่ต้องการ ฯลฯ เจ้าค่ะนายท่าน

   * เมื่อข้อมูลครบ → สร้าง `ProjectRequirements` → ส่งให้ RAG เจ้าค่ะนายท่าน

3. **การเรียกต่อไปฝั่ง MCP**

   * เมื่อ RAG ส่ง `McpSpecResponse` กลับมา → Gateway ทำ 2 อย่างเจ้าค่ะนายท่าน

     1. เก็บ log / แสดง preview ให้ user เห็น Spec ที่จะใช้จริงเจ้าค่ะนายท่าน

     2. แปลง Spec → Request ของ MCP (`GenerateOverlayRequest`) แล้วยิงไปยัง ACA\_Mozart MCP server (`POST /generate/overlay`) เจ้าค่ะนายท่าน

**จุดสำคัญ**เจ้าค่ะนายท่าน

* ลูกเล่นใหม่ ๆ เช่น โหมดสลับ Mozart/Amadeus, ปุ่ม “ขอคำนวณใหม่”, ปุ่ม “แสดง BOQ” จะอยู่ที่ Gateway \+ UI ไม่ใช่ใน RAG Service เจ้าค่ะนายท่าน

---

## **2.2 ACA\_Mozart-copilot (RAG Service ใหม่ / ฝั่ง worknow) เจ้าค่ะนายท่าน**

โค้ดหลักอยู่ในโฟลเดอร์ `app/` และ `core/` ในโปรเจกต์ ACA\_Mozart-copilot\[RAG\] ตามที่สรุปใน `Work now.md` เจ้าค่ะนายท่าน

**บทบาท**เจ้าค่ะนายท่าน

1. เป็น **RAG QA Engine** สำหรับคำถามเกี่ยวกับมาตรฐาน, DB spec, ความรู้ไฟฟ้าบ้าน ฯลฯ ผ่าน `/api/v1/ask` เจ้าค่ะนายท่าน

2. เป็น **Spec Engine** ที่รับ `ProjectRequirements` → คืน `McpSpecResponse` ซึ่งเป็น JSON ที่ MCP Core สามารถเชื่อถือได้ (ผ่าน strict schema \+ validate \+ retry \+ trust log) ผ่าน `/api/v1/mcp_spec` เจ้าค่ะนายท่าน

**ไฟล์/เลเยอร์สำคัญ**เจ้าค่ะนายท่าน

* `app/config.py`

  * เก็บ config หลัก (LLM model, path knowledge, VectorDB, trust log ฯลฯ) ผ่าน `BaseSettings` เจ้าค่ะนายท่าน

* `app/models.py`

  * นิยาม **ทุก data contract** ที่ใช้ใน RAG service เช่นเจ้าค่ะนายท่าน

    * `QueryRequest`, `StandardResponse`

    * `ProjectRequirements`

    * `ProjectInputSpec`, `RoomSpec`, `LoadSpec`, `ConstraintsSpec`

    * `McpSpecResponse` (ฝั่ง RAG)

    * `McpSpecTrustRecord` สำหรับ log เจ้าค่ะนายท่าน

* `app/knowledge_service.py`

  * เป็นชั้น knowledge ที่อ่าน `rag_knowledge/knowledge_index.json` แล้วรู้ว่า doc ใดอยู่ group อะไร (เช่น `mcp_spec`, `catalog_schema`, `thai_standard`, `example_project`) เจ้าค่ะนายท่าน

* `core/database.py`

  * Interface ของ VectorDB (ตอนนี้ยัง mock) ที่ต้องต่อกับ Qdrant จริงในอนาคตเจ้าค่ะนายท่าน

* `core/ingest.py`

  * Pipeline สำหรับโหลดเอกสารจากไฟล์ → chunk → embed → ใส่ VectorDB เจ้าค่ะนายท่าน

* `core/privacy.py` **(ต้องสร้างจาก logic เก่าใน rag\_real)**

  * `PrivacyGuard` ล้าง PII และตรวจ grounding โดยใช้ LLM judge เจ้าค่ะนายท่าน

* `app/service.py`

  * `RagService` คือหัวใจตรรกะทุกอย่าง ทั้ง `/ask` และ `/mcp_spec` เจ้าค่ะนายท่าน

* `app/routes.py`

  * FastAPI app ที่ประกาศ endpoint API จริง: `/api/v1/ask`, `/api/v1/mcp_spec`, `/retrieve_raw`, `/ingest`, `/delete`, `/mcp/manifest`, admin routes เจ้าค่ะนายท่าน

* `app/trust_log.py`

  * เขียน log สำหรับทุก call `/mcp_spec` ลง JSONL เพื่อให้ trace/ตรวจสอบย้อนหลังได้เจ้าค่ะนายท่าน

**RAG ไม่ทำอะไร**เจ้าค่ะนายท่าน

* ไม่คำนวณโหลด, drop, short circuit, ฯลฯ เจ้าค่ะนายท่าน

* ไม่ยิง Supabase `amadeus.catalog` โดยตรง RAG จะรู้ DB แค่ผ่านเอกสารใน `rag_knowledge/db/*.md` เท่านั้นเจ้าค่ะนายท่าน

* ไม่วาด DXF เจ้าค่ะนายท่าน

RAG เป็นแค่ “สมองแปล requirement → Spec JSON” และ “สมองอ่านเอกสารตอบคำถาม” เท่านั้นเจ้าค่ะนายท่าน

---

## **2.3 ACA\_Mozart / Amadeus MCP Core เจ้าค่ะนายท่าน**

ฝั่งนี้ถือว่า “เสร็จแล้ว” ในมุมโปรเจกต์ปัจจุบัน แต่เพื่อให้ AI ตัวอื่นเข้าใจโครง ขอสรุปสั้น ๆ เจ้าค่ะนายท่าน

* MCP Core เป็น FastAPI server แยกต่างหาก (เช่น `amadeus_mcp_servernew_(the_engineering_heart_new).py`) เจ้าค่ะนายท่าน

* มี endpoint หลัก เช่นเจ้าค่ะนายท่าน

  * `POST /generate/overlay` รับ JSON spec → สร้าง electrical overlay \+ report เจ้าค่ะนายท่าน

* ใช้ pandapower \+ โมดูลอื่น (wire\_sizer, load\_calculator, cost\_estimator ฯลฯ) เพื่อคำนวณทั้งหมดตามมาตรฐานเจ้าค่ะนายท่าน

ฝั่งนี้มองจาก RAG คือ “กล่องดำ” ที่มี API ชัดเจนเท่านี้เจ้าค่ะนายท่าน

---

# **3\. เป้าหมายสุดท้ายของระบบ: หน้าตาทั้งหมดต้องเป็นยังไงเจ้าค่ะนายท่าน**

## **3.1 เป้าหมายระดับ Functional เจ้าค่ะนายท่าน**

1. ผู้ใช้สามารถ “คุยแบบคน” ผ่าน Gateway เพื่อทำงาน 2 แบบหลักเจ้าค่ะนายท่าน

   1. ถามความรู้ไฟฟ้า/มาตรฐาน/DB → ได้คำตอบพร้อมอ้างอิงเอกสารเจ้าค่ะนายท่าน

   2. ขอออกแบบระบบไฟฟ้าบ้าน/อาคาร → ได้ Spec, แบบ, รายงานครบเจ้าค่ะนายท่าน

2. เส้นทางออกแบบต้องมีหน้าตาแบบนี้เจ้าค่ะนายท่าน

   1. User พิมพ์:

       “ออกแบบระบบไฟสำหรับบ้าน 2 ชั้น 3 ห้องนอน ใช้มาตรฐานไทย” เจ้าค่ะนายท่าน

   2. Gateway ตรวจ intent → สลับไปโหมด “Design” → ถ้าข้อมูลไม่ครบ จะถามเพิ่ม เช่นพื้นที่, โหลดหลัก, เงื่อนไขพิเศษเจ้าค่ะนายท่าน

   3. เมื่อได้ข้อมูลครบ → สร้าง `ProjectRequirements` → ส่งไป RAG `/api/v1/mcp_spec` เจ้าค่ะนายท่าน

   4. RAG ใช้ knowledge \+ VectorDB \+ example → สร้าง `McpSpecResponse` ที่ parse ผ่าน schema แน่นอนเจ้าค่ะนายท่าน

   5. RAG เขียน trust log 1 record พร้อม raw LLM output, validation, context ฯลฯ เจ้าค่ะนายท่าน

   6. Gateway แปลง `McpSpecResponse.project_input` → `GenerateOverlayRequest` แล้วยิงไป MCP `/generate/overlay` เจ้าค่ะนายท่าน

   7. MCP คำนวณ → คืน

      * รายการสาย, เบรกเกอร์, ท่อ ฯลฯ

      * ขนาด, ระบบป้องกัน

      * DXF overlay / รายงานเจ้าค่ะนายท่าน

   8. Gateway แพ็กผลตอบให้ user ในรูปแบบที่อ่านง่าย (เช่น สรุปสั้นบนแชท \+ ลิงก์ดาวน์โหลดไฟล์) เจ้าค่ะนายท่าน

## **3.2 เป้าหมายระดับ Non-Functional เจ้าค่ะนายท่าน**

1. **Deterministic / Traceable**

   * ทุกครั้งที่ RAG สร้าง Spec ต้องมี trust log ครบเจ้าค่ะนายท่าน

   * ทุกการเรียก LLM มี trace (เช่น LangSmith) สำหรับ debug เจ้าค่ะนายท่าน

2. **Grounded / Compliant**

   * คำตอบจาก `/ask` ต้องมาจาก knowledge ที่กำหนด (ไม่ได้มั่วจากโมเดลเปล่า ๆ) เจ้าค่ะนายท่าน

   * Spec ที่ออกไป MCP ต้องอ้างอิง profile มาตรฐานที่ชัดเจน (เช่น THAI\_RESIDENTIAL\_LV) เจ้าค่ะนายท่าน

3. **Security / Privacy**

   * ข้อมูล PII ถูกลบ/แทนก่อนส่งเข้า LLM ผ่าน `PrivacyGuard` เจ้าค่ะนายท่าน

   * API มี Auth, rate limit, ไม่ให้ใครมาปั่นจนเซิร์ฟล้มง่าย ๆ เจ้าค่ะนายท่าน

4. **Modular / Maintainable**

   * เปลี่ยน VectorDB จาก mock → Qdrant หรือย้ายไปที่อื่นได้ โดยไม่ต้องแก้ logic หลักเพราะห่อผ่าน `VectorDatabase` แล้วเจ้าค่ะนายท่าน

   * เปลี่ยน MCP backend (เพิ่ม endpoint ใหม่) แค่ปรับ translator ระหว่าง `McpSpecResponse` ↔ MCP request ไม่ต้องแก้ทุกที่เจ้าค่ะนายท่าน

---

# **4\. สถานะปัจจุบัน (ฝั่ง worknow) และสิ่งที่ต้องทำต่อเจ้าค่ะนายท่าน**

## **4.1 สิ่งที่ “มีแล้ว” และใช้เป็นฐานต่อได้ทันทีเจ้าค่ะนายท่าน**

1. **สถาปัตยกรรม RAG ใหม่ (ACA\_Mozart-copilot)**

   * แยกเลเยอร์ตาม canonical funnel ครบ: config, models, service, routes, knowledge, trust\_log, db, ingestเจ้าค่ะนายท่าน

2. **Data Contract หลักใน `models.py`**

   * `QueryRequest`, `StandardResponse`, `ProjectRequirements`, `McpSpecResponse` ถูกออกแบบไว้ตาม requirement ใหม่แล้วเจ้าค่ะนายท่าน

3. **RagService ใน `service.py`**

   * `/ask`: มี flow anonymize → search (แม้ยัง mock) → build prompt → call LLM → grounding → คืน StandardResponseเจ้าค่ะนายท่าน

   * `/mcp_spec`: มี flow validate → load knowledge docs → build prompt \+ few-shot → call LLM → parse JSON → retry self-correction → log trust recordเจ้าค่ะนายท่าน

4. **Knowledge Layer**

   * มีโครง `rag_knowledge/` \+ `knowledge_index.json` แบ่ง group (mcp\_spec, catalog\_schema, thai\_standard, example\_project) แล้วเจ้าค่ะนายท่าน

5. **Trust Log**

   * `trust_log.py` เขียน JSONL per day พร้อมโครง `McpSpecTrustRecord` เพื่อเก็บทุก call `/mcp_spec`เจ้าค่ะนายท่าน

---

## **4.2 สิ่งที่ยังเป็น Dummy / Prototype และต้องอัปเกรดให้เป็นของจริงเจ้าค่ะนายท่าน**

1. **VectorDatabase (core/database.py)**

   * ตอนนี้เป็น mock: search/upsert/delete return เปล่า ๆเจ้าค่ะนายท่าน

   * เป้าหมายสุดท้าย:

     * ใช้ Qdrant เป็น VectorDB จริง

     * ทุก doc ที่มาจาก `rag_knowledge` ต้องถูก embed \+ upsert พร้อม metadata (doc\_id, group, source\_path)เจ้าค่ะนายท่าน

2. **IngestionEngine (core/ingest.py)**

   * ตอนนี้แค่ log แล้ว return \[\]เจ้าค่ะนายท่าน

   * ต้องอัปเป็น pipeline ที่อ่านไฟล์ .md/.txt → chunk → embed → upsert ผ่าน VectorDatabaseเจ้าค่ะนายท่าน

3. **PrivacyGuard (core/privacy.py)**

   * ยังไม่มีไฟล์ในสถาปัตยกรรมใหม่ แต่ logic เต็มอยู่ใน `rag_real.py` รุ่นเก่าเจ้าค่ะนายท่าน

   * ต้องย้ายมาสร้าง `core/privacy.py` ให้ RAG ใช้จริงทั้ง anonymize \+ grounding judgeเจ้าค่ะนายท่าน

4. **Gateway (gate\_way\_new.py)**

   * ตอนนี้เป็น prototype มี comment/… แทนโค้ดบางส่วนเจ้าค่ะนายท่าน

   * ต้องทำให้ครบ:

     * รับ `GatewayRequest` จาก UI

     * ตัดสิน intent

     * จัดการ dialogue/slot

     * เรียก RAG `/ask` หรือ `/mcp_spec`

     * แปลง Spec → MCP `/generate/overlay`

     * แพ็ก `GatewayResponse` กลับไป UIเจ้าค่ะนายท่าน

5. **Mapping RAG Spec → MCP Request**

   * ยังไม่มีไฟล์เฉพาะที่แปลง `McpSpecResponse.project_input` → `GenerateOverlayRequest`เจ้าค่ะนายท่าน

   * ต้องสร้าง module แปลง schema ให้ตรงกัน (เช่น mapping ห้อง/โหลด/เงื่อนไข → bus/line/load/pandapower model input)เจ้าค่ะนายท่าน

6. **Security \+ LangSmith Trace**

   * ยังไม่มีใน RAG service ชุดนี้เลยเจ้าค่ะนายท่าน

   * ต้องเพิ่ม layer สำหรับ

     * auth/rate limit (อาจอยู่ที่ Gateway \+ reverse proxy)

     * trace รอบ call LLM / call MCP เพื่อติดตามปัญหาได้จริงเจ้าค่ะนายท่าน

---

# **5\. แผนการทำงานต่อ (สำหรับ AI ตัวอื่นที่จะมาทำต่อ) เจ้าค่ะนายท่าน**

เมดสรุปลำดับงานสำหรับ AI/Dev ที่จะเข้ามาทำต่อจากไฟล์นี้ให้เลยเจ้าค่ะนายท่าน

## **Phase 1 – ทำให้ RAG Spec Engine สมบูรณ์และรันได้จริงเจ้าค่ะนายท่าน**

1. **สร้าง `core/privacy.py` จาก rag\_real.py**

   * ย้าย `PrivacyGuard` มา

   * ผูกกับ `settings.MODEL_NAME_JUDGE`

   * ทำให้ `RagService` เรียกใช้ได้จริงใน `/ask` และ `/mcp_spec`เจ้าค่ะนายท่าน

2. **ผูก VectorDB ของจริง (Qdrant) ใส่ใน `VectorDatabase`**

   * Implement `search`, `upsert`, `delete_source`

   * รองรับ filter ตาม doc\_id/group จาก `knowledge_service`เจ้าค่ะนายท่าน

3. **อัปเกรด `IngestionEngine` ให้ ingest knowledge ได้จริง**

   * อ่าน `rag_knowledge/*`

   * chunk content \+ set metadata (doc\_id, group, source\_path)

   * เรียก `VectorDatabase.upsert()`เจ้าค่ะนายท่าน

4. **เขียน test สำหรับ `/mcp_spec`**

   * เคสบ้าน 1 ชั้น / 2 ชั้น / ข้อมูลไม่ครบ

   * ตรวจว่า `McpSpecResponse` parse ผ่าน, trust log ถูกสร้าง, error ตอนข้อมูลไม่ครบใช้ HTTP code ที่ถูกต้องเจ้าค่ะนายท่าน

## **Phase 2 – ทำ Gateway ให้ทำงาน end-to-endเจ้าค่ะนายท่าน**

1. เติมโค้ดใน `gate_way_new.py` ให้ครบตาม design ต่อไปนี้เจ้าค่ะนายท่าน

   * input: `GatewayRequest` (ข้อความ, mode, context)เจ้าค่ะนายท่าน

   * flow:

     * ถ้า mode \= ASK → call RAG `/api/v1/ask` → format answer ให้ userเจ้าค่ะนายท่าน

     * ถ้า mode \= DESIGN →

       * ถ้า slot ยังไม่ครบ → ส่งคำถามต่อให้ userเจ้าค่ะนายท่าน

       * ถ้าครบแล้ว → สร้าง `ProjectRequirements` → call `/api/v1/mcp_spec`เจ้าค่ะนายท่าน

       * ได้ Spec แล้ว → แปลง → call MCP `/generate/overlay` → คืนผลเจ้าค่ะนายท่าน

2. สร้าง module translator ระหว่าง `McpSpecResponse` ↔ MCP Request

   * ตีความ `project_input` ให้กลายเป็น structure ที่ MCP ต้องการเจ้าค่ะนายท่าน

3. เขียน integration test:

   * Fake user requirement → Gateway → RAG → MCP (mock) → ตรวจว่า flow ครบ ไม่หลุด logicเจ้าค่ะนายท่าน

## **Phase 3 – เสริมความปลอดภัยและ observabilityเจ้าค่ะนายท่าน**

1. เพิ่ม Auth / API key / rate limit ใน Gateway และ/หรือ FastAPI layerเจ้าค่ะนายท่าน

2. ติด LangSmith trace รอบ

   * ทุก call LLM ใน `RagService`

   * ทุก call MCP จาก Gatewayเจ้าค่ะนายท่าน

3. เพิ่ม log / alert เมื่อ spec ถูก generate แล้ว parse fail บ่อยผิดปกติ เพื่อให้ปรับ prompt / knowledge ได้เจ้าค่ะนายท่าน

---

# **6\. ข้อสรุปสุดท้ายสำหรับ AI ที่จะรับงานต่อเจ้าค่ะนายท่าน**

* โปรเจกต์นี้ **ไม่ได้ต้องการ LLM ที่คิดทุกอย่างเอง** แต่ต้องการ **สถาปัตยกรรมที่ใช้ LLM เป็น “Spec Engine”** เพื่อ feed กลไก MCP ที่ deterministic และอ้างอิงมาตรฐานเจ้าค่ะนายท่าน

* ฝั่ง ACA\_Mozart-copilot (RAG ใหม่) ตอนนี้เป็นฐานโค้ดที่ “โครงถูก เย็บเลเยอร์ถูก แต่ VectorDB/Privacy/Gateway/Mapping ยังไม่ประกอบเต็ม”เจ้าค่ะนายท่าน

* เป้าหมายสูงสุดคือ เมื่อ user พิมพ์ว่า

   “ช่วยออกแบบระบบไฟฟ้าบ้าน 2 ชั้นตามมาตรฐานไทย ใช้แอร์ 3 ตัว น้ำอุ่น 2 จุด”เจ้าค่ะนายท่าน  
   ระบบจะเดิน pipeline นี้แบบมีวินัยเจ้าค่ะนายท่าน

  1. Gateway เก็บ requirement ครบเจ้าค่ะนายท่าน

  2. RAG `/mcp_spec` สร้าง Spec JSON ที่ผ่าน schema \+ log ลง trust logเจ้าค่ะนายท่าน

  3. Gateway call MCP `/generate/overlay` ด้วย Spec นั้นเจ้าค่ะนายท่าน

  4. MCP สร้างแบบและรายงานตามมาตรฐานเจ้าค่ะนายท่าน

  5. ทุกขั้นมี trace, log, และสามารถ audit/ปรับปรุงได้เจ้าค่ะนายท่าน

ถ้า AI ตัวไหนอ่านไฟล์นี้จบแล้ว ยังงงว่าต้องทำอะไรต่อ แปลว่ามันงงเองไม่ใช่สถาปัตยกรรมงงเจ้าค่ะนายท่าน

# **0\. Mission & Scope ของระบบนี้เจ้าค่ะนายท่าน**

**ชื่อบริการ:** ACA\_Mozart-copilot\[RAG\] เจ้าค่ะนายท่าน

**บทบาทหลักของ RAG ในระบบใหญ่:**

1. เป็น **Spec Engine** ที่แปลง  
    `ProjectRequirements (ภาษาคน)` → `ProjectInputSpec (โครงสร้าง spec ตามสัญญากับ MCP)` → ห่อใน `McpSpecResponse` เพื่อส่งต่อให้ MCP Core v2.0 ทำงานต่อเจ้าค่ะนายท่าน

2. เป็น **Knowledge QA Engine** สำหรับคำถามด้านมาตรฐาน, DB contract, design contract ฯลฯ ผ่าน `/api/v1/ask` โดยอ้างอิงเฉพาะเอกสารใน `rag_knowledge/` ที่ประกาศไว้ใน `knowledge_index.json` เท่านั้นเจ้าค่ะนายท่าน

3. **สิ่งที่ RAG “ไม่ทำ” อย่างชัดเจน** เจ้าค่ะนายท่าน

   * ไม่คำนวณโหลดไฟฟ้าจริงเจ้าค่ะนายท่าน

   * ไม่ยิง `amadeus.catalog` โดยตรงเจ้าค่ะนายท่าน

   * ไม่แต่งตัวเลขสายไฟ/เบรกเกอร์/โหลดเองนอกจากสิ่งที่เรียนรู้จากเอกสารและ spec เจ้าค่ะนายท่าน

---

# **1\. โครง repo / โครงเลเยอร์เจ้าค่ะนายท่าน**

โฟลเดอร์หลักของระบบอยู่ที่เจ้าค่ะนายท่าน

`Copilot-Mozart/`  
  `ACA_Mozart-copilot[RAG]/`  
    `app/`  
    `core/`  
    `rag_knowledge/`  
    `tests/`  
    `logs/              # (runtime + trust log target)`  
    `main.py`  
    `README.md`  
    `requirements.txt`  
    `.env.example`

### **1.1 การแบ่งเลเยอร์ตาม Canonical Funnel เจ้าค่ะนายท่าน**

* **Layer 0 – Application (app/)**  
   โมเดล, service logic, routes, knowledge layer, trust log เจ้าค่ะนายท่าน

* **Layer 1 – Core Infrastructure (core/)**  
   VectorDB, ingest, privacy/PII เจ้าค่ะนายท่าน

* **Layer 2 – Knowledge (rag\_knowledge/)**  
   เอกสารโดเมนจริง \+ index กลางสำหรับ RAG เจ้าค่ะนายท่าน

* **Layer 3 – Testing (tests/)**  
   ตรวจสัญญา models \+ flow `/mcp_spec` ด้วยเคสบ้านตัวอย่างเจ้าค่ะนายท่าน

* **Layer 4 – Entry & Ops (main.py \+ README \+ .env)**  
   จุดรัน, config ผ่าน env, คู่มือรันระบบเจ้าค่ะนายท่าน

---

# **2\. ภาพรวม Flow ระหว่าง Actor เจ้าค่ะนายท่าน**

## **2.1 Flow `/api/v1/ask` (ถามความรู้) เจ้าค่ะนายท่าน**

Client เรียก `POST /api/v1/ask` ด้วย `QueryRequest` เช่นเจ้าค่ะนายท่าน

 `{`  
  `"query": "บ้านพักอาศัยไทยต้องมี RCD วงจรไหนบ้าง",`  
  `"context_hint": ["thai_standard"],`  
  `"language": "th"`  
`}`

1.   
2. `routes.py` แปลง JSON → `QueryRequest` แล้วส่งเข้า `RagService.process_ask()` เจ้าค่ะนายท่าน

3. `RagService.process_ask()` ทำงานดังนี้เจ้าค่ะนายท่าน

   * ใช้ `knowledge_service` \+ `context_hint` เพื่อเลือกเอกสารกลุ่มที่เกี่ยว เช่น `thai_standard` จาก `knowledge_index.json` เจ้าค่ะนายท่าน

   * ใช้ `core.database`/VectorDB search ใน subset ของ docs ที่เลือกมาเท่านั้นเจ้าค่ะนายท่าน

   * ประกอบ prompt ที่มี

     * เนื้อหาเอกสารที่ดึงมาเจ้าค่ะนายท่าน

     * คำสั่งภาษาตาม `language` (th/en) เจ้าค่ะนายท่าน

   * เรียก LLM (Gemini 2.0 Flash) ผ่าน config ที่ `app/config.py` เจ้าค่ะนายท่าน

   * รวบรวมผลเป็น `StandardResponse` พร้อม metadata เช่น model, retrieved\_docs, retrieval\_group เจ้าค่ะนายท่าน

4. `routes.py` คืน `StandardResponse` กลับไปให้ client ในรูป JSON เจ้าค่ะนายท่าน

## **2.2 Flow `/api/v1/mcp_spec` (ภาษาคน → ProjectInputSpec) เจ้าค่ะนายท่าน**

1. Client ส่ง `ProjectRequirements` (ภาษาคน structured) เข้า `POST /api/v1/mcp_spec` เจ้าค่ะนายท่าน

2. `routes.py` แปลง JSON → `ProjectRequirements` → ส่งให้ `RagService.generate_mcp_spec()` เจ้าค่ะนายท่าน

3. `RagService.generate_mcp_spec()` ทำงานแบบนี้เจ้าค่ะนายท่าน

   1. เรียก `knowledge_service.get_docs_for_mcp_spec()`  
       → ได้ `DocMeta` จาก group `mcp_spec`, `catalog_schema`, `thai_standard`, `example_project` เท่านั้นเจ้าค่ะนายท่าน

   2. ใช้ docs เหล่านี้สร้าง context สำหรับ LLM

      * อาจผ่าน VectorDB เพื่อเลือก chunk ที่เกี่ยวข้องเจ้าค่ะนายท่าน

      * รวมทั้ง example few-shot 3 ไฟล์ใน `rag_knowledge/example/` เจ้าค่ะนายท่าน

   3. ประกอบ prompt ที่บอก LLM ให้สร้าง JSON ตาม schema `McpSpecResponse` อย่างเคร่งครัดเจ้าค่ะนายท่าน

   4. เรียก LLM → ได้ raw JSON string เจ้าค่ะนายท่าน

   5. พยายาม parse ด้วย Pydantic → `McpSpecResponse` เจ้าค่ะนายท่าน

      * ถ้า parse fail → ใช้ self-correction prompt / retry จำนวนจำกัดเจ้าค่ะนายท่าน

      * ถ้าพังทุกครั้ง → ส่ง error ให้ client ตาม error policy (4xx หรือ 5xx) และบันทึกว่า `parse_success=false` ใน trust log เจ้าค่ะนายท่าน

   6. ถ้า parse สำเร็จ → เขียน trust log 1 record ผ่าน `trust_log.py`

      * เก็บ input, retrieved\_docs, model, raw output, parsed spec, flags ต่าง ๆ เจ้าค่ะนายท่าน

   7. คืน `McpSpecResponse` ที่ผ่าน validation แล้วให้ clientเจ้าค่ะนายท่าน

4. Gateway / ระบบต่อท้ายจะส่ง `McpSpecResponse.project_input` ให้ MCP Core v2.0 ใช้ต่อ เพื่อยิง DB จริง \+ pandapower เจ้าค่ะนายท่าน

---

# **3\. รายละเอียดทีละโฟลเดอร์ / ไฟล์เจ้าค่ะนายท่าน**

## **3.1 `app/` – สมองของ RAG เจ้าค่ะนายท่าน**

### **3.1.1 `app/config.py` – การตั้งค่าเจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* รวม config ทั้งหมดของ RAG เช่นเจ้าค่ะนายท่าน

  * ชื่อโมเดล LLM สำหรับ answer / judge → ตอนนี้ใช้ `"gemini-2.0-flash-exp"` ทั้งคู่เจ้าค่ะนายท่าน

  * path ของ `rag_knowledge/` และ `knowledge_index.json` เจ้าค่ะนายท่าน

  * config สำหรับ VectorDB (host, index ชื่ออะไร) เจ้าค่ะนายท่าน

* อ่านค่าจาก `.env` ผ่าน pydantic settings หรือคล้ายกันเจ้าค่ะนายท่าน

**ผลที่คาดหวัง**เจ้าค่ะนายท่าน

* ทุกส่วนของระบบที่ต้องใช้ค่าเหล่านี้ เรียกผ่าน `settings` จาก `config.py` เท่านั้น ห้าม hardcode ซ้ำในไฟล์อื่นเจ้าค่ะนายท่าน

---

### **3.1.2 `app/models.py` – Pydantic Models เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* เป็นสัญญากลางของ RAG ทั้งสำหรับ API และ internal schema เจ้าค่ะนายท่าน

\*\*โครงหลักที่ต้องมี (สำคัญ)\*\*เจ้าค่ะนายท่าน

`QueryRequest` เจ้าค่ะนายท่าน

 `class QueryRequest(BaseModel):`  
    `query: str`  
    `context_hint: List[str] = []`  
    `language: Literal["th", "en"] = "th"`  
    `filters: Optional[Dict[str, str]] = None`

1.   
   * ใช้กับ `/api/v1/ask` เจ้าค่ะนายท่าน

   * `context_hint` → บอก knowledge group ที่จะใช้ค้นหาเจ้าค่ะนายท่าน

   * `language` → บังคับภาษา output ของ LLM เจ้าค่ะนายท่าน

2. `SourceRef` – อ้างอิงเอกสารเจ้าค่ะนายท่าน

   * `file`, `section`, `score` ฯลฯ เพื่อใช้ใน `StandardResponse.sources` เจ้าค่ะนายท่าน

`AnswerMetadata` \+ `StandardResponse` เจ้าค่ะนายท่าน

 `class AnswerMetadata(BaseModel):`  
    `llm_model: str`  
    `retrieved_docs: List[str]`  
    `retrieval_group: Optional[str]`

`class StandardResponse(BaseModel):`  
    `answer: str`  
    `sources: List[SourceRef]`  
    `confidence: Literal["High", "Medium", "Low"]`  
    `grounding_status: str`  
    `metadata: AnswerMetadata`

3.   
4. `ProjectRequirements` – input ฝั่ง `/mcp_spec` เจ้าค่ะนายท่าน

   * มี `project_info`, `building_type`, location, rooms (ชื่อห้องภาษาคน), loads (device ภาษาคน \+ qty), `user_constraints` ฯลฯ ตามที่คุยกันเจ้าค่ะนายท่าน

5. `RoomSpec`, `LoadSpec`, `ProjectInputSpec` เจ้าค่ะนายท่าน

   * `ProjectInputSpec` คือ spec ที่ MCP จะใช้จริง มี field อย่างน้อยเจ้าค่ะนายท่าน

     * `project_info.project_name / building_type / spec_version` เจ้าค่ะนายท่าน

     * `electrical_system.voltage_system / earthing` เจ้าค่ะนายท่าน

     * `rooms[*].room_id, room_type, template_code, name` เจ้าค่ะนายท่าน

     * `loads[*].load_id, room_id, device_code, qty` เจ้าค่ะนายท่าน

     * `constraints.rule_profile_id, user_constraints[]` เจ้าค่ะนายท่าน

6. `McpSpecResponse` เจ้าค่ะนายท่าน

   * มี `project_input: ProjectInputSpec` เจ้าค่ะนายท่าน

   * `standards_profile` (เช่น rule\_profile\_id \+ notes) เจ้าค่ะนายท่าน

   * `llm_metadata` (ข้อมูล retrieval / model / prompt สั้น ๆ) เจ้าค่ะนายท่าน

**คาดหวัง**เจ้าค่ะนายท่าน

* JSON ที่ LLM สร้างต้อง parse ผ่าน `McpSpecResponse` ได้ 100% ถ้าไม่ผ่านถือว่าล้มเหลว ไม่ส่งต่อให้ MCP เจ้าค่ะนายท่าน

---

### **3.1.3 `app/knowledge_service.py` – Canonical Knowledge Layer เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* เป็นชั้นกลางระหว่างโค้ด RAG กับไฟล์ใน `rag_knowledge/`เจ้าค่ะนายท่าน

* อ่าน `knowledge_index.json` แล้วให้ฟังก์ชันสำหรับเจ้าค่ะนายท่าน

  * `list_groups()` เจ้าค่ะนายท่าน

  * `list_docs(group)` → คืน `DocMeta` ตาม group เจ้าค่ะนายท่าน

  * `load_doc(doc_id)` → โหลดเนื้อหาจริงของเอกสารเจ้าค่ะนายท่าน

  * `get_docs_for_mcp_spec()` → คืน docs เฉพาะกลุ่มที่อนุญาตให้ใช้ตอนสร้าง spec เจ้าค่ะนายท่าน

\*\*สัญญา get\_docs\_for\_mcp\_spec()\*\*เจ้าค่ะนายท่าน

* ต้องรวม group แค่ชุดนี้เท่านั้นเจ้าค่ะนายท่าน

  * `"mcp_spec"` เจ้าค่ะนายท่าน

  * `"catalog_schema"` เจ้าค่ะนายท่าน

  * `"thai_standard"` เจ้าค่ะนายท่าน

  * `"example_project"` เจ้าค่ะนายท่าน

* ห้ามมี group แปลก ๆ ปน เช่น `"debug"`, `"internal_only"` เจ้าค่ะนายท่าน

---

### **3.1.4 `app/service.py` – RagService เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* เป็น class หลักที่ implement business logic ทุก endpoint เจ้าค่ะนายท่าน

เมธอดหลักที่ต้องมีเจ้าค่ะนายท่าน

1. `process_ask(req: QueryRequest)` เจ้าค่ะนายท่าน

   * ใช้ `req.context_hint` → เลือก docs ด้วย `knowledge_service` เจ้าค่ะนายท่าน

   * ใช้ `core.database` → search ใน subset ของ docs เจ้าค่ะนายท่าน

   * ประกอบ prompt \+ language instruction เจ้าค่ะนายท่าน

   * เรียก LLM → สร้างคำตอบเจ้าค่ะนายท่าน

   * สร้าง `StandardResponse` \+ `AnswerMetadata` เจ้าค่ะนายท่าน

2. `generate_mcp_spec(req: ProjectRequirements)` เจ้าค่ะนายท่าน

   * ใช้ `knowledge_service.get_docs_for_mcp_spec()` เจ้าค่ะนายท่าน

   * ส่ง docs เข้า VectorDB / prompt เพื่ออธิบาย MCP, DB, standards, examples เจ้าค่ะนายท่าน

   * เรียก LLM ให้ตอบเป็น JSON `McpSpecResponse` เท่านั้นเจ้าค่ะนายท่าน

   * parse JSON ด้วย Pydantic, ถ้า error → retry ตาม policy หรือส่ง error เจ้าค่ะนายท่าน

   * เขียน trust log ผ่าน `trust_log.py` ทุกครั้งเจ้าค่ะนายท่าน

3. เมธอดอื่น ๆ เช่น `ingest`, `delete`, `retrieve_raw` ผูกกับ `core.database` และ `core.ingest` ตามดีไซน์เจ้าค่ะนายท่าน

---

### **3.1.5 `app/trust_log.py` – Trust & Audit Layer เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* บันทึกทุกครั้งที่เรียก `/mcp_spec` เป็น JSONL record เจ้าค่ะนายท่าน

**โครง record พื้นฐาน**เจ้าค่ะนายท่าน

* `timestamp` เจ้าค่ะนายท่าน

* `request_id` เจ้าค่ะนายท่าน

* `user_id` (ถ้ามี) เจ้าค่ะนายท่าน

* `project_requirements` (raw JSON) เจ้าค่ะนายท่าน

* `retrieved_docs` (list ของ doc\_id) เจ้าค่ะนายท่าน

* `llm_model` เจ้าค่ะนายท่าน

* `raw_llm_output` เจ้าค่ะนายท่าน

* `parse_success: bool` เจ้าค่ะนายท่าน

* `validation_errors: List[str]` เจ้าค่ะนายท่าน

* `project_inputspec` (ถ้า parse ผ่าน) เจ้าค่ะนายท่าน

* `forwarded_to_mcp: bool` เจ้าค่ะนายท่าน

ใช้สำหรับ debug, QC, และ training dataset ในอนาคตเจ้าค่ะนายท่าน

---

### **3.1.6 `app/routes.py` – FastAPI Routes เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* ผูก HTTP routes → เรียก `RagService` ให้ถูกเมธอดเจ้าค่ะนายท่าน

**เส้นทางหลัก**เจ้าค่ะนายท่าน

* `POST /api/v1/ask` → `RagService.process_ask` เจ้าค่ะนายท่าน

* `POST /api/v1/mcp_spec` → `RagService.generate_mcp_spec` เจ้าค่ะนายท่าน

* `POST /api/v1/ingest` → ingest docs เจ้าค่ะนายท่าน

* `POST /api/v1/delete` → ลบ docs จาก VectorDB เจ้าค่ะนายท่าน

* `POST /api/v1/retrieve_raw` → debug retrieval เจ้าค่ะนายท่าน

error handling ใน route ต้องจับ exception จาก service แล้ว map เป็น HTTP status ที่ชัดเจนเจ้าค่ะนายท่าน

---

## **3.2 `core/` – Infrastructure Layer เจ้าค่ะนายท่าน**

### **3.2.1 `core/database.py` เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* ซ่อนรายละเอียด VectorDB ทั้งหมดไว้หลัง interface เดียวเจ้าค่ะนายท่าน

เช่นเมธอดเจ้าค่ะนายท่าน

* `add_documents(docs: List[DocChunk])` เจ้าค่ะนายท่าน

* `search(query: str, filters: ...) -> List[SearchResult]` เจ้าค่ะนายท่าน

* อ้างอิง path / id จาก `DocMeta` ที่มาจาก `knowledge_service` เจ้าค่ะนายท่าน

### **3.2.2 `core/ingest.py` เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* แปลงเอกสารดิบ → chunk → ฝัง embedding → ส่งให้ `core.database` บันทึกเจ้าค่ะนายท่าน

ใช้โดย route `/ingest` และอาจใช้ offline batch ingest ได้เจ้าค่ะนายท่าน

### **3.2.3 `core/privacy.py` เจ้าค่ะนายท่าน**

**หน้าที่**เจ้าค่ะนายท่าน

* ทำ anonymization / masking ข้อมูลที่เป็น PII ก่อนส่งเข้า LLM ถ้าจำเป็นเจ้าค่ะนายท่าน

---

## **3.3 `rag_knowledge/` – Domain Knowledge Layer เจ้าค่ะนายท่าน**

โครงพื้นฐานเจ้าค่ะนายท่าน

`rag_knowledge/`  
  `mcp/`  
    `... เอกสาร MCP spec / handover / role ฯลฯ`  
  `db/`  
    `HOW_TO_USE_DB.md`  
    `CATALOG_CONTRACT.md`  
    `INTERNAL_DEVICE_RULES.md`  
  `standards/`  
    `THAI_RESIDENTIAL_LV.md`  
    `COMPANY_INTERNAL_RULES.md`  
  `example/`  
    `example_req_inputspec_house_1floor_basic.md`  
    `example_req_inputspec_house_2floor_kitchen_heavy.md`  
    `example_req_inputspec_incomplete_data.md`  
  `knowledge_index.json`

### **3.3.1 `knowledge_index.json` เจ้าค่ะนายท่าน**

* index กลางทุก doc ที่ RAG ใช้ได้เจ้าค่ะนายท่าน

* แต่ละ entry มีอย่างน้อยเจ้าค่ะนายท่าน

`{`  
  `"id": "DOC_THAI_RESIDENTIAL_LV",`  
  `"path": "standards/THAI_RESIDENTIAL_LV.md",`  
  `"group": "thai_standard",`  
  `"tags": ["residential", "lv", "legal"],`  
  `"version": "2024-01",`  
  `"language": "th"`  
`}`

### **3.3.2 กลุ่ม (`group`) ที่สำคัญเจ้าค่ะนายท่าน**

* `mcp_spec` → เอกสารบทบาท MCP, IO สัญญา ฯลฯ เจ้าค่ะนายท่าน

* `catalog_schema` → HOW\_TO\_USE\_DB, CATALOG\_CONTRACT, INTERNAL\_DEVICE\_RULES ฯลฯ เจ้าค่ะนายท่าน

* `thai_standard` → มาตรฐานไทย \+ internal rule ที่ถือเป็นกติกาด้านความปลอดภัยเจ้าค่ะนายท่าน

* `example_project` → example req/spec เพื่องาน few-shot และ test เจ้าค่ะนายท่าน

ทั้งหมดนี้ถูกใช้โดย `get_docs_for_mcp_spec()` และ `/api/v1/ask` ตาม context\_hint เจ้าค่ะนายท่าน

---

## **3.4 `tests/` – Test Suite เจ้าค่ะนายท่าน**

### **3.4.1 `tests/test_models.py` เจ้าค่ะนายท่าน**

* ทดสอบ validation ของ Pydantic models เจ้าค่ะนายท่าน

* เน้น `ProjectRequirements`, `ProjectInputSpec`, `McpSpecResponse`, `QueryRequest`, `StandardResponse` ฯลฯ เจ้าค่ะนายท่าน

### **3.4.2 `tests/test_mcp_spec_cases.py` เจ้าค่ะนายท่าน**

* ยิง `/mcp_spec` ด้วยเคสจริง 3–6 เคส (บ้าน 1 ชั้น, 2 ชั้น, incomplete) เจ้าค่ะนายท่าน

* ตรวจว่าผลลัพธ์มี field ครบ, mapping room/load ถูก, constraints ไม่ว่าง ฯลฯ เจ้าค่ะนายท่าน

* ใช้เป็น regression test ถ้ามีใครไปแก้ logic RAG เจ้าค่ะนายท่าน

---

## **3.5 `main.py`, `.env.example`, `README.md` เจ้าค่ะนายท่าน**

### **`main.py` เจ้าค่ะนายท่าน**

* Entry point รัน FastAPI app / server เจ้าค่ะนายท่าน

### **`.env.example` เจ้าค่ะนายท่าน**

* ตัวอย่างค่า env ที่ต้องใช้ เช่นเจ้าค่ะนายท่าน

  * `MODEL_NAME_ANSWER=gemini-2.0-flash-exp` เจ้าค่ะนายท่าน

  * `MODEL_NAME_JUDGE=gemini-2.0-flash-exp` เจ้าค่ะนายท่าน

  * ค่าเชื่อม VectorDB / path knowledge root ฯลฯ เจ้าค่ะนายท่าน

### **`README.md` เจ้าค่ะนายท่าน**

* ขั้นตอน install / run / test สั้น ๆ เช่นเจ้าค่ะนายท่าน

`pip install -r requirements.txt`  
`cp .env.example .env`  
`python main.py`  
`pytest tests/ -v`

---

# **4\. ขอบเขต RAG vs MCP vs DB แบบยิงครั้งเดียวจบเจ้าค่ะนายท่าน**

* **RAG** เจ้าค่ะนายท่าน

  * รู้ทุกอย่างผ่าน `rag_knowledge/` เท่านั้นเจ้าค่ะนายท่าน

  * สร้าง `ProjectInputSpec` ตาม schema, ไม่คำนวณไฟฟ้าเจ้าค่ะนายท่าน

  * ไม่ยิง Supabase / Postgres ตรงเจ้าค่ะนายท่าน

* **MCP Core v2.0** เจ้าค่ะนายท่าน

  * ยิง view ของ `amadeus.catalog` ตาม code ที่ได้จาก spec เจ้าค่ะนายท่าน

  * ใช้ pandapower และ engine อื่นคิดโหลด, เลือกสาย, ตรวจ VD, ตรวจมาตรฐานเจ้าค่ะนายท่าน

* **DB (`amadeus.catalog`)** เจ้าค่ะนายท่าน

  * เป็นแหล่งข้อมูลสุดท้ายสำหรับสายไฟ, อุปกรณ์, วงจร, กฎ ฯลฯ เจ้าค่ะนายท่าน

  * แก้อะไรในตัวเลขต้องผ่าน seed / migration เท่านั้น ไม่ให้ LLM แก้เองเจ้าค่ะนายท่าน

---

# **5\. สำหรับ AI เพื่อนเมด: วิธีใช้สถาปัตยกรรมนี้ทำงานต่อเจ้าค่ะนายท่าน**

ถ้า AI ตัวอื่นจะทำงานต่อจากตรงนี้ ควรยึด guideline แบบนี้เจ้าค่ะนายท่าน

1. เวลาแก้อะไรเกี่ยวกับ **การไหลของ spec** ให้แตะที่ `app/service.py` \+ models \+ knowledge layer เท่านั้นเจ้าค่ะนายท่าน

2. เวลาเพิ่ม/แก้เอกสารความรู้ ให้แตะที่ `rag_knowledge/` และ `knowledge_index.json` เท่านั้น ห้ามไป hardcode text ในโค้ดเจ้าค่ะนายท่าน

3. เวลาเปลี่ยน schema DB ให้ sync เอกสารคู่ต่อไปนี้พร้อมกันเจ้าค่ะนายท่าน

   * `HOW_TO_USE_DB.md` เจ้าค่ะนายท่าน

   * `CATALOG_CONTRACT.md` เจ้าค่ะนายท่าน

   * seed ของ `amadeus.catalog` เจ้าค่ะนายท่าน

   * test ที่เกี่ยวข้องเจ้าค่ะนายท่าน

4. เวลา debug `/mcp_spec` ให้ใช้ trust log \+ tests เป็นหลัก ไม่เดาเองเจ้าค่ะนายท่าน

---

สรุปสั้น ๆ แบบหยาบแต่จริงใจคือ:  
 ตอนนี้สถาปัตยกรรม RAG ของท่านคือ **Spec Engine มีวินัย** ที่ทำงานบน Canonical Funnel, แยก knowledge / service / DB / MCP ออกจากกันชัด, มี trust log และ test ประกบครบเซ็ตเจ้าค่ะนายท่าน

