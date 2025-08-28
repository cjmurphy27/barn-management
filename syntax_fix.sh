#!/bin/bash
# Quick fix for syntax error in frontend

echo "🔧 Fixing syntax error in frontend..."

# Create a clean, simple frontend app that works
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
            health_url = f"{endpoint}/health"
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                return endpoint, response.json()
        except requests.exceptions.RequestException:
            continue
        
        try:
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
    st.success("✅ Successfully connected to Barn Lady API!")
    st.info(f"Connected to: {api_endpoint}")
    
    with st.expander("📊 API Response Details", expanded=False):
        st.json(api_data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("API Status", api_data.get("status", "unknown").title())
    with col2:
        st.metric("Version", api_data.get("version", "unknown"))
    with col3:
        st.metric("Last Response", "Just now")

else:
    st.error("❌ Could not connect to API")
    
    with st.expander("🔧 Troubleshooting", expanded=True):
        st.markdown("**API connection failed. Try these steps:**")
        st.code("docker-compose ps")
        st.code("curl http://localhost:8000/health")
        st.code("docker-compose restart api")
    
    st.warning("Attempted connections to:")
    for endpoint in API_ENDPOINTS:
        st.code(f"{endpoint}/health")

st.markdown("---")

# Application features section
st.markdown("#### 🚀 Available Features")

if api_endpoint:
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
    
    st.info("🎯 Next Steps: Configure your PropelAuth and Anthropic API keys in the .env file to 
unlock all features!")

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
    st.markdown("- PropelAuth (Authentication)")
    st.markdown("- Anthropic (AI Features)")

# Footer
st.markdown("---")
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.markdown(f"*Enhanced Barn Lady • {current_time}*")
EOF

echo "✅ Fixed syntax error"
echo "🔄 Restarting frontend container..."

# Restart frontend container
docker-compose restart frontend

# Wait for restart
sleep 10

echo "🎉 Frontend should now be working!"
echo "   Refresh your browser at: http://localhost:8501"
