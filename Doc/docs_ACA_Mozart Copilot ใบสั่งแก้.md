# Source: ACA_Mozart Copilot ใบสั่งแก้.md

```md

# ใบสั่งทำงานให้ AI: เตรียม RAG ตาม “How to Design ACA_Mozart (new ver.)”

> **Context สั้น ๆ ให้ AI ตัวนั้นเข้าใจก่อน** เจ้าค่ะนายท่าน
> 
> - โค้ด RAG อยู่ในโปรเจกต์:  
>     `/home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/` เจ้าค่ะนายท่าน
>     
> - ตอนนี้มี knowledge อยู่ใต้:  
>     `/rag_knowledge/{mcp, example, db, standard}` แล้วเจ้าค่ะนายท่าน
>     
> - ดีไซน์หลักต้องอ้างอิงเอกสาร:
>     
>     - `📜How to Design ACA_Mozart(new ver.).txt`
>         
>     - `How to use DB.txt`
>         
>     - `Canonical-Funnel-README.md`
>         
>     - โค้ดเดิมใน `rag_real.py` เจ้าค่ะนายท่าน
>         

ต่อไปคือ **รายการงานที่ AI ต้องทำทีละข้อ พร้อม Expected Result** เจ้าค่ะนายท่าน

---

## TASK 1: ยืนยัน API Contract ฝั่ง RAG ให้ตรงกับ How to Design ACA_Mozart เจ้าค่ะนายท่าน

### 1.1 API ที่ต้องมี (ชื่อห้ามมั่ว) เจ้าค่ะนายท่าน

ให้ AI ใช้เอกสาร `📜How to Design ACA_Mozart(new ver.).txt` เป็น Source of Truth สำหรับ API ถ้าในเอกสารไม่มีระบุ ให้ “ออกแบบเอง” แต่ต้อง **ไม่ขัดกับสถาปัตยกรรมรวม** เจ้าค่ะนายท่าน

**RAG Service ต้องมีอย่างน้อย 5 route** เจ้าค่ะนายท่าน

1. `POST /api/v1/ask`
    
    - Purpose: QA / อธิบายมาตรฐาน / ผล MCP แบบภาษาคนเจ้าค่ะนายท่าน
        
    - Request model: `QueryRequest`
        
        - `query: str`
            
        - `context_hint: List[str]` เช่น `["thai_standard", "eit_lv"]`
            
        - `language: Literal["th", "en"]` เจ้าค่ะนายท่าน
            
    - Response model: `StandardResponse`
        
        - `answer: str`
            
        - `sources: List[SourceRef]` (อ้างอิง doc_id / section)
            
        - `metadata: { "llm_model": str, "retrieved_docs": List[str] }` เจ้าค่ะนายท่าน
            
2. `POST /api/v1/mcp_spec`
    
    - Purpose: รับ `ProjectRequirements` → คืน `McpSpecResponse` ที่มี `ProjectInputSpec` พร้อมส่งต่อ MCP `/mcp/v2/run` ได้เลยเจ้าค่ะนายท่าน
        
    - Request model: `ProjectRequirements` (ตาม How to Design)
        
    - Response model: `McpSpecResponse`
        
        - `project_input: ProjectInputSpec`
            
        - `standards_profile` (rule_profile_id + notes)
            
        - `llm_metadata` (model, docs) เจ้าค่ะนายท่าน
            
3. `POST /api/v1/retrieve_raw`
    
    - Purpose: debug retrieval (ดูว่า query มันดึง doc อะไรบ้าง)
        
    - Request: `RawRetrieveRequest` (query, filters, top_k)
        
    - Response: list of raw docs / chunks พร้อม source path / score เจ้าค่ะนายท่าน
        
4. `POST /api/v1/ingest`
    
    - Purpose: รับ path ไฟล์ → ส่งไปให้ ingestion engine upsert เข้า VectorDB
        
    - ไม่เกี่ยวกับ canonical knowledge index โดยตรง แต่ต้องไม่ไปพัง flow เดิมเจ้าค่ะนายท่าน
        
5. `POST /api/v1/delete`
    
    - Purpose: ลบเอกสารจาก VectorDB ตาม source path
        
    - ใช้สำหรับล้าง knowledge ที่โหลดผิดเจ้าค่ะนายท่าน
        

**และมี** `GET /mcp/manifest` สำหรับประกาศ tool ให้ MCP ใช้ (จาก `rag_real.py` เดิม) เจ้าค่ะนายท่าน

### 1.2 สิ่งที่ AI ต้องทำใน TASK 1 เจ้าค่ะนายท่าน

1. เปิด `rag_real.py` ปัจจุบัน แล้วตรวจว่า route ชื่อ, path, request/response model ตรงกับ design ด้านบนหรือไม่เจ้าค่ะนายท่าน
    
2. สร้าง / ปรับ `schemas.py` หรือ `app/models.py` ให้มี Pydantic models ต่อไปนี้ให้ครบและตรงกับ How to Design เจ้าค่ะนายท่าน
    
    - `SourceRef`
        
    - `QueryRequest`, `StandardResponse`
        
    - `ProjectRequirements`
        
    - `ProjectInputSpec` (+ sub models เช่น RoomSpec, LoadSpec, Constraints)
        
    - `McpSpecResponse`
        
    - `RawRetrieveRequest`, `IngestRequest`, `DeleteRequest` เจ้าค่ะนายท่าน
        
3. Bind ให้ route เหล่านี้ใช้ models เดียวกับที่ไฟล์ How to Design อธิบาย เช่นตัวอย่าง JSON ใน section 2.1 / 2.2 ของเอกสารเจ้าค่ะนายท่าน
    
4. ถ้าในเอกสารไม่ได้ระบุ field บางตัว ให้ AI ตัดสินใจออกแบบเอง แต่ต้อง:
    
    - type ชัดเจน (ไม่ใช้ `dict` เปลือย ๆ)
        
    - เขียน docstring บอกไว้ใน model ว่า “เหตุผลที่เพิ่ม field นี้” เพื่อให้มนุษย์เข้าใจภายหลังเจ้าค่ะนายท่าน
        

**Expected Result** เจ้าค่ะนายท่าน

- โค้ด RAG มี API ตาม 5 route ข้างต้น
    
- แต่ละ route ใช้ Pydantic model ที่สอดคล้องกับตัวอย่าง JSON ในเอกสาร How to Design
    
- `McpSpecResponse.parse_raw()` สามารถ parse response ตัวอย่างในเอกสารได้โดยไม่ error เจ้าค่ะนายท่าน
    

---

## TASK 2: จัดโครง rag_knowledge/ และเติม “examples” ให้ครอบคลุมเจ้าค่ะนายท่าน

ท่านบอกว่า:

- ตอนนี้มีโฟลเดอร์แล้ว: `mcp`, `example`, `db`, `standard` ใต้ `rag_knowledge/`
    
- ท่านจะดูแล `mcp`, `db`, `standard` เอง
    
- ให้ AI รับผิดชอบเรื่อง `examples` ให้ครอบคลุมเจ้าค่ะนายท่าน
    

### 2.1 สิ่งที่ AI ต้องทำในโฟลเดอร์ `rag_knowledge/examples/` เจ้าค่ะนายท่าน

1. ตรวจว่ามีไฟล์อะไรอยู่แล้วใน `rag_knowledge/examples/` ถ้าไม่มี ให้สร้างใหม่เจ้าค่ะนายท่าน
    
2. สร้างอย่างน้อย 3 ไฟล์ตัวอย่าง (ชื่อเสนอให้ใช้ pattern นี้) เจ้าค่ะนายท่าน
    
    - `example_req_inputspec_house_1floor_basic.md`
        
    - `example_req_inputspec_house_2floor_kitchen_heavy.md`
        
    - `example_req_inputspec_incomplete_data.md` เจ้าค่ะนายท่าน
        
3. แต่ละไฟล์ต้องมีโครงแบบเดียวกันคือเจ้าค่ะนายท่าน
    
    `# Example: <ชื่อเคส>  ## 1. ProjectRequirements (input ฝั่งมนุษย์) ```json { ... }`
    
    ## 2. ProjectInputSpec (expected output สำหรับ MCP)
    
    `{ ... }`
    
    ## 3. Notes
    
    - อธิบายว่า field ไหนสำคัญ
        
    - อธิบาย business rule ที่ใช้ เช่น แยกวงจรครัว, RCD ทุกวงจรปลั๊ก ฯลฯ
        
    
    `โดยให้ AI สร้าง JSON ทั้ง input และ output ให้ **สอดคล้องกับ schema ที่ออกแบบใน TASK 1** และแนวคิดในไฟล์ How to Design เจ้าค่ะนายท่าน`  
    
