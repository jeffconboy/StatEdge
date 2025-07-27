# StatEdge Betting Service

## Overview

The StatEdge Betting Service is a simplified microservice designed for **personal baseball betting prediction tracking**. Unlike complex betting platforms, this service focuses on helping you log your predictions, track outcomes, and analyze your betting performance over time.

### 🎯 **Purpose**
- Log your betting predictions with confidence levels and reasoning
- Track wins, losses, and calculate ROI automatically
- Analyze which betting strategies work best for you
- Monitor your betting bankroll over time
- Get reference odds from Tank01 API for informed betting decisions

### 🚫 **What This Service is NOT**
- Not a real-time betting platform
- No compliance or regulatory features
- No live odds monitoring or line movement tracking
- No automated betting or complex financial operations
- Just simple personal bet tracking for your own analysis

## Architecture

### Microservice Design
The betting service is designed as an independent microservice that:
- Runs on port **18002**
- Has its own PostgreSQL database (`betting_data`)
- Integrates with Tank01 API for MLB odds reference
- Communicates with the main sports data service for game information

### Database Schema
The service uses a simplified PostgreSQL schema with these core tables:

```sql
-- Core bet tracking
bets                    # Your betting predictions and outcomes
bet_categories         # Organize bets by type (e.g., "Safe Bets", "Longshots")
betting_strategies     # Track performance of different approaches
bankroll_history       # Daily bankroll tracking
player_prop_bets       # Individual player performance bets
games_cache           # Cached game data from Tank01 API
```

## Installation & Setup

### Prerequisites
- Docker and Docker Compose
- PostgreSQL database
- Tank01 RapidAPI subscription (for MLB odds)

### Environment Configuration
1. Copy the environment template:
```bash
cp .env.example .env
```

2. Configure your environment variables:
```bash
# Database Configuration
BETTING_DATABASE_URL=postgresql://betting_user:betting_secure_2025@localhost:5432/betting_data

# Tank01 API Configuration
TANK01_API_KEY=your_tank01_api_key_here

# Service Configuration
HOST=0.0.0.0
PORT=18002
```

### Database Setup
The service will automatically create the database schema on first run. Ensure your PostgreSQL instance is running and the betting database exists:

```sql
-- Create database and user
CREATE DATABASE betting_data;
CREATE USER betting_user WITH PASSWORD 'betting_secure_2025';
GRANT ALL PRIVILEGES ON DATABASE betting_data TO betting_user;
```

### Starting the Service

#### Using Docker Compose (Recommended)
```bash
# From the project root
docker-compose up --build betting-service
```

#### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
python main.py
```

The service will be available at:
- **API**: http://localhost:18002
- **Documentation**: http://localhost:18002/docs
- **Health Check**: http://localhost:18002/health

## API Reference

### Core Endpoints

#### Bets Management
- `POST /api/bets/` - Create a new bet prediction
- `GET /api/bets/` - Get betting history with filters
- `GET /api/bets/{bet_id}` - Get specific bet details
- `PATCH /api/bets/{bet_id}` - Update bet before game starts
- `POST /api/bets/{bet_id}/settle` - Record game outcome
- `DELETE /api/bets/{bet_id}` - Delete pending bet

#### Analytics
- `GET /api/analytics/summary` - Overall performance summary
- `GET /api/analytics/trends` - Performance trends over time
- `GET /api/analytics/confidence-analysis` - Performance by confidence level
- `GET /api/analytics/bet-type-performance` - Performance by bet type
- `GET /api/analytics/recent-activity` - Recent betting activity

#### Strategies
- `GET /api/strategies/` - Get all betting strategies
- `POST /api/strategies/` - Create new strategy
- `GET /api/strategies/{id}` - Get strategy details
- `GET /api/strategies/{id}/performance` - Strategy performance analysis

#### Bankroll
- `POST /api/bankroll/` - Add daily bankroll entry
- `GET /api/bankroll/` - Get bankroll history
- `GET /api/bankroll/summary` - Bankroll performance summary
- `GET /api/bankroll/chart-data` - Data for bankroll charts

#### Games & Odds
- `GET /api/games/today` - Today's MLB games with odds
- `GET /api/games/{game_id}/odds` - Specific game odds

## Usage Examples

### Creating Your First Bet

```python
import requests

# Create a bet prediction
bet_data = {
    "game_id": "20250726_BOS@NYY",
    "home_team": "NYY",
    "away_team": "BOS",
    "game_date": "2025-07-26",
    "bet_type": "moneyline",
    "bet_side": "home",
    "bet_amount": 50.00,
    "odds": -150,
    "confidence_level": 7,
    "prediction_reasoning": "Yankees have better starting pitcher and home field advantage"
}

response = requests.post("http://localhost:18002/api/bets/", json=bet_data)
bet = response.json()
print(f"Created bet with ID: {bet['id']}")
```

### Settling a Bet After the Game

```python
# Record the game outcome
settlement = {
    "actual_score_home": 8,
    "actual_score_away": 4,
    "bet_result": "win",
    "notes": "Great pitching performance as predicted"
}

response = requests.post(f"http://localhost:18002/api/bets/{bet_id}/settle", json=settlement)
```

### Getting Performance Analytics

```python
# Get 30-day performance summary
response = requests.get("http://localhost:18002/api/analytics/summary?days=30")
performance = response.json()

