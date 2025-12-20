# 🔲 QR Code Verification
> ดูแพงขึ้น 300% + กัน Tampering

---

## 🎯 Goal

PDF ทุกแผ่นมี QR Code ที่สแกนแล้วเห็นข้อมูลต้นฉบับใน Server

---

## 💰 Business Value

| Effect | Details |
|--------|---------|
| ดู Hi-Tech | เหมือนเอกสารราชการ |
| กัน Tampering | ผู้รับเหมาแอบแก้ไม่ได้ |
| Traceability | ตรวจสอบย้อนกลับได้ |

---

## 📱 User Flow

```
1. Generate PDF → แปะ QR มุมขวาบน
2. ลูกค้าสแกน QR ด้วยมือถือ
3. เปิดหน้า web แสดงข้อมูล Read-only
4. เปรียบเทียบกับ PDF ที่ได้รับ
```

---

## 📄 PDF Design

```
┌────────────────────────────────────────────────┐
│  [LOGO]  บริษัท ABC                    [QR]   │
│          ────────────────────────             │
│                                               │
│         ตาราง Load Schedule                   │
│              ....                             │
│                                               │
└────────────────────────────────────────────────┘
```

---

## 🔗 Verification Page

**URL:** `https://mozart.app/verify/{document_id}`

```
┌─────────────────────────────────────────┐
│  🔍 ตรวจสอบเอกสาร                       │
│  ─────────────────────────────────────  │
│  📄 เอกสาร: LS-2024-001234              │
│  📅 สร้างเมื่อ: 19/12/2568              │
│  👤 ผู้ออกแบบ: บริษัท ABC               │
│  ✅ สถานะ: เอกสารต้นฉบับ               │
│                                         │
│  [ดูรายละเอียด ▼]                        │
│  ─────────────────────────────────────  │
│  • โหลดรวม: 15,000 VA                   │
│  • Breaker: 32A                         │
│  • สาย: 6 mm²                           │
└─────────────────────────────────────────┘
```

---

## 📁 Files to Create

| ไฟล์ | งาน |
|------|-----|
| `qr_generator.py` | **[NEW]** Gen QR |
| `pdf_generator.py` | **[MODIFY]** แปะ QR |
| `VerifyPage.tsx` | **[NEW]** หน้า verify |
| `api/verify.py` | **[NEW]** API ดึงข้อมูล |
| `documents` table | **[NEW]** เก็บ doc hash |

---

## 🔐 Security

- Document ID: UUID v4
- Hash: SHA-256 of content
- Verify: Compare hash with stored

---

## ⏱️ Timeline

| Step | เวลา |
|------|------|
| QR Generator + DB | 30 นาที |
| PDF Update | 20 นาที |
| Verify API | 30 นาที |
| Frontend Page | 45 นาที |

**รวม: ~2 ชม.**
