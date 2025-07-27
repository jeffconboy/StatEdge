# Setup Guide

## StatEdge Betting Service Setup Guide

This guide will walk you through setting up the StatEdge Betting Service from scratch.

---

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 2GB RAM available
- **Storage**: At least 5GB free space
- **Network**: Internet connection for API access

### Required Software
- **Docker** (v20.0+) and **Docker Compose** (v2.0+)
- **PostgreSQL** (v13+) 
- **Python** (v3.11+) - if running locally
- **Git** - for version control

### API Access
- **Tank01 RapidAPI Key** - for MLB odds data
  - Sign up at [RapidAPI](https://rapidapi.com/)
  - Subscribe to Tank01 MLB API
  - Get your API key

---

## Quick Start (Docker Method - Recommended)

### 1. Clone and Navigate
```bash
cd /path/to/StatEdge
```

### 2. Set Up Environment
```bash
# Copy environment template
cp betting-service/.env.example betting-service/.env

# Edit environment variables
nano betting-service/.env
```

Configure these key variables:
```bash
# Database Configuration
BETTING_DATABASE_URL=postgresql://betting_user:betting_secure_2025@localhost:5432/betting_data

# Tank01 API Configuration  
TANK01_API_KEY=your_actual_tank01_api_key_here

# Service Configuration
HOST=0.0.0.0
PORT=18002
DEBUG=False
```

### 3. Create Database
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres

# Create database and user
CREATE DATABASE betting_data;
CREATE USER betting_user WITH PASSWORD 'betting_secure_2025';
GRANT ALL PRIVILEGES ON DATABASE betting_data TO betting_user;
\q
```

### 4. Start Services
```bash
# Build and start all services
docker-compose up --build

# Or start just the betting service
docker-compose up --build betting-service
```

### 5. Verify Installation
```bash
# Check service health
curl http://localhost:18002/health

# Run test suite
docker exec statedge_betting python test_service.py
```

**✅ You're ready to go!** Visit http://localhost:18002/docs for API documentation.

---

## Detailed Setup Instructions

### Database Setup (Detailed)

#### Option 1: Using Docker PostgreSQL
```bash
# Add PostgreSQL to docker-compose.yml
postgres:
  image: postgres:15
  container_name: statedge_postgres
  environment:
    POSTGRES_DB: betting_data
    POSTGRES_USER: betting_user
    POSTGRES_PASSWORD: betting_secure_2025
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Option 2: Local PostgreSQL Installation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)

#### Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE betting_data;
CREATE USER betting_user WITH PASSWORD 'betting_secure_2025';
GRANT ALL PRIVILEGES ON DATABASE betting_data TO betting_user;

# Grant schema permissions
\c betting_data
GRANT ALL ON SCHEMA public TO betting_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO betting_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO betting_user;

\q
```

#### Test Database Connection
```bash
psql -h localhost -U betting_user -d betting_data -c "SELECT version();"
```

### Tank01 API Setup

#### 1. Sign Up for RapidAPI
1. Go to [RapidAPI](https://rapidapi.com/)
2. Create a free account
3. Verify your email address

#### 2. Subscribe to Tank01 MLB API
1. Search for "Tank01 MLB Live"
2. Go to the Tank01 MLB API page
3. Choose a subscription plan (Basic plan works for personal use)
4. Subscribe to the API

#### 3. Get Your API Key
1. Go to your RapidAPI dashboard
2. Find the Tank01 MLB API in your subscriptions
3. Copy your API key (X-RapidAPI-Key)
4. Add it to your `.env` file

#### 4. Test API Access
```bash
# Test your API key
curl -X GET \
  "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com/getMLBTeams" \
  -H "X-RapidAPI-Key: YOUR_API_KEY_HERE" \
  -H "X-RapidAPI-Host: tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
