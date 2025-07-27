#!/usr/bin/env python3
"""
MLB.com Player Photo Scraper
Downloads official player photos from MLB.com for all 1,693 active players
"""

import os
import asyncio
import aiohttp
import aiofiles
import psycopg2
from pathlib import Path
import time
from bs4 import BeautifulSoup
import re

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'user': 'statedge_user',
    'password': 'statedge_pass',
    'database': 'statedge'
}

# Local storage path
STORAGE_DIR = Path(__file__).parent / "static" / "mlb-photos"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def create_mlb_url(name: str, mlb_id: int) -> str:
    """
    Create MLB.com player URL from name and ID
    Example: "Ranger Suarez" + 624133 -> "https://www.mlb.com/player/ranger-suarez-624133"
    """
    # Convert name to URL format: lowercase, spaces to hyphens, remove special chars
    clean_name = name.lower()
    clean_name = re.sub(r'[^\w\s-]', '', clean_name)  # Remove special chars except spaces and hyphens
    clean_name = clean_name.replace(' ', '-')
    clean_name = re.sub(r'-+', '-', clean_name)  # Remove multiple consecutive hyphens
    
    return f"https://www.mlb.com/player/{clean_name}-{mlb_id}"

async def scrape_player_photo(session, name: str, mlb_id: int) -> tuple[str, str, bool]:
    """
    Scrape MLB.com player page to find official photo URL
    Returns (photo_url, local_file_path, success)
    """
    try:
        mlb_url = create_mlb_url(name, mlb_id)
        print(f"  🔍 Scraping {name}: {mlb_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with session.get(mlb_url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for player headshot images - try multiple selectors
                photo_url = None
                
                # Try different image selectors that MLB.com uses
                selectors = [
                    'img[src*="headshot"]',
                    'img[src*="people"]',
                    'img[alt*="headshot"]',
                    '.player-header img',
                    '.player-bio img',
                    'img[src*="mlbstatic.com"]'
                ]
                
                for selector in selectors:
                    img_tags = soup.select(selector)
                    for img in img_tags:
                        src = img.get('src', '')
                        if src and ('headshot' in src or 'people' in src) and 'mlbstatic.com' in src:
                            # Get the highest resolution version
                            photo_url = src
                            # Try to upgrade to higher resolution
                            if 'w_213' in photo_url:
                                photo_url = photo_url.replace('w_213', 'w_360')
                            break
                    
                    if photo_url:
                        break
                
                if photo_url:
                    print(f"  📸 Found photo: {photo_url}")
                    return photo_url, "", True
                else:
                    print(f"  ❌ No photo found for {name}")
                    return "", "", False
                    
            else:
                print(f"  ❌ HTTP {response.status} for {name}")
                return "", "", False
                
    except Exception as e:
        print(f"  ❌ Error scraping {name}: {str(e)}")
        return "", "", False

async def download_photo(session, photo_url: str, name: str, mlb_id: int) -> tuple[str, bool]:
    """
    Download photo from MLB and store locally
    Returns (local_file_path, success)
    """
    try:
        # Create safe filename: ranger-suarez-624133.jpg
        safe_name = name.lower()
        safe_name = re.sub(r'[^\w\s-]', '', safe_name)
        safe_name = safe_name.replace(' ', '-')
        safe_name = re.sub(r'-+', '-', safe_name)
        
        filename = f"{safe_name}-{mlb_id}.jpg"
        local_path = STORAGE_DIR / filename
        
        print(f"  📥 Downloading {name} photo...")
        
        async with session.get(photo_url) as response:
            if response.status == 200:
                async with aiofiles.open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                # Check file size
                file_size = local_path.stat().st_size
                if file_size > 1000:
                    print(f"  ✅ {name}: {file_size:,} bytes")
                    return str(local_path), True
                else:
                    print(f"  ❌ {name}: File too small ({file_size} bytes)")
                    local_path.unlink()
                    return "", False
            else:
                print(f"  ❌ {name}: Download failed HTTP {response.status}")
                return "", False
                
    except Exception as e:
        print(f"  ❌ Download error for {name}: {str(e)}")
        return "", False

def get_all_active_players() -> list:
    """
    Get all active players from database
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, mlb_id, current_team
            FROM players 
            WHERE active = true AND mlb_id IS NOT NULL
            ORDER BY name
        """)
        
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"📊 Found {len(players)} active players in database")
        return players
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return []

