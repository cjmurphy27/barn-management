#!/bin/bash
# clean_restart.sh
# Clean up any existing processes and start fresh

echo "🧹 Cleaning up and restarting Barn Lady..."

# Kill any existing processes on ports 8000 and 8501
echo "🛑 Stopping any existing processes..."

# Kill processes using port 8000 (API)
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "Killing processes on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

# Kill processes using port 8501 (Frontend)
if lsof -ti:8501 >/dev/null 2>&1; then
    echo "Killing processes on port 8501..."
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
fi

# Kill any uvicorn or streamlit processes
pkill -f "uvicorn app.main" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true

# Clean up PID files
rm -f .api.pid .frontend.pid

echo "✅ Cleaned up existing processes"

# Wait a moment for ports to be released
sleep 3

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running! Please start Docker Desktop first."
    exit 1
fi

# Make sure Docker services are running
echo "🐳 Ensuring Docker services are running..."
docker-compose up -d db redis

# Wait for services to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Verify ports are free
echo "🔍 Checking ports..."
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "❌ Port 8000 is still in use!"
    lsof -i:8000
    exit 1
fi

if lsof -ti:8501 >/dev/null 2>&1; then
    echo "❌ Port 8501 is still in use!"
    lsof -i:8501
    exit 1
fi

echo "✅ Ports 8000 and 8501 are available"

# Start API
echo "🚀 Starting API on port 8000..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to start
sleep 5

# Check if API started successfully
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API started successfully"
else
    echo "❌ API failed to start"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Configure Streamlit to skip the welcome screen
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml << 'EOF'
[browser]
gatherUsageStats = false

[server]
headless = true
EOF

# Also create local streamlit config
mkdir -p frontend/.streamlit
cat > frontend/.streamlit/config.toml << 'EOF'
[browser]
gatherUsageStats = false

[server]
headless = true
port = 8501
address = "0.0.0.0"

[theme]
primaryColor = "#2E8B57"
EOF

# Start Frontend
echo "📱 Starting Frontend on port 8501..."
(cd frontend && streamlit run app.py --server.port 8501 --server.headless true) &
FRONTEND_PID=$!

# Save PIDs
echo $API_PID > .api.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for frontend to start
sleep 5

# Check if frontend started
if curl -s http://localhost:8501 >/dev/null 2>&1; then
    echo "✅ Frontend started successfully"
else
    echo "⚠️  Frontend may still be starting up..."
fi

echo ""
echo "🎉 Barn Lady started successfully!"
echo "================================="
echo "📱 Frontend: http://localhost:8501"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📊 API Status: http://localhost:8000/api/v1/status"
echo ""
echo "🛑 To stop: ./scripts/dev.sh stop"
echo ""
echo "Wait 10-15 seconds then visit the frontend URL"
