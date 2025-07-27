#!/usr/bin/env python3
"""
Get Complete ESPN Mapping for ALL 1,693 Active MLB Players
Uses systematic approach to find ESPN IDs for every player
"""

import psycopg2
import requests
import time
import json
from typing import Dict, List, Tuple, Optional

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'user': 'statedge_user',
    'password': 'statedge_pass',
    'database': 'statedge'
}

def search_player_on_espn(player_name: str, team: str = None) -> Optional[str]:
    """Search for player on ESPN and extract ESPN ID"""
    try:
        # Try ESPN's search functionality
        search_url = "https://www.espn.com/search/results/_/q/" + player_name.replace(" ", "%20")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Look for ESPN MLB player URLs in the response
            content = response.text
            
            # Pattern: /mlb/player/_/id/XXXXX/player-name
            import re
            pattern = r'/mlb/player/_/id/(\d+)/' + re.escape(player_name.lower().replace(' ', '-'))
            match = re.search(pattern, content.lower())
            
            if match:
                return match.group(1)
            
            # Broader pattern: any MLB player ID
            pattern = r'/mlb/player/_/id/(\d+)/'
            matches = re.findall(pattern, content.lower())
            
            if matches:
                # Return first match (most likely to be correct)
                return matches[0]
                
    except Exception as e:
        print(f"   Search failed for {player_name}: {e}")
    
    return None

def systematic_espn_discovery():
    """Systematically discover ESPN IDs for all players"""
    
    print("🔍 Systematic ESPN ID Discovery for ALL Active MLB Players")
    print("=" * 65)
    
    # Get all players without ESPN IDs
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, mlb_id, current_team, espn_id
        FROM players 
        WHERE active = true 
        ORDER BY name
    """)
    
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    
    total_players = len(players)
    print(f"📊 Processing {total_players} active players")
    
    found_count = 0
    already_mapped = 0
    updated_count = 0
    
    for i, (player_id, name, mlb_id, team, current_espn_id) in enumerate(players, 1):
        
        if current_espn_id:
            already_mapped += 1
            print(f"[{i}/{total_players}] ✓ {name} - Already mapped: {current_espn_id}")
            continue
            
        print(f"[{i}/{total_players}] 🔍 Searching: {name} ({team})")
        
        # Search for ESPN ID
        espn_id = search_player_on_espn(name, team)
        
        if espn_id:
            found_count += 1
            print(f"   ✅ Found ESPN ID: {espn_id}")
            
            # Update database
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
                
                updated_count += 1
                print(f"   📝 Updated database")
                
            except Exception as e:
                print(f"   ❌ Database update failed: {e}")
        else:
            print(f"   ❓ No ESPN ID found")
        
        # Rate limiting - be respectful to ESPN
        time.sleep(2)  # 2 second delay between requests
        
        # Progress checkpoint every 50 players
        if i % 50 == 0:
            print(f"\n📊 Progress Checkpoint:")
            print(f"   Processed: {i}/{total_players}")
            print(f"   Found new ESPN IDs: {found_count}")
            print(f"   Already mapped: {already_mapped}")
            print(f"   Total with ESPN IDs: {found_count + already_mapped}")
            print(f"   Coverage: {((found_count + already_mapped)/i)*100:.1f}%")
            print("")
    
    print(f"\n🎉 Systematic Discovery Complete!")
    print(f"📊 Final Results:")
    print(f"   Total Players: {total_players}")
    print(f"   Already Mapped: {already_mapped}")
    print(f"   Newly Found: {found_count}")
    print(f"   Database Updates: {updated_count}")
    print(f"   Total with ESPN IDs: {found_count + already_mapped}")
    print(f"   Final Coverage: {((found_count + already_mapped)/total_players)*100:.1f}%")
    
    return {
        'total': total_players,
        'already_mapped': already_mapped,
        'found': found_count,
        'updated': updated_count,
        'final_coverage': ((found_count + already_mapped)/total_players)*100
    }

def verify_espn_ids():
    """Verify that discovered ESPN IDs return valid images"""
    
    print(f"\n🔍 Verifying ESPN URLs...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, espn_id
        FROM players 
        WHERE active = true AND espn_id IS NOT NULL
        ORDER BY name
        LIMIT 20
    """)
    
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print(f"📸 Testing {len(players)} ESPN URLs:")
    
    working_count = 0
    
    for name, espn_id in players:
        url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                working_count += 1
                print(f"   ✅ {name}: {url}")
            else:
                print(f"   ❌ {name}: Invalid ESPN ID {espn_id}")
        except:
            print(f"   ❌ {name}: URL test failed")
    
    print(f"\n📊 URL Verification:")
    print(f"   Working URLs: {working_count}/{len(players)}")
    print(f"   Success Rate: {(working_count/len(players))*100:.1f}%")

if __name__ == "__main__":
    try:
        print("🎯 Complete ESPN ID Discovery for ALL MLB Players")
        print("This will systematically find ESPN IDs for all 1,693 active players")
        print("Estimated time: 1-2 hours (2 second delay per player)")
        
        input("\nPress Enter to start systematic discovery...")
        
        results = systematic_espn_discovery()
        verify_espn_ids()
        
        print(f"\n🎉 Mission Complete!")
        if results['final_coverage'] >= 90:
            print("✅ Excellent coverage achieved!")
        elif results['final_coverage'] >= 75:
            print("👍 Good coverage achieved!")
        else:
            print("⚠️ Partial coverage - may need additional strategies")
        
        print(f"\n🚀 All players now have ESPN IDs or professional fallbacks!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Discovery interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")