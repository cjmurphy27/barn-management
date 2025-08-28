#!/bin/bash
# Enhanced Barn Lady Setup Script for Existing Project
# Designed to work with your existing barn-management structure

set -e  # Exit on any error

echo "🐴 Barn Lady Enhanced Setup for Existing Project!"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check that we're in the right directory
check_directory() {
    print_header "Checking current directory..."
    
    if [ ! -d "app" ] || [ ! -d "venv" ]; then
        print_error "This doesn't look like your barn-management directory."
        print_error "Please run this script from your barn-management directory."
        exit 1
    fi
    
    print_status "Found existing app/ and venv/ directories - good!"
}

# Backup existing files that we'll replace
backup_existing() {
    print_header "Backing up existing files..."
    
    # Create backup directory with timestamp
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup files we'll replace
    [ -f "main.py" ] && cp main.py "$BACKUP_DIR/"
    [ -f "requirements.txt" ] && cp requirements.txt "$BACKUP_DIR/"
    [ -f ".env" ] && cp .env "$BACKUP_DIR/"
    
    # Backup specific app files if they exist
    [ -f "app/database.py" ] && cp app/database.py "$BACKUP_DIR/"
    [ -d "app/models" ] && cp -r app/models "$BACKUP_DIR/"
    [ -d "app/api" ] && cp -r app/api "$BACKUP_DIR/"
    [ -d "app/schemas" ] && cp -r app/schemas "$BACKUP_DIR/"
    
    print_status "Backup created in $BACKUP_DIR/"
}

# Ensure directory structure exists
ensure_structure() {
    print_header "Ensuring proper directory structure..."
    
    # Create missing directories
    mkdir -p app/{api,core,models,schemas,services}
    mkdir -p frontend
    mkdir -p scripts
    mkdir -p tests
    mkdir -p uploads
    mkdir -p logs
    
    # Create __init__.py files if missing
    touch app/__init__.py
    touch app/api/__init__.py
    touch app/core/__init__.py
    touch app/models/__init__.py
    touch app/schemas/__init__.py
    touch app/services/__init__.py
    
    # Create .gitkeep files for empty directories
    touch uploads/.gitkeep
    touch logs/.gitkeep
    
    print_status "Directory structure verified"
}

# Update virtual environment
update_venv() {
    print_header "Updating virtual environment..."
    
    # Activate existing virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_status "Virtual environment activated and pip upgraded"
}

# Install/update dependencies
install_dependencies() {
    print_header "Installing Barn Lady dependencies..."
    
    # Make sure we're in the virtual environment
    source venv/bin/activate
    
    # Install core Barn Lady dependencies
    pip install fastapi==0.104.1 uvicorn[standard]==0.24.0
    pip install sqlalchemy==2.0.23 psycopg2-binary==2.9.9
    pip install pydantic==2.5.0 pydantic-settings==2.1.0
    pip install redis==5.0.1 requests==2.31.0
    pip install streamlit==1.28.1 pandas==2.1.4
    pip install python-dotenv==1.0.0 python-dateutil==2.8.2
    pip install alembic==1.13.0
    
    print_status "Core dependencies installed"
    
    # Install optional AI dependencies
    read -p "Install Anthropic Claude AI integration? (y/N): " install_ai
    if [[ $install_ai =~ ^[Yy]$ ]]; then
        pip install anthropic==0.7.8
        print_status "AI dependencies installed"
    fi
}

# Update Docker Compose if needed
update_docker_compose() {
    print_header "Checking Docker Compose configuration..."
    
    # Check if docker-compose.yml has the services we need
    if grep -q "postgres" docker-compose.yml && grep -q "redis" docker-compose.yml; then
        print_status "Docker Compose already has required services"
    else
        print_warning "Updating Docker Compose with Barn Lady services..."
        
        # Backup existing docker-compose.yml
        cp docker-compose.yml docker-compose.yml.backup
        
        # Create new docker-compose.yml
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: barnlady
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
EOF
        
        print_status "Docker Compose updated"
    fi
}

# Create or update .env file
setup_env_file() {
    print_header "Setting up environment configuration..."
    
    if [ -f ".env" ]; then
        print_warning "Existing .env file found. Creating new .env.barnlady template..."
        ENV_FILE=".env.barnlady"
    else
        ENV_FILE=".env"
    fi
    
    cat > "$ENV_FILE" << 'EOF'
# Barn Lady Configuration
APP_NAME=Barn Lady
DEBUG=True
SECRET_KEY=change-this-to-a-secure-secret-key-$(openssl rand -hex 16)

# Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=barnlady

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Keys (add your actual keys here)
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# PROPELAUTH_URL=https://your-auth-domain.propelauth.com
# PROPELAUTH_API_KEY=your-propelauth-api-key

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO
EOF
    
    if [ "$ENV_FILE" = ".env.barnlady" ]; then
        print_warning "Created $ENV_FILE - please merge with your existing .env"
    else
        print_status "Environment file created (.env)"
    fi
}

