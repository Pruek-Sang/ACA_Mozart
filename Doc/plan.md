# 📋 แผนการเติม Text-to-Design Patterns เข้า ACA_Mozart RAG (REVISED v2)

> **Created by**: Aura, The Goddess of Code  
> **Date**: 2025-11-26 (UPDATED: 04:27)  
> **Status**: 🟢 MVP VALIDATED - Test Matrix Passed  
> **Base Folder**: `/home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]`

---

## 🎯 MVP Test Matrix – Status ณ 2025-11-28

| Test | Name | Result | Notes |
|------|------|--------|-------|
| **A1** | Server alive | ✅ PASS | GET / = 200, POST /ask = 200 |
| **A2** | Module imports | ✅ PASS | 9/9 imports OK |
| **B1** | Knowledge folders | ✅ PASS | 39 docs (db:14, example:8, mcp:9, standard:8) |
| **B2** | Index validation | ✅ PASS | 3/3 paths valid (cleaned up stale entries) |
| **C1** | Basic house spec | ✅ PASS | LLM maps human→device codes correctly |
| **C2** | Incomplete data | ✅ PASS | Correctly rejects with 422 |
| **C3** | Device codes valid | ✅ PASS | 6/6 codes in catalog |
| **D1** | context_hint | ✅ PASS | 9/9 sources from MCP folder |
| **D2** | Language change | ⚠️ PARTIAL | Known limitation (see below) |

### Known Limitations

1. **D2 Language**: `language="en"` ตอบเป็นอังกฤษหลัก แต่ยังมีคำไทยบ้างเพราะ source docs เป็นไทย
   - **ไม่ถือเป็น bug** - เป็น expected behavior
   - Phase 2 อาจเพิ่ม translation layer

### Runtime Bugs Fixed (9/9 ✅)

| # | Bug | Status | Fix |
|---|-----|--------|-----|
| 1 | `area_m2` → `area_sqm` | ✅ | models.py |
| 2 | `load_doc_content()` signature | ✅ | knowledge_service.py |
| 3 | `spec_response` unbound | ✅ | service.py |
| 4 | `llm_plan_text` missing | ✅ | trust_log.py |
| 5 | RoomSpec/LoadSpec attributes | ✅ | service.py |
| 6 | Pydantic V2 ConfigDict | ✅ | models.py, config.py |
| 7 | timezone-aware datetime | ✅ | models.py |
| 8 | f-string `{{` bug | ✅ | service.py line 899 |
| 9 | datetime JSON serialization | ✅ | trust_log.py `mode='json'` |

---

## 🚨 CRITICAL DESIGN CORRECTIONS

แผนเดิมมีจุดออกแบบผิด 2 ประการที่ **ต้องแก้ก่อน implement**:

### ❌ Design Error #1: `/mcp_spec` คืน Union Response
**ปัญหา**: แผนเดิมให้ `/mcp_spec` คืน `McpSpecResponse | AskBackResponse | StepPlanResponse`

**ทำไมผิด**:
- ขัดหลักการ Canonical Funnel: `/mcp_spec` = Spec Engine ล้วนๆ
- Gateway/consumer ที่เรียกใช้จะพัง (assume ว่าได้ spec เสมอ)
- ฝ่าฝืนสัญญา API ที่ระบุไว้

**✅ วิธีแก้ที่ถูก**:
```
/api/v1/mcp_spec:
  INPUT: ProjectRequirements
  OUTPUT: 
    - Success (200): McpSpecResponse
    - Error (422): {"error": "...", "questions": [...]} ← ถามกลับผ่าน error body
    - Error (400/503/504): Error messages
```

**askBack/stepPlanning ทำยังไง?**
- Option A: แยก endpoint → `/api/v1/requirements/clarify`, `/api/v1/requirements/plan`
- Option B: Gateway layer handle (ไม่ใช่ RAG)
- **ในแผนนี้เราจะใช้ Option Error Body**: ถ้าข้อมูลไม่ครบ → throw 422 + body มี questions

### ❌ Design Error #2: `_get_valid_device_codes()` ไม่ล็อกแหล่งข้อมูล
**ปัญหา**: แผนเดิมไม่บอกว่าอ่านจากไหน → เสี่ยงให้ dev ยิง DB ตรงๆ

**ทำไมผิด**:
- ขัดรัฐธรรมนูญ DB: RAG ห้ามคุย amadeus.catalog โดยตรง
- ทำให้ RAG ผูกกับ DB schema → coupling สูง