print(f"Win Rate: {performance['win_rate']}%")
print(f"ROI: {performance['roi']}%")
print(f"Total Profit: ${performance['total_profit']}")
```

## Data Models

### Bet Types
- **Moneyline**: Win/loss bets on teams
- **Spread**: Point spread betting (-1.5, +1.5 runs)
- **Total**: Over/under run totals (O8.5, U8.5)
- **Prop**: Player performance bets (hits, RBIs, etc.)

### Bet Sides
- **Home/Away**: For moneyline and spread bets
- **Over/Under**: For total bets
- **Yes/No**: For proposition bets

### Confidence Levels
Rate your confidence from 1-10:
- **1-3**: Low confidence, experimental bets
- **4-6**: Medium confidence, decent analysis
- **7-9**: High confidence, strong analysis
- **10**: Maximum confidence, "lock" bets

### Bet Categories (Pre-loaded)
- **Safe Bets**: Low risk, high confidence
- **Value Bets**: Good odds vs actual probability
- **Longshots**: High risk, high reward
- **Player Props**: Individual performance bets
- **System Plays**: Bets based on specific systems
- **Live Bets**: In-game opportunities
- **Favorites**: Betting on favored teams
- **Underdogs**: Betting on underdog teams

## Analytics Features

### Performance Metrics
- **Win Rate**: Percentage of bets won (excluding pushes)
- **ROI**: Return on investment percentage
- **Units Won/Lost**: Profit in betting units
- **Average Confidence**: Your average confidence level
- **Longest Streak**: Longest winning/losing streaks

### Trend Analysis
- Daily, weekly, monthly performance breakdowns
- Performance by bet type and confidence level
- Strategy effectiveness over time
- Bankroll progression charts

### Confidence Analysis
See how your betting performance correlates with your confidence levels:
- Do your high-confidence bets actually win more?
- What confidence level gives you the best ROI?
- Are you overconfident or underconfident?

## Best Practices

### Bet Logging
1. **Be Honest**: Record your actual predictions, not post-game rationalizations
2. **Include Reasoning**: Write down why you made each bet
3. **Set Confidence Levels**: Rate your confidence honestly
4. **Use Categories**: Organize bets by type for better analysis
5. **Track Strategies**: Link bets to specific approaches

### Bankroll Management
1. **Daily Tracking**: Record your bankroll daily
2. **Unit Sizing**: Use consistent bet sizing based on bankroll
3. **Set Limits**: Define maximum daily/weekly loss limits
4. **Review Regularly**: Analyze performance weekly/monthly

### Strategy Development
1. **Create Systems**: Develop specific betting criteria
2. **Track Everything**: Link bets to strategies for analysis
3. **Be Patient**: Give strategies time to show results
4. **Adapt**: Modify strategies based on performance data

## Testing

### Service Health Check
```bash
curl http://localhost:18002/health
```

### Run Full Test Suite
```bash
python test_service.py
```

This will test:
- Service connectivity
- API endpoints
- Database operations
- Tank01 integration
- Sample bet creation

## Troubleshooting

### Common Issues

#### Database Connection Failed
```
Error: Database connection error
```
**Solution**: Check PostgreSQL is running and betting_data database exists

#### Tank01 API Errors
```
Error: Failed to get Tank01 data
```
**Solution**: Verify TANK01_API_KEY is set correctly and subscription is active

#### Port Already in Use
```
Error: Address already in use
```
**Solution**: Stop other services on port 18002 or change PORT in .env

### Logs and Debugging
- Check container logs: `docker logs statedge_betting`
- Enable debug mode: Set `DEBUG=True` in .env
- View API docs: http://localhost:18002/docs

## Integration

### Frontend Integration
The service provides REST APIs that can be consumed by any frontend:

```javascript
// Example React integration
const createBet = async (betData) => {
  const response = await fetch('http://localhost:18002/api/bets/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(betData)
  });
  return response.json();
};
```

### Sports Data Service Integration
The betting service can integrate with the main sports data service:
- Get game schedules and results
- Access player statistics for prop bets
- Retrieve team information and matchups

## Security

### Data Protection
- All personal betting data stays in your local database
- No external sharing of betting information
- Tank01 API only used for reference odds

### Access Control
- Service runs on localhost by default
- No authentication required (personal use)
- Database credentials should be kept secure

## Future Enhancements

### Potential Features
- Mobile app integration
- Advanced statistical models
- Machine learning prediction analysis
- Export functionality for tax reporting
- Integration with more odds providers
- Social features for group challenges

### Extensibility
The service is designed to be easily extended:
- Add new bet types through database schema
- Create custom analytics endpoints
- Integrate additional APIs
- Build custom frontend components

## Support

### Getting Help
1. Check the API documentation at `/docs`
2. Review the test suite for examples
3. Check container logs for error details
4. Verify environment configuration

### Contributing
To contribute improvements:
1. Fork the repository
2. Create feature branches
3. Write tests for new functionality
4. Submit pull requests with clear descriptions

---

**Remember**: This is a personal betting tracker, not a commercial betting platform. Use responsibly and within your means. The service is designed to help you analyze your predictions and improve your betting strategy over time.