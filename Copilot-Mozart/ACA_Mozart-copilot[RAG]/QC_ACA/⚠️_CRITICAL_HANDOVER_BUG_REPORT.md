# 🛑 CRITICAL HANDOVER REPORT: 0 LOADS & 422 ERROR BUGS

> [!CAUTION]
> **CRITICAL PRIORITY - DO NOT IGNORE**
> **THIS BUG BREAKS PRODUCTION. FIXES ARE READY LOCALLY BUT NOT DEPLOYED.**

**Date:** 2025-12-23
**Status:** 🔴 Fixes Ready Locally, PENDING PUSH

---

## 🎯 The Core Problems (System Down)
1.  **"0 Loads" in Output:** User sees a formatted Load Schedule but with 0 items. **(MAJOR UX FAIL)**
2.  **422 Unprocessable Entity:** Gateway sends numeric values for `site_context`, but previous model expected strings. **(API FAIL)**
3.  **Site Context Blocking:** User currently sees `⚠️ Missing site_context fields` logs, blocking the design flow.

---

## 🛠️ Root Cause Analysis (LOGIC FAULTS FOUND)

### 1. The "0 Loads" Bug (SOLVED LOCALLY)
*   **SYMPTOM:** User gets a beautiful report, but the "Load Schedule" table has 0 rows.
*   **ROOT CAUSE:** The markdown formatter relies on `mcp_result['request']['loads']`. However, the `McpClient.to_dict()` method **was silently discarding the `request` object** from the MCP Core response.
*   **THE FIX (Local):** Updated `app/mcp_client.py` to explicitly include `request` and `summary` in the `to_dict()` return value.
*   **Commit:** `237acc3`

### 2. The 422 Error (SOLVED LOCALLY)
*   **SYMPTOM:** API calls fail with 422 immediately.
*   **ROOT CAUSE:** `QueryRequest.site_context` was strictly defined as `Dict[str, str]`. Gateway sends float values (e.g., `service_distance_m: 50.0`), violating strict typing.
*   **THE FIX (Local):** Relaxed type to `Optional[Dict[str, Any]]` in `app/models.py`.
*   **Commit:** `df6191c`

---

## 📂 Critical Files (DO NOT REVERT THESE FIXES)
*   `app/mcp_client.py`: **MUST** include `request` in `to_dict()`.
*   `app/models.py`: **MUST** use `Dict[str, Any]` for `site_context`.

---

## ⏭️ IMMEDIATE ACTION REQUIRED

> [!IMPORTANT]
> **THE CODE ON LOCAL IS CORRECT. THE CODE ON CLOUD IS BROKEN.**
> **YOU MUST PUSH TO DEPLOY.**

1.  **PUSH THE FIXES:**
    ```bash
    git push pruek-sang main
    ```
2.  **Verify Deployment:** Wait for Cloud Run to update.
3.  **Test:** verify that "0 loads" is gone and 422 errors are resolved.
