#!/bin/bash

echo "🐴 Starting Barn Lady System..."
echo "==============================="

# Check if API is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  API is already running on port 8000"
else
    echo "🚀 Starting API backend..."
    cd app
    python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    API_PID=$!
    echo "   ✅ API started with PID: $API_PID"
    cd ..
fi

# Wait a moment for API to start
sleep 2

echo "🎨 Starting Streamlit frontend..."
cd frontend
python3 -m streamlit run app.py