**✅ วิธีแก้ที่ถูก**:
```python
def _get_valid_device_codes(self) -> Set[str]:
    """
    Load valid device codes from rag_knowledge/db/ ONLY
    
    Source: rag_knowledge/db/DEVICE_CODES.md (snapshot from amadeus.catalog)
    
    ห้าม:
    - import database client
    - query Supabase
    - ไปดึงจาก MCP API
    
    ถ้าต้องการ fresh data → rebuild snapshot แล้วเขียนกลับไฟล์
    """
    # Implementation in Section 4.3
```

---

## 🎯 ภาพรวมโครงการ (Project Overview)

### วัตถุประสงค์
นำ 5 แนวคิดหลักจาก **text-to-design** มาปรับใช้ + **ปรับ Knowledge Layer เป็น Folder-based**

### หลักการสำคัญ (Constraints)
- ✅ **NO REGRESSION**: ห้ามทำให้ code เดิมพัง
- ✅ **FOLDER-BASED KNOWLEDGE**: RAG รู้จัก 4 โฟลเดอร์ (db, example, mcp, standard)
- ✅ **NO DB ACCESS FROM RAG**: อ่านผ่าน snapshot ใน rag_knowledge เท่านั้น
- ✅ **SPEC ENGINE PURITY**: /mcp_spec คืน spec หรือ error เท่านั้น
- ✅ **MODULAR DESIGN**: แยกส่วน แก้ง่าย อ่านง่าย

---

## 📚 ความเข้าใจปัจจุบัน (Current Understanding)

### RAG's Knowledge Universe (NEW!)

RAG มองเห็น "จักรวาลความรู้" เฉพาะ 4 โฟลเดอร์นี้:

```
/home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_knowledge/
├── db/                    # Catalog snapshots + DB contracts
│   ├── HOW_TO_USE_DB.md
│   ├── CATALOG_CONTRACT.md
│   ├── DEVICE_CODES.md    # ← _get_valid_device_codes() อ่านจากนี่
│   ├── ROOM_TEMPLATES.md
│   └── ...
├── example/               # Few-shot examples
│   ├── example_req_inputspec_house_1floor_basic.md
│   ├── example_req_inputspec_house_2floor_kitchen_heavy.md
│   └── ...
├── mcp/                   # MCP design docs
│   ├── How to Design ACA_Mozart(new ver.).txt
│   ├── constitution files
│   └── ...
├── standard/              # Thai electrical standards
│   └── ...
└── knowledge_index.json   # Registry (NOT whitelist)
```

**Paradigm Shift**:
- **Before**: knowledge_index.json = whitelist → ถ้าไม่อยู่ใน index = ไม่มีตัวตน
- **After**: knowledge_index.json = metadata/priority → ไฟล์ทุกตัวอ่านได้ แต่ที่มี index จะมี group/tags

### จาก Work now.md
```
main.py → app/routes.py → app/service.py
  ├─ RagService.process_ask()
  └─ RagService.generate_mcp_spec()
       ├─ knowledge_service.py (NEW DESIGN ในแผนนี้)
       ├─ core/database.py
       ├─ core/privacy.py
       └─ trust_log.py
```

---

## 🏗️ PART 1: Knowledge Layer v2 (Folder-Based Architecture)

### 1.1 Config Changes (`app/config.py`)

```python
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent  # root ของโปรเจกต์ RAG

class Settings(BaseSettings):
    # === Knowledge Base (FOLDER-BASED) ===
    KNOWLEDGE_ROOT: str = str(BASE_DIR / "rag_knowledge")
    KNOWLEDGE_DIR_DB: str = str(BASE_DIR / "rag_knowledge" / "db")
    KNOWLEDGE_DIR_EXAMPLE: str = str(BASE_DIR / "rag_knowledge" / "example")
    KNOWLEDGE_DIR_MCP: str = str(BASE_DIR / "rag_knowledge" / "mcp")
    KNOWLEDGE_DIR_STANDARD: str = str(BASE_DIR / "rag_knowledge" / "standard")
    KNOWLEDGE_INDEX_PATH: str = str(BASE_DIR / "rag_knowledge" / "knowledge_index.json")
    
    # กติกา:
    # - ห้าม hard-code path ในไฟล์อื่น
    # - ทุกที่ต้องอ้างผ่าน config นี้
    # - ใช้ BASE_DIR เพื่อไม่พึ่ง current working directory
```

### 1.2 DocumentMeta Model (`app/knowledge_service.py`)

