#!/usr/bin/env python3
"""
Test MLB.com scraper with a few players first
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

def create_mlb_url(name: str, mlb_id: int) -> str:
    """Create MLB.com URL"""
    clean_name = name.lower()
    clean_name = re.sub(r'[^\w\s-]', '', clean_name)
    clean_name = clean_name.replace(' ', '-')
    clean_name = re.sub(r'-+', '-', clean_name)
    return f"https://www.mlb.com/player/{clean_name}-{mlb_id}"

async def test_scrape_player(session, name: str, mlb_id: int):
    """Test scraping one player"""
    try:
        mlb_url = create_mlb_url(name, mlb_id)
        print(f"🔍 Testing {name}: {mlb_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with session.get(mlb_url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for images
                images = soup.find_all('img')
                photo_urls = []
                
                for img in images:
                    src = img.get('src', '')
                    if src and ('headshot' in src or 'people' in src) and 'mlbstatic.com' in src:
                        photo_urls.append(src)
                
                print(f"  ✅ Found {len(photo_urls)} potential photos:")
                for i, url in enumerate(photo_urls[:3]):  # Show first 3
                    print(f"    {i+1}. {url}")
                
                return len(photo_urls) > 0
            else:
                print(f"  ❌ HTTP {response.status}")
                return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

async def test_mlb_scraper():
    """Test with a few known players"""
    test_players = [
        ("Ranger Suarez", 624133),
        ("Enyel De Los Santos", 660853),
        ("Mike Trout", 545361),
        ("Aaron Judge", 592450)
    ]
    
    print("🧪 TESTING MLB.COM SCRAPER")
    print("=" * 40)
    
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for name, mlb_id in test_players:
            success = await test_scrape_player(session, name, mlb_id)
            print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print()
            await asyncio.sleep(2)  # Be nice to MLB.com

if __name__ == "__main__":
    asyncio.run(test_mlb_scraper())