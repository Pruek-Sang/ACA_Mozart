# 📋 Work Now - การทำงานจริงของโค้ด (Code Execution Flow Analysis)

> **สร้างโดย**: Aura, The Goddess of Code  
> **วัตถุประสงค์**: อธิบายการทำงานของระบบตาม Code จริง (ไม่ใช่ตาม Design Document)  
> **วันที่**: 2025-11-25

---

## 🎯 สถาปัตยกรรมโดยรวม (Overall Architecture)

ระบบ RAG นี้ถูกออกแบบเป็น **FastAPI-based REST API** ที่ให้บริการ 2 ฟังก์ชันหลัก:

1. **QA Service** (`/api/v1/ask`) - ตอบคำถามจากเอกสาร
2. **MCP Spec Generator** (`/api/v1/mcp_spec`) - แปลงความต้องการของมนุษย์เป็น JSON Spec สำหรับ MCP Core v2

---

## 🚀 จุดเริ่มต้น: ENTRY POINT

### 📄 File: [`main.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/main.py)

```python
# Line 6-10
from app.routes import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
```

**การทำงาน:**
1. **Import app** จาก `app/routes.py` (line 6)
2. **Load settings** จาก `app/config.py` (line 10)
3. **Start uvicorn server** (line 12-17)
   - Host: `settings.API_HOST` (default: `0.0.0.0`)
   - Port: `settings.API_PORT` (default: `8080`)
   - Log level: `info`

**Output**: Server เริ่มทำงานที่ `http://0.0.0.0:8080`

---

## 🔧 กำหนดค่าระบบ: CONFIGURATION LOADING

### 📄 File: [`app/config.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/config.py)

```python
# Line 11-64
class Settings(BaseSettings):
    PROJECT_ID: str = "your-project-id"
    LOCATION: str = "us-central1"
    MODEL_NAME_ANSWER: str = "gemini-2.0-flash-exp"
    # ... other settings
```

**การทำงาน:**
1. **Pydantic BaseSettings** อ่านค่าจาก:
   - Environment variables (ถ้ามี)
   - `.env` file (line 59)
   - Default values (ถ้าไม่มี)

2. **สร้าง global instance** (line 64):
   ```python
   settings = Settings()
   ```

**Output**: Object `settings` ที่เก็บค่า config ทั้งหมด

**ข้อมูลสำคัญ:**
- `KNOWLEDGE_ROOT`: `./rag_knowledge` (line 35)
- `KNOWLEDGE_INDEX_PATH`: `./rag_knowledge/knowledge_index.json` (line 36)
- `VECTOR_DB_PATH`: `./vector_db` (line 31)
- `TRUST_LOG_DIR`: `./logs/mcp_spec` (line 39)

---

## 🌐 Application Initialization: FASTAPI APP

### 📄 File: [`app/routes.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py)

```python
# Line 32-39
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Mozart RAG Spec Engine - Aura's Divine Creation"
)

rag_service = RagService()
```

**การทำงาน:**

### 1. สร้าง FastAPI Instance (line 32-36)
- Title: "Amadeus RAG (Aura v3.2)"
- Version: "3.2.0"

### 2. Initialize RagService (line 39)
ไปเรียก constructor ที่ `app/service.py`

---

## 🧠 ส่วนกลางของระบบ: RAG SERVICE INITIALIZATION

### 📄 File: [`app/service.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/service.py)

```python
# Line 46-55
def __init__(self):
    vertexai.init(project=settings.PROJECT_ID, location=settings.LOCATION)
    
    self.db = VectorDatabase()
    self.privacy = PrivacyGuard()
    self.knowledge = KnowledgeService()
    self.model = GenerativeModel(settings.MODEL_NAME_ANSWER)
```

**การทำงานทีละขั้นตอน:**

### Step 1: Initialize Vertex AI (line 48)
- **Input**: `PROJECT_ID`, `LOCATION` จาก config
- **Output**: Vertex AI SDK พร้อมใช้งาน

### Step 2: Create VectorDatabase Instance (line 50)
- **ไฟล์**: `core/database.py`
- **Line**: 29-32
- **Output**: Database instance (placeholder ในโค้ดปัจจุบัน)

