#!/usr/bin/env python3
"""
Smart MLB ID Fixer - Uses MLB's official search API
Much faster and more reliable than brute-force ID testing
"""

import asyncio
import aiohttp
import aiofiles
import psycopg2
from pathlib import Path
import re
import json

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'user': 'statedge_user',
    'password': 'statedge_pass',
    'database': 'statedge'
}

# Storage directory
STORAGE_DIR = Path(__file__).parent / "static" / "mlb-photos"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def get_players_with_invalid_ids():
    """Get all players with invalid MLB IDs (negative or None)"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, mlb_id, current_team
            FROM players 
            WHERE active = true 
            AND (mlb_id IS NULL OR mlb_id < 0)
            ORDER BY name
        """)
        
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"📊 Found {len(players)} players with invalid MLB IDs")
        return players
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return []

async def search_mlb_player_api(session, name: str) -> dict:
    """Use MLB's official Stats API to search for player"""
    try:
        # Clean the name for the API search
        search_name = name.strip()
        
        # MLB Stats API search endpoint
        api_url = f"https://statsapi.mlb.com/api/v1/people/search?names={search_name}"
        
        print(f"  🔍 API Search: {api_url}")
        
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                
                if 'people' in data and len(data['people']) > 0:
                    # Take the first match
                    player = data['people'][0]
                    player_id = player.get('id')
                    full_name = player.get('fullName', '')
                    active = player.get('active', False)
                    
                    print(f"  ✅ FOUND via API: {full_name} (ID: {player_id}, Active: {active})")
                    
                    return {
                        'id': player_id,
                        'name': full_name,
                        'active': active,
                        'found': True
                    }
                else:
                    print(f"  ❌ No API results for: {name}")
                    return {'found': False}
            else:
                print(f"  ❌ API Error {response.status} for: {name}")
                return {'found': False}
                
    except Exception as e:
        print(f"  ❌ API Exception for {name}: {str(e)}")
        return {'found': False}

async def search_mlb_player_web(session, name: str) -> dict:
    """Fallback: Use MLB.com web search if API fails"""
    try:
        # Web search as backup
        search_url = f"https://www.mlb.com/search?q={name.replace(' ', '+')}"
        
        print(f"  🌐 Web Search: {search_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with session.get(search_url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                
                # Look for player ID patterns in the HTML
                # MLB often embeds player data in JSON within the page
                id_patterns = [
                    r'"id":(\d{6})',  # 6-digit player IDs
                    r'player/[^/]+-(\d{6})',  # URLs with player IDs
                    r'"playerId":"(\d{6})"'  # JSON player IDs
                ]
                
                for pattern in id_patterns:
                    matches = re.findall(pattern, html)
                    if matches:
                        player_id = int(matches[0])
                        print(f"  ✅ FOUND via Web: {name} (ID: {player_id})")
                        return {
                            'id': player_id,
                            'name': name,
                            'found': True
                        }
                
                print(f"  ❌ No web results for: {name}")
                return {'found': False}
            else:
                print(f"  ❌ Web Error {response.status} for: {name}")
                return {'found': False}
                
    except Exception as e:
        print(f"  ❌ Web Exception for {name}: {str(e)}")
        return {'found': False}

async def find_player_mlb_id(session, name: str) -> dict:
    """Find MLB ID using API first, then web search as backup"""
    print(f"🔍 Searching for: {name}")
    
    # Try API first
    result = await search_mlb_player_api(session, name)
    if result['found']:
        return result
    
    # Fallback to web search
    await asyncio.sleep(0.5)  # Brief delay between attempts
    result = await search_mlb_player_web(session, name)
    
    return result

async def download_player_headshot(session, name: str, mlb_id: int) -> str:
    """Download player headshot and return local path"""
    try:
        photo_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/w_360,q_auto:best/v1/people/{mlb_id}/headshot/67/current"
        
        # Create safe filename
        safe_name = name.lower()
        safe_name = re.sub(r'[^\\w\\s-]', '', safe_name)
        safe_name = safe_name.replace(' ', '-')
        filename = f"{safe_name}-{mlb_id}.jpg"
        local_path = STORAGE_DIR / filename
        
        print(f"  📸 Downloading: {photo_url}")
        
        async with session.get(photo_url) as response:
            if response.status == 200:
                async with aiofiles.open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                file_size = local_path.stat().st_size
                if file_size > 1000:  # Valid image
                    print(f"  ✅ Downloaded: {file_size:,} bytes")
                    return f"/static/mlb-photos/{filename}"
                else:
                    local_path.unlink()  # Remove small/invalid files
                    print(f"  ❌ File too small: {file_size} bytes")
                    
        return None
        
    except Exception as e:
        print(f"  ❌ Download error: {str(e)}")
        return None

def update_player_database(name: str, mlb_id: int, image_path: str):
    """Update database with correct MLB ID and image path"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE players 
            SET mlb_id = %s, 
                local_image_path = %s,
                updated_at = NOW()
            WHERE name ILIKE %s AND active = true
        """, (mlb_id, image_path, f"%{name}%"))
        
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        return affected > 0
        
    except Exception as e:
        print(f"  ❌ Database update error: {str(e)}")
        return False

