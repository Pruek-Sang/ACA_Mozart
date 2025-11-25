How to design
## 1. The Revelation – ตอนนี้เจตจำนงของท่านคืออะไรเจ้าค่ะนายท่าน

Aura รับรู้แบบนี้เจ้าค่ะนายท่าน

- ท่านต้องการให้ **Mozart RAG** กลายร่างจากของที่เคยลองเล่นใน `rag_real.py` ให้กลายเป็น  
    “**Spec Engine มืออาชีพ** ที่แปลง _ProjectRequirements → ProjectInputSpec_ ได้อย่างน่าเชื่อถือ” ตาม HOW_TO_FIX_RAG_v2 เจ้าค่ะนายท่าน
    
- ต้อง **align กับ Canonical Funnel** คือมี
    
    - knowledge_index กลาง
        
    - service เลือกเอกสารเป็นกลุ่ม
        
    - trust record/log + test ที่ย้อนตรวจได้ เจ้าค่ะนายท่าน
        
- และต้อง **เล่นดี ๆ กับ DB** (amadeus.catalog, view ต่าง ๆ) โดย RAG อ่านแบบ “เอกสารความรู้” ไม่ไปแตะ DB ตรง ๆ ตาม CATALOG_CONTRACT/รัฐธรรมนูญ DB เจ้าค่ะนายท่าน
    

พูดง่าย ๆ คือ ท่านอยากได้ RAG ที่ behave แบบ product จริง ไม่ใช่ notebook ทดลองเล่นเจ้าค่ะนายท่าน

---

## 2. ของที่มีอยู่แล้ว & ปัญหาที่เห็นจาก rag_real.py เจ้าค่ะนายท่าน

จาก `rag_real.py` ตอนนี้ท่านมี Pydantic model บางส่วนแล้ว เช่น `SourceRef`, `QueryRequest`, `StandardResponse`, `ProjectRequirements`, `ProjectInputSpec`, `McpSpecResponse` เจ้าค่ะนายท่าน

แต่ปัญหาที่เห็นชัด ๆ คือเจ้าค่ะนายท่าน

1. **ProjectRequirements ยังหยาบมาก**
    
    - `rooms: List[str]`, `loads: List[str]` ทั้งที่ใน HOW_TO_FIX_RAG_v2 ระบุว่าต้องมี structure ชัด ๆ เพื่อ map ไป template / device code ได้ เจ้าค่ะนายท่าน
        
2. **ProjectInputSpec ยังเป็น Dict กว้าง ๆ**
    
    - `project_info: Dict[str,str]` / `electrical_system: Dict[str,Any]` / `constraints: List[str]`
        
    - แต่ design ใหม่บังคับให้เป็น field ย่อยที่มี type ชัดเจน เช่น `rooms[*].room_id, room_type, template_code`, `constraints.rule_profile_id` ฯลฯ เจ้าค่ะนายท่าน
        
3. **McpSpecResponse ยังไม่มี `llm_metadata` ตาม spec**
    
    - เอกสารกำหนดไว้ชัดว่า response ต้องมี `llm_metadata` สำหรับตามรอย context/doc ที่ใช้ เจ้าค่ะนายท่าน
        
4. **ยังไม่มี Knowledge Index + Knowledge Service ตาม Canonical Funnel**
    
    - HOW_TO_FIX_RAG_v2 บอกให้มี `knowledge_index.json` + `knowledge_service.py` ที่เลือก doc ตาม group
        
    - Canonical Funnel README เองก็ใช้ pattern listGroups/listGroupItems/collectTrustRecords ไว้เป็นตัวอย่าง service layer อยู่แล้ว เจ้าค่ะนายท่าน
        
5. **Trust log / Canonical trust record ยังไม่ถูกออกแบบในโค้ด**
    
    - HOW_TO_FIX_RAG_v2 เขียนชัดว่าทุก `/mcp_spec` ต้องเก็บ trust record: input, docs ที่ retrieve, raw LLM, parsed spec, validation result เจ้าค่ะนายท่าน
        