def update_database_with_mlb_photos(results: dict):
    """
    Update database with local MLB photo paths
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\n📝 Updating database with MLB photo paths...")
        
        updated_count = 0
        
        for (name, mlb_id), (local_path, success) in results.items():
            if success and local_path:
                # Convert to web path
                filename = Path(local_path).name
                web_path = f"/static/mlb-photos/{filename}"
                
                cursor.execute("""
                    UPDATE players 
                    SET local_image_path = %s,
                        updated_at = NOW()
                    WHERE mlb_id = %s AND active = true
                """, (web_path, mlb_id))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    if updated_count % 100 == 0:
                        print(f"  ✅ Updated {updated_count} players...")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"📊 Database update complete: {updated_count} players updated")
        return updated_count
        
    except Exception as e:
        print(f"❌ Database update failed: {str(e)}")
        return 0

async def download_all_mlb_photos():
    """
    Download all MLB player photos
    """
    print("⚾ MLB.COM PLAYER PHOTO SCRAPER")
    print("=" * 50)
    
    # Get all players
    players = get_all_active_players()
    if not players:
        print("❌ No players found!")
        return
    
    print(f"📥 Processing {len(players)} MLB players...")
    print(f"📁 Storage: {STORAGE_DIR}")
    print("")
    
    results = {}
    successful_scrapes = 0
    successful_downloads = 0
    failed_count = 0
    
    # Process in batches to avoid overwhelming MLB.com
    batch_size = 10
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i in range(0, len(players), batch_size):
            batch = players[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(players) + batch_size - 1) // batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} players)")
            print("-" * 60)
            
            # Process batch
            for name, mlb_id, team in batch:
                print(f"\n🔄 Processing {name} (ID: {mlb_id}, Team: {team})")
                
                # Step 1: Scrape for photo URL
                photo_url, _, scrape_success = await scrape_player_photo(session, name, mlb_id)
                
                if scrape_success and photo_url:
                    successful_scrapes += 1
                    
                    # Step 2: Download photo
                    local_path, download_success = await download_photo(session, photo_url, name, mlb_id)
                    
                    if download_success:
                        successful_downloads += 1
                        results[(name, mlb_id)] = (local_path, True)
                    else:
                        failed_count += 1
                        results[(name, mlb_id)] = ("", False)
                else:
                    failed_count += 1
                    results[(name, mlb_id)] = ("", False)
            
            # Progress update
            print(f"\n📊 Batch {batch_num} Complete:")
            print(f"   Photos Found: {successful_scrapes}/{len(players)}")
            print(f"   Downloads: {successful_downloads}/{len(players)}")
            print(f"   Failed: {failed_count}/{len(players)}")
            
            # Delay between batches
            if batch_num < total_batches:
                print(f"⏱️  Waiting 3 seconds before next batch...")
                await asyncio.sleep(3)
    
    # Final summary
    print(f"\n🎉 MLB PHOTO SCRAPING COMPLETE!")
    print(f"=" * 50)
    print(f"📊 Final Results:")
    print(f"   Total Players: {len(players)}")
    print(f"   Photos Found: {successful_scrapes}")
    print(f"   Successfully Downloaded: {successful_downloads}")
    print(f"   Failed: {failed_count}")
    print(f"   Success Rate: {(successful_downloads/len(players))*100:.1f}%")
    
    # Update database
    if successful_downloads > 0:
        updated_count = update_database_with_mlb_photos(results)
        print(f"📝 Database records updated: {updated_count}")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting MLB.com photo scraping...")
    results = asyncio.run(download_all_mlb_photos())
    print(f"\n✅ Complete! Check {STORAGE_DIR} for downloaded photos.")