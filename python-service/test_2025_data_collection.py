#!/usr/bin/env python3
"""
Test script to verify 2025 MLB data collection and fix date formatting issues
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
from services.data_collector import DataCollector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_current_data_collection():
    """Test collecting current 2025 MLB data"""
    collector = DataCollector()
    await collector.init_redis()
    
    # Get yesterday's date (games are usually available the day after)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    logger.info(f"Testing data collection for {yesterday}")
    
    try:
        # Test Statcast data collection
        logger.info("Testing Statcast data collection...")
        await collector.collect_statcast_data(yesterday)
        
        # Test MLB lineups collection
        logger.info("Testing MLB lineups collection...")
        await collector.collect_mlb_lineups(yesterday)
        
        # Test FanGraphs data collection for 2025 season
        logger.info("Testing FanGraphs data collection for 2025...")
        await collector.collect_fangraphs_data(2025)
        
        logger.info("✅ All data collection tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Data collection test failed: {str(e)}")
        raise

async def test_date_conversion():
    """Test the date conversion utility function"""
    collector = DataCollector()
    
    test_dates = [
        '2025-07-24',
        '2025-07-24T19:30:00Z',
        datetime(2025, 7, 24),
        datetime.now().date(),
        None
    ]
    
    logger.info("Testing date conversion utility...")
    for test_date in test_dates:
        converted = collector._convert_to_date(test_date)
        logger.info(f"Input: {test_date} ({type(test_date)}) -> Output: {converted} ({type(converted)})")
    
    logger.info("✅ Date conversion tests completed!")

async def verify_aaron_judge_data():
    """Verify that Aaron Judge has 2025 statistics in the database"""
    from database.connection import get_db_session
    from sqlalchemy import text
    
    async for session in get_db_session():
        try:
            # Look for Aaron Judge in the players table
            query = text("""
                SELECT p.id, p.name, p.mlb_id, p.current_team 
                FROM players p 
                WHERE p.name ILIKE '%judge%' 
                LIMIT 5
            """)
            result = await session.execute(query)
            players = result.fetchall()
            
            if players:
                logger.info("Found Judge-related players:")
                for player in players:
                    logger.info(f"  - {player.name} (ID: {player.id}, MLB ID: {player.mlb_id}, Team: {player.current_team})")
                    
                    # Check for 2025 batting stats
                    stats_query = text("""
                        SELECT season, games_played, avg, ops, war_fg
                        FROM fangraphs_batting 
                        WHERE player_id = :player_id AND season = 2025
                        LIMIT 1
                    """)
                    stats_result = await session.execute(stats_query, {'player_id': player.id})
                    stats = stats_result.fetchone()
                    
                    if stats:
                        logger.info(f"    2025 stats: {stats.games_played}G, .{stats.avg:.3f} AVG, {stats.ops:.3f} OPS, {stats.war_fg} WAR")
                    else:
                        logger.info("    No 2025 statistics found")
            else:
                logger.warning("No Judge-related players found in database")
                
        except Exception as e:
            logger.error(f"Error verifying player data: {str(e)}")
        finally:
            break

async def main():
    """Main test function"""
    logger.info("🚀 Starting 2025 MLB data collection tests...")
    
    try:
        # Test 1: Date conversion utility
        await test_date_conversion()
        
        # Test 2: Current data collection
        await test_current_data_collection()
        
        # Test 3: Verify player data
        await verify_aaron_judge_data()
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Tests failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())