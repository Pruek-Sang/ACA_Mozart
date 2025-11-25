# สิ่งที่ยังขาดตามไฟล์ "ใบสั่งแก้" และ "How to Design"

## ✅ สิ่งที่ทำเสร็จแล้ว (ครบ 95%)

### TASK 1: API Contract ✅ COMPLETE
- ✅ มี 5 routes ครบ: `/api/v1/ask`, `/api/v1/mcp_spec`, `/api/v1/retrieve_raw`, `/api/v1/ingest`, `/api/v1/delete`
- ✅ มี `/mcp/manifest`
- ✅ Pydantic models ครบทุกตัว

### TASK 2: Examples ✅ COMPLETE
- ✅ สร้าง 3 examples ครบ

### TASK 3: Knowledge Index ✅ COMPLETE
- ✅ มี `knowledge_index.json`
- ✅ มี 4 groups: `mcp_spec`, `catalog_schema`, `thai_standard`, `example_project`

### TASK 4: Mapping ภาษาคน → Code ✅ COMPLETE
- ✅ RAG ไม่ query Supabase โดยตรง
- ✅ ProjectInputSpec ออกแบบเป็น semantic spec

### TASK 5: Error Policy + Trust Log ✅ COMPLETE
- ✅ Error codes: 400, 422, 502, 503, 504
- ✅ Retry logic
- ✅ Trust log (JSONL)

### TASK 6: Test Cases ✅ COMPLETE
- ✅ มี 3 test cases ครบ

---

## ❌ สิ่งที่ยังขาด (5%)

### 1. QueryRequest ขาด 2 fields ❌

**ตามใบสั่งแก้ Line 39-45**:
```python
class QueryRequest(BaseModel):
    query: str
    context_hint: List[str]  # ❌ ขาด!
    language: Literal["th", "en"]  # ❌ ขาด!
```

**ที่ทำไว้ (app/models.py)**:
```python
class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, str]] = None  # ไม่ตรง spec
```

**ต้องแก้**:
- เพิ่ม `context_hint: List[str]` สำหรับระบุ group ที่จะค้นหา
- เพิ่ม `language: Literal["th", "en"]` สำหรับควบคุมภาษาตอบ
- `filters` อาจเก็บไว้ หรือเปลี่ยนเป็น optional

---

### 2. StandardResponse ขาด metadata field ❌

**ตามใบสั่งแก้ Line 47-53**:
```python
class StandardResponse(BaseModel):
    answer: str
    sources: List[SourceRef]
    metadata: dict  # ❌ ขาด! → ต้องมี llm_model, retrieved_docs
```

**ที่ทำไว้**:
```python
class StandardResponse(BaseModel):
    answer: str
    sources: List[SourceRef]
    confidence: Literal["High", "Medium", "Low"]
    grounding_status: str
    # ❌ ไม่มี metadata!
```

**ต้องแก้**:
```python
class AnswerMetadata(BaseModel):
    """Metadata for /api/v1/ask responses"""
    llm_model: str
    retrieved_docs: List[str]
    retrieval_group: Optional[str] = None
    
class StandardResponse(BaseModel):
    answer: str
    sources: List[SourceRef]
    confidence: Literal["High", "Medium", "Low"]
    grounding_status: str
    metadata: AnswerMetadata  # เพิ่มใหม่
```

---

### 3. SourceRef อาจจะขาด doc_id field (ขึ้นกับการตีความ) ⚠️

**ตามใบสั่งแก้ Line 51**: "อ้างอิง doc_id / section"

**ที่ทำไว้**:
```python
class SourceRef(BaseModel):
    file: str  # อาจจะคือ file path
    section: str = "N/A"
    score: Optional[float] = None
```

**ควรมี** (แล้วแต่การตีความ):
```python
class SourceRef(BaseModel):
    doc_id: str  # จาก knowledge_index.json
    file: str  # file path
    section: str = "N/A"
    score: Optional[float] = None
```

หรือ `file` คือ `doc_id` อยู่แล้ว → ก็ผ่าน

