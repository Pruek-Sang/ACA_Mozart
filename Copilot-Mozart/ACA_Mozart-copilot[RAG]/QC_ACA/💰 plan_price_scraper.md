# 💰 แผน Daily Price Scraper & BOQ Integration

## 🎯 เป้าหมาย
สร้างระบบดึงราคาอุปกรณ์ไฟฟ้าจากเว็บจริง (ThaiWatsadu, HomePro, Lazada) แบบ **Batch/Cache** เพื่อให้ BOQ แสดงราคาจริงโดยไม่ทำให้ SQL บวม

---

## 📊 Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│              GitHub Actions (Scheduled Daily)                   │
│  ┌─────────────────┐              ┌─────────────────────────┐  │
│  │ price_scraper.py│ ──scrape──→  │ catalog/prices.csv      │  │
│  │                 │  ThaiWatsadu │ (auto commit + push)    │  │
│  │                 │  HomePro     └─────────────────────────┘  │
│  │                 │  Lazada                                    │
│  └─────────────────┘                                            │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (Docker build รวม csv)
┌────────────────────────────────────────────────────────────────┐
│                     Cloud Run (Runtime)                         │
│  ┌─────────────────┐              ┌─────────────────────────┐  │
│  │ boq_service.py  │ ──read──→    │ prices.csv (in RAM)     │  │
│  │                 │  (startup)   │ No SQL Connection!      │  │
│  └─────────────────┘              └─────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## ✅ Tasks Checklist

### Phase 1: Price Scraper Workflow
- [ ] สร้าง `catalog/prices.csv` (skeleton)
- [ ] สร้าง `.github/workflows/price-scraper.yml`
- [ ] ทดสอบ scrape ด้วย GitHub Actions
- [ ] ตั้ง Schedule: ทุกวัน 00:00 (เวลาไทย)

### Phase 2: BOQ Integration
- [ ] แก้ `boq_service.py` อ่าน `prices.csv`
- [ ] แก้ `api.py` endpoint `/boq/{session_id}`
- [ ] ทดสอบ BOQ output กับราคาจริง

### Phase 3: Fix Electrical Design Bugs
- [ ] รอ GitHub Actions build เสร็จ (balanced algorithm)
- [ ] ทดสอบ 19 outlets → 2 circuits (ไม่ใช่ 3)
- [ ] ยืนยัน MCB count ลดลง

---

## 📁 Files to Create/Modify

### [NEW] `.github/workflows/price-scraper.yml`
```yaml
name: 💰 Daily Price Scraper

on:
  schedule:
    - cron: '0 17 * * *'  # 00:00 Thailand Time (UTC+7)
  workflow_dispatch:       # Manual trigger

jobs:
  scrape-prices:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4
      
      - name: Run Price Scraper
        run: |
          cd mcp_core_v2
          python -m core.price_scraper --output catalog/prices.csv
      
      - name: Commit & Push prices.csv
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "bot@github.com"
          git add mcp_core_v2/catalog/prices.csv
          git commit -m "📊 Update prices $(date +'%Y-%m-%d')" || exit 0
          git push
```

### [NEW] `mcp_core_v2/catalog/prices.csv`
```csv
item_code,description,price_thb,source,last_updated
MCB-15A-1P,MCB 15A 1P Schneider,185,ThaiWatsadu,2025-12-19
MCB-20A-1P,MCB 20A 1P Schneider,195,HomePro,2025-12-19
RCBO-30A-2P,RCBO 30mA 30A 2P,890,Lazada,2025-12-19
THW-2.5,สายไฟ THW 2.5mm² (100m),1250,ThaiWatsadu,2025-12-19
THW-4.0,สายไฟ THW 4.0mm² (100m),1850,HomePro,2025-12-19
THW-6.0,สายไฟ THW 6.0mm² (100m),2450,ThaiWatsadu,2025-12-19
```

### [MODIFY] `mcp_core_v2/core/price_scraper.py`
- เพิ่ม `--output` argument
- เพิ่ม function `save_to_csv()`
- แก้ให้เขียนผล scrape ลง CSV

### [MODIFY] `mcp_core_v2/core/boq_service.py`
- แก้ให้อ่าน `catalog/prices.csv` ตอน startup
- Cache prices ใน memory (Python dict)
- lookup ราคาจาก cache แทน scrape runtime

---

## 🛡️ Risk Mitigation

| Risk | Mitigation |
|------|------------|
| เว็บ block IP | ใช้ delay ระหว่าง request + rotate User-Agent |
| เว็บเปลี่ยน HTML | Fallback เป็น Mock ถ้า scrape fail |
| CSV ไม่ถูก commit | ตั้ง alert ถ้า workflow fail |
| ราคาผิดพลาด | Validate range (ราคาต้อง > 0, < 100,000) |

---

## 📅 Timeline

| Day | Task |
|-----|------|
| **Today** | สร้าง skeleton CSV + workflow |
| **Tonight** | ทดสอบ manual trigger |
| **Tomorrow** | ยืนยัน auto-run 00:00 |
| **+2 Days** | Fix bugs + integrate BOQ |

---

## 🔗 Dependencies

- `requests` (already in requirements)
- `beautifulsoup4` (need to add)
- GitHub Actions enabled
- Git permissions for bot commit

---

*Created: 2025-12-19*
*Status: Planning*
