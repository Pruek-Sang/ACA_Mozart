# 🔧 Technical Debt Tracker

**Last Updated:** 2026-01-03

---

## ⚠️ INCOMPLETE IMPLEMENTATIONS

### 1. download_guard.py (LOW Priority)

**File:** `app/middleware/download_guard.py`

**Status:** ❌ Skeleton only - all methods raise `NotImplementedError`

**What's Missing:**
| Method | Purpose | Status |
|--------|---------|--------|
| `create_token()` | Generate download token | ❌ TODO |
| `validate_token()` | Check if token valid | ❌ TODO |
| `mark_used()` | Mark token as used | ❌ TODO |
| `check_rate_limit()` | Check download quota | ❌ TODO |
| `log_download()` | Log download for audit | ❌ TODO |
| `generate_watermark()` | Embed watermark in Excel | ❌ TODO |

**Impact:** None - Core download works without tracking

**Why Deferred:** Feature not critical for MVP

**To Implement:**
1. Create Supabase table: `download_tokens`, `download_logs`
2. Implement token generation (UUID4)
3. Add rate limiting (10/hour/user)
4. Connect to middleware in `routes.py`

**Estimated Effort:** 1-2 hours

---

## ✅ COMPLETED TECHNICAL DEBT

| Item | Resolved Date | Notes |
|------|--------------|-------|
| Session Integration | 2026-01-03 | Unified session_store + session_injector |
| HistoryPanel connectivity | 2026-01-03 | revisionHistory now passed from App |
| FeedbackModal API | 2026-01-03 | Connected to /api/v1/feedback |

---

## 📊 Debt Summary

| Category | Count | Priority |
|----------|-------|----------|
| ❌ Incomplete | 1 | LOW |
| ✅ Resolved | 3 | - |