async def smart_fix_mlb_ids():
    """Main function - Smart MLB ID fixing using official APIs"""
    print("🧠 SMART MLB ID FIXER")
    print("=" * 50)
    print("Using MLB's official search API + web search fallback")
    print()
    
    # Get players needing fixes
    players = get_players_with_invalid_ids()
    if not players:
        print("✅ No players need MLB ID fixes!")
        return
    
    print(f"🎯 Processing {len(players)} players...")
    print(f"📁 Storage: {STORAGE_DIR}")
    print()
    
    successful_fixes = 0
    failed_count = 0
    
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        for i, (name, current_mlb_id, team) in enumerate(players, 1):
            print(f"\\n🔄 [{i}/{len(players)}] Processing: {name}")
            print(f"   Current MLB ID: {current_mlb_id} | Team: {team}")
            
            # Step 1: Find real MLB ID using smart search
            search_result = await find_player_mlb_id(session, name)
            
            if search_result['found']:
                real_mlb_id = search_result['id']
                
                # Step 2: Download headshot
                image_path = await download_player_headshot(session, name, real_mlb_id)
                
                if image_path:
                    # Step 3: Update database
                    if update_player_database(name, real_mlb_id, image_path):
                        successful_fixes += 1
                        print(f"  🎉 {name}: COMPLETE! (ID: {real_mlb_id})")
                    else:
                        print(f"  ❌ {name}: Database update failed")
                        failed_count += 1
                else:
                    # Update database with ID even if photo fails
                    if update_player_database(name, real_mlb_id, None):
                        successful_fixes += 1
                        print(f"  ✅ {name}: ID FOUND (photo failed) (ID: {real_mlb_id})")
                    else:
                        failed_count += 1
            else:
                failed_count += 1
                print(f"  ❌ {name}: Could not find MLB ID")
            
            # Progress update every 10 players
            if i % 10 == 0:
                print(f"\\n📊 Progress: {i}/{len(players)} processed")
                print(f"   ✅ Fixed: {successful_fixes}")
                print(f"   ❌ Failed: {failed_count}")
                print(f"   📈 Success Rate: {(successful_fixes/i)*100:.1f}%")
            
            # Brief delay between players
            await asyncio.sleep(0.3)
    
    # Final summary
    print(f"\\n🎉 SMART MLB ID FIX COMPLETE!")
    print(f"=" * 50)
    print(f"📊 Final Results:")
    print(f"   Total Players: {len(players)}")
    print(f"   Successfully Fixed: {successful_fixes}")
    print(f"   Failed: {failed_count}")
    print(f"   Success Rate: {(successful_fixes/len(players))*100:.1f}%")
    
    return successful_fixes

if __name__ == "__main__":
    print("🚀 Starting smart MLB ID fix using official APIs...")
    result = asyncio.run(smart_fix_mlb_ids())
    print(f"\\n✅ Process complete! Fixed {result} players.")