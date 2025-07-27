# ⚾ StatEdge - Advanced Baseball Analytics Platform

StatEdge is a comprehensive baseball analytics platform that combines real-time Statcast data with advanced FanGraphs statistics to provide actionable insights for sports betting and baseball analysis.

## 🎯 Features

- **Complete 2025 Season Data**: 493k+ Statcast pitch records with 118 fields each
- **Comprehensive Player Statistics**: 2,088+ players with 300+ advanced metrics
- **Real-time Data Collection**: Automated daily updates from MLB data sources
- **AI-Powered Analytics**: OpenAI integration for intelligent insights
- **Microservices Architecture**: Scalable Docker-based infrastructure
- **RESTful API**: Full-featured API for data access and analysis

## 🏗️ Architecture

StatEdge uses a microservices architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   Node.js API   │    │  Python Service │
│   Port: 3000     │◄──►│   Gateway       │◄──►│   FastAPI       │
│                 │    │   Port: 3001    │    │   Port: 18000   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                    ┌─────────────────┐    ┌─────────────────┐
                    │   PostgreSQL    │    │     Redis       │
                    │   Database      │    │     Cache       │
                    │   Port: 15432   │    │   Port: 16379   │
                    └─────────────────┘    └─────────────────┘
```

### Services Overview

| Service | Technology | Purpose | Port |
|---------|------------|---------|------|
| **Frontend** | React + Tailwind CSS | User interface and visualization | 3000 |
| **API Gateway** | Node.js + Express | Authentication and routing | 3001 |
| **Data Service** | Python + FastAPI | Data collection and processing | 18000 |
| **Database** | PostgreSQL | Primary data storage | 15432 |
| **Cache** | Redis | Session and performance caching | 16379 |

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 16GB+ RAM recommended
- 10GB+ available disk space

### 1. Clone and Setup

```bash
git clone <repository-url>
cd StatEdge
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start all 5 services automatically. First-time setup takes 2-3 minutes.

### 3. Verify Installation

```bash
# Check all services are running
docker-compose ps

# Test API connectivity
curl http://localhost:18000/health
curl http://localhost:3001/health
```

### 4. Access the Platform

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:3001
- **Python API Docs**: http://localhost:18000/docs
- **Database**: localhost:15432 (user: statedge, db: statedge)

## 📊 Data Sources

### Statcast Data
- **Source**: MLB Advanced Media via PyBaseball
- **Coverage**: Complete 2025 season (493k+ pitch records)
- **Fields**: 118 metrics per pitch including:
  - Velocity, spin rate, release point
  - Launch angle, exit velocity, hit distance
  - Strike zone coordinates
  - Pitch outcome and result

### FanGraphs Data
- **Source**: FanGraphs.com via PyBaseball
- **Coverage**: 2,088+ active MLB players
- **Batting Stats**: 320+ fields including wRC+, wOBA, WAR
- **Pitching Stats**: 393+ fields including FIP, xFIP, SIERA

## 🔧 Configuration

### Environment Variables

Create `.env` files in each service directory:

#### Python Service (.env)
```bash
DATABASE_URL=postgresql://statedge:statedge123@postgres:5432/statedge
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=your_openai_key_here
JWT_SECRET=your_jwt_secret_here
```

#### Node.js Service (.env)
```bash
DATABASE_URL=postgresql://statedge:statedge123@postgres:5432/statedge
JWT_SECRET=your_jwt_secret_here
PYTHON_SERVICE_URL=http://python-service:8000
```

### Database Configuration

The PostgreSQL database is automatically initialized with:
- Complete schema for baseball statistics
- Sample data for testing
- Proper indexes for performance
- JSONB storage for flexible stat structures

## 🔌 API Usage

### Authentication

All API endpoints require JWT authentication:

```bash
# Login to get token
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@statedge.com", "password": "admin123"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:18000/api/players/search
```

### Key Endpoints

#### Player Search
```bash
POST /api/players/search
{
  "query": "Aaron Judge",
  "limit": 10
}
```