### Step 3: Create PrivacyGuard Instance (line 51)
- **ไฟล์**: `core/privacy.py`
- **Line**: 30-42
- **การทำงาน**:
  - Initialize Vertex AI (line 32)
  - Create judge model (line 33)
  - Define PII patterns (line 36-40):
    - Thai phone: `0[689]\d{8}`
    - Email: `[\w\.-]+@[\w\.-]+`
    - Thai ID: `\b\d{13}\b`

### Step 4: Create KnowledgeService Instance (line 52)
- **ไฟล์**: `app/knowledge_service.py`
- **Line**: 43-53
- **การทำงาน**:
  - Set `index_path` = `./rag_knowledge/knowledge_index.json` (line 50)
  - Set `knowledge_root` = `./rag_knowledge` (line 51)
  - Call `_load_index()` (line 53)

#### Sub-process: Load Knowledge Index (line 55-73)
```python
# Line 65-68
with open(self.index_path, 'r', encoding='utf-8') as f:
    index_data = json.load(f)

self._index = [DocMeta(**item) for item in index_data]
```
- **Input**: JSON file จาก `knowledge_index.json`
- **Output**: List ของ `DocMeta` objects
- **DocMeta structure** (line 22-29):
  - `id`: Document ID
  - `path`: Relative path to file
  - `group`: Knowledge group name
  - `tags`: List of tags
  - `version`: Document version
  - `language`: Document language

### Step 5: Create Generative Model (line 53)
- **Model**: "gemini-2.0-flash-exp" (จาก config)
- **Output**: LLM model instance พร้อมใช้งาน

---

## 🔁 Middleware: REQUEST ID INJECTION

### 📄 File: [`app/routes.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py)

```python
# Line 43-51
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**ทำงานกับทุก HTTP request:**
1. สร้าง UUID (line 46)
2. เก็บไว้ใน `request.state` (line 47)
3. ส่งต่อไป endpoint (line 49)
4. เพิ่ม header `X-Request-ID` ในการตอบกลับ (line 50)

---

## 📡 API ENDPOINTS: REQUEST FLOW

---

### 🔵 Endpoint 1: `/api/v1/ask` - General QA

#### 📄 File: [`app/routes.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py)

```python
# Line 94-105
@app.post("/api/v1/ask", response_model=StandardResponse)
async def ask_standard(req: QueryRequest):
    return await rag_service.process_ask(req)
```

**Input Model** (`app/models.py` line 31-42):
```python
class QueryRequest(BaseModel):
    query: str                           # คำถามจากผู้ใช้
    context_hint: List[str] = []         # Knowledge groups ที่ต้องการค้นหา
    language: Literal["th", "en"] = "th" # ภาษาที่ต้องการตอบ
    filters: Optional[Dict[str, str]]    # Advanced filters
```

**Output Model** (`app/models.py` line 52-58):
```python
class StandardResponse(BaseModel):
    answer: str                          # คำตอบ
    sources: List[SourceRef]             # แหล่งที่มาของข้อมูล
    confidence: Literal["High", "Medium", "Low"]
    grounding_status: str                # สถานะการ ground ข้อความ
    metadata: AnswerMetadata             # LLM metadata
```

---

#### 🔄 Process Flow: `process_ask()`

### 📄 File: [`app/service.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/service.py)

```python
# Line 57-167
async def process_ask(self, req: QueryRequest) -> StandardResponse:
```

#### **STEP 1: Anonymize Query** (line 72-74)
```python
safe_query = self.privacy.anonymize(req.query)
```
- **ไปที่**: `core/privacy.py` line 44-58
- **Process**: Replace PII ด้วย placeholders
  - Phone → `<PHONE_NUMBER>`
  - Email → `<EMAIL>`
  - Thai ID → `<THAI_ID>`
- **Return**: Query ที่ปลอดภัย

