#!/bin/bash
# Quick ingest script - runs detached from terminal
# Usage: ./scripts/quick_ingest.sh

cd /workspaces/ACA_Mozart-clone/Copilot-Mozart/ACA_Mozart-copilot[RAG]

echo "🚀 Starting ingest in background..."
echo "📄 Log file: ingest_output.log"
echo "⏱️  Check progress: tail -f ingest_output.log"

# Run Python ingest completely detached
setsid python -u scripts/ingest_all.py > ingest_output.log 2>&1 &

INGEST_PID=$!
echo "🔧 PID: $INGEST_PID"
echo ""
echo "Commands:"
echo "  tail -f ingest_output.log   # Watch progress"
echo "  ps aux | grep $INGEST_PID   # Check if running"
echo "  kill $INGEST_PID            # Stop if needed"
