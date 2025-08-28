#!/bin/bash
# fix_dependencies.sh
# Fix the dependency installation issues

echo "🔧 Fixing Barn Lady dependencies..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip first
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Create corrected requirements.txt
echo "📝 Creating corrected requirements.txt..."
cat > requirements.txt << 'REQUIREMENTS_EOF'
# Core FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# PropelAuth integration (using latest available version)
propelauth-fastapi==4.2.8
propelauth-py==4.2.8

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

# Web requests
requests==2.31.0

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Streamlit frontend
streamlit==1.28.1
pandas==2.1.3
plotly==5.17.0
REQUIREMENTS_EOF

echo "✅ Updated requirements.txt with correct versions"

# Also update frontend requirements
echo "📝 Creating frontend/requirements.txt..."
cat > frontend/requirements.txt << 'FRONTEND_REQUIREMENTS_EOF'
# Streamlit Frontend Dependencies
streamlit==1.28.1
requests==2.31.0
pandas==2.1.3
plotly==5.17.0

# Date/time handling
python-dateutil==2.8.2

# For handling API responses
pydantic==2.5.0
FRONTEND_REQUIREMENTS_EOF

echo "✅ Updated frontend/requirements.txt"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Dependencies installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Start your app: ./scripts/dev.sh start"
    echo "2. Visit frontend: http://localhost:8501"
    echo "3. Visit API: http://localhost:8000"
    echo ""
else
    echo "❌ Some dependencies failed to install"
    echo "You can try installing them individually:"
    echo "pip install fastapi uvicorn streamlit requests"
fi