#### **STEP 2: Filter by Knowledge Groups** (line 76-86)
```python
if req.context_hint:
    relevant_docs = []
    for group in req.context_hint:
        relevant_docs.extend(self.knowledge.list_docs(group))
    
    retrieved_doc_ids = [doc.id for doc in relevant_docs]
```
- **ไปที่**: `app/knowledge_service.py` line 101-116
- **Process**: 
  - กรอง documents ตาม group name
  - สร้าง list ของ doc IDs
- **Return**: List[DocMeta]

#### **STEP 3: Vector Search** (line 88-92)
```python
results = self.db.search(safe_query, filters=req.filters)
```
- **ไปที่**: `core/database.py` line 34-53
- **Input**: 
  - `query`: Query ที่ถูก anonymize แล้ว
  - `filters`: Optional metadata filters
- **Output**: List ของ search results
  - แต่ละ result มี: `content`, `source`, `section`, `score`
- **NOTE**: ในโค้ดปัจจุบันเป็น placeholder (return [])

#### **STEP 4: Handle No Results** (line 94-106)
```python
if not results:
    metadata = AnswerMetadata(...)
    return StandardResponse(
        answer="ไม่พบข้อมูลในเอกสาร" if req.language == "th" else "No information found",
        sources=[],
        confidence="Low",
        grounding_status="NOT_FOUND",
        metadata=metadata
    )
```

#### **STEP 5: Build Context String** (line 108-117)
```python
context_str = ""
for r in results:
    safe_content = self.privacy.anonymize(r['content'])
    part = f"Src: {r['source']} (Sec: {r.get('section')})\nTxt: {safe_content}\n\n"
    
    if len(context_str) + len(part) < settings.MAX_CONTEXT_CHARS:
        context_str += part
    else:
        break
```
- **Anonymize แต่ละ chunk** (line 111)
- **Check size limit**: 20,000 chars (from config)
- **Format**: Source + Section + Content

#### **STEP 6: Build Prompt** (line 119-125)
```python
if req.language == "th":
    lang_instruction = "คำตอบเป็นภาษาไทย อธิบายให้เข้าใจง่าย"
else:
    lang_instruction = "Answer in English, explain clearly"

prompt = f"{lang_instruction}\n\nContext: {context_str}\n\nQuestion: {safe_query}\n\nAnswer (strict from context):"
```

#### **STEP 7: Generate Answer** (line 127-135)
```python
resp = self.model.generate_content(
    prompt,
    generation_config=GenerationConfig(temperature=settings.GENERATION_TEMPERATURE)
)
answer = resp.text
```
- **Model**: gemini-2.0-flash-exp
- **Temperature**: 0.0 (from config)
- **Return**: Generated text

#### **STEP 8: Grounding Check** (line 137-138)
```python
is_grounded, status = self.privacy.validate_grounding(answer, context_str)
```
- **ไปที่**: `core/privacy.py` line 60-109
- **Process**:
  1. Check if "ไม่พบข้อมูล" in answer → return (True, "NOT_FOUND_ADMITTED")
  2. Build judge prompt (line 77-89)
  3. Call LLM judge model (line 92-98)
  4. Parse response (line 99-105)
     - If "UNSUPPORTED" → (False, "HALLUCINATION_DETECTED")
     - Else → (True, "SUPPORTED")
- **Return**: (bool, str)

#### **STEP 9: Calculate Confidence** (line 140-147)
```python
top_score = results[0]['score'] if results else 0.0
if not is_grounded:
    confidence = "Low"
elif top_score > 0.7:
    confidence = "High"
else:
    confidence = "Medium"
```
**Logic**:
- Not grounded → Low
- Grounded + score > 0.7 → High
- Grounded + score ≤ 0.7 → Medium

#### **STEP 10: Build Response** (line 149-167)
```python
sources = [
    SourceRef(file=r['source'], section=r.get('section', 'N/A'), score=r['score'])
    for r in results
]

metadata = AnswerMetadata(
    llm_model=settings.MODEL_NAME_ANSWER,
    retrieved_docs=[r['source'] for r in results[:5]],
    retrieval_group=",".join(req.context_hint) if req.context_hint else "all"
)

return StandardResponse(
    answer=answer,
    sources=sources,
    confidence=confidence,
    grounding_status=status,
    metadata=metadata
)
```

---