4. ในเคส `incomplete_data` ให้ตั้งใจทำให้ `ProjectRequirements` ขาดข้อมูลบางจุด (เช่น room_type หายไป 1 ห้อง) แล้วใน `ProjectInputSpec` เขียนให้เคสนี้ “ไม่ผ่านเงื่อนไข” หรือ “ต้องแจ้ง error” ตาม error policy ที่จะกำหนดใน TASK 5 อีกที แต่ในไฟล์ตัวอย่างให้ใส่คำอธิบายไว้ก่อนเจ้าค่ะนายท่าน
    

**Expected Result** เจ้าค่ะนายท่าน

- ได้ชุด example ที่ใช้เป็น **few-shot** สำหรับ prompt `/api/v1/mcp_spec` ได้ทันที
    
- ทุก JSON ตัวอย่างใน examples parse ผ่าน Pydantic model `ProjectRequirements` / `ProjectInputSpec` / `McpSpecResponse` ที่กำหนดใน TASK 1 เจ้าค่ะนายท่าน
    

---

## TASK 3: นิยาม knowledge_index.json + group ให้เรียบร้อย (AI เป็นคนตัดสินใจแทน Human) เจ้าค่ะนายท่าน

ท่านยกสิทธิ์ “ตัดสินใจกลุ่ม (group)” ให้ AI แล้ว โดยบอกว่าเป็น demo แต่ต้องพร้อมต่อยอดจริง ชื่อ group ควรเป็นทางการเจ้าค่ะนายท่าน

