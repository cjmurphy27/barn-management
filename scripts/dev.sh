#!/bin/bash

case "$1" in
    "start")
        echo "🚀 Starting Barn Lady..."
        
        # Start database
        docker-compose up -d db redis
        sleep 10
        
        # Activate venv if it exists
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        # Start API
        uvicorn app.main:app --reload --port 8000 &
        echo $! > .api.pid
        
        # Start frontend
        (cd frontend && streamlit run app.py --server.port 8501) &
        echo $! > .frontend.pid
        
        echo "✅ Started!"
        echo "Frontend: http://localhost:8501"
        echo "API: http://localhost:8000"
        ;;
    "stop")
        echo "🛑 Stopping..."
        
        if [ -f .api.pid ]; then
            kill $(cat .api.pid) 2>/dev/null || true
            rm .api.pid
        fi
        
        if [ -f .frontend.pid ]; then
            kill $(cat .frontend.pid) 2>/dev/null || true
            rm .frontend.pid
        fi
        
        pkill -f "uvicorn app.main" 2>/dev/null || true
        pkill -f "streamlit run" 2>/dev/null || true
        docker-compose down
        
        echo "✅ Stopped!"
        ;;
    "install")
        echo "📦 Installing..."
        
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        pip install -r requirements.txt
        echo "✅ Installed!"
        ;;
    *)
        echo "Commands: start | stop | install"
        ;;
esac
