# Database Structure Analysis

## Database Connection Details

**Working Connection:**
- Database: `sports_data` 
- Host: `localhost:5432`
- User: `sports_user`
- Password: `sports_secure_2025`

**Backend Expected Connection (from connection.py):**
- Default: `postgresql://sports_user:sports_secure_2025@sports-db:5432/sports_data`
- The backend expects to connect to `sports-db` hostname, but the actual database is on `localhost`

## Table Structures Found

### 1. mlb_players (781 records)

**Key Findings:**
- ✅ Table exists and has data
- Column names use **snake_case**: `player_id`, `team_id`, `full_name`, `jersey_number`, etc.
- Primary key: `id` (auto-increment)
- Season column: `season` (integer)

**Key Columns:**
```
id, player_id, team_id, full_name, jersey_number, position_code, 
position_name, position_type, position_abbreviation, status_code, 
status_description, roster_type, season, created_at, updated_at
```

### 2. fangraphs_batting (1,323 records)

**Key Findings:**
- ✅ Table exists and has substantial data
- Column names use **Title Case with special characters**: `IDfg`, `Season`, `Name`, `Team`, `1B`, `2B`, `3B`, `BB%`, `K%`, etc.
- Primary key: Composite of `IDfg` and `Season`
- Season column: `Season` (bigint, Title Case)

**Critical API Issue:**
The backend code is likely expecting lowercase column names like `season`, `batting_stats`, but the actual columns are:
- `Season` (not `season`)
- Individual stat columns like `AVG`, `HR`, `RBI`, `OBP`, `SLG`, etc. (not a JSON `batting_stats` field)

**Key Stat Columns:**
```
IDfg, Season, Name, Team, Age, G, AB, PA, H, 1B, 2B, 3B, HR, R, RBI, 
BB, IBB, SO, HBP, SF, SH, GDP, SB, CS, AVG, OBP, SLG, OPS, ISO, 
BABIP, wOBA, wRAA, wRC, WAR, etc.
```

### 3. fangraphs_pitching (1,066 records)

**Key Findings:**
- ✅ Table exists and has data
- Similar structure to batting - **Title Case columns**: `IDfg`, `Season`, `Name`, `Team`
- Season column: `Season` (bigint, Title Case)
- Individual pitching stat columns, not JSON

**Key Stat Columns:**
```
IDfg, Season, Name, Team, Age, W, L, WAR, ERA, G, GS, CG, ShO, SV, 
BS, IP, TBF, H, R, ER, HR, BB, IBB, SO, HBP, BK, WP, BF, etc.
```

### 4. statcast (472,556 records)

**Key Findings:**
- ✅ Table exists with substantial data (470K+ records)
- Column names use **snake_case**: `pitch_type`, `game_date`, `release_speed`, `player_name`, etc.
- No primary key apparent - appears to be pitch-by-pitch data
- Season information in: `game_year` (bigint)

**Key Columns:**
```
pitch_type, game_date, release_speed, release_pos_x, release_pos_z, 
player_name, batter, pitcher, events, description, zone, home_team, 
away_team, hit_location, bb_type, balls, strikes, game_year, 
pfx_x, pfx_z, plate_x, plate_z, inning, etc.
```

## Critical Backend API Issues Identified

### Issue 1: Column Name Casing Mismatch

**Problem:** Backend code expects lowercase column names but tables use different casing:

- `mlb_players`: Uses snake_case ✅ (likely works)
- `fangraphs_batting`: Uses Title Case ❌ (will fail)
- `fangraphs_pitching`: Uses Title Case ❌ (will fail)  
- `statcast`: Uses snake_case ✅ (likely works)

### Issue 2: Data Structure Mismatch

**Problem:** Backend might expect JSON fields like `batting_stats`, but the actual structure has individual columns for each statistic.

**FanGraphs tables have 320+ individual columns for batting and 393+ for pitching**, not consolidated JSON fields.

### Issue 3: Season Column Variations

**Problem:** Different tables use different column names/types for season:
- `mlb_players.season` (integer, snake_case)
- `fangraphs_batting.Season` (bigint, Title Case)
- `fangraphs_pitching.Season` (bigint, Title Case)
- `statcast.game_year` (bigint, snake_case)

### Issue 4: Connection Hostname

**Problem:** Backend expects `sports-db` hostname but database is actually on `localhost`

## Recommended Fixes

### 1. Update Database Connection
Change backend connection string from:
```
postgresql://sports_user:sports_secure_2025@sports-db:5432/sports_data
```
To:
```
postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data
```

### 2. Fix Column Name Queries
For FanGraphs tables, use proper Title Case column names:
```sql
-- Wrong
SELECT season, name, avg FROM fangraphs_batting;

-- Correct  
SELECT "Season", "Name", "AVG" FROM fangraphs_batting;
```

### 3. Handle Individual Stat Columns
Instead of expecting `batting_stats` JSON field, query individual columns:
```sql
SELECT "IDfg", "Season", "Name", "Team", "AVG", "HR", "RBI", "OBP", "SLG", "WAR"
FROM fangraphs_batting 
WHERE "Season" = 2025;
```

### 4. Standardize Season Queries
Use appropriate season column for each table:
- `mlb_players`: `season`
- `fangraphs_batting`: `"Season"`
- `fangraphs_pitching`: `"Season"`
- `statcast`: `game_year`

## Test Queries

Here are working queries to test the corrected API:

```sql
-- MLB Players (works)
SELECT player_id, full_name, team_id, season 
FROM mlb_players 
WHERE season = 2025;

-- FanGraphs Batting (corrected)
SELECT "IDfg", "Season", "Name", "Team", "AVG", "HR", "RBI" 
FROM fangraphs_batting 
WHERE "Season" = 2025;

-- FanGraphs Pitching (corrected)  
SELECT "IDfg", "Season", "Name", "Team", "ERA", "W", "L", "SO"
FROM fangraphs_pitching
WHERE "Season" = 2025;

-- Statcast (works)
SELECT player_name, pitcher, batter, events, game_year
FROM statcast 
WHERE game_year = 2025 
LIMIT 10;
```