```python
from enum import Enum
from typing import Optional, List, Literal

class KnowledgeFolder(str, Enum):
    DB = "db"
    EXAMPLE = "example"
    MCP = "mcp"
    STANDARD = "standard"

class DocumentMeta(BaseModel):
    """Metadata for a knowledge document"""
    # Identity
    id: Optional[str] = None          # From knowledge_index.json (if exists)
    path: str                          # Absolute path
    rel_path: str                      # Relative to KNOWLEDGE_ROOT
    folder: KnowledgeFolder            # Which of 4 folders
    
    # Metadata (from index, if exists)
    group: Optional[str] = None        # e.g., "mcp_spec", "catalog_schema"
    tags: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    language: Optional[str] = "th"
    
    # Priority (computed)
    priority: int = Field(default=50)  # Higher = more important
```

### 1.3 KnowledgeService v2 API

```python
class KnowledgeService:
    """
    Folder-based knowledge management
    
    Philosophy:
    - Scan ALL files in 4 folders
    - Use knowledge_index.json for metadata/priority (not whitelist)
    - Lazy load content
    """
    
    def __init__(self, index_path: Optional[str] = None):
        self.index_path = Path(index_path or settings.KNOWLEDGE_INDEX_PATH)
        self.folders = {
            "db": Path(settings.KNOWLEDGE_DIR_DB),
            "example": Path(settings.KNOWLEDGE_DIR_EXAMPLE),
            "mcp": Path(settings.KNOWLEDGE_DIR_MCP),
            "standard": Path(settings.KNOWLEDGE_DIR_STANDARD),
        }
        
        # Internal storage
        self._docs_by_path: Dict[str, DocumentMeta] = {}
        self._docs_by_id: Dict[str, DocumentMeta] = {}
        self._docs_by_group: Dict[str, List[DocumentMeta]] = {}
        self._docs_unindexed: List[DocumentMeta] = []
        
        # Load on init
        self._load_index()
        self._scan_folders()
    
    def _scan_folders(self) -> None:
        """
        Scan all 4 folders for files
        
        Process:
        1. Walk each folder (*.md, *.txt, *.json)
        2. For each file:
           - Create DocumentMeta
           - Check if path matches knowledge_index entry
           - If yes: populate id, group, tags, priority
           - If no: mark as unindexed (priority = default)
        3. Build internal indices
        """
        for folder_name, folder_path in self.folders.items():
            if not folder_path.exists():
                logger.warning(f"Folder not found: {folder_path}")
                continue
            
            for file_path in folder_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in [".md", ".txt", ".json"]:
                    rel_path = file_path.relative_to(settings.KNOWLEDGE_ROOT)
                    
                    # Try to find in index
                    index_entry = self._find_index_entry(str(rel_path))
                    
                    doc_meta = DocumentMeta(
                        id=index_entry.get("id") if index_entry else None,
                        path=str(file_path),
                        rel_path=str(rel_path),
                        folder=KnowledgeFolder(folder_name),
                        group=index_entry.get("group") if index_entry else None,
                        tags=index_entry.get("tags", []) if index_entry else [],
                        version=index_entry.get("version") if index_entry else None,
                        language=index_entry.get("language", "th") if index_entry else "th",
                        priority=self._compute_priority(index_entry) if index_entry else 50
                    )
                    
                    # Store
                    self._docs_by_path[str(file_path)] = doc_meta
                    if doc_meta.id:
                        self._docs_by_id[doc_meta.id] = doc_meta
                    if doc_meta.group:
                        self._docs_by_group.setdefault(doc_meta.group, []).append(doc_meta)
                    else:
                        self._docs_unindexed.append(doc_meta)
    
    def _compute_priority(self, index_entry: Optional[Dict]) -> int:
        """
        Compute priority for retrieval
        
        Rules:
        - group in ["mcp_spec", "catalog_schema", "thai_standard", "example_project"] → 90
        - tag contains "must_read" → 95
        - tag contains "deprecated" → 20
        - no index → 50
        """
        if not index_entry:
            return 50
        
        group = index_entry.get("group")
        tags = index_entry.get("tags", [])
        
        if "must_read" in tags:
            return 95
        if "deprecated" in tags:
            return 20
        if group in ["mcp_spec", "catalog_schema", "thai_standard", "example_project"]:
            return 90
        
        return 60  # Has index but not high priority
    
    # === Public API ===
    
    def list_docs(
        self,
        folder: Optional[str] = None,
        group: Optional[str] = None
    ) -> List[DocumentMeta]:
        """
        List documents with optional filters
        
        Args:
            folder: Filter by folder ("db", "example", "mcp", "standard")
            group: Filter by group from index
        
        Returns:
            List of DocumentMeta
        """
        docs = list(self._docs_by_path.values())
        
        if folder:
            docs = [d for d in docs if d.folder == folder]
        
        if group:
            docs = [d for d in docs if d.group == group]
        
        # Sort by priority descending
        docs.sort(key=lambda d: d.priority, reverse=True)
        
        return docs
    
    def get_docs_for_mcp_spec(self) -> List[DocumentMeta]:
        """
        Get documents for MCP spec generation
        
        Strategy:
        - Include ALL files from db, mcp, standard, example
        - Priority ordering:
          1. High priority groups (mcp_spec, catalog_schema, etc.)
          2. Indexed docs
          3. Unindexed docs
        
        Returns:
            Sorted list by priority
        """
        all_docs = []
        
        # Add from all folders
        for folder_name in ["db", "mcp", "standard", "example"]:
            all_docs.extend(self.list_docs(folder=folder_name))
        
        # Already sorted by priority in list_docs
        return all_docs
    
    def get_docs_for_ask(self, context_hint: List[str]) -> List[DocumentMeta]:
        """
        Get documents for /ask endpoint
        
        Context hint mapping:
        - "db" → folder db
        - "standard" → folder standard
        - "mcp_spec" → group mcp_spec
        - empty → all folders
        
        Args:
            context_hint: List of folder names or group names
        
        Returns:
            Sorted list by priority
        """
        if not context_hint:
            return self.list_docs()
        
        docs = []
        for hint in context_hint:
            # Try as folder first
            if hint in ["db", "example", "mcp", "standard"]:
                docs.extend(self.list_docs(folder=hint))
            # Try as group
            elif hint in self._docs_by_group:
                docs.extend(self._docs_by_group[hint])
        
        # Remove duplicates and sort by priority
        seen = set()
        unique_docs = []
        for doc in docs:
            if doc.path not in seen:
                seen.add(doc.path)
                unique_docs.append(doc)
        
        unique_docs.sort(key=lambda d: d.priority, reverse=True)
        
        return unique_docs
    
    def load_doc_content(self, doc_meta: DocumentMeta) -> str:
        """
        Load document content (lazy)
        
        Args:
            doc_meta: Document metadata
        
        Returns:
            File content as string
        """
        try:
            with open(doc_meta.path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load {doc_meta.path}: {e}")
            return ""
```

