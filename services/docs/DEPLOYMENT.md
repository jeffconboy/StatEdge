# StatEdge Deployment Guide

Comprehensive deployment guide for the StatEdge microservice architecture with Docker, environment configuration, and production setup.

## Quick Start Deployment

### 1. Complete System Startup
```bash
# Clone and navigate to project
git clone <repository-url>
cd StatEdge

# Start all services with Docker Compose
docker-compose up -d

# Verify all services are running
docker-compose ps

# Check service health
curl http://localhost:8000/health  # Sports API
curl http://localhost:8001/health  # User Management
curl http://localhost:8002/health  # Betting Odds
curl http://localhost:3000         # Frontend
```

### 2. Service Access Points
- **Frontend**: http://localhost:3000
- **Sports API**: http://localhost:8000/docs
- **User Management**: http://localhost:8001/docs
- **Betting Odds**: http://localhost:8002/docs
- **Databases**: PostgreSQL on 5432 (Sports) and 5433 (Users)
- **Cache**: Redis on 6379

## Docker Compose Configuration

### Main docker-compose.yml
```yaml
version: '3.8'

services:
  # Frontend Service
  frontend:
    build: ./services/frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - VITE_API_BASE_URL=http://localhost:8000
      - VITE_USER_API_URL=http://localhost:8001
    depends_on:
      - sports-api
      - user-management
    networks:
      - statedge-network

  # Sports API Service
  sports-api:
    build: ./services/sports-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data
      - REDIS_URL=redis://redis:6379
      - API_V1_STR=/api/v1
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=["http://localhost:3000"]
    depends_on:
      - sports-database
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - statedge-network

  # User Management Service
  user-management:
    build: ./services/user-management
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://user_admin:user_secure_2025@users-database:5433/users_data
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
    depends_on:
      - users-database
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - statedge-network

  # Betting Odds Service
  betting-odds:
    build: ./services/betting-odds
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data
      - REDIS_URL=redis://redis:6379
      - DRAFTKINGS_API_KEY=${DRAFTKINGS_API_KEY}
      - FANDUEL_API_KEY=${FANDUEL_API_KEY}
      - ODDS_API_KEY=${ODDS_API_KEY}
    depends_on:
      - sports-database
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - statedge-network

  # Sports Database
  sports-database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sports_data
      POSTGRES_USER: sports_user
      POSTGRES_PASSWORD: sports_secure_2025
    ports:
      - "5432:5432"
    volumes:
      - sports_data:/var/lib/postgresql/data
      - ./services/databases/sql/sports_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sports_user -d sports_data"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - statedge-network

  # Users Database
  users-database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: users_data
      POSTGRES_USER: user_admin
      POSTGRES_PASSWORD: user_secure_2025
    ports:
      - "5433:5432"
    volumes:
      - users_data:/var/lib/postgresql/data
      - ./services/databases/sql/users_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user_admin -d users_data"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - statedge-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - statedge-network

  # Nginx Load Balancer
  nginx:
    build: ./services/infrastructure/nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./services/infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./services/infrastructure/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - sports-api
      - user-management
      - betting-odds
    networks:
      - statedge-network

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./services/infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - statedge-network

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./services/infrastructure/monitoring/grafana:/etc/grafana/provisioning
    networks:
      - statedge-network

volumes:
  sports_data:
  users_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  statedge-network:
    driver: bridge
```

## Environment Configuration

### .env File Setup
```bash
# Create environment file
cp .env.example .env

# Required environment variables
cat > .env << EOF
# Database Configuration
SPORTS_DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data
USERS_DATABASE_URL=postgresql://user_admin:user_secure_2025@users-database:5433/users_data
REDIS_URL=redis://redis:6379

# Authentication & Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256

# Payment Processing
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Sportsbook APIs
DRAFTKINGS_API_KEY=your_draftkings_api_key
FANDUEL_API_KEY=your_fanduel_api_key
BETMGM_API_KEY=your_betmgm_api_key
ODDS_API_KEY=your_odds_api_key

# External APIs
BASEBALL_SAVANT_API_KEY=your_baseball_savant_key
FANGRAPHS_API_KEY=your_fangraphs_key

# Email Configuration
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key

# Application Settings
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
API_V1_STR=/api/v1

# Data Collection
COLLECTION_ENABLED=true
LIVE_UPDATE_INTERVAL=30
PREGAME_UPDATE_INTERVAL=300

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
EOF
```

