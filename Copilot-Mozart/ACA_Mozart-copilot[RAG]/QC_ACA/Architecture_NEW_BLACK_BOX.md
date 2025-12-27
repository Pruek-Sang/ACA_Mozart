# 🏛️ Architecture NEW BLACK BOX: End-to-End Logic Flow
> **เอกสารนี้สำหรับ:** ทำความเข้าใจ Flow การทำงานแบบ Visual Flowchart (Stateful Intelligence)
> **สถานะ:** ✅ Backend Completed (2025-12-28)

---

## 🏗️ Scenario 1: New Design (เริ่มออกแบบใหม่)

**Input:** *"ออกแบบระบบไฟฟ้า บ้าน 2 ชั้น..."*

```mermaid
flowchart TD
    %% Nodes
    User([User])
    FE[Gateway / Frontend]
    Route[routes.py]
    Service[service.py]
    LLM[LLM Parser]
    Injector[session_injector]
    Adapter[mcp_adapter]
    MCP[MCP Core API]
    Pipeline[pipeline.py]
    Formatter[Formatter]

    %% Flow
    User -->|POST /api/v1/ask| FE
    FE --> Route
    Route -->|process_ask(req)| Service
    
    subgraph RAG_Service
        Service -->|1. Detect Intent| Service
        Service -- "Design=YES" --> LLM
        LLM -->|2. Extract JSON| Service
        Service -->|3. Create Session| Injector
        Injector -->|Save DB| DB[(Supabase)]
        Service -->|4. Convert| Adapter
    end

    Adapter -->|5. POST /design| MCP
    
    subgraph MCP_Core
        MCP -->|6. LoadInput| Pipeline
        Pipeline -->|7. Calculate Breaker/Wire| Pipeline
        Pipeline -->|8. Group Circuits| Pipeline
    end

    Pipeline -->|Result JSON| Service
    Service -->|9. Save Result| Injector
    Injector --> DB
    Service -->|10. Format Report| Formatter
    Formatter -->|Markdown| User
```

---

## 🔧 Scenario 2: Stateful Edit (แก้ไขงานเดิม)

**Input:** *"ห้องนอนชั้น 2 เพิ่มแอร์ 18000 BTU"*

```mermaid
flowchart TD
    %% Nodes
    User([User])
    FE[Gateway / Frontend]
    Route[routes.py]
    Service[service.py]
    Merge[merge_engine.py]
    LLM[LLM Parser (Edit)]
    Injector[session_injector]
    MCP[MCP Core API]
    Pipeline[pipeline.py]

    %% Flow
    User -->|POST /ask?session_id=UUID| FE
    FE --> Route
    Route -->|process_ask(session_id)| Service
    
    subgraph Stateful_Intelligence
        Service -->|1. Detect Edit Intent| Service
        Service -- "Edit=YES" --> Merge
        
        Merge -->|2. Load Session| Injector
        Injector -->|Get OLD Data| DB[(Supabase)]
        
        Merge -->|3. Parse Command| LLM
        LLM -- "Action: ADD, Device: AC-18000" --> Merge
        
        Merge -->|4. Apply Logic| Merge
        Merge -- "New List = Old + New" --> Injector
        Injector -->|5. UPDATE DB| DB
    end

    Injector -- "Merged Data" --> Service
    Service -->|6. ProjectRequirements| MCP
    
    subgraph Recalculation
        MCP -->|7. Re-Calculate All| Pipeline
        Pipeline -- "New Breaker (32A)" --> Service
    end

    Service -->|8. New Report| User

    %% Styling
    style Merge fill:#f9f,stroke:#333
    style Injector fill:#ccf,stroke:#333
    style MCP fill:#ff9,stroke:#333
```

---

## 🧩 Key Logic Explanation

### 1. The Merge Brain (`merge_engine.py`)
ทำหน้าที่เหมือน **Git Merge**:
- **Input OLD:** `[AC-12000, Fan]`
- **Input DIFF:** `+ AC-18000`
- **Output NEW:** `[AC-12000, Fan, AC-18000]`

### 2. The Truth Source (`MCP Core`)
ทำหน้าที่เหมือน **Compiler**:
- รับ Input List (ไม่สนว่ามาจาก Create หรือ Edit)
- คำนวณเบรกเกอร์/สายไฟใหม่ **ทุกครั้ง** (Stateless Calculation)
- ดังนั้น: แก้แอร์ -> เบรกเกอร์เปลี่ยนเองอัตโนมัติ ✅


---

## 🧩 Key Modules Overview

### 1. `app/context/merge_engine.py` (The Brain)
- ทำหน้าที่: รวมของเก่า + ของใหม่
- Logic:
  - ถ้าเจอ `CHANGE` → หาตัวเดิมให้เจอ (matching device/room) แล้วแก้ค่า
  - ถ้าเจอ `ADD` → ยัดใส่ list
  - ถ้าเจอ `REMOVE` → ลบทิ้ง

### 2. `app/parsers/llm_parser.py` (The Translator)
- ทำหน้าที่: แปลภาษาคน → Machine Command
- ความสามารถ:
  - เข้าใจพิมพ์ผิด ("แอ", "น้ำอุ่น")
  - เข้าใจบริบท ("สายยาว 20 เมตร" = VD)
  - เข้าใจ Room Operations ("เพิ่มห้องนอน 2 ห้อง")

### 3. `app/context/session_injector.py` (The Vault)
- ทำหน้าที่: คุยกับ Supabase
- เก็บทุกอย่าง: Rooms, Loads, Messages, Site Context
- **Fallback:** ถ้าเน็ตหลุด/Supabase ล่ม → ใช้ Memory แทนชั่วคราว (กันตาย)

---

## 🚨 จุดสำคัญที่ต้องระวัง (Developer Note)
1. **Session ID ห้ามหาย:** Frontend ต้องส่ง `session_id` มาตลอด ไม่งั้นระบบจะนึกว่าเป็นงานใหม่ (Create New)
2. **MCP Core คือ Final Truth:** เราแก้แค่ "Input List" (เช่น เปลี่ยน AC) แต่ขนาดเบรกเกอร์/สายไฟ **MCP Core จะเป็นคนเลือกให้ใหม่เสมอ** (Smart Selection)

*เอกสารนี้คือ map ลายแทงสำหรับระบบ Intelligent Wiring ที่ implement เสร็จแล้ว 100%*
