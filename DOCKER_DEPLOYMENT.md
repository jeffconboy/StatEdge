# StatEdge Docker Containerization

## Quick Start

Start the entire StatEdge application with a single command:

```bash
docker-compose up -d
```

Access the application:
- **Frontend**: http://localhost:3002
- **API**: http://localhost:18001
- **Database**: localhost:15432 (PostgreSQL)

## Services

### Database (PostgreSQL 16)
- **Port**: 15432
- **Database**: statedge
- **User**: statedge_user
- **Password**: statedge_password

### API (Python FastAPI)
- **Port**: 18001
- **Health Check**: http://localhost:18001/health
- **Documentation**: http://localhost:18001/docs

### Frontend (Vue.js + Vite)
- **Port**: 3002
- **Development server with hot reload**

## Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose build

# Clean restart (remove volumes)
docker-compose down -v && docker-compose up -d
```

## Production Deployment

Use the production compose file for optimized builds:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Production changes:
- Frontend uses Nginx with static builds (port 80)
- Environment variables from .env file
- Read-only volume mounts

## Environment Configuration

Copy `.env.example` to `.env` and modify for your environment:

```bash
cp .env.example .env
```

Key variables:
- `POSTGRES_PASSWORD`: Database password
- `VITE_API_BASE_URL`: Frontend API endpoint

## Health Checks

All services include health checks:
- **Database**: PostgreSQL connection test
- **API**: `/health` endpoint
- **Frontend**: HTTP response check

## Volume Persistence

- `postgres_data`: Database files persist across container restarts
- `./static`: AI portraits and static assets

## Sprint Completion ✅

**Docker containerization sprint completed successfully!**

All StatEdge services now run in containers with:
- ✅ Complete service orchestration
- ✅ Health monitoring
- ✅ Data persistence
- ✅ Development and production modes
- ✅ Single-command deployment

**Run `docker-compose up -d` to start the full StatEdge platform!**