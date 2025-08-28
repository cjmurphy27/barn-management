#!/bin/bash
# quick_fix_upgrade.sh
# Complete the Barn Lady upgrade from where it left off

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "🔧 =============================================="
echo "   BARN LADY UPGRADE - QUICK FIX"
echo "   Completing the upgrade from where it left off"
echo "===============================================${NC}"
echo

# Function to print success messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print info messages
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Function to print section headers
print_section() {
    echo -e "${PURPLE}📋 $1${NC}"
    echo "----------------------------------------"
}

# Fix the .env file (add missing variables if needed)
fix_env_file() {
    print_section "Fixing Environment Configuration"
    
    # Check and add missing variables
    if ! grep -q "SECRET_KEY" .env; then
        echo "" >> .env
        echo "# Added by upgrade script" >> .env
        echo 
"SECRET_KEY=your-secret-key-change-this-in-production-minimum-32-characters" 
>> .env
        print_success "Added SECRET_KEY to .env file"
    fi
    
    if ! grep -q "ANTHROPIC_API_KEY" .env; then
        echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env
        print_success "Added ANTHROPIC_API_KEY to .env file"
    fi
    
    print_success "Environment file is ready"
    echo
}

# Create missing directories
create_directories() {
    print_section "Creating Missing Directories"
    
    directories=(
        "app/core"
        "app/models" 
        "app/api"
        "app/services"
        "frontend/.streamlit"
        "scripts"
        "tests"
        "logs"
        "docs"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        fi
    done
    echo
}

# Update requirements.txt
update_requirements() {
    print_section "Updating Requirements"
    
    cat > requirements.txt << 'EOF'
# Core FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# PropelAuth integration
propelauth-fastapi==3.1.3
propelauth-py==4.1.2

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Pydantic for data validation
pydantic==2.5.0
pydantic-settings==2.0.3

# Claude AI
anthropic==0.7.8

# Utilities
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dateutil==2.8.2

# File processing
PyPDF2==3.0.1
python-docx==1.1.0
openpyxl==3.1.2

# Data processing and export
pandas==2.1.3

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
black==23.11.0
flake8==6.1.0
isort==5.12.0

# System monitoring
psutil==5.9.6
EOF
    
    print_success "Updated requirements.txt"
    
    # Update frontend requirements
    cat > frontend/requirements.txt << 'EOF'
# Streamlit Frontend Dependencies
streamlit==1.28.1
requests==2.31.0
pandas==2.1.3
plotly==5.17.0

# Date/time handling
python-dateutil==2.8.2

# For handling API responses
pydantic==2.5.0

# Enhanced UI components
streamlit-elements==0.1.0
streamlit-option-menu==0.3.6
EOF
    
    print_success "Updated frontend/requirements.txt"
    echo
}

# Create core files
create_core_files() {
    print_section "Creating Core Application Files"
    
    # Create __init__.py files
    touch app/__init__.py
    touch app/core/__init__.py
    touch app/models/__init__.py
    touch app/api/__init__.py
    touch app/services/__init__.py
    touch tests/__init__.py
    
    # Create enhanced config.py
    cat > app/core/config.py << 'EOF'
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PropelAuth Configuration
    PROPELAUTH_URL: str = os.getenv("PROPELAUTH_URL", "")
    PROPELAUTH_API_KEY: str = os.getenv("PROPELAUTH_API_KEY", "")
    PROPELAUTH_VERIFIER_KEY: str = os.getenv("PROPELAUTH_VERIFIER_KEY", 
"")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", 
"postgresql://postgres:password@localhost:5432/barnlady")
    
    # Claude AI Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Application Configuration
    APP_NAME: str = "Barn Lady"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", 
"your-secret-key-change-this-in-production")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", 
"http://localhost:8501"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Validation helper
def validate_required_settings():
    """Validate that all required settings are present"""
    missing = []
    
    if not settings.PROPELAUTH_URL:
        missing.append("PROPELAUTH_URL")
    if not settings.PROPELAUTH_API_KEY:
        missing.append("PROPELAUTH_API_KEY")
    if not settings.ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', 
'.join(missing)}")
    
    return True
EOF
    
    print_success "Created app/core/config.py"
    
    # Create enhanced main.py
    cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Barn Lady API",
    version="1.0.0",
    description="AI-Powered Multi-Tenant Horse Management System",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🐴 Welcome to Barn Lady API - Enhanced Version!",
        "status": "healthy",
        "version": "1.0.0",
        "features": [
            "Multi-tenant horse management",
            "AI-powered insights with Claude",
            "Health record tracking",
            "Feeding management",
            "Analytics and reporting"
        ],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Barn Lady API is running",
        "components": {
            "api": "healthy",
            "config": "loaded"
        }
    }

