# 🏗️ NEXIA Session Summary — 20 December 2025

**Session Duration**: ~2 hours  
**Persona**: Nexia (Code Extension Architect)  
**Principle**: Open/Closed — Extend without modifying legacy code  

---

## 📋 Executive Summary

เพิ่ม **Site & Installation Safety Features** เข้าสู่ระบบ ACA_Mozart โดย:
1. สร้าง **Context Injector Pattern** เพื่อเพิ่ม logic ใหม่โดยไม่แก้ Core Calculators
2. สร้าง **Session Memory** สำหรับจำค่า Input ของ User
3. สร้าง **Interactive Questionnaire** สำหรับถามคำถามพร้อมตัวเลือก

---

## 🎯 Requirements ที่ได้รับ

User ต้องการเพิ่ม 4 factors สำหรับ Safety Calculations:

| Factor | Purpose | Impact |
|--------|---------|--------|
| **Distance to Transformer** | ใกล้หม้อแปลง = Short Circuit Current สูง | ต้องใช้ Breaker kA สูงขึ้น |
| **Installation Area** | อุณหภูมิสูง/ใต้ดิน = สายทนกระแสน้อยลง | ต้อง Derate สายไฟ |
| **Panel Type** | Main vs Sub Panel | Sub Panel ห้ามต่อ N-G Link |
| **Conduit Grouping** | หลายเส้นในท่อเดียว = ความร้อนสะสม | ต้อง Derate สายไฟ |

**เพิ่มเติม**: User ต้องการ "จำค่า" และ "ถามพร้อมตัวเลือก" แทนการบังคับกรอกทุกครั้ง

---

## 🏗️ Architecture Design

### Pattern: Context Injector

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Core Pipeline                            │
│                                                                 │
│  Step 1: Resolve Templates                                      │
│  Step 2: Calculate Loads                                        │
│                     ↓                                           │
│  ╔═══════════════════════════════════════════════════════════╗  │
│  ║ [INJECTOR] DeratingInjector.inject()                      ║  │
│  ║ • Reads: installation_area, conduit_grouping              ║  │
│  ║ • Modifies: load.power_watts (increase for derating)      ║  │
│  ╚═══════════════════════════════════════════════════════════╝  │
│                     ↓                                           │
│  Step 3: Size Wires (uses derated loads)                        │
│  Step 4: Select Breakers                                        │
│  Step 5: Size Conduits                                          │
│  Step 6: Check Compliance                                       │
│  Step 7: Generate AutoLISP                                      │
│  Step 8: Build Result                                           │
│                     ↓                                           │
│  ╔═══════════════════════════════════════════════════════════╗  │
│  ║ [INJECTOR] KaRatingInjector.inject()                      ║  │
│  ║ • Reads: distance_to_transformer                          ║  │
│  ║ • Modifies: main breaker kA rating                        ║  │
│  ╠═══════════════════════════════════════════════════════════╣  │
│  ║ [INJECTOR] NgLinkInjector.inject()                        ║  │
│  ║ • Reads: panel_type                                       ║  │
│  ║ • Adds: warnings for sub-panel N-G Link                   ║  │
│  ╚═══════════════════════════════════════════════════════════╝  │
│                     ↓                                           │
│  Return: DesignResult (with safety warnings)                    │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Pattern?

1. **Open/Closed Principle**: Core calculators unchanged
2. **Testable**: Each injector can be unit tested independently
3. **Reversible**: Remove injector = back to original behavior
4. **Composable**: Add more injectors without touching pipeline

---

## 📁 Files Created

### 1. `mcp_core_v2/context/__init__.py`
```python
from .derating_injector import DeratingInjector
from .ka_rating_injector import KaRatingInjector
from .ng_link_injector import NgLinkInjector

__all__ = ['DeratingInjector', 'KaRatingInjector', 'NgLinkInjector']
```

### 2. `mcp_core_v2/context/derating_injector.py` (98 lines)

**Purpose**: Adjust load power to compensate for environmental derating

**Logic**:
```python
TEMP_FACTORS = {
    "indoor": 1.0,      # Standard
    "high_temp": 0.8,   # >45°C → Derate 20%
    "outdoor": 0.9,     # Sun exposure
    "underground": 0.7  # Heat dissipation issues → Derate 30%
}

GROUPING_FACTORS = {
    "1": 1.0,           # Single circuit
    "2-3": 0.8,         # 2-3 circuits → Derate 20%
    "4-6": 0.7          # 4-6 circuits → Derate 30%
}

# Formula: Effective Load = Real Load / (Temp Factor × Group Factor)
# This makes wire sizer choose larger wire
```

**Key Feature**: Uses `object.__setattr__` to modify Pydantic models safely

### 3. `mcp_core_v2/context/ka_rating_injector.py` (81 lines)

**Purpose**: Enforce minimum kA rating based on transformer distance

