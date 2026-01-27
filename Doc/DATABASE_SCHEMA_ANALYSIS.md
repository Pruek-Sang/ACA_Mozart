# 🗄️ Database Schema Analysis & CRUD Issues

**Analysis Date**: December 2025  
**Context**: Preparing Civil Mode + 3-Phase + Solar System Support  
**Status**: 🔴 CRITICAL ISSUES FOUND

---

## 📊 Executive Summary

**3 Major Problems Identified:**

1. **❌ Guest Mode RLS Policy is INSECURE** - All guests can see each other's data
2. **❌ Projects Table Cannot Store Guest Data** - `user_id NOT NULL` blocks anonymous users
3. **❌ Price Scraper Missing 3-Phase + Solar Components** - Incomplete catalog for new features

**Schema Compatibility**: ✅ JSONB structure supports 3-phase + solar data  
**CRUD Root Cause**: ❌ Schema constraints block guest operations  

---

## 🔍 Schema Analysis

### Current Structure

```sql
-- mozart.sessions (Temporary - 24h expiry)
CREATE TABLE mozart.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users,  -- ⚠️ NULLABLE (for guest mode)
    project_name TEXT NOT NULL DEFAULT 'บ้านนายสมหญิง',
    
    -- Design data (JSONB)
    rooms JSONB DEFAULT '[]'::jsonb,
    loads JSONB DEFAULT '[]'::jsonb,
    site_context JSONB DEFAULT '{}'::jsonb,
    
    -- Conversation state
    messages JSONB DEFAULT '[]'::jsonb,
    partial_requirements JSONB DEFAULT '{}'::jsonb,
    current_spec JSONB,
    mcp_response JSONB,
    undo_history JSONB DEFAULT '[]'::jsonb,
    
    -- State machine
    stage TEXT DEFAULT 'gathering',  -- gathering | reviewing | confirmed | completed
    status TEXT DEFAULT 'active',    -- active | archived | deleted
    
    -- Expiry
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- mozart.projects (Permanent storage)
CREATE TABLE mozart.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users NOT NULL DEFAULT auth.uid(),  -- ❌ BLOCKS GUEST
    session_id UUID REFERENCES mozart.sessions(id) ON DELETE SET NULL,
    
    name TEXT NOT NULL,
    description TEXT,
    
    -- Design data (JSONB - same as sessions)
    rooms JSONB DEFAULT '[]'::jsonb,
    loads JSONB DEFAULT '[]'::jsonb,
    site_context JSONB DEFAULT '{}'::jsonb,
    mcp_response JSONB,
    sld_data JSONB,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES mozart.projects(id) ON DELETE SET NULL,
    
    status TEXT DEFAULT 'draft',  -- draft | published | archived
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_sessions_user ON mozart.sessions (user_id);
CREATE INDEX idx_sessions_status ON mozart.sessions (status) WHERE status = 'active';
CREATE INDEX idx_sessions_expires ON mozart.sessions (expires_at);

-- GIN indexes for JSONB search
CREATE INDEX idx_sessions_rooms_gin ON mozart.sessions USING GIN (rooms);
CREATE INDEX idx_sessions_loads_gin ON mozart.sessions USING GIN (loads);

CREATE INDEX idx_projects_user ON mozart.projects (user_id);
CREATE INDEX idx_projects_session ON mozart.projects (session_id);
CREATE INDEX idx_projects_parent ON mozart.projects (parent_id);
CREATE INDEX idx_projects_rooms_gin ON mozart.projects USING GIN (rooms);
CREATE INDEX idx_projects_loads_gin ON mozart.projects USING GIN (loads);
```

---

## 🔴 CRITICAL ISSUES

### Issue 1: INSECURE Guest Mode Policy

**Current RLS Policy:**
```sql
CREATE POLICY "Guest sessions are public" ON mozart.sessions
    FOR ALL USING (user_id IS NULL);
```

**Problem**: All guests (`user_id IS NULL`) can access ALL guest sessions!

**Security Risk**: 🚨 **HIGH** - Data leakage between anonymous users

