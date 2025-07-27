# 🔧 StatEdge Troubleshooting Guide

This guide helps resolve common issues with the StatEdge baseball analytics platform.

## 🚨 Quick Diagnostic Commands

Before diving into specific issues, run these commands to check system status:

```bash
# Check all services
docker-compose ps

# View service logs
docker-compose logs python-service
docker-compose logs node-service
docker-compose logs postgres
docker-compose logs redis

# Test API connectivity
curl http://localhost:18000/health
curl http://localhost:3001/health

# Check database connectivity
curl http://localhost:18000/api/test/database-stats
```

## 🐳 Docker Issues

### Services Won't Start

**Symptoms:**
- `docker-compose up` fails
- Services show as "Exit 1" status
- Port binding errors

**Solutions:**

1. **Check Port Conflicts**
```bash
# Check if ports are in use
netstat -tulpn | grep :15432  # PostgreSQL
netstat -tulpn | grep :16379  # Redis  
netstat -tulpn | grep :18000  # Python service
netstat -tulpn | grep :3001   # Node service
netstat -tulpn | grep :3000   # Frontend

# Stop any conflicting services
sudo systemctl stop postgresql
sudo systemctl stop redis-server
```

2. **Clean Docker State**
```bash
# Stop all containers
docker-compose down

# Remove containers and networks
docker-compose down --remove-orphans

# Rebuild with clean state
docker-compose up --build --force-recreate
```

3. **Check Docker Resources**
```bash
# Verify Docker has enough resources
docker system df
docker system prune  # Clean up if needed

# Check available disk space
df -h
```

### Database Connection Issues

**Symptoms:**
- "Connection refused" errors
- Database queries timeout
- Authentication failures

**Solutions:**

1. **Verify Database Status**
```bash
# Check PostgreSQL container
docker-compose logs postgres

# Test database connection
docker exec -it statedge_postgres psql -U statedge -d statedge -c "SELECT 1;"
```

2. **Reset Database**
```bash
# Stop services
docker-compose down

# Remove database volume (CAUTION: Loses data)
docker volume rm statedge_postgres_data

# Restart with fresh database
docker-compose up -d postgres
```

3. **Check Environment Variables**
```bash
# Verify database credentials in docker-compose.yml
grep -A 5 -B 5 "POSTGRES" docker-compose.yml

# Check Python service connection string
docker-compose logs python-service | grep -i database
```

## 🐍 Python Service Issues

### Service Won't Start

**Symptoms:**
- Python container exits immediately
- Import errors in logs
- Port binding failures

**Solutions:**

1. **Check Dependencies**
```bash
# View Python service logs
docker-compose logs python-service

# Rebuild Python service
docker-compose build python-service

# Check requirements.txt
cat python-service/requirements.txt
```

2. **Test PyBaseball Connection**
```bash
# Test PyBaseball import
docker exec statedge_python python -c "import pybaseball; print('PyBaseball OK')"

# Test data collection
curl -X POST "http://localhost:18000/api/test/collect-data?date=2025-07-23"
```

3. **Environment Variables**
```bash
# Check Python service environment
docker exec statedge_python env | grep -E "(DATABASE|REDIS|OPENAI)"
```

### Data Collection Failures

**Symptoms:**
- Collection endpoints return errors
- No data being stored
- PyBaseball import errors

**Solutions:**

1. **Check PyBaseball Status**
```bash
# Test PyBaseball directly
docker exec statedge_python python -c "
import pybaseball as pyb
from datetime import date
try:
    data = pyb.statcast(start_dt='2025-07-23', end_dt='2025-07-23')
    print(f'Success: {len(data)} records')
except Exception as e:
    print(f'Error: {e}')
"
```

2. **Verify Database Schema**
```bash
# Check if tables exist
docker exec statedge_postgres psql -U statedge -d statedge -c "
\dt
SELECT COUNT(*) FROM statcast_pitches;
SELECT COUNT(*) FROM fangraphs_batting;
"
```

3. **Check API Rate Limits**
```bash
# Test with smaller date range
curl -X POST "http://localhost:18000/api/test/collect-data?date=2025-07-23"

# Check logs for rate limit messages
docker-compose logs python-service | grep -i "rate\|limit\|error"
```

