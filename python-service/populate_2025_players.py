#!/usr/bin/env python3
"""
Script to specifically populate current star players (Aaron Judge, etc.) with real 2025 season data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from services.data_collector import DataCollector
from database.connection import get_db_session
from sqlalchemy import text
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of current MLB stars to ensure we have data for
TARGET_PLAYERS = [
    {'name': 'Aaron Judge', 'mlb_id': 592450, 'team': 'NYY'},
    {'name': 'Mookie Betts', 'mlb_id': 605141, 'team': 'LAD'},
    {'name': 'Ronald Acuna Jr.', 'mlb_id': 660670, 'team': 'ATL'},
    {'name': 'Juan Soto', 'mlb_id': 665742, 'team': 'NYY'},
    {'name': 'Shohei Ohtani', 'mlb_id': 660271, 'team': 'LAD'},
    {'name': 'Fernando Tatis Jr.', 'mlb_id': 665487, 'team': 'SD'},
    {'name': 'Vladimir Guerrero Jr.', 'mlb_id': 665489, 'team': 'TOR'},
    {'name': 'Mike Trout', 'mlb_id': 545361, 'team': 'LAA'},
    {'name': 'Francisco Lindor', 'mlb_id': 596019, 'team': 'NYM'},
    {'name': 'Freddie Freeman', 'mlb_id': 518692, 'team': 'LAD'}
]

async def ensure_players_exist():
    """Ensure target players exist in the database"""
    async for session in get_db_session():
        try:
            for player_info in TARGET_PLAYERS:
                # Check if player exists
                check_query = text("""
                    SELECT id FROM players WHERE mlb_id = :mlb_id
                """)
                result = await session.execute(check_query, {'mlb_id': player_info['mlb_id']})
                existing = result.fetchone()
                
                if not existing:
                    # Insert player
                    insert_query = text("""
                        INSERT INTO players (
                            mlb_id, name, current_team, active,
                            first_name, last_name, primary_position
                        ) VALUES (
                            :mlb_id, :name, :current_team, true,
                            :first_name, :last_name, :position
                        ) RETURNING id
                    """)
                    
                    # Split name for first/last
                    name_parts = player_info['name'].split(' ', 1)
                    first_name = name_parts[0] if len(name_parts) > 0 else ''
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    await session.execute(insert_query, {
                        'mlb_id': player_info['mlb_id'],
                        'name': player_info['name'],
                        'current_team': player_info['team'],
                        'first_name': first_name,
                        'last_name': last_name,
                        'position': 'OF'  # Default position
                    })
                    
                    logger.info(f"✅ Added player: {player_info['name']}")
                else:
                    logger.info(f"✓ Player exists: {player_info['name']}")
            
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error ensuring players exist: {str(e)}")
            raise
        finally:
            break

async def collect_recent_data():
    """Collect recent data that should include our target players"""
    collector = DataCollector()
    await collector.init_redis()
    
    # Collect data for the last 7 days to increase chances of getting player data
    for days_back in range(1, 8):
        target_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        logger.info(f"Collecting data for {target_date}...")
        
        try:
            # Collect Statcast data (pitch-by-pitch includes our players as batters)
            await collector.collect_statcast_data(target_date)
            
            # Collect game/lineup data
            await collector.collect_mlb_lineups(target_date)
            
        except Exception as e:
            logger.warning(f"Failed to collect data for {target_date}: {str(e)}")
            continue
    
    # Collect 2025 season FanGraphs data
    logger.info("Collecting 2025 FanGraphs season data...")
    await collector.collect_fangraphs_data(2025)

async def verify_player_data():
    """Verify that our target players have 2025 data"""
    async for session in get_db_session():
        try:
            logger.info("\n📊 Verifying 2025 player data:")
            logger.info("=" * 60)
            
            for player_info in TARGET_PLAYERS:
                # Get player from database
                player_query = text("""
                    SELECT id, name FROM players WHERE mlb_id = :mlb_id
                """)
                result = await session.execute(player_query, {'mlb_id': player_info['mlb_id']})
                player = result.fetchone()
                
                if not player:
                    logger.warning(f"❌ Player not found: {player_info['name']}")
                    continue
                
                logger.info(f"\n🏟️ {player.name}:")
                
                # Check FanGraphs batting stats
                batting_query = text("""
                    SELECT season, games_played, plate_appearances, avg, obp, slg, ops, war_fg
                    FROM fangraphs_batting 
                    WHERE player_id = :player_id AND season = 2025
                """)
                batting_result = await session.execute(batting_query, {'player_id': player.id})
                batting_stats = batting_result.fetchone()
                
                if batting_stats:
                    logger.info(f"  📈 2025 Batting: {batting_stats.games_played}G, "
                              f"{batting_stats.plate_appearances}PA, "
                              f".{batting_stats.avg:.3f}/.{batting_stats.obp:.3f}/.{batting_stats.slg:.3f}, "
                              f"{batting_stats.ops:.3f} OPS, {batting_stats.war_fg} WAR")
                else:
                    logger.warning(f"  ⚠️ No 2025 batting stats found")
                
                # Check Statcast data (recent at-bats)
                statcast_query = text("""
                    SELECT COUNT(*) as pitch_count, 
                           COUNT(DISTINCT game_date) as game_days,
                           MAX(game_date) as latest_game
                    FROM statcast_pitches 
                    WHERE batter_id = :mlb_id 
                    AND game_date >= '2025-01-01'
                """)
                statcast_result = await session.execute(statcast_query, {'mlb_id': player_info['mlb_id']})
                statcast_stats = statcast_result.fetchone()
                
                if statcast_stats and statcast_stats.pitch_count > 0:
                    logger.info(f"  ⚾ 2025 Statcast: {statcast_stats.pitch_count} pitches across "
                              f"{statcast_stats.game_days} game days (latest: {statcast_stats.latest_game})")
                else:
                    logger.warning(f"  ⚠️ No 2025 Statcast data found")
            
        except Exception as e:
            logger.error(f"Error verifying player data: {str(e)}")
        finally:
            break

async def main():
    """Main execution function"""
    logger.info("🚀 Starting 2025 MLB player data population...")
    
    try:
        # Step 1: Ensure all target players exist in database
        logger.info("Step 1: Ensuring target players exist in database...")
        await ensure_players_exist()
        
        # Step 2: Collect recent data
        logger.info("\nStep 2: Collecting recent MLB data...")
        await collect_recent_data()
        
        # Step 3: Verify the data was populated
        logger.info("\nStep 3: Verifying player data...")
        await verify_player_data()
        
        logger.info("\n🎉 2025 MLB player data population completed!")
        
    except Exception as e:
        logger.error(f"💥 Population failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())