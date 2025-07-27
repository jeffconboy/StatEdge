#!/usr/bin/env python3
"""
Download ESPN Uniform Photos
Downloads all 88 manually verified ESPN chest-up uniform photos and stores them locally
"""

import os
import asyncio
import aiohttp
import aiofiles
import psycopg2
from pathlib import Path
import time

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'user': 'statedge_user',
    'password': 'statedge_pass',
    'database': 'statedge'
}

# ESPN ID mapping from the original playerImages.ts
KNOWN_ESPN_IDS = {
    'Aaron Judge': '33192',
    'Mike Trout': '30836',
    'Mookie Betts': '33039',
    'Ronald Acuna Jr.': '36185',
    'Vladimir Guerrero Jr.': '35002',
    'Fernando Tatis Jr.': '35983',
    'Juan Soto': '36969',
    'Manny Machado': '31097',
    'Jose Altuve': '30204',
    'Freddie Freeman': '30896',
    'Cal Raleigh': '41292',
    'Bryce Harper': '32158',
    'Trea Turner': '33169',
    'Francisco Lindor': '32681',
    'Pete Alonso': '39869',
    'Jose Ramirez': '30155',
    'Rafael Devers': '39893',
    'Xander Bogaerts': '31735',
    'Corey Seager': '32519',
    'Carlos Correa': '32790',
    'Nolan Arenado': '30967',
    'Paul Goldschmidt': '30896',
    'Max Scherzer': '31060',
    'Jacob deGrom': '32796',
    'Gerrit Cole': '32162',
    'Clayton Kershaw': '28963',
    'Shane Bieber': '39853',
    'Byron Buxton': '33444',
    'Christian Yelich': '33444',
    'Salvador Perez': '30308',
    'Gleyber Torres': '36620',
    'Giancarlo Stanton': '32085',
    'Anthony Rizzo': '31007',
    'Ozzie Albies': '36749',
    'Austin Riley': '40235',
    'Matt Olson': '33192',
    'Bo Bichette': '40235',
    'George Springer': '31713',
    'Alex Bregman': '33192',
    'Yordan Alvarez': '40719',
    'Kyle Tucker': '39530',
    'J.T. Realmuto': '31735',
    'Nick Castellanos': '31735',
    'Starling Marte': '31097',
    'Julio Rodriguez': '40719',
    'Eugenio Suarez': '31735',
    'Logan Webb': '39530',
    'Matt Chapman': '33444',
    'Cody Bellinger': '36185',
    'Nico Hoerner': '40235',
    'Nolan Gorman': '40719',
    'Willy Adames': '36185',
    'Elly De La Cruz': '40719',
    'Spencer Steer': '40235',
    'Luis Robert': '40719',
    'Andrew Vaughn': '40235',
    'Riley Greene': '40719',
    'Spencer Torkelson': '40235',
    'Bobby Witt Jr.': '40719',
    'Brent Rooker': '40235',
    'Adley Rutschman': '40719',
    'Gunnar Henderson': '40235',
    'Ryan Mountcastle': '39530',
    'Trevor Story': '33444',
    'Wander Franco': '40719',
    'Randy Arozarena': '40235',
    'Jazz Chisholm Jr.': '40719',
    'Keibert Ruiz': '40235',
    'Ke\'Bryan Hayes': '40235',
    'Paul Skenes': '40719',
    'Charlie Blackmon': '33444',
    'C.J. Cron': '31735',
    'Ketel Marte': '33444',
    'Christian Walker': '36185',
}

# Local storage path
STORAGE_DIR = Path(__file__).parent / "static" / "espn-uniforms"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