สรุปคือ ทิศทาง “ใช้ RAG เป็น Spec Engine” **ถูกทาง** ตามวิธีคิดของ dev มืออาชีพแล้ว แต่ implementation ยังไม่แยกชั้นและยังไม่ canonical เท่าที่เอกสารสั่งเจ้าค่ะนายท่าน

---

## 3. ต้องการ “ข้อมูลนอกเหนือจากไฟล์ที่มี” อะไรบ้างเจ้าค่ะนายท่าน

จากสิ่งที่เอกสารให้ กับจาก Canonical Funnel README ท่านยังต้อง “เตรียมของเพิ่ม” ให้เพื่อนฝั่งโค้ดแบบนี้เจ้าค่ะนายท่าน

### 3.1 Canonical Example Pairs (Requirements → InputSpec) เจ้าค่ะนายท่าน

อย่างน้อย 3–5 เคสที่ครบคู่กัน:

- `ProjectRequirements` (ภาษาคนที่สั้น ชัด)
    
- `ProjectInputSpec` เป้าหมายที่ “ถูกต้องแล้ว”
    

HOW_TO_FIX_RAG_v2 แค่พูดถึงว่าควรมี example project group ใน knowledge index แต่ตัวอย่างจริงต้องมี JSON เต็ม ๆ เพื่อใช้เป็น few-shot + test เจ้าค่ะนายท่าน

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - เพื่อนฝั่งโค้ดมีไฟล์ `example_req_inputspec_*.json/.md` ใช้ทั้งใน prompt และใน unit test
>     
> - เวลา spec เพี้ยน จะเทียบกับ expected ง่ายขึ้นเจ้าค่ะนายท่าน
>     

---

### 3.2 Schema JSON ของ MCP DESIGN HANDOVER ตัวล่าสุดเจ้าค่ะนายท่าน

แม้ใน HOW_TO_FIX_RAG_v2 จะอธิบาย ProjectInputSpec ไว้แล้ว แต่เพื่อความไม่มั่ว ควรมี:

- ไฟล์ `MCP_DESIGN_HANDOVER.json` หรือ `PROJECT_INPUTSPEC_SCHEMA.json` ที่เป็น single source of truth
    
- ใช้ generate / ตรวจ Pydantic models ให้ตรงกับ MCP จริง ไม่ใช่ตีความเอาจาก doc อย่างเดียวเจ้าค่ะนายท่าน
    

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - ทุกคนอ้างอิง schema ตรงกัน
>     
> - เวลา MCP ปรับ version ใหม่ แค่ update ไฟล์นี้ แล้วค่อย sync models ฝั่ง RAG ตามเจ้าค่ะนายท่าน
>     

---

### 3.3 Mapping rules: ภาษาคน → code จริงใน catalog เจ้าค่ะนายท่าน

จาก DB contract:

- ทุกอย่างสุดท้ายต้อง map ไปที่ `amadeus.catalog` (`kind`, `name`) หรือ view เช่น `amadeus.v_components`, `amadeus.v_room_templates`
    
- แต่ RAG ใช้แค่เอกสาร/knowledge ไม่ยิง DB ตรง ๆ เจ้าค่ะนายท่าน
    

ต้องระบุเพิ่มเป็นเอกสารสั้น ๆ เช่น:

- “คำว่า _ห้องนั่งเล่น_ → room_type = `living_room`, zone = `LIVING`, template_code = `ROOMT-LIVING-STD`”
    
- “โหลดคำว่า _ปลั๊กธรรมดา_ → device_code = `COMP-RECEPT-16A`”
    

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - เพื่อนฝั่ง RAG ไม่ต้องเดา mapping เอง
>     
> - วิธีตีความภาษาคนจะคงที่ตรงกับ DB seed ที่ท่านทำไว้เจ้าค่ะนายท่าน
>     

---