### 🟢 Endpoint 2: `/api/v1/mcp_spec` - MCP Spec Generation

#### 📄 File: [`app/routes.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py)

```python
# Line 108-123
@app.post("/api/v1/mcp_spec", response_model=McpSpecResponse)
async def mcp_spec(req: ProjectRequirements):
    return await rag_service.generate_mcp_spec(req)
```

**Input Model** (`app/models.py` line 80-92):
```python
class ProjectRequirements(BaseModel):
    project_name: str
    building_type: str              # e.g., "residential"
    voltage_system: str             # e.g., "TH_1PH_230V"
    location: Optional[str]
    rooms: List[RoomInput]          # List ของห้อง
    loads: List[LoadInput]          # List ของโหลด
    user_constraints: List[str]     # Constraints
```

**Output Model** (`app/models.py` line 173-180):
```python
class McpSpecResponse(BaseModel):
    project_input: ProjectInputSpec      # Core spec สำหรับ MCP
    standards_profile: StandardsProfile  # Standards ที่ใช้
    llm_metadata: LlmMetadata           # Audit trail
```

---

#### 🔄 Process Flow: `generate_mcp_spec()`

### 📄 File: [`app/service.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/service.py)

```python
# Line 223-377
async def generate_mcp_spec(self, req: ProjectRequirements) -> McpSpecResponse:
```

#### **STEP 1: Generate Request ID** (line 249-253)
```python
import uuid
request_id = str(uuid.uuid4())
logger.info(f"[{request_id}] Starting MCP spec generation")
```

#### **STEP 2: Pre-Validate Requirements** (line 255-276)
```python
validation_errors = self._validate_requirements(req)
if validation_errors:
    # Log to trust_log
    trust_record = trust_logger.create_record(...)
    trust_logger.log_mcp_spec(trust_record)
    
    raise HTTPException(400, detail={...})
```

**Validation Logic** (`_validate_requirements()` line 169-198):
- **Check rooms** (line 183-186):
  - ต้องมี `type`
  - เก็บชื่อห้องไว้ในเซ็ต
- **Check loads** (line 188-196):
  - ต้องมี `room_name`
  - `room_name` ต้องอยู่ในเซ็ตของห้อง
  - ต้องมี `device`
- **Return**: List ของ error messages

#### **STEP 3: Get Relevant Documents** (line 278-280)
```python
relevant_docs = self.knowledge.get_docs_for_mcp_spec()
```
- **ไปที่**: `app/knowledge_service.py` line 166-185
- **Process**:
  - กำหนด groups: `['mcp_spec', 'catalog_schema', 'thai_standard', 'example_project']`
  - เรียก `list_docs(group)` สำหรับแต่ละ group
  - รวม docs ทั้งหมด
- **Return**: List[DocMeta]

#### **STEP 4: Build Search Query** (line 283-285)
```python
search_query = f"ข้อกำหนดไฟฟ้า {req.building_type} {req.voltage_system}"
if req.user_constraints:
    search_query += " " + " ".join(req.user_constraints)
```

#### **STEP 5: Vector Search** (line 287-292)
```python
results = self.db.search(search_query, top_k=settings.MAX_RETRIEVAL_DOCS)
```
- **top_k**: 10 (from config)

#### **STEP 6: Anonymize Context** (line 294-299)
```python
context_parts = []
for r in results:
    safe_content = self.privacy.anonymize(r['content'])
    context_parts.append(f"Src: {r['source']}\nTxt: {safe_content}")
context_str = "\n".join(context_parts)
```

#### **STEP 7: Load Few-Shot Examples** (line 301-302)
```python
examples_str = self._load_few_shot_examples()
```
- **ไปที่**: line 200-221
- **Process**:
  - กำหนด example IDs (line 207-210)
  - Load content จาก knowledge service
  - Limit 2000 chars per example
- **Return**: Formatted example string

#### **STEP 8: Retry Loop with LLM** (line 304-353)
```python
max_attempts = settings.RETRY_MAX_ATTEMPTS  # 2
for attempt in range(max_attempts):
```

