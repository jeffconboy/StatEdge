#!/usr/bin/env python3
"""
Find the real MLB ID for Jose Alvarado by searching MLB.com
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def search_mlb_player(session, player_name):
    """Search MLB.com for a player to find their real ID"""
    try:
        # Try common URL patterns first
        search_patterns = [
            f"https://www.mlb.com/player/jose-alvarado-",  # We need to find the real ID
            f"https://www.mlb.com/search?q={player_name.replace(' ', '+')}"
        ]
        
        # Let's try a Google search approach to find the MLB page
        google_search = f"site:mlb.com/player jose alvarado"
        print(f"🔍 Need to search for: {google_search}")
        
        # Try some common MLB ID ranges for Jose Alvarado
        # Recent players often have IDs in 600000+ range
        test_ids = [
            621237,  # Common range for recent players
            672724,  # Another common range
            650671,  # Another range
            665489,  # Around Vladimir Guerrero Jr's ID
            660271,  # Around Ohtani's ID
        ]
        
        for test_id in test_ids:
            test_url = f"https://www.mlb.com/player/jose-alvarado-{test_id}"
            print(f"🧪 Testing: {test_url}")
            
            try:
                async with session.get(test_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        if "jose alvarado" in html.lower() or "alvarado" in html.lower():
                            print(f"✅ FOUND! Jose Alvarado's MLB ID: {test_id}")
                            print(f"📸 Photo URL: https://img.mlbstatic.com/mlb-photos/image/upload/w_360/v1/people/{test_id}/headshot/67/current")
                            return test_id
                    else:
                        print(f"❌ {test_id}: HTTP {response.status}")
            except Exception as e:
                print(f"❌ {test_id}: {str(e)}")
                
            await asyncio.sleep(1)  # Be nice to MLB.com
        
        print("❌ Could not find Jose Alvarado's real MLB ID in test ranges")
        return None
        
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return None

async def find_jose_alvarado():
    """Find Jose Alvarado's real MLB information"""
    print("🔍 FINDING JOSE ALVARADO'S REAL MLB ID")
    print("=" * 50)
    
    timeout = aiohttp.ClientTimeout(total=15)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        real_id = await search_mlb_player(session, "Jose Alvarado")
        
        if real_id:
            print(f"\n🎉 SUCCESS!")
            print(f"Real MLB ID: {real_id}")
            print(f"Real MLB URL: https://www.mlb.com/player/jose-alvarado-{real_id}")
            print(f"Headshot URL: https://img.mlbstatic.com/mlb-photos/image/upload/w_360/v1/people/{real_id}/headshot/67/current")
        else:
            print(f"\n❌ Could not find Jose Alvarado's real MLB ID")
            print("💡 Try searching manually: https://www.mlb.com/search?q=jose+alvarado")

if __name__ == "__main__":
    asyncio.run(find_jose_alvarado())