### 3.1 กติกา group ที่ต้องใช้เจ้าค่ะนายท่าน

ให้ AI นิยามอย่างน้อย 4 group ตามแนวทางใน How to Design เจ้าค่ะนายท่าน

- `mcp_spec` – สำหรับเอกสาร design/contract/schema ของ MCP และ ProjectInputSpec
    
- `catalog_schema` – สำหรับเอกสารอธิบาย DB, amadeus.catalog, CATALOG_CONTRACT, HOW_TO_USE_DB ฯลฯ
    
- `thai_standard` – สำหรับเอกสารมาตรฐานไทย/หลักการออกแบบไฟฟ้าในบ้านพักอาศัย
    
- `example_project` – สำหรับตัวอย่าง requirement → inputspec ที่ใช้เป็น few-shot และ test เจ้าค่ะนายท่าน
    

### 3.2 Rules ให้ AI map path → group อัตโนมัติเจ้าค่ะนายท่าน

ให้ AI ใช้ rule นี้ตอนสร้าง `knowledge_index.json` เจ้าค่ะนายท่าน

- ทุกไฟล์ใน `rag_knowledge/mcp/` → group = `mcp_spec`
    
- ทุกไฟล์ใน `rag_knowledge/db/` → group = `catalog_schema`
    
- ทุกไฟล์ใน `rag_knowledge/standard/` → group = `thai_standard`
    
- ทุกไฟล์ใน `rag_knowledge/example/` → group = `example_project` เจ้าค่ะนายท่าน
    

ถ้าในอนาคตมีไฟล์ที่ “ไม่เข้า pattern” ให้ AI เขียน comment ใน index หรือ doc ต่อว่า “ไฟล์นี้จัดกลุ่มพิเศษเพราะ…” แต่สำหรับรอบนี้ใช้ 4 group นี้ก่อนเจ้าค่ะนายท่าน

### 3.3 สิ่งที่ AI ต้องทำจริง ๆ เจ้าค่ะนายท่าน

