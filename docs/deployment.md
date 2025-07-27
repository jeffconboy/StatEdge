# 🚀 StatEdge Deployment Guide

This guide covers deploying StatEdge from local development to production environments.

## 🏗️ Deployment Architecture

### Local Development
```
Docker Compose → All services on localhost
├── PostgreSQL (port 15432)
├── Redis (port 16379)
├── Python Service (port 18000)
├── Node.js API Gateway (port 3001)
└── React Frontend (port 3000)
```

### Production (Recommended)
```
Cloud Load Balancer
├── Frontend (CDN/Static Hosting)
├── API Gateway (Container Service)
├── Python Service (Container Service)
├── Managed PostgreSQL (RDS/Cloud SQL)
└── Managed Redis (ElastiCache/MemoryStore)
```

## 🐳 Docker Production Build

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: statedge
      POSTGRES_USER: statedge
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    
  python-service:
    build: 
      context: ./python-service
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://statedge:${POSTGRES_PASSWORD}@postgres:5432/statedge
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      JWT_SECRET: ${JWT_SECRET}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    
  node-service:
    build:
      context: ./node-service
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://statedge:${POSTGRES_PASSWORD}@postgres:5432/statedge
      JWT_SECRET: ${JWT_SECRET}
      PYTHON_SERVICE_URL: http://python-service:8000
      NODE_ENV: production
    ports:
      - "3001:3001"
    depends_on:
      - postgres
      - python-service
    restart: unless-stopped
    
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        REACT_APP_API_URL: ${REACT_APP_API_URL}
    ports:
      - "3000:80"
    depends_on:
      - node-service
    restart: unless-stopped

volumes:
  postgres_data:
```

### Production Dockerfiles

**Python Service (`python-service/Dockerfile.prod`):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Node.js Service (`node-service/Dockerfile.prod`):**
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

EXPOSE 3001

CMD ["node", "server.js"]
```

**Frontend (`frontend/Dockerfile.prod`):**
```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## ☁️ Cloud Deployment

### AWS Deployment

**Architecture:**
```
Internet Gateway
├── CloudFront (CDN) → S3 (Frontend)
├── Application Load Balancer
│   ├── ECS Service (API Gateway)
│   └── ECS Service (Python Service)
├── RDS PostgreSQL (Multi-AZ)
└── ElastiCache Redis (Cluster Mode)
```

**Required AWS Services:**
- **ECS (Elastic Container Service)**: Container orchestration
- **RDS**: Managed PostgreSQL database
- **ElastiCache**: Managed Redis cache
- **S3 + CloudFront**: Frontend hosting and CDN
- **Application Load Balancer**: Traffic routing
- **VPC**: Network isolation and security

**Estimated Monthly Cost:**
- **ECS Tasks**: 2x t3.medium = $60
- **RDS**: db.t3.micro = $25
- **ElastiCache**: cache.t3.micro = $15
- **Load Balancer**: $18
- **S3 + CloudFront**: $5
- **Total**: ~$125/month

### Google Cloud Deployment

**Architecture:**
```
Cloud Load Balancer
├── Cloud CDN → Cloud Storage (Frontend)
├── Cloud Run (API Gateway)
├── Cloud Run (Python Service)
├── Cloud SQL (PostgreSQL)
└── Memorystore (Redis)
```

**Deployment Script:**
```bash
#!/bin/bash

# Set project variables
PROJECT_ID="statedge-prod"
REGION="us-central1"

# Build and push containers
gcloud builds submit --tag gcr.io/$PROJECT_ID/python-service ./python-service
gcloud builds submit --tag gcr.io/$PROJECT_ID/node-service ./node-service

# Deploy Cloud Run services
gcloud run deploy python-service \
  --image gcr.io/$PROJECT_ID/python-service \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2

gcloud run deploy node-service \
  --image gcr.io/$PROJECT_ID/node-service \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1

# Deploy frontend to Cloud Storage
gsutil -m rsync -r -d ./frontend/build gs://statedge-frontend
```

### Azure Deployment

**Architecture:**
```
Azure Front Door
├── Azure CDN → Blob Storage (Frontend)
├── Container Instances (API Gateway)
├── Container Instances (Python Service)
├── Azure PostgreSQL (Flexible Server)
└── Azure Cache for Redis
```

## 🔧 Environment Configuration

### Production Environment Variables

Create `.env.prod`:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://statedge:your_secure_password_here@postgres:5432/statedge

# Security
JWT_SECRET=your_jwt_secret_minimum_32_characters
OPENAI_API_KEY=your_openai_api_key

# API URLs
REACT_APP_API_URL=https://api.yourdomain.com
PYTHON_SERVICE_URL=http://python-service:8000

# Performance
REDIS_URL=redis://redis:6379
NODE_ENV=production
PYTHONUNBUFFERED=1
```

### Security Configuration

**SSL/TLS Setup:**
```bash
# Generate SSL certificates (Let's Encrypt)
certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Update nginx configuration
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Environment Security:**
```bash
# Secure file permissions
chmod 600 .env.prod
chown root:root .env.prod

# Use Docker secrets in production
docker secret create postgres_password postgres_password.txt
docker secret create jwt_secret jwt_secret.txt
```

## 📊 Database Migration

### Production Database Setup

```sql
-- Create production database
CREATE DATABASE statedge_prod;
CREATE USER statedge_prod WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE statedge_prod TO statedge_prod;