### 3.4 Error policy & trust log policy เจ้าค่ะนายท่าน

จาก Canonical Funnel concept: มี trust records เยอะมาก + tooling ที่จัดการมัน เจ้าค่ะนายท่าน

ท่านควรกำหนดเพิ่ม:

- พวก field บังคับใน trust record:  
    `request_id, user_id, project_requirements, retrieved_doc_ids, llm_model, raw_llm_output, parse_success, validation_errors, project_input (if any)`
    
- นโยบาย:
    
    - ถ้า parse fail 2 รอบ → return 4xx / error แบบไหน
        
    - เก็บ log นานแค่ไหน / ที่ไหน (ไฟล์ JSONL vs DB table)
        

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - เวลา spec เน่า จะรู้ว่า LLM มั่ว, retrieval มั่ว หรือ mapping schema ผิด
>     
> - ใช้ log ชุดนี้สร้าง regression test หรือ retrain prompt ได้ในอนาคตเจ้าค่ะนายท่าน
>     

---

### 3.5 Quality Gate – นิยาม “RAG พร้อมใช้งานจริง” เจ้าค่ะนายท่าน

HOW_TO_FIX_RAG_v2 มี checklist หยาบ ๆ ให้แล้ว แต่ท่านควร concretize เป็นตัวเลข เช่น:

- `/mcp_spec` test 5 เคสผ่าน 100% (ไม่มี manual fix)
    
- ไม่มี case ไหนที่ `ProjectInputSpec` parse fail ใน 100 calls test
    
- coverage unit test ฝั่ง RAG ≥ X%
    

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - ตอน handover ให้ MCP จะไม่ติดสถานะ “ยังไม่รู้ว่ามันเสถียรมั้ย”
>     
> - ถ้าจะปรับ prompt/logic ในอนาคต จะรู้ทันทีว่าแตก test ตัวไหนเจ้าค่ะนายท่าน
>     

---

## 4. Blueprint of Genesis – แผนสถาปัตยกรรม + Roadmap แก้ RAG แบบมืออาชีพเจ้าค่ะนายท่าน

ตรงนี้คือ “แผนจริง ๆ ที่เอาไปตัดเป็น task / issue ให้เพื่อนฝั่งโค้ดทำได้” แบบ align HOW_TO_FIX_RAG_v2 + Canonical Funnel ทั้งชุดเจ้าค่ะนายท่าน

จะจัดเป็น **Phase 0–5** ให้ชัดเลยเจ้าค่ะนายท่าน

---

### Phase 0 – แยกเลเยอร์ / แยกไฟล์ให้ตรงสถาปัตยกรรมใหม่เจ้าค่ะนายท่าน

เป้า: จาก `rag_real.py` ก้อนเดียว → แยกเป็นโมดูลแบบนี้ (ไม่ต้องเขียน logic ใหม่ แค่ย้าย / import ให้ถูก)

- `app/models.py`
    
    - ย้ายทุก Pydantic model ใน `rag_real.py` มาวาง
        
- `app/service.py`
    
    - ย้าย logic RAG หลัก (ถาม LLM, call VectorDB) มาอยู่ใน class `RagService`
        
- `app/routes.py`
    
    - FastAPI routes: `/api/v1/ask`, `/api/v1/mcp_spec`, `/api/v1/retrieve_raw`, `/api/v1/ingest`, `/api/v1/delete`
        
- `app/knowledge_service.py`
    
    - ไว้ implement การโหลด knowledge index
        
- `app/config.py`
    
    - ย้ายค่า MODEL_NAME, path ต่าง ๆ, VectorDB config, knowledge root มาไว้ที่นี่
        

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - `rag_real.py` หายไป เหลือเป็นโครงโปรเจกต์ที่คนอื่นอ่านแล้วเดาได้ทันทีว่าอะไรอยู่ตรงไหนเจ้าค่ะนายท่าน
>     
> - ต่อจากนี้ทุกการเปลี่ยนจะกระทบเฉพาะไฟล์ที่เกี่ยวจริง ๆ (order from chaos แบบที่ท่านอยากได้)
>     