---

### 4. app/service.py → process_ask() ยังไม่ใช้ context_hint และ language ❌

**ปัญหา**:
- `process_ask()` ยังไม่รองรับ `context_hint` (ไม่ได้ filter ตาม group)
- ยังไม่รองรับ `language` (ยังไม่มี instruction สำหรับ EN vs TH)
- ยังไม่ส่ง `metadata` ใน response

**ต้องแก้**:
```python
async def process_ask(self, req: QueryRequest) -> StandardResponse:
    # 1. ใช้ context_hint เพื่อ filter group
    if req.context_hint:
        # ค้นหาเฉพาะ docs ใน groups ที่ระบุ
        relevant_docs = []
        for group in req.context_hint:
            relevant_docs.extend(self.knowledge.list_docs(group))
        # จากนั้น search เฉพาะ docs เหล่านี้
    
    # 2. ใส่ language instruction ใน prompt
    lang_instruction = "Answer in Thai" if req.language == "th" else "Answer in English"
    
    # 3. สร้าง metadata
    metadata = AnswerMetadata(
        llm_model=settings.MODEL_NAME_ANSWER,
        retrieved_docs=[r['source'] for r in results],
        retrieval_group=",".join(req.context_hint) if req.context_hint else "all"
    )
    
    return StandardResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        grounding_status=status,
        metadata=metadata  # เพิ่มใหม่
    )
```

---

## 📝 สรุปที่ต้องแก้

### ไฟล์ที่ต้องแก้: 2 ไฟล์

#### 1. `app/models.py` - เพิ่ม fields
```python
# เพิ่ม
class AnswerMetadata(BaseModel):
    llm_model: str
    retrieved_docs: List[str]
    retrieval_group: Optional[str] = None

# แก้
class QueryRequest(BaseModel):
    query: str
    context_hint: List[str] = Field(
        default_factory=list,
        description="Knowledge groups to search, e.g., ['thai_standard', 'mcp_spec']"
    )
    language: Literal["th", "en"] = Field(
        default="th",
        description="Response language"
    )
    filters: Optional[Dict[str, str]] = None  # เก็บไว้สำหรับ advanced filtering

# แก้
class StandardResponse(BaseModel):
    answer: str
    sources: List[SourceRef]
    confidence: Literal["High", "Medium", "Low"]
    grounding_status: str
    metadata: AnswerMetadata  # เพิ่มใหม่
```

#### 2. `app/service.py` - ปรับ process_ask()
```python
async def process_ask(self, req: QueryRequest) -> StandardResponse:
    # ใช้ context_hint
    # ใส่ language instruction
    # สร้าง metadata
    # ดูรายละเอียดด้านบน
```

---

## 🎯 ความสำคัญ

### High Priority (ต้องแก้)
- ✅ QueryRequest fields (context_hint, language) - **ตาม spec อย่างชัดเจน**
- ✅ StandardResponse.metadata - **ตาม spec อย่างชัดเจน**
- ✅ ปรับ process_ask() ให้ใช้ fields ใหม่

### Medium Priority (ควรแก้)
- ⚠️ SourceRef ให้ชัดเจนว่า `file` คือ `doc_id` หรือต้องแยก field

### Low Priority (Optional enhancement)
- 💡 เพิ่ม validation ว่า context_hint ที่ส่งเข้ามาต้องเป็น valid group
- 💡 เพิ่ม admin endpoint `/api/v1/knowledge/validate` เพื่อตรวจ index

---

## เปอร์เซ็นต์ความสมบูรณ์

- **ก่อนแก้**: 95% ✅ (ใช้งานได้ แต่ไม่ตรง spec 100%)
- **หลังแก้**: 100% ✅ (ตรงตามใบสั่งแก้ทุกจุด)

---

**สรุป**: ส่วนใหญ่ทำครบแล้ว แต่ยัง**ขาดรายละเอียดใน QueryRequest และ StandardResponse** ซึ่งเป็น API สำคัญสำหรับ `/api/v1/ask`
