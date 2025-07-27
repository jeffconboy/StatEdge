#!/usr/bin/env python3
"""
Collect FanGraphs Batting Data with PyBaseball
==============================================

Uses pybaseball to collect current FanGraphs batting statistics for 2025.
"""

import logging
import pybaseball as pyb
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_fangraphs_batting_data():
    """Collect current FanGraphs batting data for 2025"""
    
    try:
        logger.info("🔍 Collecting FanGraphs batting data for 2025...")
        
        # Get current season batting stats from FanGraphs
        # Using qual=1 to get all qualified players (minimum PA threshold)
        batting_data = pyb.batting_stats(2025, qual=1)
        
        if batting_data is None or batting_data.empty:
            logger.warning("❌ No batting data returned from FanGraphs")
            return
        
        logger.info(f"✅ Successfully retrieved {len(batting_data)} batting records")
        logger.info(f"📋 Columns available: {list(batting_data.columns)}")
        
        # Display first few rows for verification
        logger.info("\n🔍 Sample data:")
        print(batting_data.head())
        
        # Save to CSV for inspection
        output_file = "fangraphs_batting_2025.csv"
        batting_data.to_csv(output_file, index=False)
        logger.info(f"💾 Saved data to {output_file}")
        
        # Display key statistics
        logger.info(f"\n📊 Data Summary:")
        logger.info(f"   - Total players: {len(batting_data)}")
        logger.info(f"   - Unique teams: {batting_data['Team'].nunique() if 'Team' in batting_data.columns else 'N/A'}")
        logger.info(f"   - Top BA: {batting_data['AVG'].max() if 'AVG' in batting_data.columns else 'N/A'}")
        logger.info(f"   - Top wOBA: {batting_data['wOBA'].max() if 'wOBA' in batting_data.columns else 'N/A'}")
        logger.info(f"   - Top wRC+: {batting_data['wRC+'].max() if 'wRC+' in batting_data.columns else 'N/A'}")
        
        return batting_data
        
    except Exception as e:
        logger.error(f"❌ Failed to collect FanGraphs batting data: {e}")
        return None

if __name__ == "__main__":
    collect_fangraphs_batting_data()