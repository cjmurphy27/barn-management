#!/bin/bash

echo "🔧 Fixing API to bind to all interfaces..."

# The issue is the API only binds to localhost inside the container
# Let's check and fix the Dockerfile CMD

# Update the Dockerfile to ensure proper binding
cat > Dockerfile << 'DOCKERFILE'
# FastAPI Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Create storage directory for tenant files
RUN mkdir -p /app/storage

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Expose port
EXPOSE 8000

# Start command - FORCE binding to 0.0.0.0
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
DOCKERFILE

echo "✅ Updated Dockerfile to force bind to 0.0.0.0"

# Also ensure main.py has correct binding in case it overrides
echo "Checking main.py uvicorn config..."
grep -n "uvicorn.run" app/main.py

# Rebuild the API with the fixed Dockerfile
echo "🔧 Rebuilding API container..."
docker-compose build --no-cache api

# Restart the API
echo "🔄 Restarting API..."
docker-compose restart api

echo "⏱️ Waiting for API to start with proper binding..."
sleep 15

echo "🧪 Testing API from host:"
curl -s http://localhost:8000/health | head -c 50

echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "🎉 Try the Debug Connection button at http://localhost:8501"
echo "The API should now accept connections from other containers!"
