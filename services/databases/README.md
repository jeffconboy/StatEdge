# Database Services

Comprehensive PostgreSQL database architecture for the StatEdge platform with specialized databases for sports data and user management.

## Overview

The StatEdge platform utilizes a dual-database architecture with separate PostgreSQL instances optimized for different workloads and data types.

## Database Architecture

### Sports Database (Port 5432)
**Purpose**: Central repository for all baseball analytics data

- **Host**: `sports-database:5432`
- **Database**: `sports_data`
- **User**: `sports_user`
- **Password**: `sports_secure_2025`

### Users Database (Port 5433)
**Purpose**: User management, authentication, and subscription data

- **Host**: `users-database:5433`
- **Database**: `users_data`
- **User**: `user_admin`
- **Password**: `user_secure_2025`

## Sports Database Schema

### Core Tables

#### Statcast Table (470k+ records)
```sql
CREATE TABLE statcast (
    id SERIAL PRIMARY KEY,
    pitch_type VARCHAR(10),
    game_date DATE,
    release_speed DECIMAL(5,2),
    release_pos_x DECIMAL(6,3),
    release_pos_z DECIMAL(6,3),
    player_name VARCHAR(100),
    batter VARCHAR(100),
    pitcher VARCHAR(100),
    events VARCHAR(50),
    description VARCHAR(200),
    spin_dir DECIMAL(6,2),
    spin_rate_deprecated DECIMAL(8,2),
    break_angle_deprecated DECIMAL(6,2),
    break_length_deprecated DECIMAL(6,2),
    zone INTEGER,
    des VARCHAR(500),
    game_type VARCHAR(10),
    stand VARCHAR(1),
    p_throws VARCHAR(1),
    home_team VARCHAR(10),
    away_team VARCHAR(10),
    type VARCHAR(10),
    hit_location INTEGER,
    bb_type VARCHAR(20),
    balls INTEGER,
    strikes INTEGER,
    game_year INTEGER,
    pfx_x DECIMAL(6,3),
    pfx_z DECIMAL(6,3),
    plate_x DECIMAL(6,3),
    plate_z DECIMAL(6,3),
    on_3b VARCHAR(100),
    on_2b VARCHAR(100),
    on_1b VARCHAR(100),
    outs_when_up INTEGER,
    inning INTEGER,
    inning_topbot VARCHAR(10),
    hc_x DECIMAL(8,3),
    hc_y DECIMAL(8,3),
    tfs_deprecated DECIMAL(10,6),
    tfs_zulu_deprecated TIMESTAMP,
    fielder_2 INTEGER,
    umpire VARCHAR(100),
    sv_id VARCHAR(50),
    vx0 DECIMAL(8,4),
    vy0 DECIMAL(8,4),
    vz0 DECIMAL(8,4),
    ax DECIMAL(8,4),
    ay DECIMAL(8,4),
    az DECIMAL(8,4),
    sz_top DECIMAL(6,3),
    sz_bot DECIMAL(6,3),
    hit_distance_sc INTEGER,
    launch_speed DECIMAL(6,2),
    launch_angle DECIMAL(6,2),
    effective_speed DECIMAL(6,2),
    release_spin_rate DECIMAL(8,2),
    release_extension DECIMAL(6,3),
    game_pk INTEGER,
    pitcher_1 INTEGER,
    fielder_2_1 INTEGER,
    fielder_3 INTEGER,
    fielder_4 INTEGER,
    fielder_5 INTEGER,
    fielder_6 INTEGER,
    fielder_7 INTEGER,
    fielder_8 INTEGER,
    fielder_9 INTEGER,
    release_pos_y DECIMAL(6,3),
    estimated_ba_using_speedangle DECIMAL(6,4),
    estimated_woba_using_speedangle DECIMAL(6,4),
    woba_value DECIMAL(6,4),
    woba_denom INTEGER,
    babip_value DECIMAL(6,4),
    iso_value DECIMAL(6,4),
    launch_speed_angle INTEGER,
    at_bat_number INTEGER,
    pitch_number INTEGER,
    pitch_name VARCHAR(50),
    home_score INTEGER,
    away_score INTEGER,
    bat_score INTEGER,
    fld_score INTEGER,
    post_away_score INTEGER,
    post_home_score INTEGER,
    post_bat_score INTEGER,
    post_fld_score INTEGER,
    if_fielding_alignment VARCHAR(20),
    of_fielding_alignment VARCHAR(20),
    spin_axis DECIMAL(6,2),
    delta_home_win_exp DECIMAL(8,6),
    delta_run_exp DECIMAL(8,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### FanGraphs Batting (320+ columns)
```sql
CREATE TABLE fangraphs_batting (
    id SERIAL PRIMARY KEY,
    season INTEGER,
    name VARCHAR(100),
    team VARCHAR(10),
    g INTEGER,
    ab INTEGER,
    pa INTEGER,
    h INTEGER,
    "1b" INTEGER,
    "2b" INTEGER,
    "3b" INTEGER,
    hr INTEGER,
    r INTEGER,
    rbi INTEGER,
    bb INTEGER,
    ibb INTEGER,
    so INTEGER,
    hbp INTEGER,
    sf INTEGER,
    sh INTEGER,
    gdp INTEGER,
    sb INTEGER,
    cs INTEGER,
    avg DECIMAL(6,4),
    gb INTEGER,
    fb INTEGER,
    ld INTEGER,
    iffb INTEGER,
    pitches INTEGER,
    balls INTEGER,
    strikes INTEGER,
    iff INTEGER,
    bu INTEGER,
    buh INTEGER,
    bb_percent DECIMAL(6,3),
    k_percent DECIMAL(6,3),
    bb_k DECIMAL(6,3),
    obp DECIMAL(6,4),
    slg DECIMAL(6,4),
    ops DECIMAL(6,4),
    iso DECIMAL(6,4),
    babip DECIMAL(6,4),
    gb_fb DECIMAL(6,3),
    ld_percent DECIMAL(6,3),
    gb_percent DECIMAL(6,3),
    fb_percent DECIMAL(6,3),
    iffb_percent DECIMAL(6,3),
    hr_fb DECIMAL(6,3),
    iff_percent DECIMAL(6,3),
    buh_percent DECIMAL(6,3),
    pull_percent DECIMAL(6,3),
    cent_percent DECIMAL(6,3),
    oppo_percent DECIMAL(6,3),
    soft_percent DECIMAL(6,3),
    med_percent DECIMAL(6,3),
    hard_percent DECIMAL(6,3),
    tto DECIMAL(6,3),
    woba DECIMAL(6,4),
    wrc_plus INTEGER,
    bsr DECIMAL(6,2),
    off DECIMAL(6,2),
    def DECIMAL(6,2),
    war DECIMAL(6,2),
    -- Additional 280+ metrics columns...
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### FanGraphs Pitching (393+ columns)
```sql
CREATE TABLE fangraphs_pitching (
    id SERIAL PRIMARY KEY,
    season INTEGER,
    name VARCHAR(100),
    team VARCHAR(10),
    w INTEGER,
    l INTEGER,
    era DECIMAL(6,3),
    g INTEGER,
    gs INTEGER,
    cg INTEGER,
    sho INTEGER,
    sv INTEGER,
    bs INTEGER,
    ip DECIMAL(7,2),
    tbf INTEGER,
    h INTEGER,
    r INTEGER,
    er INTEGER,
    hr INTEGER,
    bb INTEGER,
    ibb INTEGER,
    hbp INTEGER,
    wp INTEGER,
    bk INTEGER,
    so INTEGER,
    gb INTEGER,
    fb INTEGER,
    ld INTEGER,
    iffb INTEGER,
    balls INTEGER,
    strikes INTEGER,
    pitches INTEGER,
    rs INTEGER,
    iff INTEGER,
    bu INTEGER,
    buh INTEGER,
    k_9 DECIMAL(6,3),
    bb_9 DECIMAL(6,3),
    k_bb DECIMAL(6,3),
    h_9 DECIMAL(6,3),
    hr_9 DECIMAL(6,3),
    avg DECIMAL(6,4),
    whip DECIMAL(6,3),
    babip DECIMAL(6,4),
    lob_percent DECIMAL(6,3),
    fip DECIMAL(6,3),
    gb_fb DECIMAL(6,3),
    ld_percent DECIMAL(6,3),
    gb_percent DECIMAL(6,3),
    fb_percent DECIMAL(6,3),
    iffb_percent DECIMAL(6,3),
    hr_fb DECIMAL(6,3),
    iff_percent DECIMAL(6,3),
    buh_percent DECIMAL(6,3),
    pull_percent DECIMAL(6,3),
    cent_percent DECIMAL(6,3),
    oppo_percent DECIMAL(6,3),
    soft_percent DECIMAL(6,3),
    med_percent DECIMAL(6,3),
    hard_percent DECIMAL(6,3),
    siera DECIMAL(6,3),
    xfip DECIMAL(6,3),
    war DECIMAL(6,2),
    -- Additional 340+ metrics columns...
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Player Lookup (25k+ records)
```sql
CREATE TABLE player_lookup (
    id SERIAL PRIMARY KEY,
    name_last VARCHAR(50),
    name_first VARCHAR(50),
    key_mlbam INTEGER UNIQUE,
    key_retro VARCHAR(20),
    key_bbref VARCHAR(20),
    key_fangraphs INTEGER,
    mlb_played_first INTEGER,
    mlb_played_last INTEGER,
    col_played_first INTEGER,
    col_played_last INTEGER,
    pro_played_first INTEGER,
    pro_played_last INTEGER,
    full_name VARCHAR(100),
    birth_year INTEGER,
    death_year INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mlbam (key_mlbam),
    INDEX idx_fangraphs (key_fangraphs),
    INDEX idx_name (name_last, name_first),
    INDEX idx_full_name (full_name)
);
```

#### Games Table
```sql
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER UNIQUE,
    game_date DATE,
    home_team VARCHAR(10),
    away_team VARCHAR(10),
    home_score INTEGER,
    away_score INTEGER,
    game_type VARCHAR(10),
    status VARCHAR(20),
    inning INTEGER,
    inning_state VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_game_date (game_date),
    INDEX idx_teams (home_team, away_team),
    INDEX idx_game_pk (game_pk)
);
```

#### Betting Odds Table
```sql
CREATE TABLE betting_odds (
    id SERIAL PRIMARY KEY,
    game_pk INTEGER,
    sportsbook VARCHAR(50),
    home_ml DECIMAL(7,2),
    away_ml DECIMAL(7,2),
    over_under DECIMAL(4,1),
    over_odds DECIMAL(7,2),
    under_odds DECIMAL(7,2),
    home_spread DECIMAL(4,1),
    home_spread_odds DECIMAL(7,2),
    away_spread DECIMAL(4,1),
    away_spread_odds DECIMAL(7,2),
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_pk) REFERENCES games(game_pk),
    INDEX idx_game_odds (game_pk, sportsbook),
    INDEX idx_timestamp (timestamp)
);
```

## Users Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_active_users (is_active, is_verified)
);
```

