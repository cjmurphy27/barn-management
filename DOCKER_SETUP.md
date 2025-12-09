# Docker Setup Guide

This project uses Docker Compose to run a full-stack application with:
- **Frontend**: TypeScript/React with Vite (port 3000)
- **Backend**: Python FastAPI (port 8000)
- **Database**: PostgreSQL (port 5432)

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)

## Quick Start

1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your actual configuration values.

2. **Build and start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Database: localhost:5432

## Common Commands

### Start services
```bash
# Start all services in foreground
docker-compose up

# Start all services in background
docker-compose up -d

# Build and start (when you've made changes)
docker-compose up --build
```

### Stop services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database data)
docker-compose down -v
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f db
```

### Restart a service
```bash
docker-compose restart api
docker-compose restart frontend
```

### Run commands in containers
```bash
# Access backend shell
docker-compose exec api bash

# Access database
docker-compose exec db psql -U postgres -d barnlady

# Run database migrations
docker-compose exec api alembic upgrade head
```

## Project Structure

```
.
├── docker-compose.yml          # Main orchestration file
├── Dockerfile                  # Backend Python/FastAPI
├── app/                        # Backend source code
├── mobile/                     # Frontend TypeScript/React
│   ├── Dockerfile             # Frontend build configuration
│   ├── nginx.conf             # Nginx web server config
│   └── src/                   # Frontend source code
└── init-db.sql                # Database initialization
```

## Development Workflow

### Frontend Development
The frontend is built with Vite and served via Nginx in production mode. For hot-reload development:

```bash
cd mobile
npm install
npm run dev
```

This runs on port 5173 with hot module replacement.

### Backend Development
For local development with auto-reload:

```bash
# Start only database
docker-compose up db -d

# Run backend locally
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or run with docker but mount source code:

```yaml
# In docker-compose.yml, uncomment the volumes line under api service:
volumes:
  - ./app:/app/app
```

## Troubleshooting

### Port already in use
```bash
# Find what's using the port
lsof -i :8000  # or :3000, :5432

# Kill the process or change ports in docker-compose.yml
```

### Database connection issues
```bash
# Check if database is healthy
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Frontend not loading
```bash
# Check if API is running
curl http://localhost:8000/health

# Rebuild frontend
docker-compose up --build frontend
```

### Clear everything and start fresh
```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Rebuild from scratch
docker-compose up --build
```

## Environment Variables

Key environment variables in `.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_DB` | Database name | `barnlady` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `password` |
| `PROPELAUTH_URL` | PropelAuth URL | `https://your-app.propelauthtest.com` |
| `PROPELAUTH_API_KEY` | PropelAuth API key | `your-api-key` |
| `PROPELAUTH_VERIFIER_KEY` | PropelAuth verifier key | `your-verifier-key` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `VITE_API_BASE_URL` | Frontend API URL | `http://localhost:8000` |

## Health Checks

All services include health checks:
- **API**: `curl http://localhost:8000/health`
- **Frontend**: `wget http://localhost:3000/`
- **Database**: `pg_isready -U postgres`

Check status:
```bash
docker-compose ps
```

## Production Deployment

For production, consider:
1. Use proper secrets management (not `.env` files)
2. Use production-grade PostgreSQL with backups
3. Set up SSL/TLS certificates
4. Configure proper CORS settings
5. Set `DEBUG=false` in backend
6. Use environment-specific configuration files
