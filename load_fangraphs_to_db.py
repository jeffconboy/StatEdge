#!/usr/bin/env python3
"""
Load FanGraphs Data to Database
===============================

Loads the collected FanGraphs batting data into the PostgreSQL sports_data database.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_fangraphs_to_database():
    """Load FanGraphs batting data to the sports_data database"""
    
    try:
        # Load the CSV data we collected
        logger.info("📂 Loading FanGraphs batting data from CSV...")
        df = pd.read_csv('/home/jeffreyconboy/StatEdge/fangraphs_batting_2025.csv')
        logger.info(f"✅ Loaded {len(df)} records from CSV")
        
        # Connect to your sports_data database
        logger.info("🔌 Connecting to sports_data database...")
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='sports_data',
            user='sports_user',
            password='sports_secure_2025'
        )
        cursor = conn.cursor()
        
        # Check if fangraphs_batting table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'fangraphs_batting'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.info("🏗️ Creating fangraphs_batting table...")
            cursor.execute("""
                CREATE TABLE fangraphs_batting (
                    id SERIAL PRIMARY KEY,
                    player_id INTEGER,
                    season INTEGER,
                    name TEXT,
                    team TEXT,
                    age INTEGER,
                    games INTEGER,
                    plate_appearances INTEGER,
                    at_bats INTEGER,
                    hits INTEGER,
                    home_runs INTEGER,
                    runs INTEGER,
                    rbi INTEGER,
                    walks INTEGER,
                    strikeouts INTEGER,
                    stolen_bases INTEGER,
                    caught_stealing INTEGER,
                    avg DECIMAL(5,3),
                    obp DECIMAL(5,3),
                    slg DECIMAL(5,3),
                    ops DECIMAL(5,3),
                    woba DECIMAL(5,3),
                    wrc_plus INTEGER,
                    war DECIMAL(4,1),
                    babip DECIMAL(5,3),
                    iso DECIMAL(5,3),
                    bb_percent DECIMAL(5,1),
                    k_percent DECIMAL(5,1),
                    hard_hit_percent DECIMAL(5,1),
                    barrel_percent DECIMAL(5,1),
                    exit_velocity DECIMAL(5,1),
                    launch_angle DECIMAL(5,1),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("✅ Created fangraphs_batting table")
        
        # Clear existing 2025 data
        cursor.execute("DELETE FROM fangraphs_batting WHERE season = 2025;")
        logger.info("🗑️ Cleared existing 2025 data")
        
        # Prepare data for insertion
        logger.info("🔄 Preparing data for insertion...")
        records = []
        for _, row in df.iterrows():
            try:
                record = (
                    int(row['IDfg']) if pd.notna(row['IDfg']) else None,  # player_id
                    int(row['Season']) if pd.notna(row['Season']) else 2025,  # season
                    str(row['Name']) if pd.notna(row['Name']) else None,  # name
                    str(row['Team']) if pd.notna(row['Team']) else None,  # team
                    int(row['Age']) if pd.notna(row['Age']) else None,  # age
                    int(row['G']) if pd.notna(row['G']) else None,  # games
                    int(row['PA']) if pd.notna(row['PA']) else None,  # plate_appearances
                    int(row['AB']) if pd.notna(row['AB']) else None,  # at_bats
                    int(row['H']) if pd.notna(row['H']) else None,  # hits
                    int(row['HR']) if pd.notna(row['HR']) else None,  # home_runs
                    int(row['R']) if pd.notna(row['R']) else None,  # runs
                    int(row['RBI']) if pd.notna(row['RBI']) else None,  # rbi
                    int(row['BB']) if pd.notna(row['BB']) else None,  # walks
                    int(row['SO']) if pd.notna(row['SO']) else None,  # strikeouts
                    int(row['SB']) if pd.notna(row['SB']) else None,  # stolen_bases
                    int(row['CS']) if pd.notna(row['CS']) else None,  # caught_stealing
                    float(row['AVG']) if pd.notna(row['AVG']) else None,  # avg
                    float(row['OBP']) if pd.notna(row['OBP']) else None,  # obp
                    float(row['SLG']) if pd.notna(row['SLG']) else None,  # slg
                    float(row['OPS']) if pd.notna(row['OPS']) else None,  # ops
                    float(row['wOBA']) if pd.notna(row['wOBA']) else None,  # woba
                    int(row['wRC+']) if pd.notna(row['wRC+']) else None,  # wrc_plus
                    float(row['WAR']) if pd.notna(row['WAR']) else None,  # war
                    float(row['BABIP']) if pd.notna(row['BABIP']) else None,  # babip
                    float(row['ISO']) if pd.notna(row['ISO']) else None,  # iso
                    float(row['BB%']) if pd.notna(row['BB%']) else None,  # bb_percent
                    float(row['K%']) if pd.notna(row['K%']) else None,  # k_percent
                    float(row['HardHit%']) if pd.notna(row['HardHit%']) else None,  # hard_hit_percent
                    float(row['Barrel%']) if pd.notna(row['Barrel%']) else None,  # barrel_percent
                    float(row['EV']) if pd.notna(row['EV']) else None,  # exit_velocity
                    float(row['LA']) if pd.notna(row['LA']) else None,  # launch_angle
                )
                records.append(record)
            except Exception as e:
                logger.warning(f"Skipping row for {row.get('Name', 'Unknown')}: {e}")
                continue
        
        # Insert data
        logger.info(f"💾 Inserting {len(records)} records...")
        insert_query = """
            INSERT INTO fangraphs_batting (
                player_id, season, name, team, age, games, plate_appearances, 
                at_bats, hits, home_runs, runs, rbi, walks, strikeouts, 
                stolen_bases, caught_stealing, avg, obp, slg, ops, woba, 
                wrc_plus, war, babip, iso, bb_percent, k_percent, 
                hard_hit_percent, barrel_percent, exit_velocity, launch_angle
            ) VALUES %s
        """
        
        execute_values(cursor, insert_query, records)
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM fangraphs_batting WHERE season = 2025;")
        count = cursor.fetchone()[0]
        
        logger.info(f"✅ Successfully inserted {count} FanGraphs batting records")
        
        # Show sample data
        cursor.execute("""
            SELECT name, team, avg, obp, slg, woba, wrc_plus, war 
            FROM fangraphs_batting 
            WHERE season = 2025 
            ORDER BY war DESC NULLS LAST 
            LIMIT 10;
        """)
        top_players = cursor.fetchall()
        
        logger.info("\n🏆 Top 10 players by WAR:")
        for player in top_players:
            logger.info(f"   {player[0]} ({player[1]}): {player[2]:.3f} AVG, {player[3]:.3f} OBP, {player[4]:.3f} SLG, {player[5]:.3f} wOBA, {player[6]} wRC+, {player[7]} WAR")
        
        conn.commit()
        logger.info("🎉 FanGraphs batting data successfully loaded!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    load_fangraphs_to_database()