**Logic**:
```python
KA_REQUIREMENTS = {
    "less_than_50m": 10,   # High Isc → 10kA minimum
    "50_100m": 6,          # Medium Isc
    "more_than_100m": 6    # Low Isc
}
```

**Output**: Adds warning to `result.warnings` if breaker upgraded

### 4. `mcp_core_v2/context/ng_link_injector.py` (62 lines)

**Purpose**: Add safety warnings for sub-panel grounding

**Logic**: If `panel_type == "sub"`, add warning about N-G Link prohibition

---

## 📁 Files Modified

### 1. `Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/models.py`

**Added** (~160 lines):

```python
# SiteContext - Required fields for safety
class SiteContext(BaseModel):
    distance_to_transformer: str  # Required
    installation_area: str        # Required
    panel_type: str               # Required
    conduit_grouping: str = "1"   # Optional, default safe

# Interactive Questionnaire Models
class SiteContextOption(BaseModel):
    value: str    # Machine-readable
    label: str    # Thai label
    hint: str     # Warning/explanation

class SiteContextQuestion(BaseModel):
    field_name: str
    question_th: str
    question_en: str
    options: List[SiteContextOption]
    required: bool
    current_value: Optional[str]

class SiteContextQuestionnaire(BaseModel):
    session_id: str
    questions: List[SiteContextQuestion]
    answered_count: int
    total_count: int
    can_proceed: bool
    message: str

# Pre-defined Questions
SITE_CONTEXT_QUESTIONS = [
    {
        "field_name": "distance_to_transformer",
        "question_th": "ระยะห่างจากหม้อแปลงไฟฟ้า?",
        "options": [
            {"value": "less_than_50m", "label": "น้อยกว่า 50 เมตร", "hint": "⚠️ ต้องใช้เบรกเกอร์ 10kA ขึ้นไป"},
            {"value": "50_100m", "label": "50-100 เมตร", "hint": "ใช้เบรกเกอร์ 6kA ได้"},
            {"value": "more_than_100m", "label": "มากกว่า 100 เมตร", "hint": "ใช้เบรกเกอร์ทั่วไปได้"}
        ]
    },
    # ... 3 more questions
]

def build_site_context_questionnaire(session_id, current_values) -> SiteContextQuestionnaire:
    # Builds questionnaire showing answered vs pending questions
```

**Also Added**: `site_context: Optional[SiteContext]` field to `ProjectRequirements`

### 2. `Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/routes.py`

**Added** (~215 lines):

```python
# Validation in /api/v1/design
if not req.site_context:
    raise HTTPException(400, "Missing site_context - required for safe electrical calculations!")

# 6 New Session Endpoints
POST   /api/v1/session/start          → Create session, return questionnaire
GET    /api/v1/session/{id}/site      → Get current questionnaire status
POST   /api/v1/session/{id}/site      → Update site_context with answers
GET    /api/v1/session/{id}           → Get full session status
POST   /api/v1/session/{id}/design    → Design using session's remembered site_context
DELETE /api/v1/session/{id}           → Delete session
```

**Key Feature**: Session-based endpoint uses remembered `site_context` if not provided in request

### 3. `Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/mcp_adapter.py`

**Changed**:
```python
# Before
def convert(self, spec: ProjectInputSpec) -> McpDesignRequest:

# After
def convert(self, spec: ProjectInputSpec, site_context: Optional[SiteContext] = None) -> McpDesignRequest:
    # ...
    site_context_dict = site_context.model_dump() if site_context else None
    return McpDesignRequest(..., site_context=site_context_dict)
```

**Also Added**: `site_context` field to `McpDesignRequest` dataclass

### 4. `mcp_core_v2/api.py`

**Changed**:
```python
class DesignRequestInput(BaseModel):
    # ... existing fields ...
    site_context: Optional[Dict[str, Any]] = None  # 🆕 Added

def _convert_to_internal(request: DesignRequestInput):
    return DesignRequest(
        # ... existing fields ...
        site_context=request.site_context  # 🆕 Added
    )
```

### 5. `mcp_core_v2/models/contracts.py`

**Added**:
```python
class DesignRequest(BaseModel):
    # ... existing fields ...
    site_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Site & installation context for safety calculations"
    )
```

### 6. `mcp_core_v2/pipeline.py`

**Added**:
```python
# Import Injectors
from context import DeratingInjector, KaRatingInjector, NgLinkInjector

class DesignPipeline:
    def __init__(self):
        # ... existing init ...
        # Initialize Injectors
        self.derating_injector = DeratingInjector()
        self.ka_rating_injector = KaRatingInjector()
        self.ng_link_injector = NgLinkInjector()
    
    def execute(self, request):
        # ... Step 1-2 ...
        
        # Pre-hook: Apply Derating
        site_context = request.site_context or {}
        self.derating_injector.inject(request.loads, site_context)
        
        # ... Step 3-8 ...
        
        # Post-hook: Apply Safety Checks
        result = self.ka_rating_injector.inject(result, site_context)
        result = self.ng_link_injector.inject(result, site_context)
        
        return result
```