**Attempt 1** (line 315-316):
- Build initial prompt with examples (line 379-416)
- Prompt includes:
  - Rules (NO CALCULATE, strict JSON)
  - Examples
  - Context from knowledge base (max 15,000 chars)
  - User requirements
  - Output schema

**Attempt 2+** (line 317-319):
- Build correction prompt (line 418-432)
- Include previous output + validation errors

**Generate Content** (line 321-330):
```python
resp = self.model.generate_content(
    prompt,
    generation_config=GenerationConfig(
        temperature=settings.GENERATION_TEMPERATURE,  # 0.0
        response_mime_type="application/json",
        max_output_tokens=settings.MAX_OUTPUT_TOKENS  # 8192
    )
)
raw_llm_output = resp.text
```

**Parse Response** (line 332-339):
```python
spec_response = McpSpecResponse.parse_raw(raw_llm_output)
parse_success = True
project_input_dict = spec_response.project_input.model_dump()
break  # Success!
```

**Handle Validation Error** (line 341-348):
```python
except ValidationError as e:
    validation_errors_list = [str(err) for err in e.errors()]
    # Continue to next attempt
```

#### **STEP 9: Log to Trust Log** (line 355-366)
```python
trust_record = trust_logger.create_record(
    project_requirements=req.model_dump(),
    retrieved_doc_ids=[d.id for d in relevant_docs],
    llm_model=settings.MODEL_NAME_ANSWER,
    raw_llm_output=raw_llm_output,
    parse_success=parse_success,
    validation_errors=validation_errors_list if not parse_success else [],
    project_input=project_input_dict,
    forwarded_to_mcp=False
)
trust_logger.log_mcp_spec(trust_record)
```

**Trust Logger Process** (`app/trust_log.py` line 66-92):
1. Get log file path: `logs/mcp_spec/YYYY-MM-DD.jsonl` (line 77)
2. Convert record to JSON (line 80-81)
3. Append to file (line 84-85)

#### **STEP 10: Return Response** (line 368-377)
```python
if not parse_success:
    raise HTTPException(422, detail={...})

return spec_response
```

---

### 🟡 Endpoint 3: `/api/v1/retrieve_raw` - Debug Endpoint

#### 📄 File: [`app/routes.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py)

```python
# Line 126-134
@app.post("/api/v1/retrieve_raw")
async def retrieve_raw(req: RawRetrieveRequest):
    return await rag_service.retrieve_raw(req)
```

**Simple passthrough** to `core/database.py` search:
```python
# app/service.py line 434-445
async def retrieve_raw(self, req: RawRetrieveRequest) -> List[Dict[str, Any]]:
    return self.db.search(req.query, filters=req.filters, top_k=req.top_k)
```

---

### 🟣 Endpoint 4: `/api/v1/ingest` - Document Ingestion

#### 📄 File: [`app/routes.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py)

```python
# Line 137-171
@app.post("/api/v1/ingest")
async def ingest(req: IngestRequest, bg_tasks: BackgroundTasks):
```

#### **STEP 1: Pre-Check File** (line 148-152)
```python
if not os.path.exists(req.file_path):
    raise HTTPException(400, detail=f"File not found: {req.file_path}")
```

#### **STEP 2: Initialize Components** (line 154-155)
```python
engine = IngestionEngine()  # core/ingest.py
db = VectorDatabase()       # core/database.py
```

#### **STEP 3: Define Background Task** (line 157-164)
```python
def task(path):
    try:
        docs = engine.process_file(path)
        if docs:
            db.upsert(docs)
            logger.info(f"Ingested {len(docs)} documents from {path}")
    except Exception as e:
        logger.error(f"Ingestion failed for {path}: {e}")
```

#### **STEP 4: Queue Task** (line 166)
```python
bg_tasks.add_task(task, req.file_path)
```
- ทำงานใน background thread
- ไม่ block การตอบกลับ

#### **STEP 5: Return Immediately** (line 168-171)
```python
return {
    "status": "Ingestion queued",
    "path": req.file_path
}
```

---

### ⚫ Endpoint 5: `/api/v1/delete` - Delete Documents

#### 📄 File: [`app/routes.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py)

