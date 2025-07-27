# API Documentation

## StatEdge Betting Service API Reference

### Base URL
```
http://localhost:18002
```

### Authentication
No authentication required (personal use service)

### Response Format
All endpoints return JSON responses with consistent structure:

```json
{
  "success": true,
  "data": {...},
  "message": "Success message",
  "timestamp": "2025-07-26T19:30:00Z"
}
```

Error responses:
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

---

## System Endpoints

### Health Check
**GET** `/health`

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-26T19:30:00Z",
  "service": "betting-service"
}
```

### Service Info
**GET** `/`

Get basic service information and available endpoints.

**Response:**
```json
{
  "message": "StatEdge Betting Service",
  "status": "running",
  "version": "1.0.0",
  "documentation": "/docs",
  "endpoints": {
    "bets": "/api/bets/",
    "analytics": "/api/analytics/",
    "strategies": "/api/strategies/",
    "bankroll": "/api/bankroll/"
  }
}
```

---

## Bets API

### Create Bet
**POST** `/api/bets/`

Create a new betting prediction.

**Request Body:**
```json
{
  "game_id": "20250726_BOS@NYY",
  "sport": "MLB",
  "home_team": "NYY",
  "away_team": "BOS",
  "game_date": "2025-07-26",
  "game_time": "19:05:00",
  "bet_type": "moneyline",
  "bet_side": "home",
  "bet_amount": 50.00,
  "odds": -150,
  "confidence_level": 7,
  "prediction_reasoning": "Yankees have better starting pitcher",
  "predicted_score_home": 6,
  "predicted_score_away": 4,
  "category_ids": [1, 2],
  "strategy_ids": [3],
  "notes": "Home field advantage"
}
```

**Required Fields:**
- `game_id`: Unique game identifier
- `home_team`: Home team abbreviation
- `away_team`: Away team abbreviation  
- `game_date`: Game date (YYYY-MM-DD)
- `bet_type`: "moneyline", "spread", "total", "prop"
- `bet_side`: "home", "away", "over", "under", "yes", "no"
- `bet_amount`: Amount wagered (> 0)
- `confidence_level`: Integer from 1-10

**Response:**
```json
{
  "id": 123,
  "game_id": "20250726_BOS@NYY",
  "sport": "MLB",
  "home_team": "NYY",
  "away_team": "BOS",
  "game_date": "2025-07-26",
  "bet_type": "moneyline",
  "bet_side": "home",
  "bet_amount": 50.00,
  "odds": -150,
  "implied_probability": 60.00,
  "confidence_level": 7,
  "game_status": "pending",
  "created_at": "2025-07-26T15:30:00Z",
  "updated_at": "2025-07-26T15:30:00Z"
}
```

### Get Betting History
**GET** `/api/bets/`

Retrieve betting history with optional filters.

**Query Parameters:**
- `limit` (int): Number of bets to return (default: 50)
- `offset` (int): Number of bets to skip (default: 0)
- `sport` (string): Filter by sport
- `bet_type` (string): Filter by bet type
- `game_status` (string): Filter by status ("pending", "completed", "cancelled")
- `start_date` (date): Start date filter (YYYY-MM-DD)
- `end_date` (date): End date filter (YYYY-MM-DD)

**Example:**
```
GET /api/bets/?limit=10&bet_type=moneyline&start_date=2025-07-01
```

**Response:**
```json
[
  {
    "id": 123,
    "game_id": "20250726_BOS@NYY",
    "home_team": "NYY",
    "away_team": "BOS",
    "game_date": "2025-07-26",
    "bet_type": "moneyline",
    "bet_side": "home",
    "bet_amount": 50.00,
    "bet_result": "win",
    "payout": 83.33,
    "profit_loss": 33.33,
    "created_at": "2025-07-26T15:30:00Z"
  }
]
```

### Get Specific Bet
**GET** `/api/bets/{bet_id}`

Get details for a specific bet.

**Response:**
```json
{
  "id": 123,
  "game_id": "20250726_BOS@NYY",
  "sport": "MLB",
  "home_team": "NYY",
  "away_team": "BOS",
  "game_date": "2025-07-26",
  "bet_type": "moneyline",
  "bet_side": "home",
  "bet_amount": 50.00,
  "odds": -150,
  "confidence_level": 7,
  "prediction_reasoning": "Yankees have better starting pitcher",
  "actual_score_home": 6,
  "actual_score_away": 4,
  "bet_result": "win",
  "payout": 83.33,
  "game_status": "completed",
  "created_at": "2025-07-26T15:30:00Z",
  "updated_at": "2025-07-26T22:30:00Z"
}
```

### Update Bet
**PATCH** `/api/bets/{bet_id}`

Update bet details before game completion.

**Request Body:**
```json
{
  "confidence_level": 8,
  "prediction_reasoning": "Updated analysis - even stronger case",
  "predicted_score_home": 7,
  "predicted_score_away": 3,
  "notes": "Added bullpen analysis",
  "category_ids": [1, 3],
  "strategy_ids": [2, 4]
}
```

**Note:** Only pending bets can be updated.

### Settle Bet
**POST** `/api/bets/{bet_id}/settle`

Record the outcome of a completed game.

**Request Body:**
```json
{
  "actual_score_home": 6,
  "actual_score_away": 4,
  "bet_result": "win",
  "payout": 83.33,
  "notes": "Great pitching performance as predicted"
}
```

**Bet Results:**
- `"win"`: Bet won
- `"loss"`: Bet lost
- `"push"`: Tie/push (refunded)
- `"void"`: Voided bet

### Delete Bet
**DELETE** `/api/bets/{bet_id}`

Delete a pending bet (completed bets cannot be deleted).

**Response:**
```json
{
  "message": "Bet deleted successfully"
}
```

### Betting Summary
**GET** `/api/bets/summary/stats`

Get overall betting performance statistics.

**Query Parameters:**
- `start_date` (date): Start date for analysis
- `end_date` (date): End date for analysis

**Response:**
```json
{
  "total_bets": 150,
  "wins": 85,
  "losses": 60,
  "pushes": 5,
  "win_percentage": 58.62,
  "total_wagered": 7500.00,
  "total_profit": 1250.00,
  "roi_percentage": 16.67,
  "by_bet_type": {
    "moneyline": {
      "total_bets": 75,
      "wins": 45,
      "losses": 30,
      "win_percentage": 60.00,
      "roi": 18.50
    }
  },
  "by_sport": {
    "MLB": {
      "total_bets": 150,
      "wins": 85,
      "win_percentage": 58.62,
      "roi": 16.67
    }
  }
}
```

---

## Analytics API

### Performance Summary
**GET** `/api/analytics/summary`

Get overall performance summary for specified period.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Response:**
```json
{
  "period": "30 days",
  "total_bets": 45,
  "wins": 28,
  "losses": 15,
  "pushes": 2,
  "win_rate": 65.12,
  "total_wagered": 2250.00,
  "total_profit": 425.00,
  "roi": 18.89,
  "average_confidence": 6.8
}
```

### Performance Trends
**GET** `/api/analytics/trends`

Get performance trends over time.

**Query Parameters:**
- `period` (string): Grouping period ("day", "week", "month")

**Response:**
```json
[
  {
    "period": "2025-07-20",
    "bets_count": 5,
    "wins": 3,
    "win_rate": 60.00,
    "wagered": 250.00,
    "profit": 45.00,
    "roi": 18.00
  },
  {
    "period": "2025-07-19",
    "bets_count": 3,
    "wins": 2,
    "win_rate": 66.67,
    "wagered": 150.00,
    "profit": 30.00,
    "roi": 20.00
  }
]
```

### Confidence Analysis
**GET** `/api/analytics/confidence-analysis`

Analyze performance by confidence level.

**Response:**
```json
[
  {
    "confidence_level": 8,
    "bet_count": 25,
    "wins": 18,
    "win_rate": 72.00,
    "total_wagered": 1250.00,
    "total_profit": 325.00,
    "roi": 26.00,
    "avg_bet_size": 50.00
  },
  {
    "confidence_level": 7,
    "bet_count": 35,
    "wins": 20,
    "win_rate": 57.14,
    "total_wagered": 1750.00,
    "total_profit": 180.00,
    "roi": 10.29,
    "avg_bet_size": 50.00
  }
]
```

### Bet Type Performance
**GET** `/api/analytics/bet-type-performance`

Performance breakdown by bet type.

**Response:**
```json
[
  {
    "bet_type": "moneyline",
    "bet_count": 75,
    "wins": 45,
    "losses": 28,
    "pushes": 2,
    "win_rate": 61.64,
    "total_wagered": 3750.00,
    "total_profit": 650.00,
    "roi": 17.33,
    "avg_bet_size": 50.00,
    "avg_confidence": 7.2
  },
  {
    "bet_type": "total",
    "bet_count": 40,
    "wins": 22,
    "losses": 18,
    "pushes": 0,
    "win_rate": 55.00,
    "total_wagered": 2000.00,
    "total_profit": 180.00,
    "roi": 9.00,
    "avg_bet_size": 50.00,
    "avg_confidence": 6.5
  }
]
```

### Recent Activity
**GET** `/api/analytics/recent-activity`

Get recent betting activity and results.

**Query Parameters:**
- `limit` (int): Number of recent bets to return (default: 10)

**Response:**
```json
[
  {
    "game_id": "20250726_BOS@NYY",
    "matchup": "BOS @ NYY",
    "game_date": "2025-07-26",
    "bet_type": "moneyline",
    "bet_side": "home",
    "bet_amount": 50.00,
    "odds": -150,
    "confidence": 7,
    "result": "win",
    "payout": 83.33,
    "profit": 33.33,
    "final_score": "4-6",
    "created_at": "2025-07-26T15:30:00Z"
  }
]
```

---

## Strategies API

### Get All Strategies
**GET** `/api/strategies/`

Get all betting strategies with performance metrics.

**Response:**
```json
[
  {
    "id": 1,
    "strategy_name": "Home Favorite",
    "description": "Bet on home teams favored by 1-2 runs",
    "criteria": {
      "max_spread": 2,
      "team_location": "home",
      "min_confidence": 6
    },
    "total_bets": 25,
    "wins": 16,
    "losses": 8,
    "pushes": 1,
    "total_wagered": 1250.00,
    "total_profit": 285.00,
    "win_rate": 66.67,
    "roi": 22.80,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-07-26T22:30:00Z"
  }
]
```

### Create Strategy
**POST** `/api/strategies/`

Create a new betting strategy.

**Request Body:**
```json
{
  "strategy_name": "Road Underdogs",
  "description": "Bet on away teams getting +150 or better odds",
  "criteria": {
    "min_odds": 150,
    "team_location": "away",
    "max_spread": 2.5
  }
}
```

### Get Strategy Details
**GET** `/api/strategies/{strategy_id}`

Get specific strategy with performance metrics.

### Update Strategy
**PUT** `/api/strategies/{strategy_id}`

Update strategy details.

### Delete Strategy
**DELETE** `/api/strategies/{strategy_id}`

Delete a strategy (removes mappings but keeps bet history).

### Get Strategy Bets
**GET** `/api/strategies/{strategy_id}/bets`

Get all bets that used this strategy.

### Strategy Performance Analysis
**GET** `/api/strategies/{strategy_id}/performance`

Get detailed performance analysis for a strategy.

**Response:**
```json
{
  "strategy": {
    "id": 1,
    "name": "Home Favorite",
    "description": "Bet on home teams favored by 1-2 runs",
    "criteria": {...}
  },
  "overall_performance": {
    "total_bets": 25,
    "wins": 16,
    "win_rate": 66.67,
    "roi": 22.80
  },
  "monthly_performance": [
    {
      "month": "2025-07",
      "bets_count": 8,
      "wins": 6,
      "win_rate": 75.00,
      "roi": 28.50
    }
  ],
  "bet_type_breakdown": [
    {
      "bet_type": "moneyline",
      "bets_count": 20,
      "win_rate": 70.00,
      "roi": 25.00
    }
  ]
}
```

---

## Bankroll API

### Add Bankroll Entry
**POST** `/api/bankroll/`

Record daily bankroll information.

**Request Body:**
```json
{
  "date": "2025-07-26",
  "starting_balance": 1000.00,
  "ending_balance": 1050.00,
  "total_wagered": 200.00,
  "number_of_bets": 3,
  "notes": "Good day with 2 wins"
}
```

**Response:**
```json
{
  "id": 123,
  "date": "2025-07-26",
  "starting_balance": 1000.00,
  "ending_balance": 1050.00,
  "daily_pnl": 50.00,
  "total_wagered": 200.00,
  "number_of_bets": 3,
  "notes": "Good day with 2 wins",
  "created_at": "2025-07-26T23:00:00Z"
}
```

### Get Bankroll History
**GET** `/api/bankroll/`

Get bankroll history with optional date range.

**Query Parameters:**
- `start_date` (date): Start date filter
- `end_date` (date): End date filter
- `limit` (int): Number of entries to return (default: 30)

### Bankroll Summary
**GET** `/api/bankroll/summary`

Get bankroll performance summary.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Response:**
```json
{
  "period": "30 days",
  "current_balance": 1250.00,
  "last_updated": "2025-07-26",
  "period_return": 25.00,
  "total_pnl": 250.00,
  "total_wagered": 3000.00,
  "total_bets": 45,
  "avg_daily_pnl": 8.33,
  "best_day": 125.00,
  "worst_day": -75.00,
  "positive_days": 18,
  "negative_days": 8,
  "total_days": 30
}
```

### Bankroll Chart Data
**GET** `/api/bankroll/chart-data`

Get bankroll data formatted for charts.

**Query Parameters:**
- `days` (int): Number of days to include (default: 30)

**Response:**
```json
{
  "data": [
    {
      "date": "2025-07-01",
      "balance": 1000.00,
      "daily_pnl": 0.00,
      "cumulative_pnl": 0.00,
      "wagered": 0.00,
      "bets": 0
    },
    {
      "date": "2025-07-02",
      "balance": 1025.00,
      "daily_pnl": 25.00,
      "cumulative_pnl": 25.00,
      "wagered": 100.00,
      "bets": 2
    }
  ],
  "period": "30 days",
  "total_points": 30
}
```

### Delete Bankroll Entry
**DELETE** `/api/bankroll/{entry_date}`

Delete a bankroll entry for a specific date.

---

## Games & Odds API

### Today's Games
**GET** `/api/games/today`

Get today's MLB games with current odds.

**Response:**
```json
{
  "success": true,
  "games": [
    {
      "game_id": "20250726_BOS@NYY",
      "home_team": "NYY",
      "away_team": "BOS",
      "game_time": "7:05p",
      "game_date": "20250726",
      "game_status": "scheduled",
      "odds": {
        "home_ml": -150,
        "away_ml": 130,
        "home_spread": -1.5,
        "total_over": 8.5,
        "total_under": 8.5
      }
    }
  ],
  "count": 15,
  "date": "20250726",
  "timestamp": "2025-07-26T19:30:00Z"
}
```

### Game Odds
**GET** `/api/games/{game_id}/odds`

Get current odds for a specific game.

**Response:**
```json
{
  "success": true,
  "game_id": "20250726_BOS@NYY",
  "home_team": "NYY",
  "away_team": "BOS",
  "odds": {
    "moneyline": {
      "home": -150,
      "away": 130
    },
    "spread": {
      "home": {
        "line": -1.5,
        "odds": 110
      },
      "away": {
        "line": 1.5,
        "odds": -110
      }
    },
    "total": {
      "over": {
        "line": 8.5,
        "odds": -110
      },
      "under": {
        "line": 8.5,
        "odds": -110
      }
    }
  },
  "last_updated": "2025-07-26T19:30:00Z"
}
```

---

## Error Handling

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **404**: Not Found
- **422**: Unprocessable Entity (validation error)
- **500**: Internal Server Error

### Error Response Format

```json
{
  "detail": "Validation error message",
  "status_code": 400
}
```

### Common Validation Errors

**Bet Creation Errors:**
```json
{
  "detail": "Confidence level must be between 1 and 10",
  "status_code": 422
}
```

**Update Errors:**
```json
{
  "detail": "Cannot update completed bet",
  "status_code": 400
}
```

**Not Found Errors:**
```json
{
  "detail": "Bet not found",
  "status_code": 404
}
```

---

## Rate Limits

No rate limits are enforced for personal use, but reasonable usage is expected:

- Maximum 1000 requests per hour
- Maximum 100 bet creations per day
- Maximum 50 concurrent requests

---

## Interactive Documentation

Visit http://localhost:18002/docs for interactive API documentation with:
- Request/response examples
- Try-it-out functionality
- Schema definitions
- Authentication details

---

## SDK Examples

### Python SDK Example

```python
import requests
from datetime import date

class BettingAPI:
    def __init__(self, base_url="http://localhost:18002"):
        self.base_url = base_url
    
    def create_bet(self, bet_data):
        response = requests.post(f"{self.base_url}/api/bets/", json=bet_data)
        return response.json()
    
    def get_performance_summary(self, days=30):
        response = requests.get(f"{self.base_url}/api/analytics/summary?days={days}")
        return response.json()
    
    def settle_bet(self, bet_id, outcome):
        response = requests.post(f"{self.base_url}/api/bets/{bet_id}/settle", json=outcome)
        return response.json()

# Usage
api = BettingAPI()

# Create a bet
bet = api.create_bet({
    "game_id": "20250726_BOS@NYY",
    "home_team": "NYY",
    "away_team": "BOS", 
    "game_date": date.today().isoformat(),
    "bet_type": "moneyline",
    "bet_side": "home",
    "bet_amount": 50.00,
    "confidence_level": 7
})

# Get performance
stats = api.get_performance_summary(days=30)
print(f"Win Rate: {stats['win_rate']}%")
```

---

This API documentation provides comprehensive coverage of all endpoints and their usage. For the most up-to-date documentation, always refer to the interactive docs at `/docs`.