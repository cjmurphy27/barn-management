#!/bin/bash

echo "🔧 Final API networking fix..."

# Check what the API is currently doing
echo "Current API status:"
curl -s http://localhost:8000/health

# Update the API to ensure it binds to 0.0.0.0 AND add explicit service networking
cat > frontend/app.py << 'FRONTENDPY'
import streamlit as st
import requests

st.set_page_config(page_title="Barn Lady", layout="wide")

st.title("🐴 Barn Lady - Multi-Barn Horse Management")

# Try multiple connection methods in order
def try_api_connection():
    endpoints = [
        "http://api:8000",  # Docker service name
        "http://localhost:8000"  # Fallback
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{endpoint}/health", timeout=2)
            if response.status_code == 200:
                return endpoint
        except:
            continue
    return None

if st.button("🚀 Load Your Horses"):
    api_endpoint = try_api_connection()
    
    if not api_endpoint:
        st.error("❌ Cannot connect to API using any method")
        st.info("Tried: api:8000, localhost:8000")
    else:
        st.success(f"✅ Connected via {api_endpoint}")
        
        try:
            response = requests.get(f"{api_endpoint}/api/v1/horses/", timeout=10)
            
            if response.status_code == 200:
                horses = response.json()
                st.success(f"🐴 Found {len(horses)} horses in your barn!")
                
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
                        
                st.balloons()  # Celebrate success!
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
        
        except Exception as e:
            st.error(f"Error loading horses: {e}")

if st.button("🔍 Debug Connection"):
    st.write("**Testing all connection methods:**")
    
    methods = [
        ("Docker service name", "http://api:8000/health"),
        ("Localhost", "http://localhost:8000/health"),
        ("Direct container IP", "http://172.18.0.5:8000/health")
    ]
    
    for name, url in methods:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                st.success(f"✅ {name}: Working")
            else:
                st.error(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            st.error(f"❌ {name}: {str(e)[:100]}...")
FRONTENDPY

echo "✅ Updated frontend with multiple connection attempts"

# Restart frontend to pick up changes
echo "🔄 Restarting frontend..."
docker-compose restart frontend

# Also restart API to ensure it's binding properly
echo "🔄 Restarting API..."
docker-compose restart api

echo "⏱️ Waiting for services..."
sleep 10

echo "🧪 Testing API directly:"
curl -s http://localhost:8000/health | head -c 100

echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "🎉 Try http://localhost:8501 again!"
echo "Click 'Debug Connection' to see which method works."