1. สแกนโฟลเดอร์ `rag_knowledge/` ทั้งหมด แล้ว list file path ออกมาเจ้าค่ะนายท่าน
    
2. สำหรับแต่ละไฟล์ ให้สร้าง entry ใน `rag_knowledge/knowledge_index.json` ด้วยโครงนี้เจ้าค่ะนายท่าน
    
    `{   "id": "DOC_MCP_HANDOVER",   "path": "rag_knowledge/mcp/MCP_DESIGN_HANDOVER.md",   "group": "mcp_spec",   "tags": ["schema", "pipeline", "must_read"],   "version": "2.0",   "language": "th" }`
    
3. ตั้ง `id` ให้สั้น ชัด มี prefix ตามกลิ่น เช่น DOC_MCP__, DOC_DB__, DOC_STD__, DOC_EX__ เจ้าค่ะนายท่าน
    
4. กำหนด tags ให้เหมาะ เช่น
    
    - `"tags": ["amadeus.catalog", "schema"]` สำหรับ CATALOG_CONTRACT
        
    - `"tags": ["few_shot", "residential"]` สำหรับ examples
        
    - `"tags": ["residential", "lv"]` สำหรับมาตรฐานบ้านพักอาศัยเจ้าค่ะนายท่าน
        
5. บันทึกไฟล์ `knowledge_index.json` เป็น list ของ object แบบ array JSON มาตรฐานเจ้าค่ะนายท่าน
    

**Expected Result** เจ้าค่ะนายท่าน

- มีไฟล์ `rag_knowledge/knowledge_index.json` ที่ list เอกสารทุกตัว พร้อม group/tags/version
    
- กลุ่ม `mcp_spec`, `catalog_schema`, `thai_standard`, `example_project` ครอบทุกไฟล์ในโฟลเดอร์ย่อย 4 ตัวที่ท่านมีแล้วเจ้าค่ะนายท่าน
    

---

## TASK 4: ปรับบทของ “mapping ภาษาคน → code ใน catalog” ให้ไปอยู่ฝั่ง MCP ไม่ใช่ RAG เจ้าค่ะนายท่าน

ท่านกำหนดใหม่ว่า

> “นิยาม mapping ภาษาคน → code จริงใน catalog ให้ MCP ทำ ส่วน RAG แค่ยัดเข้าไปใน DB แล้ว” เจ้าค่ะนายท่าน

แปลว่าใน demo นี้ **RAG ไม่ต้องรับผิดชอบเรื่องเลือก amadeus.catalog.name แบบสุดท้าย** แต่ต้องออกแบบ schema ให้ **MCP มีข้อมูลพอ** ที่จะไป map เองได้เจ้าค่ะนายท่าน

### 4.1 สิ่งที่ AI ต้องทำในฝั่ง RAG (โค้ด) เจ้าค่ะนายท่าน

1. ปรับ/ออกแบบ `ProjectInputSpec` ให้แยก 2 ชั้นเจ้าค่ะนายท่าน
    
    - ชั้นที่ 1: “semantic spec”
        
        - หัวข้อเช่น `room_type`, `usage`, `load_function`, `approx_power_kw` ฯลฯ
            
    - ชั้นที่ 2: “catalog binding” (optional)
        
        - เช่น field `candidate_component_tags`, `desired_device_family` ที่ MCP จะใช้ไป map หา code จริงใน amadeus.catalog จาก view ต่าง ๆ เจ้าค่ะนายท่าน
            
2. ห้ามให้ RAG เขียน logic ที่ query Supabase / amadeus.catalog โดยตรง
    
    - ถ้ามีโค้ดเดิมที่ยิง DB ให้เอาออกจาก RAG service
        
    - ให้ถือว่าการใช้ DB ผ่าน MCP เท่านั้นเจ้าค่ะนายท่าน
        