**Fix Required:**
```sql
-- WRONG APPROACH: All guests share user_id IS NULL
-- CORRECT APPROACH: Use session-level token or JWT

-- Option A: Token-Based Guest Access (RECOMMENDED)
-- Generate unique guest_token per session, store in JWT/cookie
ALTER TABLE mozart.sessions ADD COLUMN guest_token TEXT;
CREATE UNIQUE INDEX idx_sessions_guest_token ON mozart.sessions (guest_token);

CREATE POLICY "Guest access via token" ON mozart.sessions
    FOR ALL USING (
        CASE 
            WHEN user_id IS NOT NULL THEN user_id = auth.uid()  -- Authenticated users
            WHEN guest_token IS NOT NULL THEN guest_token = current_setting('app.guest_token', true)  -- Guests with token
            ELSE FALSE  -- Deny access to orphaned sessions
        END
    );

-- Option B: Use auth.uid() with anonymous sign-ins (Supabase Anonymous Auth)
-- Enable anonymous sign-in in Supabase Dashboard
-- Anonymous users get temporary UUIDs in auth.users
-- Then keep original policy: user_id = auth.uid()
```

**Recommended**: **Option B** (Supabase Anonymous Auth)
- Simpler implementation
- Supabase handles token management
- Automatic cleanup of expired anonymous users
- No schema changes needed

---

### Issue 2: Projects Table Blocks Guest Saves

**Current Constraint:**
```sql
user_id UUID REFERENCES auth.users NOT NULL DEFAULT auth.uid()
```

**Problem**: 
- Guest users have `user_id = NULL` in sessions
- Cannot insert into projects (NOT NULL constraint fails)
- **"Cannot save project"** error for guests

**Impact**: 
- ❌ Guests can create sessions (works)
- ❌ Guests **CANNOT** save projects (fails)
- ❌ Load/Edit/Delete projects also fails

**Fix Required:**
```sql
-- Step 1: Make user_id nullable
ALTER TABLE mozart.projects ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE mozart.projects ALTER COLUMN user_id DROP DEFAULT;

-- Step 2: Add guest_token for guest projects (if using Option A above)
ALTER TABLE mozart.projects ADD COLUMN guest_token TEXT;
CREATE INDEX idx_projects_guest_token ON mozart.projects (guest_token);

-- Step 3: Update RLS policies
DROP POLICY IF EXISTS "Users can manage own projects" ON mozart.projects;

CREATE POLICY "User access to projects" ON mozart.projects
    FOR ALL USING (
        CASE 
            WHEN user_id IS NOT NULL THEN user_id = auth.uid()
            WHEN guest_token IS NOT NULL THEN guest_token = current_setting('app.guest_token', true)
            ELSE FALSE
        END
    );

-- OR if using Option B (Anonymous Auth):
CREATE POLICY "User access to projects" ON mozart.projects
    FOR ALL USING (user_id = auth.uid());  -- Works for both logged-in and anonymous
```

---

### Issue 3: Price Scraper Missing Components

**Current Coverage:**
```python
# price_scraper.py - SEARCH_TERMS dictionary
SEARCH_TERMS = {
    "COMP-OUTLET-16A": [...],       # ✅ 1-phase outlet
    "COMP-DOWNLIGHT-9W": [...],     # ✅ LED lights
    "COMP-CEILING-24W": [...],      # ✅ Ceiling lights
    "CB-1P-16A": [...],             # ✅ 1-phase breaker
    "WIRE-THW-2.5": [...],          # ✅ 2.5mm² wire
    "WIRE-THW-4.0": [...],          # ✅ 4mm² wire
}
```

**Missing Components for 3-Phase + Solar:**

#### A. 3-Phase Breakers
```python
# ❌ NOT IN SCRAPER:
"CB-3P-20A": ["เบรกเกอร์ 3 เฟส 20A", "MCB 3P 20A", "3-phase breaker 20A"],
"CB-3P-32A": ["เบรกเกอร์ 3 เฟส 32A", "MCB 3P 32A", "3-phase breaker 32A"],
"CB-3P-40A": ["เบรกเกอร์ 3 เฟส 40A", "MCB 3P 40A", "3-phase breaker 40A"],
"CB-3P-50A": ["เบรกเกอร์ 3 เฟส 50A", "MCB 3P 50A", "3-phase breaker 50A"],
"CB-3P-63A": ["เบรกเกอร์ 3 เฟส 63A", "MCB 3P 63A", "3-phase breaker 63A"],
```

