#!/usr/bin/env python3
"""
Simple Migration to sports_data Database
========================================

Uses pg_dump and psql for reliable data migration.
"""

import subprocess
import logging
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data():
    """Migrate data using pg_dump and psql"""
    
    try:
        # First verify we can connect to both databases
        logger.info("🔌 Verifying database connections...")
        
        # Test source connection
        source_conn = psycopg2.connect(
            host='localhost', port=15432, database='statedge',
            user='statedge_user', password='statedge_pass'
        )
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT COUNT(*) FROM statcast;")
        statcast_count = source_cursor.fetchone()[0]
        source_conn.close()
        
        # Test destination connection  
        dest_conn = psycopg2.connect(
            host='localhost', port=5432, database='sports_data',
            user='sports_user', password='sports_secure_2025'
        )
        dest_cursor = dest_conn.cursor()
        dest_cursor.execute("SELECT COUNT(*) FROM fangraphs_batting WHERE \"Season\" = 2025;")
        fg_count = dest_cursor.fetchone()[0]
        dest_conn.close()
        
        logger.info(f"✅ Source (statedge): {statcast_count:,} Statcast records")
        logger.info(f"✅ Destination (sports_data): {fg_count:,} FanGraphs records")
        
        # Export specific tables from statedge database
        logger.info("📦 Exporting Statcast data...")
        
        # Export statcast table
        subprocess.run([
            'pg_dump',
            '-h', 'localhost', '-p', '15432',
            '-U', 'statedge_user', '-d', 'statedge',
            '--table', 'statcast',
            '--data-only', '--inserts',
            '-f', '/tmp/statcast_data.sql'
        ], env={'PGPASSWORD': 'statedge_pass'}, check=True)
        
        # Export players table
        subprocess.run([
            'pg_dump', 
            '-h', 'localhost', '-p', '15432',
            '-U', 'statedge_user', '-d', 'statedge',
            '--table', 'players',
            '--data-only', '--inserts',
            '-f', '/tmp/players_data.sql'
        ], env={'PGPASSWORD': 'statedge_pass'}, check=True)
        
        logger.info("📥 Importing data into sports_data...")
        
        # Clear existing data in sports_data
        dest_conn = psycopg2.connect(
            host='localhost', port=5432, database='sports_data',
            user='sports_user', password='sports_secure_2025'
        )
        dest_cursor = dest_conn.cursor()
        
        # Clear statcast table
        dest_cursor.execute("TRUNCATE TABLE statcast;")
        logger.info("🗑️ Cleared existing Statcast data")
        
        # Clear players table
        dest_cursor.execute("TRUNCATE TABLE players CASCADE;")
        logger.info("🗑️ Cleared existing players data")
        
        dest_conn.commit()
        dest_conn.close()
        
        # Import statcast data
        subprocess.run([
            'psql',
            '-h', 'localhost', '-p', '5432',
            '-U', 'sports_user', '-d', 'sports_data',
            '-f', '/tmp/statcast_data.sql'
        ], env={'PGPASSWORD': 'sports_secure_2025'}, check=True)
        
        # Import players data
        subprocess.run([
            'psql',
            '-h', 'localhost', '-p', '5432', 
            '-U', 'sports_user', '-d', 'sports_data',
            '-f', '/tmp/players_data.sql'
        ], env={'PGPASSWORD': 'sports_secure_2025'}, check=True)
        
        # Verify final counts
        dest_conn = psycopg2.connect(
            host='localhost', port=5432, database='sports_data',
            user='sports_user', password='sports_secure_2025'
        )
        dest_cursor = dest_conn.cursor()
        
        dest_cursor.execute("SELECT COUNT(*) FROM statcast;")
        final_statcast = dest_cursor.fetchone()[0]
        
        dest_cursor.execute("SELECT COUNT(*) FROM players;")
        final_players = dest_cursor.fetchone()[0]
        
        dest_cursor.execute("SELECT COUNT(*) FROM fangraphs_batting WHERE \"Season\" = 2025;")
        final_fg = dest_cursor.fetchone()[0]
        
        dest_conn.close()
        
        logger.info(f"""
🎉 Migration Complete!
   📊 Statcast: {final_statcast:,} records
   👥 Players: {final_players:,} records  
   ⚾ FanGraphs: {final_fg:,} records
        """)
        
        # Cleanup temp files
        subprocess.run(['rm', '-f', '/tmp/statcast_data.sql', '/tmp/players_data.sql'])
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_data()