#### Subscription Tiers Table
```sql
CREATE TABLE subscription_tiers (
    id SERIAL PRIMARY KEY,
    tier_name VARCHAR(20) UNIQUE NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    monthly_price DECIMAL(8,2) NOT NULL DEFAULT 0,
    yearly_price DECIMAL(8,2) NOT NULL DEFAULT 0,
    features JSONB NOT NULL,
    api_rate_limit INTEGER DEFAULT 100,
    max_historical_data_years INTEGER DEFAULT 1,
    advanced_analytics BOOLEAN DEFAULT false,
    priority_support BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### User Subscriptions Table
```sql
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tier_id INTEGER REFERENCES subscription_tiers(id),
    status VARCHAR(20) DEFAULT 'active',
    billing_cycle VARCHAR(10) DEFAULT 'monthly',
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    external_subscription_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_subscription (user_id, status),
    INDEX idx_period_end (current_period_end)
);
```

#### API Usage Table
```sql
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_status INTEGER,
    response_time_ms INTEGER,
    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    request_ip INET,
    user_agent TEXT,
    INDEX idx_user_usage (user_id, request_timestamp),
    INDEX idx_endpoint_usage (endpoint, request_timestamp),
    INDEX idx_timestamp (request_timestamp)
);
```

## Database Configuration

### Environment Variables

#### Sports Database
```bash
# Sports Database Configuration
SPORTS_DATABASE_URL=postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data
SPORTS_DB_HOST=sports-database
SPORTS_DB_PORT=5432
SPORTS_DB_NAME=sports_data
SPORTS_DB_USER=sports_user
SPORTS_DB_PASSWORD=sports_secure_2025

