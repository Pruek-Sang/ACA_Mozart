# 🐳 How to Docker Nginx - Frontend Deployment Guide

> **เป้าหมาย:** เพิ่ม Nginx Service สำหรับ serve Frontend (mozart-chat) เข้า Docker โดยไม่กระทบ Services เดิม

---

## 📊 สถานะปัจจุบัน

| Service | Port | หน้าที่ |
|---------|------|--------|
| `mcp-core` | 5001 | Electrical Calculation Engine |
| `mozart-rag` | 8080 | RAG Spec Engine (AI) |
| ❌ **ยังไม่มี** | - | Frontend Web Server |

---

## 🎯 เป้าหมาย

| Service | Port | หน้าที่ |
|---------|------|--------|
| `mcp-core` | 5001 | (เดิม) ไม่แก้ไข |
| `mozart-rag` | 8080 | (เดิม) ไม่แก้ไข |
| ✅ `mozart-frontend` | **80** | Nginx Serve React App |

---

## ⚠️ หลักการป้องกัน Regression

> [!IMPORTANT]
> **กฎทอง:** ไม่แก้ไขอะไรใน Service เดิม (`mcp-core`, `mozart-rag`) เลยแม้แต่บรรทัดเดียว

### สิ่งที่จะทำ (Safe Actions):
1. ✅ **เพิ่มไฟล์ใหม่** - `Dockerfile_frontend`, `nginx.conf`
2. ✅ **เพิ่ม Service ใหม่** - Append ต่อท้าย docker-compose
3. ✅ **ใช้ Network เดิม** - `mozart-network`

### สิ่งที่จะไม่ทำ (Forbidden):
1. ❌ แก้ไข `mcp-core` block
2. ❌ แก้ไข `mozart-rag` block
3. ❌ เปลี่ยน Port ของ Services เดิม
4. ❌ เปลี่ยน Volume mapping เดิม

---

## 📁 ไฟล์ที่ต้องสร้างใหม่

### 1. `frontend_UI_UX/mozart-chat/Dockerfile`

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2. `frontend_UI_UX/mozart-chat/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA: ทุก route redirect ไป index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to Gateway
    location /api/ {
        proxy_pass http://host.docker.internal:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 📝 การแก้ไข docker-compose-local.yml

> [!CAUTION]
> **แก้ไขเฉพาะส่วนท้ายของไฟล์เท่านั้น!** ห้ามแตะ mcp-core และ mozart-rag

### เพิ่มต่อท้าย (Append Only):

```yaml
  # ═══════════════════════════════════════════════════════════════════
  # Mozart Frontend - Nginx Web Server (NEW)
  # ═══════════════════════════════════════════════════════════════════
  mozart-frontend:
    container_name: mozart-frontend
    build:
      context: /mnt/BigDrive/Linux_Work/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/frontend_UI_UX/mozart-chat
      dockerfile: Dockerfile
    image: mozart-frontend:1.0.0
    
    ports:
      - "80:80"
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 5s
      retries: 3
    
    networks:
      - mozart-network
```

---

## 🔄 ขั้นตอนการ Deploy

### Step 1: สร้างไฟล์ใหม่
```bash
# สร้าง Dockerfile และ nginx.conf ใน mozart-chat/
```

### Step 2: ทดสอบ Build
```bash
cd frontend_UI_UX/mozart-chat
docker build -t mozart-frontend:1.0.0 .
```

### Step 3: ทดสอบ Run เดี่ยวก่อน
```bash
docker run -p 80:80 mozart-frontend:1.0.0
# เปิด http://localhost ดูว่า Frontend ขึ้นมั้ย
```

### Step 4: ถ้าสำเร็จ → Integrate เข้า Compose
```bash
# Append service to docker-compose-local.yml
docker-compose -f Docker/docker-compose-local.yml up -d
```

---

## ✅ Verification Checklist

| Test | Command | Expected |
|------|---------|----------|
| Frontend ขึ้น | `curl http://localhost` | HTML response |
| MCP-Core ยังปกติ | `curl http://localhost:5001/health` | `{"status": "ok"}` |
| Mozart-RAG ยังปกติ | `curl http://localhost:8080/` | Health response |
| Network connected | `docker network inspect mozart-fullstack-network` | 3 containers |

---

## 🚨 Rollback Plan

ถ้ามีปัญหา:
```bash
# ลบ Frontend container ออก (ไม่กระทบ Backend)
docker-compose -f Docker/docker-compose-local.yml stop mozart-frontend
docker-compose -f Docker/docker-compose-local.yml rm mozart-frontend
```

Services เดิม (`mcp-core`, `mozart-rag`) จะยังทำงานปกติค่ะ!