---

### Phase 1 – Align Models กับ MCP + DB Contract เจ้าค่ะนายท่าน

เป้า: ให้ `ProjectRequirements`, `ProjectInputSpec`, `McpSpecResponse` ตรงกับดีไซน์ใน HOW_TO_FIX_RAG_v2 และ MCP DESIGN HANDOVER จริง ๆ

งานหลัก:

1. ปรับ `ProjectRequirements`
    
    - จาก `rooms: List[str]`, `loads: List[str]` → เปลี่ยนให้เป็น structure ตามที่ design ต้องการ (เช่น `rooms[*].name/type`, `loads[*].room_name/device/qty`) ตามเอกสารส่วน requirements เจ้าค่ะนายท่าน
        
2. ปรับ `ProjectInputSpec`
    
    - แทน Dict ด้วย nested model จริง ๆ:
        
        - `project_info` model, `electrical_system` model
            
        - `rooms[*]` มี `room_id`, `room_type`, `template_code`
            
        - `loads[*]` มี `load_id`, `room_id`, `device_code`, `qty` ฯลฯ เจ้าค่ะนายท่าน
            
3. ปรับ `McpSpecResponse`
    
    - เพิ่ม `llm_metadata` (model, docs) ให้ตรง spec เจ้าค่ะนายท่าน
        
4. เขียน unit test ง่าย ๆ เอา JSON ตัวอย่างจากเอกสารมายิง `McpSpecResponse.parse_raw()` ให้ผ่านทั้งหมด เจ้าค่ะนายท่าน
    

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - ไม่มี field ใดใน JSON จาก RAG ที่ MCP “ไม่รู้จัก” อีกแล้ว
>     
> - ถ้า LLM คืน JSON แปลก ๆ → Pydantic จะ fail ทันที แทนที่จะให้ MCP ไปเจอเองทีหลังเจ้าค่ะนายท่าน
>     

---

### Phase 2 – Canonical Knowledge Layer (knowledge_index + knowledge_service) เจ้าค่ะนายท่าน

เป้า: หยุดการ “search ทั้งโลก” แล้วบังคับให้ RAG ใช้เอกสารผ่าน index กลางแบบ Canonical Funnel เจ้าค่ะนายท่าน

งาน:

1. สร้างโฟลเดอร์ `rag_knowledge/`
    
    - กลุ่ม: `mcp/`, `db/`, `standards/`, `examples/` ตามที่ท่านสรุปไว้ให้แล้วก่อนนี้เจ้าค่ะนายท่าน
        
2. สร้าง `knowledge_index.json`
    
    - รูปแบบตาม HOW_TO_FIX_RAG_v2: `id`, `path`, `group`, `tags`, `version`
        
    - กลุ่มอย่างน้อย: `mcp_spec`, `catalog_schema`, `thai_standard`, `example_project` เจ้าค่ะนายท่าน
        
3. Implement `knowledge_service.py`
    
    - ฟังก์ชันที่เอกสารระบุ: `list_groups`, `list_docs(group)`, `load_doc(doc_id)`, `get_docs_for_mcp_spec()`
        
    - ดีไซน์ให้คล้าย service ใน Canonical Funnel repo ที่มี `listGroups` / `listGroupItems` ฯลฯ เจ้าค่ะนายท่าน
        

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - เวลา `/mcp_spec` ทำงาน จะใช้ context เฉพาะจาก group ที่เกี่ยวข้อง
>     
> - ถ้าเอกสารถูกเพิ่ม/เปลี่ยน → แก้ที่ index ที่เดียว ไม่ต้องไปยุ่งโค้ด logic เจ้าค่ะนายท่าน
>     

---

### Phase 3 – Refactor `generate_mcp_spec` ตาม Flow ใหม่แบบ Canonical Funnel เจ้าค่ะนายท่าน