### Development Environment
```bash
# Development-specific settings
cat > .env.development << EOF
# Development overrides
LOG_LEVEL=DEBUG
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Use test Stripe keys
STRIPE_SECRET_KEY=sk_test_development_key
STRIPE_WEBHOOK_SECRET=whsec_test_development_webhook

# Reduced collection frequency for development
LIVE_UPDATE_INTERVAL=60
PREGAME_UPDATE_INTERVAL=600

# Development database settings
SPORTS_DB_POOL_SIZE=5
USERS_DB_POOL_SIZE=3
EOF
```

### Production Environment
```bash
# Production-specific settings
cat > .env.production << EOF
# Production overrides
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://statedge.com", "https://app.statedge.com"]

# Production Stripe keys
STRIPE_SECRET_KEY=sk_live_production_key
STRIPE_WEBHOOK_SECRET=whsec_live_production_webhook

# Optimized for production
SPORTS_DB_POOL_SIZE=25
USERS_DB_POOL_SIZE=15

# Production security
JWT_SECRET_KEY=your-production-jwt-secret-256-bit-key
REDIS_PASSWORD=your-production-redis-password

# SSL Configuration
SSL_CERT_PATH=/etc/ssl/certs/statedge.crt
SSL_KEY_PATH=/etc/ssl/private/statedge.key
EOF
```

## Individual Service Deployment

### Sports API Service
```bash
# Navigate to service directory
cd services/sports-api

# Build Docker image
docker build -t statedge/sports-api:latest .

# Run with environment variables
docker run -d \
  --name sports-api \
  --network statedge-network \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data \
  -e REDIS_URL=redis://redis:6379 \
  statedge/sports-api:latest

# Check logs
docker logs sports-api -f

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

### User Management Service
```bash
# Navigate to service directory
cd services/user-management

# Build and run
docker build -t statedge/user-management:latest .
docker run -d \
  --name user-management \
  --network statedge-network \
  -p 8001:8001 \
  -e DATABASE_URL=postgresql://user_admin:user_secure_2025@users-database:5433/users_data \
  -e JWT_SECRET_KEY=your-secret-key \
  -e STRIPE_SECRET_KEY=your-stripe-key \
  statedge/user-management:latest

# Test authentication endpoints
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123"}'
```

### Betting Odds Service
```bash
# Navigate to service directory
cd services/betting-odds

# Build and run
docker build -t statedge/betting-odds:latest .
docker run -d \
  --name betting-odds \
  --network statedge-network \
  -p 8002:8002 \
  -e DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data \
  -e ODDS_API_KEY=your-odds-api-key \
  statedge/betting-odds:latest

# Test odds endpoints
curl http://localhost:8002/api/v1/odds/current
curl http://localhost:8002/api/v1/odds/arbitrage
```

### Frontend Service
```bash
# Navigate to service directory
cd services/frontend

# Build production bundle
npm install
npm run build

# Build Docker image
docker build -t statedge/frontend:latest .
docker run -d \
  --name frontend \
  --network statedge-network \
  -p 3000:3000 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  -e VITE_USER_API_URL=http://localhost:8001 \
  statedge/frontend:latest

# Access application
open http://localhost:3000
```

## Database Deployment

### PostgreSQL Setup
```bash
# Start both databases
docker-compose up -d sports-database users-database

# Wait for initialization
docker-compose logs -f sports-database users-database

# Verify connections
docker exec -it sports-database psql -U sports_user -d sports_data -c "SELECT version();"
docker exec -it users-database psql -U user_admin -d users_data -c "SELECT version();"

# Run migrations (if needed)
cd services/sports-api
alembic upgrade head

cd ../user-management
alembic upgrade head
```

### Data Migration from Existing SQLite
```bash
# Export data from existing SQLite database
python scripts/export_sqlite_data.py \
  --source-db /mnt/e/StatEdge/statedge_mlb_full.db \
  --output-dir ./migration_data

# Import to PostgreSQL
python scripts/import_to_postgres.py \
  --input-dir ./migration_data \
  --sports-db postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data \
  --users-db postgresql://user_admin:user_secure_2025@localhost:5433/users_data

