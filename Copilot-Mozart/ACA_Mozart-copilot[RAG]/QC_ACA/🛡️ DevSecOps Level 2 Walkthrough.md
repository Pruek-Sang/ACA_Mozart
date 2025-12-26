# 🛡️ DevSecOps Level 2 Walkthrough

**วันที่:** 26 ธ.ค. 2567  
**สถานะ:** ✅ Verified & Deployed

---

## 📋 สรุป Phase ที่ทำ

| Phase | งาน | สถานะ | ตรวจสอบ |
|-------|-----|-------|---------|
| 1 | Scaling (min=0, max=10) | ✅ | docker-build.yml:344-345, 369-370 |
| 2 | Alerting (5xx > 5 in 5min) | ✅ | GCP Policy ID: 9628039011910464929 |
| 3 | Retry Logic (3 attempts) | ✅ | mcp_client.py:159-222 |
| 4 | Secret Manager | ✅ | gemini-key:latest |
| 5 | Cloud Armor | ⏸️ | รอมีงบ (~$5-15/mo) |

---

## 🔐 Phase 4: Secret Manager Verification

```bash
# ตรวจสอบ Secret
$ gcloud secrets describe gemini-key --project=gen-lang-client-0658701327
NAME                                      CREATE_TIME
projects/203658178245/secrets/gemini-key  2025-12-26T16:48:02Z  ✅

# Cloud Run ใช้ --set-secrets
--set-secrets=GOOGLE_API_KEY=gemini-key:latest  ✅
```

---

## 🔔 Phase 2: Alerting Verification

```bash
$ gcloud alpha monitoring policies list --project=gen-lang-client-0658701327
DISPLAY_NAME             ENABLED
Mozart Error Rate Alert  True  ✅
```

**Trigger Condition:**
- Cloud Run 5xx errors > 5 ครั้ง ใน 5 นาที

---

## 🔄 Phase 3: Retry Logic

**ไฟล์:** `app/mcp_client.py` line 159-222

```python
max_retries = 3
retry_delays = [1, 2, 4]  # exponential backoff

for attempt in range(max_retries):
    try:
        response = await client.post(url, json=payload)
        # success → return
    except (httpx.TimeoutException, httpx.ConnectError):
        await asyncio.sleep(delay)
        # retry
```

---

## ⚠️ Security Scan Results

| Item | Status |
|------|--------|
| **Hardcoded API Key in .py/.yml** | ✅ ไม่พบ |
| **Hardcoded API Key in Doc files** | ⚠️ พบ (แต่เป็น historical docs) |
| **Secret in GCP** | ✅ gemini-key:latest |
| **IAM Access** | ✅ Cloud Run SA granted |

---

## 📁 Files Changed

| File | Changes |
|------|---------|
| `docker-build.yml` | +min/max instances, +--set-secrets |
| `mcp_client.py` | +retry logic with exponential backoff |
| `scripts/gcp_infra_setup.sh` | NEW: Phase 4-5 commands |

---

## 🚨 How to Debug

| ปัญหา | ดูที่ไหน |
|-------|---------|
| Deploy พัง | GitHub Actions → Logs |
| RAG/MCP ไม่ทำงาน | GCP Console → Cloud Run → Logs |
| Alert ไม่ส่ง | GCP Console → Monitoring → Alerting |
| Secret ผิด | GCP Console → Secret Manager |
| Retry ไม่ทำงาน | RAG logs: ดูคำว่า "attempt 1/3" |

---

## 📊 Security Level Assessment

| Level | Status |
|-------|--------|
| **Level 1 (MVP)** | ✅ Passed |
| **Level 2 (Startup)** | ✅ Passed (Phase 1-4) |
| **Level 3 (Enterprise)** | ❌ ยังไม่ได้ (VPC, WAF, Pentest) |

---

## 🔗 Git Commits

| Commit | Description |
|--------|-------------|
| `445d82a` | Phase 1 (Scaling) + Phase 3 (Retry) |
| `2caba32` | min=0 (ประหยัดตังค์) |
| `3061877` | GCP setup script |
| `e30747e` | Phase 4 - Secret Manager |
