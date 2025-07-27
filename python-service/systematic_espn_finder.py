#!/usr/bin/env python3
"""
Systematic ESPN ID Finder
Based on analysis of successful mappings - uses direct URL testing approach
"""

import psycopg2
import requests
import time
from typing import Optional, List, Tuple

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'user': 'statedge_user',
    'password': 'statedge_pass',
    'database': 'statedge'
}

def create_espn_player_slug(name: str) -> str:
    """Create ESPN player URL slug from name"""
    # Convert "Aaron Judge" -> "aaron-judge"
    return name.lower().replace(' ', '-').replace('.', '').replace("'", '')

def test_espn_player_page(espn_id: str, name_slug: str) -> bool:
    """Test if ESPN player page exists and is valid"""
    try:
        url = f"https://www.espn.com/mlb/player/_/id/{espn_id}/{name_slug}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=8)
        
        # Check if page exists and contains player name
        if response.status_code == 200:
            content = response.text.lower()
            # Verify this is actually the right player
            name_parts = name_slug.split('-')
            
            # Check if major name parts appear on the page
            name_found = all(part in content for part in name_parts if len(part) > 2)
            
            return name_found
            
    except Exception as e:
        return False
    
    return False

def find_espn_id_systematic(player_name: str) -> Optional[str]:
    """Find ESPN ID by systematically testing ID ranges"""
    
    name_slug = create_espn_player_slug(player_name)
    print(f"   Testing ESPN URLs for: {name_slug}")
    
    # ESPN ID ranges to test (based on successful patterns)
    # Recent players: 35000-45000, Veterans: 30000-35000, Older: 25000-30000
    id_ranges = [
        range(35000, 42000, 100),  # Recent players, test every 100
        range(30000, 35000, 100),  # Veterans
        range(42000, 45000, 100),  # Very recent
        range(25000, 30000, 200),  # Older players
    ]
    
    for id_range in id_ranges:
        for base_id in id_range:
            # Test 10 IDs around each base
            for offset in range(0, 100, 10):
                test_id = str(base_id + offset)
                
                if test_espn_player_page(test_id, name_slug):
                    print(f"   ✅ Found at ESPN ID: {test_id}")
                    return test_id
                
            # Small delay every 10 tests
            time.sleep(0.1)
            
    return None

def verify_espn_image_url(espn_id: str) -> bool:
    """Verify ESPN ID returns valid image"""
    try:
        url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def update_player_espn_id(player_id: int, espn_id: str) -> bool:
    """Update player's ESPN ID in database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE players 
            SET espn_id = %s 
            WHERE id = %s
        """, (espn_id, player_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Database update failed: {e}")
        return False

def get_unmapped_players(limit: int = 50) -> List[Tuple]:
    """Get players without ESPN IDs"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, current_team, mlb_id
        FROM players 
        WHERE active = true AND espn_id IS NULL
        ORDER BY 
            CASE WHEN current_team IS NOT NULL THEN 1 ELSE 2 END,
            name
        LIMIT %s
    """, (limit,))
    
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return players

def systematic_mapping_sprint(batch_size: int = 20):
    """Run systematic mapping in manageable batches"""
    
    print("🔍 SYSTEMATIC ESPN ID FINDER")
    print("=" * 40)
    print("Based on successful mapping patterns")
    print("")
    
    batch_num = 1
    total_found = 0
    total_processed = 0
    
    while True:
        # Get next batch of unmapped players
        players = get_unmapped_players(batch_size)
        
        if not players:
            print("✅ No more unmapped players found!")
            break
            
        print(f"📦 Processing Batch {batch_num} ({len(players)} players)")
        print("-" * 50)
        
        batch_found = 0
        
        for i, (player_id, name, team, mlb_id) in enumerate(players, 1):
            print(f"[{i}/{len(players)}] 🔍 {name} ({team})")
            
            # Find ESPN ID systematically
            espn_id = find_espn_id_systematic(name)
            
            if espn_id:
                # Verify image URL works
                if verify_espn_image_url(espn_id):
                    print(f"   ✅ Verified image URL")
                    
                    # Update database
                    if update_player_espn_id(player_id, espn_id):
                        batch_found += 1
                        total_found += 1
                        print(f"   📝 Updated database with ESPN ID: {espn_id}")
                        
                        # Show the working URL
                        image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
                        print(f"   🖼️  {image_url}")
                    else:
                        print(f"   ❌ Database update failed")
                else:
                    print(f"   ⚠️  ESPN ID {espn_id} has no valid image")
            else:
                print(f"   ❓ No ESPN ID found")
            
            total_processed += 1
            
            # Progress delay
            time.sleep(2)
        
        # Batch summary
        success_rate = (batch_found / len(players)) * 100
        print(f"\n📊 Batch {batch_num} Results:")
        print(f"   Found: {batch_found}/{len(players)} ({success_rate:.1f}%)")
        print(f"   Total Found: {total_found}")
        print(f"   Total Processed: {total_processed}")
        
        batch_num += 1
        
        # Ask if user wants to continue
        if batch_found == 0:
            print(f"\n⚠️  No players found in this batch.")
            break
        else:
            print(f"\n✅ Batch complete! Found {batch_found} ESPN IDs")
            
        print(f"Continue with next batch? (y/n): ", end="")
        try:
            choice = input().lower()
            if choice != 'y':
                break
        except:
            break
    
    # Final summary
    print(f"\n🎉 SYSTEMATIC MAPPING COMPLETE!")
    print(f"📊 Final Results:")
    print(f"   Total Players Processed: {total_processed}")
    print(f"   ESPN IDs Found: {total_found}")
    print(f"   Success Rate: {(total_found/total_processed)*100:.1f}%" if total_processed > 0 else "N/A")
    
    # Check final coverage
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM players WHERE active = true")
    total_active = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM players WHERE active = true AND espn_id IS NOT NULL")
    with_espn = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    coverage = (with_espn / total_active) * 100
    print(f"\n📈 Total Database Coverage: {with_espn}/{total_active} ({coverage:.1f}%)")
    
    return {
        'processed': total_processed,
        'found': total_found,
        'total_coverage': coverage
    }

if __name__ == "__main__":
    try:
        print("🎯 Systematic ESPN ID Discovery")
        print("Using successful mapping patterns from working players")
        
        results = systematic_mapping_sprint(batch_size=10)  # Start with small batches
        
        if results['found'] > 0:
            print(f"\n🎊 SUCCESS! Found {results['found']} new ESPN IDs")
            print("Players will now show correct chest-up uniform photos!")
        else:
            print(f"\n⚠️  No new ESPN IDs found - may need different approach")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Mapping interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")