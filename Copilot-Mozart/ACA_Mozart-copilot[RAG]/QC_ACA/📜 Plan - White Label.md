# 📜 White Label - Digital Stamp & Signature
> แผนสำหรับ Profile System + Custom Branding

---

## 🎯 Goal

ให้ User (วิศวกร/ผู้รับเหมา) อัปโหลดโลโก้+ลายเซ็น เพื่อแปะบน PDF ที่ gen ออกมา

---

## 💰 Business Value

| ฟีเจอร์ | Effect |
|--------|--------|
| โลโก้บริษัท | ดูเป็นมืออาชีพ |
| ลายเซ็นดิจิทัล | ไม่ต้อง sign ทุกแผ่น |
| White Label | ซ่อนว่าใช้ Mozart |

> **"ลูกค้าเห็น Report สวยงาม = ยอมจ้างแพงขึ้น"**

---

## 📁 System Design

### Database Schema

```sql
-- User Profile Extension
ALTER TABLE users ADD COLUMN company_name VARCHAR(200);
ALTER TABLE users ADD COLUMN company_logo_url TEXT;
ALTER TABLE users ADD COLUMN signature_url TEXT;
ALTER TABLE users ADD COLUMN license_no VARCHAR(50);
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
```

### Frontend - Profile Settings

```
┌─────────────────────────────────────────┐
│  ⚙️ ตั้งค่าองค์กร                       │
├─────────────────────────────────────────┤
│  ชื่อบริษัท: [__________________]       │
│  เลขทะเบียน: [__________________]       │
│                                         │
│  โลโก้: [📤 อัปโหลด] [🖼️ Preview]        │
│  ลายเซ็น: [📤 อัปโหลด] [🖼️ Preview]     │
│                                         │
│  [💾 บันทึก]                             │
└─────────────────────────────────────────┘
```

---

## 📄 PDF Output

### Header (ทุกหน้า)

```
┌─────────────────────────────────────────────────────┐
│  [LOGO]  บริษัท ABC Electric จำกัด                 │
│          เลขทะเบียน: กวก.001234                    │
│          โทร: 02-xxx-xxxx                          │
└─────────────────────────────────────────────────────┘
```

### Footer (หน้าสุดท้าย)

```
┌─────────────────────────────────────────────────────┐
│  ผู้ออกแบบ: _______[SIGNATURE]_______              │
│  วันที่: 19/12/2568                                │
│  เอกสารนี้ออกจากระบบ ACA Mozart                    │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Files to Create

| ไฟล์ | งาน |
|------|-----|
| `ProfileSettings.tsx` | **[NEW]** หน้าตั้งค่า |
| `ImageUploader.tsx` | **[NEW]** Upload component |
| `useProfile.ts` | **[NEW]** Hook จัดการ profile |
| `pdf_generator.py` | **[MODIFY]** แปะ logo/signature |
| `api/profile.py` | **[NEW]** CRUD profile |

---

## ⏱️ Timeline

| Step | เวลา |
|------|------|
| Database schema | 15 นาที |
| API endpoints | 30 นาที |
| Frontend Profile page | 1 ชม. |
| PDF generator update | 45 นาที |
| Test + Commit | 30 นาที |

**รวม: ~3 ชม.**

---

## 🔗 Dependencies

- [ ] ต้องมี User Auth ก่อน
- [ ] ต้องมี Cloud Storage (GCS/S3) สำหรับเก็บรูป
- [ ] PDF library ที่รองรับ image embed (reportlab/fpdf)
