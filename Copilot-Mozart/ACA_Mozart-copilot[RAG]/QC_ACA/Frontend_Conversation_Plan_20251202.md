# Frontend Conversation Management - Implementation Plan

**วันที่**: 2025-12-02  
**เป้าหมาย**: Session management สำหรับ gate_way_new (Frontend-only approach)

---

## 🎯 Overview

### ทำไมเลือก Frontend-Only?

✅ **Simple** - ไม่ต้องแก้ backend  
✅ **Fast** - 2-4 ชั่วโมง  
✅ **Deploy ง่าย** - ไม่กระทบ Docker/API  
✅ **พอเพียง** - MVP ทำงานได้  

---

## 📋 Architecture

```
Frontend (gate_way_new)
  ├── State Management (React/Vue)
  │   ├── projectName
  │   ├── buildingType
  │   ├── rooms[]
  │   └── appliances[]
  ├── Query Builder
  │   └── Aggregate data → single query
  └── Send to RAG API
      └── POST /api/v1/ask (existing endpoint)
```

---

## 💻 Implementation

### Step 1: State Hook (30 min)

```typescript
// hooks/useProjectBuilder.ts
interface ProjectData {
  projectName?: string;
  buildingType?: string;
  rooms: Array<{ type: string; count: number }>;
  appliances: Array<{ room: string; device: string; power?: number }>;
}

export function useProjectBuilder() {
  const [data, setData] = useState<ProjectData>({
    rooms: [],
    appliances: []
  });

  const updateProject = (key: string, value: any) => {
    setData(prev => ({ ...prev, [key]: value }));
  };

  const addRoom = (type: string, count: number) => {
    setData(prev => ({
      ...prev,
      rooms: [...prev.rooms, { type, count }]
    }));
  };

  const addAppliance = (room: string, device: string, power?: number) => {
    setData(prev => ({
      ...prev,
      appliances: [...prev.appliances, { room, device, power }]
    }));
  };

  const buildQuery = () => {
    const parts = [];
    
    parts.push("สร้าง JSON สำหรับระบบไฟฟ้าบ้าน");
    
    if (data.projectName) {
      parts.push(`- ชื่อโปรเจค: ${data.projectName}`);
    }
    
    if (data.buildingType) {
      parts.push(`- ประเภท: ${data.buildingType}`);
    }
    
    if (data.rooms.length > 0) {
      parts.push(`- ห้อง: ${data.rooms.map(r => `${r.type} ${r.count} ห้อง`).join(', ')}`);
    }
    
    if (data.appliances.length > 0) {
      parts.push(`- เครื่องใช้: ${data.appliances.map(a => 
        `${a.room}: ${a.device}${a.power ? ` ${a.power}W` : ''}`
      ).join(', ')}`);
    }
    
    return parts.join('\n');
  };

  return { data, updateProject, addRoom, addAppliance, buildQuery };
}
```

---

### Step 2: Chat Component (1 hour)

```typescript
// components/ProjectChat.tsx
import { useProjectBuilder } from '../hooks/useProjectBuilder';

export function ProjectChat() {
  const { data, addRoom, addAppliance, buildQuery } = useProjectBuilder();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const parseUserInput = (text: string) => {
    // Simple parser (can be improved)
    if (text.includes('ชื่อ') && text.includes('บ้าน')) {
      const match = text.match(/["']([^"']+)["']/);
      if (match) {
        updateProject('projectName', match[1]);
      }
    }
    
    if (text.includes('ห้องนอน')) {
      const match = text.match(/(\d+)\s*ห้อง/);
      if (match) {
        addRoom('BEDROOM', parseInt(match[1]));
      }
    }
    
    // ... more parsing rules
  };

  const handleSend = async () => {
    // Step 1-3: Parse and accumulate
    if (!input.includes('สร้าง JSON')) {
      parseUserInput(input);
      setMessages([...messages, 
        { role: 'user', text: input },
        { role: 'assistant', text: 'รับทราบ ต้องการข้อมูลเพิ่มเติมอะไรอีกมั้ย?' }
      ]);
    }
    // Step 4: Generate JSON
    else {
      const fullQuery = buildQuery();
      const response = await fetch('/api/v1/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: fullQuery, language: 'th' })
      });
      const data = await response.json();
      setMessages([...messages, { role: 'assistant', text: data.answer }]);
    }
    
    setInput('');
  };

  return (/* UI */);
}
```

---

### Step 3: Integration with Amadeus (30 min)

```typescript
// utils/mcpBridge.ts
export async function sendToMCP(jsonData: any) {
  // Send JSON to MCP backend
  const response = await fetch('http://amadeus-mcp:5000/api/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(jsonData)
  });
  
  return response.json();
}

// In component:
const handleGenerateAutoLISP = async () => {
  const ragResponse = await askRAG(buildQuery());
  const json = extractJSON(ragResponse.answer);
  const mcpResult = await sendToMCP(json);
  // Display AutoLISP result
};
```

---

## 🔗 Integration Points

### 1. RAG API (existing)
```
POST /api/v1/ask
{
  "query": "สร้าง JSON...",
  "language": "th"
}
```

### 2. MCP API (Amadeus)
```
POST /api/calculate
{
  "project_info": {...},
  "electrical_system": {...},
  "rooms": [...],
  "loads": [...]
}
```

### 3. AutoLISP Generation
```
Response:
{
  "circuits": [...],
  "autolisp": "...",
  "drawings": [...]
}
```

---

## 📊 Data Flow

```
User Input → Frontend State → Build Query → RAG API
                ↓
         Extract JSON from Response
                ↓
         Validate & Send to MCP
                ↓
         Get AutoLISP Result
                ↓
         Display to User
```

---

## ✅ Pros

1. ✅ **Simple** - ไม่แก้ RAG backend
2. ✅ **Fast** - 2-4 ชม.
3. ✅ **No DB** - State ใน browser
4. ✅ **Easy Deploy** - static files
5. ✅ **Works with Amadeus** - REST API call

---

## ⚠️ Limitations (ยอมรับได้สำหรับ MVP)

1. Session หายถ้า refresh (Fix: localStorage)
2. ต้อง parse user input (Fix: improved regex)
3. ไม่มี server-side validation (Fix: add client validation)

---

## 🚀 Timeline

- **Hour 1**: State management hook
- **Hour 2**: Chat component + parser
- **Hour 3**: MCP integration
- **Hour 4**: Testing + fixes

**Total**: ~4 hours

---

## 🎯 Deliverables

1. ✅ State management for project data
2. ✅ Chat interface with accumulation
3. ✅ Query builder (aggregate → single request)
4. ✅ MCP bridge (send JSON)
5. ✅ AutoLISP display

---

## 🔄 Future Enhancements

### ถ้าต้องการ persistent sessions:

```typescript
// Add localStorage
useEffect(() => {
  localStorage.setItem('projectData', JSON.stringify(data));
}, [data]);

// Load on mount
useEffect(() => {
  const saved = localStorage.getItem('projectData');
  if (saved) setData(JSON.parse(saved));
}, []);
```

---

## ✅ สรุป

**Frontend-Only Conversation Management**

- ⏱️ **เวลา**: 2-4 ชั่วโมง
- 🎯 **เป้าหมาย**: MVP ready
- ✅ **เหมาะกับ**: gate_way_new + Amadeus integration
- 🚀 **พร้อม**: Deploy + Test

**แนะนำสำหรับ MVP!**