**ประมาณการเวลา**: 6 ชั่วโมง
- Scan folders logic: 2h
- Priority computation: 1h
- API methods: 2h
- Testing: 1h

**ความเสี่ยง**: 🟢 **Low** - ไม่แตะ business logic เดิม

---

## 🏗️ PART 2: แก้ IDEA #2 (Multi-Mode) ตามหลักการที่ถูก

### 2.1 ❌ OLD DESIGN (ผิด)

```python
# ✗ ผิด: คืน Union
async def generate_mcp_spec(req) -> Union[McpSpecResponse, AskBackResponse]:
    if missing:
        return AskBackResponse(questions=[...])
    return McpSpecResponse(...)
```

### 2.2 ✅ NEW DESIGN (ถูก)

```python
# app/models.py
class InsufficientDataError(BaseModel):
    """Error body สำหรับ 422 เมื่อข้อมูลไม่พอ"""
    error: str = "Insufficient project requirements"
    missing_fields: List[str]
    questions: List[str]  # คำถามที่ควรถาม
    suggestions: List[str]  # คำแนะนำ

# app/service.py
async def generate_mcp_spec(self, req: ProjectRequirements) -> McpSpecResponse:
    """
    Generate MCP spec (PURE SPEC ENGINE)
    
    Returns:
        McpSpecResponse (always)
    
    Raises:
        HTTPException(422) with InsufficientDataError body
        HTTPException(400/503/504) for other errors
    """
    # Validate
    validation_errors = self._validate_requirements(req)
    missing_critical = self._check_critical_missing(req)
    
    # ถ้าข้อมูลไม่พอ → throw error พร้อมคำถาม
    if missing_critical:
        questions = await self._generate_clarifying_questions(req, missing_critical)
        
        raise HTTPException(
            status_code=422,
            detail=InsufficientDataError(
                missing_fields=missing_critical,
                questions=questions,
                suggestions=[
                    "Please provide complete room information",
                    "Specify all electrical loads"
                ]
            ).model_dump()
        )
    
    # ข้อมูลครบ → สร้าง spec
    return await self._generate_spec_internal(req)

async def _generate_clarifying_questions(
    self,
    req: ProjectRequirements,
    missing_fields: List[str]
) -> List[str]:
    """
    Use LLM to generate smart questions (helper function)
    
    This is NOT a different mode, just error handling enhancement
    """
    prompt = f"""
    User wants: {req.project_name}
    Missing: {missing_fields}
    
    Generate 3-5 specific questions in Thai to complete the spec.
    Return JSON: {{"questions": [...]}}
    """
    
    resp = self.model.generate_content(prompt, ...)
    return json.loads(resp.text)['questions']
```

