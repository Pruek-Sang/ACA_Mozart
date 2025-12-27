# 🧠 Stateful Intelligence Implementation - Walkthrough

> **Version:** 1.0.0 | **Date:** 2025-12-28

---

## ✅ What Was Done

### Phase 1: Database Setup (By User)

**SQL schema executed in Supabase SQL Editor:**

| Table | Schema | Purpose |
|-------|--------|---------|
| `mozart.sessions` | `mozart` | Temporary working sessions (24h auto-expire) |
| `mozart.projects` | `mozart` | Permanent saved designs with versioning |

**Features included:**
- ✅ RLS (Row Level Security) - Users only see their own data
- ✅ GIN indexes for JSONB columns (fast queries)
- ✅ Triggers for auto `updated_at`
- ✅ CHECK constraints for status/stage values
- ✅ Versioning support (`parent_id`, `version`)
- ✅ Cleanup function for expired sessions

---

### Phase 2: Backend Code (By Valida)

#### New `app/context/` Folder (Data Access Layer)

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `supabase_client.py` | Backend Supabase connection with lazy init |
| `session_injector.py` | Full CRUD for `mozart.sessions` |
| `project_injector.py` | Full CRUD for `mozart.projects` with versioning |

#### New `app/middleware/` Folder

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `rate_limiter.py` | In-memory rate limiting for expensive API calls |

---

## 📁 New File Structure

```
app/
├── context/                    🆕 NEW!
│   ├── __init__.py
│   ├── supabase_client.py      # DB connection
│   ├── session_injector.py     # Session CRUD
│   └── project_injector.py     # Project CRUD + versioning
│
├── middleware/                 🆕 NEW!
│   ├── __init__.py
│   └── rate_limiter.py         # Rate limiting
│
├── routes.py                   # (Existing - needs integration)
├── service.py                  # (Existing - needs integration)
└── session_store.py            # (Existing - in-memory, still works)
```

---

## 🔧 Environment Variables Required

Add these to your deployment (Cloud Run, `.env`, etc.):

```bash
# Supabase Backend Connection
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # Service role key (NOT anon key!)
```

> ⚠️ **Security Note:** Use `SUPABASE_SERVICE_ROLE_KEY` for backend, NOT `SUPABASE_ANON_KEY`.

---

## 📋 Next Steps (TODO)

| # | งาน | สถานะ |
|---|-----|:------:|
| 1 | ✅ เพิ่ม `supabase>=2.0.0` ใน requirements | ✅ Done |
| 2 | ✅ แก้ `docker-build.yml` เพิ่ม secrets | ✅ Done |
| 3 | ✅ อัพเดท `gcp_infra_setup.sh` | ✅ Done |
| 4 | 🔐 สร้าง Secrets ใน GCP (นายท่านทำ) | ⏳ Pending |
| 5 | Integrate injectors ใน routes.py | ⏳ Next Phase |

---

## 🔐 GCP Secret Manager Setup (นายท่านต้องทำ)

### Quick Commands:
```bash
# 1. สร้าง Supabase URL secret
echo -n "https://YOUR_PROJECT.supabase.co" | \
  gcloud secrets create supabase-url --data-file=- \
  --project=gen-lang-client-0658701327

# 2. สร้าง Service Role Key secret  
echo -n "eyJ...YOUR_SERVICE_KEY..." | \
  gcloud secrets create supabase-service-key --data-file=- \
  --project=gen-lang-client-0658701327

# 3. Grant access ให้ Cloud Run
SA="203658178245-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding supabase-url \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gen-lang-client-0658701327

gcloud secrets add-iam-policy-binding supabase-service-key \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gen-lang-client-0658701327
```

### หา Supabase Service Role Key ได้ที่:
1. ไป Supabase Dashboard → Project Settings → API
2. Copy **service_role** key (ไม่ใช่ anon key!)

---

## 📊 Architecture Comparison

### Before (Stateless)

```
Frontend ──→ Gateway ──→ RAG (service.py) ──→ MCP Core
                              ↓
                         In-memory only
                         (Lost on restart!)
```

### After (Stateful)

```
Frontend ──→ Gateway ──→ RAG (service.py) ──→ MCP Core
                              ↓
                    session_injector.py
                              ↓
                    Supabase (mozart.sessions)
                              ↓
                    project_injector.py
                              ↓
                    Supabase (mozart.projects)
```

---

## 🧪 Verification Commands

```bash
# Check new files exist
ls -la /home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/context/
ls -la /home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/app/middleware/

# Test import (after installing supabase-py)
cd /home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]
python -c "from app.context import session_injector, project_injector; print('✅ Imports OK')"
```

---

## 💡 Usage Examples

### Using Session Injector

```python
from app.context import session_injector

# Create session
session = await session_injector.create(user_id="xxx-xxx-xxx")

# Load session
session = await session_injector.load(session_id="yyy-yyy-yyy")

# Update design
await session_injector.update_design(
    session_id=session.id,
    rooms=[{"name": "ห้องนอน", "loads": [...]}],
    site_context={"distance_to_transformer": "80m"}
)

# Migrate to project
project_id = await session_injector.migrate_to_project(session.id, "บ้านพักอาศัย 2 ชั้น")
```

### Using Rate Limiter

```python
from app.middleware import rate_limiter, RateLimitExceeded

try:
    rate_limiter.check(user_id="xxx", endpoint="design")
    # ... expensive LLM call ...
except RateLimitExceeded as e:
    return {"error": str(e), "retry_after": e.retry_after}
```

---

*Walkthrough by Valida - 2025-12-28*
