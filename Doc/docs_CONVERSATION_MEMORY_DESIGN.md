# Source: CONVERSATION_MEMORY_DESIGN.md

```md
# Conversation Memory Design for ACA Mozart RAG

## 📋 สถานะปัจจุบัน

**One-Shot Only:**
```
User → POST /api/v1/mcp_spec (ProjectRequirements) → LLM → McpSpecResponse → END
```

ปัญหา:
- ไม่สามารถแก้ไข spec ทีละส่วน
- ไม่สามารถถามเพิ่ม
- VB อาจเละถ้ารัน test หลายชุด

---

## 🎯 เป้าหมาย: Multi-Turn Conversation

```
Turn 1: "บ้าน 2 ชั้น 180 ตร.ม."
→ RAG สร้าง partial spec + ถามกลับ

Turn 2: "มีแอร์ 3 ตัว เครื่องทำน้ำอุ่น 2 ตัว"
→ RAG อัปเดต spec + ถามเพิ่ม

Turn 3: "เตาไฟฟ้าแบบ induction ในครัว"
→ RAG อัปเดต spec + confirm

Turn 4: "confirm"
→ RAG ส่ง final spec ไป MCP Core
```

---

## 🏗️ Architecture: Session-Based Memory

### Option A: In-Memory Store (Simple)

```python
# app/session_store.py
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

@dataclass
class ConversationSession:
    """Single conversation session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Accumulated data
    partial_requirements: Dict = field(default_factory=dict)
    messages: list = field(default_factory=list)  # Chat history
    current_spec: Optional[Dict] = None  # Latest generated spec
    
    # State
    stage: str = "gathering"  # gathering | reviewing | confirmed
    
    def is_expired(self, ttl_minutes: int = 60) -> bool:
        return datetime.utcnow() - self.updated_at > timedelta(minutes=ttl_minutes)


class SessionStore:
    """In-memory session storage"""
    
    def __init__(self, ttl_minutes: int = 60):
        self._sessions: Dict[str, ConversationSession] = {}
        self.ttl = ttl_minutes
    
    def create_session(self) -> ConversationSession:
        session = ConversationSession(session_id=str(uuid.uuid4()))
        self._sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        session = self._sessions.get(session_id)
        if session and not session.is_expired(self.ttl):
            return session
        return None
    
    def update_session(self, session_id: str, **kwargs):
        session = self.get_session(session_id)
        if session:
            for k, v in kwargs.items():
                setattr(session, k, v)
            session.updated_at = datetime.utcnow()
    
    def cleanup_expired(self):
        expired = [sid for sid, s in self._sessions.items() if s.is_expired(self.ttl)]
        for sid in expired:
            del self._sessions[sid]

# Singleton
session_store = SessionStore()
```

### Option B: Redis-Backed (Production)

```python
# For production with multiple instances
import redis
import json

class RedisSessionStore:
    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl_seconds
    
    def get_session(self, session_id: str) -> Optional[dict]:
        data = self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    def save_session(self, session_id: str, data: dict):
        self.redis.setex(f"session:{session_id}", self.ttl, json.dumps(data))
```

---

## 🔌 New API Endpoints

### 1. Start Session
```
POST /api/v1/conversation/start
Response: { "session_id": "uuid", "message": "สวัสดีครับ..." }
```

### 2. Send Message (Multi-Turn)
```
POST /api/v1/conversation/{session_id}/message
Body: { "message": "บ้าน 2 ชั้น มีแอร์ 3 ตัว" }
Response: {
    "session_id": "...",
    "stage": "gathering",
    "partial_spec": { ... },
    "assistant_message": "ต้องการทราบเพิ่มเติม...",
    "questions": ["ห้องครัวมีเตาไฟฟ้าหรือไม่?", "..."]
}
```

### 3. Review Spec
```
POST /api/v1/conversation/{session_id}/review
Response: {
    "stage": "reviewing",
    "full_spec": { ... },
    "summary": "สรุป: 6 ห้อง, 10 โหลด...",
    "warnings": []
}
```

### 4. Confirm & Send to MCP
```
POST /api/v1/conversation/{session_id}/confirm
Response: {
    "stage": "confirmed",
    "mcp_response": { ... },  // Response from MCP Core
    "spec_id": "..."
}
```

---

## 🧠 Conversation Handler Design

```python
# app/conversation_service.py

class ConversationService:
    """Multi-turn conversation handler"""
    
    def __init__(self, rag_service: RagService):
        self.rag = rag_service
        self.store = session_store
    
    async def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> ConversationResponse:
        """Process user message in conversation context"""
        
        session = self.store.get_session(session_id)
        if not session:
            raise SessionNotFoundError()
        
        # Add to history
        session.messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Build context from history
        conversation_context = self._build_context(session)
        
        # Extract requirements from message
        extracted = await self._extract_requirements(
            user_message,
            session.partial_requirements,
            conversation_context
        )
        
        # Merge into partial requirements
        session.partial_requirements = self._merge_requirements(
            session.partial_requirements,
            extracted
        )
        
        # Check completeness
        missing = self._check_missing_fields(session.partial_requirements)
        
        if not missing:
            # Ready for spec generation
            session.stage = "reviewing"
            
            # Generate spec
            spec = await self.rag.generate_mcp_spec(
                ProjectRequirements(**session.partial_requirements)
            )
            session.current_spec = spec.model_dump()
            
            return ConversationResponse(
                stage="reviewing",
                partial_spec=session.current_spec,
                assistant_message="ข้อมูลครบถ้วนแล้ว กรุณาตรวจสอบ spec",
                questions=[]
            )
        else:
            # Ask for missing info
            questions = await self._generate_questions(missing, session.partial_requirements)
            
            session.messages.append({
                "role": "assistant",
                "content": questions[0] if questions else "กรุณาให้ข้อมูลเพิ่มเติม",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return ConversationResponse(
                stage="gathering",
                partial_spec=session.partial_requirements,
                assistant_message=questions[0] if questions else "",
                questions=questions
            )
    
    async def _extract_requirements(
        self,
        message: str,
        current: dict,
        context: str
    ) -> dict:
        """Use LLM to extract requirements from natural language"""
        
        prompt = f"""Extract electrical project requirements from user message.

