# 🚨 Security Roadmap v5.0 - Frontend Direct to Supabase

> อัปเดต: 19 ธ.ค. 2024 01:07

---

## 🎯 สถาปัตยกรรม

```
┌──────────┐       ┌───────────┐
│ Frontend │ ───── │ Supabase  │  ← Auth + CRUD ตรง
│ (React)  │       │ (RLS)     │
└──────────┘       └───────────┘
      │
      ▼
┌──────────┐       ┌───────────┐
│ Gateway  │ ───── │ RAG/MCP   │  ← ไม่แก้ไข!
└──────────┘       └───────────┘
```

**หลักการ:** Frontend จัดการ Auth/CRUD | Gateway จัดการ RAG/MCP

---

## 📊 Supabase Tables (จาก Agent อื่น)

### Table: `users` (auth.users)
- Supabase Auth จัดการให้อัตโนมัติ

### Table: `user_profiles`
```sql
id UUID PRIMARY KEY REFERENCES auth.users(id)
full_name TEXT
is_superuser BOOLEAN DEFAULT false
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

### Table: `projects`
```sql
id UUID PRIMARY KEY
owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE  ← สำคัญ!
name TEXT NOT NULL
description TEXT
rooms JSONB       -- ข้อมูลห้อง
loads JSONB       -- ข้อมูลโหลด
sld_data JSONB    -- Single Line Diagram (อนาคต)
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

### RLS Policies
- `owner_id = auth.uid()` → User เห็นแค่ project ของตัวเอง

---

## ✅ Progress

| Phase | งาน | สถานะ |
|-------|-----|-------|
| 0 | Supabase Tables | ✅ เสร็จ |
| 1 | ติดตั้ง supabase-js | ✅ เสร็จ |
| 2 | สร้าง supabase.ts + .env | ✅ เสร็จ |
| 3 | สร้าง useAuth hook | ✅ เสร็จ |
| 4 | สร้าง AuthContext | ✅ เสร็จ |
| 5 | สร้าง LoginForm | ✅ เสร็จ |
| 6 | อัปเดต App.tsx | ✅ เสร็จ |
| 7 | Build ผ่าน | ✅ เสร็จ |
| 8 | สร้าง useProjects | ✅ เสร็จ |
| 9 | Build ผ่าน (รอบ 2) | ✅ เสร็จ |
| 10 | ทดสอบ e2e | ⏳ รอ user test |

---

## 📁 ไฟล์ที่สร้าง

| ไฟล์ | สถานะ |
|------|-------|
| `src/lib/supabase.ts` | ✅ |
| `src/hooks/useAuth.ts` | ✅ |
| `src/hooks/useProjects.ts` | ✅ |
| `src/contexts/AuthContext.tsx` | ✅ |
| `src/components/LoginForm.tsx` | ✅ |
| `src/main.tsx` | ✅ |
| `src/App.tsx` | ✅ |
| `.env` | ✅ |

---

## ⚠️ กฎเหล็ก

1. **ห้าม Regression** - ไม่แตะ gateway/RAG/MCP
2. **ห้าม ENV หลุด** - ใช้ `import.meta.env` เท่านั้น
3. **ห้าม Mock** - ทุกอย่างต้องทำงานจริง
4. **ห้ามแก้ Backend** - ทำแค่ Frontend

---

## 🔧 Verification Commands

```bash
# Build test
cd frontend_UI_UX/mozart-chat && npm run build

# Run dev server
npm run dev
```

---

*Secura v5.0 - 19 ธ.ค. 2024*
