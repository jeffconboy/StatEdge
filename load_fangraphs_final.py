#!/usr/bin/env python3
"""
Load FanGraphs Data - Final Version
==================================

Loads the collected FanGraphs batting data with proper NaN handling.
"""

import pandas as pd
import psycopg2
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_fangraphs_data():
    """Load FanGraphs data with proper error handling"""
    
    try:
        # Load the CSV data
        logger.info("📂 Loading FanGraphs batting data from CSV...")
        df = pd.read_csv('/home/jeffreyconboy/StatEdge/fangraphs_batting_2025.csv')
        logger.info(f"✅ Loaded {len(df)} records from CSV")
        
        # Replace NaN values with None for proper SQL insertion
        df = df.where(pd.notnull(df), None)
        
        # Connect to database
        logger.info("🔌 Connecting to sports_data database...")
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='sports_data',
            user='sports_user',
            password='sports_secure_2025'
        )
        cursor = conn.cursor()
        
        # Clear existing 2025 data
        cursor.execute('DELETE FROM fangraphs_batting WHERE "Season" = 2025;')
        deleted_count = cursor.rowcount
        logger.info(f"🗑️ Cleared {deleted_count} existing 2025 records")
        
        # Insert data one row at a time to handle any issues
        logger.info("🔄 Inserting data row by row...")
        
        columns = list(df.columns)
        quoted_columns = [f'"{col}"' for col in columns]
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f'INSERT INTO fangraphs_batting ({",".join(quoted_columns)}) VALUES ({placeholders})'
        
        successful_inserts = 0
        failed_inserts = 0
        
        for index, row in df.iterrows():
            try:
                values = tuple(row.values)
                cursor.execute(insert_query, values)
                successful_inserts += 1
                
                if successful_inserts % 100 == 0:
                    logger.info(f"   Inserted {successful_inserts} records...")
                    
            except Exception as e:
                failed_inserts += 1
                logger.warning(f"Failed to insert row {index} ({row.get('Name', 'Unknown')}): {e}")
                continue
        
        # Verify insertion
        cursor.execute('SELECT COUNT(*) FROM fangraphs_batting WHERE "Season" = 2025;')
        count = cursor.fetchone()[0]
        
        logger.info(f"✅ Successfully inserted {successful_inserts} records")
        logger.info(f"❌ Failed to insert {failed_inserts} records")
        logger.info(f"📊 Total records in database: {count}")
        
        # Show sample data
        cursor.execute('''
            SELECT "Name", "Team", "AVG", "OBP", "SLG", "wOBA", "wRC+", "WAR" 
            FROM fangraphs_batting 
            WHERE "Season" = 2025 AND "WAR" IS NOT NULL
            ORDER BY "WAR" DESC 
            LIMIT 10;
        ''')
        top_players = cursor.fetchall()
        
        logger.info("\n🏆 Top 10 players by WAR:")
        for player in top_players:
            name, team, avg, obp, slg, woba, wrc_plus, war = player
            avg_str = f"{avg:.3f}" if avg is not None else "N/A"
            obp_str = f"{obp:.3f}" if obp is not None else "N/A"
            slg_str = f"{slg:.3f}" if slg is not None else "N/A"
            woba_str = f"{woba:.3f}" if woba is not None else "N/A"
            wrc_str = str(wrc_plus) if wrc_plus is not None else "N/A"
            war_str = str(war) if war is not None else "N/A"
            logger.info(f"   {name} ({team}): {avg_str} AVG, {obp_str} OBP, {slg_str} SLG, {woba_str} wOBA, {wrc_str} wRC+, {war_str} WAR")
        
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
    load_fangraphs_data()