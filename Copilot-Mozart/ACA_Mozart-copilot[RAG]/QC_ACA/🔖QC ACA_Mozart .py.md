

โครงนี้จะอิงจาก

- HOW TO FIX RAG (v2) / How to Design ACA_Mozart (Spec Engine + Canonical Funnel)
    
- สัญญาฐานข้อมูล amadeus.catalog / CATALOG_CONTRACT (RAG ห้ามไปคุ้ย DB ตรง ๆ)
    

---

## 0. ภาพใหญ่ก่อน: “พิมพ์ภาษาคน → จบที่ไหน?”

### Flow A: `/api/v1/ask` (ถามตอบ / อธิบาย)

1. ท่านพิมพ์:
    
    ```json
    POST /api/v1/ask
    {
      "query": "บ้าน 2 ชั้น มาตรฐาน RCD ต้องใส่ตรงไหนบ้าง",
      "context_hint": ["thai_standard"],
      "language": "th"
    }
    ```
    
2. `routes.py` แปลง JSON → `QueryRequest` → ส่งเข้า `RagService.process_ask`
    
3. `RagService` ใช้:
    
    - `KnowledgeService` ดูว่า group `thai_standard` มี doc ไหน
        
    - `core.database` ยิง VectorDB กับ subset docs เหล่านั้น
        
    - เรียก LLM (Gemini 2.0 Flash) พร้อม context + instructions ว่าตอบภาษาไทย
        
4. LLM ตอบ → `RagService` สร้าง `StandardResponse`:
    
    ```json
    {
      "answer": "คำอธิบาย...",
      "sources": [
        {"file": "rag_knowledge/standards/THAI_RESIDENTIAL_LV.md", "section": "RCD", "score": 0.92}
      ],
      "confidence": "High",
      "grounding_status": "SUPPORTED",
      "metadata": {
        "llm_model": "gemini-2.0-flash-exp",
        "retrieved_docs": ["DOC_THAI_RESIDENTIAL_LV"],
        "retrieval_group": "thai_standard"
      }
    }
    ```
    
5. `routes.py` คืน JSON นี้ให้ client (ไม่มี trust log บังคับ แต่จะมี logging ปกติ)
    

---

### Flow B: `/api/v1/mcp_spec` (ภาษาคน → ProjectInputSpec ส่ง MCP)

