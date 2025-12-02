# ═══════════════════════════════════════════════════════════════════
# Mozart Docker Deployment - README
# ═══════════════════════════════════════════════════════════════════

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Mozart Full Stack                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐       ┌─────────────────────────────────┐ │
│  │   Mozart RAG    │──────▶│       MCP Core v2               │ │
│  │   (port 8080)   │ HTTP  │       (port 5001)               │ │
│  │                 │       │                                 │ │
│  │ • AI Spec Gen   │       │ • Load Calculator               │ │
│  │ • Knowledge RAG │       │ • Wire Sizer                    │ │
│  │ • Conversation  │       │ • Breaker Selector              │ │
│  │                 │       │ • Conduit Sizer                 │ │
│  └─────────────────┘       │ • AutoLISP Generator            │ │
│                            └─────────────────────────────────┘ │
│                                                                 │
│  Network: mozart-fullstack-network                              │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Build & Run All Services

```bash
cd Docker
docker compose up -d --build
```

### 2. Check Status

```bash
docker compose ps
docker compose logs -f
```

### 3. Test Endpoints

```bash
# Health Check - MCP Core
curl http://localhost:5001/health

# Health Check - RAG
curl http://localhost:8080/

# Test MCP Calculation
curl -X POST http://localhost:5001/api/v1/design \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "project_name": "Test House",
    "service_voltage": "230V_1PH",
    "utility_service_size": 100,
    "loads": [
      {
        "id": "L1",
        "name": "AC",
        "load_type": "hvac",
        "voltage": "230V_1PH",
        "power_watts": 1200,
        "quantity": 1,
        "location": {"room": "Bedroom", "floor": "2"}
      }
    ],
    "panels": [
      {
        "id": "MDB",
        "name": "Main Panel",
        "voltage": "230V_1PH",
        "main_breaker_rating": 50,
        "number_of_circuits": 12,
        "location": {"room": "Utility", "floor": "1"},
        "feeds": ["L1"]
      }
    ]
  }'
```

## 📦 Individual Services

### MCP Core Only

```bash
cd ../../mcp_core_v2
docker build -f Docker/Dockerfile -t mcp-core:2.0.0 .
docker run -d -p 5001:5001 --name mcp-core mcp-core:2.0.0
```

### RAG Only

```bash
docker build -f Docker/Dockerfile_ACA -t mozart-rag:3.2.0 .
docker run -d -p 8080:8080 --env-file Docker/.env_ACA --name mozart-rag mozart-rag:3.2.0
```

## ⚙️ Configuration

### Environment Variables

**MCP Core (`mcp-core`):**
| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 5001 | API port |
| `LOG_LEVEL` | INFO | Logging level |

**RAG (`mozart-rag`):**
| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 8080 | API port |
| `MCP_CORE_URL` | http://mcp-core:5001 | MCP Core endpoint |
| `GOOGLE_API_KEY` | - | Google AI API key |

### .env_ACA Example

```bash
GOOGLE_API_KEY=your-google-ai-api-key
MCP_CORE_URL=http://mcp-core:5001
```

## 🧹 Cleanup

```bash
docker compose down
docker compose down -v  # Also remove volumes
docker system prune -f  # Clean unused resources
```

## 📊 Monitoring

```bash
# View logs
docker compose logs -f mcp-core
docker compose logs -f mozart-rag

# Resource usage
docker stats
```

## 🔧 Troubleshooting

### MCP Core not starting
```bash
docker logs mcp-core-v2
```

### RAG can't connect to MCP
- Check network: `docker network inspect mozart-fullstack-network`
- Verify MCP is healthy: `curl http://localhost:5001/health`

### Port already in use
```bash
# Find process using port
lsof -i :5001
lsof -i :8080

# Or use different ports in docker-compose.yml
```