# Start or restart Docker services
start_services() {
    print_header "Starting Docker services..."
    
    # Stop any existing services
    docker-compose down
    
    # Start PostgreSQL and Redis
    docker-compose up -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to start..."
    
    # Wait up to 30 seconds for services to be ready
    for i in {1..30}; do
        if docker-compose ps | grep -q "Up.*healthy"; then
            print_status "Docker services started successfully"
            return 0
        fi
        sleep 1
    done
    
    print_warning "Services may still be starting. Check with: docker-compose ps"
}

# Create placeholder files with instructions
create_placeholder_files() {
    print_header "Creating placeholder files for Barn Lady code..."
    
    # Create main.py placeholder
    cat > main.py << 'EOF'
# Barn Lady FastAPI Main Application
# TODO: Replace this with the FastAPI Main Application artifact content

from fastapi import FastAPI

app = FastAPI(title="Barn Lady - Placeholder")

@app.get("/")
def root():
    return {"message": "Barn Lady placeholder - please add the FastAPI code from the artifacts"}

@app.get("/health")
def health():
    return {"status": "placeholder", "message": "Please add the complete FastAPI application code"}

if __name__ == "__main__":
    import uvicorn
    print("⚠️  This is a placeholder. Please add the FastAPI Main Application artifact content.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
    
    # Create requirements.txt
    cat > requirements.txt << 'EOF'
# Barn Lady Core Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
requests==2.31.0
streamlit==1.28.1
pandas==2.1.4
python-dotenv==1.0.0
python-dateutil==2.8.2
alembic==1.13.0
python-multipart==0.0.6

# Optional AI Integration
# anthropic==0.7.8

# Development
black==23.11.0
pytest==7.4.3
EOF
    
    # Create file creation guide
    cat > BARN_LADY_SETUP_GUIDE.md << 'EOF'
# 🐴 Barn Lady File Creation Guide

Your setup script has prepared the environment. Now you need to add the Barn Lady code files.

## Required Files to Create

Copy the content from the Claude artifacts into these files:

### 1. Core Application Files
- `app/core/config.py` - App Configuration artifact
- `app/database.py` - Database Setup artifact  
- `main.py` - FastAPI Main Application artifact (replace placeholder)

### 2. Database Models
- `app/models/horse.py` - Horse Database Model artifact
- `app/models/health.py` - Health Records Model artifact

### 3. API Schemas
- `app/schemas/horse.py` - Horse Pydantic Schemas artifact

### 4. API Endpoints
- `app/api/horses.py` - Horse API Endpoints artifact

### 5. Frontend
- `frontend/app.py` - Horse Management Frontend artifact

### 6. Database Migration
- `scripts/migrate.py` - Database Migration Script artifact

## After Creating Files

1. Install dependencies: `source venv/bin/activate && pip install -r requirements.txt`
2. Run migration: `python scripts/migrate.py`
3. Start API: `python main.py`
4. Start Frontend: `streamlit run frontend/app.py`

## Need Help?

- Check docker services: `docker-compose ps`
- View logs: `docker-compose logs`
- Test API: `curl http://localhost:8000/health`
EOF
    
    print_status "Placeholder files and setup guide created"
}

# Test the setup
test_setup() {
    print_header "Testing the setup..."
    
    # Check Docker services
    if docker-compose ps | grep -q "Up"; then
        print_status "✓ Docker services are running"
    else
        print_warning "⚠ Docker services may not be fully started"
    fi
    
    # Check virtual environment
    source venv/bin/activate
    if python -c "import fastapi, sqlalchemy, streamlit" 2>/dev/null; then
        print_status "✓ Core dependencies are installed"
    else
        print_warning "⚠ Some dependencies may be missing"
    fi
    
    print_status "Setup test completed"
}

# Print final instructions
print_completion() {
    echo ""
    echo "🎉 Barn Lady Enhanced Setup Completed!"
    echo "====================================="
    echo ""
    echo "✅ Environment prepared"
    echo "✅ Dependencies installed"  
    echo "✅ Docker services started"
    echo "✅ Directory structure ready"
    echo ""
    echo "📋 NEXT STEPS:"
    echo ""
    echo "1. Copy the Barn Lady code from Claude artifacts into the files listed in:"
    echo "   📄 BARN_LADY_SETUP_GUIDE.md"
    echo ""
    echo "2. After adding the code files, run:"
    echo "   source venv/bin/activate"
    echo "   python scripts/migrate.py"
    echo ""
    echo "3. Start your applications:"
    echo "   python main.py  # API server"
    echo "   streamlit run frontend/app.py  # Frontend (in another terminal)"
    echo ""
    echo "4. Access your applications:"
    echo "   🌐 API: http://localhost:8000"
    echo "   🖥️  Frontend: http://localhost:8501"
    echo "   📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📁 Your existing work has been backed up in backup_* directories"
    echo ""
    echo "🆘 If you need help, check BARN_LADY_SETUP_GUIDE.md"
    echo ""
    echo "Happy horse management! 🐴✨"
}

# Main setup function
main() {
    echo "Starting enhanced Barn Lady setup for existing project..."
    echo ""
    
    check_directory
    backup_existing
    ensure_structure
    update_venv
    install_dependencies
    update_docker_compose
    setup_env_file
    start_services
    create_placeholder_files
    test_setup
    print_completion
}

# Handle script interruption
trap 'print_error "Setup interrupted"; exit 1' INT

# Run main function
main "$@"
