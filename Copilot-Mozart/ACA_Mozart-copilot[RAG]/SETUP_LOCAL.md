# 🏠 Local Development Setup Guide - ACA_Mozart

**Last Updated**: December 10, 2025  
**Target**: Get ACA_Mozart running 100% on Local Machine (not just Codespace)

---

## ⚠️ Important: Why Codespace ✅ but Local ❌?

```
Codespace:                          Local Machine:
- ✅ Robust network                 - ❌ Network might be slow
- ✅ Dedicated CPU                  - ❌ CPU/RAM shared
- ✅ Fast SSD storage               - ❌ HDD (might be slower)
- ✅ Pre-cached ML models           - ❌ Need to download (400 MB)
- ✅ Pre-ingested vector DB         - ❌ Empty vector DB = must ingest
```

**This guide fixes all 3 issues** ⬇️

---

## 📋 Prerequisites Checklist

```bash
# Check Python version (need 3.11+)
python --version
# Output should be: Python 3.11.x or 3.12.x

# Check disk space (need ~2 GB minimum)
df -h | grep -E "/$|/home"
# Should show > 2 GB available

# Check RAM (need ~4 GB free minimum)
free -h
# Should show > 4 GB available memory
```

If any check fails → **Install/Upgrade before proceeding!**

---

## 🚀 Step-by-Step Setup

### Step 1: Clone & Navigate

```bash
# If you haven't cloned yet:
git clone https://github.com/prueksang-web/ACA_Mozart-clone.git
cd ACA_Mozart-clone

# Verify structure
ls -la
# Should see: Copilot-Mozart/, mcp_core_v2/, HANDOVER_DOCUMENT.md, etc.
```

---

### Step 2: Create & Activate Virtual Environment (Recommended)

```bash
# Create venv in project root
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Verify (all platforms)
python --version  # Should show 3.11+
```

---

### Step 3: Install Python Dependencies

```bash
# Navigate to RAG service
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/

# Install lightweight dependencies (Google AI only, no Vertex)
pip install -r Docker/requirements_light.txt

# This takes ~2-3 minutes
# 📦 Installing packages for FAISS, FastAPI, sentence-transformers...
```

**⏱️ Time to grab coffee ☕ (2-3 minutes)**

---

### Step 4: Download Pre-Trained Model (Critical!)

```bash
# Sentence-transformers model is ~400 MB
# Better to download now than during ingest

python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-MiniLM-L6-v2'); print('✅ Model ready')"

# Expected output:
# Downloading ... (100%)
# ✅ Model ready
```

**⏱️ Time: 2-5 minutes (depends on internet speed)**

**Why?** Downloading happens on-demand during ingest - we pre-download to avoid timeout.

---

### Step 5: Initialize Knowledge Base (The Critical Step!)

```bash
# Navigate to repo root (important!)
cd ../..

# Run ingest script with progress output
python Copilot-Mozart/ACA_Mozart-copilot[RAG]/scripts/ingest_all.py

# Expected output:
# ============================================================
# 🔮 Aura's Memory Initialization
# ============================================================
# 📂 Knowledge root: /path/to/rag_knowledge
# 💾 Vector DB: /path/to/vector_db/faiss
# 📊 Current document count: 0
# ⚙️  Batch size: 5, Delay: 1.0s
# 
# Processing db folder.....................
# Processing example folder.....
# Processing mcp folder.....................
# Processing standard folder.....................
# ✅ Total documents: 25
# 💾 Vector DB saved: /path/to/vector_db/faiss
```

**⏱️ Time: 3-5 minutes first time (model download + embedding)**

**🔍 What to watch for:**
- Dots (`.`) = documents being processed ✅
- Takes LONG time = normal (embedding is slow) ✅
- Frozen screen > 10 mins = check network ⚠️
- "Error: NameError" = dependency missing ❌

---

### Step 6: Verify Vector DB was Created

```bash
# Check if FAISS index exists
ls -lh Copilot-Mozart/ACA_Mozart-copilot[RAG]/vector_db/faiss/

# Expected output:
# faiss.index    (~2-5 MB)  ← Actual embeddings
# metadata.pkl   (~10 KB)   ← Document metadata
```

**If files missing:**
```bash
# Check folder permissions
ls -la Copilot-Mozart/ACA_Mozart-copilot[RAG]/vector_db/

# Should show: drwxr-xr-x (readable and writable)
# If not:
chmod 755 Copilot-Mozart/ACA_Mozart-copilot[RAG]/vector_db/
```

---