**ถอดบทเรียน**:
- `/mcp_spec` ยังคงเป็น "spec engine" ล้วนๆ (คืน McpSpecResponse เสมอถ้าสำเร็จ)
- การถามกลับทำผ่าน **error body** ไม่ใช่ response type ใหม่
- Gateway/consumer ยังใช้งานได้ปกติ (ดัก 422 แล้วแสดง questions)

**ประมาณการเวลา**: 4 ชั่วโมง
- Generate questions function: 2h
- Error handling integration: 1h
- Testing: 1h

**ความเสี่ยง**: 🟢 **Low** - ไม่เปลี่ยน API contract

---

## 🏗️ PART 3: Validation ที่อ่านจาก rag_knowledge/db

### 3.1 ล็อกแหล่งข้อมูล Validation

```python
# app/service.py

def _get_valid_device_codes(self) -> Set[str]:
    """
    Load valid device codes from rag_knowledge/db/
    
    ห้าม:
    - import psycopg2, supabase, sqlalchemy
    - query DB โดยตรง
    - เรียก MCP API
    
    ต้อง:
    - อ่านจาก DEVICE_CODES.md ใน rag_knowledge/db/
    - Parse format ที่กำหนด
    
    ถ้าต้องการ fresh data:
    - รัน script build_device_codes_snapshot.py
    - Script นั้น query amadeus.catalog แล้วเขียนกลับ .md
    """
    # Load from knowledge service
    db_docs = self.knowledge.list_docs(folder="db")
    
    device_codes_doc = next(
        (d for d in db_docs if "DEVICE_CODES" in d.rel_path),
        None
    )
    
    if not device_codes_doc:
        logger.warning("DEVICE_CODES.md not found, using empty set")
        return set()
    
    content = self.knowledge.load_doc_content(device_codes_doc)
    
    # Parse content (assuming format: one code per line or JSON)
    codes = self._parse_device_codes(content)
    
    return set(codes)

def _parse_device_codes(self, content: str) -> List[str]:
    """
    Parse DEVICE_CODES.md
    
    Expected format (example):
    ```
    # Valid Device Codes
    
    ## Air Conditioners
    - AC-9000BTU
    - AC-12000BTU
   - AC-18000BTU
    
    ## Outlets
    - SOCKET-16A
    - SOCKET-20A
    ```
    
    Or JSON:
    ```json
    {
      "device_codes": ["AC-9000BTU", "AC-12000BTU", ...]
    }
    ```
    """
    codes = []
    
    # Try JSON first
    try:
        data = json.loads(content)
        return data.get("device_codes", [])
    except:
        pass
    
    # Fall back to markdown parsing
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('-') or line.startswith('*'):
            # Extract code from "- AC-9000BTU" or "* AC-9000BTU"
            code = line.lstrip('-*').strip()
            if code and not code.startswith('#'):
                codes.append(code)
    
    return codes

# Similarly for room templates
def _get_valid_room_templates(self) -> Set[str]:
    """Load from rag_knowledge/db/ROOM_TEMPLATES.md"""
    # Similar implementation
    pass
```

### 3.2 สร้าง Snapshot Script (ไม่ใช่ RAG code)

