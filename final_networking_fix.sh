#!/bin/bash

echo "🔧 Final networking fix - using host network access..."

# Update the frontend to use host networking
cat > frontend/app.py << 'FRONTENDPY'
import streamlit as st
import requests
import os

st.set_page_config(page_title="Barn Lady", layout="wide")

# Use host network since container networking is having issues
API_BASE_URL = "http://host.docker.internal:8000/api/v1"

def test_api_connection():
    """Test if API is reachable"""
    try:
        health_url = "http://host.docker.internal:8000/health"
        response = requests.get(health_url, timeout=3)
        return response.status_code == 200
    except:
        return False

st.title("🐴 Barn Lady - Multi-Barn Horse Management")

# Add debug info
with st.expander("🔧 Debug Info"):
    st.write(f"**API Base URL:** {API_BASE_URL}")
    st.write(f"**Environment Variables:**")
    for key, value in os.environ.items():
        if 'API' in key or 'PROPEL' in key:
            st.write(f"- {key}: {value}")
    
    # Test connection
    if test_api_connection():
        st.success("✅ API connection working!")
    else:
        st.error("❌ Cannot reach API")

if st.button("🚀 Load Your Horses"):
    st.session_state.show_horses = True

if st.session_state.get('show_horses'):
    if not test_api_connection():
        st.error("❌ Cannot connect to API. Please check if containers are running.")
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

# Test API Connection button
if st.button("🔍 Test API Connection"):
    try:
        health_url = "http://host.docker.internal:8000/health"
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

echo "✅ Updated frontend to use host networking"

# Restart frontend to pick up changes
echo "🔄 Restarting frontend..."
docker-compose restart frontend

echo "⏱️ Waiting for frontend to restart..."
sleep 5

echo "🎉 Try http://localhost:8501 again!"
echo "The frontend should now connect via host.docker.internal"
