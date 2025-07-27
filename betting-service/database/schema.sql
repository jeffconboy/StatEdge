-- Betting Service Database Schema
-- ===============================
-- 
-- Simplified schema for personal bet tracking and prediction analysis
-- No real-time odds or compliance features needed

-- Database: betting_data
-- Purpose: Track personal betting predictions and outcomes

-- Bets table - Core bet tracking
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

-- Betting Categories for organization
CREATE TABLE bet_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(7) -- Hex color for UI
);

-- Bet category mapping
CREATE TABLE bet_category_mapping (
    bet_id INTEGER REFERENCES bets(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES bet_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (bet_id, category_id)
);

-- Player prop bets (separate table for more complex props)
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

-- Betting strategies for tracking what works
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

-- Link bets to strategies
CREATE TABLE bet_strategy_mapping (
    bet_id INTEGER REFERENCES bets(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES betting_strategies(id) ON DELETE CASCADE,
    PRIMARY KEY (bet_id, strategy_id)
);

-- Bankroll tracking for money management
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

-- Game information cache (from Tank01 API)
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

-- Indexes for performance
CREATE INDEX idx_bets_game_date ON bets(game_date);
CREATE INDEX idx_bets_sport ON bets(sport);
CREATE INDEX idx_bets_bet_type ON bets(bet_type);
CREATE INDEX idx_bets_result ON bets(bet_result);
CREATE INDEX idx_bets_game_status ON bets(game_status);
CREATE INDEX idx_games_cache_game_date ON games_cache(game_date);
CREATE INDEX idx_games_cache_sport ON games_cache(sport);

-- Insert default bet categories
INSERT INTO bet_categories (category_name, description, color_code) VALUES
('Safe Bets', 'Low risk, high confidence bets', '#28a745'),
('Value Bets', 'Good odds vs actual probability', '#17a2b8'),
('Longshots', 'High risk, high reward bets', '#dc3545'),
('Player Props', 'Individual player performance bets', '#ffc107'),
('System Plays', 'Bets based on specific systems', '#6f42c1'),
('Live Bets', 'In-game betting opportunities', '#fd7e14'),
('Favorites', 'Betting on favored teams', '#20c997'),
('Underdogs', 'Betting on underdog teams', '#e83e8c');

-- Insert default betting strategies
INSERT INTO betting_strategies (strategy_name, description, criteria) VALUES
('Home Favorite', 'Bet on home teams favored by 1-2 runs', '{"max_spread": 2, "team_location": "home", "min_confidence": 6}'),
('Underdog Value', 'Bet on underdogs with good value', '{"min_odds": 150, "max_odds": 300, "min_confidence": 7}'),
('Total Overs', 'Bet overs in high-scoring environments', '{"total_threshold": 8.5, "weather": "good", "min_confidence": 6}'),
('Starting Pitcher', 'Bet based on starting pitcher quality', '{"min_pitcher_era": 3.50, "pitcher_form": "good", "min_confidence": 7}'),
('Revenge Game', 'Teams coming off losses to same opponent', '{"recent_loss": true, "same_opponent": true, "min_confidence": 6}'),
('Hot Team', 'Teams on winning streaks', '{"min_win_streak": 4, "recent_form": "hot", "min_confidence": 6}');

-- Views for common queries
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