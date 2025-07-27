# 🗄️ StatEdge Database Schema Documentation

This document provides comprehensive documentation for the StatEdge PostgreSQL database schema, including all tables, relationships, and data structures.

## 📊 Overview

The StatEdge database is designed to handle massive amounts of baseball statistical data with flexibility and performance in mind. Key design principles:

- **JSONB Storage**: Flexible schema for statistical data that can evolve over time
- **Relational Structure**: Normalized design for core entities (players, games, users)
- **Performance Optimized**: Strategic indexes for common query patterns
- **Scalability**: Designed to handle millions of records with sub-2 second queries

## 🏗️ Schema Overview

```sql
-- Core Tables
├── users               -- User authentication and profiles
├── players            -- Master player information
├── games              -- MLB game data and lineups
├── statcast_pitches   -- Pitch-by-pitch Statcast data
├── fangraphs_batting  -- Comprehensive batting statistics
└── fangraphs_pitching -- Comprehensive pitching statistics
```

## 📋 Table Definitions

### 1. Users Table

Manages user authentication and subscription tiers.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    api_calls_today INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

**Fields:**
- `id`: Primary key
- `email`: Unique user email for authentication
- `password_hash`: bcrypt hashed password
- `subscription_tier`: `free`, `basic`, or `premium`
- `api_calls_today`: Daily API usage counter
- `created_at`: Account creation timestamp
- `last_login`: Last authentication timestamp

