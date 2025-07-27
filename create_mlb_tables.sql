-- Create tables for MLB API data integration

-- Teams table
CREATE TABLE IF NOT EXISTS mlb_teams (
    id INTEGER PRIMARY KEY,
    team_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(5) NOT NULL,
    team_code VARCHAR(5) NOT NULL,
    team_name VARCHAR(50) NOT NULL,
    location_name VARCHAR(50) NOT NULL,
    franchise_name VARCHAR(50) NOT NULL,
    club_name VARCHAR(50) NOT NULL,
    league_id INTEGER,
    league_name VARCHAR(50),
    division_id INTEGER,
    division_name VARCHAR(50),
    venue_id INTEGER,
    venue_name VARCHAR(100),
    first_year_of_play VARCHAR(4),
    active BOOLEAN DEFAULT true,
    season INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players table (roster data)
CREATE TABLE IF NOT EXISTS mlb_players (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    jersey_number VARCHAR(3),
    position_code VARCHAR(2),
    position_name VARCHAR(20),
    position_type VARCHAR(20),
    position_abbreviation VARCHAR(5),
    status_code VARCHAR(5),
    status_description VARCHAR(20),
    roster_type VARCHAR(20),
    season INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, team_id, season)
);

-- Game lineups table (detailed batting order and position data)
CREATE TABLE IF NOT EXISTS mlb_game_lineups (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    team_type VARCHAR(4) NOT NULL, -- 'home' or 'away'
    player_id INTEGER NOT NULL,
    batting_order INTEGER,
    position_code VARCHAR(2),
    position_name VARCHAR(20),
    jersey_number VARCHAR(3),
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_pk, team_id, player_id)
);

-- Probable pitchers table
CREATE TABLE IF NOT EXISTS mlb_probable_pitchers (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    team_type VARCHAR(4) NOT NULL, -- 'home' or 'away'
    pitcher_id INTEGER NOT NULL,
    pitcher_name VARCHAR(100) NOT NULL,
    jersey_number VARCHAR(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_pk, team_id, pitcher_id)
);

-- Game details table (enhanced version of existing games table structure)
CREATE TABLE IF NOT EXISTS mlb_game_details (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER UNIQUE NOT NULL,
    game_guid VARCHAR(100),
    game_type VARCHAR(5),
    season INTEGER NOT NULL,
    game_date TIMESTAMP NOT NULL,
    official_date DATE NOT NULL,
    
    -- Status information
    status_code VARCHAR(5),
    detailed_state VARCHAR(50),
    abstract_game_state VARCHAR(20),
    
    -- Team information
    home_team_id INTEGER NOT NULL,
    home_team_name VARCHAR(100),
    home_score INTEGER,
    home_wins INTEGER,
    home_losses INTEGER,
    home_is_winner BOOLEAN,
    
    away_team_id INTEGER NOT NULL,
    away_team_name VARCHAR(100),
    away_score INTEGER,
    away_wins INTEGER,
    away_losses INTEGER,
    away_is_winner BOOLEAN,
    
    -- Venue
    venue_id INTEGER,
    venue_name VARCHAR(100),
    
    -- Additional game info
    series_number INTEGER,
    game_number INTEGER,
    double_header VARCHAR(1),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_mlb_teams_team_id ON mlb_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_mlb_teams_season ON mlb_teams(season);

CREATE INDEX IF NOT EXISTS idx_mlb_players_player_id ON mlb_players(player_id);
CREATE INDEX IF NOT EXISTS idx_mlb_players_team_id ON mlb_players(team_id);
CREATE INDEX IF NOT EXISTS idx_mlb_players_season ON mlb_players(season);

CREATE INDEX IF NOT EXISTS idx_mlb_game_lineups_game_pk ON mlb_game_lineups(game_pk);
CREATE INDEX IF NOT EXISTS idx_mlb_game_lineups_team_id ON mlb_game_lineups(team_id);

CREATE INDEX IF NOT EXISTS idx_mlb_probable_pitchers_game_pk ON mlb_probable_pitchers(game_pk);
CREATE INDEX IF NOT EXISTS idx_mlb_probable_pitchers_team_id ON mlb_probable_pitchers(team_id);

CREATE INDEX IF NOT EXISTS idx_mlb_game_details_game_pk ON mlb_game_details(game_pk);
CREATE INDEX IF NOT EXISTS idx_mlb_game_details_season ON mlb_game_details(season);
CREATE INDEX IF NOT EXISTS idx_mlb_game_details_game_date ON mlb_game_details(game_date);
CREATE INDEX IF NOT EXISTS idx_mlb_game_details_home_team ON mlb_game_details(home_team_id);
CREATE INDEX IF NOT EXISTS idx_mlb_game_details_away_team ON mlb_game_details(away_team_id);