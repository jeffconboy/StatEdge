# Betting Odds Service

Real-time sports betting odds collection and analysis service for the StatEdge platform.

## Overview

The Betting Odds Service collects, processes, and serves real-time betting odds from multiple sportsbooks, providing comprehensive market data for baseball games with historical tracking and analytics capabilities.

## Service Details

- **Port**: 8002
- **Framework**: FastAPI (Python 3.11+)
- **Database**: Sports PostgreSQL (Port 5432) - Shared with Sports API
- **Cache**: Redis (Port 6379) for real-time data
- **Update Frequency**: 30 seconds during live games, 5 minutes pre-game

## Core Responsibilities

### Real-time Odds Collection
- Fetch current betting lines from multiple sportsbooks
- Track line movements and market changes
- Monitor odds for all MLB games
- Calculate implied probabilities and market efficiency

### Historical Data Management
- Store complete odds history for trend analysis
- Track line movement patterns
- Archive closed market data
- Maintain sportsbook-specific data integrity

### Market Analysis
- Identify arbitrage opportunities
- Calculate market consensus
- Detect sharp money movements
- Generate betting insights and recommendations

### API Integration
- Integrate with major sportsbook APIs
- Handle rate limiting and API quotas
- Manage authentication tokens
- Implement failover for data source redundancy

## Supported Sportsbooks

### Primary Sources
- **DraftKings**: MLB game lines, player props, futures
- **FanDuel**: Competitive odds, live betting markets
- **BetMGM**: Comprehensive market coverage
- **Caesars**: Traditional sportsbook offerings
- **PointsBet**: Unique spread betting options

### Secondary Sources
- **Bet365**: International market perspective
- **William Hill**: Established market maker
- **Unibet**: European sportsbook data
- **Barstool**: Recreational market insights

### Data Aggregators
- **The Odds API**: Centralized odds feed
- **SportsDataIO**: Professional data service
- **RapidAPI Sports**: Backup data source

## API Endpoints

### Current Odds
```http
GET /api/v1/odds/current
GET /api/v1/odds/game/{game_pk}
GET /api/v1/odds/today
GET /api/v1/odds/sportsbook/{sportsbook_name}
```

### Historical Data
```http
GET /api/v1/odds/history/{game_pk}
GET /api/v1/odds/movements?game_pk={game_pk}&hours=24
GET /api/v1/odds/closing-lines?date=2024-07-26
```

### Market Analysis
```http
GET /api/v1/odds/arbitrage
GET /api/v1/odds/consensus/{game_pk}
GET /api/v1/odds/sharp-action?date=2024-07-26
GET /api/v1/odds/market-efficiency
```

### Player Props
```http
GET /api/v1/odds/props/player/{player_id}
GET /api/v1/odds/props/game/{game_pk}
GET /api/v1/odds/props/types
```

### Futures & Specials
```http
GET /api/v1/odds/futures/world-series
GET /api/v1/odds/futures/mvp
GET /api/v1/odds/futures/division-winners
GET /api/v1/odds/specials
```

## Database Schema

### Betting Odds Table
```sql
CREATE TABLE betting_odds (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER NOT NULL,
    sportsbook VARCHAR(50) NOT NULL,
    market_type VARCHAR(30) NOT NULL, -- moneyline, spread, total, props
    
    -- Moneyline odds
    home_ml DECIMAL(7,2),
    away_ml DECIMAL(7,2),
    
    -- Totals (Over/Under)
    over_under DECIMAL(4,1),
    over_odds DECIMAL(7,2),
    under_odds DECIMAL(7,2),
    
    -- Run line spreads
    home_spread DECIMAL(4,1),
    home_spread_odds DECIMAL(7,2),
    away_spread DECIMAL(4,1),
    away_spread_odds DECIMAL(7,2),
    
    -- Market metadata
    limit_amount DECIMAL(10,2),
    market_status VARCHAR(20), -- open, closed, suspended
    last_updated TIMESTAMP WITH TIME ZONE,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints and indexes
    UNIQUE(game_pk, sportsbook, market_type, last_updated),
    INDEX idx_game_sportsbook (game_pk, sportsbook),
    INDEX idx_timestamp (last_updated),
    INDEX idx_market_status (market_status, last_updated),
    FOREIGN KEY (game_pk) REFERENCES games(game_pk)
);
```

