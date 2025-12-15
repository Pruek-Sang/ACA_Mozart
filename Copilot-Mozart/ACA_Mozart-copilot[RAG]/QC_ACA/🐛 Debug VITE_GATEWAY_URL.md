# 🐛 Debug Plan: VITE_GATEWAY_URL / localhost:8000 Issue

## 📋 สถานะปัจจุบัน
- ✅ GitHub Secret `VITE_GATEWAY_URL` ถูกเพิ่มแล้ว
- ✅ Workflow ใช้ `${{ secrets.VITE_GATEWAY_URL }}`
- ❌ Frontend ยังแสดง `localhost:8000`

---

## 🔍 Possible Root Causes (4 ข้อ)

### #1: GitHub Actions ไม่อ่าน Secret
**ตรวจสอบ:**
1. ไป https://github.com/Pruek-Sang/ACA_Mozart/actions
2. คลิก build ล่าสุด (commit `c432a95`)
3. ดู step "📝 Create .env.production from GitHub Secrets"
4. ดูว่า echo output เป็นอะไร (จะ mask secret แต่ไม่ควรเป็นว่าง)

**ถ้าเป็นว่าง:**
- Secret ชื่อผิด (typo)
- Secret อยู่ผิด repo

---

### #2: npm build ใช้ cache เก่า
**ตรวจสอบ:**
ใน workflow step "🔨 Build React app" ดูว่ามี output ที่แสดงว่า build ใหม่จริง

**แก้ไข:**
```yaml
- name: 📝 Create .env.production from GitHub Secrets
  run: |
    echo "VITE_GATEWAY_URL=${{ secrets.VITE_GATEWAY_URL }}" > .env.production
    echo "VITE_MOCK_MODE=false" >> .env.production
    cat .env.production  # Debug: แสดงไฟล์ที่สร้าง
```

---

### #3: Docker image cache
**ตรวจสอบ:**
```bash
docker pull acatest01/mozart-frontend:latest
docker inspect acatest01/mozart-frontend:latest | grep -i created
```

**แก้ไข:**
เพิ่ม `--no-cache` ใน Docker build:
```yaml
- name: 🐳 Build and push Frontend (Cloud Run)
  uses: docker/build-push-action@v5
  with:
    no-cache: true  # ← เพิ่มนี้
```

---

### #4: Cloud Run pull old image (cached)
**ตรวจสอบ:**
```bash
gcloud run revisions list --service=frontend --region=asia-southeast1
```

**แก้ไข:**
Deploy with specific SHA instead of `latest`:
```bash
# ใช้ image tag ที่ specific
gcloud run deploy frontend \
  --image docker.io/acatest01/mozart-frontend:c432a95 \
  --port 80 \
  --region asia-southeast1 \
  --allow-unauthenticated
```

---

## 🚀 Quick Fix (100% Working)

**สร้าง `.env.production` ใน repo แทนที่จะพึ่ง Secrets:**

```bash
# สร้างไฟล์ใน repo
echo "VITE_GATEWAY_URL=https://gateway-rc5mtgajza-as.a.run.app" > ./Copilot-Mozart/ACA_Mozart-copilot[RAG]/frontend_UI_UX/mozart-chat/.env.production
echo "VITE_MOCK_MODE=false" >> ./Copilot-Mozart/ACA_Mozart-copilot[RAG]/frontend_UI_UX/mozart-chat/.env.production
```

**ข้อดี:** 
- ไม่พึ่ง GitHub Secrets
- Vite อ่าน `.env.production` โดยตรง
- 100% reliable

**ข้อเสีย:**
- URL อยู่ใน repo (แต่ไม่ใช่ secret)

---

## 📋 Debug Steps (ทำตามลำดับ)

### Step 1: ตรวจสอบ GitHub Actions Logs
```
1. ไป https://github.com/Pruek-Sang/ACA_Mozart/actions
2. คลิก workflow run ล่าสุด
3. ดู step "📝 Create .env.production"
4. ดูว่า output เป็นอะไร
```

### Step 2: ถ้า Step 1 ดูปกติ → ตรวจสอบ Docker Hub
```bash
# ดูว่า image ถูก push เมื่อไหร่
docker pull acatest01/mozart-frontend:latest
docker history acatest01/mozart-frontend:latest | head -5
```

### Step 3: ถ้ายังไม่ได้ → ใช้ Quick Fix
```bash
# สร้าง .env.production ใน repo
cd /home/builder/Desktop/ACA_Mozart
echo "VITE_GATEWAY_URL=https://gateway-rc5mtgajza-as.a.run.app" > "./Copilot-Mozart/ACA_Mozart-copilot[RAG]/frontend_UI_UX/mozart-chat/.env.production"
git add .
git commit -m "fix: add .env.production with Gateway URL"
git push origin main
```

### Step 4: Deploy ใหม่
```bash
# รอ GitHub Actions build เสร็จ แล้ว:
gcloud run deploy frontend \
  --image docker.io/acatest01/mozart-frontend:latest \
  --port 80 \
  --region asia-southeast1 \
  --allow-unauthenticated
```

---

## ✅ Expected Result

หลัง debug เสร็จ ควรเห็น:
- Frontend เรียก `https://gateway-rc5mtgajza-as.a.run.app` แทน `localhost:8000`
- ไม่มี error "Failed to fetch"

---

*Debug Plan by Architecta - 2025-12-16*
