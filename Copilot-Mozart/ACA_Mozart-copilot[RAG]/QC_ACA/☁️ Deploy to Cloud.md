# ☁️ Deploy to Cloud - Mozart Full Stack

## 📋 สถานะปัจจุบัน

### ✅ สิ่งที่พร้อมแล้ว
| Component | Docker Hub | Cloud Run | หมายเหตุ |
|-----------|------------|-----------|----------|
| mcp-core | `acatest01/mcp-core:latest` | ✅ Deployed | Port 5001 |
| mozart-rag | `acatest01/mozart-rag:latest` | ✅ Deployed | Port 8080 |
| gateway | `acatest01/mozart-gateway:latest` | ✅ Deployed | Port 8000 |
| frontend | `acatest01/mozart-frontend:latest` | ❌ Failed | nginx.conf ปัญหา |

### Cloud Run URLs (สำเร็จแล้ว)
- MCP Core: `https://mcp-core-rc5mtgajza-as.a.run.app`
- Mozart RAG: `https://mozart-rag-rc5mtgajza-as.a.run.app`
- Gateway: `https://gateway-rc5mtgajza-as.a.run.app`

---

## ❌ ปัญหา Frontend บน Cloud Run

### สาเหตุ
```nginx
# nginx.conf บรรทัด 88-96
upstream gateway_backend {
    server gateway:8000;  ← Docker Compose network name (ไม่มีใน Cloud Run)
}
```

### ความแตกต่าง
| Platform | Network | ใช้ชื่อ |
|----------|---------|--------|
| Docker Compose | Internal Docker network | `gateway:8000` ✅ |
| Cloud Run | ไม่มี internal network | ต้องใช้ URL เต็ม |

---

## 🛠️ วิธีแก้ที่แนะนำ

### Option A: สร้าง nginx config แยกสำหรับ Cloud (แนะนำ ⭐)

**ข้อดี:** ไม่กระทบ Docker Compose เดิม
**ข้อเสีย:** ต้อง maintain 2 ไฟล์

**ขั้นตอน:**
1. สร้าง `nginx-cloudrun.conf` (ไม่มี upstream)
2. สร้าง `Dockerfile.frontend-cloudrun`
3. เพิ่ม GitHub Actions job สำหรับ build cloud version
4. Deploy frontend ใหม่

### Option B: ให้ Frontend เรียก Gateway ตรงๆ

**ข้อดี:** ง่าย, ไม่ต้องแก้ nginx
**ข้อเสีย:** ต้องแก้ React code

**ขั้นตอน:**
1. แก้ `api.config.ts` ให้ใช้ Gateway URL ตรงๆ
2. ใช้ nginx เป็นแค่ static file server
3. Rebuild frontend image

### Option C: ใช้ Environment Variable Substitution ใน nginx

**ข้อดี:** Config เดียวใช้ได้ทุกที่
**ข้อเสีย:** ซับซ้อน, ต้องใช้ envsubst

---

## 📊 เปรียบเทียบ Cloud Platforms

| Platform | Docker Compose Support | ราคา | ความยาก |
|----------|------------------------|------|---------|
| **Google Cloud Run** | ❌ แยก services | Free tier มี | กลาง |
| **AWS Lightsail** | ✅ VM + compose | $3.50+/mo | ง่าย |
| **Railway** | ⚠️ จำกัด free tier | $5 free/mo | ง่าย |
| **DigitalOcean Droplet** | ✅ VM + compose | $4+/mo | ง่าย |
| **Google Compute Engine** | ✅ VM + compose | Free tier มี | กลาง |

---

## 🎯 แผนที่แนะนำ

### สำหรับ Production (ประหยัด):
1. **ใช้ Google Compute Engine** (e2-micro ฟรี)
2. ติดตั้ง Docker + Docker Compose
3. รัน `docker-compose.prod.yml` เหมือน local
4. ไม่ต้องแก้อะไร!

### สำหรับ Scalable (อนาคต):
1. แก้ Frontend ให้ไม่พึ่ง nginx proxy (Option B)
2. Deploy ทุก services บน Cloud Run
3. ใช้ Cloud Run auto-scaling

---

## 📝 ขั้นตอนถัดไป

### ถ้าเลือก Google Compute Engine (แนะนำ):
```bash
# 1. สร้าง VM (ใน Cloud Shell)
gcloud compute instances create mozart-server \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud

# 2. SSH เข้าไป
gcloud compute ssh mozart-server --zone=us-central1-a

# 3. ติดตั้ง Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 4. Clone repo + รัน compose
git clone https://github.com/Pruek-Sang/ACA_Mozart.git
cd ACA_Mozart
docker compose -f docker-compose.prod.yml up -d
```

### ถ้าเลือก Cloud Run (ต้องแก้ Frontend):
- ดู Option A หรือ B ด้านบน
- ต้องสร้างไฟล์ใหม่และ rebuild image

---

## ⚠️ สิ่งที่ต้องระวัง

1. **nginx.conf เดิม** - อย่าแก้! ใช้สำหรับ Docker Compose
2. **Environment Variables** - ต้องตั้งให้ถูกตาม platform
3. **CORS** - Cloud Run ต้องเปิด `ALLOWED_ORIGINS=*` หรือใส่ URL ที่ถูกต้อง
4. **API Keys** - ใส่ผ่าน env vars ไม่ใช่ hardcode

---

## 📁 ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | ใช้สำหรับ |
|------|----------|
| `docker-compose.prod.yml` | Deploy บน VM (Lightsail, GCE, Droplet) |
| `docker-compose.fullstack.yml` | Local development |
| `.github/workflows/docker-build.yml` | Auto build + push to Docker Hub |
| `Docker/nginx.conf` | Frontend for Docker Compose |
| `Docker/nginx-cloudrun.conf` | Frontend for Cloud Run (ยังไม่ได้ใช้) |

---

*Last Updated: 2025-12-16*