### Player Props Table
```sql
CREATE TABLE player_props (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER NOT NULL,
    player_id INTEGER,
    player_name VARCHAR(100),
    sportsbook VARCHAR(50) NOT NULL,
    prop_type VARCHAR(50) NOT NULL, -- hits, home_runs, strikeouts, etc.
    prop_line DECIMAL(6,2),
    over_odds DECIMAL(7,2),
    under_odds DECIMAL(7,2),
    market_status VARCHAR(20),
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_player_game (player_id, game_pk),
    INDEX idx_prop_type (prop_type, last_updated),
    INDEX idx_sportsbook_status (sportsbook, market_status),
    FOREIGN KEY (game_pk) REFERENCES games(game_pk)
);
```

### Futures Odds Table
```sql
CREATE TABLE futures_odds (
    id SERIAL PRIMARY KEY,
    market_category VARCHAR(50) NOT NULL, -- world_series, mvp, division
    team_or_player VARCHAR(100),
    team_id INTEGER,
    player_id INTEGER,
    sportsbook VARCHAR(50) NOT NULL,
    odds DECIMAL(7,2),
    implied_probability DECIMAL(6,4),
    market_status VARCHAR(20),
    season INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_market_season (market_category, season),
    INDEX idx_team_player (team_id, player_id),
    INDEX idx_sportsbook_market (sportsbook, market_category)
);
```

### Market Movements Table
```sql
CREATE TABLE market_movements (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER NOT NULL,
    sportsbook VARCHAR(50) NOT NULL,
    market_type VARCHAR(30) NOT NULL,
    movement_type VARCHAR(20), -- line_move, odds_change, volume_spike
    
    -- Before values
    old_home_ml DECIMAL(7,2),
    old_away_ml DECIMAL(7,2),
    old_total DECIMAL(4,1),
    old_spread DECIMAL(4,1),
    
    -- After values
    new_home_ml DECIMAL(7,2),
    new_away_ml DECIMAL(7,2),
    new_total DECIMAL(4,1),
    new_spread DECIMAL(4,1),
    
    -- Movement analysis
    movement_size DECIMAL(6,3),
    movement_direction VARCHAR(10), -- up, down, neutral
    market_impact VARCHAR(20), -- sharp, steam, public
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_game_movements (game_pk, timestamp),
    INDEX idx_movement_type (movement_type, timestamp),
    INDEX idx_market_impact (market_impact, timestamp)
);
```

## Data Collection System

### Collection Schedule
```python
# Live games - high frequency updates
LIVE_GAME_INTERVAL = 30  # seconds
PRE_GAME_INTERVAL = 300  # 5 minutes
POST_GAME_INTERVAL = 3600  # 1 hour

# Collection priorities
PRIORITY_SPORTSBOOKS = [
    "draftkings", "fanduel", "betmgm", "caesars"
]

SECONDARY_SPORTSBOOKS = [
    "pointsbet", "bet365", "williamhill", "unibet"
]
```

### API Integration Framework
```python
class SportsbookAPI:
    def __init__(self, name: str, api_key: str, base_url: str):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = RateLimiter()
        
    async def fetch_game_odds(self, game_pk: int) -> dict:
        """Fetch odds for a specific game"""
        
    async def fetch_player_props(self, game_pk: int) -> list:
        """Fetch player props for a game"""
        
    async def fetch_futures(self, market_type: str) -> list:
        """Fetch futures odds"""

# Sportsbook implementations
class DraftKingsAPI(SportsbookAPI):
    async def fetch_game_odds(self, game_pk: int):
        endpoint = f"/games/{game_pk}/odds"
        return await self._make_request(endpoint)

class FanDuelAPI(SportsbookAPI):
    async def fetch_game_odds(self, game_pk: int):
        endpoint = f"/events/{game_pk}/markets"
        return await self._make_request(endpoint)
```