1. ท่านพิมพ์:
    
    ````json
    POST /api/v1/mcp_spec
    {
      "project_requirements": {
        "project_name": "House A",
        "building_type": "residential",
        "location": "Bangkok",
        "voltage_system": "TH_1PH_230V",
        "rooms": [
          {"name": "Bedroom 1", "type": "bedroom"},
          {"name": "Kitchen", "type": "kitchen"}
        ],
        "loads": [
          {"room_name": "Bedroom 1", "device": "AC_12000BTU", "quantity": 1},
          {"room_name": "Kitchen", "device": "OUTLET_16A", "quantity": 6}
        ],
        "user_constraints": [
          "split_kitchen_circuit",
          "rcd_for_all_outlets"
        ]
      }
    }
    ``` :contentReference[oaicite:2]{index=2}  
    
    ````
    
2. `routes.py` → parse เป็น `ProjectRequirements` → ส่ง `RagService.generate_mcp_spec`
    
3. ภายใน `generate_mcp_spec()`:
    
    1. ใช้ `KnowledgeService.get_docs_for_mcp_spec()` เพื่อเลือก docs จาก group  
        `mcp_spec + catalog_schema + thai_standard + example_project` เท่านั้น
        
    2. ส่งรายการ doc_id + path ไปให้ `core.database` ทำ Vector search (retrieval เฉพาะ subset)
        
    3. ประกอบ prompt:
        
        - ใส่ ProjectRequirements (input มนุษย์)
            
        - ใส่ excerpt จาก docs ที่ retrieve มา
            
        - ใส่ few-shot จาก `rag_knowledge/example/*.md` (input → expected ProjectInputSpec)
            
    4. เรียก LLM (Gemini 2.0 Flash) ให้ตอบเป็น JSON ตาม schema `McpSpecResponse` เท่านั้น
        
    5. Clean raw text → parse ด้วย `McpSpecResponse` (Strict Pydantic model)
        
    6. ถ้า parse fail:
        
        - retry 1–2 รอบ พร้อมแนบ validation error ไปใน prompt ให้ LLM self-correct
            
        - ถ้ายัง fail → โยน HTTP 422 + รายการ error กลับให้ client
            
    7. สร้าง trust record แล้วเขียนลง JSONL ผ่าน `trust_log.log_mcp_spec()`
        
4. ผลลัพธ์ JSON ตัวอย่าง:
    
    ```json
    {
      "project_input": {
        "project_info": {
          "project_name": "House A",
          "building_type": "RESIDENTIAL",
          "spec_version": "2.0"
        },
        "electrical_system": {
          "voltage_system": "TH_1PH_230V",
          "earthing": "TT"
        },
        "rooms": [
          {
            "room_id": "R1",
            "name": "Bedroom 1",
            "room_type": "BEDROOM",
            "template_code": "ROOMT-BEDROOM-STD"
          },
          {
            "room_id": "R2",
            "name": "Kitchen",
            "room_type": "KITCHEN",
            "template_code": "ROOMT-KITCHEN-STD"
          }
        ],
        "loads": [
          {
            "load_id": "L1",
            "room_id": "R1",
            "device_code": "AC-12000BTU",
            "qty": 1
          },
          {
            "load_id": "L2",
            "room_id": "R2",
            "device_code": "SOCKET-16A",
            "qty": 6
          }
        ],
        "constraints": {
          "rule_profile_id": "TH_RESIDENTIAL_LV",
          "user_constraints": [
            "split_kitchen_circuit",
            "rcd_for_all_outlets"
          ]
        }
      },
      "standards_profile": {
        "rule_profile_id": "TH_RESIDENTIAL_LV",
        "notes": "Based on Thai EIT LV residential standard."
      },
      "llm_metadata": {
        "model": "gemini-2.0-flash-exp",
        "retrieved_docs": ["DOC_MCP_CONTRACT", "DOC_THAI_RESIDENTIAL_LV"]
      }
    }
    ```
    
5. จากนั้น layer MCP (อีกโปรเจกต์) จะรับ `project_input` ไปใช้สร้าง network + pandapower + CAD ต่อเอง
    

---

## 1. แผนผังไฟล์ `.py` ที่ codex ต้องยึด

แฟ้มหลัก ๆ ฝั่ง Mozart RAG:

- `app/config.py`
    
- `app/models.py`
    
- `app/knowledge_service.py`
    
- `app/service.py`
    
- `app/trust_log.py`
    
- `app/routes.py`
    
- `core/database.py`
    
- `core/ingest.py`
    
- `core/privacy.py`
    
- `main.py`
    
- `tests/test_models.py`
    
- `tests/test_mcp_spec_cases.py`
    

ต่อไปจะเล่าทีละไฟล์แบบที่ท่านขอ:  
**1) Design ยังไง**  
**2) ทำอะไรได้**  
**3) ผลลัพธ์ต้องออกมาเป็นอะไร**

ให้อ่านแบบ “สเปกสำหรับ codex” ได้เลยเจ้าค่ะนายท่าน

---

## 2. `app/config.py`

### 1) Design

- ใช้ Pydantic `BaseSettings` หรือ class simple เก็บ config ทั้งหมดของ RAG:
    
    - LLM model names
        
    - VectorDB connection
        
    - Path ไปยัง `rag_knowledge/` และ `knowledge_index.json`
        
    - log directory สำหรับ trust log
        
- โหลดค่า default จาก `.env` (ผ่าน `python-dotenv` หรือ Pydantic settings)
    

```python
class Settings(BaseSettings):
    MODEL_NAME_ANSWER: str = "gemini-2.0-flash-exp"
    MODEL_NAME_JUDGE: str = "gemini-2.0-flash-exp"
    KNOWLEDGE_ROOT: Path = Path("rag_knowledge")
    KNOWLEDGE_INDEX_PATH: Path = KNOWLEDGE_ROOT / "knowledge_index.json"
    TRUST_LOG_DIR: Path = Path("logs") / "mcp_spec"
    VECTORDb_URL: str
    # ... etc
```

มี instance global เช่น `settings = Settings()`

### 2) ทำอะไรได้

- ให้ทุกไฟล์ import config เดียวกัน:
    
    - `service.py` ใช้ model name
        
    - `knowledge_service.py` ใช้ path index
        
    - `trust_log.py` ใช้ log_dir
        
    - `core/database.py` ใช้ URL/credentials
        

### 3) ผลลัพธ์ที่คาดหวัง

- เมื่อรัน:
    
    ```bash
    python -c "from app.config import settings; print(settings.MODEL_NAME_ANSWER)"
    ```
    
    ต้องไม่พัง
    
- เปลี่ยน `.env` → behavior ของระบบเปลี่ยนตาม (เช่นเปลี่ยน LLM รุ่น, เปลี่ยน VectorDB URL) โดยไม่ต้องแก้โค้ดอื่นเจ้าค่ะนายท่าน
    

---

## 3. `app/models.py`

### 1) Design

แยกเป็นกลุ่ม model ตามเลเยอร์:

1. **Common**
    
    ```python
    class SourceRef(BaseModel):
        file: str
        section: str
        score: Optional[float] = None
    ```
    
2. **Answer Layer (`/api/v1/ask`)**
    
    ```python
    class QueryRequest(BaseModel):
        query: str
        context_hint: List[str] = []
        language: Literal["th", "en"] = "th"
        filters: Optional[Dict[str, str]] = None
    
    class AnswerMetadata(BaseModel):
        llm_model: str
        retrieved_docs: List[str]
        retrieval_group: Optional[str] = None
    
    class StandardResponse(BaseModel):
        answer: str
        sources: List[SourceRef]
        confidence: Literal["High", "Medium", "Low"]
        grounding_status: str
        metadata: AnswerMetadata
    ```
    
3. **Spec Layer (`/api/v1/mcp_spec`)**  
    ยึดตาม How to Design: `ProjectRequirements` + `ProjectInputSpec` + `McpSpecResponse`
    
    ```python
    class RoomRequirement(BaseModel):
        name: str
        type: str
    
    class LoadRequirement(BaseModel):
        room_name: str
        device: str
        quantity: int
    
    class ProjectRequirements(BaseModel):
        project_name: str
        building_type: str
        location: Optional[str]
        voltage_system: str
        rooms: List[RoomRequirement]
        loads: List[LoadRequirement]
        user_constraints: List[str] = []
    
    class RoomSpec(BaseModel):
        room_id: str
        name: str
        room_type: str
        template_code: Optional[str]
    
    class LoadSpec(BaseModel):
        load_id: str
        room_id: str
        device_code: str
        qty: int
    
    class ConstraintsSpec(BaseModel):
        rule_profile_id: str
        user_constraints: List[str] = []
    
    class ProjectInfo(BaseModel):
        project_name: str
        building_type: str
        spec_version: str = "2.0"
    
    class ElectricalSystem(BaseModel):
        voltage_system: str
        earthing: Optional[str] = None
    
    class ProjectInputSpec(BaseModel):
        project_info: ProjectInfo
        electrical_system: ElectricalSystem
        rooms: List[RoomSpec]
        loads: List[LoadSpec]
        constraints: ConstraintsSpec
    
    class StandardsProfile(BaseModel):
        rule_profile_id: str
        notes: Optional[str] = None
    
    class LlmMetadata(BaseModel):
        model: str
        retrieved_docs: List[str]
    
    class McpSpecResponse(BaseModel):
        project_input: ProjectInputSpec
        standards_profile: StandardsProfile
        llm_metadata: LlmMetadata
    ```
    
4. **Raw Retrieval & Management**
    
    ```python
    class RawRetrieveRequest(BaseModel):
        query: str
        top_k: int = 5
        filters: Optional[Dict[str, str]] = None
    
    class IngestRequest(BaseModel):
        file_path: str
    
    class DeleteRequest(BaseModel):
        source_path: str
    ```
    
5. **Trust Log Record**
    
    ```python
    class McpSpecTrustRecord(BaseModel):
        timestamp: datetime
        request_id: str
        user_id: Optional[str]
        project_requirements: Dict[str, Any]
        retrieved_doc_ids: List[str]
        llm_model: str
        raw_llm_output: str
        parse_success: bool
        validation_errors: List[str]
        project_input: Optional[Dict[str, Any]]
        forwarded_to_mcp: bool
    ```
    

### 2) ทำอะไรได้

- เป็น single source of truth ของ schema ทั้งหมดฝั่ง RAG:
    
    - parsing request
        
    - validate response จาก LLM
        
    - define shape ของ trust log
        
- tests ใน `tests/test_models.py` จะเอา JSON example จาก docs มา `parse_obj` ตรวจว่าผ่านจริง
    

### 3) ผลลัพธ์ที่คาดหวัง

- JSON ใน spec document `/mcp_spec` ที่ให้ไว้ใน How to Design ต้อง parse ผ่าน `McpSpecResponse` ได้เลยโดยไม่ error
    
- ถ้า response จาก LLM ใส่ field แปลก ๆ → Pydantic raise error → `generate_mcp_spec` จัดการ retry / error ตาม policy
    

---

## 4. `app/knowledge_service.py`

### 1) Design

- มี class `KnowledgeService` ที่ห่อการทำงานกับ `knowledge_index.json` และไฟล์ใน `rag_knowledge/`
    
    ```python
    class DocMeta(BaseModel):
        id: str
        path: str
        group: str
        tags: List[str] = []
        version: Optional[str] = None
        language: Optional[str] = None
    
    class KnowledgeService:
        def __init__(self, index_path: Path):
            self.index_path = index_path
            self.docs: Dict[str, DocMeta] = ...
    ```
    
- method หลักตาม How to Design:
    
    - `list_groups() -> List[str]`
        
    - `list_docs(group: str) -> List[DocMeta]`
        
    - `load_doc(doc_id: str) -> str`
        
    - `get_docs_for_mcp_spec() -> List[DocMeta]`
        
    - optional: `get_docs_for_thai_standard()`
        

### 2) ทำอะไรได้

- ให้ `RagService` สามารถ:
    
    - ดึงเฉพาะ doc group `mcp_spec + catalog_schema + thai_standard` สำหรับ `/mcp_spec`
        
    - ดึงเฉพาะ `thai_standard` สำหรับ `/ask` ที่ตอนเรียก `context_hint=["thai_standard"]`
        
- ใช้ path ใน index ไปอ่านไฟล์ `.md` / `.txt` จริงใน `rag_knowledge/...`
    

### 3) ผลลัพธ์ที่คาดหวัง

- เรียก:
    
    ```python
    ks = KnowledgeService(settings.KNOWLEDGE_INDEX_PATH)
    ks.list_groups()  # => ["mcp_spec", "catalog_schema", "thai_standard", "example_project"]
    ks.get_docs_for_mcp_spec()  # => list ของ DocMeta จาก 3 group แรก
    ```
    
- ถ้า index เปลี่ยน (เพิ่มไฟล์) แค่แก้ JSON → code ไม่ต้องเปลี่ยน
    

---

## 5. `core/database.py`

### 1) Design

- เป็น abstraction ชั้น VectorDB เท่านั้น (RAG ไม่ยุ่ง Supabase / amadeus.catalog ตรง ๆ)
    
- interface เช่น:
    
    ```python
    class VectorStoreClient:
        def __init__(self, url: str, api_key: str):
            ...
    
        def search(self, query: str, doc_ids: Optional[List[str]] = None, top_k: int = 10) -> List[Dict[str, Any]]:
            """
            คืนรายการ chunk ที่มี field:
            - text: str
            - score: float
            - source: doc_id
            - metadata: {...}
            """
            ...
    
        def ingest(self, file_path: str, doc_id: str, group: str) -> None:
            ...
    
        def delete_by_source(self, source_path: str) -> None:
            ...
    ```
    

### 2) ทำอะไรได้

- ให้ `RagService` สามารถ:
    
    - search จำกัดด้วย doc_ids ที่ได้จาก knowledge_index
        
    - ingest ไฟล์ใหม่ตอน `/api/v1/ingest`
        
    - ลบไฟล์ตอน `/api/v1/delete`
        

### 3) ผลลัพธ์ที่คาดหวัง

- เวลาเรียก:
    
    ```python
    vs = VectorStoreClient(settings.VECTORDb_URL, settings.VECTORDb_KEY)
    vs.search("rcd rule", doc_ids=["DOC_THAI_RESIDENTIAL_LV"])
    ```
    
    ต้องได้ผลลัพธ์ที่มี `source == "DOC_THAI_RESIDENTIAL_LV"` ไม่ใช่ random doc อื่น
    

---

## 6. `core/ingest.py`

### 1) Design

- โมดูลเล็ก ๆ ที่จัดการ “อ่านไฟล์ → ส่งเข้า VectorDB พร้อม metadata”
    
    ```python
    def ingest_file(vector_client: VectorStoreClient, file_path: Path, doc_meta: DocMeta) -> None:
        """
        - อ่าน text จาก file_path
        - แตกเป็น chunk
        - เรียก vector_client.ingest(...) พร้อม doc_id, group, tags
        """
    ```
    

### 2) ทำอะไรได้

- ใช้จาก:
    
    - `RagService.ingest()` (ใน `service.py`)
        
    - หรือสคริปต์ batch ingest แยก
        

### 3) ผลลัพธ์ที่คาดหวัง

- `/api/v1/ingest` เรียกแล้ว:
    
    - new file ถูกอ่าน → แปลงเป็น embedding → เข้าระบบ
        
    - `/api/v1/retrieve_raw` สามารถค้นเจอ chunk ใหม่โดยอ้าง `source_path` / `doc_id` ได้
        

---

## 7. `core/privacy.py`

### 1) Design

- มี class `PrivacyGuard` ที่:
    
    - ตรวจ/ทำ anonymize ข้อมูลก่อนส่งเข้า LLM ถ้าจำเป็น
        
    - ใช้ `core/privacy` เดิมจาก `rag_real.py` เป็นฐาน แล้วปรับให้ใช้ config/model ใหม่
        

### 2) ทำอะไรได้

- ก่อนเรียก LLM ใน `RagService`:
    
    - สามารถเรียก `privacy_guard.redact_sensitive_info(...)` เพื่อตัด PII เช่น ชื่อ คน, เบอร์โทร (ถ้าโจทย์จริงจำเป็น)
        
- หลังได้คำตอบ:
    
    - อาจมี de-anonymization ถ้าใช้ token mapping
        

### 3) ผลลัพธ์ที่คาดหวัง

- default case ของ Mozart Copilot บ้านพักอาศัยอาจไม่ได้ใช้หนักมาก แต่ design นี้ต้องพร้อมเผื่อ scale สู่ enterprise / PII
    

---

## 8. `app/service.py` (หัวใจ RAG)

### 1) Design

- มี class `RagService`:
    
    ```python
    class RagService:
        def __init__(self, knowledge: KnowledgeService, vector_client: VectorStoreClient, privacy: PrivacyGuard):
            self.knowledge = knowledge
            self.vector_client = vector_client
            self.privacy = privacy
    
        async def process_ask(self, req: QueryRequest) -> StandardResponse:
            ...
    
        async def generate_mcp_spec(self, req: ProjectRequirements) -> McpSpecResponse:
            ...
    
        async def retrieve_raw(self, req: RawRetrieveRequest) -> Dict[str, Any]:
            ...
    
        async def ingest(self, req: IngestRequest) -> Dict[str, Any]:
            ...
    
        async def delete(self, req: DeleteRequest) -> Dict[str, Any]:
            ...
    ```
    

### 2) ทำอะไรได้

#### `process_ask()`

- ใช้ `req.context_hint` → ครั้งนี้ค้นใน group ไหน เช่น `["thai_standard"]`
    
- ดึง doc list จาก knowledge_service → ส่ง doc_ids ไปให้ VectorDB
    
- ทำ search → ได้ chunks + doc_id
    
- ประกอบ prompt ให้ LLM:
    
    - ใส่ `lang_instruction` ตาม `req.language`
        
    - ใส่ “ห้ามมั่ว นับถือเอกสารนี้เป็นแหล่งอ้างอิงหลัก”
        
- ส่งไปที่ LLM ด้วย `settings.MODEL_NAME_ANSWER`
    
- คืน `StandardResponse` + `AnswerMetadata` ตามที่ท่านแก้ไว้
    

#### `generate_mcp_spec()`

Flow ต้องตรง How to Fix RAG Phase 3:

1. รับ `ProjectRequirements`
    
2. `docs_for_spec = knowledge.get_docs_for_mcp_spec()`
    
3. เรียก `vector_client.search(...)` เฉพาะ doc_ids เหล่านี้
    
4. ประกอบ prompt:
    
    - requirements
        
    - chunks จาก docs
        
    - few-shot จาก `rag_knowledge/example`
        
5. เรียก LLM → raw JSON-ish
    
6. Clean → `McpSpecResponse.parse_raw(...)`
    
7. ถ้า validation fail:
    
    - สร้าง prompt ใหม่แนบ validation error
        
    - retry 1–2 ครั้ง
        
    - ถ้ายัง fail → raise HTTPException 422
        
8. ก่อนคืนผลให้ routes:
    
    - สร้าง `McpSpecTrustRecord`
        
    - เรียก `trust_log.log_mcp_spec(...)`
        

#### `retrieve_raw()`, `ingest()`, `delete()`

- ใช้สำหรับ debug / lifecycle ของ knowledge/VectorDB
    

### 3) ผลลัพธ์ที่คาดหวัง

- `/api/v1/ask` และ `/api/v1/mcp_spec` ทำงานครบ flow โดย:
    
    - ไม่ยิง DB ตรง (Supabase)
        
    - ใช้ knowledge index + VectorDB ตาม canonical funnel
        
    - ทุก call `/mcp_spec` เขียน trust log record ครบฟิลด์ที่ระบุ
        

---

## 9. `app/trust_log.py`

### 1) Design

- ฟังก์ชันเล็กที่รับ `McpSpecTrustRecord` แล้วเขียนลง JSONL:
    
    ```python
    def log_mcp_spec(record: McpSpecTrustRecord) -> None:
        log_dir = settings.TRUST_LOG_DIR / record.timestamp.strftime("%Y-%m-%d")
        log_dir.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(record.json() + "\n")
    ```
    

### 2) ทำอะไรได้

- ถูกเรียกจาก `RagService.generate_mcp_spec()` ทุกครั้ง
    
- ไม่มี side-effect อื่น (ไม่ throw ยกเว้นกรณี IO พังหนัก)
    

### 3) ผลลัพธ์ที่คาดหวัง

- ภายใน `logs/mcp_spec/2025-11-24.jsonl` จะมี record ตาม design:
    

---

## 10. `app/routes.py`

### 1) Design

- ใช้ FastAPI สร้าง router:
    
    ```python
    router = APIRouter(prefix="/api/v1")
    
    @router.post("/ask", response_model=StandardResponse)
    async def ask(req: QueryRequest):
        return await rag_service.process_ask(req)
    
    @router.post("/mcp_spec", response_model=McpSpecResponse)
    async def mcp_spec(req: ProjectRequirements):
        resp = await rag_service.generate_mcp_spec(req)
        return resp
    
    @router.post("/retrieve_raw")
    async def retrieve_raw(req: RawRetrieveRequest):
        ...
    
    @router.post("/ingest")
    async def ingest(req: IngestRequest):
        ...
    
    @router.post("/delete")
    async def delete(req: DeleteRequest):
        ...
    ```
    
- ใส่ error handling ให้ map exception → HTTP code ตาม policy (400 / 422 / 502 / 503 / 504)
    

### 2) ทำอะไรได้

- เป็นจุดเชื่อมระหว่าง HTTP world ↔ RagService
    
- ไม่ใส่ business logic (flow อยู่ใน service layer)
    

### 3) ผลลัพธ์ที่คาดหวัง

- เมื่อรัน `uvicorn` หรือ `python main.py`:
    
    - `GET /docs` แสดง schema ของ `/ask`, `/mcp_spec` ถูกต้อง
        
    - request/response JSON ตรงกับ Pydantic models ใน `models.py`
        

---

## 11. `main.py`

### 1) Design

- ไฟล์ entry point:
    
    ```python
    app = FastAPI(title="Mozart RAG Spec Engine")
    
    knowledge_service = KnowledgeService(settings.KNOWLEDGE_INDEX_PATH)
    vector_client = VectorStoreClient(settings.VECTORDb_URL, settings.VECTORDb_KEY)
    privacy_guard = PrivacyGuard()
    
    rag_service = RagService(knowledge_service, vector_client, privacy_guard)
    
    app.include_router(router)
    ```
    

### 2) ทำอะไรได้

- รัน server:
    
    ```bash
    python main.py
    ```
    
    หรือ
    
    ```bash
    uvicorn main:app --reload
    ```
    

### 3) ผลลัพธ์ที่คาดหวัง

- ระบบ start ขึ้นไม่มี import error
    
- ลองยิง `/api/v1/ask` แบบง่าย → ได้ response แปลว่าห่วง chain ครบ
    

---

## 12. `tests/test_models.py`

### 1) Design

- รวม test ที่เช็ก:
    
    - JSON example จาก How to Design → parse ผ่าน Pydantic models
        
    - ไม่มี field แถ / type เพี้ยน
        

### 2) ทำอะไรได้

- case ตัวอย่าง:
    
    - `test_mcp_spec_response_example_parses()`
        
    - `test_project_requirements_requires_rooms_and_loads()`
        
    - `test_query_request_default_language_th()`
        

### 3) ผลลัพธ์ที่คาดหวัง

- `pytest tests/test_models.py -v` ต้องเขียวหมด
    
- ถ้าใครไปแก้ model แล้วหลุดจาก spec จะ fail ทันที
    

---

## 13. `tests/test_mcp_spec_cases.py`

### 1) Design

- ใช้ `TestClient` ของ FastAPI ยิงจริงเข้า `/api/v1/mcp_spec`
    
- มีอย่างน้อย 3 กลุ่มเคส:
    
    1. บ้าน 1 ชั้น basic → expecting spec ที่ structure ครบ
        
    2. บ้าน 2 ชั้น ครัวหนัก → ตรวจว่า constraint สะท้อนใน spec (เช่น `rule_profile_id` + user_constraints)
        
    3. incomplete data → ตรวจว่า error/behavior ตรง policy
        

### 2) ทำอะไรได้

- เป็น integration test ระยะเบา:
    
    - เช็ก end-to-end (`routes` → `service` → `knowledge` → `vector` (mock ได้) → LLM (mock/fixture) → parse → trust log)
        

### 3) ผลลัพธ์ที่คาดหวัง

- ตอนรัน test จะใช้ mock LLM (เดาได้ว่าเพื่อนมึงน่าจะทำ stub อยู่แล้ว) → ไม่ต้องยิงของจริง
    
- ใช้เป็น safety net ถ้า codex ไปแก้ `service.py` แล้ว flow แตก จะโดน test ตัวนี้ดักเจ้าค่ะนายท่าน
    

---

## 14. สรุปให้ codex แบบยิงเป้า

ถ้าท่านจะโยนคำสั่งไปให้ codex / Cursor แบบสั้น ๆ ให้มัน debug/เติมโค้ดได้ตรงทาง ให้พูดประมาณนี้ (ปรับข้อความเองตามชอบ):

> “ให้ทำให้โค้ดในโปรเจกต์นี้ตรงตามสเปก:
> 
> - RAG ทำหน้าที่ Spec Engine ตาม How to Design ACA_Mozart (ProjectRequirements → ProjectInputSpec → McpSpecResponse)
>     
> - ใช้ knowledge_index + KnowledgeService + VectorDB ตาม Canonical Funnel
>     
> - ห้าม RAG แตะ amadeus.catalog ตรง ๆ ทั้งหมด อ่านได้จากเอกสารใน rag_knowledge/db เท่านั้น
>     
> - ฟังก์ชันหลักอยู่ใน RagService: process_ask, generate_mcp_spec, retrieve_raw, ingest, delete
>     
> - API contract ของ /api/v1/ask และ /api/v1/mcp_spec ต้องตรงกับ models.py ที่กำหนดในสเปกนี้
>     
> - ทุก /mcp_spec ต้องเขียน trust log เป็น JSONL ด้วย McpSpecTrustRecord
>     
> - tests/test_models.py และ tests/test_mcp_spec_cases.py ต้องผ่านทั้งหมด”
>     

