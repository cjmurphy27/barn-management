#!/bin/bash

# Run database migration on startup
echo "Running database migration..."
python migrate_on_startup.py

# Start FastAPI backend on port 8002
uvicorn app.main:app --host 0.0.0.0 --port 8002 &

# Wait for backend to start
sleep 3

# Start Streamlit frontend on the main port
PORT=${PORT:-8000}
exec streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0