### Data Processing Pipeline
```python
class OddsProcessor:
    def __init__(self):
        self.validators = []
        self.analyzers = []
        
    async def process_odds_data(self, raw_data: dict, sportsbook: str):
        # 1. Validate incoming data
        validated_data = await self.validate_odds(raw_data)
        
        # 2. Normalize format across sportsbooks
        normalized_data = await self.normalize_odds(validated_data, sportsbook)
        
        # 3. Calculate derived metrics
        enhanced_data = await self.calculate_metrics(normalized_data)
        
        # 4. Detect market movements
        movements = await self.detect_movements(enhanced_data)
        
        # 5. Store in database
        await self.store_odds(enhanced_data, movements)
        
        # 6. Update cache
        await self.update_cache(enhanced_data)
        
        return enhanced_data

    async def calculate_metrics(self, odds_data: dict) -> dict:
        """Calculate implied probabilities and market efficiency"""
        
        # Convert American odds to implied probability
        def american_to_probability(odds: float) -> float:
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)
        
        # Calculate market efficiency (total implied probability)
        home_prob = american_to_probability(odds_data['home_ml'])
        away_prob = american_to_probability(odds_data['away_ml'])
        market_efficiency = home_prob + away_prob
        
        odds_data.update({
            'home_implied_prob': home_prob,
            'away_implied_prob': away_prob,
            'market_efficiency': market_efficiency,
            'vig_percentage': (market_efficiency - 1.0) * 100
        })
        
        return odds_data
```

## Market Analysis Features

### Arbitrage Detection
```python
class ArbitrageDetector:
    def __init__(self, min_profit_margin: float = 0.02):
        self.min_profit_margin = min_profit_margin
        
    async def find_arbitrage_opportunities(self, game_pk: int) -> list:
        """Find arbitrage opportunities across sportsbooks"""
        
        # Get all current odds for the game
        all_odds = await self.get_game_odds(game_pk)
        
        opportunities = []
        
        # Check moneyline arbitrage
        best_home = max(all_odds, key=lambda x: x['home_ml'])
        best_away = max(all_odds, key=lambda x: x['away_ml'])
        
        if best_home['sportsbook'] != best_away['sportsbook']:
            profit_margin = self.calculate_arbitrage_profit(
                best_home['home_ml'], 
                best_away['away_ml']
            )
            
            if profit_margin > self.min_profit_margin:
                opportunities.append({
                    'type': 'moneyline',
                    'game_pk': game_pk,
                    'profit_margin': profit_margin,
                    'home_bet': {
                        'sportsbook': best_home['sportsbook'],
                        'odds': best_home['home_ml']
                    },
                    'away_bet': {
                        'sportsbook': best_away['sportsbook'],
                        'odds': best_away['away_ml']
                    }
                })
        
        return opportunities

    def calculate_arbitrage_profit(self, home_odds: float, away_odds: float) -> float:
        """Calculate guaranteed profit percentage from arbitrage"""
        home_prob = self.american_to_decimal_prob(home_odds)
        away_prob = self.american_to_decimal_prob(away_odds)
        
        total_prob = home_prob + away_prob
        
        if total_prob < 1.0:
            return (1.0 - total_prob) / total_prob
        
        return 0.0
```

### Sharp Action Detection
```python
class SharpActionDetector:
    def __init__(self):
        self.sharp_indicators = [
            'reverse_line_movement',
            'low_ticket_high_money',
            'steam_moves',
            'consensus_fade'
        ]
    
    async def detect_sharp_action(self, game_pk: int, hours: int = 24) -> dict:
        """Detect indicators of sharp money on a game"""
        
        movements = await self.get_line_movements(game_pk, hours)
        ticket_data = await self.get_betting_percentages(game_pk)
        
        indicators = {
            'reverse_line_movement': self.check_reverse_line_movement(movements, ticket_data),
            'steam_moves': self.detect_steam_moves(movements),
            'low_ticket_high_money': self.check_ticket_money_divergence(ticket_data),
            'line_value': self.calculate_line_value(movements)
        }
        
        # Calculate sharp action score
        sharp_score = self.calculate_sharp_score(indicators)
        
        return {
            'game_pk': game_pk,
            'sharp_score': sharp_score,
            'indicators': indicators,
            'recommendation': self.generate_recommendation(sharp_score, indicators)
        }
```

## Configuration

### Environment Variables
```bash
# Sportsbook API Keys
DRAFTKINGS_API_KEY=your_draftkings_key
FANDUEL_API_KEY=your_fanduel_key
BETMGM_API_KEY=your_betmgm_key
CAESARS_API_KEY=your_caesars_key
ODDS_API_KEY=your_odds_api_key

# Database Configuration
DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data
REDIS_URL=redis://redis:6379

# Collection Settings
COLLECTION_ENABLED=true
LIVE_UPDATE_INTERVAL=30
PREGAME_UPDATE_INTERVAL=300
MAX_CONCURRENT_REQUESTS=10

# Market Analysis
ARBITRAGE_MIN_PROFIT=0.02
SHARP_ACTION_THRESHOLD=0.7
STEAM_MOVE_THRESHOLD=1.5

# API Configuration
API_V1_STR=/api/v1
CORS_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start dependencies
docker-compose up -d sports-database redis

# Configure API keys
cp .env.example .env
# Edit .env with your sportsbook API keys

# Run development server
uvicorn main:app --reload --port 8002

# Access API documentation
open http://localhost:8002/docs
```