# Verify data integrity
python scripts/verify_migration.py \
  --sports-db postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data
```

## Load Balancer Configuration

### Nginx Setup
```nginx
# services/infrastructure/nginx/nginx.conf
upstream frontend_servers {
    server frontend:3000;
}

upstream sports_api_servers {
    server sports-api:8000;
}

upstream user_management_servers {
    server user-management:8001;
}

upstream betting_odds_servers {
    server betting-odds:8002;
}

server {
    listen 80;
    server_name statedge.com www.statedge.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name statedge.com www.statedge.com;

    ssl_certificate /etc/nginx/ssl/statedge.crt;
    ssl_certificate_key /etc/nginx/ssl/statedge.key;

    # Frontend routes
    location / {
        proxy_pass http://frontend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Sports API routes
    location /api/v1/sports/ {
        proxy_pass http://sports_api_servers/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # User Management routes
    location /api/v1/auth/ {
        proxy_pass http://user_management_servers/api/v1/auth/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/v1/user/ {
        proxy_pass http://user_management_servers/api/v1/user/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Betting Odds routes
    location /api/v1/odds/ {
        proxy_pass http://betting_odds_servers/api/v1/odds/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health checks
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# services/infrastructure/monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'sports-api'
    static_configs:
      - targets: ['sports-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'user-management'
    static_configs:
      - targets: ['user-management:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'betting-odds'
    static_configs:
      - targets: ['betting-odds:8002']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres-sports'
    static_configs:
      - targets: ['sports-database:5432']
    scrape_interval: 60s

  - job_name: 'postgres-users'
    static_configs:
      - targets: ['users-database:5432']
    scrape_interval: 60s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboards
```bash
# Create Grafana dashboard configurations
mkdir -p services/infrastructure/monitoring/grafana/dashboards

# Main application dashboard
cat > services/infrastructure/monitoring/grafana/dashboards/statedge-overview.json << EOF
{
  "dashboard": {
    "title": "StatEdge Overview",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (service)",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))",
            "legendFormat": "95th percentile - {{service}}"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(pg_stat_database_numbackends) by (datname)",
            "legendFormat": "{{datname}}"
          }
        ]
      }
    ]
  }
}
EOF
```

## Deployment Commands Reference

### Complete System Deployment
```bash
# 1. Initial setup
git clone <repository-url>
cd StatEdge
cp .env.example .env
# Edit .env with your configuration

# 2. Build all services
docker-compose build

# 3. Start infrastructure services first
docker-compose up -d sports-database users-database redis

# 4. Wait for databases to initialize
sleep 30

# 5. Start application services
docker-compose up -d sports-api user-management betting-odds

# 6. Start frontend and load balancer
docker-compose up -d frontend nginx

# 7. Start monitoring (optional)
docker-compose up -d prometheus grafana

# 8. Verify deployment
docker-compose ps
curl http://localhost/health
```

### Rolling Updates
```bash
# Update individual service
docker-compose build sports-api
docker-compose up -d --no-deps sports-api

# Update all services
docker-compose build
docker-compose up -d

# Zero-downtime deployment with multiple instances
docker-compose up -d --scale sports-api=3
docker-compose up -d --no-deps --scale sports-api=3 sports-api
```

### Backup and Restore
```bash
# Create backups
docker exec sports-database pg_dump -U sports_user sports_data > backups/sports_$(date +%Y%m%d).sql
docker exec users-database pg_dump -U user_admin users_data > backups/users_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i sports-database psql -U sports_user -d sports_data < backups/sports_20250726.sql
docker exec -i users-database psql -U user_admin -d users_data < backups/users_20250726.sql
```

### Troubleshooting Commands
```bash
# Check service logs
docker-compose logs -f sports-api
docker-compose logs -f user-management
docker-compose logs -f betting-odds

# Check database connectivity
docker exec sports-database pg_isready -U sports_user
docker exec users-database pg_isready -U user_admin

# Check Redis connectivity
docker exec redis redis-cli ping

# Monitor resource usage
docker stats

# Check network connectivity
docker exec sports-api ping users-database
docker exec frontend curl sports-api:8000/health
```

---

This deployment guide provides comprehensive instructions for setting up the complete StatEdge microservice architecture with proper configuration, monitoring, and maintenance procedures.