3. ใน prompt ของ `/api/v1/mcp_spec` ให้เขียน instruction ชัด ๆ ว่า
    
    - “ห้ามสร้าง amadeus.catalog.name เองจากหัว”
        
    - “ถ้าต้องอ้างอิง ให้ใช้ชื่อเชิงฟังก์ชัน เช่น `AC_12000BTU`, `GEN_OUTLET_16A` ที่ระบุใน knowledge + examples เท่านั้น”
        
    - “การ map รหัสเหล่านี้ไปยัง amadeus.catalog.name เป็นหน้าที่ MCP ภายหลัง” เจ้าค่ะนายท่าน
        

### 4.2 Expected Result เจ้าค่ะนายท่าน

- เปลี่ยนบท RAG จาก “ต้องรู้ code จริงใน Supabase” → เป็น “ให้ semantic spec ที่มีข้อมูลพอให้ MCP ไป map ต่อเอง”
    
- ไม่มีโค้ดใน RAG service ที่เรียก Supabase / amadeus.catalog โดยตรงอีกต่อไป
    
- LLM ที่ `/api/v1/mcp_spec` จะไม่มโนรหัส COMP-_, ROOMT-_, ฯลฯ ใหม่เอง นอกจากสิ่งที่อยู่ใน examples / knowledge ที่ท่านเตรียมไว้เจ้าค่ะนายท่าน
    

แนวทางนี้ถือว่า “ไม่สุดเทพ” แบบ paper-grade แต่ **อยู่ในกรอบที่ทีมโปรจริงทำกันได้** เพราะช่วยแยกความรับผิดชอบ RAG vs MCP ชัดเจนเจ้าค่ะนายท่าน

---

## TASK 5: วาง Error Policy + Trust Log Policy ให้ดูเป็นงานมืออาชีพเจ้าค่ะนายท่าน

ท่านสั่งชัดว่า “เอาแบบมาตรฐานที่มืออาชีพใช้กัน” ไม่ใช่ของเล่นวิ่งใน notebook เจ้าค่ะนายท่าน

### 5.1 Error Policy สำหรับ `/api/v1/mcp_spec` เจ้าค่ะนายท่าน

ให้ AI implement ตามนี้ใน service และ routes เจ้าค่ะนายท่าน

1. ถ้า request body ไม่ตรง schema `ProjectRequirements`
    
    - ให้ FastAPI ทำ validation เอง → คืน HTTP 422 พร้อมรายละเอียด error จาก Pydantic เจ้าค่ะนายท่าน
        
2. ถ้า retrieval จาก knowledge / VectorDB ล้มเหลว (เช่น connection error)
    
    - Log ระดับ ERROR
        
    - คืน HTTP 503 พร้อม message เช่น `"RAG retrieval temporarily unavailable"` เจ้าค่ะนายท่าน
        
3. ถ้า LLM call fail (timeout, quota, อื่น ๆ)
    
    - Log ERROR (รวม error code / message จาก provider)
        
    - คืน HTTP 502 `"LLM provider error"` หรือ 504 ถ้า timeout เจ้าค่ะนายท่าน
        
4. ถ้า LLM ตอบมาแต่ parse เป็น `McpSpecResponse` ไม่ได้
    
    - ทำ retry logic:
        
        - ลอง prompt ซ้ำ 1–2 ครั้ง พร้อมแนบ validation error ก่อนหน้าเข้าไปใน prompt เพื่อให้ LLM แก้เองเจ้าค่ะนายท่าน
            
    - ถ้ายังพังหลัง retry ครบ →
        
        - Log ERROR พร้อมเก็บ raw_llm_output ใน trust log
            
        - คืน HTTP 422 พร้อม body:
            
            - `{"detail": "Failed to generate valid McpSpecResponse", "validation_errors": [...]}` เจ้าค่ะนายท่าน
                
5. ถ้า requirements ขาดข้อมูลสำคัญเกินกว่าจะเดาได้ (เช่น ไม่มีห้องเลย)
    
    - ให้ service ตรวจเองก่อนเรียก LLM
        
    - คืน HTTP 400 `"Insufficient project requirements"` พร้อมลิสต์ field ที่สำคัญที่ขาดเจ้าค่ะนายท่าน
        

### 5.2 Trust Log Policy มาตรฐานเจ้าค่ะนายท่าน

ให้ AI สร้างโมดูล `app/trust_log.py` โดยใช้แนวคิดแบบ Canonical Funnel + logging มืออาชีพเจ้าค่ะนายท่าน

