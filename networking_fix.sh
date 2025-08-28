#!/bin/bash

echo "🔧 Fixing Docker container networking..."

# Test if containers can actually communicate
echo "🧪 Testing container-to-container networking..."
docker-compose exec frontend curl -s http://api:8000/health || echo "❌ Container networking failed"

# Fix: Update frontend to use host.docker.internal instead of service name
echo "📝 Updating frontend networking configuration..."
cat > frontend/app.py << 'FRONTENDPY'
import streamlit as st
import requests
import os

st.set_page_config(page_title="Barn Lady", layout="wide")

# Try different API endpoints for Docker networking issues
API_ENDPOINTS = [
    "http://api:8000/api/v1",                    # Docker service name
    "http://host.docker.internal:8000/api/v1",  # Docker Desktop fallback
    "http://localhost:8000/api/v1",             # Direct host access
    "http://172.18.0.4:8000/api/v1"             # Direct container IP
]

def test_api_connection():
    """Test different API endpoints to find one that works"""
    for endpoint in API_ENDPOINTS:
        try:
            health_url = endpoint.replace('/api/v1', '/health')
            response = requests.get(health_url, timeout=3)
            if response.status_code == 200:
                return endpoint
        except:
            continue
    return None

# Find working API endpoint
API_BASE_URL = test_api_connection()

st.title("🐴 Barn Lady - Multi-Barn Horse Management")

# Add debug info
with st.expander("🔧 Debug Info"):
    st.write(f"**Working API Base URL:** {API_BASE_URL}")
    st.write(f"**Environment Variables:**")
    for key, value in os.environ.items():
        if 'API' in key or 'PROPEL' in key:
            st.write(f"- {key}: {value}")
    
    st.write("**API Endpoint Test Results:**")
    for endpoint in API_ENDPOINTS:
        try:
            health_url = endpoint.replace('/api/v1', '/health')
            response = requests.get(health_url, timeout=2)
            if response.status_code == 200:
                st.success(f"✅ {endpoint} - Working")
            else:
                st.error(f"❌ {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            st.error(f"❌ {endpoint} - {str(e)[:50]}...")

if st.button("🚀 Load Your Horses"):
    st.session_state.show_horses = True

if st.session_state.get('show_horses'):
    if not API_BASE_URL:
        st.error("❌ Cannot connect to API. Please check the Debug Info above.")
    else:
        st.success("✅ Connected to Fernbell Barn!")
        
        try:
            horses_url = f"{API_BASE_URL}/horses/"
            st.info(f"Calling: {horses_url}")
            
            response = requests.get(horses_url, timeout=10)
            if response.status_code == 200:
                horses = response.json()
                
                st.write(f"**{len(horses)} horses in your barn:**")
                
                for horse in horses:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.subheader(f"🐴 {horse['name']}")
                            details = [
                                f"**Breed:** {horse['breed']}",
                                f"**Age:** {horse['age_display']}",
                                f"**Color:** {horse['color']}",
                                f"**Gender:** {horse['gender']}"
                            ]
                            st.markdown(" | ".join(details))
                            
                            if horse.get('current_location'):
                                st.write(f"📍 {horse['current_location']}")
                            if horse.get('owner_name'):
                                st.write(f"👤 Owner: {horse['owner_name']}")
                        
                        with col2:
                            st.write(f"**Status:** {horse['current_health_status']}")
                            if horse.get('is_for_sale'):
                                st.info("🏷️ For Sale")
                            if horse.get('is_retired'):
                                st.info("🌅 Retired")
                        
                        st.markdown("---")
            else:
                st.error(f"API Error: {response.status_code}")
                st.error(f"Response: {response.text}")
        
        except Exception as e:
            st.error(f"Connection Error: {e}")
            st.error(f"Tried to connect to: {API_BASE_URL}/horses/")

# Add a simple health check
if st.button("🔍 Test API Connection"):
    if not API_BASE_URL:
        st.error("❌ No working API endpoint found")
    else:
        try:
            health_url = f"{API_BASE_URL.replace('/api/v1', '')}/health"
            st.info(f"Testing: {health_url}")
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                st.success("✅ API is healthy!")
                st.json(response.json())
            else:
                st.error(f"❌ API health check failed: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Cannot reach API: {e}")
FRONTENDPY

echo "✅ Updated frontend with smart networking"

# Restart frontend to pick up changes
echo "🔄 Restarting frontend..."
docker-compose restart frontend

echo "⏱️ Waiting for frontend to restart..."
sleep 5

echo "🎉 Try http://localhost:8501 again!"
echo "The frontend will now test multiple connection methods automatically."