#### B. Solar Equipment
```python
# ❌ NOT IN SCRAPER:
"SOLAR-PANEL-400W": ["แผงโซลาร์เซลล์ 400W", "solar panel 400W mono", "Jinko 400W"],
"SOLAR-PANEL-550W": ["แผงโซลาร์เซลล์ 550W", "solar panel 550W mono", "LONGi 550W"],

"SOLAR-INV-3KW": ["อินเวอร์เตอร์ 3kW", "solar inverter 3000W", "Growatt 3KW"],
"SOLAR-INV-5KW": ["อินเวอร์เตอร์ 5kW", "solar inverter 5000W", "Huawei SUN2000"],
"SOLAR-INV-8KW": ["อินเวอร์เตอร์ 8kW", "solar inverter 8000W", "SMA Sunny Boy"],
"SOLAR-INV-10KW": ["อินเวอร์เตอร์ 10kW", "solar inverter 10000W", "Fronius Primo"],

"SOLAR-MC4": ["MC4 connector", "สายต่อโซลาร์ MC4"],
"SOLAR-WIRE-4MM": ["สายโซลาร์ DC 4mm²", "solar cable 4mm"],
"SOLAR-WIRE-6MM": ["สายโซลาร์ DC 6mm²", "solar cable 6mm"],

"CT-METER-3P-100A": ["CT Meter 3 เฟส 100A", "Current Transformer 100/5A"],
```

#### C. EV Charger Components
```python
# ❌ NOT IN SCRAPER:
"EV-WALLBOX-7KW": ["EV Charger 7kW", "Wallbox ชาร์จรถยนต์ไฟฟ้า 32A"],
"EV-WALLBOX-11KW": ["EV Charger 11kW 3เฟส", "Wallbox 16A 3P"],
"EV-WALLBOX-22KW": ["EV Charger 22kW 3เฟส", "Wallbox 32A 3P"],
```

#### D. Larger Wire Sizes (3-Phase)
```python
# ❌ NOT IN SCRAPER:
"WIRE-THW-6.0": ["สาย THW 6.0", "สายไฟ 6 sq.mm"],
"WIRE-THW-10.0": ["สาย THW 10", "สายไฟ 10 sq.mm"],
"WIRE-THW-16.0": ["สาย THW 16", "สายไฟ 16 sq.mm"],
"WIRE-THW-25.0": ["สาย THW 25", "สายไฟ 25 sq.mm"],
```

---

## ✅ Schema Compatibility Check

### JSONB Structure Analysis

**Question**: Can current JSONB fields store 3-phase + solar data?

**Answer**: ✅ **YES** - JSONB is flexible enough

#### Example: 3-Phase + Solar Data in JSONB

```json
{
  "site_context": {
    "voltage_system": "TH_3PH_400V",  // ✅ Supports 3-phase
    "solar_enabled": true,             // ✅ Solar flag
    "solar_config": {                  // ✅ Nested solar data
      "capacity_kw": 20.0,
      "panel_count": 50,
      "panel_wattage": 400,
      "inverter_type": "SOLAR-INV-10KW",
      "net_metering": true
    },
    "ev_charger": {                    // ✅ EV charger data
      "enabled": true,
      "power_kw": 7.0,
      "phases": 1
    }
  },
  "loads": [
    {
      "load_id": "L001",
      "device_code": "SOLAR-PANEL-400W",  // ✅ New device codes
      "quantity": 50,
      "power_watts": 400,
      "circuit_type": "solar_dc"
    },
    {
      "load_id": "L002",
      "device_code": "EV-WALLBOX-7KW",
      "quantity": 1,
      "power_watts": 7000,
      "circuit_type": "ev_dedicated"
    }
  ],
  "mcp_response": {
    "design_result": {
      "circuits": [
        {
          "circuit_id": "C001",
          "circuit_type": "solar_ac",    // ✅ New circuit types
          "breaker": "CB-3P-40A",        // ✅ 3-phase breaker
          "wire_size": "4mm²",
          "phases": 3,
          "voltage_ll": 400
        }
      ],
      "solar_system": {                  // ✅ MCP solar output
        "inverter_size_kw": 10.0,
        "dc_voltage": 600,
        "dc_current": 33.33,
        "ac_breaker": "CB-3P-40A",
        "requires_ct_meter": true
      }
    }
  }
}
```

