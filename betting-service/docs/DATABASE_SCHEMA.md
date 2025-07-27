# Database Schema Documentation

## StatEdge Betting Service Database Schema

### Overview

The betting service uses a PostgreSQL database named `betting_data` with a simplified schema designed for personal bet tracking. The schema focuses on core functionality without the complexity of real-time betting platforms.

### Database Configuration

```sql
-- Database: betting_data
-- User: betting_user  
-- Password: betting_secure_2025
-- Host: localhost
-- Port: 5432
```

---

## Core Tables

### 1. bets

The main table for storing betting predictions and outcomes.

```sql
CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    sport VARCHAR(20) DEFAULT 'MLB',
    home_team VARCHAR(10) NOT NULL,
    away_team VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    game_time TIME,
    
    -- Bet Details
    bet_type VARCHAR(20) NOT NULL, -- 'moneyline', 'spread', 'total', 'prop'
    bet_side VARCHAR(20) NOT NULL, -- 'home', 'away', 'over', 'under', 'yes', 'no'
    bet_amount DECIMAL(10,2) NOT NULL,
    odds DECIMAL(8,2), -- American odds format (-150, +130)
    implied_probability DECIMAL(5,2), -- Calculated from odds
    
    -- Prediction Details
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 10),
    prediction_reasoning TEXT,
    predicted_score_home INTEGER,
    predicted_score_away INTEGER,
    
    -- Outcome Tracking
    game_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'cancelled'
    actual_score_home INTEGER,
    actual_score_away INTEGER,
    bet_result VARCHAR(10), -- 'win', 'loss', 'push', 'void'
    payout DECIMAL(10,2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

**Key Columns Explained:**

- **game_id**: Unique identifier for the game (e.g., "20250726_BOS@NYY")
- **bet_type**: Type of bet placed
  - `moneyline`: Win/loss bet on teams
  - `spread`: Point spread bet
  - `total`: Over/under bet
  - `prop`: Player proposition bet
- **bet_side**: Which side of the bet
  - `home`/`away`: For moneyline and spread
  - `over`/`under`: For totals
  - `yes`/`no`: For props
- **odds**: American odds format (negative for favorites, positive for underdogs)
- **confidence_level**: Your confidence in the bet (1-10 scale)
- **game_status**: Current status of the game
- **bet_result**: Outcome of your bet

### 2. bet_categories

Organize bets by category for better analysis.

```sql
CREATE TABLE bet_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(7) -- Hex color for UI
);
```

**Pre-loaded Categories:**
- Safe Bets (#28a745)
- Value Bets (#17a2b8)
- Longshots (#dc3545)
- Player Props (#ffc107)
- System Plays (#6f42c1)
- Live Bets (#fd7e14)
- Favorites (#20c997)
- Underdogs (#e83e8c)

### 3. bet_category_mapping

Many-to-many relationship between bets and categories.

```sql
CREATE TABLE bet_category_mapping (
    bet_id INTEGER REFERENCES bets(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES bet_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (bet_id, category_id)
);
```

### 4. betting_strategies

Track different betting approaches and their performance.

```sql
CREATE TABLE betting_strategies (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    criteria JSON, -- Store strategy rules as JSON
    
    -- Performance tracking
    total_bets INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    pushes INTEGER DEFAULT 0,
    total_wagered DECIMAL(12,2) DEFAULT 0,
    total_profit DECIMAL(12,2) DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    roi DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Pre-loaded Strategies:**
- Home Favorite
- Underdog Value  
- Total Overs
- Starting Pitcher
- Revenge Game
- Hot Team

### 5. bet_strategy_mapping

Link bets to the strategies they follow.

```sql
CREATE TABLE bet_strategy_mapping (
    bet_id INTEGER REFERENCES bets(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES betting_strategies(id) ON DELETE CASCADE,
    PRIMARY KEY (bet_id, strategy_id)
);
```

### 6. bankroll_history

Track daily bankroll changes for money management.

```sql
CREATE TABLE bankroll_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    starting_balance DECIMAL(12,2) NOT NULL,
    ending_balance DECIMAL(12,2) NOT NULL,
    daily_pnl DECIMAL(12,2) NOT NULL,
    total_wagered DECIMAL(12,2) DEFAULT 0,
    number_of_bets INTEGER DEFAULT 0,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** Record your daily bankroll to track:
- Daily profit/loss
- Bankroll progression over time
- Risk management metrics
- Betting volume tracking

### 7. player_prop_bets

Detailed tracking for player proposition bets.

```sql
CREATE TABLE player_prop_bets (
    id SERIAL PRIMARY KEY,
    bet_id INTEGER REFERENCES bets(id) ON DELETE CASCADE,
    player_id VARCHAR(20) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    prop_type VARCHAR(50) NOT NULL, -- 'hits', 'runs', 'rbis', 'strikeouts', etc.
    prop_line DECIMAL(8,2) NOT NULL,
    actual_result DECIMAL(8,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Prop Types:**
- hits, runs, rbis, home_runs
- strikeouts, walks, innings_pitched
- saves, earned_runs, hits_allowed

### 8. games_cache

Cache game information from Tank01 API for reference.

```sql
CREATE TABLE games_cache (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) UNIQUE NOT NULL,
    sport VARCHAR(20) DEFAULT 'MLB',
    home_team VARCHAR(10) NOT NULL,
    away_team VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    game_time TIME,
    
    -- Odds from Tank01 API (cached for reference)
    home_ml DECIMAL(8,2),
    away_ml DECIMAL(8,2),
    home_spread DECIMAL(4,1),
    home_spread_odds DECIMAL(8,2),
    total_over DECIMAL(4,1),
    total_over_odds DECIMAL(8,2),
    
    -- Game outcome
    final_score_home INTEGER,
    final_score_away INTEGER,
    game_status VARCHAR(20) DEFAULT 'scheduled',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Database Views

### bet_summary

Pre-calculated summary statistics by sport and bet type.

```sql
CREATE VIEW bet_summary AS
SELECT 
    sport,
    bet_type,
    COUNT(*) as total_bets,
    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN bet_result = 'loss' THEN 1 ELSE 0 END) as losses,
    SUM(CASE WHEN bet_result = 'push' THEN 1 ELSE 0 END) as pushes,
    ROUND(
        SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END)::decimal / 
        NULLIF(COUNT(*) - SUM(CASE WHEN bet_result = 'push' THEN 1 ELSE 0 END), 0) * 100, 2
    ) as win_percentage,
    SUM(bet_amount) as total_wagered,
    SUM(COALESCE(payout, 0) - bet_amount) as total_profit,
    ROUND(
        (SUM(COALESCE(payout, 0) - bet_amount) / NULLIF(SUM(bet_amount), 0)) * 100, 2
    ) as roi_percentage
FROM bets 
WHERE game_status = 'completed'
GROUP BY sport, bet_type;
```

### recent_performance

Weekly performance breakdown for trend analysis.

```sql
CREATE VIEW recent_performance AS
SELECT 
    DATE_TRUNC('week', game_date) as week_start,
    COUNT(*) as bets_made,
    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
    SUM(bet_amount) as amount_wagered,
    SUM(COALESCE(payout, 0) - bet_amount) as weekly_profit
FROM bets 
WHERE game_date >= CURRENT_DATE - INTERVAL '8 weeks'
    AND game_status = 'completed'
GROUP BY DATE_TRUNC('week', game_date)
ORDER BY week_start DESC;
```

---

## Indexes

Performance indexes for common queries:

```sql
-- Bets table indexes
CREATE INDEX idx_bets_game_date ON bets(game_date);
CREATE INDEX idx_bets_sport ON bets(sport);
CREATE INDEX idx_bets_bet_type ON bets(bet_type);
CREATE INDEX idx_bets_result ON bets(bet_result);
CREATE INDEX idx_bets_game_status ON bets(game_status);

-- Games cache indexes
CREATE INDEX idx_games_cache_game_date ON games_cache(game_date);
CREATE INDEX idx_games_cache_sport ON games_cache(sport);
```

---

## Database Operations

### Common Queries

**Get Recent Bets:**
```sql
SELECT * FROM bets 
WHERE game_status = 'completed'
ORDER BY game_date DESC, created_at DESC
LIMIT 10;
```

**Calculate Win Rate:**
```sql
SELECT 
    COUNT(*) as total_bets,
    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
    ROUND(
        SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END)::decimal / 
        COUNT(*) * 100, 2
    ) as win_rate
FROM bets 
WHERE game_status = 'completed'
AND game_date >= CURRENT_DATE - INTERVAL '30 days';
```

**Strategy Performance:**
```sql
SELECT 
    bs.strategy_name,
    bs.total_bets,
    bs.wins,
    bs.win_rate,
    bs.roi
FROM betting_strategies bs
ORDER BY bs.total_bets DESC;
```

**Monthly Bankroll Progression:**
```sql
SELECT 
    DATE_TRUNC('month', date) as month,
    AVG(ending_balance) as avg_balance,
    SUM(daily_pnl) as monthly_pnl
FROM bankroll_history
WHERE date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', date)
ORDER BY month;
```

### Maintenance Queries

**Update Strategy Performance (run after settling bets):**
```sql
UPDATE betting_strategies 
SET win_rate = CASE 
    WHEN (total_bets - pushes) > 0 
    THEN ROUND((wins::decimal / (total_bets - pushes)) * 100, 2)
    ELSE 0 
END,
roi = CASE 
    WHEN total_wagered > 0 
    THEN ROUND((total_profit / total_wagered) * 100, 2)
    ELSE 0 
END;
```

**Clean Old Game Cache (run weekly):**
```sql
DELETE FROM games_cache 
WHERE game_date < CURRENT_DATE - INTERVAL '30 days'
AND game_status = 'completed';
```

---

## Data Types Reference

### Bet Types
- `moneyline`: Straight win/loss bet
- `spread`: Point spread bet (runs in baseball)
- `total`: Over/under bet on total runs
- `prop`: Player or game proposition bet

### Bet Sides
- `home`: Home team
- `away`: Away team  
- `over`: Over the total
- `under`: Under the total
- `yes`: Yes on proposition
- `no`: No on proposition

### Bet Results
- `win`: Bet won
- `loss`: Bet lost
- `push`: Tie/refund
- `void`: Voided bet

### Game Status
- `pending`: Game not yet played
- `completed`: Game finished
- `cancelled`: Game cancelled/postponed

---

## Backup & Recovery

### Daily Backup Script
```bash
#!/bin/bash
# backup_betting_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/backups/betting_data_$DATE.sql"

pg_dump -h localhost -U betting_user -d betting_data > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 30 days of backups
find /backups -name "betting_data_*.sql.gz" -mtime +30 -delete
```

### Restore from Backup
```bash
# Restore database from backup
gunzip betting_data_20250726_120000.sql.gz
psql -h localhost -U betting_user -d betting_data < betting_data_20250726_120000.sql
```

---

## Schema Migrations

### Adding New Columns
```sql
-- Example: Add new confidence tracking
ALTER TABLE bets ADD COLUMN confidence_notes TEXT;
UPDATE bets SET confidence_notes = '' WHERE confidence_notes IS NULL;
```

### Creating New Indexes
```sql
-- Example: Add index for confidence analysis
CREATE INDEX idx_bets_confidence ON bets(confidence_level);
```

---

## Security Considerations

### User Permissions
```sql
-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO betting_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO betting_user;
```

### Data Privacy
- All betting data stored locally
- No external data sharing
- Regular backup encryption recommended
- Database credentials stored securely

---

This database schema provides a solid foundation for personal betting tracking while maintaining simplicity and performance. The design supports comprehensive analytics while avoiding the complexity of commercial betting platforms.