**Indexes:**
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription ON users(subscription_tier);
```

### 2. Players Table

Master player information and metadata.

```sql
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    mlb_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    current_team VARCHAR(10),
    primary_position VARCHAR(5),
    bio_data JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id`: Internal primary key
- `mlb_id`: Official MLB player ID (unique)
- `name`: Player full name
- `current_team`: Current team abbreviation (e.g., 'NYY', 'LAD')
- `primary_position`: Position code (e.g., 'OF', 'SS', '1B')
- `bio_data`: JSONB containing biographical information
- `active`: Whether player is currently active
- `created_at`: Record creation timestamp

**Bio Data JSONB Structure:**
```json
{
  "birthdate": "1992-04-26",
  "height": "6-7",
  "weight": 282,
  "bats": "R",
  "throws": "R",
  "debut": "2016-08-13"
}
```

**Indexes:**
```sql
CREATE INDEX idx_players_mlb_id ON players(mlb_id);
CREATE INDEX idx_players_name ON players USING gin(to_tsvector('english', name));
CREATE INDEX idx_players_team ON players(current_team);
CREATE INDEX idx_players_active ON players(active) WHERE active = true;
```

### 3. Games Table

MLB game information, schedules, and lineups.

```sql
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER UNIQUE NOT NULL,
    game_date DATE NOT NULL,
    season INTEGER NOT NULL,
    home_team VARCHAR(10),
    away_team VARCHAR(10),
    game_info JSONB NOT NULL,
    completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id`: Internal primary key
- `game_pk`: Official MLB game ID
- `game_date`: Date of the game
- `season`: MLB season year
- `home_team`: Home team abbreviation
- `away_team`: Away team abbreviation
- `game_info`: Complete game information as JSONB
- `completed`: Whether the game has finished
- `created_at`: Record creation timestamp

**Game Info JSONB Structure:**
```json
{
  "status": "Final",
  "inning": 9,
  "weather": {
    "condition": "Clear",
    "temp": "72°F",
    "wind": "8 mph out to CF"
  },
  "venue": "Yankee Stadium",
  "attendance": 42000,
  "lineups": {
    "home": [...],
    "away": [...]
  }
}
```

**Indexes:**
```sql
CREATE INDEX idx_games_pk ON games(game_pk);
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_games_teams ON games(home_team, away_team);
```

### 4. Statcast Pitches Table

The heart of StatEdge - pitch-by-pitch Statcast data with 118 statistical fields per record.

```sql
CREATE TABLE statcast_pitches (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER NOT NULL,
    pitch_id VARCHAR(50) UNIQUE NOT NULL,
    game_date DATE NOT NULL,
    batter_id INTEGER,
    pitcher_id INTEGER,
    
    -- ALL 118 Statcast fields stored as JSONB
    statcast_data JSONB NOT NULL,
    
    -- Indexed commonly queried fields for performance
    pitch_type VARCHAR(10),
    release_speed DECIMAL(5,2),
    events VARCHAR(50),
    launch_speed DECIMAL(5,2),
    launch_angle DECIMAL(5,2),
    hit_distance_sc INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id`: Internal primary key
- `game_pk`: Reference to games table
- `pitch_id`: Unique identifier for each pitch
- `game_date`: Date of the game
- `batter_id`: MLB ID of the batter
- `pitcher_id`: MLB ID of the pitcher
- **`statcast_data`**: Complete Statcast record (118+ fields)
- Performance fields: Commonly queried metrics extracted for indexing

**Statcast Data JSONB Sample:**
```json
{
  "pitch_type": "FF",
  "release_speed": 97.2,
  "release_pos_x": -0.42,
  "release_pos_z": 6.15,
  "spin_rate": 2234.0,
  "spin_axis": 202,
  "zone": 5,
  "balls": 1,
  "strikes": 2,
  "events": "single",
  "description": "hit_into_play",
  "launch_speed": 105.3,
  "launch_angle": 12.0,
  "hit_distance_sc": 287,
  "hit_location": 6,
  "bb_type": "line_drive",
  "barrel": 1.0,
  "estimated_ba_using_speedangle": 0.643,
  "estimated_woba_using_speedangle": 0.861,
  "woba_value": 0.89,
  "woba_denom": 1.0,
  "babip_value": 1.0,
  "iso_value": 0.0,
  "on_3b": null,
  "on_2b": null,
  "on_1b": 605141.0,
  "outs_when_up": 1,
  "inning": 3,
  "inning_topbot": "Top",
  "hc_x": 132.85,
  "hc_y": 92.71,
  "tfs_deprecated": null,
  "tfs_zulu_deprecated": null,
  "fielder_2": 605141.0,
  "umpire": null,
  "sv_id": "250723_142157",
  "vx0": 0.68,
  "vy0": -141.524,
  "vz0": -4.792,
  "ax": -4.596,
  "ay": 28.395,
  "az": -25.099,
  "sz_top": 3.37,
  "sz_bot": 1.56,
  "if_fielding_alignment": "Standard",
  "of_fielding_alignment": "Standard"
}
```

**Complete Field List (118 fields):**
- **Pitch Mechanics**: `release_speed`, `release_pos_x`, `release_pos_z`, `spin_rate`, `spin_axis`
- **Plate Appearance**: `balls`, `strikes`, `zone`, `description`, `events`
- **Batted Ball**: `launch_speed`, `launch_angle`, `hit_distance_sc`, `hit_location`, `bb_type`
- **Expected Stats**: `estimated_ba_using_speedangle`, `estimated_woba_using_speedangle`
- **Game State**: `inning`, `inning_topbot`, `outs_when_up`, `on_1b`, `on_2b`, `on_3b`
- **Physics**: `vx0`, `vy0`, `vz0`, `ax`, `ay`, `az`
- **Strike Zone**: `sz_top`, `sz_bot`, `pfx_x`, `pfx_z`
- **Advanced Metrics**: `woba_value`, `babip_value`, `iso_value`, `barrel`

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_statcast_pitch_id ON statcast_pitches(pitch_id);
CREATE INDEX idx_statcast_game_date ON statcast_pitches(game_date);
CREATE INDEX idx_statcast_batter ON statcast_pitches(batter_id);
CREATE INDEX idx_statcast_pitcher ON statcast_pitches(pitcher_id);
CREATE INDEX idx_statcast_pitch_type ON statcast_pitches(pitch_type);
CREATE INDEX idx_statcast_events ON statcast_pitches(events) WHERE events IS NOT NULL;

-- JSONB performance indexes
CREATE INDEX idx_statcast_launch_speed ON statcast_pitches 
  USING btree ((statcast_data->>'launch_speed')::numeric) 
  WHERE statcast_data->>'launch_speed' IS NOT NULL;

CREATE INDEX idx_statcast_exit_velocity ON statcast_pitches 
  USING btree ((statcast_data->>'launch_speed')::numeric) 
  WHERE (statcast_data->>'launch_speed')::numeric > 0;
```

### 5. FanGraphs Batting Table

Comprehensive batting statistics with 320+ fields per player per season.

```sql
CREATE TABLE fangraphs_batting (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),
    season INTEGER NOT NULL,
    
    -- Time period identifiers
    split_type VARCHAR(20),
    split_value VARCHAR(50),
    
    -- ALL 320+ FanGraphs batting fields stored as JSONB
    batting_stats JSONB NOT NULL,
    
    -- Indexed commonly queried fields
    games_played INTEGER,
    plate_appearances INTEGER,
    avg DECIMAL(5,3),
    obp DECIMAL(5,3),
    slg DECIMAL(5,3),
    ops DECIMAL(5,3),
    woba DECIMAL(5,3),
    wrc_plus INTEGER,
    war_fg DECIMAL(4,1),
    
    date_range_start DATE,
    date_range_end DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Batting Stats JSONB Sample (320+ fields):**
```json
{
  "Name": "Aaron Judge",
  "Team": "NYY",
  "G": 158,
  "AB": 559,
  "PA": 704,
  "H": 180,
  "1B": 85,
  "2B": 36,
  "3B": 3,
  "HR": 56,
  "R": 117,
  "RBI": 144,
  "BB": 133,
  "IBB": 12,
  "SO": 175,
  "HBP": 4,
  "SF": 4,
  "SH": 0,
  "GDP": 15,
  "SB": 10,
  "CS": 2,
  "AVG": 0.322,
  "OBP": 0.458,
  "SLG": 0.701,
  "OPS": 1.159,
  "wOBA": 0.476,
  "wRC+": 219,
  "WAR": 11.3,
  "Barrel%": 20.5,
  "HardHit%": 60.9,
  "xBA": 0.31,
  "xSLG": 0.723,
  "xwOBA": 0.479,
  "EV": 96.8,
  "LA": 18.2,
  "Swing%": 47.1,
  "Contact%": 72.5,
  "Zone%": 44.2,
  "F-Strike%": 62.1,
  "SwStr%": 13.7
}
```

**Major Stat Categories (320+ total fields):**
- **Traditional**: G, AB, PA, H, 1B, 2B, 3B, HR, R, RBI, BB, SO
- **Rate Stats**: AVG, OBP, SLG, OPS, wOBA, wRC+, WAR
- **Plate Discipline**: BB%, K%, SwStr%, Contact%, Zone%, F-Strike%
- **Batted Ball**: EV, LA, Barrel%, HardHit%, Pull%, Cent%, Oppo%
- **Expected Stats**: xBA, xSLG, xwOBA, xISO
- **Pitch Type**: FB%, SL%, CH%, CB% (vs different pitch types)
- **Situational**: RISP, High Leverage, Late & Close
- **Advanced**: UBR, Def, Off, BsR, Clutch, WPA

**Indexes:**
```sql
CREATE INDEX idx_fangraphs_batting_player ON fangraphs_batting(player_id);
CREATE INDEX idx_fangraphs_batting_season ON fangraphs_batting(season);
CREATE INDEX idx_fangraphs_batting_war ON fangraphs_batting(war_fg) WHERE war_fg IS NOT NULL;
CREATE INDEX idx_fangraphs_batting_wrc ON fangraphs_batting(wrc_plus) WHERE wrc_plus IS NOT NULL;

-- JSONB performance indexes for common queries
CREATE INDEX idx_fangraphs_batting_avg ON fangraphs_batting 
  USING btree ((batting_stats->>'AVG')::numeric);
CREATE INDEX idx_fangraphs_batting_ops ON fangraphs_batting 
  USING btree ((batting_stats->>'OPS')::numeric);
```

### 6. FanGraphs Pitching Table

Comprehensive pitching statistics with 393+ fields per pitcher per season.

```sql
CREATE TABLE fangraphs_pitching (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),
    season INTEGER NOT NULL,
    
    -- Time period identifiers
    split_type VARCHAR(20),
    split_value VARCHAR(50),
    
    -- ALL 393+ FanGraphs pitching fields stored as JSONB
    pitching_stats JSONB NOT NULL,
    
    -- Indexed commonly queried fields
    games INTEGER,
    games_started INTEGER,
    innings_pitched DECIMAL(6,1),
    era DECIMAL(4,2),
    whip DECIMAL(4,3),
    fip DECIMAL(4,2),
    war_fg DECIMAL(4,1),
    
    date_range_start DATE,
    date_range_end DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Pitching Stats JSONB Sample (393+ fields):**
```json
{
  "Name": "Jacob deGrom",
  "Team": "TEX",
  "G": 30,
  "GS": 30,
  "W": 11,
  "L": 9,
  "SV": 0,
  "IP": 184.2,
  "H": 125,
  "R": 55,
  "ER": 47,
  "HR": 15,
  "BB": 45,
  "SO": 279,
  "ERA": 2.29,
  "WHIP": 0.921,
  "FIP": 2.67,
  "xFIP": 2.85,
  "WAR": 6.8,
  "K/9": 13.6,
  "BB/9": 2.2,
  "K/BB": 6.2,
  "BABIP": 0.255,
  "LOB%": 0.785,
  "GB%": 38.2,
  "FB%": 43.1,
  "LD%": 18.7,
  "Soft%": 18.9,
  "Med%": 48.7,
  "Hard%": 32.4,
  "Zone%": 47.8,
  "Contact%": 71.2,
  "SwStr%": 16.4,
  "F-Strike%": 64.2,
  "vFA": 96.8,
  "FA%": 42.1,
  "SL%": 31.2,
  "CH%": 15.6,
  "CB%": 11.1
}
```

**Major Stat Categories (393+ total fields):**
- **Traditional**: G, GS, W, L, SV, IP, H, R, ER, HR, BB, SO
- **Rate Stats**: ERA, WHIP, FIP, xFIP, SIERA, WAR, K/9, BB/9
- **Batted Ball**: GB%, FB%, LD%, Soft%, Med%, Hard%
- **Plate Discipline**: Zone%, Contact%, SwStr%, F-Strike%, O-Swing%
- **Pitch Mix**: FA%, SL%, CH%, CB%, CT%, KN% (pitch type percentages)
- **Pitch Velocities**: vFA, vSL, vCH, vCB (average velocities)
- **Pitch Movement**: FA-X, FA-Z, SL-X, SL-Z (horizontal/vertical movement)
- **Situational**: vs RHB, vs LHB, RISP, High Leverage
- **Advanced**: BABIP, LOB%, HR/FB, Clutch, WPA, RE24

**Indexes:**
```sql
CREATE INDEX idx_fangraphs_pitching_player ON fangraphs_pitching(player_id);
CREATE INDEX idx_fangraphs_pitching_season ON fangraphs_pitching(season);
CREATE INDEX idx_fangraphs_pitching_war ON fangraphs_pitching(war_fg) WHERE war_fg IS NOT NULL;
CREATE INDEX idx_fangraphs_pitching_era ON fangraphs_pitching(era) WHERE era IS NOT NULL;

-- JSONB performance indexes
CREATE INDEX idx_fangraphs_pitching_fip ON fangraphs_pitching 
  USING btree ((pitching_stats->>'FIP')::numeric);
CREATE INDEX idx_fangraphs_pitching_kper9 ON fangraphs_pitching 
  USING btree ((pitching_stats->>'K/9')::numeric);
```

## 🔍 Common Query Patterns

### Player Search with Statistics

```sql
-- Search for players with their latest stats
SELECT 
    p.name,
    p.current_team,
    fb.batting_stats->>'AVG' as avg,
    fb.batting_stats->>'HR' as home_runs,
    fb.batting_stats->>'WAR' as war
FROM players p
LEFT JOIN fangraphs_batting fb ON p.id = fb.player_id 
    AND fb.season = 2025
WHERE p.name ILIKE '%judge%'
ORDER BY (fb.batting_stats->>'WAR')::numeric DESC;
```

### Statcast Query Examples

```sql
-- Find all Aaron Judge home runs with exit velocity > 110 mph
SELECT 
    game_date,
    statcast_data->>'launch_speed' as exit_velocity,
    statcast_data->>'launch_angle' as launch_angle,
    statcast_data->>'hit_distance_sc' as distance
FROM statcast_pitches sp
JOIN players p ON sp.batter_id = p.mlb_id
WHERE p.name = 'Aaron Judge'
    AND statcast_data->>'events' = 'home_run'
    AND (statcast_data->>'launch_speed')::numeric > 110
ORDER BY game_date DESC;

-- Average fastball velocity by pitcher
SELECT 
    p.name,
    AVG((sp.statcast_data->>'release_speed')::numeric) as avg_fb_velocity
FROM statcast_pitches sp
JOIN players p ON sp.pitcher_id = p.mlb_id
WHERE sp.statcast_data->>'pitch_type' = 'FF'
    AND sp.game_date >= '2025-01-01'
GROUP BY p.name, p.mlb_id
HAVING COUNT(*) >= 100
ORDER BY avg_fb_velocity DESC;
```

### Advanced Analytics Queries

```sql
-- Top 10 hitters by xwOBA in 2025
SELECT 
    p.name,
    p.current_team,
    (fb.batting_stats->>'PA')::integer as plate_appearances,
    (fb.batting_stats->>'xwOBA')::numeric as expected_woba,
    (fb.batting_stats->>'wOBA')::numeric as actual_woba
FROM players p
JOIN fangraphs_batting fb ON p.id = fb.player_id
WHERE fb.season = 2025
    AND (fb.batting_stats->>'PA')::integer >= 300
ORDER BY (fb.batting_stats->>'xwOBA')::numeric DESC
LIMIT 10;
```

## 📈 Performance Characteristics

### Current Data Volume (July 2025)

| Table | Records | Storage | Avg Query Time |
|-------|---------|---------|---------------|
| `players` | 1,693 | 5 MB | < 10ms |
| `statcast_pitches` | 493,231 | 1.2 GB | 50-200ms |
| `fangraphs_batting` | 2,772 | 25 MB | < 50ms |
| `fangraphs_pitching` | 1,620 | 18 MB | < 50ms |
| `games` | 1,685 | 12 MB | < 20ms |

### Optimization Features

1. **Strategic Indexing**: B-tree indexes on commonly queried fields
2. **JSONB Indexes**: GIN indexes for flexible JSONB queries
3. **Partial Indexes**: Optimized indexes with WHERE conditions
4. **Connection Pooling**: Shared connections across API requests
5. **Query Caching**: Redis caching for expensive aggregations

### Scaling Considerations

- **Horizontal Partitioning**: Table partitioning by season for historical data
- **Read Replicas**: Dedicated read replicas for analytics queries
- **Materialized Views**: Pre-computed aggregations for common queries
- **Archival Strategy**: Move old seasons to separate archive tables

## 🚀 Future Schema Evolution

### Planned Enhancements

1. **Historical Data**: Add support for multiple seasons (2015-2025)
2. **Real-time Updates**: Streaming updates during live games
3. **Advanced Metrics**: Additional calculated fields and indexes
4. **Player Tracking**: GPS-based fielding and baserunning data
5. **Betting Integration**: Odds and line movement tracking

### Migration Strategy

The database is designed for zero-downtime migrations using:
- **Backward Compatible Changes**: New columns with defaults
- **JSONB Flexibility**: New fields added to existing JSONB columns
- **Blue-Green Deployments**: Separate environments for testing
- **Rolling Updates**: Gradual migration of production data

---

**For technical support with database queries or schema questions, contact the development team or reference the API documentation at `/docs`.**