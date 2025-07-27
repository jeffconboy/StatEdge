# 🔌 StatEdge API Reference

Complete reference documentation for the StatEdge Baseball Analytics API. All endpoints require authentication unless otherwise specified.

## 🔐 Authentication

StatEdge uses JWT (JSON Web Token) authentication. Obtain a token by logging in, then include it in the Authorization header for all requests.

### Base URLs

- **Python Data Service**: `http://localhost:18000`
- **Node.js API Gateway**: `http://localhost:3001`

### Authentication Flow

```bash
# 1. Login to get JWT token
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@statedge.com",
    "password": "admin123"
  }'

# Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "admin@statedge.com",
    "subscription_tier": "premium"
  }
}

# 2. Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:18000/api/players/search
```

## 📊 System Endpoints

### Health Check

Check system status and availability.

**GET** `/health`

```bash
curl http://localhost:18000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-25T03:37:39.041208"
}
```

### API Root

Get API information and available endpoints.

**GET** `/`

```bash
curl http://localhost:18000/
```

**Response:**
```json
{
  "message": "StatEdge Data Service API",
  "status": "running",
  "version": "1.0.0",
  "documentation": "/docs",
  "endpoints": {
    "players": "/api/players/",
    "analytics": "/api/analytics/",
    "ai": "/api/ai/",
    "data_collection": "/api/test/"
  }
}
```

## 👥 Player Endpoints

### Search Players

Search for players by name with fuzzy matching.

**POST** `/api/players/search`

**Request Body:**
```json
{
  "query": "Aaron Judge",
  "limit": 10
}
```

**Example:**
```bash
curl -X POST http://localhost:18000/api/players/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "Judge",
    "limit": 5
  }'
```

**Response:**
```json
[
  {
    "id": 1,
    "mlb_id": 592450,
    "name": "Aaron Judge",
    "team": "NYY",
    "position": "OF",
    "active": true,
    "bio": {
      "birthdate": "1992-04-26",
      "height": "6-7",
      "weight": 282,
      "bats": "R",
      "throws": "R"
    }
  }
]
```

### Get Player Statistics

Retrieve comprehensive statistics for a specific player.

**GET** `/api/players/{player_id}/stats`

**Query Parameters:**
- `stat_types` (string): Comma-separated list of stat types: `batting,pitching,statcast`
- `season` (integer): Specific season (default: current)
- `days_back` (integer): Days of recent data for Statcast (default: 30)

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:18000/api/players/1/stats?stat_types=batting,statcast&season=2025"
```

**Response:**
```json
{
  "player_info": {
    "id": 1,
    "mlb_id": 592450,
    "name": "Aaron Judge",
    "team": "NYY",
    "position": "OF"
  },
  "fangraphs_batting": [
    {
      "stats": {
        "G": 158,
        "AB": 559,
        "PA": 704,
        "H": 180,
        "HR": 56,
        "AVG": 0.322,
        "OBP": 0.458,
        "SLG": 0.701,
        "OPS": 1.159,
        "wRC+": 219,
        "WAR": 11.3
      },
      "season": 2025,
      "split_type": "season"
    }
  ],
  "statcast_data": [
    {
      "data": {
        "pitch_type": "FF",
        "release_speed": 97.2,
        "launch_speed": 105.3,
        "launch_angle": 12.0,
        "events": "single"
      },
      "game_date": "2025-07-23"
    }
  ]
}
```

### Player Summary

Get a quick performance summary for a player.

**GET** `/api/players/{player_id}/summary`

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:18000/api/players/1/summary
```

**Response:**
```json
{
  "player_info": {
    "name": "Aaron Judge",
    "team": "NYY",
    "position": "OF"
  },
  "statcast_summary": {
    "avg_exit_velocity": 95.8,
    "max_exit_velocity": 118.2,
    "barrel_rate": 0.205,
    "recent_games": 15
  },
  "fangraphs_batting": {
    "wRC+": 219,
    "WAR": 11.3,
    "OPS": 1.159
  },
  "recent_games": [
    {
      "date": "2025-07-23",
      "opponent": "BOS",
      "performance": "2-4, HR, 2 RBI"
    }
  ]
}
```

### Bulk Player Stats

Get statistics for multiple players at once.

**POST** `/api/players/bulk-stats`

**Request Body:**
```json
{
  "player_ids": [1, 2, 3],
  "stat_types": ["batting", "statcast"]
}
```

**Example:**
```bash
curl -X POST http://localhost:18000/api/players/bulk-stats \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "player_ids": [1, 2, 3],
    "stat_types": ["batting"]
  }'
```

### Trending Players

Get players with highest recent activity.

**GET** `/api/players/trending`

