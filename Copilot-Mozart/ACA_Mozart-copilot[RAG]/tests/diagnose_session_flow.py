#!/usr/bin/env python3
"""
🔬 Session Flow Diagnostic Tool
================================
This script simulates the EXACT user journey to pinpoint where data loss occurs.

Usage:
    # Against local server (default)
    python tests/diagnose_session_flow.py

    # Against production
    python tests/diagnose_session_flow.py --url https://your-api.com

What it tests:
    1. POST /api/v1/session/start → Create new session
    2. POST /api/v1/ask → Send design request (simulates user chat)
    3. GET /api/v1/session/{id}/data → Fetch session data (simulates page refresh)
    4. COMPARE → Is the data we sent still there after "refresh"?

If this script says FAIL, it tells you EXACTLY where the chain broke.
"""

import argparse
import json
import sys
import time
from datetime import datetime

# Try to import httpx (preferred) or fall back to requests
try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    try:
        import requests
        HTTP_CLIENT = "requests"
    except ImportError:
        print("❌ ERROR: Please install httpx or requests: pip install httpx")
        sys.exit(1)


def make_request(method: str, url: str, json_data: dict = None, headers: dict = None):
    """Unified request function for httpx/requests."""
    if HTTP_CLIENT == "httpx":
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, json=json_data, headers=headers)
            elif method == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unknown method: {method}")
            return response.status_code, response.json() if response.content else {}
    else:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=json_data, headers=headers, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unknown method: {method}")
        return response.status_code, response.json() if response.content else {}


def log_step(step_num: int, name: str, status: str, details: str = ""):
    """Pretty print a step result."""
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
    print(f"  [{step_num}] {icon} {name}: {status}")
    if details:
        print(f"      └─ {details}")