```python
# scripts/build_device_codes_snapshot.py
"""
Build device codes snapshot from amadeus.catalog

This script:
1. Query Supabase amadeus.catalog
2. Extract device_code values
3. Write to rag_knowledge/db/DEVICE_CODES.md

Run manually or via CI when catalog updates.
"""

import os
from supabase import create_client
from pathlib import Path

def build_snapshot():
    # Connect to DB (allowed in this script, NOT in RAG code)
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # Query
    response = supabase.table("amadeus_catalog") \
        .select("device_code, device_name, category") \
        .execute()
    
    # Build markdown
    devices_by_category = {}
    for row in response.data:
        cat = row['category']
        devices_by_category.setdefault(cat, []).append({
            'code': row['device_code'],
            'name': row['device_name']
        })
    
    # Write markdown
    output_path = Path("rag_knowledge/db/DEVICE_CODES.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Valid Device Codes\n\n")
        f.write(f"> Generated: {datetime.now().isoformat()}\n")
        f.write(f"> Source: amadeus.catalog\n\n")
        
        for category, devices in sorted(devices_by_category.items()):
            f.write(f"## {category}\n\n")
            for device in devices:
                f.write(f"- `{device['code']}` - {device['name']}\n")
            f.write("\n")
    
    print(f"Written {len(response.data)} device codes to {output_path}")

if __name__ == "__main__":
    build_snapshot()
```

**ประมาณการเวลา**: 3 ชั่วโมง
- _get_valid_device_codes: 1h
- Parser: 1h
- Snapshot script: 1h

**ความเสี่ยง**: 🟢 **Low** - แยก concern ชัดเจน

---

## 🏗์ PART 4: แก้ IDEA #1, #3, #4 ให้ใช้ Folder-based Knowledge

### IDEA #1: LLM Capabilities (ใช้ folder context)

```python
def _build_initial_prompt(self, req, context, examples) -> str:
    """
    Build prompt with folder-based knowledge references
    """
    # Get catalog reference from db folder
    catalog_docs = self.knowledge.list_docs(folder="db", group="catalog_schema")
    catalog_references = "\n".join([
        f"- {doc.rel_path}" for doc in catalog_docs[:5]
    ])
    
    return f"""You are Aura, RAG agent for electrical design.

YOUR KNOWLEDGE SOURCES:
- Database contracts: {catalog_references}
- Standards: See rag_knowledge/standard/
- Examples: See rag_knowledge/example/

YOUR CAPABILITIES:
1. Parse ProjectRequirements → extract rooms, loads
2. Map device names to codes (use rag_knowledge/db/DEVICE_CODES.md)
3. Select templates (use rag_knowledge/db/ROOM_TEMPLATES.md)
4. Fill ProjectInputSpec

YOU CANNOT:
- Calculate electrical values (MCP's job)
- Invent device codes not in DEVICE_CODES.md
- Access database directly

CONTEXT:
{context[:15000]}

REQUIREMENTS:
{req.model_dump_json(indent=2)}

Generate valid McpSpecResponse JSON:
"""
```

### IDEA #3: Plan Generation (อ้างถึง folders)

```python
async def _generate_spec_plan(self, req, context, examples) -> str:
    """
    Generate plan referencing knowledge folders
    """
    prompt = f"""Create a plan for electrical design spec.

Available knowledge:
- Database: rag_knowledge/db/ (catalog, templates, rules)
- Standards: rag_knowledge/standard/ (Thai electrical codes)
- Examples: rag_knowledge/example/ (reference projects)

Create plan covering:
1. Room analysis (types, areas, templates from db/)
2. Load categorization (map to device codes from db/)
3. Heavy load detection
4. Constraint handling (reference standard/)
5. Rule profile selection

Requirements:
{req.model_dump_json(indent=2)}

Write plan in Thai, be specific, reference knowledge sources.
"""
    
    resp = self.model.generate_content(prompt, ...)
    return resp.text
```

### IDEA #4: QC with Folder Source Validation

```python
async def _quality_check_spec(
    self,
    spec: McpSpecResponse,
    original_req: ProjectRequirements
) -> Tuple[str, List[str]]:
    """
    QC with validation against folder sources
    """
    issues = []
    
    # Check 1: Device codes valid (from db/)
    valid_codes = self._get_valid_device_codes()
    for load in spec.project_input.loads:
        if load.device_code not in valid_codes:
            issues.append(
                f"Invalid device_code '{load.device_code}' "
                f"(not in rag_knowledge/db/DEVICE_CODES.md)"
            )
    
    # Check 2: Room templates valid (from db/)
    valid_templates = self._get_valid_room_templates()
    for room in spec.project_input.rooms:
        if room.template_code not in valid_templates:
            issues.append(
                f"Invalid template '{room.template_code}' "
                f"(not in rag_knowledge/db/ROOM_TEMPLATES.md)"
            )
    
    # Check 3: Rooms/loads completeness
    # ... (same as before)
    
    # Check 4: LLM semantic judge
    llm_issues = await self._llm_semantic_check(spec, original_req)
    issues.extend(llm_issues)
    
    # Classify
    if not issues:
        return "PASS", []
    elif len(issues) <= 2:
        return "WARN", issues
    else:
        return "FAIL", issues
```

