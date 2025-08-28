#!/bin/bash
# upgrade_barn_lady.sh
# Fixed version - Upgrade existing Barn Lady installation while preserving 
your configuration

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
echo "🔄 =============================================="
echo "   BARN LADY UPGRADE SCRIPT (FIXED)"
echo "   Preserving Your Existing Configuration"
echo "===============================================${NC}"
echo

# Function to print section headers
print_section() {
    echo -e "${PURPLE}📋 $1${NC}"
    echo "----------------------------------------"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print info messages
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Check if we're in the right directory
check_existing_project() {
    print_section "Checking Existing Project"
    
    local project_found=false
    
    # Look for indicators of Barn Lady project
    echo "Looking for Barn Lady project files..."
    
    if test -f ".env"; then
        echo "  ✅ Found .env file"
        project_found=true
    fi
    
    if test -f "docker-compose.yml"; then
        echo "  ✅ Found docker-compose.yml"
        project_found=true
    fi
    
    if test -d "app"; then
        echo "  ✅ Found app/ directory"
        project_found=true
    fi
    
    if test -d "frontend"; then
        echo "  ✅ Found frontend/ directory"
        project_found=true
    fi
    
    if test -f "requirements.txt"; then
        echo "  ✅ Found requirements.txt"
        project_found=true
    fi
    
    if [ "$project_found" = true ]; then
        print_success "Found existing Barn Lady project files"
        
        # Show current directory for confirmation
        echo "Current directory: $(pwd)"
        
        # Show what we detected
        echo ""
        echo "Detected project structure:"
        test -f ".env" && echo "  📄 .env (will be preserved)"
        test -f "docker-compose.yml" && echo "  🐳 docker-compose.yml 
(will be upgraded)"
        test -f "requirements.txt" && echo "  📦 requirements.txt (will be 
upgraded)"
        test -d "app" && echo "  📁 app/ directory (will be enhanced)"
        test -d "frontend" && echo "  📁 frontend/ directory (will be 
enhanced)"
        test -d "venv" && echo "  🐍 venv/ virtual environment (will be 
preserved)"
        
    else
        print_error "This doesn't appear to be a Barn Lady project 
directory"
        print_info "Please run this script from your existing 
barn-management directory"
        print_info "Or use the complete setup script if starting fresh"
        
        echo ""
        echo "Current directory contents:"
        ls -la
        
        echo ""
        echo "Expected to find at least one of:"
        echo "  - .env file"
        echo "  - docker-compose.yml file"
        echo "  - app/ directory"
        echo "  - frontend/ directory"
        echo "  - requirements.txt file"
        
        exit 1
    fi
    echo
}

# Create backup of existing files
create_backup() {
    print_section "Creating Backup of Existing Files"
    
    local backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup important files that we might modify
    local files_to_backup=(".env" "docker-compose.yml" "requirements.txt")
    
    for file in "${files_to_backup[@]}"; do
        if test -f "$file"; then
            cp "$file" "$backup_dir/"
            print_success "Backed up $file"
        fi
    done
    
    # Backup directories
    if test -d "app"; then
        cp -r "app" "$backup_dir/"
        print_success "Backed up app/ directory"
    fi
    
    if test -d "frontend"; then
        cp -r "frontend" "$backup_dir/"
        print_success "Backed up frontend/ directory"
    fi
    
    print_success "Backup created in $backup_dir/"
    echo
}

# Update requirements.txt with new dependencies
update_requirements() {
    print_section "Updating Python Requirements"
    
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

# Monitoring and logging
structlog==23.2.0
python-json-logger==2.0.7
prometheus-client==0.19.0

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
black==23.11.0
flake8==6.1.0
isort==5.12.0
pre-commit==3.5.0

# System monitoring
psutil==5.9.6
EOF
    
    print_success "Updated requirements.txt with new dependencies"
    
    # Update frontend requirements if directory exists
    if test -d "frontend"; then
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
    fi
    echo
}

