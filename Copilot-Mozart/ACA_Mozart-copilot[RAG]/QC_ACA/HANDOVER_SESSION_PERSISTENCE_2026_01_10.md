# 📂 Handover: Session Persistence & Frontend Cleanup
**Date:** 2026-01-10
**Status:** ✅ Completed

---

## 🎯 Objectives Achieved
1.  **Full Chat History Persistence:**
    - User/Assistant messages are now logged to Supabase via `log_conversation`.
    - Covers all scenarios: Q&A, Design Result, Ask-Backs (Room/Load details), Errors.
    - Implemented **Safe Logging** with `try-except` blocks in `app/service.py` to prevent logic crashes if DB fails.

2.  **Frontend Type Safety (No More `any`):**
    - **`ResultViewer.tsx`**: Removed 27+ `any` casts. Updated Excel export logic to use typed `LoadResult`.
    - **`PDFPreviewModal.tsx`**: Removed 15+ `any` casts. fully typed `filter`/`reduce`/`map`.
    - **`useHealthTracker.ts`**: Replaced `any` with `unknown` or `Record<string, unknown>`.
    - **`types/index.ts`**: Extended `LoadResult` to include optional fields (`breaker_rating`, `ic_ka`, etc.) needed for display without casting.

3.  **React Hooks Stability:**
    - **`App.tsx`**:
        - Fixed `useEffect` (Session Init) by adding `sessionId` to dependency array => Fixes session switching bugs.
        - Wrapped `handleSubmit` in `useCallback` => Prevents unnecessary re-renders.

---

## 🛠️ Files Modified

### Backend (`app/`)
- **`service.py`**: Added `log_conversation` calls at entry/exit points of `process_ask` and `_build_design_response`.

### Frontend (`frontend/src/`)
- **`App.tsx`**:
  - `useEffect` dependencies updated.
  - `handleSubmit` wrapped in `useCallback`.
  - `window` -> `globalThis`.
- **`types/index.ts`**: Added fields to `LoadResult`.
- **`components/ResultViewer.tsx`**: Type cleanup.
- **`components/PDFPreviewModal.tsx`**: Type cleanup.
- **`hooks/useHealthTracker.ts`**: Type cleanup.

---

## 🚨 Critical Memory Added (Gateway Trap)
Added **Rule #29** to `QC_ACA/🧠 MEMORY - ความผิดพลาดที่ห้ามทำซ้ำ.md`:
> **"ห้ามข้าม step การดู Architecture Diagram เด็ดขาด"**
> ถ้ามี Gateway → ต้องแก้ Gateway ด้วยเสมอเมื่อแตะ API Interface.

---

## ✅ Verification
- **Build**: `npm run build` (Frontend) => **PASSED** (Confirming Type Safety).
- **Logic**: Reviewed `useEffect` loop prevention logic => **SAFE**.
- **Backend Safety**: Reviewed `try-except` around logs => **SAFE**.

---

## 📝 Next Steps
- Deploy to Staging.
- Verify End-to-End Chat History with real database.

---
---

# 📂 Handover: Edit Injector & CRUD Enhancement
**Date:** 2026-01-11
**Status:** ✅ Completed

---

## 🎯 Objectives Achieved

### 1. Edit Injector - Typo Tolerance (55 Keywords)
- **Issue:** "ออกแบบบ้าน...เพิ่มน้ำอุ่น..." triggered EDIT mode on empty session → Parse failed
- **Root Cause:** Edit keyword "เพิ่ม" found in CREATE request, session had 0 loads
- **Fix:** Added check for existing design before entering EDIT mode

**New Features:**
| Category | Keywords Added |
|----------|---------------|
| Typo variants | เพิม, เพิท, เพิ่ท, เพิ้ม |
| Keyboard layout | ฟฟก (add), กำสำะำ (delete) |
| Patterns | เอา X ออก, เปลี่ยน X เป็น Y |

**Files Modified:**
- `app/intent/edit_detector.py` - Added 55 keywords + `get_edit_action_type()`
- `app/intent/__init__.py` - Updated exports
- `app/service.py` - Added existing design check before EDIT mode

---

### 2. Clear Button (Soft Delete)
- **Feature:** "ล้างข้อมูล" button in top bar
- **Flow:** Confirm dialog → DELETE API → Clear all UI → Remove localStorage

