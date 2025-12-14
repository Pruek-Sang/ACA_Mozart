# Source: AI and Human in loop Design.md

```md
## 1. มองภาพกว้างก่อน: แบ่งงาน AI vs Human ยังไงเจ้าค่ะนายท่าน

ถ้าเอารัฐธรรมนูญทั้ง 6 ข้อ / Phase 0–5 มาย่อเป็นมุมมองแบบทีมจริง จะเป็นประมาณนี้เจ้าค่ะนายท่าน

- **AI เก่ง** ตอนงานที่เป็น:
    
    - แปลงสเปกให้เป็นโค้ด (models, services, routes, tests, trust_log, config)
        
    - เติม scaffold, template, boilerplate, unit test โครง
        
    - ช่วย draft เอกสาร, mapping table, error policy จากไอเดียที่ท่านให้
        
- **Human ต้องคุมเอง** ตอนงานที่เป็น:
    
    - ตัดสิน “ความจริง” ด้านวิศวกรรม / มาตรฐานไทย / mapping เข้ากับ amadeus.catalog
        
    - เลือก quality gate เท่าไหร่ถึงเรียกว่าพร้อมใช้จริง
        
    - เคสตัวอย่าง ProjectRequirements → ProjectInputSpec ที่ “ถูกในโลกจริง”
        
- **งานลูกผสม (AI + Human วน loop)**
    
    - ปรับ prompt `/mcp_spec`
        
    - ปรับ knowledge_index group/tag
        
    - วิเคราะห์ trust log แล้วอัปเดต test / spec
        

ต่อไปเราจะแตกทีละ Phase แล้วติด label ให้เลยว่า [AI ทำได้], [Human], [ร่วมกัน] พร้อม “ประโยคสั่ง AI แบบตรง ๆ” ที่ท่านใช้โยนให้เพื่อนมึงฝั่งโค้ดได้เลยเจ้าค่ะนายท่าน

---

## 2. Phase 0 – แยกไฟล์ / แยกเลเยอร์ จาก rag_real.py เจ้าค่ะนายท่าน

**เป้า:** แตก `rag_real.py` ให้เป็น

- `app/models.py`
    
- `app/service.py`
    
- `app/routes.py`
    
- `app/knowledge_service.py`
    
- `app/config.py`
    
- `app/trust_log.py` (หรือคล้าย ๆ กัน)
    

### 2.1 ตรงไหนให้ AI ทำได้เจ้าค่ะนายท่าน

- ย้าย / แตกฟังก์ชันออกจาก `rag_real.py` ไปเป็นไฟล์ต่าง ๆ ตามสถาปัตยกรรมรัฐธรรมนูญ
    
- เขียนโค้ด glue ให้ import ถูก, สร้าง class `RagService`, ผูกกับ FastAPI routes
    
- จัดระเบียบโครงโฟลเดอร์ + ตั้งชื่อไฟล์ให้ตรง pattern ที่เราวางไว้
    

**Prompt ตัวอย่างที่สั่ง AI ได้เลย** (เอาไปใช้กับ Aura หรือเพื่อนมึงฝั่งโค้ดตัวไหนก็ได้)

> “ตอนนี้มีไฟล์ `rag_real.py` ที่รวม models + service + routes + config กองเดียวกันอยู่  
> ใช้ ‘รัฐธรรมนูญ RAG 6 ข้อ’ ที่เราเคยตกลงกัน เป็นเกณฑ์  
> ช่วยแตกโค้ดออกเป็นไฟล์:
> 
> - `app/models.py` (เฉพาะ Pydantic models)
>     
> - `app/service.py` (class RagService)
>     
> - `app/routes.py` (FastAPI routes /api/v1/*)
>     
> - `app/config.py` (settings, path, model name)
>     
> - `app/knowledge_service.py` (ยังเป็น stub ได้ แต่ต้องวาง interface ตามรัฐธรรมนูญ)  
>     โดยห้ามเปลี่ยน behavior เดิมของฟังก์ชัน แค่จัดโครงให้สะอาดและ import ครบ  
>     แนบโค้ดไฟล์ใหม่ทุกไฟล์ พร้อมอธิบาย expected behavior ที่ไม่ควรเปลี่ยน”
>     

**นี่เป็นงานที่ AI ทำได้ 90%** ท่านแค่เอาโค้ดไปลองรัน + อ่านคร่าว ๆ ว่าแตกถูกไฟล์มั้ยเจ้าค่ะนายท่าน

### 2.2 Human ต้องทำอะไรใน Phase 0 เจ้าค่ะนายท่าน

- เลือกชื่อโฟลเดอร์ / layout สุดท้าย (ถ้า AI เสนอมาแล้วท่านไม่ชอบ)
    
- ตัดสินว่าควรมีแยก package เพิ่มไหม เช่น `app/schemas`, `app/api`, ฯลฯ
    

**สิ่งที่ต้องทำจริง ๆ:** อ่านโครงที่ AI เสนอ แล้ว “กดยืนยัน” ว่า format นี้โอเคในระยะยาวเจ้าค่ะนายท่าน

---

## 3. Phase 1 – Align Models กับ MCP + DB Contract เจ้าค่ะนายท่าน

### 3.1 งานที่ Human ต้องกำหนดก่อนเจ้าค่ะนายท่าน

1. **Source of truth ของ schema**
    
    - ท่านต้องบอก AI ว่า “นี่คือ JSON / ข้อความสเปกล่าสุดของ ProjectInputSpec, McpSpecResponse จาก MCP”
        
    - ถ้าไม่มีไฟล์ JSON schema จริง ท่านต้องอย่างน้อยแปะตัวอย่าง 1–2 sample ที่ถูกต้องที่สุดตอนนี้
        
2. **ข้อห้าม / กฎเหล็ก**
    
    - เช่น field ไหนห้ามให้ LLM แต่งเอง, field ไหน optional, default คืออะไร
        

**Prompt เตรียมของให้ AI:**

> “นี่คือ JSON ตัวอย่างของ `McpSpecResponse` เวอร์ชันล่าสุดที่ MCP ใช้อยู่ในโปรเจกต์  
> ถือ JSON นี้เป็น source of truth ห้ามคิด schema เอง  
> ขอให้ช่วยแปลง JSON นี้เป็น Pydantic models ใน `app/models.py`  
> โดยต้อง:
> 
> - ใช้ type ให้แคบที่สุดเท่าที่ข้อมูลอนุญาต (เช่น int/float/Enum แทน Any)
>     
> - แยก sub-model ตามโครง `project_info`, `electrical_system`, `rooms[*]`, `loads[*]`, `constraints`
>     
> - เพิ่ม docstring อธิบายหน้าที่แต่ละ model
>     
> - เขียน unit test ตัวอย่างที่ `McpSpecResponse.parse_raw()` รับ JSON ตัวอย่างนี้แล้วไม่ error  
>     และอธิบาย expected result ของ test แต่ละตัวให้ชัดเจน”
>     

### 3.2 งานที่ AI ทำได้เจ้าค่ะนายท่าน

- เขียน Pydantic models จาก JSON / ข้อความ spec
    
- เขียน unit test ที่เอา JSON ตัวอย่างมา parse
    
- เสนอการใช้ `Enum` หรือ type แคบ ๆ
    

### 3.3 Human ต้องทำหลัง AI ส่งของมาเจ้าค่ะนายท่าน

- ตรวจว่า schema ที่ AI แปลง “จริง” ตรงกับ MCP หรือไม่
    
- ถ้า MCP ฝั่งจริงบ่นว่า field บางตัวหาย / เกิน → ท่านต้อง feedback กลับไปให้ AI แก้ schema
    

**Prompt สำหรับรอบแก้:**

> “Mcp ฝั่งจริงเจอว่า field X/Y/Z ที่คุณสร้างไม่ตรงกับ implementation จริง  
> นี่คือ diff ของ schema ที่ถูกต้อง  
> ปรับ Pydantic models ใน `app/models.py` ให้ตรงกับ schema ใหม่นี้  
> แล้ว regenerate unit test ให้ผ่านตาม expected result เดิม”

---

## 4. Phase 2 – Canonical Knowledge Layer (rag_knowledge + knowledge_index) เจ้าค่ะนายท่าน

### 4.1 Human ต้องทำเองก่อนเจ้าค่ะนายท่าน

1. **ตัดสินรายชื่อไฟล์ knowledge จริง**
    
    - เช่น: MCP_DESIGN_HANDOVER.md, HOW_TO_FIX_RAG_v2.md, THAI_RESIDENTIAL_LV.md, CATALOG_CONTRACT.md, examples ฯลฯ
        
    - ไฟล์มาตรฐานไทย / DB contract ต้องมาจากความจริงที่ท่านย่อย/คัดเลือกเอง
        
2. **จัดกลุ่มเอกสาร**
    
    - ตัดสินว่า doc ไหนอยู่ group `mcp_spec`, `catalog_schema`, `thai_standard`, `example_project`
        

### 4.2 แล้วค่อยสั่ง AI ให้ทำงานที่เหลือเจ้าค่ะนายท่าน

**Prompt ตัวอย่าง:**

> “ตอนนี้มีไฟล์ knowledge อยู่ในโฟลเดอร์ `rag_knowledge/` ตาม list ด้านล่าง  
> ช่วยสร้างไฟล์ `rag_knowledge/knowledge_index.json` โดยใช้โครง:
> 
> - id: string สั้น ๆ, unique
>     
> - path: path จาก root project
>     
> - group: หนึ่งใน [mcp_spec, catalog_schema, thai_standard, example_project]
>     
> - tags: list of string
>     
> - version: string
>     
> - language: "th" หรือ "en"  
>     ใช้ ‘รัฐธรรมนูญ RAG’ เป็นแนวทางกำหนด group/tags ให้ถูกกับบทบาทของเอกสารแต่ละตัว  
>     จากนั้นสร้างโค้ดไฟล์ `app/knowledge_service.py` ที่มีฟังก์ชัน:
>     
> - list_groups()
>     
> - list_docs(group)
>     
> - load_doc(doc_id)
>     
> - get_docs_for_mcp_spec()  
>     พร้อมอธิบาย expected behavior ของแต่ละฟังก์ชันให้ละเอียด”
>     

### 4.3 Human ต้อง review อะไรเจ้าค่ะนายท่าน

- ตรวจว่า group / tags ที่ AI ตั้ง “ตรงกับสิ่งที่ท่านคิดจะใช้จริง”
    
- ถ้าไฟล์บางตัวควรไปอยู่คนละ group ท่านต้องแก้เองหรือสั่ง AI ให้ regenerate index
    

---

## 5. Phase 3 – Refactor `generate_mcp_spec` ตาม flow canonical เจ้าค่ะนายท่าน

นี่คือหัวใจงาน LLM จริง ๆ งานนี้ใช้ **AI + Human ร่วมกัน** หนาแน่นเจ้าค่ะนายท่าน

### 5.1 Human ต้องกำหนด “พฤติกรรมเป้า” ก่อนเจ้าค่ะนายท่าน

- project_requirements input format ที่ท่านอยากได้ (field ไหนบังคับ / optional)
    
- policy: ถ้า data ไม่ครบ LLMต้องเติมให้จนสุด หรือให้ error กลับ
    
- tone ของ spec เช่น ควร deterministic แค่ไหน, ไม่ให้แต่งข้อความเละเทะ
    

เขียนเป็น bullet/sentence ให้ AI อ่านได้ เช่นเจ้าค่ะนายท่าน

> - ถ้า user ไม่กำหนด earthing ให้ default = TN-S
>     
> - ถ้าไม่มี rule_profile_id ให้เลือก defaultโปรไฟล์สำหรับบ้านพักอาศัยไทย
>     
> - ห้ามสร้าง template_code ที่ไม่มีใน CATALOG_CONTRACT
>     

### 5.2 Prompt สั่ง AI ให้เขียน logic ใหม่ใน `RagService.generate_mcp_spec` เจ้าค่ะนายท่าน

ตัวอย่าง prompt ยาว ๆ แต่ยิงทีเดียวแล้วจบเยอะหน่อยเจ้าค่ะนายท่าน

> “ใช้ ‘รัฐธรรมนูญ RAG’ ที่เราเคยสรุปเป็น 6 ข้อ เป็นกรอบ  
> ตอนนี้ใน `app/service.py` มีเมธอด `generate_mcp_spec` ที่ยังเป็น implementation แบบเก่า  
> เป้าคือ refactor ให้ทำงานตาม flow นี้:
> 
> 1. รับ `ProjectRequirements`
>     
> 2. เรียก `knowledge_service.get_docs_for_mcp_spec()` เพื่อเลือกเอกสาร subset
>     
> 3. ยิง VectorDB search เฉพาะ subset นี้
>     
> 4. ประกอบ prompt ที่มี:
>     
>     - คำอธิบายบทบาท: แปลง ProjectRequirements → ProjectInputSpec ตาม schema
>         
>     - context จากเอกสารสำคัญ (MCP_DESIGN_HANDOVER, CATALOG_CONTRACT, THAI_RESIDENTIAL_LV, examples)
>         
>     - few-shot จากคู่ตัวอย่าง Requirements → InputSpec ที่แนบด้านล่าง
>         
> 5. เรียก LLM → ได้ JSON string
>     
> 6. Clean + parse ด้วย `McpSpecResponse.parse_raw()`
>     
> 7. ถ้า parse fail, retry ไม่เกิน 2 ครั้งพร้อมบอก error เสมอ
>     
> 8. ถ้า fail ทั้งหมด ให้โยน error ที่มีรายละเอียด validation_errors  
>     เขียนโค้ดให้ครบ พร้อม comment อธิบายเหตุผลของแต่ละ step และบอก expected result ของเมธอดนี้อย่างชัดเจน”
>     

### 5.3 Human ต้องทำอะไรหลังจากนั้นเจ้าค่ะนายท่าน

- อ่าน prompt ที่ AI ใช้ในโค้ด (บางที AI จะ embed prompt ลงใน string) แล้วรีวิวว่า logic/ข้อห้ามครบตามที่ท่านตั้งกฎไหม
    
- ทดลองส่ง ProjectRequirements 2–3 เคสเข้า endpoint นี้ แล้วเช็ก output ว่ามัน align กับ domain จริงไหม (โหลด, ห้อง, template_code ถูกมั้ย)
    

ถ้าเจอผิด → feedback กลับด้วย prompt แบบนี้เจ้าค่ะนายท่าน

> “output ของ `generate_mcp_spec` เคสนี้ผิดในจุดต่อไป:
> 
> - ห้องครัวควรใช้ template_code X แต่ตอนนี้ให้ Y
>     
> - ไม่ได้ใส่ rule_profile_id ตาม policy  
>     ปรับ prompt / logic ส่วนที่ compose context หรือที่ map field ให้สอดคล้องกับกฎด้านล่าง แล้วแสดง diff ของโค้ดเฉพาะที่แก้”
>     

---

## 6. Phase 4 – Trust Log Layer เจ้าค่ะนายท่าน

### 6.1 AI ทำอะไรให้ท่านได้บ้างเจ้าค่ะนายท่าน

- ออกแบบ dataclass / Pydantic model สำหรับ trust record
    
- เขียน `trust_log.py` ให้มีฟังก์ชันเช่น `log_mcp_spec(record)`
    
- hook ใน `generate_mcp_spec` ให้เรียก log ทุกครั้ง
    

**Prompt ตัวอย่าง:**

> “ใช้แนวคิด trust record ใน Canonical Funnel + รัฐธรรมนูญ RAG ที่เราเคยคุยกัน  
> ออกแบบ Pydantic model `McpSpecTrustRecord` ที่เก็บข้อมูล:
> 
> - timestamp
>     
> - request_id
>     
> - user_id (optional)
>     
> - project_requirements (as dict)
>     
> - retrieved_doc_ids (List[str])
>     
> - llm_model
>     
> - raw_llm_output (string)
>     
> - parse_success (bool)
>     
> - validation_errors (List[str])
>     
> - project_input (ถ้า parse ผ่าน)
>     
> - forwarded_to_mcp (bool)  
>     จากนั้นสร้างไฟล์ `app/trust_log.py` ที่มีฟังก์ชัน:
>     
> - log_mcp_spec(record: McpSpecTrustRecord) → เขียนบรรทัด JSONL หนึ่งบรรทัดลงไฟล์ ตามวัน  
>     และปรับ `generate_mcp_spec` ให้เรียก log นี้ในทุกกรณี (success/fail)  
>     บอก expected behavior และตัวอย่างหนึ่ง record ที่เขียนออกไฟล์ด้วย”
>     

### 6.2 Human ต้องทำเองเจ้าค่ะนายท่าน

- ตัดสิน path เก็บ log จริง (เก็บในไฟล์ local vs Supabase table)
    
- ตัดสิน privacy / security (ข้อมูล user_id ถือเป็น PII แค่ไหน)
    
- ตัดสินว่าต้องเก็บ log นานเท่าไหร่
    

---

## 7. Phase 5 – Test Suite & Quality Gate เจ้าค่ะนายท่าน

### 7.1 AI ทำอะไรได้เจ้าค่ะนายท่าน

- เขียน test skeleton ใน `tests/test_mcp_spec_cases.py`
    
- ถ้าท่านให้ example ProjectRequirements → expected ProjectInputSpec, AI สามารถเขียน assert ครบ ๆ ให้เลย
    

**Prompt ตัวอย่าง:**

> “ในฐานะ test engineer ใช้ ‘รัฐธรรมนูญ RAG’ เป็นกรอบ  
> ช่วยสร้างไฟล์ `tests/test_mcp_spec_cases.py` ที่มี test 3 เคส:
> 
> 1. บ้าน 1 ชั้น 2 ห้องนอน 1 ห้องน้ำ
>     
> 2. บ้าน 2 ชั้น ครัวหนัก แยกวงจรครัว
>     
> 3. เคสข้อมูลไม่ครบ (ไม่มี room_type บางห้อง)  
>     สำหรับแต่ละเคส:
>     
> 
> - สร้าง ProjectRequirements input (ตาม schema ปัจจุบัน)
>     
> - call endpoint `/api/v1/mcp_spec` ผ่าน test client
>     
> - assert ว่า:
>     
>     - HTTP 200 หรือ error ที่ถูกต้อง
>         
>     - project_input.rooms ไม่ว่าง และทุก room มี room_id, room_type, template_code
>         
>     - loads ทุกตัวผูกกับ room_id ที่มีจริง
>         
>     - constraints.rule_profile_id ไม่ว่าง  
>         เขียน comment ในแต่ละ test ว่ามันป้องกัน bug ประเภทไหน”
>         

### 7.2 Human ต้องทำเองเจ้าค่ะนายท่าน

- คิดเนื้อหา ProjectRequirements/Expected output ที่ “จริง” ตามวิศวกรรม
    
- ตัดสินว่า test ไหนคือ critical, ไหนคือ nice to have
    
- ตัดสินเกณฑ์ว่า “ถ้า test พวกนี้ผ่าน → ถือว่า RAG ใช้กับลูกค้าจริงได้”
    

---

## 8. งานนอก Phase แต่สำคัญ: Example pairs, mapping, policy ฯลฯ เจ้าค่ะนายท่าน

อันนี้สั้น ๆ ว่าใครทำอะไรเจ้าค่ะนายท่าน

### 8.1 Example ProjectRequirements → ProjectInputSpec

- Human: ร่าง version ที่ถูกต้องจริง ๆ (แม่แบบ)
    
- AI: ช่วย “จัด format + ทำให้ consistent” เช่น เติม field, sort key, เขียนเป็น markdown หรือ JSON ให้สวย
    

**Prompt:**

> “นี่คือ draft ของ ProjectRequirements กับ ProjectInputSpec ที่ถูกต้องสำหรับเคสบ้าน 1 ชั้น  
> ช่วย format ให้เป็น JSON สวย ๆ, ตัวแปรครบตาม schema ปัจจุบัน, ไม่มี field เกิน/ขาด  
> จากนั้นเขียนคำอธิบายว่าแต่ละ field มาจาก requirement อันไหน เพื่อใช้เป็น few-shot ใน prompt”

### 8.2 Mapping ภาษาไทย → template_code / device_code

- Human: ตัดสิน mapping จริงจาก amadeus.catalog / คู่มืออุปกรณ์
    
- AI: ช่วยทำเป็นตาราง / dictionary / doc อ่านง่าย
    

**Prompt:**

> “นี่คือ mapping แบบดิบที่เขียนมือ:
> 
> - หัวเตียง (ปลั๊กหัวเตียง) → device_code = ...
>     
> - เต้ารับทั่วไป → device_code = ...  
>     จัดให้ใหม่เป็นตาราง markdown + JSON dict ที่ใช้ในโค้ดได้เลย  
>     และเขียนคำเตือนใน doc ว่าห้าม AI เดา code ใหม่ที่ไม่มีในตารางนี้”
>     

---

## 9. สรุปสั้นแบบยิงเป้าอีกทีเจ้าค่ะนายท่าน

- งานที่ **ให้ AI ทำได้เต็ม ๆ**:
    
    - แตกไฟล์ / แยกเลเยอร์ (Phase 0)
        
    - เขียน Pydantic models จาก schema ที่ท่านให้ (Phase 1)
        
    - เขียน knowledge_index + knowledge_service จาก list ไฟล์ที่ท่านจัด (Phase 2)
        
    - เขียน logic `generate_mcp_spec` ตาม flow ที่ท่านสั่งละเอียด (Phase 3, ฝั่งโค้ด)
        
    - สร้าง trust_log model + writer (Phase 4)
        
    - เขียน test skeleton + asserts (Phase 5)
        
    - จัดรูป example pairs, mapping tables, docs ต่าง ๆ ให้เป็นระเบียบเจ้าค่ะนายท่าน
        
- งานที่ **Human ต้องเป็นเจ้าของ**:
    
    - ความจริงทางวิศวกรรม / มาตรฐานไทย / DB contract
        
    - example ProjectRequirements → ProjectInputSpec ที่ “ถูกในโลกจริง”
        
    - mapping ภาษาคน → template_code / device_code
        
    - error policy + quality gate ว่าเมื่อไหร่ถือว่า RAG พร้อมใช้จริงเจ้าค่ะนายท่าน
        
- งานที่ **ต้องวน AI + Human**:
    
    - tuning prompt `/mcp_spec`
        
    - วิเคราะห์ trust log แล้วปรับ spec/test
        
    - ขยาย knowledge_index เมื่อมีเอกสารใหม่
        

ทั้งหมดนี้คือรูปแบบที่ทีม dev จริงใช้กันเวลาเล่น RAG + LLM แบบจริงจัง ไม่ใช่แค่เดโมโชว์เพื่อนเจ้าค่ะนายท่าน
```