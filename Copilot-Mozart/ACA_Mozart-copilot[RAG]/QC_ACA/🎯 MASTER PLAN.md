# 🎯 MASTER PLAN: Mozart UI/UX Enhancement Suite

## 📋 Overview

**เป้าหมาย:** ยกระดับ Mozart จาก MVP → Production-Ready Product

| Feature | Priority | Status | Depends On |
|---------|----------|--------|------------|
| 🎛️ Smart Form + Reactive | P1 | 📄 Planned | Deck UI |
| 🃏 Deck UI Overhaul | P1 | 📄 Planned | - |
| 💰 Daily Price Scraper | P2 | 📄 Planned | - |
| ⏳ Loading Mascot | P2 | 📄 Planned | - |
| 📜 White Label | P3 | 📄 Planned | - |
| 🔐 QR Verification | P4 | 📄 Planned | White Label |

---

## 🔀 Execution Order (Critical Path)

```mermaid
graph LR
    subgraph Phase1["Phase 1: Foundation"]
        A[Bug Fixes] --> B[Deck UI]
        A --> C[Price Scraper]
        A --> D[Loading Mascot]
    end
    
    subgraph Phase2["Phase 2: Core Features"]
        B --> E[Smart Form]
        C --> F[BOQ Integration]
    end
    
    subgraph Phase3["Phase 3: Premium"]
        E --> G[White Label]
        G --> H[QR Verification]
    end
```

---

## ✅ Pre-requisites (ต้องเสร็จก่อนเริ่ม)

- [x] วสท. outlet counting fix (commit `8c0c2cc`)
- [x] SLD/BOQ endpoints (commit `bef41e3`)
- [x] CI/CD path triggers fix (commit `437ef18`)
- [ ] ⏳ รอ GitHub Actions deploy ใหม่
- [ ] ⏳ Verify 19 outlets → 2 circuits

---

# 📦 PHASE 1: Foundation (Week 1)

## 1.1 🃏 Deck UI Overhaul

> **เป้าหมาย:** เปลี่ยนจาก Phone Frame → Card Stack

### Files to Create:
| File | Type | Description |
|------|------|-------------|
| `DeckContainer.tsx` | NEW | Container จัดการ card stack |
| `Card.tsx` | NEW | Generic card wrapper |
| `DeckLayout.css` | NEW | Animations & layout |

### Files to Modify:
| File | Change |
|------|--------|
| `App.tsx` | เปลี่ยนจาก PhoneFrame → DeckContainer |
| `index.css` | เพิ่ม deck styles |

### Sub-tasks:
- [ ] 1.1.1 Create `DeckContainer.tsx` skeleton
- [ ] 1.1.2 Create `Card.tsx` with header/body/footer
- [ ] 1.1.3 Implement card stacking CSS (z-index, transforms)
- [ ] 1.1.4 Add "Overview Mode" toggle button
- [ ] 1.1.5 Add fan-out animation (CSS keyframes)
- [ ] 1.1.6 Port ChatPane to Card 1
- [ ] 1.1.7 Create LoadScheduleCard (Card 2)
- [ ] 1.1.8 Create SLDCard with lazy fetch (Card 3)
- [ ] 1.1.9 Create BOQCard with lazy fetch (Card 4)
- [ ] 1.1.10 Port FloorPlanViewer to Card 5

### Error Prevention:
- [ ] ⚠️ ไม่ลบ PhoneFrame - เก็บไว้ fallback
- [ ] ⚠️ Test responsive ทุก breakpoint
- [ ] ⚠️ Verify touch gestures ทำงานบน mobile

### 🔲 Card Template (รอตัดสินใจ):
```
┌─────────────────────────────────────┐
│  [Icon] Card Title         [⋮ More] │  ← Header
├─────────────────────────────────────┤
│                                     │
│           Card Content              │  ← Body (scrollable)
│                                     │
├─────────────────────────────────────┤
│  [Action 1]  [Action 2]  [Expand ▼] │  ← Footer (optional)
└─────────────────────────────────────┘
```

---

## 1.2 💰 Daily Price Scraper

> **เป้าหมาย:** ราคาอุปกรณ์ update อัตโนมัติทุกวัน

### Files to Create:
| File | Type | Description |
|------|------|-------------|
| `.github/workflows/price-scraper.yml` | NEW | Cron job |
| `mcp_core_v2/catalog/prices.csv` | NEW | Price database |

### Files to Modify:
| File | Change |
|------|--------|
| `price_scraper.py` | เพิ่ม `--output` arg |
| `boq_service.py` | อ่านจาก `prices.csv` |

### Sub-tasks:
- [ ] 1.2.1 Create `prices.csv` skeleton (headers only)
- [ ] 1.2.2 Add `--output` flag to `price_scraper.py`
- [ ] 1.2.3 Add `save_to_csv()` function
- [ ] 1.2.4 Create `price-scraper.yml` workflow
- [ ] 1.2.5 Test manual trigger
- [ ] 1.2.6 Set cron schedule (00:00 TH)
- [ ] 1.2.7 Update `boq_service.py` to read CSV
- [ ] 1.2.8 Add fallback if CSV missing

### Error Prevention:
- [ ] ⚠️ Validate price range (> 0, < 100,000)
- [ ] ⚠️ Log which items failed to scrape
- [ ] ⚠️ Keep old prices.csv as backup before overwrite

---

## 1.3 ⏳ Loading Mascot Animation

> **เป้าหมาย:** Mascot animation ขณะโหลด

### Files to Create:
| File | Type | Description |
|------|------|-------------|
| `LoadingMascot.tsx` | NEW | Animated mascot component |
| `mascot-animation.css` | NEW | Keyframe animations |
| `assets/mascot-*.svg` | NEW | Mascot frames |

