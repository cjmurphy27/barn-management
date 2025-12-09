# Python FastAPI Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Ensure Python can import the top-level `app` package when working dir is /app
ENV PYTHONPATH=/

# Copy only requirements first so we can install dependencies during build
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install curl for container-local healthchecks and simple tools
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Expose port
EXPOSE 8000