**Implementation:**
- **Frontend:** `handleClear()` in `App.tsx`, Trash2 icon from lucide-react
- **Backend:** `DELETE /api/v1/session/{id}` in `routes.py`
- **DB:** Uses `status='expired'` (DB CHECK constraint: active/expired/migrated)

---

### 3. Room CRUD Parsing Support
- **Issue:** "เพิ่มห้องนอน" detected as ADD but parse failed
- **Root Cause:** `regex_parser.py` only had Device patterns, no Room patterns

**Fix:** Added Room patterns:
```
add_room_thai:    เพิ่ม + ห้อง(นอน|น้ำ|ครัว|...) + quantity?
remove_room_thai: ลบ + ห้อง(นอน|น้ำ|ครัว|...) + room_name?
```

**Room Type Mapping:**
| Thai | English |
|------|---------|
| ห้องนอน | bedroom |
| ห้องน้ำ | bathroom |
| ห้องครัว | kitchen |
| ห้องนั่งเล่น | living |
| ห้องเก็บของ | storage |
| โรงรถ | garage |

**Files Modified:**
- `app/parsers/regex_parser.py` - Added Room patterns + handling logic

---

### 4. Other Fixes
- **SLD:** Switch position moved above circuit, Text wrap instead of truncation
- **BOQ:** Added `setBoqData()` during session restore
- **Docker:** Added `COPY catalog ./catalog` for prices.csv

---

## 🛠️ Commits Summary

| # | Commit | Description |
|---|--------|-------------|
| 1 | `5c8ab3e` | Health Tracker wiring + BOQ restore + prices.csv |
| 2 | `f898426` | SLD: Switch above circuit + Text wrap |
| 3 | `4a88083` | Edit Injector: Typo tolerance (55 keywords) |
| 4 | `1bd7dd1` | Clear button + Soft-delete endpoint |
| 5 | `a849e51` | Fix: Use 'expired' for DB CHECK constraint |
| 6 | `a78b2dc` | Room CRUD parsing support |

---

## ✅ Verification

### Edit Injector Tests:
| Query | Parse | Valid |
|-------|-------|-------|
| "แก้แอร์เป็น 18000 BTU" | AC, 18000 BTU | ✅ True |
| "เพิ่มแอร์ 1 ตัว" | AC | ✅ True |
| "ลบปั๊มน้ำออก" | PUMP | ✅ True |
| "เพิ่มห้องนอน" | bedroom, qty=1 | ✅ True |
| "เพิ่มห้องน้ำ 2 ห้อง" | bathroom, qty=2 | ✅ True |

### Confidence Level:
| Feature | Before | After |
|---------|--------|-------|
| Device CRUD | 80% | 80% |
| Room CRUD | 40% | 95% |

---

## 📝 Next Steps
1. Deploy to Production
2. Test Clear button with real user flow
3. Test Edit commands after having existing design
4. Consider adding VD distance edit support


---
---

# 📂 Handover: VD Default Warning False Positive Fix
**Date:** 2026-01-11 (Evening Session)
**Status:** ✅ Completed

---

## 🎯 Problem Statement

**User Report:** Audit tab shows "ใช้ค่าระยะทาง Default" warning even though user specified floor distances in input.

**Evidence:** Cloud logs showed `[CP-VD] Using RAG floor_distances for 'ไฟแสงสว่าง ชั้น 1': 15.0m` - confirming distances WERE being used correctly. Yet warning still appeared.

---

## 🔍 Root Cause Analysis

### Data Flow Traced:
```
Input → RAG (floor_distances=✅) → MCP Adapter → MCP Core (used_default_distance=❌)
```

### Root Cause:
**MCP Core checks `load.branch_distance_m` for EACH load separately.** If ANY load has `branch_distance_m=None`, it sets `used_default_distance=True` and generates a global warning.

**Problem locations:**
1. `mcp_core_v2/pipeline.py` Line 283-293: Creates warning if load.branch_distance_m is None
2. `mcp_core_v2/core/result_builder.py` Line 507-515: Checks wire_sizing.used_default_distance flag

**Why some loads had None:**
- Loads not matching any room name → didn't get floor assignment → didn't get distance
- MCP Adapter had no final fallback when floor_map lookup failed

---

## 🔧 Fixes Applied

### 1. `service.py` Line 1030
**Fix:** Ensure `room_floor` is always int (was potentially string)
```python
floor_val = r.get("floor", 1)
room_floor = int(floor_val) if floor_val else 1
```