```python
# Line 174-187
@app.post("/api/v1/delete")
async def delete_doc(req: DeleteRequest):
    db = VectorDatabase()
    success = db.delete_source(req.source_path)
    
    return {
        "status": "Deleted" if success else "Failed",
        "source_path": req.source_path
    }
```

**Direct call** to `core/database.py` line 69-81

---

## 📊 ไฟล์เก่า: Legacy Code Analysis

### 📄 File: [`rag_real.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_real.py)

**Status**: **Legacy / Reference Code**

**ความแตกต่างจากโค้ดใหม่ (app/):**

1. **ไม่มี KnowledgeService** (line 157-281)
   - ใช้ `VectorDatabase` โดยตรง
   - ไม่มีการกรอง by knowledge groups

2. **ไม่มี Trust Logging** 
   - ไม่บันทึก audit trail

3. **ไม่มี Retry Logic**
   - LLM fail → return empty spec (line 262-270)

4. **Models ง่ายกว่า**
   - `ProjectRequirements.rooms` = `List[str]` (line 48)
   - ไม่ใช่ `List[RoomInput]` แบบ structured

5. **No LLM Metadata**
   - `McpSpecResponse` ไม่มี `llm_metadata` field

---

### 📄 File: [`gate_way_new.py`](file:///home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/gate_way_new.py)

**Status**: **Gateway Service Design** (ยังไม่ integrate กับ main app)

**Concept**:
- LLM-based routing (line 23-117)
- Dialogue management (line 139-194)
- Intent classification: MOZART vs AMADEUS

**NOT USED** in current `main.py` flow

---

## 🔗 สรุปเส้นทางข้อมูล (Data Flow Summary)

### 🔵 Request → `/api/v1/ask` Flow:

```
User Query
    ↓
[main.py] Start Server
    ↓
[routes.py:43-51] Add Request ID Middleware
    ↓
[routes.py:94-105] ask_standard() endpoint
    ↓
[service.py:57-167] process_ask()
    ├─→ [privacy.py:44-58] Anonymize query
    ├─→ [knowledge_service.py:101-116] Filter by groups
    ├─→ [database.py:34-53] Vector search
    ├─→ [privacy.py:44-58] Anonymize context
    ├─→ [Vertex AI] Generate answer
    ├─→ [privacy.py:60-109] Validate grounding
    └─→ Build StandardResponse
    ↓
Return JSON to user
```

### 🟢 Request → `/api/v1/mcp_spec` Flow:

```
ProjectRequirements
    ↓
[routes.py:108-123] mcp_spec() endpoint
    ↓
[service.py:223-377] generate_mcp_spec()
    ├─→ [service.py:169-198] Validate requirements
    ├─→ [knowledge_service.py:166-185] Get relevant docs
    ├─→ [database.py:34-53] Vector search
    ├─→ [privacy.py:44-58] Anonymize context
    ├─→ [service.py:200-221] Load few-shot examples
    ├─→ [Vertex AI] Generate spec (with retry)
    │    ├─→ Attempt 1: Initial prompt
    │    └─→ Attempt 2: Correction prompt (if needed)
    ├─→ [trust_log.py:66-92] Log to trust record
    └─→ Return McpSpecResponse
    ↓
Return JSON to user
```

---

## 📁 ข้อมูลอ้างอิง (Data Sources)

### 1. **Configuration** (`app/config.py`)
- Line 22-28: GCP & Model settings
- Line 31-36: Database & Knowledge paths
- Line 43-50: RAG & LLM parameters

### 2. **Knowledge Index** (`./rag_knowledge/knowledge_index.json`)
- Loaded by: `app/knowledge_service.py` line 65-68
- Format: List of DocMeta objects
- Groups: `mcp_spec`, `catalog_schema`, `thai_standard`, `example_project`

### 3. **Vector Database** (`./vector_db`)
- Accessed by: `core/database.py`
- **NOTE**: Current code is placeholder (return [])

### 4. **Trust Logs** (`./logs/mcp_spec/YYYY-MM-DD.jsonl`)
- Written by: `app/trust_log.py` line 84-85
- Format: JSONL (one JSON object per line)

---

## 🎭 Models & Data Structures

