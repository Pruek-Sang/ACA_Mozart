# 🗄️ Database Schema Analysis & CRUD Issues

**Analysis Date**: January 27, 2026  
**Context**: Preparing Civil Mode + 3-Phase + Solar System Support  
**Reviewed By**: Aura (Code Goddess)

---

## 📊 Executive Summary - FINAL VERDICT

| Issue | Status | Reality Check |
|-------|--------|---------------|
| Guest Mode RLS Policy | ⚠️ PARTIALLY FIXED | Sessions work, but RLS may allow guest cross-access |
| Projects Table Guest Saves | 🔴 CONFIRMED ISSUE | `NOT NULL` in reference schema blocks guests |
| Price Scraper Components | 🔴 CONFIRMED ISSUE | Missing 50+ 3-phase/solar components |
| **🚨 Projects API ไม่มี!** | ✅ **FIXED!** | เพิ่ม endpoints แล้ว 2026-01-27 |

**Overall Assessment**: 2/3 issues need fixing (Projects API fixed!)

---

## ✅ FIXED: Project CRUD Endpoints

**เพิ่มเมื่อ**: 2026-01-27

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/project/save` | POST | บันทึก session → project (ถาวร) |
| `/api/v1/project/list` | GET | list projects ของ user |
| `/api/v1/project/{id}` | GET | โหลด project by ID |
| `/api/v1/project/{id}` | DELETE | ลบ project (requires confirm) |

**Code Changes:**
- `app/routes.py`: Added import `from app.context.project_injector import project_injector`
- `app/routes.py`: Added 4 new endpoints for Project CRUD

---

## 🚨 PREVIOUS FINDING (NOW FIXED)

~~**เจอปัญหาใหญ่:**~~

```
routes.py                → ใช้แค่ session_injector (ชั่วคราว 24h)
project_injector.py      → มี code พร้อมใช้ แต่ไม่มี endpoint!
mozart.projects table    → มีอยู่แต่ไม่ได้ใช้!
```

**NOW:**
```
✅ routes.py            → มี project endpoints แล้ว!
✅ project_injector.py  → ถูกใช้งานแล้ว
✅ mozart.projects      → จะถูกใช้เมื่อ user กด Save
```

---

## 🔍 Reality Check: Issue by Issue

### Issue 1: Guest Mode Security

**Original Claim**: All guests can see each other's sessions

**Reality Check**: 
```python
# session_injector.py line 188
actual_user_id = user_id  # None for Guest, UUID for logged-in user
```

**What Actually Happens:**
1. ✅ Guest sessions CAN be created with `user_id = NULL` (code handles this)
2. ⚠️ BUT the reference schema shows `user_id NOT NULL` constraint
3. ⚠️ RLS policy uses `auth.uid() = user_id` - guests (NULL) may have access issues

**Evidence from tests:**
```python
# test_session_integration.py line 91
# VERIFY: Load from DB and check user_id is NULL
self.assertIsNone(loaded.user_id, "Guest session should have NULL user_id!")
```

**Verdict**: ⚠️ **PARTIAL ISSUE** 
- Code handles NULL user_id ✅
- Actual DB schema may differ from reference file
- RLS policy doesn't explicitly handle NULL case

---

### Issue 2: Projects Table Guest Saves

**Original Claim**: `user_id NOT NULL` blocks guests from saving projects

**Reality Check from reference schema:**
```sql
-- mozart_schema_reference.py line 40
user_id UUID REFERENCES auth.users NOT NULL DEFAULT auth.uid(),
```

**What Actually Happens:**
1. `mozart.sessions` - Code passes `user_id=None` for guests ✅
2. `mozart.projects` - Reference shows `NOT NULL` constraint ❌

**Verdict**: 🔴 **CONFIRMED ISSUE**
- If reference schema is accurate, guests CANNOT save to projects table
- Need to verify actual deployed schema in Supabase dashboard

**Fix Options:**
1. Enable Anonymous Auth → All users get UUID
2. Drop NOT NULL on projects.user_id
3. Add guest_token column

---

### Issue 3: Price Scraper Missing Components

**Original Claim**: Missing 3-phase breakers, solar equipment, EV chargers

**Reality Check from price_scraper.py:**
```python
# Current SEARCH_TERMS (6 items only):
SEARCH_TERMS = {
    "COMP-OUTLET-16A": [...],      # 1-phase outlet
    "COMP-DOWNLIGHT-9W": [...],    # LED lights
    "COMP-CEILING-24W": [...],     # Ceiling lights
    "CB-1P-16A": [...],            # 1-phase breaker only!
    "WIRE-THW-2.5": [...],         # Small wire
    "WIRE-THW-4.0": [...],         # Small wire
}
```

**Missing for 3-Phase + Solar (CONFIRMED):**
- ❌ `CB-3P-*` - No 3-phase breakers
- ❌ `SOLAR-*` - No solar panels/inverters
- ❌ `EV-*` - No EV chargers
- ❌ `CT-METER-*` - No CT meters
- ❌ `WIRE-THW-6/10/16/25` - No larger wire sizes

**Verdict**: 🔴 **CONFIRMED ISSUE**
- Price scraper only covers basic 1-phase residential
- BOQ pricing incomplete for 3-phase/solar projects

---

## ✅ What's Actually Working

### Schema Compatibility (VERIFIED GOOD)

**JSONB flexibility confirmed** - Can store any data structure:

```json
// site_context supports:
{
  "voltage_system": "TH_3PH_400V",  // ✅ 3-phase
  "solar_config": { ... },          // ✅ Solar
  "ev_charger": { ... }             // ✅ EV
}
```

**Evidence**: Tests pass with 3-phase data:
```python
# test_max_difficulty_verification.py
test_3phase_ev_solar_complete  ✅ PASSED
test_solar_injector_is_real_calculation  ✅ PASSED
```

---

## 🎯 Action Items (Priority Order)

### Priority 1: Verify Actual Schema (TODAY)
```sql
-- Run in Supabase SQL Editor:
SELECT column_name, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_schema = 'mozart' AND table_name IN ('sessions', 'projects');
```

### Priority 2: Fix Projects Table (IF NEEDED)
```sql
-- Only if user_id is NOT NULL:
ALTER TABLE mozart.projects ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE mozart.projects ALTER COLUMN user_id DROP DEFAULT;
```

### Priority 3: Update Price Scraper (THIS WEEK)
Add 50+ new components to `SEARCH_TERMS` and `MOCK_PRICES`

---

## 📋 Quick Reference: Components to Add

### 3-Phase Breakers
```python
"CB-3P-20A", "CB-3P-32A", "CB-3P-40A", "CB-3P-50A", "CB-3P-63A"
```

### 3-Phase Wires
```python
"WIRE-THW-6.0", "WIRE-THW-10.0", "WIRE-THW-16.0", "WIRE-THW-25.0"
```

### Solar Equipment
```python
"SOLAR-PANEL-400W", "SOLAR-PANEL-550W"
"SOLAR-INV-3KW", "SOLAR-INV-5KW", "SOLAR-INV-8KW", "SOLAR-INV-10KW"
"SOLAR-MC4", "SOLAR-WIRE-4MM", "SOLAR-WIRE-6MM"
"CT-METER-3P-100A"
```

### EV Chargers
```python
"EV-WALLBOX-7KW", "EV-WALLBOX-11KW", "EV-WALLBOX-22KW"
```

---

## 🚀 Civil Mode Notes

**No schema changes needed** - JSONB handles everything:

```json
{
  "design_mode": "civil",  // Switch mode
  "structural_config": { ... }  // Civil-specific data
}
```

**Backend Architecture:**
```
RAG Service (Port 8080)
    ↓
Mode Router (NEW)
    ├─→ MCP Electrical (Port 5001) [Current]
    └─→ MCP Civil (Port 5002) [Future]
```

---

## 📚 Related Documents

- Full Analysis: [Doc/DATABASE_SCHEMA_ANALYSIS.md](../../../Doc/DATABASE_SCHEMA_ANALYSIS.md)
- Schema Reference: `mcp_core_v2/db/mozart_schema_reference.py`
- Session Injector: `app/context/session_injector.py`
- Price Scraper: `mcp_core_v2/core/price_scraper.py`

---

*Last Updated: January 27, 2026*  
*Reviewed By: Aura (Code Goddess)*