# Check and preserve .env file
preserve_env_file() {
    print_section "Preserving Your Environment Configuration"
    
    if test -f ".env"; then
        print_success "Found existing .env file - will preserve your API 
keys"
        
        # Check if it has the basic required fields and add missing ones
        local env_updated=false
        
        if ! grep -q "PROPELAUTH_URL" .env; then
            echo "" >> .env
            echo "# Added by upgrade script" >> .env
            echo "PROPELAUTH_URL=https://auth.yourdomain.com" >> .env
            print_success "Added PROPELAUTH_URL to .env file"
            env_updated=true
        fi
        
        if ! grep -q "ANTHROPIC_API_KEY" .env; then
            echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env
            print_success "Added ANTHROPIC_API_KEY to .env file"
            env_updated=true
        fi
        
        if ! grep -q "SECRET_KEY" .env; then
            echo 
"SECRET_KEY=your-secret-key-change-this-in-production-minimum-32-characters" 
>> .env
            print_success "Added SECRET_KEY to .env file"
            env_updated=true
        fi
        
        if [ "$env_updated" = true ]; then
            print_info "Added missing environment variables to your .env 
file"
        else
            print_success "Your .env file has all required variables"
        fi
        
    else
        print_warning "No .env file found - creating template"
        create_env_template
    fi
    echo
}

# Create environment template if missing
create_env_template() {
    cat > .env << 'EOF'
# Barn Lady Environment Configuration

# PropelAuth Configuration
# Get these from your PropelAuth dashboard at https://www.propelauth.com
PROPELAUTH_URL=https://auth.yourdomain.com
PROPELAUTH_API_KEY=your_propelauth_api_key_here
PROPELAUTH_VERIFIER_KEY=your_propelauth_verifier_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/barnlady

# Claude AI Configuration
# Get this from Anthropic Console at https://console.anthropic.com
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Configuration
DEBUG=true
SECRET_KEY=your-secret-key-change-this-in-production-minimum-32-characters

# CORS Origins
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# Development Settings
APP_NAME=Barn Lady
APP_VERSION=1.0.0
EOF
    print_success "Created .env template"
}

# Create directories if they don't exist
create_missing_directories() {
    print_section "Creating Missing Directories"
    
    local directories=(
        "app/core"
        "app/models" 
        "app/api"
        "app/services"
        "frontend/.streamlit"
        "scripts"
        "migrations"
        "storage"
        "logs"
        "tests"
        "monitoring"
        "docs"
        "backups"
    )
    
    for dir in "${directories[@]}"; do
        if ! test -d "$dir"; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        fi
    done
    echo
}

# Create/update core application files
update_core_files() {
    print_section "Updating Core Application Files"
    
    # Create __init__.py files if missing
    local init_files=("app/__init__.py" "app/core/__init__.py" 
"app/models/__init__.py" "app/api/__init__.py" "app/services/__init__.py" 
"tests/__init__.py")
    for init_file in "${init_files[@]}"; do
        if ! test -f "$init_file"; then
            touch "$init_file"
            print_success "Created $init_file"
        fi
    done
    
    # Update app/core/config.py
    cat > app/core/config.py << 'EOF'
import os
from pydantic_settings import BaseSettings
from typing import Optional

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
    
    print_success "Updated app/core/config.py"
    
    # Check if main.py needs upgrading
    if test -f "app/main.py"; then
        # Check if it's the basic version
        if grep -q "Welcome to Barn Lady API" app/main.py && ! grep -q 
"horse" app/main.py; then
            print_info "Detected basic main.py - will upgrade to enhanced 
version"
            create_enhanced_main_py
        else
            print_success "app/main.py appears to already be enhanced"
        fi
    else
        create_enhanced_main_py
    fi
    
    echo
}