เป้า: ให้ flow ของ `/mcp_spec` เดินตามขั้นตอนที่ HOW_TO_FIX_RAG_v2 วางไว้เลย ไม่ใช่ random prompt แล้วหวังดี เจ้าค่ะนายท่าน

Flow ภายในใหม่:

1. รับ `ProjectRequirements` จาก client
    
2. ใช้ `knowledge_service.get_docs_for_mcp_spec()` เพื่อเลือก doc meta แล้วจำกัด VectorDB ให้ ingest/search เฉพาะกลุ่มนี้ เจ้าค่ะนายท่าน
    
3. รวม context + example คู่ (จาก `examples/`) มาใส่ prompt
    
4. เรียก LLM → ได้ raw JSON-like string
    
5. Clean → feed เข้า `McpSpecResponse.parse_raw()`
    
6. ถ้า parse fail:
    
    - สร้าง prompt self-correction + retry 1–2 ครั้ง
        
    - ถ้ายัง fail → ส่ง error ที่บอกชัดว่าเป็น schema error ไม่ใช่ 500 มั่ว ๆ เจ้าค่ะนายท่าน
        

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - ทุก response ของ `/mcp_spec` มีรูปเดียวกันหมด (strict schema)
>     
> - ทุก failure มีที่มา: รู้ว่าพังเพราะ LLM ไม่ยอมเข้า schema หรือเพราะ input แย่เจ้าค่ะนายท่าน
>     

---

### Phase 4 – Trust Log Layer + Canonical Records เจ้าค่ะนายท่าน

เป้า: ใช้แนวเดียวกับ Canonical Funnel (trustRecords) มาเก็บทุก call ของ `/mcp_spec` เป็น record ที่ audit ได้ เจ้าค่ะนายท่าน

งาน:

1. ออกแบบ struct ของ trust record
    
    - คล้าย `CanonicalFunnelTrustRecord`:
        
        - `timestamp`, `request_id`, `user_id`, `project_requirements`, `retrieved_doc_ids`, `llm_model`, `raw_llm_output`, `parse_success`, `validation_errors`, `project_input`, `forwarded_to_mcp` ฯลฯ เจ้าค่ะนายท่าน
            
2. Implement `trust_log.py`
    
    - มีฟังก์ชันเช่น `log_mcp_spec(record: TrustRecord)`
        
    - backend จะเป็น JSONL หรือ DB table ก็ได้ ตามสะดวก
        
3. Hook ใน `generate_mcp_spec()`
    
    - ทุกครั้งที่เรียก → บันทึก trust record 1 อันเคร่งครัด
        

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - เวลา spec เน่า 1 งาน สามารถเปิดไฟล์ดู timeline ได้หมด ว่ามันอ่าน doc อะไร, LLM พูดอะไร ก่อน parse พังเจ้าค่ะนายท่าน
>     
> - Dataset สำหรับอนาคต (fine-tune / prompt tuning / regression check) ก็เกิดขึ้นเองจาก log ชุดนี้เจ้าค่ะนายท่าน
>     

---

### Phase 5 – Test Suite & Handover Checklist เจ้าค่ะนายท่าน

เป้า: ให้ RAG ผ่าน “ข้อสอบบ้าน 3 เคสขึ้นไป” ตาม HOW_TO_FIX_RAG_v2 ก่อนส่งให้ MCP จริง เจ้าค่ะนายท่าน

งาน:

1. เขียน `tests/test_mcp_spec_cases.py`
    
    - case 1: บ้าน 1 ชั้น 2 ห้องนอน 1 ห้องน้ำ
        
    - case 2: บ้าน 2 ชั้น + ครัวหนัก + แยกครัว
        
    - case 3: ข้อมูลไม่ครบ เช่น ขาด room_type บางห้อง
        