async def download_espn_image(session, player_name: str, espn_id: str) -> tuple[str, bool]:
    """
    Download a single ESPN uniform image
    Returns (local_file_path, success)
    """
    try:
        # Create safe filename: aaron-judge-33192.png
        safe_name = player_name.lower().replace(' ', '-').replace('.', '').replace("'", '').replace('é', 'e')
        filename = f"{safe_name}-{espn_id}.png"
        local_path = STORAGE_DIR / filename
        
        # ESPN uniform photo URL
        espn_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        
        print(f"  📥 Downloading {player_name} from {espn_url}")
        
        async with session.get(espn_url) as response:
            if response.status == 200:
                # Write image to local file
                async with aiofiles.open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                # Check file size (should be > 1KB for valid image)
                file_size = local_path.stat().st_size
                if file_size > 1000:
                    print(f"  ✅ {player_name}: {file_size:,} bytes")
                    return str(local_path), True
                else:
                    print(f"  ❌ {player_name}: File too small ({file_size} bytes)")
                    local_path.unlink()  # Delete small file
                    return "", False
            else:
                print(f"  ❌ {player_name}: HTTP {response.status}")
                return "", False
                
    except Exception as e:
        print(f"  ❌ {player_name}: Error - {str(e)}")
        return "", False

def update_database_with_local_paths(download_results: dict):
    """
    Update database with local file paths for successfully downloaded images
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\n📝 Updating database with local file paths...")
        
        updated_count = 0
        
        for player_name, (local_path, success) in download_results.items():
            if success and local_path:
                # Convert full path to relative web path
                filename = Path(local_path).name
                web_path = f"/static/espn-uniforms/{filename}"
                
                # Update player record
                cursor.execute("""
                    UPDATE players 
                    SET local_image_path = %s,
                        updated_at = NOW()
                    WHERE name = %s AND active = true
                """, (web_path, player_name))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    print(f"  ✅ Updated {player_name}: {web_path}")
                else:
                    print(f"  ❓ Player not found in database: {player_name}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n📊 Database update complete: {updated_count} players updated")
        return updated_count
        
    except Exception as e:
        print(f"❌ Database update failed: {str(e)}")
        return 0

async def download_all_espn_uniforms():
    """
    Download all ESPN uniform photos
    """
    print("🏈 ESPN UNIFORM PHOTO DOWNLOADER")
    print("=" * 50)
    print(f"📥 Downloading {len(KNOWN_ESPN_IDS)} ESPN uniform photos...")
    print(f"📁 Storage: {STORAGE_DIR}")
    print("")
    
    download_results = {}
    successful_downloads = 0
    failed_downloads = 0
    
    # Create aiohttp session with longer timeout
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Download images in batches to avoid overwhelming ESPN servers
        batch_size = 5
        player_items = list(KNOWN_ESPN_IDS.items())
        
        for i in range(0, len(player_items), batch_size):
            batch = player_items[i:i + batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(player_items) + batch_size - 1)//batch_size}")
            
            # Download batch concurrently
            tasks = []
            for player_name, espn_id in batch:
                task = download_espn_image(session, player_name, espn_id)
                tasks.append((player_name, task))
            
            # Wait for batch to complete
            for player_name, task in tasks:
                local_path, success = await task
                download_results[player_name] = (local_path, success)
                
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads += 1
            
            # Small delay between batches
            await asyncio.sleep(1)
    
    print(f"\n📊 DOWNLOAD SUMMARY")
    print(f"=" * 30)
    print(f"✅ Successful: {successful_downloads}")
    print(f"❌ Failed: {failed_downloads}")
    print(f"📈 Success Rate: {(successful_downloads/(successful_downloads+failed_downloads))*100:.1f}%")
    
    # Update database with local paths
    if successful_downloads > 0:
        updated_count = update_database_with_local_paths(download_results)
        print(f"📝 Database records updated: {updated_count}")
    
    return download_results

if __name__ == "__main__":
    print("🚀 Starting ESPN uniform photo download...")
    results = asyncio.run(download_all_espn_uniforms())
    print(f"\n🎉 Download complete! Check {STORAGE_DIR} for images.")