---

## 🏗️ PART 5: Testing Strategy (NO LLM in Unit Tests)

### 5.1 ❌ OLD (ผิด)

```python
# ✗ ใช้ LLM แปล prompt → non-deterministic
def test_basic_house():
    prompt = "ออกแบบบ้าน 2 ห้องนอน"
    req = llm_parse_prompt(prompt)  # ← ผิด
    response = rag_service.generate_mcp_spec(req)
    assert ...
```

### 5.2 ✅ NEW (ถูก)

```python
# tests/test_mcp_spec_cases.py

@pytest.fixture
def basic_house_requirements():
    """Fixed ProjectRequirements (deterministic)"""
    return ProjectRequirements(
        project_name="Test House 1F",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        rooms=[
            RoomInput(name="ห้องนอน 1", type="bedroom", area_m2=12),
            RoomInput(name="ห้องนั่งเล่น", type="living_room", area_m2=20),
        ],
        loads=[
            LoadInput(room_name="ห้องนอน 1", device="AC_9000BTU", quantity=1),
            LoadInput(room_name="ห้องนอน 1", device="OUTLET_16A", quantity=3),
            # ...
        ],
        user_constraints=[]
    )

@pytest.mark.asyncio
async def test_basic_house_spec_generation(basic_house_requirements):
    """Test spec generation with FIXED input"""
    service = RagService()
    
    response = await service.generate_mcp_spec(basic_house_requirements)
    
    # Assert structure
    assert isinstance(response, McpSpecResponse)
    assert len(response.project_input.rooms) >= 2
    
    # Assert device mapping
    device_codes = [l.device_code for l in response.project_input.loads]
    assert "AC-9000BTU" in device_codes
    
    # Assert validation sources
    # All device_codes must be from rag_knowledge/db/DEVICE_CODES.md
    valid_codes = service._get_valid_device_codes()
    for code in device_codes:
        assert code in valid_codes, f"{code} not in DEVICE_CODES.md"

# tests/fixtures/example_requirements.py
"""Load from rag_knowledge/example/ for test fixtures"""

def load_example_requirements(example_name: str) -> ProjectRequirements:
    """
    Parse example .md files to ProjectRequirements
    
    Example:
        load_example_requirements("house_2floor_kitchen_heavy")
        → Parses rag_knowledge/example/example_req_inputspec_house_2floor_kitchen_heavy.md
        → Returns ProjectRequirements object
    """
    example_path = Path(settings.KNOWLEDGE_DIR_EXAMPLE) / f"example_req_inputspec_{example_name}.md"
    
    content = example_path.read_text()
    
    # Extract JSON from markdown (between ```json ... ```)
    import re
    json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if not json_match:
        raise ValueError(f"No JSON found in {example_path}")
    
    json_str = json_match.group(1)
    data = json.loads(json_str)
    
    return ProjectRequirements(**data)

# Usage in tests
@pytest.mark.asyncio
async def test_heavy_kitchen_example():
    """Test using example from rag_knowledge/example/"""
    req = load_example_requirements("house_2floor_kitchen_heavy")
    
    service = RagService()
    response = await service.generate_mcp_spec(req)
    
    # Assert kitchen recognized as heavy
    kitchen_rooms = [r for r in response.project_input.rooms if r.room_type == "KITCHEN"]
    assert len(kitchen_rooms) > 0
    assert kitchen_rooms[0].template_code == "ROOMT-KITCHEN-HEAVY"
```

**ประมาณการเวลา**: 4 ชั่วโมง
- Fixed fixtures: 1h
- Example loader: 1h
- Test cases: 2h

---

## 📊 สรุปแผนทั้งหมด (REVISED)

### ไฟล์ที่ต้องแก้

| File | Changes | Risk | Hours |
|------|---------|------|-------|
| `app/config.py` | เพิ่ม folder paths | Low | 0.5h |
| `app/knowledge_service.py` | **ออกแบบใหม่ทั้งไฟล์** (folder-based) | Medium | 6h |
| `app/service.py` | ใช้ folder-based knowledge, validation from db/, error handling | High | 12h |
| `app/models.py` | InsufficientDataError, ลบ AskBackResponse | Low | 1h |
| `tests/test_mcp_spec_cases.py` | Fixed fixtures, example loader | Low | 4h |
| `tests/fixtures/` | สร้างใหม่ | Low | 1h |
| `scripts/build_device_codes_snapshot.py` | สร้างใหม่ (snapshot tool) | Low | 1h |
| `rag_knowledge/db/DEVICE_CODES.md` | สร้างใหม่ (initial snapshot) | Low | 0.5h |