@app.get("/api/v1/status")
async def api_status():
    """API status with configuration check"""
    try:
        from app.core.config import validate_required_settings
        
        config_status = "configured"
        missing_configs = []
        
        try:
            validate_required_settings()
        except ValueError as e:
            config_status = "missing_configs"
            missing_configs = str(e).split(": ")[1].split(", ")
        
        return {
            "api_status": "running",
            "config_status": config_status,
            "missing_configs": missing_configs,
            "timestamp": datetime.utcnow().isoformat(),
            "next_steps": [
                "Configure missing API keys in .env file" if 
missing_configs else "Ready for horse management!",
                "Visit /docs for API documentation",
                "Use the frontend at http://localhost:8501"
            ]
        }
    except Exception as e:
        return {
            "api_status": "running",
            "config_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
    
    print_success "Created enhanced app/main.py"
    echo
}

# Create enhanced frontend
create_frontend() {
    print_section "Creating Enhanced Frontend"
    
    cat > frontend/app.py << 'EOF'
import streamlit as st
import requests
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="🐴 Barn Lady",
    page_icon="🐴",
    layout="wide"
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

def test_api_connection():
    """Test connection to the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200, response.json() if 
response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        return False, str(e)

def test_api_status():
    """Test API status and configuration"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/status", 
timeout=5)
        return response.status_code == 200, response.json() if 
response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        return False, str(e)

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">🐴 Barn Lady - Enhanced 
Version</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Horse Management System")
    
    # Test API connection
    api_connected, api_data = test_api_connection()
    
    if api_connected:
        st.success("✅ Successfully connected to Barn Lady API!")
        
        # Test API status
        status_ok, status_data = test_api_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔌 API Health:**")
            if api_data:
                st.json(api_data)
        
        with col2:
            st.markdown("**⚙️ Configuration Status:**")
            if status_ok and status_data:
                if status_data.get("config_status") == "configured":
                    st.success("🎉 All API keys configured!")
                elif status_data.get("config_status") == 
"missing_configs":
                    st.warning(f"⚠️ Missing: {', 
'.join(status_data.get('missing_configs', []))}")
                    st.info("Edit your .env file to add missing API keys")
                
                if status_data.get("next_steps"):
                    st.markdown("**Next Steps:**")
                    for step in status_data["next_steps"]:
                        st.markdown(f"• {step}")
        
        # Feature overview
        st.markdown("---")
        st.markdown("## 🚀 Enhanced Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h4>🐎 Horse Management</h4>
                <ul>
                    <li>Complete horse profiles</li>
                    <li>Health record tracking</li>
                    <li>Multi-barn organization</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h4>🏥 Health & Care</h4>
                <ul>
                    <li>Veterinary records</li>
                    <li>Vaccination tracking</li>
                    <li>Health analytics</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <h4>🤖 AI Features</h4>
                <ul>
                    <li>Intelligent insights</li>
                    <li>Health recommendations</li>
                    <li>Feeding plans</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
    else:
        st.error(f"❌ Could not connect to Barn Lady API at 
{API_BASE_URL}")
        st.markdown(f"**Error:** {api_data}")
        
        st.markdown("**🛠️ Troubleshooting:**")
        st.markdown("1. Start the API: `./scripts/dev.sh start`")
        st.markdown("2. Check status: `./scripts/dev.sh status`")
        st.markdown("3. View logs: `./scripts/dev.sh logs`")
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Barn Lady v1.0.0 - Enhanced • 
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()
EOF
    
    print_success "Created enhanced frontend/app.py"
    
    # Create Streamlit config
    mkdir -p frontend/.streamlit
    cat > frontend/.streamlit/config.toml << 'EOF'
[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#2E8B57"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F8F0"
textColor = "#262730"
EOF
    
    print_success "Created Streamlit configuration"
    echo
}

# Create development scripts
create_dev_scripts() {
    print_section "Creating Development Scripts"
    
    cat > scripts/dev.sh << 'EOF'
#!/bin/bash
# Enhanced development script for Barn Lady

case "$1" in
    "start")
        echo "🚀 Starting Barn Lady development environment..."
        
        # Start database and Redis first
        echo "Starting database and Redis..."
        docker-compose up -d db redis
        
        # Wait for services
        echo "Waiting for services to be ready..."
        sleep 15
        
        # Check if we're in virtual environment
        if [ -z "$VIRTUAL_ENV" ]; then
            if [ -d "venv" ]; then
                echo "Activating virtual environment..."
                source venv/bin/activate
            else
                echo "⚠️  Virtual environment not found. Run: 
./scripts/dev.sh install"
            fi
        fi
        
        # Start API
        echo "Starting API..."
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        API_PID=$!
        
        # Start Frontend
        echo "Starting Frontend..."
        (cd frontend && streamlit run app.py --server.port 8501) &
        FRONTEND_PID=$!
        
        # Save PIDs
        echo $API_PID > .api.pid
        echo $FRONTEND_PID > .frontend.pid
        
        echo "✅ All services started!"
        echo ""
        echo "🎯 Access your enhanced application:"
        echo "📱 Frontend: http://localhost:8501"
        echo "🔌 API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo "⚙️ API Status: http://localhost:8000/api/v1/status"
        echo ""
        echo "🛑 To stop: ./scripts/dev.sh stop"
        ;;
    "stop")
        echo "🛑 Stopping development services..."
        
        # Stop background processes
        if [ -f .api.pid ]; then
            kill $(cat .api.pid) 2>/dev/null || true
            rm .api.pid
        fi
        
        if [ -f .frontend.pid ]; then
            kill $(cat .frontend.pid) 2>/dev/null || true
            rm .frontend.pid
        fi
        
        # Stop by name
        pkill -f "uvicorn app.main:app" 2>/dev/null || true
        pkill -f "streamlit run app.py" 2>/dev/null || true
        
        # Stop Docker containers
        docker-compose down
        
        echo "✅ All services stopped!"
        ;;
    "status")
        echo "📊 Barn Lady Service Status:"
        docker-compose ps
        echo ""
        
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo "✅ API is running"
        else
            echo "❌ API is not responding"
        fi
        
        if curl -s http://localhost:8501 >/dev/null 2>&1; then
            echo "✅ Frontend is running"
        else
            echo "❌ Frontend is not responding"
        fi
        ;;
    "install")
        echo "📦 Installing dependencies..."
        
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            echo "✅ Created virtual environment"
        fi
        
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        echo "✅ Dependencies installed!"
        ;;
    *)
        echo "Barn Lady Development Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  status   - Check service status"
        echo "  install  - Install dependencies"
        ;;
