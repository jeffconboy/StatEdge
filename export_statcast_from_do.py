#!/usr/bin/env python3
"""
Export Statcast Data from Digital Ocean Database
===============================================

Uses MCP postgres connection to export statcast data to SQL file,
then imports it into local sports_data database.
"""

import psycopg2
import logging
import subprocess
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_and_import_statcast():
    """Export Statcast data from DO and import to local database"""
    
    try:
        # First, let's check what we have in the MCP postgres (Digital Ocean)
        logger.info("📊 Checking Digital Ocean database contents...")
        
        # Connect to local sports_data database to prepare it
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
            
            # Create a basic statcast table structure (we'll adjust as needed)
            create_table_sql = """
            CREATE TABLE statcast (
                pitch_type VARCHAR(10),
                game_date DATE,
                release_speed DECIMAL(5,2),
                release_pos_x DECIMAL(8,4),
                release_pos_z DECIMAL(8,4),
                player_name VARCHAR(100),
                batter INTEGER,
                pitcher INTEGER,
                events VARCHAR(50),
                description VARCHAR(200),
                spin_dir DECIMAL(8,4),
                spin_rate_deprecated DECIMAL(8,2),
                break_angle_deprecated DECIMAL(8,4),
                break_length_deprecated DECIMAL(8,4),
                zone INTEGER,
                des VARCHAR(500),
                game_type VARCHAR(5),
                stand VARCHAR(1),
                p_throws VARCHAR(1),
                home_team VARCHAR(10),
                away_team VARCHAR(10),
                type VARCHAR(1),
                hit_location INTEGER,
                bb_type VARCHAR(20),
                balls INTEGER,
                strikes INTEGER,
                game_year INTEGER,
                pfx_x DECIMAL(8,4),
                pfx_z DECIMAL(8,4),
                plate_x DECIMAL(8,4),
                plate_z DECIMAL(8,4),
                on_3b INTEGER,
                on_2b INTEGER,
                on_1b INTEGER,
                outs_when_up INTEGER,
                inning INTEGER,
                inning_topbot VARCHAR(10),
                hc_x DECIMAL(8,4),
                hc_y DECIMAL(8,4),
                tfs_deprecated DECIMAL(8,4),
                tfs_zulu_deprecated VARCHAR(30),
                fielder_2 INTEGER,
                umpire INTEGER,
                sv_id VARCHAR(50),
                vx0 DECIMAL(8,4),
                vy0 DECIMAL(8,4),
                vz0 DECIMAL(8,4),
                ax DECIMAL(8,4),
                ay DECIMAL(8,4),
                az DECIMAL(8,4),
                sz_top DECIMAL(8,4),
                sz_bot DECIMAL(8,4),
                hit_distance_sc INTEGER,
                launch_speed DECIMAL(8,4),
                launch_angle DECIMAL(8,4),
                effective_speed DECIMAL(8,4),
                release_spin_rate DECIMAL(8,2),
                release_extension DECIMAL(8,4),
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
                release_pos_y DECIMAL(8,4),
                estimated_ba_using_speedangle DECIMAL(8,6),
                estimated_woba_using_speedangle DECIMAL(8,6),
                woba_value DECIMAL(8,6),
                woba_denom INTEGER,
                babip_value INTEGER,
                iso_value DECIMAL(8,6),
                launch_speed_angle INTEGER,
                at_bat_number INTEGER,
                pitch_number INTEGER,
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
                spin_axis DECIMAL(8,2),
                delta_home_win_exp DECIMAL(10,8),
                delta_run_exp DECIMAL(8,6)
            );
            """
            local_cursor.execute(create_table_sql)
            local_conn.commit()
            logger.info("✅ Created statcast table structure")
        
        # Clear existing statcast data in local database
        local_cursor.execute("TRUNCATE TABLE statcast;")
        local_conn.commit()
        logger.info("🗑️ Cleared existing statcast data in local database")
        
        logger.info("📝 Creating CSV export script...")
        
        # Create a simple export script that we can run through MCP
        export_script = """
import pandas as pd
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This will be run in the MCP context - it should have access to the DO database
try:
    # The MCP postgres should handle the connection for us
    logger.info("Exporting statcast data to CSV...")
    
    # We'll create a simple query to export the data
    query = "SELECT * FROM statcast LIMIT 100000;"  # Start with first 100k records
    
    logger.info("Query prepared - this should be run via MCP postgres")
    
except Exception as e:
    logger.error(f"Export failed: {e}")
"""
        
        with open('/tmp/export_script.py', 'w') as f:
            f.write(export_script)
            
        logger.info("⚠️  Need to use MCP postgres connection to export data")
        logger.info("Let me query the Digital Ocean database through MCP to get the data...")
        
        local_conn.close()
        
        logger.info("✅ Local database prepared. Ready for data import from Digital Ocean.")
        logger.info("📋 Next: Use MCP postgres queries to get statcast data in batches")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        raise

if __name__ == "__main__":
    export_and_import_statcast()