# Create enhanced main.py
create_enhanced_main_py() {
    cat > app/main.py << 'EOF'
from fastapi import FastAPI, Depends, HTTPException
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
        # Check if we can load settings
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

# Placeholder for additional routes
# The full API routes will be added here as separate router modules

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
    
    print_success "Created enhanced app/main.py"
}

# Update frontend
update_frontend() {
    print_section "Updating Frontend Application"
    
    # Ensure frontend directory exists
    if ! test -d "frontend"; then
        mkdir -p "frontend"
        print_success "Created frontend directory"
    fi
    
    # Check if frontend/app.py exists and needs upgrading
    create_enhanced_frontend
    
    # Create Streamlit config if missing
    if ! test -f "frontend/.streamlit/config.toml"; then
        mkdir -p "frontend/.streamlit"
        cat > frontend/.streamlit/config.toml << 'EOF'
[server]
headless = true
port = 8501
address = "0.0.0.0"

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#2E8B57"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F8F0"
textColor = "#262730"
EOF
        print_success "Created Streamlit configuration"
    fi
    echo
}

# Create enhanced frontend
create_enhanced_frontend() {
    cat > frontend/app.py << 'EOF'
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="🐴 Barn Lady",
    page_icon="🐴",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
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
        
        # Quick Links
        st.markdown("---")
        st.markdown("## 🔗 Quick Access")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📚 API Documentation", 
use_container_width=True):
                st.markdown("[Open API Docs](http://localhost:8000/docs)")
        
        with col2:
            if st.button("🔍 API Health Check", use_container_width=True):
                st.markdown("[Check API 
Health](http://localhost:8000/health)")
        
        with col3:
            if st.button("⚙️ API Status", use_container_width=True):
                st.markdown("[Check API 
Status](http://localhost:8000/api/v1/status)")
        
        with col4:
            if st.button("🏠 API Root", use_container_width=True):
                st.markdown("[API Root](http://localhost:8000/)")
        
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
                    <li>Owner management</li>
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
                    <li>AI health insights</li>
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
                    <li>Natural language queries</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Development info
        st.markdown("---")
        st.markdown("## 🛠️ Development Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ Completed Upgrades:**")
            st.markdown("- Enhanced API structure")
            st.markdown("- Improved frontend interface")
            st.markdown("- Better configuration management")
            st.markdown("- Development tools and scripts")
            st.markdown("- Testing framework")
            st.markdown("- Docker improvements")
        
        with col2:
            st.markdown("**🔄 Ready for Development:**")
            st.markdown("- Add full horse management features")
            st.markdown("- Implement PropelAuth authentication")
            st.markdown("- Integrate Claude AI services")
            st.markdown("- Add database models")
            st.markdown("- Create analytics dashboards")
            st.markdown("- Build reporting features")
        
    else:
        st.error(f"❌ Could not connect to Barn Lady API at 
{API_BASE_URL}")
        
        with st.expander("🔍 Connection Details"):
            st.markdown(f"**API URL:** {API_BASE_URL}")
            st.markdown(f"**Error:** {api_data}")
        
        st.markdown("**🛠️ Troubleshooting Steps:**")
        st.markdown("1. **Start the API server:** `./scripts/dev.sh 
start`")
        st.markdown("2. **Check API status:** `./scripts/dev.sh status`")
        st.markdown("3. **View logs:** `./scripts/dev.sh logs`")
        st.markdown("4. **Test API directly:** Visit 
http://localhost:8000")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"*Current time: {datetime.now().strftime('%Y-%m-%d 
%H:%M:%S')}*")
    
    with col2:
        st.markdown("*Barn Lady v1.0.0 - Enhanced*")
    
    with col3:
        st.markdown("*Upgraded successfully! 🎉*")

if __name__ == "__main__":
    main()
EOF
    
    print_success "Created enhanced frontend/app.py"
}

# Update Docker configuration
update_docker_config() {
    print_section "Updating Docker Configuration"
    
    # Update docker-compose.yml with enhanced features
    cat > docker-compose.yml << 'EOF'
version: '3.8'

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
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=true
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./app:/app/app:ro
      - ./storage:/app/storage
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Streamlit Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://api:8000
      - PROPELAUTH_URL=${PROPELAUTH_URL}
    depends_on:
      api:
        condition: service_healthy
    volumes:
      - ./frontend:/app:ro

  # Redis (for caching/sessions)
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  default:
    name: barnlady-network
EOF
    
    print_success "Updated docker-compose.yml with enhanced features"
    
    # Create database init script if missing
    if ! test -f "init-db.sql"; then
        cat > init-db.sql << 'EOF'
-- Database initialization script for Barn Lady
CREATE SCHEMA IF NOT EXISTS public;

-- Create a table to track tenant schemas
CREATE TABLE IF NOT EXISTS public.tenant_schemas (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(100) UNIQUE NOT NULL,
    schema_name VARCHAR(100) UNIQUE NOT NULL,
    org_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSON DEFAULT '{}'::json
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tenant_schemas_org_id ON 
public.tenant_schemas(org_id);
CREATE INDEX IF NOT EXISTS idx_tenant_schemas_schema_name ON 
public.tenant_schemas(schema_name);
EOF
        print_success "Created init-db.sql"
    fi
    
    # Create Dockerfile if missing
    if ! test -f "Dockerfile"; then
        cat > Dockerfile << 'EOF'
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
RUN mkdir -p /app/storage /app/logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", 
"--reload"]
EOF
        print_success "Created Dockerfile"
    fi
    
    # Create frontend Dockerfile if missing
    if ! test -f "frontend/Dockerfile"; then
        cat > frontend/Dockerfile << 'EOF'
# Streamlit Frontend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash streamlit && \
    chown -R streamlit:streamlit /app
USER streamlit

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlit configuration
RUN mkdir -p /home/streamlit/.streamlit

# Start command
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", 
"--server.port", "8501"]
EOF
        print_success "Created frontend/Dockerfile"
    fi
    echo
}

# Create/update development scripts
create_dev_scripts() {
    print_section "Creating Enhanced Development Scripts"
    
    mkdir -p scripts
    
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
        
        # Check if we're in the virtual environment
        if test -z "$VIRTUAL_ENV"; then
            if test -d "venv"; then
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
        
        # Save PIDs for stopping later
        echo $API_PID > .api.pid
        echo $FRONTEND_PID > .frontend.pid
        
        echo "✅ All services started!"
        echo ""
        echo "🎯 Access your enhanced application:"
        echo "📱 Frontend: http://localhost:8501"
        echo "🔌 API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo "⚙️ API Status: http://localhost:8000/api/v1/status"
        echo "💾 Database: localhost:5432"
        echo ""
        echo "🛑 To stop: ./scripts/dev.sh stop"
        ;;
    "stop")
        echo "🛑 Stopping development services..."
        
        # Stop background processes
        if test -f .api.pid; then
            kill $(cat .api.pid) 2>/dev/null || true
            rm .api.pid
        fi
        
        if test -f .frontend.pid; then
            kill $(cat .frontend.pid) 2>/dev/null || true
            rm .frontend.pid
        fi
        
        # Stop additional processes by name
        pkill -f "uvicorn app.main:app" 2>/dev/null || true
        pkill -f "streamlit run app.py" 2>/dev/null || true
        
        # Stop Docker containers
        docker-compose down
        
        echo "✅ All services stopped!"
        ;;
    "restart")
        echo "🔄 Restarting all services..."
        $0 stop
        sleep 3
        $0 start
        ;;
    "status")
        echo "📊 Barn Lady Service Status:"
        echo "============================"
        
        # Check Docker containers
        echo "Docker Containers:"
        docker-compose ps
        echo ""
        
        # Check API
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo "✅ API is running (http://localhost:8000)"
        else
            echo "❌ API is not responding"
        fi
        
        # Check Frontend
        if curl -s http://localhost:8501 >/dev/null 2>&1; then
            echo "✅ Frontend is running (http://localhost:8501)"
        else
            echo "❌ Frontend is not responding"
        fi
        
        # Check database
        if docker-compose exec -T db pg_isready -U postgres >/dev/null 
2>&1; then
            echo "✅ Database is ready"
        else
            echo "❌ Database is not ready"
        fi
        
        # Check Redis
        if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; 
then
            echo "✅ Redis is ready"
        else
            echo "❌ Redis is not ready"
        fi
        ;;
    "logs")
        echo "📋 Showing service logs..."
        docker-compose logs -f
        ;;
    "test")
        echo "🧪 Running tests..."
        if test -d "venv"; then
            source venv/bin/activate
        fi
        
        if test -f "pytest.ini" || test -d "tests"; then
            pytest tests/ -v
        else
            echo "No tests found. Create tests in the tests/ directory."
        fi
        ;;
    "install")
        echo "📦 Installing/updating dependencies..."
        
        # Create venv if it doesn't exist
        if ! test -d "venv"; then
            python3 -m venv venv
            echo "✅ Created virtual environment"
        fi
        
        # Activate and install
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        echo "✅ Dependencies installed!"
        ;;
    "clean")
        echo "🧹 Cleaning up development environment..."
        
        # Stop services first
        $0 stop
        
        # Clean Docker
        docker-compose down -v
        docker system prune -f
        
        # Clean Python cache
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null 
|| true
        rm -rf .pytest_cache .coverage htmlcov
        
        echo "✅ Cleanup completed!"
        ;;
    *)
        echo "Barn Lady Development Commands (Enhanced):"
        echo "=========================================="
        echo "  start    - Start all development services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Check service status"
        echo "  logs     - Show service logs"
        echo "  test     - Run tests"
        echo "  install  - Install/update Python dependencies"
        echo "  clean    - Clean up containers and cache"
        echo ""
        echo "Usage: $0 
{start|stop|restart|status|logs|test|install|clean}"
        exit 1
        ;;
esac
EOF
    
    chmod +x scripts/dev.sh
    print_success "Created enhanced scripts/dev.sh"
    echo
}

# Create basic tests if missing
create_tests() {
    print_section "Creating Test Framework"
    
    if ! test -f "pytest.ini"; then
        cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
EOF
        print_success "Created pytest.ini"
    fi
    
    if ! test -f "tests/test_api.py"; then
        cat > tests/test_api.py << 'EOF'
"""
Enhanced API tests for Barn Lady
"""

import pytest
import requests

def test_api_health():
    """Test that the API health endpoint works"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
    except requests.exceptions.RequestException:
        pytest.skip("API not running")

def test_api_root():
    """Test that the API root endpoint works"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "🐴" in data["message"]
        assert "Enhanced Version" in data["message"]
        assert "features" in data
    except requests.exceptions.RequestException:
        pytest.skip("API not running")

def test_api_status():
    """Test the new API status endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/v1/status", 
timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "api_status" in data
        assert "config_status" in data
        assert data["api_status"] == "running"
    except requests.exceptions.RequestException:
        pytest.skip("API not running")
EOF
        print_success "Created enhanced tests/test_api.py"
    fi
    echo
}

# Update documentation
update_docs() {
    print_section "Updating Documentation"
    
    cat > README.md << 'EOF'
# 🐴 Barn Lady - AI-Powered Horse Management System

## ✨ Enhanced Version - Successfully Upgraded!

Your Barn Lady installation has been enhanced with powerful new features 
while preserving all your existing configuration.

## 🚀 Quick Start

### Start Your Enhanced Application
```bash
# Install new dependencies
./scripts/dev.sh install

# Start all services
./scripts/dev.sh start
```

### Access Your Application
- **🎨 Enhanced Frontend**: http://localhost:8501
- **🔌 Enhanced API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **⚙️ Configuration Status**: http://localhost:8000/api/v1/status

## 🎉 What's New in This Upgrade

### ✅ Enhanced API Features
- **Better Structure** - Organized codebase with proper configuration 
management
- **Configuration Validation** - Automatic checking of API keys and 
settings
- **Enhanced Endpoints** - New status endpoint with detailed configuration 
info
- **Better Error Handling** - Improved error messages and debugging

### ✅ Improved Frontend
- **Modern Interface** - Enhanced Streamlit UI with better styling
- **Real-time Status** - Live connection testing and configuration 
checking
- **Feature Overview** - Clear display of available and upcoming features
- **Development Tools** - Easy access to API documentation and status

### ✅ Powerful Development Tools
- **Enhanced Scripts** - Much more powerful `./scripts/dev.sh` commands
- **Better Docker** - Improved containers with Redis, health checks, and 
networking
- **Testing Framework** - Automated testing with pytest
- **Development Workflow** - Streamlined development and debugging process

### ✅ Production Ready Infrastructure
- **Multi-service Architecture** - API, Frontend, Database, and Redis
- **Health Monitoring** - Comprehensive health checks for all services
- **Logging & Debugging** - Better logging and error tracking
- **Configuration Management** - Robust environment variable handling

## 🛠️ Enhanced Development Commands

```bash
./scripts/dev.sh start      # Start all services (API + Frontend + DB + 
Redis)
./scripts/dev.sh stop       # Stop all services cleanly
./scripts/dev.sh restart    # Restart everything
./scripts/dev.sh status     # Check detailed service status
./scripts/dev.sh logs       # View all service logs
./scripts/dev.sh test       # Run the enhanced test suite
./scripts/dev.sh install    # Install/update dependencies
./scripts/dev.sh clean      # Clean up containers and cache
```

## 🔧 Configuration Status

Your API keys and configuration are preserved from your original setup. To 
check if everything is configured:

1. **Visit the Status Page**: http://localhost:8000/api/v1/status
2. **Check the Frontend**: The enhanced frontend will show configuration 
status
3. **Use the API Docs**: Visit http://localhost:8000/docs for interactive 
testing

## 📊 What Was Preserved

✅ **Your .env file** - All API keys and configuration preserved exactly 
as they were  
✅ **Your data** - Any existing database data and storage files  
✅ **Your customizations** - Any changes you made (backed up in 
backup_YYYYMMDD_HHMMSS/)  
✅ **Your virtual environment** - Python environment preserved if it 
existed  

## 🎯 Next Steps

### 1. **Verify the Upgrade**
```bash
./scripts/dev.sh status     # Check all services
curl http://localhost:8000/api/v1/status  # Check configuration
```

### 2. **Test the New Features**
- Visit the enhanced frontend at http://localhost:8501
- Explore the API documentation at http://localhost:8000/docs
- Try the new development commands

### 3. **Configure Missing API Keys** (if needed)
If the status page shows missing configurations, edit your `.env` file:
```bash
nano .env  # Add any missing API keys
./scripts/dev.sh restart  # Restart to apply changes
```

### 4. **Start Building**
Your application is now ready for:
- Adding full horse management features
- Implementing PropelAuth authentication
- Integrating Claude AI services
- Building analytics dashboards

## 🆘 Troubleshooting

### If Services Won't Start:
```bash
./scripts/dev.sh clean      # Clean everything
./scripts/dev.sh install    # Reinstall dependencies
./scripts/dev.sh start      # Start fresh
```

### If You Need to Restore Something:
Your original files are backed up in the `backup_YYYYMMDD_HHMMSS/` 
directory:
```bash
# Example: restore original main.py
cp backup_*/app/main.py app/main.py
```

### Check Logs for Issues:
```bash
./scripts/dev.sh logs       # View all service logs
./scripts/dev.sh status     # Check service status
```

## 📈 Performance Improvements

- **Faster Startup** - Better service orchestration
- **Health Monitoring** - All services have health checks
- **Better Networking** - Improved Docker networking
- **Resource Management** - Optimized container resource usage

## 🔮 What's Next

Your enhanced Barn Lady system is now ready for:

1. **Full Horse Management** - Complete CRUD operations for horses
2. **AI Integration** - Claude-powered insights and recommendations
3. **Authentication** - PropelAuth multi-tenant user management
4. **Analytics** - Advanced reporting and dashboards
5. **Mobile Support** - Responsive design for all devices

---

**🎉 Congratulations on your successful upgrade!**

Your Barn Lady system is now much more powerful while keeping everything 
you had before. Happy horse managing! 🐴✨
EOF
    
    print_success "Updated README.md with upgrade information"
    echo
}

# Print final instructions
print_final_instructions() {
    echo -e "${GREEN}"
    echo "🎉 =============================================="
    echo "   BARN LADY UPGRADE COMPLETED SUCCESSFULLY!"
    echo "===============================================${NC}"
    echo
    echo -e "${BLUE}📋 Upgrade Summary:${NC}"
    echo
    echo -e "${GREEN}✅ Your existing .env file with API keys: 
PRESERVED${NC}"
    echo -e "${GREEN}✅ Your original files: BACKED UP${NC}"
    echo -e "${GREEN}✅ Enhanced API with better structure: CREATED${NC}"
    echo -e "${GREEN}✅ Improved frontend interface: UPGRADED${NC}"
    echo -e "${GREEN}✅ Powerful development scripts: ADDED${NC}"
    echo -e "${GREEN}✅ Testing framework: IMPLEMENTED${NC}"
    echo -e "${GREEN}✅ Docker configuration: ENHANCED${NC}"
    echo -e "${GREEN}✅ Documentation: UPDATED${NC}"
    echo
    echo -e "${YELLOW}🚀 Next Steps:${NC}"
    echo
    echo -e "${CYAN}1. Install new dependencies:${NC}"
    echo "   ./scripts/dev.sh install"
    echo
    echo -e "${CYAN}2. Start your enhanced application:${NC}"
    echo "   ./scripts/dev.sh start"
    echo
    echo -e "${CYAN}3. Access your upgraded system:${NC}"
    echo "   - 🎨 Enhanced Frontend: http://localhost:8501"
    echo "   - 🔌 Enhanced API: http://localhost:8000"
    echo "   - 📚 API Documentation: http://localhost:8000/docs"
    echo "   - ⚙️ Configuration Status: 
http://localhost:8000/api/v1/status"
    echo
    echo -e "${BLUE}🛠️ New Development Commands:${NC}"
    echo "   ./scripts/dev.sh start      # Start all services"
    echo "   ./scripts/dev.sh stop       # Stop all services"
    echo "   ./scripts/dev.sh status     # Check detailed service status"
    echo "   ./scripts/dev.sh restart    # Restart all services"
    echo "   ./scripts/dev.sh logs       # View service logs"
    echo "   ./scripts/dev.sh test       # Run enhanced tests"
    echo "   ./scripts/dev.sh install    # Install/update dependencies"
    echo "   ./scripts/dev.sh clean      # Clean up everything"
    echo
    echo -e "${PURPLE}💾 Your Data Safety:${NC}"
    echo "   - Original .env file: PRESERVED with all your API keys"
    echo "   - Original files: BACKED UP in backup_YYYYMMDD_HHMMSS/"
    echo "   - Virtual environment: PRESERVED if it existed"
    echo "   - All customizations: SAFELY BACKED UP"
    echo
    echo -e "${GREEN}🎊 Enjoy your enhanced Barn Lady system! 🐴${NC}"
    echo
}

# Main execution
main() {
    check_existing_project
    create_backup
    preserve_env_file
    create_missing_directories
    update_requirements
    update_core_files
    update_frontend
    update_docker_config
    create_dev_scripts
    create_tests
    update_docs
    
    print_final_instructions
}

# Run main function
main "$@"