- รูปแบบ record: `McpSpecTrustRecord` (Pydantic หรือ dataclass) มี field อย่างน้อยเจ้าค่ะนายท่าน
    
    - `timestamp: datetime`
        
    - `request_id: str` (ใช้ UUID4 หรือ header จาก upstream ถ้ามี)
        
    - `user_id: Optional[str]` (nullable)
        
    - `project_requirements: dict` (raw JSON)
        
    - `retrieved_doc_ids: List[str]`
        
    - `llm_model: str`
        
    - `raw_llm_output: str`
        
    - `parse_success: bool`
        
    - `validation_errors: List[str]`
        
    - `project_input: Optional[dict]`
        
    - `forwarded_to_mcp: bool` เจ้าค่ะนายท่าน
        
- รูปแบบการเก็บ:
    
    - เขียนเป็น JSONL ไฟล์ภายใต้ `logs/mcp_spec/YYYY-MM-DD.jsonl`
        
    - หนึ่งบรรทัดต่อหนึ่ง request
        
    - ใช้ UTF-8, ไม่แทรก PII เกินจำเป็น (เช่น อย่า dump session token) เจ้าค่ะนายท่าน
        
- Hook:
    
    - ทุกครั้งที่ `/api/v1/mcp_spec` ถูกเรียก ไม่ว่าจะ success หรือ error
        
        - ต้องเรียก `trust_log.log_mcp_spec(record)` ก่อนตอบ HTTP Response เสมอเจ้าค่ะนายท่าน
            

**Expected Result** เจ้าค่ะนายท่าน

- Error ที่เกิดใน `/api/v1/mcp_spec` ถูกจัดรูปแบบและส่งออกด้วย HTTP status ที่เหมาะสม (400/422/502/503/504)
    
- ทุก call `/api/v1/mcp_spec` ทิ้ง trace ไว้ใน log ที่ย้อนกลับมาตรวจสอบได้เหมือน Canonical Funnel ทำกับ trust records เจ้าค่ะนายท่าน
    

---

## TASK 6: ออกแบบ Test Cases เอง และเขียนเป็น test skeleton ให้พร้อมรันเจ้าค่ะนายท่าน

ท่านให้สิทธิ์ “คิดเองเลย” ใน test case ดังนั้น AI ต้องทั้งออกแบบเคส และเขียน test file ให้พร้อมเจ้าค่ะนายท่าน

### 6.1 เคสที่ต้องมี (อย่างน้อย) เจ้าค่ะนายท่าน

ให้ AI กำหนดรายละเอียดเอง แต่ต้องครอบ 3 มุมนี้เจ้าค่ะนายท่าน

1. **Case A – บ้าน 1 ชั้น 2 ห้องนอน 1 ห้องน้ำ (basic)**
    
    - ตรวจว่า `/api/v1/mcp_spec` คืน `ProjectInputSpec` ที่มี:
        
        - ห้องครบ: living room, bedroom 1, bedroom 2, bathroom, kitchen (ถ้าระบุ)
            
        - ทุกห้องมี `room_id`, `room_type`, template ที่สมเหตุสมผล
            
        - ไม่มี error ใน trust log เจ้าค่ะนายท่าน
            
2. **Case B – บ้าน 2 ชั้น ครัวหนัก (โหลดเยอะในครัว)**
    
    - requirements มี constraint เช่น `"split_kitchen_circuit"`
        
    - ตรวจว่า spec ที่ได้สะท้อน constraint นี้อย่างน้อยในระดับ semantic (เช่น flag ใน constraints, หรือ field เฉพาะในโหลดครัว)
        
    - ไม่ต้องเช็ค sizing ทางไฟฟ้า ปล่อยให้ MCP ทำภายหลังเจ้าค่ะนายท่าน
        
