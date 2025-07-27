#!/usr/bin/env python3
"""
Fix MLB IDs for all players with invalid data
Systematically find real MLB IDs and download headshots
"""

import asyncio
import aiohttp
import aiofiles
import psycopg2
from pathlib import Path
import re
from bs4 import BeautifulSoup
import time

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

# Targeted MLB ID ranges based on recent players (much smaller, more focused)
MLB_ID_RANGES = [
    # Focus on most likely ranges for current active players
    range(660000, 680000),  # Very recent players (2020-2024)
    range(640000, 660000),  # Recent players (2018-2020) 
    range(620000, 640000),  # 2016-2018 players
    range(600000, 620000),  # 2014-2016 players
    range(580000, 600000),  # 2012-2014 players
    range(540000, 580000),  # Veterans still active
]

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

def create_mlb_url(name: str, mlb_id: int) -> str:
    """Create MLB.com player URL from name and ID"""
    clean_name = name.lower()
    clean_name = re.sub(r'[^\\w\\s-]', '', clean_name)
    clean_name = clean_name.replace(' ', '-')
    clean_name = re.sub(r'-+', '-', clean_name)
    return f"https://www.mlb.com/player/{clean_name}-{mlb_id}"

async def test_mlb_id(session, name: str, test_id: int) -> bool:
    """Test if an MLB ID belongs to the given player"""
    try:
        test_url = create_mlb_url(name, test_id)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with session.get(test_url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                
                # Check if the player name appears in the page
                name_parts = name.lower().split()
                html_lower = html.lower()
                
                # Look for both first and last name in the HTML
                matches = sum(1 for part in name_parts if part in html_lower)
                
                # Consider it a match if most name parts are found
                if matches >= len(name_parts) - 1:  # Allow for minor variations
                    return True
                    
            return False
            
    except Exception as e:
        return False

async def find_real_mlb_id(session, name: str, current_team: str) -> int:
    """Find the real MLB ID for a player by testing focused ranges"""
    print(f"🔍 Searching for {name} ({current_team})...")
    
    tested_count = 0
    
    # Test focused ID ranges - much smaller sample
    for id_range in MLB_ID_RANGES:
        # Test every 500th ID first (quick scan)
        quick_scan = list(range(id_range.start, id_range.stop, 500))
        
        for test_id in quick_scan:
            tested_count += 1
            if await test_mlb_id(session, name, test_id):
                print(f"  ✅ FOUND! {name} = MLB ID {test_id} (tested {tested_count} IDs)")
                return test_id
            
            # Very short delay
            await asyncio.sleep(0.1)
            
            # Give up after testing 50 IDs to avoid getting stuck
            if tested_count >= 50:
                print(f"  ⏭️ Skipping {name} after testing {tested_count} IDs")
                return None
    
    print(f"  ❌ Could not find MLB ID for {name} (tested {tested_count} IDs)")
    return None

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
        
        async with session.get(photo_url) as response:
            if response.status == 200:
                async with aiofiles.open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                file_size = local_path.stat().st_size
                if file_size > 1000:  # Valid image
                    print(f"  📸 Downloaded headshot: {file_size:,} bytes")
                    return f"/static/mlb-photos/{filename}"
                else:
                    local_path.unlink()  # Remove small/invalid files
                    
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"  ❌ Database update error: {str(e)}")
        return False

async def fix_all_mlb_ids():
    """Main function to fix all MLB IDs"""
    print("🔧 FIXING ALL MLB IDs")
    print("=" * 50)
    
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
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        for i, (name, current_mlb_id, team) in enumerate(players, 1):
            print(f"\\n🔄 [{i}/{len(players)}] Processing {name} (Team: {team})")
            print(f"   Current MLB ID: {current_mlb_id}")
            
            # Step 1: Find real MLB ID
            real_mlb_id = await find_real_mlb_id(session, name, team)
            
            if real_mlb_id:
                # Step 2: Download headshot
                image_path = await download_player_headshot(session, name, real_mlb_id)
                
                if image_path:
                    # Step 3: Update database
                    if update_player_database(name, real_mlb_id, image_path):
                        successful_fixes += 1
                        print(f"  ✅ {name}: COMPLETE (ID: {real_mlb_id})")
                    else:
                        print(f"  ❌ {name}: Database update failed")
                        failed_count += 1
                else:
                    print(f"  ❌ {name}: Photo download failed")
                    failed_count += 1
            else:
                failed_count += 1
            
            # Progress update every 10 players
            if i % 10 == 0:
                print(f"\\n📊 Progress: {i}/{len(players)} processed")
                print(f"   ✅ Fixed: {successful_fixes}")
                print(f"   ❌ Failed: {failed_count}")
                print(f"   ⏱️  Success Rate: {(successful_fixes/i)*100:.1f}%")
            
            # Small delay between players  
            await asyncio.sleep(0.5)
    
    # Final summary
    print(f"\\n🎉 MLB ID FIX COMPLETE!")
    print(f"=" * 50)
    print(f"📊 Final Results:")
    print(f"   Total Players: {len(players)}")
    print(f"   Successfully Fixed: {successful_fixes}")
    print(f"   Failed: {failed_count}")
    print(f"   Success Rate: {(successful_fixes/len(players))*100:.1f}%")
    
    return successful_fixes

if __name__ == "__main__":
    print("🚀 Starting comprehensive MLB ID fix...")
    result = asyncio.run(fix_all_mlb_ids())
    print(f"\\n✅ Process complete! Fixed {result} players.")