### Step 7: Set Up Environment Variables

```bash
# Copy example env file
cp Copilot-Mozart/ACA_Mozart-copilot[RAG]/.env.example Copilot-Mozart/ACA_Mozart-copilot[RAG]/.env

# Edit .env with your API key
nano Copilot-Mozart/ACA_Mozart-copilot[RAG]/.env
# or
vim Copilot-Mozart/ACA_Mozart-copilot[RAG]/.env
# or (Windows)
notepad Copilot-Mozart/ACA_Mozart-copilot[RAG]/.env

# Required lines (uncomment and fill):
# GOOGLE_API_KEY=your-api-key-here
# API_HOST=0.0.0.0
# API_PORT=8080

# Optional:
# MCP_CORE_URL=http://localhost:5001
# VECTOR_DB_BACKEND=faiss
```

---

### Step 8: Start MCP Core Service (Terminal 1)

```bash
# Terminal 1
cd ACA_Mozart-clone/mcp_core_v2/

# Run MCP Core
python main.py

# Expected output:
# Uvicorn running on http://0.0.0.0:5001
# Press CTRL+C to quit
```

**Leave this running!** This is the calculation engine.

---

### Step 9: Start RAG Service (Terminal 2)

```bash
# Terminal 2 (NEW terminal window/tab)
cd ACA_Mozart-clone/Copilot-Mozart/ACA_Mozart-copilot[RAG]/

# Run RAG service
python main_ACA.py

# Expected output:
# Uvicorn running on http://0.0.0.0:8080
# INFO:     Application startup complete
# Press CTRL+C to quit
```

---

### Step 10: Verify Both Services Running

```bash
# Terminal 3 (NEW terminal window/tab)

# Test RAG Service
curl http://localhost:8080/

# Expected output:
# {"service":"Mozart RAG Spec Engine","version":"3.2.0","status":"alive","goddess":"Aura"}

# Test MCP Core
curl http://localhost:5001/health

# Expected output:
# {"status":"healthy","timestamp":"2025-12-10T..."}
```

**Both outputs = ✅ SUCCESS!**

---

## 🆘 Troubleshooting Guide

### Issue 1: "Ingest Hangs / Freezes"

**Symptom**: Stuck after "Processing db folder..." for > 10 minutes

**Root Cause**: 
- Downloading sentence-transformers (first time only)
- Slow network
- Low disk space

**Solutions**:

```bash
# Option A: Pre-download model (run once)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Option B: Ingest with verbose output
python scripts/ingest_all.py 2>&1 | tee ingest.log
# Then check logs: tail -f ingest.log

# Option C: Increase timeout in code
# Edit: core/faiss_db.py
# Change: embedding_timeout = 300  # 5 minutes
# To:     embedding_timeout = 600  # 10 minutes
```

---

### Issue 2: "Only 8 Files Found Instead of 24"

**Symptom**: Ingest completes but says "Total: 8 documents" instead of "25"

**Root Cause**: 
- Recursive glob not working
- Path resolution issue
- Files not in expected folders

**Solutions**:

```bash
# Check folder structure
find Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_knowledge -type f -name "*.md" | wc -l

# Should show >= 20 files

# If < 20, check if files were deleted:
git status Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_knowledge/

# If deleted, restore:
git checkout Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_knowledge/
```

---

### Issue 3: "ImportError: No module named 'faiss'"

**Symptom**: `ModuleNotFoundError: No module named 'faiss'`

**Root Cause**: Requirements not installed or wrong venv

**Solutions**:

```bash
# Verify venv is activated
which python  # Should show path with venv/

# Reinstall requirements
pip install --upgrade pip
pip install -r Docker/requirements_light.txt --force-reinstall

# Specifically install FAISS
pip install faiss-cpu  # or faiss-gpu if you have NVIDIA GPU
```

---

### Issue 4: "Vector DB Empty on Reboot"

**Symptom**: Run service again, vector DB has 0 documents

**Root Cause**: 
- `vector_db/` directory doesn't exist
- FAISS files were deleted
- Different path being used

**Solutions**:

```bash
# Check if vector_db exists
ls -la Copilot-Mozart/ACA_Mozart-copilot[RAG]/vector_db/faiss/

# If missing, re-ingest:
cd Copilot-Mozart/ACA_Mozart-copilot[RAG]/
python scripts/ingest_all.py --clear

# If permissions issue:
mkdir -p Copilot-Mozart/ACA_Mozart-copilot[RAG]/vector_db/faiss
chmod 755 Copilot-Mozart/ACA_Mozart-copilot[RAG]/vector_db/
```