# Connection Pool Settings
SPORTS_DB_MIN_CONNECTIONS=5
SPORTS_DB_MAX_CONNECTIONS=25
SPORTS_DB_CONNECTION_TIMEOUT=30
```

#### Users Database
```bash
# Users Database Configuration
USERS_DATABASE_URL=postgresql://user_admin:user_secure_2025@users-database:5433/users_data
USERS_DB_HOST=users-database
USERS_DB_PORT=5433
USERS_DB_NAME=users_data
USERS_DB_USER=user_admin
USERS_DB_PASSWORD=user_secure_2025

# Connection Pool Settings
USERS_DB_MIN_CONNECTIONS=3
USERS_DB_MAX_CONNECTIONS=15
USERS_DB_CONNECTION_TIMEOUT=30
```

## Performance Optimization

### Indexing Strategy

#### Sports Database Indexes
```sql
-- Player name lookups
CREATE INDEX idx_statcast_player ON statcast(player_name);
CREATE INDEX idx_statcast_batter ON statcast(batter);
CREATE INDEX idx_statcast_pitcher ON statcast(pitcher);

-- Date-based queries
CREATE INDEX idx_statcast_date ON statcast(game_date);
CREATE INDEX idx_fangraphs_batting_season ON fangraphs_batting(season);
CREATE INDEX idx_fangraphs_pitching_season ON fangraphs_pitching(season);