## 🌐 Node.js Service Issues

### Authentication Problems

**Symptoms:**
- Login returns 401 errors
- JWT token invalid
- User not found errors

**Solutions:**

1. **Check User Database**
```bash
# Verify admin user exists
docker exec statedge_postgres psql -U statedge -d statedge -c "
SELECT id, email, subscription_tier FROM users;
"
```

2. **Reset Admin Password**
```bash
# Generate new password hash
docker exec statedge_node node -e "
const bcrypt = require('bcryptjs');
console.log(bcrypt.hashSync('admin123', 10));
"

# Update in database (replace HASH with output above)
docker exec statedge_postgres psql -U statedge -d statedge -c "
UPDATE users SET password_hash = 'HASH' WHERE email = 'admin@statedge.com';
"
```

3. **Check JWT Configuration**
```bash
# Verify JWT_SECRET is set
docker-compose logs node-service | grep -i jwt

# Test login endpoint
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@statedge.com", "password": "admin123"}'
```

## 📊 Database Issues

### Poor Query Performance

**Symptoms:**
- API responses > 5 seconds
- Database connection timeouts
- High CPU usage

**Solutions:**

1. **Check Database Stats**
```bash
# Monitor active connections
docker exec statedge_postgres psql -U statedge -d statedge -c "
SELECT COUNT(*) as active_connections FROM pg_stat_activity;
SELECT datname, numbackends FROM pg_stat_database WHERE datname = 'statedge';
"
```

2. **Analyze Slow Queries**
```bash
# Enable query logging (temporary)
docker exec statedge_postgres psql -U statedge -d statedge -c "
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
"

# View slow queries in logs
docker-compose logs postgres | grep -i "slow\|duration"
```

3. **Rebuild Indexes**
```bash
# Rebuild critical indexes
docker exec statedge_postgres psql -U statedge -d statedge -c "
REINDEX INDEX idx_statcast_game_date;
REINDEX INDEX idx_players_name;
ANALYZE statcast_pitches;
ANALYZE fangraphs_batting;
"
```

### Disk Space Issues

**Symptoms:**
- Database writes failing
- Docker build failures
- "No space left on device" errors

**Solutions:**

1. **Check Disk Usage**
```bash
# System disk space
df -h

# Docker space usage
docker system df

# Database size
docker exec statedge_postgres psql -U statedge -d statedge -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

2. **Clean Up Space**
```bash
# Clean Docker system
docker system prune -a  # CAUTION: Removes unused images

# Clean old data (CAUTION: Data loss)
docker exec statedge_postgres psql -U statedge -d statedge -c "
DELETE FROM statcast_pitches WHERE game_date < '2025-01-01';
VACUUM FULL statcast_pitches;
"
```

## 🔌 API Issues

### Slow Response Times

**Symptoms:**
- API calls take > 5 seconds
- Timeouts on large queries
- High server load

**Solutions:**

1. **Check Redis Cache**
```bash
# Test Redis connectivity
docker exec statedge_redis redis-cli ping

# Check cache hit rates
docker exec statedge_redis redis-cli info stats | grep -E "(hits|misses)"

# Clear cache if needed
docker exec statedge_redis redis-cli flushall
```

2. **Optimize Database Queries**
```bash
# Check query execution plans
docker exec statedge_postgres psql -U statedge -d statedge -c "
EXPLAIN ANALYZE SELECT * FROM players WHERE name ILIKE '%judge%';
"

# Update table statistics
docker exec statedge_postgres psql -U statedge -d statedge -c "
ANALYZE players;
ANALYZE statcast_pitches;
ANALYZE fangraphs_batting;
"
```

### CORS Issues

**Symptoms:**
- Browser console shows CORS errors
- Frontend can't connect to API
- Cross-origin request blocked

**Solutions:**

1. **Check CORS Configuration**
```bash
# View Python service CORS settings
docker-compose logs python-service | grep -i cors

# Test with curl (bypasses CORS)
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:18000/api/players/search
```

2. **Update CORS Settings**
```python
# In python-service/main.py, verify CORS middleware:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔄 Data Quality Issues