**Query Parameters:**
- `limit` (integer): Number of players to return (default: 10)

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:18000/api/players/trending?limit=5"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Aaron Judge",
    "team": "NYY",
    "position": "OF",
    "recent_activity": 47
  }
]
```

## 📈 Data Collection Endpoints

### Manual Data Collection

Trigger manual data collection for a specific date.

**POST** `/api/test/collect-data`

**Query Parameters:**
- `date` (string): Date in YYYY-MM-DD format (optional, defaults to yesterday)

**Example:**
```bash
curl -X POST "http://localhost:18000/api/test/collect-data?date=2025-07-23" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "Data collection completed for 2025-07-23",
  "timestamp": "2025-07-25T03:27:10.906736"
}
```

**Data Collected:**
- Statcast pitch-by-pitch data (118 fields per pitch)
- MLB game schedules and lineups
- Player information updates

**Rate Limits:** 10 requests per hour, 30-120 seconds per request

### FanGraphs Data Collection

Collect comprehensive FanGraphs statistics for a season.

**POST** `/api/test/collect-fangraphs`

**Query Parameters:**
- `season` (integer): MLB season year (default: 2025)

**Example:**
```bash
curl -X POST "http://localhost:18000/api/test/collect-fangraphs?season=2025" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "FanGraphs data collection completed for 2025",
  "timestamp": "2025-07-25T03:27:30.194036"
}
```

**Data Collected:**
- **Batting Statistics**: 320+ fields including wRC+, wOBA, WAR
- **Pitching Statistics**: 393+ fields including FIP, xFIP, SIERA
- **Player Information**: Names, teams, positions, ages

**Typical Results:**
- 1,300+ batting players per season
- 750+ pitching players per season

**Rate Limits:** 1 request per hour, 15-30 seconds processing time

### Bulk Season Collection

Collect complete season Statcast data in batches.

**POST** `/api/test/collect-season-statcast`

**Query Parameters:**
- `season` (integer): Season year (default: 2025)
- `batch_days` (integer): Days per batch (default: 7)

**Example:**
```bash
curl -X POST "http://localhost:18000/api/test/collect-season-statcast?season=2025&batch_days=14" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "Season 2025 Statcast collection completed",
  "total_records_collected": 458469,
  "batches_processed": 11,
  "date_range": "2025-03-01 to 2025-07-25",
  "timestamp": "2025-07-25T03:35:57.969099"
}
```

**Process:**
- Collects data in configurable batch sizes
- Handles API rate limits automatically
- Provides progress tracking
- Covers complete season date range

**Rate Limits:** 1 request per day, 5-30 minutes processing time

## 📊 Database Statistics

### Current Database Stats

Get overview of all data in the database.

**GET** `/api/test/database-stats`

**Example:**
```bash
curl http://localhost:18000/api/test/database-stats
```

**Response:**
```json
{
  "total_players": 1693,
  "total_statcast_pitches": 493231,
  "total_fangraphs_batting_players": 2772,
  "total_fangraphs_pitching_players": 1620,
  "statcast_2025_records": 493097,
  "fangraphs_2025_batting_players": 1322,
  "fangraphs_2025_pitching_players": 766,
  "statcast_date_range": {
    "earliest": "2024-07-04",
    "latest": "2025-07-23"
  },
  "timestamp": "2025-07-25T03:28:19.584583"
}
```

### 2025 Data Verification

Comprehensive verification of current season data completeness.

**GET** `/api/test/2025-data-verification`

**Example:**
```bash
curl http://localhost:18000/api/test/2025-data-verification
```

**Response:**
```json
{
  "2025_statcast_data": {
    "total_pitches": 493097,
    "unique_games": 1685,
    "unique_batters": 1414,
    "unique_pitchers": 1123,
    "date_range": {
      "earliest": "2025-03-15",
      "latest": "2025-07-23"
    },
    "monthly_breakdown": [
      {
        "month": "Mar",
        "pitch_count": 63740,
        "game_count": 216
      },
      {
        "month": "Apr",
        "pitch_count": 114857,
        "game_count": 391
      },
      {
        "month": "May",
        "pitch_count": 120230,
        "game_count": 411
      },
      {
        "month": "Jun",
        "pitch_count": 115908,
        "game_count": 397
      },
      {
        "month": "Jul",
        "pitch_count": 78362,
        "game_count": 270
      }
    ],
    "sample_field_count": 118
  },
  "2025_fangraphs_data": {
    "batting_players": 1322,
    "pitching_players": 766,
    "batting_fields": 320,
    "pitching_fields": 393
  },
  "data_quality": {
    "statcast_completeness": "100%",
    "fangraphs_completeness": "100%",
    "collection_status": "Complete - All 2025 data collected successfully"
  },
  "summary": {
    "total_2025_records": 495185,
    "data_coverage": "Full season through July 25, 2025",
    "last_updated": "2025-07-25T03:37:39.041208"
  }
}
```

## 🤖 AI Analytics Endpoints

### AI Chat

Natural language queries for baseball analytics.

**POST** `/api/ai/chat`

**Request Body:**
```json
{
  "message": "Show me Aaron Judge's home runs vs left-handed pitching this season",
  "context": "betting_analysis"
}
```

**Example:**
```bash
curl -X POST http://localhost:18000/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Compare Mookie Betts and Ronald Acuña Jr batting stats",
    "context": "player_comparison"
  }'