-- Analytics queries
CREATE INDEX idx_statcast_launch_data ON statcast(launch_speed, launch_angle) WHERE launch_speed IS NOT NULL;
CREATE INDEX idx_fangraphs_batting_war ON fangraphs_batting(war DESC);
CREATE INDEX idx_fangraphs_pitching_era ON fangraphs_pitching(era);

-- Game data
CREATE INDEX idx_games_date_teams ON games(game_date, home_team, away_team);
CREATE INDEX idx_betting_odds_game_time ON betting_odds(game_pk, timestamp);
```

#### Users Database Indexes
```sql
-- Authentication
CREATE INDEX idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX idx_users_username_active ON users(username) WHERE is_active = true;

-- Subscription queries
CREATE INDEX idx_active_subscriptions ON user_subscriptions(user_id, status) WHERE status = 'active';
CREATE INDEX idx_subscription_expiry ON user_subscriptions(current_period_end) WHERE status = 'active';

-- Usage analytics
CREATE INDEX idx_api_usage_user_date ON api_usage(user_id, request_timestamp);
CREATE INDEX idx_api_usage_hourly ON api_usage(DATE_TRUNC('hour', request_timestamp), user_id);
```

### Connection Pooling

#### Sports Database Pool
```python
# Sports database connection pool
SPORTS_DB_CONFIG = {
    "host": "sports-database",
    "port": 5432,
    "database": "sports_data",
    "user": "sports_user",
    "password": "sports_secure_2025",
    "min_size": 5,
    "max_size": 25,
    "max_queries": 50000,
    "max_inactive_connection_lifetime": 3600
}
```

#### Users Database Pool
```python
# Users database connection pool
USERS_DB_CONFIG = {
    "host": "users-database",
    "port": 5433,
    "database": "users_data",
    "user": "user_admin",
    "password": "user_secure_2025",
    "min_size": 3,
    "max_size": 15,
    "max_queries": 10000,
    "max_inactive_connection_lifetime": 1800
}
```

## Data Migration

### From SQLite to PostgreSQL

#### Migration Scripts
```bash
# Sports data migration
python scripts/migrate_sports_data.py \
  --source-db /mnt/e/StatEdge/statedge_mlb_full.db \
  --target-db postgresql://sports_user:sports_secure_2025@sports-database:5432/sports_data