```

### Local Development Setup

#### 1. Python Environment
```bash
# Create virtual environment
cd betting-service
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Environment Configuration
```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

#### 3. Database Initialization
```bash
# Initialize database schema
python -c "
import asyncio
from database.connection import init_database
asyncio.run(init_database())
"
```

#### 4. Start Development Server
```bash
# Start the service
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 18002 --reload
```

---

## Configuration Options

### Environment Variables

#### Database Configuration
```bash
# PostgreSQL connection string
BETTING_DATABASE_URL=postgresql://user:password@host:port/database

# Examples:
# Local database:
BETTING_DATABASE_URL=postgresql://betting_user:betting_secure_2025@localhost:5432/betting_data

# Docker database:
BETTING_DATABASE_URL=postgresql://betting_user:betting_secure_2025@postgres:5432/betting_data

# Remote database:
BETTING_DATABASE_URL=postgresql://user:pass@db.example.com:5432/betting_data
```

#### API Configuration
```bash
# Tank01 RapidAPI Key
TANK01_API_KEY=your_rapidapi_key

# Service settings
HOST=0.0.0.0                    # Listen on all interfaces
PORT=18002                      # Service port
DEBUG=False                     # Debug mode (True for development)
```

#### Integration URLs
```bash
# Other service URLs (for microservice communication)
SPORTS_DATA_SERVICE_URL=http://localhost:18001
FRONTEND_URL=http://localhost:3002
```

### Docker Configuration

#### Dockerfile Customization
```dockerfile
# Custom build for different environments
FROM python:3.11-slim

# Development
ENV DEBUG=True
ENV LOG_LEVEL=DEBUG

# Production  
ENV DEBUG=False
ENV LOG_LEVEL=INFO
```

#### Docker Compose Overrides
```yaml
# docker-compose.override.yml for local development
version: '3.8'
services:
  betting-service:
    volumes:
      - ./betting-service:/app
    environment:
      - DEBUG=True
    command: uvicorn main:app --host 0.0.0.0 --port 18002 --reload
```

---

## Verification & Testing

### Health Checks

#### Service Health
```bash
# Basic health check
curl http://localhost:18002/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-07-26T19:30:00Z",
  "service": "betting-service"
}
```

#### Database Health
```bash
# Test database connection
curl http://localhost:18002/api/analytics/summary

# Should return performance data (even if empty)
```

#### API Integration Health
```bash
# Test Tank01 integration
curl http://localhost:18002/api/games/today

# Should return today's games with odds
```

### Automated Testing

#### Run Full Test Suite
```bash
# From betting-service directory
python test_service.py
```

#### Individual Component Tests
```bash
# Test database connection
python -c "
import asyncio
from database.connection import test_connection
asyncio.run(test_connection())
"

# Test Tank01 API
python -c "
import asyncio
from services.tank01_service import Tank01Service
tank01 = Tank01Service()
result = asyncio.run(tank01.test_connection())
print(result)
"
```

### Manual Testing

#### Create Sample Bet
```bash
curl -X POST http://localhost:18002/api/bets/ \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "20250726_TEST@SAMPLE",
    "home_team": "SAMPLE",
    "away_team": "TEST",
    "game_date": "2025-07-26",
    "bet_type": "moneyline",
    "bet_side": "home",
    "bet_amount": 25.00,
    "confidence_level": 7,
    "prediction_reasoning": "Test bet"
  }'