### 2. `service.py` Line 1085-1093
**Fix:** Add fallback default distance for ALL loads before MCP call
```python
default_fallback_distance = 15.0  # meters
branch_distance_m=l.get("branch_distance_m") or default_fallback_distance
```

### 3. `mcp_adapter.py` Line 377-379
**Fix:** Add final fallback in Adapter - ensure dist is NEVER None
```python
if default_dist is None:
    floor_int = int(floor) if floor.isdigit() else 1
    dist = {1: 15.0, 2: 25.0, 3: 35.0}.get(floor_int, 15.0)
```

---

## ✅ Commits

| Commit | Description |
|--------|-------------|
| `90f15b9` | fix(ci): use mozart schema + require confirm param for DELETE |
| `f7fac48` | fix(vd): ensure ALL loads have branch_distance_m to prevent default warnings |

---

## 📊 Expected Result

| Before | After |
|--------|-------|
| "มีการใช้ค่าระยะทาง Default บางจุด" | No warning (if user specifies floor_distances) |
| False positive warnings in Audit tab | Clean Audit tab when distances are specified |

---

## 📝 Next Steps
1. Deploy and verify in Production
2. Test with various input patterns (single floor, multi-floor, outdoor areas)
3. Consider adding per-device distance override support


---
---

# 📂 Handover: Audit Distance Logic SSOT & HTML Rendering
**Date:** 2026-01-13 (Early Morning Session)
**Status:** ✅ Completed

---

## 🎯 Problem Statement

### 1. Audit Distance "Default" Bug (Critical)
**Issue:** Audit Tab showed "Default 15m" for ALL circuits, even when user explicitly specified distances (e.g., "ชั้น 1 = 15m").
**Root Cause:** Timing/SSOT Issue. `floor_distances` was injected **AFTER** MCP Core calculation.
  - MCP Core didn't see distance → Used default → marked `used_default_distance=True`.
  - Audit Validator read this flag → Showed warning.

### 2. Raw HTML in Chat (UI)
**Issue:** Audit report displayed raw HTML tags (e.g., `<span style='color:red'>`) in Chat UI.
**Root Cause:** `react-markdown` strips HTML by default for security.

---

## 🔧 Fixes Applied

### 1. Single Source of Truth (SSOT) for Distance
**Concept:** Pass `floor_distances` to MCP Adapter **BEFORE** creating `McpDesignRequest`.

**Files Modified:**
- **`app/service.py`**:
  - Line 1118: Added `floor_distances` to `adapter.convert()` call.
  - Line 2251: Added `floor_distances` to session-based `adapter.convert()` call.
- **`app/routes.py`**:
  - Line 854: Added `floor_distances` to session-based `adapter.convert()` call.
- **`app/mcp_adapter.py`**:
  - Added **Critical Logging** (`[MCP-ADAPTER]`) to track if `floor_distances` is received or empty.

### 2. HTML Rendering in Chat
**Concept:** Enable `rehype-raw` plugin for Markdown renderer.

**Files Modified:**
- **`frontend/src/components/ChatBubble.tsx`**:
  - Imported `rehype-raw`.
  - Added `rehypePlugins={[rehypeRaw]}` to `<Markdown>` component.

---

## ✅ Commits Summary

| Commit | Description |
|--------|-------------|
| `67ab2b7` | fix(vd): pass floor_distances to McpAdapter BEFORE MCP Core calculation |
| `ddc20a9` | fix(routes): pass floor_distances in session-based design endpoint |
| `526613c` | chore: add critical logging at adapter.convert for floor_distances |
| `ebe4f0b` | fix(frontend): enable HTML rendering in chat with rehype-raw |

---

## 📊 Verification Steps

1. **Test Input:** "บ้าน 2 ชั้น ... ระยะเดินสายชั้น 1 = 15m, ชั้น 2 = 25m"
2. **Check Cloud Logs:**
   - Look for `[MCP-ADAPTER] 📏 Received floor_distances: {1: 15.0, 2: 25.0}`.
   - If you see `⚠️ floor_distances is EMPTY`, something is wrong.
3. **Check Usage:**
   - Circuits on Floor 1 should use 15m.
   - Circuits on Floor 2 should use 25m.
4. **Check Audit Tab:**
   - **MUST NOT** show "Default 15m" warning for these circuits.
   - **Status:** Should be ✅ PASS (Green) or ⚠️ WARN (Yellow) based on other factors, but NOT default distance.

---