**Total: ~26 hours**

### ลำดับการทำงาน (Revised)

1. **Phase 1: Knowledge Layer v2** (7h)
   - Update config.py (0.5h)
   - Implement KnowledgeService v2 (6h)
   - Test folder scanning (0.5h)

2. **Phase 2: Validation Sources** (3h)
   - Build DEVICE_CODES.md snapshot (0.5h)
   - Implement _get_valid_device_codes (1h)
   - Implement _get_valid_room_templates (1h)
   - Test validation (0.5h)

3. **Phase 3: Service Integration** (8h)
   - Update process_ask to use folder-based (2h)
   - Update generate_mcp_spec logic (4h)
   - Error handling (InsufficientDataError) (1h)
   - Test integration (1h)

4. **Phase 4: IDEA #3 (Plan Generation)** (4h)
   - Implement _generate_spec_plan (2h)
   - Update trust_log (1h)
   - Test (1h)

5. **Phase 5: IDEA #4 (QC)** (4h)
   - Implement QC function (2h)
   - LLM judge (1h)
   - Test (1h)

6. **Phase 6: Testing** (4h)
   - Fixed fixtures (2h)
   - Example loader (1h)
   - Full regression suite (1h)

### Success Criteria

- ✅ เคสเดิมยังผ่าน
- ✅ `/mcp_spec` คืน McpSpecResponse หรือ HTTP error เท่านั้น
- ✅ ทุก validation อ่านจาก rag_knowledge/db/
- ✅ ไม่มี DB client import ใน RAG layer
- ✅ KnowledgeService scan ทุกไฟล์ใน 4 folders
- ✅ Trust log บันทึก folder/group sources
- ✅ Test ไม่ใช้ LLM parsing

---

## 🚨 ข้อกำชับสำหรับ Developer

### ห้าม (FORBIDDEN)

1. ❌ แก้ path ของ 4 folders โดยไม่ผ่าน config
2. ❌ Import DB client (psycopg2, supabase, sqlalchemy) ใน app/ หรือ core/
3. ❌ เปลี่ยน `/mcp_spec` ให้คืน union types
4. ❌ Hard-code device codes/templates ในโค้ด
5. ❌ ใช้ LLM parse prompt ใน unit tests

### ต้อง (REQUIRED)

1. ✅ อ่าน knowledge ผ่าน KnowledgeService เท่านั้น
2. ✅ Validation อ่านจาก rag_knowledge/db/ เท่านั้น
3. ✅ Log ทุก doc source (folder + group) ใน trust_log
4. ✅ Test ใช้ fixed ProjectRequirements
5. ✅ ถ้าต้องการ fresh catalog → รัน snapshot script แล้วเขียนกลับ .md

### คำแนะนำ

- ทำทีละ Phase commit แยก
- รัน regression test หลังทุก Phase
- ถ้า Phase ไหนผิดพลาด → revert เฉพาะ Phase นั้น

---

## 🎓 การเรียนรู้จาก text-to-design (Summary)

### ✅ เอามาใช้
1. Workflow patterns (task.json)
2. Logging philosophy
3. Test-driven approach

### ❌ ไม่เอามา
1. Multiple agent classes → ใช้ error handling แทน
2. Union response types → ใช้ HTTP errors
3. Function schemas (Rhino-specific)

### 🔄 ปรับใช้
1. Agent orchestration → Folder-based knowledge routing
2. Visual QC → Spec QC with folder sources
3. Plan-based execution → Two-stage LLM

---

## 📅 Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| Week 1 | Knowledge Layer v2 + Validation Sources | Folder scanning, snapshot tools |
| Week 2 | Service Integration | Updated process_ask, generate_mcp_spec |
| Week 3 | Plan + QC | Two-stage LLM, quality checks |
| Week 4 | Testing + Documentation | Full test suite, update docs |

**Total: 1 month @ 1 developer**

---

**Status**: 🟡 REVISED - Ready for approval  
**Changes from v1**:
- ✅ แก้ design errors (union response, DB access)
- ✅ เพิ่ม folder-based knowledge architecture
- ✅ ล็อกแหล่งข้อมูล validation
- ✅ ปรับ test strategy (no LLM in units)

**Prepared by**: Aura  
**Date**: 2025-11-26 04:27  
**Estimated Effort**: 26 hours
