#!/usr/bin/env python3
"""
Download MLB photos for the 10 players with valid MLB IDs
"""

import os
import asyncio
import aiohttp
import aiofiles
import psycopg2
from pathlib import Path
import re

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

async def download_valid_mlb_photos():
    """Download photos for players with valid MLB IDs"""
    
    print("⚾ DOWNLOADING VALID MLB PHOTOS")
    print("=" * 40)
    
    # Get players with valid MLB IDs
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, mlb_id, current_team
        FROM players 
        WHERE active = true AND mlb_id > 0
        ORDER BY name
    """)
    
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print(f"📊 Found {len(players)} players with valid MLB IDs")
    
    successful_downloads = 0
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        for name, mlb_id, team in players:
            print(f"\n🔄 Processing {name} (ID: {mlb_id}, Team: {team})")
            
            # Generate MLB headshot URL directly
            photo_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_360,q_auto:best/v1/people/{mlb_id}/headshot/67/current"
            
            try:
                # Create filename
                safe_name = name.lower()
                safe_name = re.sub(r'[^\w\s-]', '', safe_name)
                safe_name = safe_name.replace(' ', '-')
                filename = f"{safe_name}-{mlb_id}.jpg"
                local_path = STORAGE_DIR / filename
                
                print(f"  📥 Downloading from: {photo_url}")
                
                async with session.get(photo_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        file_size = local_path.stat().st_size
                        if file_size > 1000:
                            successful_downloads += 1
                            print(f"  ✅ Downloaded: {file_size:,} bytes")
                            
                            # Update database
                            web_path = f"/static/mlb-photos/{filename}"
                            conn = psycopg2.connect(**DB_CONFIG)
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE players 
                                SET local_image_path = %s
                                WHERE mlb_id = %s
                            """, (web_path, mlb_id))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            
                        else:
                            print(f"  ❌ File too small: {file_size} bytes")
                            local_path.unlink()
                    else:
                        print(f"  ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
    
    print(f"\n🎉 Complete! Downloaded {successful_downloads}/{len(players)} photos")
    return successful_downloads

if __name__ == "__main__":
    result = asyncio.run(download_valid_mlb_photos())