#!/usr/bin/env python3
"""
Quick script to map all players to ESPN IDs systematically
This will give us correct chest-up photos for every player
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_session
from services.player_id_mapper import run_systematic_mapping
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Map all players systematically"""
    
    print("🔍 Starting systematic player image mapping...")
    print("This will find ESPN IDs for all players in the database")
    
    async for session in get_db_session():
        try:
            # First, let's see how many players we have
            count_query = text("SELECT COUNT(*) FROM players WHERE mlb_id IS NOT NULL AND active = true")
            result = await session.execute(count_query)
            total_players = result.scalar()
            
            print(f"📊 Found {total_players} active players with MLB IDs")
            
            # Check how many already have ESPN IDs
            mapped_query = text("SELECT COUNT(*) FROM players WHERE espn_id IS NOT NULL")
            result = await session.execute(mapped_query)
            already_mapped = result.scalar()
            
            print(f"✅ {already_mapped} players already have ESPN IDs")
            print(f"🎯 Need to map {total_players - already_mapped} players")
            
            # Run the systematic mapping
            mappings = await run_systematic_mapping(session)
            
            print(f"\n🎉 Mapping Complete!")
            print(f"📈 Successfully mapped {len(mappings)} new players")
            
            # Show some examples
            if mappings:
                print("\n📸 Examples of mapped players:")
                count = 0
                for mlb_id, espn_id in list(mappings.items())[:5]:
                    # Get player name
                    name_query = text("SELECT name FROM players WHERE mlb_id = :mlb_id")
                    result = await session.execute(name_query, {"mlb_id": mlb_id})
                    name = result.scalar()
                    
                    espn_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
                    print(f"   {name}: {espn_url}")
                    count += 1
                    if count >= 5:
                        break
            
            # Final check
            final_mapped_query = text("SELECT COUNT(*) FROM players WHERE espn_id IS NOT NULL")
            result = await session.execute(final_mapped_query)
            final_mapped = result.scalar()
            
            coverage_percent = (final_mapped / total_players) * 100 if total_players > 0 else 0
            
            print(f"\n📊 Final Stats:")
            print(f"   Total Active Players: {total_players}")
            print(f"   Players with ESPN IDs: {final_mapped}")
            print(f"   Coverage: {coverage_percent:.1f}%")
            
            if coverage_percent >= 80:
                print("🎯 Excellent coverage! Most players should have correct photos.")
            elif coverage_percent >= 60:
                print("👍 Good coverage! Major players should have correct photos.")
            else:
                print("⚠️  Limited coverage. May need manual mapping for some players.")
                
        except Exception as e:
            logger.error(f"Error during mapping: {e}")
            print(f"❌ Error: {e}")
        finally:
            break

if __name__ == "__main__":
    asyncio.run(main())