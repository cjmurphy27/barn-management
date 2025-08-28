#!/bin/bash
# Fix frontend API connection issues

echo "🔧 Fixing frontend API connection..."
echo "==================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this from the barn-management directory"
    exit 1
fi

# Backup existing frontend app
if [ -f "frontend/app.py" ]; then
    echo "📄 Backing up existing frontend..."
    cp frontend/app.py frontend/app.py.backup
fi

# Create the fixed frontend app
echo "🎨 Creating enhanced frontend..."
cat > frontend/app.py << 'EOF'
import streamlit as st
import requests
from datetime import datetime
import os

st.set_page_config(
    page_title="🐴 Barn Lady",
    page_icon="🐴",
    layout="wide"
)

st.title("🐴 Barn Lady - Enhanced Version")
st.markdown("### AI-Powered Horse Management System")

# API Configuration - try multiple endpoints
API_ENDPOINTS = [
    "http://api:8000",  # Docker internal network
    "http://localhost:8000",  # Local development
    "http://127.0.0.1:8000",  # Alternative local
]

def test_api_connection():
    """Test API connection with multiple endpoints"""
    for endpoint in API_ENDPOINTS:
        try:
            # Test health endpoint first
            health_url = f"{endpoint}/health"
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                return endpoint, response.json()
        except requests.exceptions.RequestException:
            continue
        
        try:
            # Try root endpoint if health fails
            root_url = f"{endpoint}/"
            response = requests.get(root_url, timeout=5)
            if response.status_code == 200:
                return endpoint, response.json()
        except requests.exceptions.RequestException:
            continue
    
    return None, None

# Test API connection
st.markdown("#### 🔌 API Connection Status")

with st.spinner("Testing API connection..."):
    api_endpoint, api_data = test_api_connection()

if api_endpoint and api_data:
    st.success(f"✅ Successfully connected to Barn Lady API!")
    st.info(f"Connected to: `{api_endpoint}`")
    
    # Show API response in an expandable section
    with st.expander("📊 API Response Details", expanded=False):
        st.json(api_data)
    
    # API Status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("API Status", api_data.get("status", "unknown").title())
    with col2:
        st.metric("Version", api_data.get("version", "unknown"))
    with col3:
        if "timestamp" in api_data:
            st.metric("Last Response", "Just now")
        else:
            st.metric("Response Time", "< 1s")

else:
    st.error("❌ Could not connect to API")
    
    with st.expander("🔧 Troubleshooting", expanded=True):
        st.markdown("""
        **API connection failed. Try these steps:**
        
        1. **Check if API is running:**
           ```bash
           docker-compose ps
           curl http://localhost:8000/health
           ```
        
        2. **Restart services:**
           ```bash
           ./scripts/dev.sh start
           ```
        
        3. **Check logs:**
           ```bash
           docker-compose logs api
           ```
        
        4. **Manual restart:**
           ```bash
           docker-compose restart api
           ```
        """)
    
    # Show what we tried
    st.warning("Attempted connections to:")
    for endpoint in API_ENDPOINTS:
        st.code(f"{endpoint}/health")
        st.code(f"{endpoint}/")

st.markdown("---")

# Application features section
st.markdown("#### 🚀 Available Features")

if api_endpoint:
    # Show features since API is connected
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🐎 Horse Management**
        - Complete horse profiles
        - Health records tracking
        - Feeding schedules
        
        **🏥 Veterinary Care**
        - Medical history
        - Vaccination tracking
        - Treatment records
        """)
    
    with col2:
        st.markdown("""
        **🤖 AI Features**
        - Health insights
        - Feeding recommendations
        - Care suggestions
        
        **📊 Analytics**
        - Health trends
        - Feeding analytics
        - Performance metrics
        """)
    
    st.info("🎯 **Next Steps:** Configure your PropelAuth and Anthropic API keys in the .env file 
to unlock all features!")

else:
    st.markdown("""
    **Available once API is connected:**
    - 🐎 Horse Management
    - 🏥 Health Records  
    - 🤖 AI Integration
    - 📊 Analytics Dashboard
    """)

# Configuration section
st.markdown("---")
st.markdown("#### ⚙️ Configuration Status")

config_col1, config_col2 = st.columns(2)

with config_col1:
    st.markdown("**📁 Environment File**")
    env_file_exists = os.path.exists("/app/.env") or os.path.exists(".env")
    if env_file_exists:
        st.success("✅ .env file found")
    else:
        st.warning("⚠️ .env file missing")

with config_col2:
    st.markdown("**🔑 API Keys**")
    st.info("Configure in .env file")
    st.markdown("""
    - PropelAuth (Authentication)
    - Anthropic (AI Features)
    """)

# Footer
st.markdown("---")
st.markdown(f"*Enhanced Barn Lady • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

# Auto-refresh option
if st.checkbox("🔄 Auto-refresh connection status (every 30s)"):
    import time
    time.sleep(30)
    st.rerun()
EOF

echo "✅ Enhanced frontend created"

# Restart the frontend container to pick up changes
echo "🔄 Restarting frontend container..."
docker-compose restart frontend

# Wait for it to start
echo "⏳ Waiting for frontend to restart..."
sleep 10

# Test if frontend is responding
echo "🧪 Testing frontend..."
if curl -f http://localhost:8501 >/dev/null 2>&1; then
    echo "✅ Frontend is responding!"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "🎉 Frontend fix completed!"
echo "   Refresh your browser at: http://localhost:8501"
echo "   The new frontend will test multiple API endpoints automatically"
echo ""
echo "📋 What was fixed:"
echo "   - Added Docker internal network endpoint (http://api:8000)"
echo "   - Multiple endpoint fallback system"
echo "   - Better error handling and troubleshooting info"
echo "   - Enhanced UI with status indicators"
