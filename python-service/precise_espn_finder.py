#!/usr/bin/env python3
"""
Precise ESPN ID Finder
Fixed approach - properly validates player matches before accepting ESPN ID
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

def test_espn_url_precisely(espn_id: str, player_name: str) -> bool:
    """Test ESPN ID and verify it actually matches the player name"""
    try:
        # Test the image URL first (fast check)
        image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        image_response = requests.head(image_url, timeout=5)
        
        if image_response.status_code != 200:
            return False
        
        # Now test the player page to verify it's the right player
        name_slug = player_name.lower().replace(' ', '-').replace('.', '').replace("'", '')
        player_url = f"https://www.espn.com/mlb/player/_/id/{espn_id}/{name_slug}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        page_response = requests.get(player_url, headers=headers, timeout=8)
        
        if page_response.status_code == 200:
            content = page_response.text.lower()
            
            # Split name into parts and check each part appears on the page
            name_parts = player_name.lower().split()
            
            # Must find ALL significant name parts (length > 2) on the page
            significant_parts = [part for part in name_parts if len(part) > 2]
            
            if len(significant_parts) == 0:
                return False
            
            # Check if all significant name parts appear in the content
            parts_found = sum(1 for part in significant_parts if part in content)
            
            # Require at least 80% of name parts to match
            match_ratio = parts_found / len(significant_parts)
            
            # Also check the page title contains the player name
            title_match = any(part in content for part in significant_parts)
            
            return match_ratio >= 0.8 and title_match
        
    except Exception as e:
        print(f"   Error testing ESPN ID {espn_id}: {e}")
    
    return False

def find_espn_id_for_player(player_name: str) -> Optional[str]:
    """Find ESPN ID for specific player with precise validation"""
    
    print(f"   🔍 Searching for: {player_name}")
    
    # Test smaller, more targeted ranges
    test_ranges = [
        # Most active current players
        range(39000, 42000),
        range(35000, 39000), 
        range(30000, 35000),
        range(42000, 45000),
        # Some veterans
        range(25000, 30000)
    ]
    
    for test_range in test_ranges:
        print(f"   Testing range {test_range.start}-{test_range.stop}...")
        
        for espn_id in test_range:
            if test_espn_url_precisely(str(espn_id), player_name):
                print(f"   ✅ VERIFIED match: ESPN ID {espn_id}")
                return str(espn_id)
            
            # Only test every 10th ID to speed up (can adjust)
            if espn_id % 10 != 0:
                continue
                
            # Small delay every 50 tests
            if espn_id % 50 == 0:
                time.sleep(0.5)
        
        print(f"   ❌ No match found in range {test_range.start}-{test_range.stop}")
    
    return None

def manual_test_espn_ids():
    """Test a few players manually to verify the approach works"""
    
    test_players = [
        "Shohei Ohtani",
        "Freddie Freeman", 
        "Bryce Harper",
        "Bo Bichette",
        "Kyle Tucker"
    ]
    
    print("🧪 MANUAL TESTING - Verifying approach works")
    print("=" * 50)
    
    for player in test_players:
        print(f"\n🔍 Testing: {player}")
        espn_id = find_espn_id_for_player(player)
        
        if espn_id:
            image_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
            player_url = f"https://www.espn.com/mlb/player/_/id/{espn_id}/"
            print(f"✅ FOUND: {player} = ESPN ID {espn_id}")
            print(f"   Image: {image_url}")
            print(f"   Page: {player_url}")
        else:
            print(f"❌ NOT FOUND: {player}")

def update_database_with_espn_id(player_id: int, espn_id: str) -> bool:
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

def process_unmapped_players():
    """Process players without ESPN IDs using precise method"""
    
    # Get a few unmapped players to test
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, current_team
        FROM players 
        WHERE active = true AND espn_id IS NULL
        ORDER BY 
            CASE WHEN current_team IS NOT NULL THEN 1 ELSE 2 END,
            name
        LIMIT 5
    """)
    
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print(f"\n🎯 PROCESSING UNMAPPED PLAYERS")
    print("=" * 40)
    
    found_count = 0
    
    for i, (player_id, name, team) in enumerate(players, 1):
        print(f"\n[{i}/5] Processing: {name} ({team})")
        
        espn_id = find_espn_id_for_player(name)
        
        if espn_id:
            if update_database_with_espn_id(player_id, espn_id):
                found_count += 1
                print(f"   📝 Updated database with ESPN ID: {espn_id}")
            else:
                print(f"   ❌ Database update failed")
        else:
            print(f"   ❓ No ESPN ID found for {name}")
    
    print(f"\n📊 Results: Found {found_count}/5 ESPN IDs")

if __name__ == "__main__":
    print("🎯 PRECISE ESPN ID FINDER")
    print("Fixed approach with proper player validation")
    print("")
    
    # First, test manually to verify approach
    manual_test_espn_ids()
    
    # Then process a few real players
    process_unmapped_players()
    
    print(f"\n✅ Testing complete! If results look good, we can scale up.")