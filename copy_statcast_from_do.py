#!/usr/bin/env python3
"""
Copy Statcast Data from Digital Ocean to Local Database
======================================================

Copies the 472K+ Statcast records from Digital Ocean database to local sports_data database.
"""

import psycopg2
import logging
from psycopg2.extras import execute_values
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def copy_statcast_data():
    """Copy Statcast data from Digital Ocean to local sports_data database"""
    
    try:
        # Connect to Digital Ocean database (source)
        logger.info("🔌 Connecting to Digital Ocean database...")
        
        # Use MCP postgres connection (which connects to DO database)
        # We'll need to use environment variables or direct connection
        do_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'db-postgresql-nyc1-44982-do-user-18396360-0.c.db.ondigitalocean.com'),
            port=os.getenv('POSTGRES_PORT', 25060),
            database=os.getenv('POSTGRES_DB', 'mlb_data'),
            user=os.getenv('POSTGRES_USER', 'mlb_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'mlb_secure_pass_2024'),
            sslmode='require'
        )
        do_cursor = do_conn.cursor()
        
        # Connect to local sports_data database (destination)
        logger.info("🔌 Connecting to local sports_data database...")
        local_conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='sports_data',
            user='sports_user',
            password='sports_secure_2025'
        )
        local_cursor = local_conn.cursor()
        
        # Check if statcast table exists in local database
        local_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'statcast'
            );
        """)
        table_exists = local_cursor.fetchone()[0]
        
        if not table_exists:
            logger.info("🏗️ Creating statcast table in local database...")
            
            # Get table schema from Digital Ocean database
            do_cursor.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'statcast' 
                ORDER BY ordinal_position;
            """)
            columns = do_cursor.fetchall()
            
            # Build CREATE TABLE statement
            column_defs = []
            for col_name, data_type, char_length, nullable, default in columns:
                col_def = f'"{col_name}" {data_type}'
                if char_length:
                    col_def += f'({char_length})'
                if nullable == 'NO':
                    col_def += ' NOT NULL'
                if default:
                    col_def += f' DEFAULT {default}'
                column_defs.append(col_def)
            
            create_table_sql = f"CREATE TABLE statcast ({', '.join(column_defs)});"
            local_cursor.execute(create_table_sql)
            logger.info("✅ Created statcast table")
        
        # Get total count from Digital Ocean
        do_cursor.execute("SELECT COUNT(*) FROM statcast;")
        total_count = do_cursor.fetchone()[0]
        logger.info(f"📊 Found {total_count:,} Statcast records to copy")
        
        # Clear existing data in local database
        local_cursor.execute("TRUNCATE TABLE statcast;")
        logger.info("🗑️ Cleared existing statcast data in local database")
        
        # Copy data in batches
        batch_size = 10000
        offset = 0
        total_copied = 0
        
        # Get column names for INSERT
        do_cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'statcast' 
            ORDER BY ordinal_position;
        """)
        column_names = [row[0] for row in do_cursor.fetchall()]
        
        while offset < total_count:
            logger.info(f"📦 Copying batch {offset + 1:,} to {min(offset + batch_size, total_count):,}")
            
            # Get batch from Digital Ocean
            do_cursor.execute(f"""
                SELECT * FROM statcast 
                ORDER BY game_date, game_pk 
                LIMIT {batch_size} OFFSET {offset};
            """)
            batch_data = do_cursor.fetchall()
            
            if not batch_data:
                break
            
            # Insert batch into local database
            quoted_columns = [f'"{col}"' for col in column_names]
            placeholders = ','.join(['%s'] * len(column_names))
            insert_query = f"INSERT INTO statcast ({','.join(quoted_columns)}) VALUES ({placeholders})"
            
            execute_values(local_cursor, insert_query, batch_data, page_size=1000)
            
            total_copied += len(batch_data)
            offset += batch_size
            
            logger.info(f"   ✅ Copied {total_copied:,} / {total_count:,} records")
            
            # Commit periodically
            if total_copied % 50000 == 0:
                local_conn.commit()
                logger.info("💾 Committed batch to database")
        
        # Final verification
        local_cursor.execute("SELECT COUNT(*) FROM statcast;")
        final_count = local_cursor.fetchone()[0]
        
        # Check FanGraphs data too
        local_cursor.execute('SELECT COUNT(*) FROM fangraphs_batting WHERE "Season" = 2025;')
        fg_count = local_cursor.fetchone()[0]
        
        logger.info(f"""
🎉 Data Copy Complete!
   📊 Statcast: {final_count:,} records
   ⚾ FanGraphs: {fg_count:,} records
        """)
        
        # Show sample of recent data
        local_cursor.execute("""
            SELECT game_date, player_name, events, launch_speed, launch_angle, hit_distance_sc
            FROM statcast 
            WHERE events IS NOT NULL 
            ORDER BY game_date DESC 
            LIMIT 5;
        """)
        recent_data = local_cursor.fetchall()
        
        logger.info("\n🔥 Recent Statcast data:")
        for row in recent_data:
            date, name, event, speed, angle, distance = row
            speed_str = f"{speed} mph" if speed else "N/A"
            angle_str = f"{angle}°" if angle else "N/A"
            dist_str = f"{distance} ft" if distance else "N/A"
            logger.info(f"   {date} - {name}: {event} ({speed_str}, {angle_str}, {dist_str})")
        
        local_conn.commit()
        logger.info("💾 All changes committed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Data copy failed: {e}")
        if 'local_conn' in locals():
            local_conn.rollback()
        raise
    finally:
        if 'do_conn' in locals():
            do_conn.close()
        if 'local_conn' in locals():
            local_conn.close()

if __name__ == "__main__":
    copy_statcast_data()