### Sub-tasks:
- [ ] 1.3.1 Design mascot character (simple robot/helper)
- [ ] 1.3.2 Create 3-4 animation frames (SVG)
- [ ] 1.3.3 Implement CSS keyframe animation
- [ ] 1.3.4 Create `LoadingMascot.tsx` component
- [ ] 1.3.5 Add random loading messages (Thai)
- [ ] 1.3.6 Integrate into API loading states
- [ ] 1.3.7 Add fade in/out transitions

### Error Prevention:
- [ ] ⚠️ Fallback to spinner if SVG fails to load
- [ ] ⚠️ Preload mascot assets on app start

---

# 📦 PHASE 2: Core Features (Week 2)

## 2.1 🎛️ Smart Form + Reactive Design

> **เป้าหมาย:** Real-time editing ที่ update ทุกอย่างอัตโนมัติ

### Files to Create:
| File | Type | Description |
|------|------|-------------|
| `hooks/useDesignState.ts` | NEW | State + undo/redo |
| `hooks/useReactiveDesign.ts` | NEW | Auto recalculate |
| `components/SmartField.tsx` | NEW | Editable field with lock |
| `components/UndoRedoBar.tsx` | NEW | Undo/Redo controls |

### Files to Modify:
| File | Change |
|------|--------|
| `api.py` | เพิ่ม `GET /session/{id}` |
| Deck Cards | ใช้ useReactiveDesign |

### Sub-tasks:
- [ ] 2.1.1 Create `useDesignState` hook (state management)
- [ ] 2.1.2 Implement Undo stack (max 10)
- [ ] 2.1.3 Implement Redo stack
- [ ] 2.1.4 Add rate limit (2s debounce)
- [ ] 2.1.5 Create `useReactiveDesign` hook
- [ ] 2.1.6 Wire to `/api/v1/design` with debounce
- [ ] 2.1.7 Create `SmartField.tsx` component
- [ ] 2.1.8 Add Auto/Manual dropdown
- [ ] 2.1.9 Add Lock toggle (🔒/🔓)
- [ ] 2.1.10 Create `UndoRedoBar.tsx`
- [ ] 2.1.11 Add visual feedback (toast on save)
- [ ] 2.1.12 Integrate into Deck UI cards

### Error Prevention:
- [ ] ⚠️ Prevent undo during loading state
- [ ] ⚠️ Confirm before discarding unsaved changes
- [ ] ⚠️ Keep local backup in localStorage

### 🔲 Form Template (รอตัดสินใจ):
```
┌─────────────────────────────────────────────────────┐
│  ห้องนอน 1  [25 m²]                    [+ เพิ่ม]    │
├─────────────────────────────────────────────────────┤
│  🔓 แอร์        [Auto ▼]  [12000] BTU  │  [🗑️]     │
│  🔒 เต้ารับ     [Manual]  [4] จุด       │  [🗑️]     │
│  🔓 ไฟเพดาน    [Auto ▼]  [3] ดวง       │  [🗑️]     │
├─────────────────────────────────────────────────────┤
│  [↩️ Undo (3)]  [↪️ Redo]      ⏱️ Cooldown: 1.2s    │
└─────────────────────────────────────────────────────┘
```

---

## 2.2 🔗 Cascade Integration

> **เป้าหมาย:** SLD, BOQ, Floor Plan update เมื่อ input เปลี่ยน

### Sub-tasks:
- [ ] 2.2.1 Wire SLDCard to sessionId from reactive design
- [ ] 2.2.2 Wire BOQCard to sessionId from reactive design
- [ ] 2.2.3 Add loading state to each card
- [ ] 2.2.4 Implement "stale" indicator when data outdated
- [ ] 2.2.5 Add "Refresh" button per card
- [ ] 2.2.6 Auto-refresh when card becomes visible

---

# 📦 PHASE 3: Premium Features (Week 3+)

## 3.1 📜 White Label

> **เป้าหมาย:** Digital stamp + signature บนเอกสาร

### Sub-tasks:
- [ ] 3.1.1 Create stamp template
- [ ] 3.1.2 Create signature upload UI
- [ ] 3.1.3 Add overlay layer to PDF exports
- [ ] 3.1.4 Add to Load Schedule output
- [ ] 3.1.5 Add to SLD output
- [ ] 3.1.6 Add to BOQ output

---

## 3.2 🔐 QR Verification

> **เป้าหมาย:** QR code ยืนยันเอกสาร

### Sub-tasks:
- [ ] 3.2.1 Generate unique document ID
- [ ] 3.2.2 Create QR code with verification URL
- [ ] 3.2.3 Add to exported documents
- [ ] 3.2.4 Create verification landing page

---

# 🛡️ Error Prevention Checklist (Global)

## Before Each Phase:
- [ ] Create feature branch
- [ ] Run existing tests
- [ ] Backup current working version

## After Each Phase:
- [ ] Test all existing features still work
- [ ] Check mobile responsiveness
- [ ] Verify API responses unchanged
- [ ] Update MEMORY.md if new lessons learned

## Specific Risks:

| Risk | Mitigation |
|------|------------|
| Breaking existing API | ❌ No breaking changes, only additions |
| CSS conflicts | Use scoped CSS / CSS modules |
| State management conflicts | Isolate hooks, clear separation |
| Scraper gets blocked | Rate limit + User-Agent rotation |
| Undo corrupts data | Deep copy snapshots |

---

# 📊 Summary Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **1** | Foundation | Deck UI + Scraper + Mascot |
| **2** | Core | Smart Form + Cascade |
| **3+** | Premium | White Label + QR |

---

*Last Updated: 2025-12-20*
*Status: Awaiting Review*