#### Player Statistics
```bash
GET /api/players/{player_id}/stats?stat_types=batting,pitching,statcast
```

#### Data Collection
```bash
# Collect data for specific date
POST /api/test/collect-data?date=2025-07-23

# Collect FanGraphs season data
POST /api/test/collect-fangraphs?season=2025

# Bulk season collection
POST /api/test/collect-season-statcast?season=2025
```

#### Database Statistics
```bash
GET /api/test/database-stats
GET /api/test/2025-data-verification
```

## 📈 Current Data Status

As of the latest update, StatEdge contains:

| Data Type | Records | Coverage |
|-----------|---------|----------|
| **Statcast Pitches** | 493,231 | Complete 2025 season |
| **FanGraphs Batting** | 1,322 players | All qualified batters |
| **FanGraphs Pitching** | 766 players | All qualified pitchers |
| **Total Players** | 1,693 | Active MLB roster |
| **Games Covered** | 1,685 | March - July 2025 |

### Monthly Breakdown (2025 Season)
- **March**: 63,740 pitches (216 games)
- **April**: 114,857 pitches (391 games)  
- **May**: 120,230 pitches (411 games)
- **June**: 115,908 pitches (397 games)
- **July**: 78,362 pitches (270 games)

## 🛠️ Development

### Running in Development Mode

```bash
# Start only database services
docker-compose up -d postgres redis

# Run Python service locally
cd python-service
pip install -r requirements.txt
uvicorn main:app --reload --port 18000

# Run Node.js service locally  
cd node-service
npm install
npm run dev

# Run React frontend locally
cd frontend
npm install
npm start
```

### Adding New Data Sources

1. Create new collection method in `python-service/services/data_collector.py`
2. Add database schema updates in `database/init.sql`
3. Create API endpoints in appropriate router
4. Add tests and documentation

### Database Management

```bash
# Connect to database
docker exec -it statedge_postgres psql -U statedge -d statedge

# View table schemas
\dt
\d+ statcast_pitches
\d+ fangraphs_batting

# Check data counts
SELECT COUNT(*) FROM statcast_pitches WHERE game_date >= '2025-01-01';
```

## 📋 API Documentation

Complete interactive API documentation is available at:
- **Swagger UI**: http://localhost:18000/docs
- **ReDoc**: http://localhost:18000/redoc
- **OpenAPI Schema**: http://localhost:18000/openapi.json

## 🔒 Security

- JWT-based authentication with bcrypt password hashing
- CORS protection with allowed origins
- SQL injection protection via parameterized queries
- Rate limiting on data collection endpoints
- Environment variable protection for secrets

## 📊 Monitoring & Health Checks

```bash
# Check service health
curl http://localhost:18000/health
curl http://localhost:3001/health

# Monitor data collection
curl http://localhost:18000/api/test/database-stats

# View service logs
docker-compose logs python-service
docker-compose logs node-service
```

## 🧪 Testing

```bash
# Test data collection pipeline
curl -X POST http://localhost:18000/api/test/collect-data?date=2025-07-23

# Verify data quality
curl http://localhost:18000/api/test/2025-data-verification

# Test player search
curl -X POST http://localhost:18000/api/players/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Judge", "limit": 5}'
```

## 🚀 Deployment

### Production Checklist

- [ ] Update all environment variables with production values
- [ ] Enable SSL/TLS certificates
- [ ] Configure production database with backups
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Enable rate limiting and security headers
- [ ] Set up CI/CD pipeline

### Docker Production

```bash
# Build for production
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Additional Documentation

- [Database Schema](docs/database-schema.md)
- [API Reference](docs/api-reference.md) 
- [Data Collection Guide](docs/data-collection.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Support

For technical support or questions:
- **Documentation**: http://localhost:18000/docs
- **GitHub Issues**: Create an issue for bugs or feature requests
- **Email**: support@statedge.com

## 📄 License

Private License - All rights reserved.

---

**Built with ⚾ by the StatEdge Team**