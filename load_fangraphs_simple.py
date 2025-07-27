#!/usr/bin/env python3
"""
Load FanGraphs Data to Existing Table
====================================

Loads the collected FanGraphs batting data into the existing fangraphs_batting table.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_fangraphs_data():
    """Load FanGraphs data to existing table"""
    
    try:
        # Load the CSV data
        logger.info("📂 Loading FanGraphs batting data from CSV...")
        df = pd.read_csv('/home/jeffreyconboy/StatEdge/fangraphs_batting_2025.csv')
        logger.info(f"✅ Loaded {len(df)} records from CSV")
        
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
        
        # Convert DataFrame to list of tuples for insertion
        logger.info("🔄 Preparing data for insertion...")
        
        # Get column names from dataframe (they should match the database)
        columns = list(df.columns)
        
        # Create the INSERT query with proper column quoting
        quoted_columns = [f'"{col}"' for col in columns]
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f'INSERT INTO fangraphs_batting ({",".join(quoted_columns)}) VALUES ({placeholders})'
        
        # Convert DataFrame to list of tuples
        data_tuples = [tuple(row) for row in df.values]
        
        # Insert all data
        logger.info(f"💾 Inserting {len(data_tuples)} records...")
        cursor.executemany(insert_query, data_tuples)
        
        # Verify insertion
        cursor.execute('SELECT COUNT(*) FROM fangraphs_batting WHERE "Season" = 2025;')
        count = cursor.fetchone()[0]
        logger.info(f"✅ Successfully inserted {count} FanGraphs batting records")
        
        # Show sample data
        cursor.execute('''
            SELECT "Name", "Team", "AVG", "OBP", "SLG", "wOBA", "wRC+", "WAR" 
            FROM fangraphs_batting 
            WHERE "Season" = 2025 
            ORDER BY "WAR" DESC NULLS LAST 
            LIMIT 10;
        ''')
        top_players = cursor.fetchall()
        
        logger.info("\n🏆 Top 10 players by WAR:")
        for player in top_players:
            name, team, avg, obp, slg, woba, wrc_plus, war = player
            logger.info(f"   {name} ({team}): {avg:.3f} AVG, {obp:.3f} OBP, {slg:.3f} SLG, {woba:.3f} wOBA, {wrc_plus} wRC+, {war} WAR")
        
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