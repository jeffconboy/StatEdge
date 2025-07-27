#!/usr/bin/env python3
"""
Migrate Statcast Data to sports_data Database
============================================

Migrates Statcast and other important data from statedge to sports_data database.
"""

import psycopg2
import logging
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_statcast_data():
    """Migrate Statcast data from statedge to sports_data"""
    
    try:
        # Connect to source database (statedge)
        logger.info("🔌 Connecting to source database (statedge)...")
        source_conn = psycopg2.connect(
            host='localhost',
            port=15432,
            database='statedge',
            user='statedge_user',
            password='statedge_pass'
        )
        source_cursor = source_conn.cursor()
        
        # Connect to destination database (sports_data)
        logger.info("🔌 Connecting to destination database (sports_data)...")
        dest_conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='sports_data',
            user='sports_user',
            password='sports_secure_2025'
        )
        dest_cursor = dest_conn.cursor()
        
        # Check Statcast table structure in destination
        dest_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'statcast'
            );
        """)
        statcast_exists = dest_cursor.fetchone()[0]
        
        if not statcast_exists:
            logger.info("🏗️ Creating statcast table in sports_data...")
            # Get CREATE TABLE statement from source
            source_cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'statcast' 
                ORDER BY ordinal_position;
            """)
            columns = source_cursor.fetchall()
            
            # Create table (simplified approach - copy structure)
            dest_cursor.execute("""
                CREATE TABLE IF NOT EXISTS statcast (
                    LIKE statcast INCLUDING ALL
                );
            """)
        
        # Get Statcast data count from source
        source_cursor.execute("SELECT COUNT(*) FROM statcast;")
        statcast_count = source_cursor.fetchone()[0]
        logger.info(f"📊 Found {statcast_count:,} Statcast records to migrate")
        
        if statcast_count > 0:
            # Clear existing Statcast data in destination
            dest_cursor.execute("TRUNCATE TABLE statcast;")
            logger.info("🗑️ Cleared existing Statcast data in sports_data")
            
            # Migrate in batches to handle large dataset
            batch_size = 10000
            offset = 0
            total_migrated = 0
            
            while offset < statcast_count:
                logger.info(f"📦 Migrating batch {offset + 1:,} to {min(offset + batch_size, statcast_count):,}")
                
                # Get batch from source
                source_cursor.execute(f"""
                    SELECT * FROM statcast 
                    ORDER BY game_date, game_pk 
                    LIMIT {batch_size} OFFSET {offset};
                """)
                batch_data = source_cursor.fetchall()
                
                if not batch_data:
                    break
                
                # Get column names for INSERT
                source_cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'statcast' 
                    ORDER BY ordinal_position;
                """)
                column_names = [row[0] for row in source_cursor.fetchall()]
                
                # Insert batch into destination
                placeholders = ','.join(['%s'] * len(column_names))
                insert_query = f"INSERT INTO statcast ({','.join(column_names)}) VALUES ({placeholders})"
                
                execute_values(dest_cursor, insert_query, batch_data, page_size=1000)
                
                total_migrated += len(batch_data)
                offset += batch_size
                
                logger.info(f"   ✅ Migrated {total_migrated:,} / {statcast_count:,} records")
        
        # Migrate players data
        logger.info("👥 Migrating players data...")
        source_cursor.execute("SELECT COUNT(*) FROM players;")
        players_count = source_cursor.fetchone()[0]
        
        if players_count > 0:
            source_cursor.execute("SELECT * FROM players;")
            players_data = source_cursor.fetchall()
            
            # Clear and insert players
            dest_cursor.execute("TRUNCATE TABLE players CASCADE;")
            
            source_cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'players' 
                ORDER BY ordinal_position;
            """)
            player_columns = [row[0] for row in source_cursor.fetchall()]
            
            placeholders = ','.join(['%s'] * len(player_columns))
            insert_query = f"INSERT INTO players ({','.join(player_columns)}) VALUES ({placeholders})"
            execute_values(dest_cursor, insert_query, players_data)
            
            logger.info(f"✅ Migrated {players_count:,} players")
        
        # Migrate MLB teams if needed
        logger.info("🏟️ Migrating MLB teams...")
        source_cursor.execute("SELECT COUNT(*) FROM mlb_teams;")
        teams_count = source_cursor.fetchone()[0]
        
        if teams_count > 0:
            source_cursor.execute("SELECT * FROM mlb_teams;")
            teams_data = source_cursor.fetchall()
            
            dest_cursor.execute("DELETE FROM mlb_teams;")  # Clear existing
            
            source_cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'mlb_teams' 
                ORDER BY ordinal_position;
            """)
            team_columns = [row[0] for row in source_cursor.fetchall()]
            
            placeholders = ','.join(['%s'] * len(team_columns))
            insert_query = f"INSERT INTO mlb_teams ({','.join(team_columns)}) VALUES ({placeholders})"
            execute_values(dest_cursor, insert_query, teams_data)
            
            logger.info(f"✅ Migrated {teams_count:,} MLB teams")
        
        # Verify migration
        dest_cursor.execute("SELECT COUNT(*) FROM statcast;")
        final_statcast = dest_cursor.fetchone()[0]
        
        dest_cursor.execute("SELECT COUNT(*) FROM players;")
        final_players = dest_cursor.fetchone()[0]
        
        dest_cursor.execute("SELECT COUNT(*) FROM mlb_teams;")
        final_teams = dest_cursor.fetchone()[0]
        
        dest_cursor.execute("SELECT COUNT(*) FROM fangraphs_batting WHERE \"Season\" = 2025;")
        final_fangraphs = dest_cursor.fetchone()[0]
        
        logger.info(f"""
🎉 Migration Complete!
   📊 Statcast data: {final_statcast:,} records
   👥 Players: {final_players:,} records  
   🏟️ MLB Teams: {final_teams:,} records
   ⚾ FanGraphs Batting: {final_fangraphs:,} records
        """)
        
        dest_conn.commit()
        logger.info("💾 Changes committed to sports_data database")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        if 'dest_conn' in locals():
            dest_conn.rollback()
        raise
    finally:
        if 'source_conn' in locals():
            source_conn.close()
        if 'dest_conn' in locals():
            dest_conn.close()

if __name__ == "__main__":
    migrate_statcast_data()