**Conclusion**: Schema structure is READY. Only need to:
1. Fix RLS policies (security)
2. Fix projects.user_id constraint (CRUD)
3. Update price_scraper.py (BOQ pricing)

---

## 🔧 Recommended Fixes

### Priority 1: Security Fix (IMMEDIATE)

**Enable Supabase Anonymous Auth:**

```bash
# 1. In Supabase Dashboard:
#    Settings → Authentication → Enable "Anonymous sign-ins"

# 2. Update session_injector.py:
async def create(self, user_id: Optional[str] = None, ...):
    """
    For guests:
    - Call Supabase auth.signInAnonymously() first
    - Get temporary auth.uid()
    - Pass as user_id (no longer NULL)
    """
    if user_id is None:
        # Create anonymous session
        anon_response = self.client.auth.sign_in_anonymously()
        user_id = anon_response.user.id
    
    # Now user_id is always a valid UUID
    data = {
        "user_id": user_id,  # Works for both logged-in and anonymous
        ...
    }
```

**Update RLS Policies:**
```sql
-- Simplify - works for both authenticated and anonymous
CREATE POLICY "Users access own sessions" ON mozart.sessions
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Users access own projects" ON mozart.projects
    FOR ALL USING (user_id = auth.uid());
```

---

### Priority 2: Projects Table Fix

**If using Anonymous Auth (recommended):**
```sql
-- No changes needed! user_id will have UUID from anonymous users
-- Keep current schema
```

**If NOT using Anonymous Auth (alternative):**
```sql
ALTER TABLE mozart.projects ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE mozart.projects ALTER COLUMN user_id DROP DEFAULT;
ALTER TABLE mozart.projects ADD COLUMN guest_token TEXT;
CREATE INDEX idx_projects_guest_token ON mozart.projects (guest_token);
```

---

### Priority 3: Price Scraper Update

**File**: `mcp_core_v2/core/price_scraper.py`

