# ☁️ Deploy to Cloud - Mozart Full Stack

## 📋 สถานะปัจจุบัน

### ✅ สิ่งที่พร้อมแล้ว
| Component | Docker Hub | Cloud Run | หมายเหตุ |
|-----------|------------|-----------|----------|
| mcp-core | `acatest01/mcp-core:latest` | ✅ Deployed | Port 5001 |
| mozart-rag | `acatest01/mozart-rag:latest` | ✅ Deployed | Port 8080 |
| gateway | `acatest01/mozart-gateway:latest` | ✅ Deployed | Port 8000 |
| frontend | `acatest01/mozart-frontend:latest` | ✅ **Fixed** | nginx-cloudrun.conf |

### Cloud Run URLs
- MCP Core: `https://mcp-core-rc5mtgajza-as.a.run.app`
- Mozart RAG: `https://mozart-rag-rc5mtgajza-as.a.run.app`
- Gateway: `https://gateway-rc5mtgajza-as.a.run.app`
- Frontend: `https://frontend-rc5mtgajza-as.a.run.app` (รอ deploy)

---

## ✅ ปัญหา Frontend บน Cloud Run (แก้แล้ว!)

### สาเหตุเดิม
```nginx
# nginx.conf บรรทัด 88-96
upstream gateway_backend {
    server gateway:8000;  ← Docker Compose network name (ไม่มีใน Cloud Run)
}
```

### วิธีแก้ที่ใช้ (Option A)
1. ✅ สร้าง `nginx-cloudrun.conf` (ไม่มี upstream)
2. ✅ สร้าง `Dockerfile.frontend-cloudrun`
3. ✅ แก้ GitHub Actions ให้ใช้ Dockerfile ใหม่
4. ⏳ Deploy frontend ใหม่

---

## ⚠️ ปัญหา Path `[RAG]` ใน Docker (สำคัญ!)

### ปัญหา
ชื่อโฟลเดอร์ `ACA_Mozart-copilot[RAG]` มี **วงเล็บเหลี่ยม** ซึ่ง Docker ตีความเป็น **glob pattern** ทำให้ COPY ไม่เจอไฟล์

```dockerfile
# ❌ ไม่ทำงาน!
COPY Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker/nginx-cloudrun.conf /etc/nginx/nginx.conf
# Error: lstat /Copilot-Mozart: no such file or directory
```

### วิธีแก้
**Copy ไฟล์ไปที่ repo root ก่อน** ใน GitHub Actions:

```yaml
# ใน .github/workflows/docker-build.yml
- name: 📁 Copy nginx config to root (avoid special chars in path)
  run: cp "./Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker/nginx-cloudrun.conf" ./nginx-cloudrun.conf
```

แล้วใน Dockerfile ใช้ simple path:
```dockerfile
# ✅ ทำงานได้!
COPY nginx-cloudrun.conf /etc/nginx/nginx.conf
```

---

## 📁 ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | ใช้สำหรับ | หมายเหตุ |
|------|----------|----------|
| `docker-compose.prod.yml` | Deploy บน VM | ใช้ nginx.conf |
| `docker-compose.fullstack.yml` | Local development | ใช้ nginx.conf |
| `.github/workflows/docker-build.yml` | Auto build + push | **แก้แล้ว** |
| `Docker/nginx.conf` | Docker Compose | มี upstream |
| `Docker/nginx-cloudrun.conf` | **Cloud Run** | ไม่มี upstream |
| `Docker/Dockerfile.frontend` | Docker Compose | ใช้ nginx.conf |
| `Docker/Dockerfile.frontend-cloudrun` | **Cloud Run** | ใช้ nginx-cloudrun.conf |

---

## 🚀 คำสั่ง Deploy Frontend ใหม่

```bash
# รอ GitHub Actions build เสร็จก่อน (~5 นาที)
# ดูสถานะ: https://github.com/Pruek-Sang/ACA_Mozart/actions

gcloud run deploy frontend \
  --image docker.io/acatest01/mozart-frontend:latest \
  --port 80 \
  --region asia-southeast1 \
  --allow-unauthenticated
```

---

## 📊 เปรียบเทียบ Cloud Platforms

| Platform | Docker Compose Support | ราคา | ความยาก |
|----------|------------------------|------|---------|
| **Google Cloud Run** | ❌ แยก services | Free tier มี | กลาง |
| **Google Compute Engine** | ✅ VM + compose | Free tier มี | กลาง |
| **AWS Lightsail** | ✅ VM + compose | $3.50+/mo | ง่าย |
| **Railway** | ⚠️ จำกัด 3 containers | $5 free/mo | ง่าย |
| **DigitalOcean Droplet** | ✅ VM + compose | $4+/mo | ง่าย |

---

## ⚠️ สิ่งที่ต้องระวัง

1. **nginx.conf เดิม** - อย่าแก้! ใช้สำหรับ Docker Compose
2. **Path ที่มี `[RAG]`** - ต้อง copy ไป root ก่อนใน GitHub Actions
3. **CORS** - Cloud Run ต้องเปิด `ALLOWED_ORIGINS=*`
4. **API Keys** - ใส่ผ่าน env vars ไม่ใช่ hardcode

---

*Last Updated: 2025-12-16 (Fixed frontend Cloud Run deployment)*