Current requirements (partial):
{json.dumps(current, ensure_ascii=False, indent=2)}

Conversation context:
{context}

User message: {message}

Extract and return JSON with any NEW information:
{{
    "project_name": "...",  // if mentioned
    "building_type": "residential|commercial",
    "voltage_system": "TH_1PH_230V|TH_3PH_400V",
    "rooms": [  // NEW rooms mentioned
        {{"name": "...", "type": "...", "area_sqm": ...}}
    ],
    "loads": [  // NEW loads mentioned
        {{"room_name": "...", "device": "...", "quantity": ...}}
    ],
    "user_constraints": []
}}

Only include fields that are EXPLICITLY mentioned. Use null for unknown.
"""
        
        config = self.rag._get_generation_config(temperature=0.1, json_mode=True)
        response = self.rag._generate_content(prompt, config)
        
        return json.loads(response)
```

---

## 🔒 VB Stability Solution

### Problem: Test suites ทำให้ VB เละ

### Solution: Immutable Knowledge + Snapshot Pattern

```python
# rag_knowledge/ = IMMUTABLE (read-only)
# vector_db/ = DERIVED (can rebuild from rag_knowledge/)

# scripts/rebuild_vector_db.py
"""
Rebuild vector DB from rag_knowledge/ folder
Run this:
1. After adding new documents
2. After test suite causes issues
3. On deployment
"""

def rebuild_vector_db():
    # 1. Delete existing vector_db/
    shutil.rmtree("vector_db/", ignore_errors=True)
    
    # 2. Re-ingest all documents from rag_knowledge/
    from core.ingest import ingest_folder
    ingest_folder("rag_knowledge/")
    
    # 3. Verify
    from core.database import VectorDatabase
    db = VectorDatabase()
    count = db.count_documents()
    print(f"✅ Rebuilt VB with {count} documents")
```

### Test Isolation Strategy

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session", autouse=True)
def isolate_vector_db():
    """Use test-specific vector DB"""
    import os
    os.environ["CHROMA_PATH"] = "test_vector_db/"
    
    # Setup: Copy production VB snapshot
    shutil.copytree("vector_db/", "test_vector_db/")
    
    yield
    
    # Teardown: Delete test VB
    shutil.rmtree("test_vector_db/", ignore_errors=True)
```

---

## 📡 MCP Integration Flow

```
┌────────────────┐     ┌─────────────┐     ┌────────────┐
│   Frontend     │     │  RAG (Aura) │     │  MCP Core  │
│  (React/Vue)   │     │   Gateway   │     │ (Amadeus)  │
└───────┬────────┘     └──────┬──────┘     └─────┬──────┘
        │                     │                  │
        │ 1. Start Session    │                  │
        │────────────────────>│                  │
        │                     │                  │
        │ 2. Multi-turn       │                  │
        │    messages         │                  │
        │<───────────────────>│                  │
        │                     │                  │
        │ 3. Review spec      │                  │
        │────────────────────>│                  │
        │                     │                  │
        │ 4. Confirm          │                  │
        │────────────────────>│                  │
        │                     │ 5. Forward spec  │
        │                     │─────────────────>│
        │                     │                  │
        │                     │ 6. MCP result    │
        │                     │<─────────────────│
        │                     │                  │
        │ 7. Final result     │                  │
        │<────────────────────│                  │
```

### MCP Forwarding Code

```python
# app/mcp_client.py
import httpx
from app.models import McpSpecResponse

class McpClient:
    """Client to forward specs to MCP Core"""
    
    def __init__(self, base_url: str = "http://mcp-core:8000"):
        self.base_url = base_url
    
    async def run_spec(self, spec: McpSpecResponse) -> dict:
        """Forward spec to MCP Core /mcp/v2/run"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp/v2/run",
                json=spec.project_input.model_dump(),
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise McpError(f"MCP error: {response.text}")
            
            return response.json()