# User data migration (if applicable)
python scripts/migrate_user_data.py \
  --source-db /path/to/users.db \
  --target-db postgresql://user_admin:user_secure_2025@users-database:5433/users_data
```

#### Data Validation
```sql
-- Verify migration completeness
SELECT 'statcast' as table_name, COUNT(*) as record_count FROM statcast
UNION ALL
SELECT 'fangraphs_batting', COUNT(*) FROM fangraphs_batting
UNION ALL
SELECT 'fangraphs_pitching', COUNT(*) FROM fangraphs_pitching
UNION ALL
SELECT 'player_lookup', COUNT(*) FROM player_lookup;
```

## Backup & Recovery

### Automated Backups
```bash
# Sports database backup
pg_dump -h sports-database -p 5432 -U sports_user -d sports_data \
  --no-password --format=custom --compress=9 \
  > backups/sports_data_$(date +%Y%m%d_%H%M%S).dump

# Users database backup
pg_dump -h users-database -p 5433 -U user_admin -d users_data \
  --no-password --format=custom --compress=9 \
  > backups/users_data_$(date +%Y%m%d_%H%M%S).dump
```

### Recovery Procedures
```bash
# Restore sports database
pg_restore -h sports-database -p 5432 -U sports_user -d sports_data \
  --no-password --clean --if-exists \
  backups/sports_data_20250726_120000.dump

# Restore users database
pg_restore -h users-database -p 5433 -U user_admin -d users_data \
  --no-password --clean --if-exists \
  backups/users_data_20250726_120000.dump
```

## Monitoring & Health

### Database Health Checks
```sql
-- Sports database health
SELECT 
    'sports_database' as database,
    pg_database_size('sports_data') as size_bytes,
    (SELECT COUNT(*) FROM statcast) as statcast_records,
    (SELECT COUNT(*) FROM fangraphs_batting) as batting_records,
    (SELECT COUNT(*) FROM fangraphs_pitching) as pitching_records,
    (SELECT COUNT(*) FROM player_lookup) as player_records;

-- Users database health
SELECT 
    'users_database' as database,
    pg_database_size('users_data') as size_bytes,
    (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
    (SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active') as active_subscriptions,
    (SELECT COUNT(*) FROM api_usage WHERE request_timestamp > NOW() - INTERVAL '1 day') as daily_api_calls;
```

### Performance Monitoring
```sql
-- Query performance analysis
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Connection monitoring
SELECT 
    datname,
    state,
    COUNT(*) as connection_count
FROM pg_stat_activity 
GROUP BY datname, state;
```

## Docker Configuration

### Docker Compose Services
```yaml
services:
  sports-database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sports_data
      POSTGRES_USER: sports_user
      POSTGRES_PASSWORD: sports_secure_2025
    ports:
      - "5432:5432"
    volumes:
      - sports_data:/var/lib/postgresql/data
      - ./sql/sports_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sports_user -d sports_data"]
      interval: 10s
      timeout: 5s
      retries: 5

  users-database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: users_data
      POSTGRES_USER: user_admin
      POSTGRES_PASSWORD: user_secure_2025
    ports:
      - "5433:5432"
    volumes:
      - users_data:/var/lib/postgresql/data
      - ./sql/users_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user_admin -d users_data"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  sports_data:
  users_data:
```

### Database Initialization
```bash
# Start databases
docker-compose up -d sports-database users-database

# Wait for initialization
docker-compose logs -f sports-database users-database

# Verify connectivity
docker exec -it sports-database psql -U sports_user -d sports_data -c "SELECT version();"
docker exec -it users-database psql -U user_admin -d users_data -c "SELECT version();"
```

## Security

### Database Security
- **Network isolation**: Databases only accessible from service containers
- **Authentication**: Strong passwords and user separation
- **Encryption**: SSL/TLS for all connections
- **Backup encryption**: Encrypted backup storage

### Access Control
```sql
-- Sports database permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO sports_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO sports_user;

-- Users database permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO user_admin;
```

---

The database services provide a robust, scalable foundation for the StatEdge platform with optimized performance, comprehensive monitoring, and enterprise-grade security features.