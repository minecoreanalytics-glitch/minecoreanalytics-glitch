#!/bin/bash

# Kill any existing processes on ports 8000 (backend) or 5173 (frontend)
echo "🧹 Cleaning up old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Check for API Key
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: GEMINI_API_KEY is not set. The Chat features won't work."
    echo "   Please run: export GEMINI_API_KEY='your_key' before running this script."
    echo "   (Or add it to backend/.env)"
    sleep 2
fi

# Start Backend
echo "🚀 Starting Backend (Port 8000)..."
cd backend
# Use venv python if available, else fallback to system python
if [ -f "../.venv/bin/python" ]; then
    PYTHON_CMD="../.venv/bin/python"
else
    PYTHON_CMD="python"
fi

$PYTHON_CMD main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "   Backend running (PID: $BACKEND_PID). Logs at backend.log"

# Start Frontend
echo "✨ Starting Frontend..."
# Run in foreground so user can see URL
npm run dev

# Cleanup on exit
kill $BACKEND_PID