```

---

## 🎯 Implementation Roadmap

### Phase 1: Session Store (1-2 days)
- [ ] Create `app/session_store.py`
- [ ] Add session endpoints to routes
- [ ] Test in-memory sessions

### Phase 2: Conversation Handler (2-3 days)
- [ ] Create `app/conversation_service.py`
- [ ] Implement requirement extraction
- [ ] Implement incremental spec building

### Phase 3: Frontend (3-5 days)
- [ ] Simple React/Vue chat interface
- [ ] Session management
- [ ] Spec review UI

### Phase 4: MCP Integration (2-3 days)
- [ ] MCP client implementation
- [ ] Error handling
- [ ] Response visualization

### Phase 5: VB Stability (1-2 days)
- [ ] Test isolation with separate VB
- [ ] Rebuild script
- [ ] CI/CD integration

---

## 📦 Quick Start: Minimal Implementation

**สำหรับทดสอบ MCP Integration เร็วๆ:**

```python
# app/routes.py - Add simple session endpoint

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

# Simple in-memory store
_sessions: Dict[str, dict] = {}

@app.post("/api/v1/session/start")
async def start_session():
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "requirements": {},
        "messages": [],
        "spec": None
    }
    return {"session_id": session_id}

@app.post("/api/v1/session/{session_id}/update")
async def update_session(session_id: str, req: ProjectRequirements):
    if session_id not in _sessions:
        raise HTTPException(404, "Session not found")
    
    _sessions[session_id]["requirements"] = req.model_dump()
    return {"status": "updated"}

@app.post("/api/v1/session/{session_id}/generate")
async def generate_and_send(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(404, "Session not found")
    
    req = ProjectRequirements(**_sessions[session_id]["requirements"])
    spec = await rag_service.generate_mcp_spec(req)
    
    _sessions[session_id]["spec"] = spec.model_dump()
    
    # TODO: Forward to MCP Core
    # mcp_result = await mcp_client.run_spec(spec)
    
    return spec.model_dump()
```

---

## 🔑 Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Session Storage | In-memory → Redis | Start simple, scale later |
| VB Isolation | Separate test_vector_db/ | Protect production data |
| Conversation State | Server-side | Security, consistency |
| Frontend | React + shadcn/ui | Modern, fast development |

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Memory leak from sessions | TTL + cleanup job |
| LLM extraction errors | Validation + retry |
| VB corruption | Automated rebuild script |
| MCP timeout | Async with progress callback |

```