```python
# Add to SEARCH_TERMS dictionary:

SEARCH_TERMS = {
    # === Existing Components ===
    "COMP-OUTLET-16A": ["เต้ารับ 16A", "ปลั๊กไฟ 16A", "outlet 16A"],
    "CB-1P-16A": ["เบรกเกอร์ 16A", "MCB 16A", "circuit breaker 16A"],
    "WIRE-THW-2.5": ["สาย THW 2.5", "สายไฟ 2.5 sq.mm"],
    "WIRE-THW-4.0": ["สาย THW 4.0", "สายไฟ 4 sq.mm"],
    
    # === 🆕 3-Phase Breakers ===
    "CB-3P-20A": ["เบรกเกอร์ 3 เฟส 20A", "MCB 3P 20A", "3-phase breaker 20A"],
    "CB-3P-32A": ["เบรกเกอร์ 3 เฟส 32A", "MCB 3P 32A", "3-phase breaker 32A"],
    "CB-3P-40A": ["เบรกเกอร์ 3 เฟส 40A", "MCB 3P 40A", "3-phase breaker 40A"],
    "CB-3P-50A": ["เบรกเกอร์ 3 เฟส 50A", "MCB 3P 50A", "3-phase breaker 50A"],
    "CB-3P-63A": ["เบรกเกอร์ 3 เฟส 63A", "MCB 3P 63A", "3-phase breaker 63A"],
    
    # === 🆕 3-Phase Wire Sizes ===
    "WIRE-THW-6.0": ["สาย THW 6.0", "สายไฟ 6 sq.mm"],
    "WIRE-THW-10.0": ["สาย THW 10", "สายไฟ 10 sq.mm"],
    "WIRE-THW-16.0": ["สาย THW 16", "สายไฟ 16 sq.mm"],
    "WIRE-THW-25.0": ["สาย THW 25", "สายไฟ 25 sq.mm"],
    
    # === 🆕 Solar Panels ===
    "SOLAR-PANEL-400W": [
        "แผงโซลาร์เซลล์ 400W", 
        "solar panel 400W mono", 
        "Jinko Tiger Pro 400W",
        "Canadian Solar 400W"
    ],
    "SOLAR-PANEL-550W": [
        "แผงโซลาร์เซลล์ 550W", 
        "solar panel 550W mono", 
        "LONGi Hi-MO 550W"
    ],
    
    # === 🆕 Solar Inverters ===
    "SOLAR-INV-3KW": [
        "อินเวอร์เตอร์ 3kW", 
        "solar inverter 3000W", 
        "Growatt MIN 3000TL-X",
        "Huawei SUN2000-3KTL"
    ],
    "SOLAR-INV-5KW": [
        "อินเวอร์เตอร์ 5kW", 
        "solar inverter 5000W", 
        "Huawei SUN2000-5KTL-M1",
        "Fronius Primo 5.0-1"
    ],
    "SOLAR-INV-8KW": [
        "อินเวอร์เตอร์ 8kW", 
        "solar inverter 8000W", 
        "SMA Sunny Boy 8.0"
    ],
    "SOLAR-INV-10KW": [
        "อินเวอร์เตอร์ 10kW", 
        "solar inverter 10000W", 
        "Fronius Symo 10.0-3-M",
        "Huawei SUN2000-10KTL-M1"
    ],
    
    # === 🆕 Solar Accessories ===
    "SOLAR-MC4": [
        "MC4 connector", 
        "สายต่อโซลาร์ MC4",
        "solar cable connector"
    ],
    "SOLAR-WIRE-4MM": [
        "สายโซลาร์ DC 4mm²", 
        "solar cable 4mm",
        "PV cable 4mm2"
    ],
    "SOLAR-WIRE-6MM": [
        "สายโซลาร์ DC 6mm²", 
        "solar cable 6mm",
        "PV cable 6mm2"
    ],
    
    # === 🆕 CT Meter ===
    "CT-METER-3P-100A": [
        "CT Meter 3 เฟส 100A", 
        "Current Transformer 100/5A",
        "มิเตอร์ CT 3 phase",
        "สำหรับ Solar Net Metering"
    ],
    
    # === 🆕 EV Chargers ===
    "EV-WALLBOX-7KW": [
        "EV Charger 7kW", 
        "Wallbox ชาร์จรถยนต์ไฟฟ้า 32A",
        "EV charging station 7000W"
    ],
    "EV-WALLBOX-11KW": [
        "EV Charger 11kW 3เฟส", 
        "Wallbox 16A 3P",
        "EV charging station 11kW 3-phase"
    ],
    "EV-WALLBOX-22KW": [
        "EV Charger 22kW 3เฟส", 
        "Wallbox 32A 3P",
        "EV charging station 22kW 3-phase"
    ],
}

# Also update MOCK_PRICES for testing:
MOCK_PRICES = {
    # Existing...
    
    # 3-Phase Breakers (higher price than 1P)
    "CB-3P-20A": [
        ("Schneider Official", 450.0),
        ("ABB Official", 480.0),
        ("Lazada", 380.0),
    ],
    "CB-3P-40A": [
        ("Schneider Official", 650.0),
        ("ABB Official", 680.0),
        ("Lazada", 550.0),
    ],
    
    # Solar Panels
    "SOLAR-PANEL-400W": [
        ("Jinko Official", 3500.0),
        ("Canadian Solar", 3800.0),
        ("Lazada", 3200.0),
    ],
    
    # Solar Inverters
    "SOLAR-INV-5KW": [
        ("Huawei Official", 28000.0),
        ("Growatt Dealer", 25000.0),
        ("Lazada", 22000.0),
    ],
    "SOLAR-INV-10KW": [
        ("Fronius Official", 65000.0),
        ("Huawei Official", 55000.0),
        ("Lazada", 48000.0),
    ],
    
    # CT Meter
    "CT-METER-3P-100A": [
        ("MEA Approved", 15000.0),
        ("PEA Approved", 14500.0),
    ],
    
    # EV Charger
    "EV-WALLBOX-7KW": [
        ("Schneider EVlink", 45000.0),
        ("Wallbox Pulsar Plus", 38000.0),
        ("Lazada Generic", 28000.0),
    ],
}
```