## Monitoring & Alerts

### Collection Monitoring
```python
@app.middleware("http")
async def monitor_collection_health(request: Request, call_next):
    """Monitor odds collection performance"""
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log collection metrics
    if request.url.path.startswith('/collect'):
        await log_collection_metrics(
            endpoint=request.url.path,
            response_time=process_time,
            status_code=response.status_code,
            timestamp=datetime.utcnow()
        )
    
    return response

async def check_collection_health():
    """Health check for odds collection system"""
    
    health_status = {
        "status": "healthy",
        "last_collection": await get_last_collection_time(),
        "active_games": await count_active_games(),
        "sportsbook_status": await check_sportsbook_apis(),
        "data_freshness": await check_data_freshness()
    }
    
    return health_status
```

### Market Alerts
```python
class MarketAlertSystem:
    def __init__(self):
        self.alert_thresholds = {
            'arbitrage_profit': 0.03,
            'steam_move_size': 2.0,
            'line_reverse': True,
            'sharp_score': 0.8
        }
    
    async def process_alerts(self, odds_data: dict):
        """Process and send market alerts"""
        
        alerts = []
        
        # Check for arbitrage opportunities
        arb_opportunities = await self.check_arbitrage(odds_data)
        for opportunity in arb_opportunities:
            if opportunity['profit_margin'] > self.alert_thresholds['arbitrage_profit']:
                alerts.append({
                    'type': 'arbitrage',
                    'priority': 'high',
                    'data': opportunity
                })
        
        # Check for steam moves
        steam_moves = await self.detect_steam_moves(odds_data)
        for move in steam_moves:
            if move['size'] > self.alert_thresholds['steam_move_size']:
                alerts.append({
                    'type': 'steam_move',
                    'priority': 'medium',
                    'data': move
                })
        
        # Send alerts
        for alert in alerts:
            await self.send_alert(alert)
```

## Performance Characteristics

### Response Times
- **Current Odds**: < 100ms
- **Historical Data**: < 300ms (24 hours)
- **Market Analysis**: < 500ms
- **Arbitrage Detection**: < 200ms

### Throughput
- **Odds Updates**: 1000+ per minute during peak
- **API Requests**: 500+ requests/second
- **Concurrent Collections**: 50+ sportsbooks
- **Data Processing**: 10k+ odds per minute

### Reliability
- **Uptime Target**: 99.9%
- **Collection Success Rate**: > 95%
- **API Response Rate**: > 98%
- **Data Accuracy**: > 99.5%

## Error Handling

### API Failures
```python
class SportsbookAPIError(Exception):
    def __init__(self, sportsbook: str, error_code: int, message: str):
        self.sportsbook = sportsbook
        self.error_code = error_code
        self.message = message

async def handle_api_failure(sportsbook: str, error: Exception):
    """Handle sportsbook API failures gracefully"""
    
    # Log the failure
    logger.error(f"API failure for {sportsbook}: {error}")
    
    # Implement fallback strategies
    if isinstance(error, RateLimitError):
        await implement_backoff(sportsbook)
    elif isinstance(error, AuthenticationError):
        await refresh_api_credentials(sportsbook)
    else:
        await switch_to_backup_source(sportsbook)
```

### Data Quality Validation
```python
class OddsValidator:
    def validate_odds_data(self, odds: dict) -> bool:
        """Validate odds data for quality and consistency"""
        
        checks = [
            self.check_odds_range(odds),
            self.check_market_efficiency(odds),
            self.check_timestamp_validity(odds),
            self.check_required_fields(odds)
        ]
        
        return all(checks)
    
    def check_market_efficiency(self, odds: dict) -> bool:
        """Ensure market efficiency is within reasonable bounds"""
        if 'home_ml' in odds and 'away_ml' in odds:
            total_prob = (
                self.american_to_probability(odds['home_ml']) +
                self.american_to_probability(odds['away_ml'])
            )
            return 1.0 <= total_prob <= 1.15  # 0-15% vig is reasonable
        
        return True
```

---

The Betting Odds Service provides comprehensive market coverage with real-time data collection, advanced analytics, and reliable API integration for professional sports betting intelligence.