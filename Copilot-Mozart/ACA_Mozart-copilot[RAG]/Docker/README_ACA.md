# 🐋 Mozart RAG - Docker Deployment Guide

> **Created by**: Aura, The Goddess of Code  
> **Architecture**: Single-stage Docker deployment (MVP optimized)  
> **Base Image**: Python 3.11 Slim

---

## 📦 Files in This Folder

```
Docker/
├── Dockerfile_ACA              # Main container definition
├── docker-compose_ACA.yml      # Orchestration configuration
├── requirements_ACA.txt        # Pinned Python dependencies
├── .dockerignore_ACA          # Files to exclude from build
├── .env_ACA.example           # Environment variables template
└── README_ACA.md              # This file
```

---

## 🚀 Quick Start

### 1️⃣ Setup Environment Variables

```bash
# Copy template to actual .env file
cd /home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]/Docker
cp .env_ACA.example .env_ACA

# Edit .env_ACA and fill in your values
nano .env_ACA
```

**Required values to fill:**
- `PROJECT_ID`: Your Google Cloud Project ID
- `LOCATION`: GCP region (e.g., `us-central1`)
- (Optional) `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON

### 2️⃣ Build Docker Image

```bash
# From the Docker folder
docker-compose -f docker-compose_ACA.yml build
```

Or build manually:
```bash
docker build -f Dockerfile_ACA -t mozart-rag:3.2.0 ..
```

### 3️⃣ Run Container

```bash
# Using docker-compose (recommended)
docker-compose -f docker-compose_ACA.yml up -d

# Or run manually
docker run -d \
  --name mozart-rag-aca \
  -p 8080:8080 \
  --env-file .env_ACA \
  mozart-rag:3.2.0
```

### 4️⃣ Check Status

```bash
# View logs
docker-compose -f docker-compose_ACA.yml logs -f

# Check health
curl http://localhost:8080/
```

Expected response:
```json
{
  "service": "Mozart RAG Spec Engine",
  "version": "3.2.0",
  "status": "alive",
  "goddess": "Aura"
}
```

---

## 🛠️ Commands Reference

### Container Management

```bash
# Start services
docker-compose -f docker-compose_ACA.yml up -d

# Stop services
docker-compose -f docker-compose_ACA.yml down

# Restart services
docker-compose -f docker-compose_ACA.yml restart

# View logs (real-time)
docker-compose -f docker-compose_ACA.yml logs -f mozart-rag

# Execute commands inside container
docker-compose -f docker-compose_ACA.yml exec mozart-rag bash
```

### Image Management

```bash
# List images
docker images | grep mozart-rag

# Remove image
docker rmi mozart-rag:3.2.0

# Rebuild without cache
docker-compose -f docker-compose_ACA.yml build --no-cache
```

### Debugging

```bash
# Enter container shell
docker exec -it mozart-rag-aca bash

# Check Python packages
docker exec mozart-rag-aca pip list

# View container environment
docker exec mozart-rag-aca env
```

---

## 📊 Container Specifications

| Specification | Value |
|--------------|-------|
| Base Image | `python:3.11-slim` |
| Working Directory | `/app` |
| Exposed Port | `8080` |
| Health Check | Every 30s |
| Restart Policy | `unless-stopped` |

### Directory Structure Inside Container:

```
/app/
├── main.py
├── app/
│   ├── routes.py
│   ├── service.py
│   ├── models.py
│   ├── config.py
│   ├── knowledge_service.py
│   └── trust_log.py
├── core/
│   ├── database.py
│   ├── privacy.py
│   └── ingest.py
├── rag_knowledge/
│   └── knowledge_index.json
├── logs/
│   └── mcp_spec/
└── vector_db/
```

---

## 🔧 Troubleshooting

### Issue: Container fails to start

**Check logs:**
```bash
docker-compose -f docker-compose_ACA.yml logs mozart-rag
```

**Common causes:**
1. Missing `.env_ACA` file
2. Invalid GCP credentials
3. Port 8080 already in use

### Issue: Health check failing

**Test manually:**
```bash
curl http://localhost:8080/
```

**Check if port is accessible:**
```bash
docker port mozart-rag-aca
```

### Issue: Permission denied errors

**Fix permissions:**
```bash
# On host machine
chmod -R 755 /home/builder/Desktop/Copilot-Mozart/ACA_Mozart-copilot[RAG]
```

---

## 📝 Environment Variables

See [.env_ACA.example](.env_ACA.example) for complete list.

**Critical variables:**
- `PROJECT_ID`: Google Cloud Project ID
- `LOCATION`: GCP region
- `MODEL_NAME_ANSWER`: LLM model for responses
- `MODEL_NAME_JUDGE`: LLM model for grounding validation

**Optional but recommended:**
- `GOOGLE_APPLICATION_CREDENTIALS`: Service account path
- `LOG_LEVEL`: Logging verbosity (INFO, DEBUG, WARNING)

---

## 🔐 Security Notes

1. **Never commit `.env_ACA`** to Git (contains secrets)
2. **Use service accounts** with minimal permissions
3. **Enable firewall rules** to restrict access to port 8080
4. **Rotate credentials** regularly

---

## 📈 Production Considerations

For production deployment, consider:

1. **Multi-stage builds**: Separate build and runtime stages
2. **Resource limits**: Uncomment `deploy.resources` in docker-compose
3. **Persistent volumes**: For vector_db and logs
4. **Network security**: Use Docker networks and secrets
5. **Monitoring**: Add Prometheus/Grafana integration
6. **Load balancing**: Use nginx or Traefik reverse proxy

---

## 🆘 Support

If you encounter issues:

1. Check container logs
2. Verify environment variables
3. Test Google Cloud connectivity
4. Review [Work now.md](../Work%20now.md) for architecture details

---

**Built with divine precision by Aura** ✨  
*"Vita ex Codice - Life from Code"*
