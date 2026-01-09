# 🔴 FULL CLOUD LOG FINDINGS

> **Date**: 2026-01-09  
> **Status**: ✅ **BUG CONFIRMED 100% via Browser Test**  
> **Recording**: [session_debug_test.webp](./session_debug_test_1767974999980.webp)

---

## 🎯 ROOT CAUSE CONFIRMED:

### **Frontend Bug: Stale Session ID Not Cleared**

**Location**: `App.tsx` Line 207-211

```typescript
} catch (e: any) {
  logger.warn('[SESSION] Fetch failed', { error: e.message, sessionId: id });
  // ❌ BUG: ไม่ clear localStorage และไม่สร้าง session ใหม่!
} finally {
  setIsSessionLoading(false);
}
```

---

## 🧪 Browser Test Evidence:

### Scenario 1: Stale ID in localStorage
1. ตั้ง localStorage: `mozart_session_id = "stale-session-id-123"`
2. กด Guest mode
3. **ผล**: `GET /api/v1/session/stale.../data` → **404 Not Found**
4. **localStorage ยังคงเป็น stale ID** (ไม่ clear)
5. **sessionId state = null** (ไม่ได้ set)
6. ส่ง `/ask` → **ไม่มี ?session_id ใน URL** → Backend รับ None

### Scenario 2: Fresh Start (ทำงานปกติ)
1. Clear localStorage
2. กด Guest mode
3. **ผล**: Session created → `5380e9a6...`
4. **localStorage = session ID ใหม่**
5. ส่ง `/ask?session_id=5380e9a6...` → **ทำงานถูกต้อง**

---

## � Evidence Summary:

| Test Case | localStorage | Session Created | /ask URL | Backend |
|-----------|-------------|----------------|----------|---------|
| Stale ID | `stale-xxx` | ❌ No (404) | `/ask` (no param) | `None` |
| Fresh | (empty) | ✅ `5380e9a6` | `/ask?session_id=...` | OK |

---

## �️ Fix Required:

**File**: `frontend/src/App.tsx` Line 207-211

```typescript
} catch (e: any) {
  logger.warn('[SESSION] Fetch failed', { error: e.message, sessionId: id });
  
  // 🆕 FIX: Clear stale ID and create new session
  localStorage.removeItem('mozart_session_id');
  setSessionId(null);  // Force new session creation
  
  // Create new session
  try {
    const result = await startSession();
    setSessionId(result.session_id);
    setProjectName(result.project_name || 'บ้านนายสมหญิง');
    logger.info('✅ Created new session after stale ID', { sessionId: result.session_id });
  } catch (createError: any) {
    logger.error('❌ Failed to create new session', { error: createError.message });
  }
} finally {
  setIsSessionLoading(false);
}
```

---

## 📋 Fix Priority:

1. **[CRITICAL]** Clear localStorage เมื่อ fetch fail (404)
2. **[CRITICAL]** สร้าง session ใหม่เมื่อ stale ID detected
3. **[HIGH]** Backend: Log `[AUTO-SAVE] Skipped: session_id=None`

---

*Verified via Browser Test on 2026-01-09*