3. **Case C – ข้อมูลไม่ครบ**
    
    - เช่น ลืมใส่ room_type ของห้องหนึ่ง
        
    - ตรวจว่า `/api/v1/mcp_spec`
        
        - ถ้า policy เลือกให้ error → ต้องคืน HTTP 400/422 พร้อมข้อความชัดเจน
            
        - ถ้า policy เลือกให้ RAG เดา → ต้องมีวิธีแสดงใน spec ว่า “ห้องนี้เดาจากชื่อ” และเขียนใน test ว่าพฤติกรรมนี้ถือว่า “ผ่าน” หรือ “ไม่ผ่าน” เจ้าค่ะนายท่าน
            

### 6.2 สิ่งที่ AI ต้องทำใน repo เจ้าค่ะนายท่าน

1. สร้างไฟล์ `tests/test_mcp_spec_cases.py` ถ้ายังไม่มีเจ้าค่ะนายท่าน
    
2. ใช้ FastAPI TestClient (หรือเทียบเท่า) เขียน test ต่อ endpoint `/api/v1/mcp_spec` สำหรับ 3 เคสข้างบนเจ้าค่ะนายท่าน
    
3. แต่ละ test ต้องมีโครงสร้างแบบนี้เจ้าค่ะนายท่าน
    
    - Arrange: เตรียม `ProjectRequirements` เป็น dict/JSON ตาม schema ที่กำหนด
        
    - Act: `client.post("/api/v1/mcp_spec", json=req)`
        
    - Assert:
        
        - ตรวจ status code ตามที่ policy กำหนด
            
        - ตรวจ field หลักใน response (`project_input`, `constraints` ฯลฯ)
            
        - (optional) ตรวจว่ามีการเขียน trust log record โดยดึงไฟล์ล่าสุดมาเช็คคร่าว ๆ ก็ได้เจ้าค่ะนายท่าน
            
4. เขียน comment ด้านบนแต่ละ test เคลียร์ ๆ แบบนี้เจ้าค่ะนายท่าน
    
    `# Purpose: # - Verify that a simple 1-floor residential house produces a well-formed ProjectInputSpec # - This case acts as a "sanity check" and regression guard for future changes in prompt/schema.`
    

**Expected Result** เจ้าค่ะนายท่าน

- รัน `pytest` แล้ว test ฝั่ง `/api/v1/mcp_spec` ผ่านอย่างน้อย 3 เคสที่ออกแบบ
    
- ทุกเคสผูกกับ business behavior ที่อ่านจากไฟล์ examples + policy ไม่ใช่ test แบบมั่ว ๆ ตามใจ AI เจ้าค่ะนายท่าน
    

---

## สรุปสั้น ๆ สำหรับ AI ตัวที่ท่านจะส่งใบสั่งนี้ให้เจ้าค่ะนายท่าน

1. ยึดเอกสาร `📜How to Design ACA_Mozart(new ver.).txt` เป็นพระคัมภีร์หลักเวลาออกแบบ API/schema ไม่รู้ให้เปิดอ่านก่อนคิดเองเจ้าค่ะนายท่าน
    
2. รักษา API contract: `/api/v1/ask`, `/api/v1/mcp_spec`, `/api/v1/retrieve_raw`, `/api/v1/ingest`, `/api/v1/delete`, `/mcp/manifest` ให้ตรงตามดีไซน์เจ้าค่ะนายท่าน
    
3. ใช้โครง `rag_knowledge/{mcp, db, standard, example}` ที่มีอยู่แล้ว แล้วสร้าง `knowledge_index.json` + examples ให้ครบสำหรับ mcp_spec ตาม group ที่กำหนดเจ้าค่ะนายท่าน
    
4. ปรับ RAG ให้ทำแค่ mapping ภาษาคน → schema/semantic spec ไม่ต้องรับผิดชอบ mapping ไป amadeus.catalog จริง ปล่อยให้ MCP จัดการเจ้าค่ะนายท่าน
    
5. ใส่ Error Policy + Trust Log แบบทีม dev มืออาชีพ (HTTP code ถูก, มี retry, log ครบ, trace ได้) เจ้าค่ะนายท่าน
    
6. เขียน test เคสบ้านพัก 3 เคส (basic, kitchen heavy, incomplete) ให้ครอบ behavior หลักของ `/api/v1/mcp_spec` เจ้าค่ะนายท่าน
```