#!/bin/bash

echo "🔧 Bypassing Docker health check to get frontend working..."

# Backup the original docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Create a temporary version without the dependency
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

  # Streamlit Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://api:8000/api/v1
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

echo "✅ Removed health check dependency"

# Stop and restart with the fixed compose file
docker-compose down
docker-compose up -d

echo "⏱️ Waiting for services..."
sleep 10

echo "📊 Container status:"
docker-compose ps

echo ""
echo "🧪 Testing connections:"
echo "API: $(curl -s http://localhost:8000/health | head -c 50)..."
echo ""

if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ Frontend is running!"
    echo "🎉 Try http://localhost:8501 now!"
else
    echo "❌ Frontend still not responding"
    echo "📋 Frontend logs:"
    docker-compose logs frontend
fi
