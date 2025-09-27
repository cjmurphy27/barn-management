# 🐴 Barn Lady - Complete System Architecture & Development Guide

## 📋 Table of Contents
- [System Overview](#system-overview)
- [Technology Stack](#technology-stack)
- [Architecture Components](#architecture-components)
- [Authentication & Session Management](#authentication--session-management)
- [File Storage & Media Handling](#file-storage--media-handling)
- [Database Design](#database-design)
- [API Endpoints](#api-endpoints)
- [Frontend Structure](#frontend-structure)
- [Deployment & DevOps](#deployment--devops)
- [Development Workflow](#development-workflow)
- [Security Considerations](#security-considerations)
- [Performance Optimizations](#performance-optimizations)
- [Troubleshooting Guide](#troubleshooting-guide)

## 🏗️ System Overview

Barn Lady is a comprehensive AI-powered horse management system built with a modern microservices architecture. The system manages horse profiles, health records, events, supplies, and includes AI-powered features for document analysis and decision support.

### Key Features
- **Multi-tenant organization management** with PropelAuth
- **AI-powered document analysis** using Claude
- **Photo management** with FastAPI serving and JWT authentication
- **Real-time calendar and event management**
- **Supply chain and inventory tracking**
- **Message board and communication tools**
- **Comprehensive reporting and analytics**

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework for API development
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database
- **Pydantic** - Data validation and serialization
- **PropelAuth** - Authentication and user management
- **Anthropic Claude** - AI document analysis

### Frontend
- **Streamlit** - Python-based web application framework
- **Custom CSS** - Enhanced styling and responsive design
- **JavaScript integration** - For enhanced user interactions

### Infrastructure
- **Railway** - Cloud deployment platform
- **Docker** - Containerization (optional local development)
- **Git** - Version control with automated deployment

### File Storage
- **Local file system** - Organized by organization and resource type
- **FastAPI StaticFiles** - Authenticated file serving
- **JWT authentication** - Secure file access

## 🏛️ Architecture Components

### 1. API Layer (`app/`)
```
app/
├── main.py                 # FastAPI application entry point
├── database.py            # Database configuration and connection
├── core/                  # Core utilities and configuration
│   ├── config.py         # Environment and settings
│   └── auth.py           # Authentication helpers
├── api/                  # API route modules
│   ├── ai.py            # AI-powered document analysis
│   ├── calendar.py      # Event and calendar management
│   ├── horses.py        # Horse CRUD operations
│   ├── horse_photos.py  # Photo upload/serving with JWT auth
│   ├── horse_documents.py # Document management
│   ├── supplies.py      # Inventory and supply chain
│   └── whiteboard.py    # Message board functionality
├── models/              # SQLAlchemy database models
├── schemas/             # Pydantic request/response schemas
└── services/            # Business logic services
```

### 2. Frontend Layer (`frontend/`)
```
frontend/
├── app.py                 # Main Streamlit application
├── auth_helper.py         # Authentication utilities
└── static/               # Static assets and styling
```

### 3. Storage Layer (`storage/`)
```
storage/
├── horse_photos/          # Horse profile photos
│   └── {org_id}/         # Organization-specific directories
│       └── horse_{id}_migrated.{ext}
├── horse_documents/       # Horse-related documents
├── receipts/             # Supply receipts and invoices
└── whiteboard_images/    # Message board attachments
```

### 4. Scripts & Utilities (`scripts/`)
```
scripts/
├── migrate_horse_photos.py  # Photo migration utilities
└── backup_scripts/          # Backup and maintenance tools
```

## 🔐 Authentication & Session Management

### PropelAuth Integration
- **Multi-tenant architecture** with organization-based access control
- **JWT token-based authentication** for API security
- **Role-based permissions** (Owner, Admin, Member, Staff)
- **Automatic token refresh** and session management

### Session Flow
1. **User Login** → PropelAuth handles authentication
2. **Token Exchange** → Frontend receives JWT access token
3. **API Requests** → All API calls include `Authorization: Bearer {token}`
4. **Token Validation** → FastAPI validates JWT on each request
5. **Organization Access** → User access filtered by organization membership

### Authentication Helpers
```python
# Frontend (auth_helper.py)
def get_current_user() -> dict
def get_access_token() -> str
def get_user_organizations() -> list

# Backend (core/auth.py)
def get_current_user(credentials) -> dict
def get_user_barn_access(user_id, org_id) -> bool
```

## 📁 File Storage & Media Handling

### FastAPI Photo Serving Architecture
The system uses a sophisticated photo serving architecture that balances security, performance, and user experience.

#### Photo Storage Structure
```
storage/horse_photos/{organization_id}/horse_{horse_id}_migrated.{ext}
```

#### API Endpoints
```python
# Upload photo (POST /api/v1/horses/{horse_id}/photo)
@router.post("/horses/{horse_id}/photo")
async def upload_horse_photo(
    horse_id: int,
    file: UploadFile,
    organization_id: str,
    current_user: dict = Depends(get_current_user)
)

# Serve photo (GET /api/v1/horses/{horse_id}/photo)
@router.get("/horses/{horse_id}/photo")
async def get_horse_photo(
    horse_id: int,
    organization_id: str,
    current_user: dict = Depends(get_current_user)
)
```

#### Frontend Integration
```python
# Authenticated photo fetching
def fetch_horse_photo(horse_id: int, organization_id: str):
    photo_url = get_horse_photo_url(horse_id, organization_id)
    headers = get_auth_headers()
    response = requests.get(photo_url, headers=headers)
    return response.content if response.status_code == 200 else None

# Display with Streamlit
st.image(photo_data, width=200, caption="Horse Photo")
```

#### Migration from Base64
The system includes migration tools to convert from Base64 storage to file-based storage:
- **Reduced memory usage** - Eliminates large Base64 strings in database
- **Improved performance** - Faster page loads and reduced Railway memory pressure
- **Better scalability** - File-based storage scales more efficiently

## 🗄️ Database Design

### Core Models

#### Horse Model
```python
class Horse(Base):
    id: int (Primary Key)
    name: str
    breed: str
    age_years: int
    organization_id: str (Foreign Key)
    profile_photo_path: str
    current_health_status: str
    # ... additional fields
```

#### Event Model
```python
class Event(Base):
    id: int (Primary Key)
    title: str
    event_type: str
    start_time: datetime
    horse_id: int (Foreign Key)
    organization_id: str
    # ... additional fields
```

#### Supply Model
```python
class Supply(Base):
    id: int (Primary Key)
    name: str
    category: str
    current_stock: float
    organization_id: str
    # ... additional fields
```

### Relationships
- **One-to-Many**: Organization → Horses, Events, Supplies
- **One-to-Many**: Horse → Events, Documents
- **Many-to-Many**: Events ↔ Horses (via event_horses table)

## 🔌 API Endpoints

### Authentication Endpoints
```
POST /api/v1/auth/exchange-code     # Exchange auth code for token
GET  /api/v1/auth/user             # Get current user info
GET  /api/v1/auth/barns            # Get user's accessible organizations
```

### Horse Management
```
GET    /api/v1/horses/             # List horses (with org filter)
POST   /api/v1/horses/             # Create new horse
GET    /api/v1/horses/{id}         # Get horse details
PUT    /api/v1/horses/{id}         # Update horse
DELETE /api/v1/horses/{id}         # Delete horse
```

### Photo Management
```
POST   /api/v1/horses/{id}/photo   # Upload horse photo
GET    /api/v1/horses/{id}/photo   # Serve horse photo (authenticated)
DELETE /api/v1/horses/{id}/photo   # Delete horse photo
```

### Calendar & Events
```
GET    /api/v1/calendar/upcoming   # Get upcoming events
POST   /api/v1/calendar/events     # Create new event
PUT    /api/v1/calendar/events/{id} # Update event
DELETE /api/v1/calendar/events/{id} # Delete event
```

### Supply Management
```
GET    /api/v1/supplies/           # List supplies
POST   /api/v1/supplies/           # Add supply item
PUT    /api/v1/supplies/{id}       # Update supply
POST   /api/v1/supplies/receipt-scan # AI-powered receipt processing
```

### AI Services
```
POST   /api/v1/ai/analyze          # Analyze documents with Claude
POST   /api/v1/ai/ask              # Ask questions about horses/documents
```

## 🖥️ Frontend Structure

### Page Navigation
- **Horse Directory** - Main horse listing with search/filter
- **Horse Profile** - Detailed horse information and photo
- **Add New Horse** - Horse creation form
- **Edit Horse** - Horse modification form
- **Calendar** - Event management and scheduling
- **Supplies** - Inventory and supply chain management
- **Message Board** - Communication and announcements
- **AI Assistant** - Document analysis and Q&A
- **Reports** - Analytics and reporting dashboard

### Key Frontend Components
```python
# Main navigation and authentication
def main()

# Horse management
def show_horse_directory()
def show_horse_profile()
def show_edit_horse_form()

# Feature modules
def show_calendar()
def show_supplies()
def show_message_board()
def show_ai_assistant()

# Utility functions
def api_request(method, endpoint, params=None)
def fetch_horse_photo(horse_id, organization_id)
```

### Styling & UX
- **Custom CSS** for professional appearance
- **Responsive design** for mobile compatibility
- **Card-based layouts** for horse directory
- **Two-column layouts** for forms and details
- **Loading spinners** and progress indicators

## 🚀 Deployment & DevOps

### Railway Deployment
- **Automatic deployment** from GitHub main branch
- **Environment variables** managed through Railway dashboard
- **Health checks** via `/health` endpoint
- **Log monitoring** through Railway console

### Environment Configuration
```bash
# Required Environment Variables
DATABASE_URL=postgresql://...
PROPELAUTH_URL=https://...
PROPELAUTH_API_KEY=...
ANTHROPIC_API_KEY=...
```

### Backup Strategy
- **Database backups** via Railway automatic backups
- **Code versioning** with Git tags for major releases
- **Migration backups** before significant changes
- **File storage** included in deployment

### Monitoring
- **Health endpoint** for uptime monitoring
- **Railway metrics** for performance tracking
- **Error logging** via FastAPI logging configuration
- **User session monitoring** through PropelAuth

## 💻 Development Workflow

### Local Development Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd barn-management

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run database migrations
python -c "from app.database import Base, db_manager; Base.metadata.create_all(bind=db_manager.engine)"

# 6. Start services
# Terminal 1: FastAPI backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Terminal 2: Streamlit frontend
cd frontend && streamlit run app.py --server.port 8501
```

### Git Workflow
```bash
# Feature development
git checkout -b feature/photo-optimization
# ... make changes ...
git add .
git commit -m "Optimize photo loading performance"
git push origin feature/photo-optimization

# Deployment
git checkout main
git merge feature/photo-optimization
git push origin main  # Triggers Railway deployment
```

### Testing Strategy
- **Manual testing** across multiple browsers
- **Authentication flow testing** with different user roles
- **File upload/download testing** with various file types
- **Performance testing** for memory usage and response times

## 🛡️ Security Considerations

### Authentication Security
- **JWT token validation** on all protected endpoints
- **Organization-based access control** for multi-tenancy
- **Token expiration** and automatic refresh
- **Secure credential storage** via environment variables

### File Security
- **Authenticated file serving** prevents unauthorized access
- **Organization isolation** ensures users only access their files
- **File type validation** on uploads
- **Path traversal protection** in file operations

### API Security
- **CORS configuration** for cross-origin requests
- **Input validation** via Pydantic schemas
- **SQL injection prevention** via SQLAlchemy ORM
- **Rate limiting** considerations for production

## ⚡ Performance Optimizations

### Photo Serving Optimization
- **FastAPI StaticFiles** for efficient file serving
- **JWT authentication** only when necessary
- **File size optimization** through proper image formats
- **Caching headers** for browser caching

### Database Optimization
- **Connection pooling** via SQLAlchemy
- **Query optimization** with proper indexing
- **Lazy loading** for related objects
- **Pagination** for large datasets

### Frontend Optimization
- **Streamlit caching** for expensive operations
- **Session state management** for user data
- **Conditional rendering** to reduce load times
- **Image optimization** in the frontend

### Memory Management
- **Eliminated Base64 storage** for photos
- **Streaming file responses** for large files
- **Garbage collection** optimization
- **Railway memory monitoring**

## 🔧 Troubleshooting Guide

### Common Issues

#### Photo Loading Problems
```python
# Check authentication
headers = get_auth_headers()
print(f"Auth headers: {headers}")

# Verify organization access
response = api_request("GET", "/api/v1/auth/barns")
print(f"User orgs: {response}")

# Test photo endpoint directly
photo_url = get_horse_photo_url(horse_id, org_id)
response = requests.get(photo_url, headers=headers)
print(f"Photo response: {response.status_code}")
```

#### Database Connection Issues
```python
# Test database connection
from app.database import db_manager
if db_manager.test_connection():
    print("Database connected successfully")
else:
    print("Database connection failed")
```

#### Authentication Problems
```python
# Verify PropelAuth configuration
from app.core.config import get_settings
settings = get_settings()
print(f"PropelAuth URL: {settings.propelauth_url}")
```

### Performance Debugging
- **Railway logs** for server-side issues
- **Browser dev tools** for frontend debugging
- **Database query logging** for slow queries
- **Memory profiling** for optimization opportunities

### Maintenance Tasks
- **Database cleanup** for old records
- **File storage cleanup** for orphaned files
- **Log rotation** for long-term maintenance
- **Security updates** for dependencies

## 📈 Future Development Roadmap

### Planned Features
- **Mobile app** development
- **Advanced analytics** and reporting
- **Veterinary integration** with external systems
- **Automated notifications** and alerts
- **Document OCR** for automated data entry

### Technical Improvements
- **Automated testing** suite
- **Performance monitoring** integration
- **Advanced caching** strategies
- **Microservices** architecture expansion
- **Real-time updates** via WebSockets

### Scalability Considerations
- **Database sharding** for large organizations
- **CDN integration** for global file serving
- **Load balancing** for high availability
- **Caching layer** with Redis
- **Message queues** for background processing

---

## 📞 Development Support

For development questions or issues:
1. Check this documentation first
2. Review Railway logs for server issues
3. Test authentication flow manually
4. Verify environment configuration
5. Check GitHub issues for known problems

This system architecture provides a solid foundation for barn management with room for future growth and enhancement.