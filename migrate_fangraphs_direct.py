#!/usr/bin/env python3
"""
Direct FanGraphs Migration Script
================================
"""

import sqlite3
import psycopg2
import logging
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_fangraphs_data():
    """Direct migration of FanGraphs data from SQLite to PostgreSQL"""
    
    # Database connections
    sqlite_path = '/mnt/e/StatEdge/statedge_mlb_full.db'
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL
        postgres_conn = psycopg2.connect(
            host='localhost',
            port=15432,
            database='statedge',
            user='statedge_user',
            password='statedge_pass'
        )
        postgres_cursor = postgres_conn.cursor()
        
        # Temporarily disable foreign key constraints
        logger.info("⚙️ Temporarily disabling foreign key constraints...")
        postgres_cursor.execute("SET session_replication_role = replica;")
        
        logger.info("🔄 Migrating FanGraphs batting data...")
        
        # Get batting data from SQLite
        sqlite_cursor.execute("SELECT * FROM fangraphs_batting_2025")
        batting_data = sqlite_cursor.fetchall()
        
        # Get column names
        sqlite_cursor.execute("PRAGMA table_info(fangraphs_batting_2025)")
        batting_columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        logger.info(f"📊 Found {len(batting_data)} batting records")
        logger.info(f"📋 Columns: {batting_columns[:10]}... (showing first 10)")
        
        if batting_data:
            # Insert into PostgreSQL batting table
            placeholders = ','.join(['%s'] * len(batting_columns))
            insert_query = f"""
                INSERT INTO fangraphs_batting 
                (player_id, season, split_type, split_value, batting_stats, 
                 games_played, plate_appearances, avg, obp, slg, ops, woba, wrc_plus, 
                 war_fg, date_range_start, date_range_end, created_at) 
                VALUES %s
                ON CONFLICT DO NOTHING
            """
            
            # Transform data to match our schema
            transformed_data = []
            for row in batting_data:
                # Map SQLite data to PostgreSQL schema based on actual structure
                # SQLite structure: (player_id, player_name, team, games, plate_appearances, at_bats, runs, hits, doubles, triples, home_runs, rbi, stolen_bases, caught_stealing, walks, strikeouts, batting_avg, on_base_pct, slugging_pct, ops, wrc_plus, war, woba, collection_date)
                transformed_row = (
                    str(row[0]),  # player_id (using actual SQLite player_id)
                    2025,  # season
                    'season',  # split_type
                    'all',  # split_value
                    '{}',  # batting_stats (JSON)
                    row[3] if row[3] is not None else 0,  # games
                    row[4] if row[4] is not None else 0,  # plate_appearances
                    row[16] if row[16] is not None else 0.0,  # batting_avg
                    row[17] if row[17] is not None else 0.0,  # on_base_pct
                    row[18] if row[18] is not None else 0.0,  # slugging_pct
                    row[19] if row[19] is not None else 0.0,  # ops
                    row[22] if row[22] is not None else 0.0,  # woba
                    row[20] if row[20] is not None else 0,  # wrc_plus
                    row[21] if row[21] is not None else 0.0,  # war
                    '2025-01-01',  # date_range_start
                    '2025-12-31',  # date_range_end
                    'now()'  # created_at
                )
                transformed_data.append(transformed_row)
            
            execute_values(postgres_cursor, insert_query, transformed_data)
            logger.info(f"✅ Migrated {len(batting_data)} batting records")
        
        logger.info("🔄 Migrating FanGraphs pitching data...")
        
        # Get pitching data from SQLite
        sqlite_cursor.execute("SELECT * FROM fangraphs_pitching_2025")
        pitching_data = sqlite_cursor.fetchall()
        
        logger.info(f"📊 Found {len(pitching_data)} pitching records")
        
        if pitching_data:
            # Insert into PostgreSQL pitching table
            insert_query = f"""
                INSERT INTO fangraphs_pitching 
                (player_id, season, split_type, split_value, pitching_stats,
                 games, games_started, innings_pitched, era, whip, fip, war_fg,
                 date_range_start, date_range_end, created_at)
                VALUES %s
                ON CONFLICT DO NOTHING
            """
            
            # Transform pitching data
            transformed_pitching = []
            for row in pitching_data:
                # Map SQLite pitching data based on actual structure
                # Key columns: IDfg(1), Season(2), Name(3), Team(4), G(10), GS(11), IP(16), ERA(9), WHIP(45), FIP(48), WAR(8)
                transformed_row = (
                    str(row[1]) if row[1] is not None else str(row[0]),  # player_id (IDfg or fallback to id)
                    2025,  # season
                    'season',  # split_type
                    'all',  # split_value
                    '{}',  # pitching_stats (JSON)
                    row[10] if row[10] is not None else 0,  # games (G)
                    row[11] if row[11] is not None else 0,  # games_started (GS)
                    row[16] if row[16] is not None else 0.0,  # innings_pitched (IP)
                    row[9] if row[9] is not None else 0.0,  # era (ERA)
                    row[45] if row[45] is not None else 0.0,  # whip (WHIP)
                    row[48] if row[48] is not None else 0.0,  # fip (FIP)
                    row[8] if row[8] is not None else 0.0,  # war (WAR)
                    '2025-01-01',  # date_range_start
                    '2025-12-31',  # date_range_end
                    'now()'  # created_at
                )
                transformed_pitching.append(transformed_row)
            
            execute_values(postgres_cursor, insert_query, transformed_pitching)
            logger.info(f"✅ Migrated {len(pitching_data)} pitching records")
        
        # Verify migration
        postgres_cursor.execute("SELECT COUNT(*) FROM fangraphs_batting")
        batting_count = postgres_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM fangraphs_pitching")
        pitching_count = postgres_cursor.fetchone()[0]
        
        logger.info(f"🎉 Migration complete!")
        logger.info(f"   - FanGraphs batting: {batting_count:,} records")
        logger.info(f"   - FanGraphs pitching: {pitching_count:,} records")
        
        postgres_conn.commit()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        postgres_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    migrate_fangraphs_data()