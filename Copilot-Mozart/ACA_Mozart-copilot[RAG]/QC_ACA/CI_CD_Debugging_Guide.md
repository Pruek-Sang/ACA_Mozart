# 🔧 CI/CD Debugging Guide

> **สำหรับ:** AI หรือ Dev ที่มารับงานต่อและเจอปัญหา CI/CD
> **Updated:** 2026-01-02

---

## 🚨 Quick Diagnosis Table

| Error | Most Likely Cause | Fix |
|-------|------------------|-----|
| `test-supabase` FAILED | `SUPABASE_SERVICE_KEY` missing or wrong syntax | Check secrets + use `client.schema("mozart").table()` |
| `smoke-test` FAILED | Deploy succeeded but app broken | Check RAG logs, Supabase connection |
| `test-e2e` FAILED | MCP/RAG contract mismatch | Compare `api.py` vs `mcp_adapter.py` fields |
| `test-frontend-lint` FAILED | React Hooks violation | Check hooks are before conditionals |
| `rollback` triggered | Smoke failed, rolled back | Check previous revision in Cloud Run |
| Build timeout | Docker cache issue | Force rebuild with `--no-cache` |

---

## 📁 Key Files to Check

### When Tests Fail:
```
tests/
├── test_supabase_schema.py   ← Supabase connection issues
├── test_smoke_production.py  ← Post-deploy issues
├── test_gateway_router.py    ← Routing logic bugs
├── test_rag_mcp_contract.py  ← API schema mismatch
└── chaos/test_resilience.py  ← Fallback handling
```

### When Deploy Fails:
```
.github/workflows/docker-build.yml  ← Line 604+ for smoke/rollback
Copilot-Mozart/.../app/routes.py    ← Line 147-149 for health check
Copilot-Mozart/.../app/context/supabase_client.py ← Line 80-83
```

---

## 🔍 Common Issues & Solutions

### 1. Error #310 (React Hooks)
**Symptom:** Frontend crashes with "Minified React error #310"
**Root Cause:** Usually backend returning null/undefined data
**Debug Path:**
1. Check RAG `/` endpoint → Is `supabase: "connected"`?
2. Check `compute.py` → Is display_data returning all fields?
3. Check `ResultViewer.tsx` → Are all hooks before conditionals?

### 2. Supabase Schema Error
**Symptom:** `test-supabase` fails with "table not found"
**Root Cause:** Wrong query syntax
**Fix:** Use `client.schema("mozart").table("sessions")` NOT `client.table("mozart.sessions")`

### 3. Smoke Test Fail After Deploy
**Symptom:** Deploy succeeds, smoke fails
**Debug:**
1. Check Cloud Run logs: `gcloud logging read "resource.labels.service_name=mozart-rag" --limit=50`
2. Test manually: `curl https://mozart-rag-xxx.run.app/`
3. Check if Supabase IP whitelist includes Cloud Run

### 4. Rollback Was Triggered
**Symptom:** Alert says rollback executed
**What Happened:** Smoke test failed → pipeline auto-rolled back
**Recovery:**
1. Check which revision is now active
2. Find the failing revision's logs
3. Fix the issue and redeploy

---

## 🧪 Manual Test Commands

```bash
# Test Supabase locally
export SUPABASE_URL="..."
export SUPABASE_SERVICE_ROLE_KEY="..."
pytest tests/test_supabase_schema.py -v

# Test Smoke locally
pytest tests/test_smoke_production.py -v

# Test Gateway Router
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]
pytest ../tests/test_gateway_router.py -v

# Run K6 load test
k6 run tests/load/stress-test.js
```

---

## 📊 Workflow Debug Tips

### See full CI output:
1. Go to GitHub Actions → Click failed job
2. Expand failed step → Read error message
3. Check "Annotations" at bottom

### Force re-run specific job:
1. Click "Re-run jobs" → Select specific job
2. Or re-push empty commit: `git commit --allow-empty -m "ci: retry"`

### Skip CI temporarily:
```bash
git commit -m "fix: something [skip ci]"
```

---

## 🔗 Related Docs

- [Blackbox_Workflow_Architecture.md](file:///home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/QC_ACA/Blackbox_Workflow_Architecture.md) - Data flow diagram
- [MEMORY - ความผิดพลาดที่ห้ามทำซ้ำ.md](file:///home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/QC_ACA/MEMORY%20-%20ความผิดพลาดที่ห้ามทำซ้ำ.md) - Known issues list
