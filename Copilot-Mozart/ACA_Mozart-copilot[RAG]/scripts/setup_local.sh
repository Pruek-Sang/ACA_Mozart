#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# ACA Mozart - Local Setup Script
# ═══════════════════════════════════════════════════════════════════
# Run this script once after cloning the repository
# Usage: ./scripts/setup_local.sh
# ═══════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "🏛️ ACA Mozart - Local Setup"
echo "═══════════════════════════════════════════════════════════════════"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAG_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$(dirname "$RAG_DIR")")"
MCP_DIR="$ROOT_DIR/mcp_core_v2"

echo "📂 RAG Directory: $RAG_DIR"
echo "📂 MCP Directory: $MCP_DIR"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step 1: Check vector_db exists
# ═══════════════════════════════════════════════════════════════════
echo "📦 Step 1: Checking vector_db..."
if [ -f "$RAG_DIR/vector_db/faiss/faiss.index" ]; then
    echo "   ✅ vector_db found!"
else
    echo "   ❌ vector_db NOT found!"
    echo "   Please run 'git pull' to get the pre-built vector_db"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# Step 2: Check/Create .env file
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "🔑 Step 2: Checking .env file..."
if [ -f "$RAG_DIR/.env" ]; then
    echo "   ✅ .env found!"
else
    echo "   ⚠️  .env not found. Creating from example..."
    cp "$RAG_DIR/.env.example" "$RAG_DIR/.env"
    echo "   📝 Please edit $RAG_DIR/.env and add your GOOGLE_API_KEY"
    echo ""
    echo "   Get your API key from: https://aistudio.google.com/app/apikey"
    echo ""
    read -p "   Press Enter after you've added your API key..."
fi

# ═══════════════════════════════════════════════════════════════════
# Step 3: Install Python dependencies
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "📦 Step 3: Installing Python dependencies..."

echo "   Installing RAG dependencies..."
pip install -r "$RAG_DIR/Docker/requirements_light.txt" -q

echo "   Installing MCP Core dependencies..."
pip install -r "$MCP_DIR/requirements.txt" -q

echo "   ✅ Dependencies installed!"

# ═══════════════════════════════════════════════════════════════════
# Step 4: Verify setup
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Step 4: Verifying setup..."

# Check vector_db count
CHUNK_COUNT=$(cd "$RAG_DIR" && python -c "from core.vector_adapter import get_vector_db; db = get_vector_db(); print(db.count())" 2>/dev/null || echo "0")
echo "   Vector DB chunks: $CHUNK_COUNT"

if [ "$CHUNK_COUNT" -gt "0" ]; then
    echo "   ✅ Vector DB is ready!"
else
    echo "   ❌ Vector DB is empty!"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# Done!
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "To start the services, run:"
echo ""
echo "   # Terminal 1: Start MCP Core"
echo "   cd $MCP_DIR && python api.py"
echo ""
echo "   # Terminal 2: Start RAG Service"
echo "   cd $RAG_DIR && python main_ACA.py"
echo ""
echo "   # Test:"
echo "   curl http://localhost:8080/"
echo "   curl http://localhost:5001/health"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