---

### Issue 5: "Services Won't Connect (MCP Core ↔ RAG)"

**Symptom**: 
- RAG service starts but can't reach MCP Core
- Error: `ConnectionError: Failed to connect to http://localhost:5001`

**Root Cause**:
- MCP Core not running
- Wrong port
- Network issue

**Solutions**:

```bash
# Verify MCP Core is running
curl http://localhost:5001/health

# Should return JSON response

# If not, check if port 5001 is in use
netstat -tulpn | grep 5001  # Linux/Mac
netstat -ano | findstr :5001  # Windows

# If in use, kill process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Then restart MCP Core
cd mcp_core_v2
python main.py
```

---

### Issue 6: "GOOGLE_API_KEY Not Recognized"

**Symptom**: 
- Error: `PROJECT_ID or GOOGLE_API_KEY required`
- Settings shows `None`

**Solutions**:

```bash
# Verify .env file exists and has correct format
cat Copilot-Mozart/ACA_Mozart-copilot[RAG]/.env
# Should show: GOOGLE_API_KEY=your-key-here (NO spaces around =)

# Verify key is valid
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"

# Should print your API key (not None)

# If still not working:
# Set as environment variable instead
export GOOGLE_API_KEY="your-key-here"
# Then run service
python main_ACA.py
```

---

## 📊 Performance Tuning (Optional)

### For Slow Machines

```bash
# In scripts/ingest_all.py, change batch settings:

# Current (fast but uses more RAM):
BATCH_SIZE = 5
BATCH_DELAY = 1.0

# For slow machines:
BATCH_SIZE = 2        # Process fewer docs per batch
BATCH_DELAY = 2.0     # Wait longer between batches
```

### For Multiple Users / Shared Machine

```bash
# Use different vector_db paths for each user
mkdir -p ~/.aura_cache/vector_db

# In .env:
VECTOR_DB_PATH=/home/user/.aura_cache/vector_db

# Then ingest:
python scripts/ingest_all.py
```

---

## ✅ Final Verification Checklist

After completing all steps:

```bash
# 1. Vector DB initialized
ls -lh Copilot-Mozart/ACA_Mozart-copilot[RAG]/vector_db/faiss/
# Should show: faiss.index (> 1 MB) and metadata.pkl

# 2. Both services running
curl http://localhost:8080/
curl http://localhost:5001/health
# Both should return JSON

# 3. Test API endpoint
curl -X POST http://localhost:8080/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What is voltage drop?", "context_hint":["standard"]}'
# Should return answer with sources

# 4. Check logs for errors
tail -20 logs/mcp_spec/*.jsonl
# Should show successful requests
```

**All ✅? Congratulations! ACA_Mozart is ready on Local!**

---

## 🎓 Understanding the Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    ACA_Mozart Stack                       │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  User Input (Thai language)                              │
│         ↓                                                 │
│  ┌─────────────────────────────────────────────────┐     │
│  │     RAG Service (Port 8080)                     │     │
│  │  - Receives question/requirements               │     │
│  │  - Searches vector DB (FAISS) ← YOU SET THIS UP│     │
│  │  - Generates response with LLM                  │     │
│  │  - Returns structured spec                      │     │
│  └──────────────────┬──────────────────────────────┘     │
│                     │                                     │
│                     ↓ (HTTP API Call)                     │
│  ┌─────────────────────────────────────────────────┐     │
│  │     MCP Core Service (Port 5001)                │     │
│  │  - Performs electrical calculations             │     │
│  │  - Validates design against NEC standards       │     │
│  │  - Generates AutoLISP code                      │     │
│  │  - Returns calculation results                  │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  Output: AutoLISP code → Copy to AutoCAD                 │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 📞 Getting Help

If you're still stuck:

1. **Check logs**:
   ```bash
   tail -50 Copilot-Mozart/ACA_Mozart-copilot[RAG]/logs/mcp_spec/$(date +%Y-%m-%d).jsonl
   ```

2. **Run ingest with debug**:
   ```bash
   python scripts/ingest_all.py 2>&1 | tee debug.log
   cat debug.log | grep -i error
   ```

3. **Check system resources**:
   ```bash
   top           # Check CPU/RAM usage
   df -h         # Check disk space
   netstat -tulpn | grep -E "5001|8080"  # Check ports
   ```

---

*Created: December 10, 2025*  
*Author: Opsia (Infrastructure Guardian)*  
*Status: Production Ready*
