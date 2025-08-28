#!/bin/bash

echo "🔄 Reverting to bridge networking and fixing properly..."

# Restore the working docker-compose.yml with bridge networking
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

  # Streamlit Frontend - back to bridge networking with port mapping
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://localhost:8000/api/v1
      - PROPELAUTH_URL=${PROPELAUTH_URL}
    volumes:
      - ./frontend:/app:ro

  # Redis
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

# Simple frontend that uses the host's localhost (since API works there)
cat > frontend/app.py << 'FRONTENDPY'
import streamlit as st
import requests

st.set_page_config(page_title="Barn Lady", layout="wide")

st.title("🐴 Barn Lady - Multi-Barn Horse Management")

# Since the API works on localhost:8000 from the host, try that from frontend
API_BASE_URL = "http://localhost:8000/api/v1"

if st.button("🚀 Load Your Horses"):
    try:
        st.info(f"Calling: {API_BASE_URL}/horses/")
        response = requests.get(f"{API_BASE_URL}/horses/", timeout=10)
        
        if response.status_code == 200:
            horses = response.json()
            st.success(f"✅ Found {len(horses)} horses!")
            
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
            st.error(f"API Error: {response.status_code} - {response.text}")
    
    except Exception as e:
        st.error(f"Connection Error: {e}")

if st.button("🔍 Test API"):
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ API is healthy!")
            st.json(response.json())
        else:
            st.error(f"❌ API returned: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Cannot reach API: {e}")
FRONTENDPY

echo "✅ Reverted to bridge networking with proper port mapping"

# Restart everything
echo "🔄 Restarting all services..."
docker-compose down
docker-compose up -d

echo "⏱️ Waiting for services to start..."
sleep 15

echo "📊 Container status:"
docker-compose ps

echo ""
echo "🎉 Try http://localhost:8501 now!"
echo "Frontend should be accessible again with proper port mapping."