-- Import schema
\i /path/to/init.sql

-- Create additional indexes for production
CREATE INDEX CONCURRENTLY idx_statcast_compound 
ON statcast_pitches(game_date, batter_id, pitcher_id);

CREATE INDEX CONCURRENTLY idx_fangraphs_season_player 
ON fangraphs_batting(season, player_id);

-- Set up automated backups
SELECT pg_create_physical_replication_slot('backup_slot');
```

### Data Migration

```bash
# Export from development
docker exec statedge_postgres pg_dump -U statedge statedge > dev_backup.sql

# Import to production
psql -h prod-db-host -U statedge_prod statedge_prod < dev_backup.sql

# Verify data integrity
psql -h prod-db-host -U statedge_prod statedge_prod -c "
SELECT 
    'statcast' as table_name, COUNT(*) as records 
FROM statcast_pitches
UNION ALL
SELECT 'fangraphs_batting', COUNT(*) FROM fangraphs_batting
UNION ALL  
SELECT 'fangraphs_pitching', COUNT(*) FROM fangraphs_pitching;
"
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Tests
        run: |
          docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
          
  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
          
      - name: Build and push images
        run: |
          # Build images
          docker build -t statedge/python-service:$GITHUB_SHA ./python-service
          docker build -t statedge/node-service:$GITHUB_SHA ./node-service
          
          # Push to ECR
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker tag statedge/python-service:$GITHUB_SHA $ECR_REGISTRY/python-service:$GITHUB_SHA
          docker tag statedge/node-service:$GITHUB_SHA $ECR_REGISTRY/node-service:$GITHUB_SHA
          docker push $ECR_REGISTRY/python-service:$GITHUB_SHA
          docker push $ECR_REGISTRY/node-service:$GITHUB_SHA
          
      - name: Deploy to ECS
        run: |
          # Update ECS service
          aws ecs update-service --cluster statedge-cluster --service python-service --force-new-deployment
          aws ecs update-service --cluster statedge-cluster --service node-service --force-new-deployment
```

### Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash

set -e

# Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "Deploying StatEdge $VERSION to $ENVIRONMENT"

# Pre-deployment checks
echo "Running pre-deployment checks..."
docker-compose -f docker-compose.test.yml run --rm test

# Build production images
echo "Building production images..."
docker-compose -f docker-compose.prod.yml build

# Database migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm python-service python migrate.py

# Deploy services
echo "Deploying services..."
docker-compose -f docker-compose.prod.yml up -d

# Health checks
echo "Performing health checks..."
sleep 30

for service in python-service node-service; do
  if ! docker-compose -f docker-compose.prod.yml exec $service curl -f http://localhost/health; then
    echo "Health check failed for $service"
    exit 1
  fi
done

echo "Deployment completed successfully!"
```

## 📈 Monitoring and Logging

### Production Monitoring

**Health Check Endpoints:**
```bash
# Service health
curl https://api.yourdomain.com/health

# Database connectivity
curl https://api.yourdomain.com/api/test/database-stats

# Data freshness
curl https://api.yourdomain.com/api/test/2025-data-verification
```

**Monitoring Setup:**
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000" 
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

### Log Aggregation

**Centralized Logging:**
```bash
# Install log aggregation
docker run -d \
  --name fluentd \
  -p 24224:24224 \
  -v /var/log:/fluentd/log \
  fluentd:latest

# Configure services to use fluentd
docker-compose -f docker-compose.prod.yml up -d \
  --log-driver=fluentd \
  --log-opt fluentd-address=localhost:24224
```

## 🔒 Security Hardening

### Production Security Checklist

- [ ] **SSL/TLS**: HTTPS everywhere with valid certificates
- [ ] **Firewall**: Only necessary ports exposed
- [ ] **Authentication**: Strong JWT secrets and password policies
- [ ] **Database**: Encrypted connections and restricted access
- [ ] **Secrets**: Environment variables and Docker secrets
- [ ] **Updates**: Regular security patches and dependency updates
- [ ] **Backups**: Automated database and configuration backups
- [ ] **Monitoring**: Real-time security monitoring and alerting

### Security Configuration

```bash
# Firewall setup (UFW)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Docker security
echo '{
  "icc": false,
  "userland-proxy": false,
  "no-new-privileges": true
}' > /etc/docker/daemon.json

systemctl restart docker
```

## 🔄 Backup and Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/statedge"

# Database backup
docker exec statedge_postgres pg_dump -U statedge statedge | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Configuration backup
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
  docker-compose.prod.yml \
  .env.prod \
  nginx.conf

# Upload to cloud storage (AWS S3 example)
aws s3 sync $BACKUP_DIR s3://statedge-backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### Disaster Recovery

```bash
# Recovery procedure
#!/bin/bash

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore database
gunzip -c backup.sql.gz | docker exec -i statedge_postgres psql -U statedge statedge

# Restore configuration
tar -xzf config_backup.tar.gz

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Verify recovery
curl https://api.yourdomain.com/health
```

---

**Production deployment requires careful planning and testing. Always test in a staging environment before deploying to production.**