---

## 🔄 Data Flow (Final)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND                                                                    │
│                                                                             │
│ 1. POST /api/v1/session/start                                               │
│    Response: { session_id: "abc123", questionnaire: {...} }                 │
│                                                                             │
│ 2. User answers via Radio Buttons/Dropdowns                                 │
│    POST /api/v1/session/abc123/site                                         │
│    Body: { answers: [                                                       │
│      {field_name: "distance_to_transformer", value: "less_than_50m"},       │
│      {field_name: "installation_area", value: "indoor"},                    │
│      {field_name: "panel_type", value: "main"}                              │
│    ]}                                                                       │
│                                                                             │
│ 3. POST /api/v1/session/abc123/design                                       │
│    Body: { project_name: "บ้านทดสอบ", rooms: [...], loads: [...] }          │
│    (site_context ไม่ต้องส่ง - ระบบจำไว้แล้ว!)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ RAG SERVICE (Port 8080)                                                     │
│                                                                             │
│ routes.py:                                                                  │
│   1. ดึง site_context จาก session หรือ request                              │
│   2. rag_service.generate_mcp_spec(req)                                     │
│   3. McpAdapter.convert(spec, site_context)                                 │
│   4. McpClient.design(mcp_request)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ MCP CORE (Port 5001)                                                        │
│                                                                             │
│ api.py → DesignRequestInput(site_context={...})                             │
│        → _convert_to_internal()                                             │
│        → DesignRequest(site_context={...})                                  │
│                                                                             │
│ pipeline.py:                                                                │
│   Pre-Hook:  derating_injector.inject(loads, site_context)                  │
│   Step 3-8:  Wire sizing, Breaker, Conduit, Compliance, AutoLISP            │
│   Post-Hook: ka_rating_injector.inject(result, site_context)                │
│              ng_link_injector.inject(result, site_context)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ RESPONSE                                                                    │
│                                                                             │
│ {                                                                           │
│   "status": "complete",                                                     │
│   "design_result": {                                                        │
│     "wire_sizing": {...},                                                   │
│     "breaker_selections": {                                                 │
│       "panel_main": { "ka_rating": 10, "ka_adjusted": true }                │
│     },                                                                      │
│     "warnings": [                                                           │
│       "[Safety] 1 main breaker(s) upgraded to 10kA due to proximity..."     │
│     ]                                                                       │
│   }                                                                         │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Verification Results

| Test | Result |
|------|--------|
| Context Injectors importable | ✅ PASS |
| DeratingInjector.TEMP_FACTORS correct | ✅ PASS |
| KaRatingInjector.KA_REQUIREMENTS correct | ✅ PASS |
| SiteContext models importable | ✅ PASS |
| `build_site_context_questionnaire()` works | ✅ PASS |
| Session store saves site_context | ✅ PASS |
| DesignRequestInput accepts site_context | ✅ PASS |
| No Python syntax errors | ✅ PASS |
| Full flow trace: No gaps | ✅ PASS |

---

## 🐛 Bugs Fixed During Session

### Bug 1: Duplicate Code in pipeline.py
**Problem**: Step 3, 4, 5 were running twice  
**Fix**: Removed duplicate block (was copy-paste error from previous edit)

### Bug 2: Pydantic Model Modification
**Problem**: `load.power_watts = new_value` failed on frozen Pydantic model  
**Fix**: Use `object.__setattr__(load, 'power_watts', new_value)`

### Bug 3: DesignRequestInput Missing site_context
**Problem**: MCP API was dropping site_context because field didn't exist  
**Fix**: Added `site_context: Optional[Dict[str, Any]]` to DesignRequestInput

### Bug 4: _convert_to_internal Not Passing site_context
**Problem**: Even after adding field, it wasn't passed to internal DesignRequest  
**Fix**: Added `site_context=request.site_context` to DesignRequest constructor

---

## 📊 Lines of Code Summary

| Type | Files | Lines |
|------|-------|-------|
| **NEW** | 4 files | ~453 lines |
| **MODIFIED** | 6 files | ~421 lines added |
| **TOTAL** | 10 files | ~874 lines |

---

## 🔮 Future Work (Not Done)

1. **Frontend UI** — Radio buttons/dropdowns for questionnaire
2. **Unit Tests** — For each injector
3. **Integration Tests** — Full flow test
4. **Documentation** — Update API docs with new endpoints

---

## 🎓 Key Learnings

1. **Context Injector Pattern** works well for adding cross-cutting concerns
2. **Session Memory** enables better UX (user answers once, reuse many times)
3. **Pre-defined Options** better than free-text for safety-critical inputs
4. **Pydantic Frozen Models** require `object.__setattr__` for modification
5. **API Contract Changes** must be done at BOTH ends (RAG + MCP)

---

*Generated by Nexia — Code Extension Architect*  
*Session Date: 20 December 2025*
