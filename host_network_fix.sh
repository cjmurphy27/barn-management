#!/bin/bash

echo "🔧 Using host networking for frontend..."

# Update docker-compose to use host networking for frontend
cat > docker-compose.yml << 'COMPOSE'
services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: barnlady
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  # FastAPI Backend
  api:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/barnlady
      - PROPELAUTH_URL=${PROPELAUTH_URL}
      - PROPELAUTH_API_KEY=${PROPELAUTH_API_KEY}
      - PROPELAUTH_VERIFIER_KEY=${PROPELAUTH_VERIFIER_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEBUG=true
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./app:/app/app:ro
      - ./storage:/app/storage

  # Streamlit Frontend - using host networking
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    network_mode: host
    environment:
      - API_BASE_URL=http://localhost:8000/api/v1
      - PROPELAUTH_URL=${PROPELAUTH_URL}
    volumes:
      - ./frontend:/app:ro

  # Redis (for future caching/sessions)
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  default:
    name: barnlady-network
COMPOSE

# Update frontend to use localhost
cat > frontend/app.py << 'FRONTENDPY'
import streamlit as st
import requests
import os

st.set_page_config(page_title="Barn Lady", layout="wide")

# Use localhost since we're using host networking
API_BASE_URL = "http://localhost:8000/api/v1"

def test_api_connection():
    """Test if API is reachable"""
    try:
        health_url = "http://localhost:8000/health"
        response = requests.get(health_url, timeout=3)
        return response.status_code == 200
    except:
        return False

st.title("🐴 Barn Lady - Multi-Barn Horse Management")

# Add debug info
with st.expander("🔧 Debug Info"):
    st.write(f"**API Base URL:** {API_BASE_URL}")
    st.write("**Using host networking mode**")
    
    # Test connection
    if test_api_connection():
        st.success("✅ API connection working!")
    else:
        st.error("❌ Cannot reach API at localhost:8000")

if st.button("🚀 Load Your Horses"):
    st.session_state.show_horses = True

if st.session_state.get('show_horses'):
    if not test_api_connection():
        st.error("❌ Cannot connect to API")
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
        health_url = "http://localhost:8000/health"
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

echo "✅ Updated to use host networking"

# Restart everything
echo "🔄 Restarting with host networking..."
docker-compose down
docker-compose up -d

echo "⏱️ Waiting for services..."
sleep 15

echo "📊 Container status:"
docker-compose ps

echo ""
echo "🎉 Try http://localhost:8501 now!"
echo "Frontend now uses host networking to bypass container networking issues."