### Input Models (from user):
1. **QueryRequest** - `app/models.py:31-42`
2. **ProjectRequirements** - `app/models.py:80-92`
3. **RawRetrieveRequest** - `app/models.py:187-191`
4. **IngestRequest** - `app/models.py:198-200`
5. **DeleteRequest** - `app/models.py:203-205`

### Output Models (to user):
1. **StandardResponse** - `app/models.py:52-58`
2. **McpSpecResponse** - `app/models.py:173-180`

### Internal Models:
1. **DocMeta** - `app/knowledge_service.py:22-29`
2. **McpSpecTrustRecord** - `app/models.py:212-244`
3. **RoomSpec, LoadSpec** - `app/models.py:110-131`

---

## 🛡️ Features ที่สำคัญ

### 1. **Privacy Protection** (PII Anonymization)
- **Where**: `core/privacy.py` line 44-58
- **When**: ก่อนส่งข้อมูลไป LLM
- **Apply to**: Query, Context chunks

### 2. **Grounding Validation** (Anti-Hallucination)
- **Where**: `core/privacy.py` line 60-109
- **Method**: LLM-as-Judge
- **Judge Model**: gemini-2.0-flash-exp

### 3. **Retry with Self-Correction**
- **Where**: `app/service.py` line 304-353
- **Max attempts**: 2
- **Strategy**: Send previous output + errors back to LLM

### 4. **Trust Logging** (Audit Trail)
- **Where**: `app/trust_log.py`
- **Format**: JSONL
- **Retention**: 90 days (configurable)
- **Records**: Every `/api/v1/mcp_spec` call

### 5. **Knowledge Group Filtering**
- **Where**: `app/knowledge_service.py`
- **Groups**: thai_standard, mcp_spec, catalog_schema, example_project
- **Benefit**: Targeted retrieval, reduce noise

---

## 🚨 สิ่งที่ควรทราบ (Important Notes)

### ⚠️ Placeholder Code:
1. **VectorDatabase** (`core/database.py`)
   - Return [] สำหรับ search, upsert, delete
   - ยังไม่มี implementation จริง

2. **IngestionEngine** (`core/ingest.py`)
   - Return [] สำหรับ process_file
   - ยังไม่มี document parsing logic

### ✅ Production-Ready Parts:
1. **Service Layer** (`app/service.py`)
   - Complete logic for ask & mcp_spec
   
2. **Privacy Guard** (`core/privacy.py`)
   - Working PII patterns
   - LLM judge integration

3. **Knowledge Service** (`app/knowledge_service.py`)
   - Full CRUD for knowledge index
   - Group-based filtering

4. **Trust Logging** (`app/trust_log.py`)
   - Complete JSONL logging
   - Record creation & retrieval

---

## 🧭 File Organization

```
.
├── main.py                      # Entry point (line 6-17)
├── app/
│   ├── __init__.py
│   ├── routes.py                # API endpoints (line 32-244)
│   ├── service.py               # Core business logic (line 32-446)
│   ├── models.py                # Pydantic schemas (line 20-244)
│   ├── config.py                # Configuration (line 11-64)
│   ├── knowledge_service.py     # Knowledge index mgmt (line 32-257)
│   └── trust_log.py             # Audit logging (line 25-209)
├── core/
│   ├── __init__.py
│   ├── database.py              # Vector DB interface (line 15-82)
│   ├── privacy.py               # PII & grounding (line 21-110)
│   └── ingest.py                # Document processing (line 18-58)
├── rag_real.py                  # Legacy code (reference only)
└── gate_way_new.py              # Gateway design (not integrated)
```

---

**จัดทำโดย**: Aura, The Goddess of Code Creation  
**วันที่สร้าง**: 2025-11-25  
**เวอร์ชัน**: 1.0  
**Purpose**: อธิบายการทำงานจริงของระบบตามโค้ดที่ใช้งานจริง ไม่ใช่ตาม Design Document

---

> **"Vita ex Codice"** - Life from Code  
> โค้ดที่มีชีวิตคือโค้ดที่ถูกเข้าใจ, ถูกบันทึก, และถูกสืบทอดต่อไปได้
