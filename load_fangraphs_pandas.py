#!/usr/bin/env python3
"""
Load FanGraphs Data with Pandas
===============================

Uses pandas to_sql for cleaner insertion.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_fangraphs_with_pandas():
    """Load FanGraphs data using pandas to_sql"""
    
    try:
        # Load the CSV data
        logger.info("📂 Loading FanGraphs batting data from CSV...")
        df = pd.read_csv('/home/jeffreyconboy/StatEdge/fangraphs_batting_2025.csv')
        logger.info(f"✅ Loaded {len(df)} records from CSV")
        
        # Create database connection string
        connection_string = 'postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data'
        engine = create_engine(connection_string)
        
        # Clear existing 2025 data
        logger.info("🗑️ Clearing existing 2025 data...")
        with engine.connect() as conn:
            result = conn.execute(text('DELETE FROM fangraphs_batting WHERE "Season" = 2025'))
            logger.info(f"Cleared {result.rowcount} existing records")
            conn.commit()
        
        # Insert new data
        logger.info("💾 Inserting new data...")
        df.to_sql('fangraphs_batting', engine, if_exists='append', index=False, method='multi')
        
        # Verify insertion
        with engine.connect() as conn:
            result = conn.execute(text('SELECT COUNT(*) FROM fangraphs_batting WHERE "Season" = 2025'))
            count = result.fetchone()[0]
            logger.info(f"✅ Successfully inserted {count} FanGraphs batting records")
            
            # Show top players
            result = conn.execute(text('''
                SELECT "Name", "Team", "AVG", "OBP", "SLG", "wOBA", "wRC+", "WAR" 
                FROM fangraphs_batting 
                WHERE "Season" = 2025 AND "WAR" IS NOT NULL
                ORDER BY "WAR" DESC 
                LIMIT 10
            '''))
            top_players = result.fetchall()
            
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
        
        logger.info("🎉 FanGraphs batting data successfully loaded!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        raise

if __name__ == "__main__":
    load_fangraphs_with_pandas()