```

**Response:**
```json
{
  "response": "Based on 2025 statistics, here's how Mookie Betts and Ronald Acuña Jr compare...",
  "data_used": {
    "players": ["Mookie Betts", "Ronald Acuña Jr"],
    "stats_compared": ["AVG", "OBP", "SLG", "HR", "SB", "WAR"],
    "season": 2025
  },
  "confidence": 0.95,
  "follow_up_questions": [
    "Would you like to see their head-to-head matchup history?",
    "How do they perform in clutch situations?"
  ]
}
```

### Betting Analysis

AI-powered betting insights and recommendations.

**POST** `/api/ai/betting-analysis`

**Request Body:**
```json
{
  "player_name": "Aaron Judge",
  "bet_type": "home_run",
  "game_context": {
    "opponent": "BOS",
    "pitcher": "Chris Sale",
    "ballpark": "Yankee Stadium"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:18000/api/ai/betting-analysis \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "player_name": "Shohei Ohtani",
    "bet_type": "strikeouts",
    "game_context": {
      "opposing_team": "HOU"
    }
  }'
```

**Response:**
```json
{
  "recommendation": "OVER 7.5 strikeouts",
  "confidence": 0.78,
  "reasoning": [
    "Ohtani averages 11.2 K/9 this season",
    "Houston ranks 3rd in team strikeout rate",
    "Ohtani has 8+ strikeouts in 68% of starts vs AL West"
  ],
  "key_stats": {
    "season_k_per_9": 11.2,
    "vs_opponent_avg": 8.7,
    "recent_form": "12 K in last start"
  },
  "risk_factors": [
    "Pitch count may be limited due to recent high usage",
    "Houston has improved plate discipline in July"
  ]
}
```

## 📊 Analytics Endpoints

### Player Comparisons

Compare multiple players across various metrics.

**POST** `/api/analytics/compare-players`

**Request Body:**
```json
{
  "player_ids": [1, 2, 3],
  "stat_categories": ["batting", "statcast"],
  "season": 2025
}
```

### Team Analytics  

Get team-level statistics and insights.

**GET** `/api/analytics/team-stats/{team_code}`

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:18000/api/analytics/team-stats/NYY
```

### Advanced Metrics

Calculate advanced sabermetric statistics.

**POST** `/api/analytics/advanced-metrics`

**Request Body:**
```json
{
  "player_id": 1,
  "metric_type": "expected_stats",
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-07-25"
  }
}
```

## 🚨 Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "detail": "Error description",
  "error_code": "PLAYER_NOT_FOUND",
  "timestamp": "2025-07-25T03:37:39.041208"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Common Error Scenarios

#### Authentication Errors
```json
{
  "detail": "Invalid or expired token",
  "error_code": "INVALID_TOKEN"
}
```

#### Rate Limiting
```json
{
  "detail": "Rate limit exceeded. Try again in 3600 seconds",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 3600
}
```

#### Data Not Found
```json
{
  "detail": "Player not found",
  "error_code": "PLAYER_NOT_FOUND"
}
```

## 🔄 Rate Limits

### Endpoint Rate Limits

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Player Search | 100/hour | Rolling |
| Statistics | 200/hour | Rolling |
| Data Collection | 10/hour | Rolling |
| Bulk Operations | 1/hour | Rolling |
| AI Analytics | 50/hour | Rolling |

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1643723400
```

## 📝 Interactive Documentation

### Swagger UI

Complete interactive API documentation with request/response examples:

**URL:** http://localhost:18000/docs

Features:
- Try endpoints directly in the browser
- Authentication support
- Request/response examples
- Schema definitions
- Error code documentation

### ReDoc

Alternative documentation format:

**URL:** http://localhost:18000/redoc

### OpenAPI Schema

Raw OpenAPI 3.0 specification:

**URL:** http://localhost:18000/openapi.json

## 🔧 SDK and Client Libraries

### cURL Examples

All examples in this documentation use cURL for maximum compatibility.

### Python Client

```python
import requests

class StatEdgeClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def search_players(self, query, limit=10):
        response = requests.post(
            f"{self.base_url}/api/players/search",
            json={"query": query, "limit": limit},
            headers=self.headers
        )
        return response.json()

# Usage
client = StatEdgeClient("http://localhost:18000", "your_token")
players = client.search_players("Aaron Judge")
```

### JavaScript Client

```javascript
class StatEdgeAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async searchPlayers(query, limit = 10) {
    const response = await fetch(`${this.baseURL}/api/players/search`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ query, limit })
    });
    return response.json();
  }
}

// Usage
const api = new StatEdgeAPI('http://localhost:18000', 'your_token');
const players = await api.searchPlayers('Aaron Judge');
```

---

**For additional support or questions about the API, visit the interactive documentation at `/docs` or contact the development team.**