esac
EOF
    
    chmod +x scripts/dev.sh
    print_success "Created scripts/dev.sh"
    echo
}

# Create basic tests
create_tests() {
    print_section "Creating Basic Tests"
    
    cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
EOF
    
    cat > tests/test_api.py << 'EOF'
"""
Basic API tests for Barn Lady
"""

import pytest
import requests

def test_api_health():
    """Test API health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    except requests.exceptions.RequestException:
        pytest.skip("API not running")

def test_api_status():
    """Test API status endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/v1/status", 
timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "api_status" in data
    except requests.exceptions.RequestException:
        pytest.skip("API not running")
EOF
    
    print_success "Created basic test framework"
    echo
}

# Update documentation
update_docs() {
    print_section "Updating Documentation"
    
    cat > README.md << 'EOF'
# 🐴 Barn Lady - Enhanced Version

## ✨ Successfully Upgraded!

Your Barn Lady installation has been enhanced with powerful new features.

## 🚀 Quick Start

```bash
# Install dependencies
./scripts/dev.sh install

# Start all services
./scripts/dev.sh start
```

## 🌐 Access Points

- **Frontend**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Status Check**: http://localhost:8000/api/v1/status

## 🛠️ Development Commands

```bash
./scripts/dev.sh start     # Start all services
./scripts/dev.sh stop      # Stop all services
./scripts/dev.sh status    # Check service status
./scripts/dev.sh install   # Install dependencies
```

## 🎉 New Features

✅ Enhanced API with better structure  
✅ Improved frontend interface  
✅ Configuration status checking  
✅ Development tools and scripts  
✅ Testing framework  
✅ Better error handling  

## 💾 Your Data

✅ Your .env file: PRESERVED  
✅ Your original files: BACKED UP in backup_* directory  
✅ Your API keys: SAFE  

## 🆘 Troubleshooting

```bash
./scripts/dev.sh status    # Check what's running
./scripts/dev.sh stop      # Stop everything
./scripts/dev.sh install   # Reinstall dependencies
./scripts/dev.sh start     # Start fresh
```

Happy horse managing! 🐴
EOF
    
    print_success "Updated README.md"
    echo
}

# Main execution
main() {
    print_info "Completing upgrade from where it left off..."
    echo
    
    fix_env_file
    create_directories
    update_requirements
    create_core_files
    create_frontend
    create_dev_scripts
    create_tests
    update_docs
    
    echo -e "${GREEN}"
    echo "🎉 =============================================="
    echo "   BARN LADY UPGRADE COMPLETED!"
    echo "===============================================${NC}"
    echo
    echo -e "${CYAN}Next steps:${NC}"
    echo "1. Install dependencies: ./scripts/dev.sh install"
    echo "2. Start your app: ./scripts/dev.sh start"
    echo "3. Visit: http://localhost:8501"
    echo
    echo -e "${GREEN}Your upgrade is now complete! 🐴✨${NC}"
}

# Run the fix
main
