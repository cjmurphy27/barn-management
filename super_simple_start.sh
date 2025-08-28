#!/bin/bash
# super_simple_start.sh
# Get Barn Lady working with minimal fuss

echo "🐴 Super Simple Barn Lady Start (No Docker)"
echo "==========================================="

# Clean up any existing processes
echo "🧹 Cleaning up..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true
pkill -f "python.*app.main" 2>/dev/null || true

# Force kill anything on our ports
for port in 8000 8501; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "Killing process on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

sleep 3

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ No virtual environment found"
    echo "Creating one now..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated"

# Make sure we have the basic packages
echo "📦 Installing essential packages..."
pip install --quiet fastapi uvicorn streamlit requests

# Create a super simple API that works
echo "📝 Creating minimal working API..."
cat > simple_api.py << 'API_EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="Barn Lady Simple API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "🐴 Barn Lady Simple API is working!",
        "status": "healthy",
        "time": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "healthy", "api": "working"}

@app.get("/test")
def test():
    return {"test": "success", "message": "API is responding correctly"}
API_EOF

# Create a super simple frontend that works
echo "📝 Creating minimal working frontend..."
cat > simple_frontend.py << 'FRONTEND_EOF'
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="🐴 Barn Lady", page_icon="🐴")

st.title("🐴 Barn Lady - Simple Version")
st.markdown("### Just Testing That Everything Works")

# Show current time to prove it's live
st.info(f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')}")

# Test API connection
st.markdown("---")
st.markdown("## 🔌 API Connection Test")

try:
    response = requests.get("http://localhost:8000/", timeout=3)
    if response.status_code == 200:
        st.success("✅ API is working!")
        data = response.json()
        st.json(data)
        
        # Test another endpoint
        test_response = requests.get("http://localhost:8000/test", timeout=3)
        if test_response.status_code == 200:
            st.success("✅ API test endpoint working!")
            st.json(test_response.json())
            
    else:
        st.error(f"❌ API returned status {response.status_code}")
        
except requests.exceptions.ConnectionError:
    st.error("❌ Cannot connect to API")
    st.markdown("**The API might not be running**")
    
except Exception as e:
    st.error(f"❌ Error: {str(e)}")

# Simple interactive elements
st.markdown("---")
st.markdown("## 🧪 Interactive Test")

if st.button("🔄 Refresh Page"):
    st.rerun()

name = st.text_input("Enter a horse name:", placeholder="Thunder")
if name:
    st.success(f"🐎 Hello {name}!")

# Show this is working
st.markdown("---")
st.success("✅ If you can see this page, your Streamlit frontend is working!")
st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
FRONTEND_EOF

echo "✅ Created simple files"

# Start API
echo "🚀 Starting simple API on port 8000..."
uvicorn simple_api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to start
sleep 3

# Test if API is responding
if curl -s http://localhost:8000/ >/dev/null 2>&1; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding"
    kill $API_PID 2>/dev/null || true
    echo "Try running manually: uvicorn simple_api:app --port 8000"
    exit 1
fi

# Start Frontend
echo "📱 Starting simple frontend on port 8501..."
streamlit run simple_frontend.py --server.port 8501 &
FRONTEND_PID=$!

# Save PIDs
echo $API_PID > .simple_api.pid
echo $FRONTEND_PID > .simple_frontend.pid

echo ""
echo "🎉 SUCCESS! Both services started!"
echo "=================================="
echo "📱 Frontend: http://localhost:8501"
echo "🔌 API: http://localhost:8000"
echo ""
echo "🛑 To stop: kill \$(cat .simple_api.pid .simple_frontend.pid)"
echo ""
echo "Wait 10 seconds then visit the frontend URL in your browser"