### Missing or Incorrect Data

**Symptoms:**
- Players showing wrong stats
- Recent games missing
- Statistical anomalies

**Solutions:**

1. **Verify Data Sources**
```bash
# Test PyBaseball directly
docker exec statedge_python python -c "
import pybaseball as pyb
batting = pyb.batting_stats(2025, 2025, qual=0)
print(f'FanGraphs batting: {len(batting)} players, {len(batting.columns)} columns')
"
```

2. **Check Data Collection Logs**
```bash
# View recent collection attempts
docker-compose logs python-service | grep -i "collect\|error" | tail -20

# Check database update timestamps
docker exec statedge_postgres psql -U statedge -d statedge -c "
SELECT 
    'statcast' as table_name,
    COUNT(*) as records,
    MAX(created_at) as last_update
FROM statcast_pitches
UNION ALL
SELECT 
    'fangraphs_batting',
    COUNT(*),
    MAX(created_at)
FROM fangraphs_batting;
"
```

3. **Recollect Data**
```bash
# Trigger fresh data collection
curl -X POST "http://localhost:18000/api/test/collect-fangraphs?season=2025"

# Check results
curl http://localhost:18000/api/test/database-stats
```

## 🖥️ Frontend Issues

### Page Won't Load

**Symptoms:**
- Blank page at localhost:3000
- JavaScript errors in browser console
- Build failures

**Solutions:**

1. **Check React Service**
```bash
# View frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend

# Test Node/npm versions
docker exec statedge_frontend node --version
docker exec statedge_frontend npm --version
```

2. **Check Dependencies**
```bash
# Install dependencies
docker exec statedge_frontend npm install

# Check for vulnerabilities
docker exec statedge_frontend npm audit
```

## 🛠️ Recovery Procedures

### Complete System Reset

If all else fails, completely reset StatEdge:

```bash
# 1. Stop all services
docker-compose down

# 2. Remove all containers and volumes (CAUTION: Data loss)
docker-compose down --volumes --remove-orphans

# 3. Clean Docker system
docker system prune -a

# 4. Rebuild everything
docker-compose up --build

# 5. Wait for initialization (2-3 minutes)
# 6. Test connectivity
curl http://localhost:18000/health
```

### Database Recovery

Restore database from backup:

```bash
# Create backup first
docker exec statedge_postgres pg_dump -U statedge statedge > backup.sql

# Restore from backup
cat backup.sql | docker exec -i statedge_postgres psql -U statedge -d statedge
```

### Data Re-collection

If data is corrupted or missing:

```bash
# 1. Clear affected tables
docker exec statedge_postgres psql -U statedge -d statedge -c "
TRUNCATE statcast_pitches, fangraphs_batting, fangraphs_pitching;
"

# 2. Recollect 2025 season data
curl -X POST "http://localhost:18000/api/test/collect-season-statcast?season=2025"
curl -X POST "http://localhost:18000/api/test/collect-fangraphs?season=2025"

# 3. Verify results
curl http://localhost:18000/api/test/2025-data-verification
```

## 📞 Getting Additional Help

### Log Collection

When reporting issues, include these logs:

```bash
# Collect comprehensive logs
mkdir troubleshooting-logs
docker-compose logs > troubleshooting-logs/all-services.log
docker-compose ps > troubleshooting-logs/service-status.txt
curl http://localhost:18000/api/test/database-stats > troubleshooting-logs/db-stats.json
docker system df > troubleshooting-logs/docker-usage.txt
```

### System Information

```bash
# System specs
echo "OS: $(uname -a)" > system-info.txt
echo "Docker: $(docker --version)" >> system-info.txt
echo "Docker Compose: $(docker-compose --version)" >> system-info.txt
echo "Memory: $(free -h)" >> system-info.txt
echo "Disk: $(df -h)" >> system-info.txt
```

### Contact Support

- **Documentation**: http://localhost:18000/docs
- **GitHub Issues**: Report bugs with logs attached
- **Email**: support@statedge.com (include system info and logs)

---

**Most issues can be resolved by restarting services or clearing cache. For persistent problems, the complete system reset procedure resolves 95% of issues.**