def run_diagnostic(base_url: str, auth_token: str = None):
    """Run the full session diagnostic flow."""
    print("=" * 60)
    print("🔬 SESSION FLOW DIAGNOSTIC")
    print(f"   Target: {base_url}")
    print(f"   Time: {datetime.now().isoformat()}")
    print("=" * 60)

    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    results = []
    session_id = None

    # ═══════════════════════════════════════════════════════════════
    # STEP 1: Create Session
    # ═══════════════════════════════════════════════════════════════
    print("\n📋 STEP 1: Create Session (POST /api/v1/session/start)")
    try:
        status, data = make_request(
            "POST",
            f"{base_url}/api/v1/session/start",
            json_data={"project_name": f"Diagnostic_{int(time.time())}"},
            headers=headers
        )
        if status == 200 and "session_id" in data:
            session_id = data["session_id"]
            log_step(1, "Create Session", "PASS", f"session_id = {session_id[:16]}...")
            results.append(("Create Session", True))
        else:
            log_step(1, "Create Session", "FAIL", f"Status={status}, Response={data}")
            results.append(("Create Session", False))
            return results  # Cannot continue
    except Exception as e:
        log_step(1, "Create Session", "FAIL", f"Exception: {e}")
        results.append(("Create Session", False))
        return results

    # ═══════════════════════════════════════════════════════════════
    # STEP 2: Send Design Request (simulates user chat)
    # ═══════════════════════════════════════════════════════════════
    print("\n📋 STEP 2: Send Design Request (POST /api/v1/ask)")
    test_prompt = "ออกแบบบ้าน 2 ชั้น ห้องนอน 2 ห้องน้ำ 2"
    try:
        status, data = make_request(
            "POST",
            f"{base_url}/api/v1/ask?session_id={session_id}",
            json_data={"prompt": test_prompt},
            headers=headers
        )
        if status == 200 and "answer" in data:
            log_step(2, "Send Design Request", "PASS", f"Got answer: {data['answer'][:50]}...")
            results.append(("Send Design Request", True))

            # Check if metadata is present (this is the data we need to persist)
            if data.get("metadata", {}).get("display_data"):
                log_step(2, "Design Data Present", "PASS", "display_data found in response")
            else:
                log_step(2, "Design Data Present", "WARN", "No display_data in response (might be OK for simple prompts)")
        else:
            log_step(2, "Send Design Request", "FAIL", f"Status={status}, Response={json.dumps(data)[:100]}")
            results.append(("Send Design Request", False))
    except Exception as e:
        log_step(2, "Send Design Request", "FAIL", f"Exception: {e}")
        results.append(("Send Design Request", False))

    # ═══════════════════════════════════════════════════════════════
    # STEP 3: Simulate "Page Refresh" → Fetch Session Data
    # ═══════════════════════════════════════════════════════════════
    print("\n📋 STEP 3: Fetch Session Data (GET /api/v1/session/{id}/data) - Simulates Refresh")
    try:
        status, data = make_request(
            "GET",
            f"{base_url}/api/v1/session/{session_id}/data",
            headers=headers
        )
        if status == 200:
            log_step(3, "Fetch Session Data", "PASS", f"Status=200")
            results.append(("Fetch Session Data", True))

            # Check critical fields
            has_project_name = bool(data.get("project_name"))
            has_mcp_response = bool(data.get("mcp_response"))
            has_messages = bool(data.get("messages"))

            log_step(3, "project_name exists", "PASS" if has_project_name else "FAIL")
            log_step(3, "mcp_response exists", "PASS" if has_mcp_response else "WARN")
            log_step(3, "messages exists", "PASS" if has_messages else "WARN")

            # If mcp_response has display_data, that's the gold standard
            if has_mcp_response and data.get("mcp_response", {}).get("display_data"):
                log_step(3, "display_data preserved", "PASS", "Design results are intact!")
                results.append(("Data Integrity", True))
            else:
                log_step(3, "display_data preserved", "FAIL", "⚠️ THIS IS THE BUG! Design data was lost!")
                results.append(("Data Integrity", False))

        elif status == 404:
            log_step(3, "Fetch Session Data", "FAIL", "❌ 404 Not Found - Session was NOT persisted to database!")
            results.append(("Fetch Session Data", False))
        else:
            log_step(3, "Fetch Session Data", "FAIL", f"Status={status}, Response={data}")
            results.append(("Fetch Session Data", False))
    except Exception as e:
        log_step(3, "Fetch Session Data", "FAIL", f"Exception: {e}")
        results.append(("Fetch Session Data", False))

    # ═══════════════════════════════════════════════════════════════
    # STEP 4: Cleanup (Optional - Delete Session)
    # ═══════════════════════════════════════════════════════════════
    print("\n📋 STEP 4: Cleanup (DELETE /api/v1/session/{id}?confirm=CONFIRM)")
    try:
        status, data = make_request(
            "DELETE",
            f"{base_url}/api/v1/session/{session_id}?confirm=CONFIRM",
            headers=headers
        )
        if status == 200:
            log_step(4, "Delete Session", "PASS", "Cleaned up test session")
        else:
            log_step(4, "Delete Session", "SKIP", f"Status={status} (not critical)")
    except Exception as e:
        log_step(4, "Delete Session", "SKIP", f"Exception: {e} (not critical)")

    # ═══════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)

    all_passed = all(r[1] for r in results)
    for name, passed in results:
        print(f"  {'✅' if passed else '❌'} {name}")

    print("\n" + "-" * 60)
    if all_passed:
        print("🎉 RESULT: ALL CHECKS PASSED!")
        print("   Session CRUD is working correctly.")
    else:
        print("💀 RESULT: SOME CHECKS FAILED!")
        print("   Review the failed steps above to identify the issue.")
        print("\n   Common causes:")
        print("   • 404 on Step 3 → Backend not saving to Supabase")
        print("   • display_data missing → Auto-save not triggered after /ask")
        print("   • Network error → Check if server is running")

    return results


def main():
    parser = argparse.ArgumentParser(description="Session Flow Diagnostic Tool")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional: Bearer token for authenticated requests"
    )
    args = parser.parse_args()

    results = run_diagnostic(args.url, args.token)

    # Exit with error code if any test failed
    if not all(r[1] for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