```

#### Check Betting History
```bash
curl http://localhost:18002/api/bets/?limit=5
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed
**Error:** `Database connection error`

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list | grep postgres  # macOS
   ```

2. Verify database exists:
   ```bash
   psql -h localhost -U betting_user -d betting_data -c "\l"
   ```

3. Check connection string format:
   ```bash
   # Correct format:
   postgresql://user:password@host:port/database
   ```

#### Tank01 API Errors
**Error:** `Failed to get Tank01 data`

**Solutions:**
1. Verify API key is set:
   ```bash
   echo $TANK01_API_KEY
   ```

2. Test API key manually:
   ```bash
   curl -H "X-RapidAPI-Key: YOUR_KEY" \
     "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com/getMLBTeams"
   ```

3. Check subscription status on RapidAPI dashboard

#### Port Already in Use
**Error:** `Address already in use`

**Solutions:**
1. Find what's using the port:
   ```bash
   lsof -i :18002  # Linux/macOS
   netstat -ano | findstr :18002  # Windows
   ```

2. Kill the process or change port:
   ```bash
   # Kill process
   kill -9 <PID>
   
   # Or change port in .env
   PORT=18003
   ```

#### Permission Denied
**Error:** `Permission denied`

**Solutions:**
1. Check Docker permissions:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. Check file permissions:
   ```bash
   chmod +x betting-service/test_service.py
   ```

### Log Analysis

#### Container Logs
```bash
# View betting service logs
docker logs statedge_betting

# Follow logs in real-time
docker logs -f statedge_betting

# View last 100 lines
docker logs --tail 100 statedge_betting
```

#### Application Logs
```bash
# Enable debug logging in .env
DEBUG=True

# View logs in development
tail -f /var/log/betting-service.log
```

#### Database Logs
```bash
# PostgreSQL logs location varies by OS
# Ubuntu/Debian:
sudo tail -f /var/log/postgresql/postgresql-*.log

# macOS (Homebrew):
tail -f /usr/local/var/log/postgres.log
```

---

## Production Deployment

### Security Hardening

#### Database Security
```sql
-- Revoke public permissions
REVOKE ALL ON SCHEMA public FROM public;
GRANT USAGE ON SCHEMA public TO betting_user;

-- Use strong passwords
ALTER USER betting_user PASSWORD 'very_secure_password_123!';

-- Restrict connections
-- In postgresql.conf:
listen_addresses = 'localhost'
```

#### Network Security
```yaml
# docker-compose.yml - production settings
services:
  betting-service:
    networks:
      - betting_network
    expose:
      - "18002"  # Don't publish to host in production

networks:
  betting_network:
    driver: bridge
    internal: true  # No external access
```

### Performance Optimization

#### Database Optimization
```sql
-- Create additional indexes for common queries
CREATE INDEX idx_bets_created_at ON bets(created_at);
CREATE INDEX idx_bets_confidence_date ON bets(confidence_level, game_date);

-- Analyze tables for query optimization
ANALYZE bets;
ANALYZE betting_strategies;
```

#### Application Optimization
```bash
# Use production WSGI server
pip install gunicorn

# Start with multiple workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:18002
```

### Monitoring Setup

#### Health Monitoring
```bash
# Add health check script
#!/bin/bash
# health_monitor.sh

HEALTH_URL="http://localhost:18002/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "$(date): Service healthy"
else
    echo "$(date): Service unhealthy - HTTP $RESPONSE"
    # Add alerting logic here
fi
```

#### Backup Automation
```bash
# Add to crontab for daily backups
0 2 * * * /usr/local/bin/backup_betting_db.sh
```

---

## Next Steps

After successful setup:

1. **Explore the API**: Visit http://localhost:18002/docs
2. **Create your first bet**: Use the interactive API docs
3. **Set up frontend integration**: Connect to the React frontend
4. **Configure strategies**: Define your betting approaches
5. **Start tracking**: Begin logging your predictions

### Integration with Frontend
The betting service is designed to integrate with the StatEdge frontend. Update the frontend environment to include:

```bash
# In frontend .env
VITE_BETTING_API_URL=http://localhost:18002/api
```

### Integration with Sports Data Service
The betting service can call the sports data service for additional game information:

```bash
# In betting service .env
SPORTS_DATA_SERVICE_URL=http://localhost:18001
```

---

## Support

If you encounter issues during setup:

1. Check the troubleshooting section above
2. Review the logs for error details
3. Verify all prerequisites are installed
4. Test each component individually
5. Ensure all environment variables are set correctly

The betting service is designed to be self-contained and easy to set up. Most issues are related to database connections or API key configuration.