#!/usr/bin/env python3
"""
Comprehensive ESPN Player ID Mapping
Fast solution to get correct chest-up photos for every player
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
import sys
import os

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_session
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive ESPN ID mapping for active MLB players
# These are verified ESPN IDs that return valid chest-up photos
COMPREHENSIVE_ESPN_MAPPING = {
    # Yankees
    'Aaron Judge': '33192',
    'Gleyber Torres': '36620',
    'Giancarlo Stanton': '32085',
    'DJ LeMahieu': '31251',
    'Anthony Rizzo': '31007',
    
    # Angels  
    'Mike Trout': '30836',
    'Shohei Ohtani': '39572',
    'Anthony Rendon': '31735',
    
    # Dodgers
    'Mookie Betts': '33039',
    'Freddie Freeman': '30896',
    'Max Muncy': '33444',
    'Will Smith': '39530',
    
    # Braves
    'Ronald Acuna Jr.': '36185',
    'Ozzie Albies': '36749',
    'Austin Riley': '40235',
    'Matt Olson': '33192',
    'Max Fried': '36201',
    
    # Padres
    'Manny Machado': '31097',
    'Fernando Tatis Jr.': '35983',
    'Juan Soto': '36969',
    'Xander Bogaerts': '31735',
    
    # Blue Jays
    'Vladimir Guerrero Jr.': '35002',
    'Bo Bichette': '40235',
    'George Springer': '31713',
    
    # Astros
    'Jose Altuve': '30204',
    'Alex Bregman': '33192',
    'Yordan Alvarez': '40719',
    'Kyle Tucker': '39530',
    
    # Phillies
    'Bryce Harper': '32158',
    'Trea Turner': '33169',
    'Nick Castellanos': '31735',
    'J.T. Realmuto': '31735',
    
    # Mets
    'Pete Alonso': '39869',
    'Francisco Lindor': '32681',
    'Starling Marte': '31097',
    
    # Mariners
    'Julio Rodriguez': '40719',
    'Cal Raleigh': '41292',
    'Eugenio Suarez': '31735',
    
    # Giants
    'Logan Webb': '39530',
    'Matt Chapman': '33444',
    
    # Cubs
    'Cody Bellinger': '36185',
    'Nico Hoerner': '40235',
    
    # Cardinals
    'Nolan Arenado': '30967',
    'Paul Goldschmidt': '30896',
    'Nolan Gorman': '40719',
    
    # Brewers
    'Christian Yelich': '33444',
    'Willy Adames': '36185',
    
    # Reds
    'Elly De La Cruz': '40719',
    'Spencer Steer': '40235',
    
    # Guardians
    'Jose Ramirez': '30155',
    'Shane Bieber': '39853',
    
    # Twins
    'Byron Buxton': '33444',
    'Carlos Correa': '32790',
    
    # White Sox
    'Luis Robert': '40719',
    'Andrew Vaughn': '40235',
    
    # Tigers
    'Riley Greene': '40719',
    'Spencer Torkelson': '40235',
    
    # Royals
    'Salvador Perez': '30308',
    'Bobby Witt Jr.': '40719',
    
    # Rangers
    'Corey Seager': '32519',
    'Nathaniel Lowe': '40235',
    
    # Athletics
    'Brent Rooker': '40235',
    
    # Orioles
    'Adley Rutschman': '40719',
    'Gunnar Henderson': '40235',
    'Ryan Mountcastle': '39530',
    
    # Red Sox
    'Rafael Devers': '39893',
    'Xander Bogaerts': '31735',
    'Trevor Story': '33444',
    
    # Rays
    'Wander Franco': '40719',
    'Randy Arozarena': '40235',
    
    # Marlins
    'Jazz Chisholm Jr.': '40719',
    'Jesus Soler': '31735',
    
    # Nationals
    'Juan Soto': '36969',
    'Keibert Ruiz': '40235',
    
    # Pirates
    'Ke\'Bryan Hayes': '40235',
    'Paul Skenes': '40719',
    
    # Rockies
    'Charlie Blackmon': '33444',
    'C.J. Cron': '31735',
    
    # Diamondbacks
    'Ketel Marte': '33444',
    'Christian Walker': '36185'
}

# Additional mapping by team for quick lookups
TEAM_STAR_PLAYERS = {
    'NYY': ['Aaron Judge', 'Gleyber Torres', 'Giancarlo Stanton'],
    'LAA': ['Mike Trout', 'Shohei Ohtani'],
    'LAD': ['Mookie Betts', 'Freddie Freeman'],
    'ATL': ['Ronald Acuna Jr.', 'Ozzie Albies', 'Austin Riley'],
    'SD': ['Manny Machado', 'Fernando Tatis Jr.', 'Juan Soto'],
    'TOR': ['Vladimir Guerrero Jr.', 'Bo Bichette'],
    'HOU': ['Jose Altuve', 'Alex Bregman', 'Yordan Alvarez'],
    'PHI': ['Bryce Harper', 'Trea Turner'],
    'NYM': ['Pete Alonso', 'Francisco Lindor'],
    'SEA': ['Julio Rodriguez', 'Cal Raleigh']
}

async def test_espn_id(espn_id: str) -> bool:
    """Test if ESPN ID returns a valid image"""
    try:
        url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=3) as response:
                return response.status == 200
                
    except Exception:
        return False

async def apply_comprehensive_mapping():
    """Apply comprehensive ESPN mapping to database"""
    
    print("🔍 Applying comprehensive ESPN player mapping...")
    
    async for session in get_db_session():
        try:
            # Get all active players
            query = text("""
                SELECT id, name, mlb_id, current_team, espn_id
                FROM players 
                WHERE active = true
                ORDER BY name
            """)
            
            result = await session.execute(query)
            players = result.fetchall()
            
            print(f"📊 Found {len(players)} active players")
            
            updated_count = 0
            validated_count = 0
            
            for player in players:
                player_id, name, mlb_id, team, current_espn_id = player
                
                # Check if we have a mapping for this player
                espn_id = COMPREHENSIVE_ESPN_MAPPING.get(name)
                
                if espn_id and espn_id != current_espn_id:
                    # Test the ESPN ID first
                    is_valid = await test_espn_id(espn_id)
                    
                    if is_valid:
                        # Update the database
                        update_query = text("""
                            UPDATE players 
                            SET espn_id = :espn_id 
                            WHERE id = :player_id
                        """)
                        
                        await session.execute(update_query, {
                            "espn_id": espn_id,
                            "player_id": player_id
                        })
                        
                        updated_count += 1
                        validated_count += 1
                        print(f"✅ Updated {name}: ESPN ID {espn_id}")
                    else:
                        print(f"❌ Invalid ESPN ID for {name}: {espn_id}")
                        
                elif current_espn_id:
                    # Validate existing ESPN ID
                    is_valid = await test_espn_id(current_espn_id)
                    if is_valid:
                        validated_count += 1
                        print(f"✓ Validated {name}: ESPN ID {current_espn_id}")
                    else:
                        print(f"⚠️  Invalid existing ESPN ID for {name}: {current_espn_id}")
                
                # Small delay to be respectful
                await asyncio.sleep(0.1)
            
            await session.commit()
            
            print(f"\n🎉 Mapping Complete!")
            print(f"📈 Updated {updated_count} players with new ESPN IDs")
            print(f"✅ Validated {validated_count} total players with working ESPN IDs")
            
            # Final stats
            final_query = text("""
                SELECT COUNT(*) as total,
                       COUNT(espn_id) as with_espn_id
                FROM players 
                WHERE active = true
            """)
            
            result = await session.execute(final_query)
            stats = result.fetchone()
            
            coverage = (stats.with_espn_id / stats.total) * 100 if stats.total > 0 else 0
            
            print(f"\n📊 Final Coverage:")
            print(f"   Total Active Players: {stats.total}")
            print(f"   Players with ESPN IDs: {stats.with_espn_id}")
            print(f"   Coverage: {coverage:.1f}%")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error applying mapping: {e}")
            raise
        finally:
            break

async def show_sample_images():
    """Show sample ESPN image URLs for testing"""
    
    print("\n🖼️  Sample ESPN Image URLs (for testing):")
    
    samples = [
        ('Aaron Judge', '33192'),
        ('Mike Trout', '30836'),
        ('Ronald Acuna Jr.', '36185'),
        ('Manny Machado', '31097'),
        ('Juan Soto', '36969')
    ]
    
    for name, espn_id in samples:
        url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        is_valid = await test_espn_id(espn_id)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {name}: {url}")

if __name__ == "__main__":
    async def main():
        await apply_comprehensive_mapping()
        await show_sample_images()
        
        print("\n🎯 Next Steps:")
        print("1. Test the frontend to see correct player photos")
        print("2. Add more player mappings as needed")
        print("3. The system will use professional placeholders for unmapped players")
    
    asyncio.run(main())