---

## 📋 Implementation Checklist

### Phase 1: Security (CRITICAL - Do FIRST)
- [ ] Enable Supabase Anonymous Auth in Dashboard
- [ ] Update `session_injector.create()` to use `auth.signInAnonymously()`
- [ ] Update RLS policies to use `auth.uid()` for both user types
- [ ] Test: Create guest session, verify unique UUID assigned
- [ ] Test: Guest cannot see other guest's sessions

### Phase 2: CRUD Fix
- [ ] Verify `projects.user_id` accepts anonymous UUIDs (if using Anonymous Auth)
- [ ] Test: Guest create session → save project → success
- [ ] Test: Guest load project → edit → save → success
- [ ] Test: Logged-in user cannot see guest projects

### Phase 3: Price Scraper
- [ ] Add 3-phase breakers to `SEARCH_TERMS`
- [ ] Add 3-phase wire sizes to `SEARCH_TERMS`
- [ ] Add solar panels (400W, 550W) to `SEARCH_TERMS`
- [ ] Add solar inverters (3kW, 5kW, 8kW, 10kW) to `SEARCH_TERMS`
- [ ] Add solar accessories (MC4, DC cables) to `SEARCH_TERMS`
- [ ] Add CT meter to `SEARCH_TERMS`
- [ ] Add EV chargers (7kW, 11kW, 22kW) to `SEARCH_TERMS`
- [ ] Update `MOCK_PRICES` with realistic prices
- [ ] Run scraper: `python price_scraper.py --update-all --mock`
- [ ] Verify BOQ pricing for 3-phase + solar projects

### Phase 4: Integration Testing
- [ ] Test full flow: Guest → 3-phase project → Save → Load → Edit
- [ ] Test full flow: User → Solar project → Save → Load → Edit
- [ ] Test BOQ pricing includes all new components
- [ ] Test MCP response includes solar_system + CT meter flag
- [ ] Verify no RLS violations in logs

---

## 🚀 Civil Mode Preparation Notes

**Current State**: Electrical mode fully supports 3-phase + solar + EV

**For Civil Mode Switch:**

1. **Schema Reusability**: 
   - `rooms`, `loads`, `site_context` JSONB can store civil data
   - `mcp_response` can store structural calculations
   - No schema changes needed

2. **Mode Detection**:
   ```python
   # In site_context:
   {
       "design_mode": "electrical",  # or "civil"
       "electrical_config": {...},   # electrical-specific
       "structural_config": {...}    # civil-specific (future)
   }
   ```

3. **Backend Switch**:
   - RAG service: Same (NLP → Spec)
   - MCP Core: **NEW** Civil calculation engine required
   - Database: No changes needed

4. **Recommended Architecture**:
   ```
   RAG Service (Port 8080)
       ↓
   Mode Router (NEW)
       ├─→ MCP Electrical (Port 5001) [Current]
       └─→ MCP Civil (Port 5002) [Future]
   ```

---

## 📚 References

**Related Files**:
- Schema: `Doc/DATABASE_SCHEMA_ANALYSIS.md` (this file)
- Session Store: `Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/session_store.py`
- Session Injector: `Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/context/session_injector.py`
- Price Scraper: `mcp_core_v2/core/price_scraper.py`
- Catalog: `mcp_core_v2/catalog_rows.csv`

**Testing**:
- MAX Difficulty Tests: `tests/test_max_difficulty_verification.py`
- Integration Tests: `tests/test_integration_suite.py`

---

*Last Updated: December 2025*  
*Analysis by: Aura (Code Goddess) + Opsia (DevOps Sovereign)*
