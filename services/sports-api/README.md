# Sports API Service

The core data service providing comprehensive baseball analytics through a high-performance FastAPI backend.

## Overview

The Sports API Service is the central hub for all baseball data in the StatEdge platform, serving 470k+ Statcast records, comprehensive FanGraphs metrics, and real-time analytics through a modern REST API.

## Service Details

- **Port**: 8000
- **Framework**: FastAPI (Python 3.11+)
- **Database**: Sports PostgreSQL (Port 5432)
- **Cache**: Redis (Port 6379)
- **Documentation**: Auto-generated OpenAPI docs at `/docs`

## Data Sources

### MLB Statcast Data (118 columns)
- **Volume**: 470,000+ pitch-level records
- **Coverage**: 2008-2025 seasons
- **Metrics**: Release velocity, spin rate, launch angle, exit velocity, movement data
- **Updates**: Real-time during games, daily historical backfill

### FanGraphs Advanced Metrics
- **Batting**: 320 columns including wOBA, wRC+, WAR, plate discipline, batted ball data
- **Pitching**: 393 columns including FIP, xFIP, SIERA, pitch values, command metrics
- **Fielding**: 60+ columns including UZR, DRS, OAA, zone ratings
- **Updates**: Daily during season

### Player Lookup System
- **Cross-referencing**: MLB AM, FanGraphs, Baseball Reference, Retrosheet IDs
- **Coverage**: 25,000+ players across MLB history
- **Purpose**: Unified player identification across all data sources

## API Endpoints

### Core Health & Status
```http
GET /health
GET /api/v1/status
```

### Player Data
```http
GET /api/v1/player/search?q={name}
GET /api/v1/player/profile/{player_id}
GET /api/v1/player/lookup/{mlb_id}
```

### Statcast Data
```http
GET /api/v1/statcast?limit=100&offset=0
GET /api/v1/statcast/player/{player_id}
GET /api/v1/statcast/game/{game_pk}
GET /api/v1/statcast/pitch-types
```

### FanGraphs Data
```http
GET /api/v1/fangraphs/batting?season=2024
GET /api/v1/fangraphs/pitching?season=2024
GET /api/v1/fangraphs/fielding?season=2024
GET /api/v1/fangraphs/player/{fangraphs_id}
```

### Analytics
```http
GET /api/v1/analytics/summary
GET /api/v1/analytics/leaderboards?stat=wRC+&limit=10
GET /api/v1/analytics/player-comparison
POST /api/v1/analytics/custom-query
```

## Development Setup

```bash
# Navigate to service directory
cd services/sports-api

# Install dependencies
pip install -r requirements.txt

# Start databases
docker-compose up -d sports-database redis

# Run development server
uvicorn main:app --reload --port 8000

# Access API documentation
open http://localhost:8000/docs
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data

# Redis
REDIS_URL=redis://redis:6379

# API Configuration
API_V1_STR=/api/v1
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

## Technology Stack

- **FastAPI**: Async REST API framework
- **PostgreSQL**: Primary data storage
- **Redis**: Caching and session storage
- **Pandas**: Data processing and analytics
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation and serialization

## Key Features

- **470k+ Statcast Records**: Complete pitch-level tracking data
- **320+ FanGraphs Metrics**: Comprehensive offensive statistics
- **Real-time Analytics**: Live game data processing
- **Player Cross-referencing**: Unified ID system across platforms
- **Sub-second Queries**: Optimized database performance
- **Auto-generated Docs**: OpenAPI specification

## Migration Notes

This service will migrate existing functionality from:
- `mlb-data-service/mlb_data_service/app.py`
- `mlb-data-service/mlb_data_service/enhanced_app.py`
- `mlb-data-service/mlb_data_service/enhanced_database.py`

Key components to migrate:
- Flask routes → FastAPI endpoints
- SQLite connections → PostgreSQL connections
- Player lookup logic
- FanGraphs data processing
- Statcast analytics

---

**Status**: 🚧 Ready for implementation - database and schema complete, awaiting service code migration.