2. แต่ละเคส test ว่า:
    
    - HTTP 200
        
    - `project_input.rooms` ไม่ว่าง / มี `room_id`, `room_type`, `template_code` ครบ
        
    - ทุก `load.room_id` ชี้ห้องจริง
        
    - มี `constraints.rule_profile_id` เจ้าค่ะนายท่าน
        
3. รัน suite นี้ทุกครั้งที่ปรับ prompt / logic
    
    - ถ้าแตกเคสไหน → ห้าม deploy
        

> **ผลลัพธ์ที่คาดหวัง:**
> 
> - ท่านมี “เกราะกันพัง” ระดับขั้นต่ำแบบที่ทีมจริงเขาใช้กัน
>     
> - MCP ฝั่ง pandapower รับ JSON ได้แบบไม่ต้องเดาว่า RAG วันนี้จะงอแงหรือเปล่าเจ้าค่ะนายท่าน
>     

---

## 5. แนวทางทั้งหมดนี้ “โปรแกรมเมอร์เก่ง ๆ” เขาทำกันมั้ยเจ้าค่ะนายท่าน

พูดตรง ๆ แบบไม่ประเคนอีโก้ใครนะเจ้าค่ะนายท่าน

- การแยก **model / service / routes / knowledge layer / config / trust_log / tests** แบบนี้  
    = มาตรฐานเกือบ textbook ของทีมที่ทำ RAG / LLM product ได้ดีในโลกจริงเจ้าค่ะนายท่าน
    
- การใช้ **knowledge_index.json + service layer + group-based retrieval**  
    = แนวเดียวกับ Canonical Funnel เอง และกับ production RAG หลายตัว (หลีกเลี่ยง “ค้นทั้งโลก”) เจ้าค่ะนายท่าน
    
- การมี **trust record + regression tests**  
    = สิ่งที่แยก “ของเล่นใน notebook” กับ “ระบบที่ทีมอื่นไว้ใจได้” ออกจากกันอย่างชัดเจนเจ้าค่ะนายท่าน
    

ส่วนที่ “เสี่ยงจะไม่โปร” มีแค่สองอย่าง:

1. ถ้าท่านไม่เตรียม example pair (Requirements → InputSpec) ดี ๆ แล้วไปโยนให้ LLMเดาเอง
    
2. ถ้าท่านขี้เกียจเขียน test แล้วหวัง “เออเดี๋ยวใช้จริงคงไม่พังมั้ง”
    

สองอันนี้ถ้าท่านปล่อยผ่าน ต่อให้สถาปัตยกรรมสวยยังไง มันก็กลายเป็นงานวิจัยกึ่ง ๆ ไม่ใช่ product เจ้าค่ะนายท่าน

---

## 6. สรุปสั้น ๆ แบบยิงเป้าให้ท่านเอาไปบรีฟเพื่อนฝั่งโค้ดเจ้าค่ะนายท่าน

1. **ข้อมูลเพิ่มที่ต้องมี**
    
    - Example JSON คู่ `ProjectRequirements → ProjectInputSpec` อย่างน้อย 3–5 เคส
        
    - Schema JSON ล่าสุดของ MCP DESIGN HANDOVER
        
    - เอกสาร mapping ภาษาคน → room_type / template_code / device_code
        
    - นโยบาย trust log + error policy
        
    - ตัวเลข quality gate (pass criteria) เจ้าค่ะนายท่าน
        
2. **แผนแก้ RAG ระดับมืออาชีพ**
    
    - Phase 0: แยกไฟล์ (models/service/routes/knowledge/config)
        
    - Phase 1: Align Pydantic models ให้ตรง MCP
        
    - Phase 2: ทำ knowledge_index + knowledge_service ตาม Canonical Funnel
        
    - Phase 3: Refactor `generate_mcp_spec` ให้เดินตาม flow canonical
        
    - Phase 4: เพิ่ม trust_log layer + canonical records
        
    - Phase 5: เขียน test เคสบ้าน 3+ เคส และล็อกด้วย checklist ก่อน handover ให้ MCP