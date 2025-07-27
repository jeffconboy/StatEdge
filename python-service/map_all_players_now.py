#!/usr/bin/env python3
"""
Map ALL 1,693 Active MLB Players to ESPN IDs
Direct database connection approach
"""

import psycopg2
import requests
import time
from typing import Dict, List, Tuple

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'user': 'statedge_user',
    'password': 'statedge_pass',
    'database': 'statedge'
}

# Known ESPN mappings (verified working)
VERIFIED_MAPPINGS = {
    'Aaron Judge': '33192',
    'Mike Trout': '30836',
    'Mookie Betts': '33039',
    'Ronald Acuna Jr.': '36185',
    'Vladimir Guerrero Jr.': '35002',
    'Fernando Tatis Jr.': '35983',
    'Juan Soto': '36969',
    'Manny Machado': '31097',
    'Jose Altuve': '30204',
    'Cal Raleigh': '41292',
    'Pete Alonso': '39869',
    # Add more verified mappings here as we find them
}

def test_espn_url(espn_id: str) -> bool:
    """Test if ESPN ID returns a valid image"""
    try:
        url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def get_all_active_players() -> List[Tuple]:
    """Get all active players from database"""
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
    
    return players

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
        print(f"Failed to update player {player_id}: {e}")
        return False

def systematic_espn_mapping():
    """Map all players systematically"""
    
    print("🔍 Starting systematic ESPN mapping for ALL active MLB players")
    print("=" * 60)
    
    # Get all players
    players = get_all_active_players()
    total_players = len(players)
    
    print(f"📊 Found {total_players} active players in database")
    
    mapped_count = 0
    verified_count = 0
    updated_count = 0
    
    for i, (player_id, name, mlb_id, team, current_espn_id) in enumerate(players, 1):
        print(f"\n[{i}/{total_players}] Processing: {name} ({team})")
        
        # Check if we have a verified mapping
        espn_id = VERIFIED_MAPPINGS.get(name)
        
        if espn_id:
            mapped_count += 1
            
            # Test the ESPN ID
            if test_espn_url(espn_id):
                verified_count += 1
                print(f"   ✅ Verified ESPN ID: {espn_id}")
                
                # Update database if different
                if espn_id != current_espn_id:
                    if update_player_espn_id(player_id, espn_id):
                        updated_count += 1
                        print(f"   📝 Updated database with ESPN ID: {espn_id}")
                    else:
                        print(f"   ❌ Failed to update database")
                else:
                    print(f"   ✓ Already has correct ESPN ID: {espn_id}")
            else:
                print(f"   ⚠️ ESPN ID {espn_id} failed validation")
                
        elif current_espn_id:
            # Validate existing ESPN ID
            if test_espn_url(current_espn_id):
                verified_count += 1
                print(f"   ✓ Existing ESPN ID validated: {current_espn_id}")
            else:
                print(f"   ❌ Existing ESPN ID invalid: {current_espn_id}")
        else:
            print(f"   ❓ No ESPN ID mapping found")
        
        # Small delay to be respectful to ESPN servers
        if i % 10 == 0:
            time.sleep(1)
    
    print(f"\n🎉 Systematic Mapping Complete!")
    print(f"📊 Final Statistics:")
    print(f"   Total Players: {total_players}")
    print(f"   Players with Verified Mappings: {mapped_count}")
    print(f"   ESPN IDs Validated: {verified_count}")
    print(f"   Database Updates Made: {updated_count}")
    print(f"   Coverage: {(verified_count/total_players)*100:.1f}%")
    
    return {
        'total': total_players,
        'mapped': mapped_count,
        'verified': verified_count,
        'updated': updated_count
    }

def show_sample_results():
    """Show sample of mapped players"""
    print(f"\n📸 Sample Verified Players:")
    
    for name, espn_id in list(VERIFIED_MAPPINGS.items())[:10]:
        url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
        print(f"   {name}: {url}")

if __name__ == "__main__":
    try:
        print("🎯 Complete MLB Player ESPN Mapping")
        print("Mapping all 1,693 active players...")
        
        results = systematic_espn_mapping()
        show_sample_results()
        
        print(f"\n🚀 Next Steps:")
        if results['verified'] >= results['total'] * 0.8:
            print("✅ Excellent coverage achieved!")
        elif results['verified'] >= results['total'] * 0.5:
            print("👍 Good coverage achieved!")
            print("💡 Consider adding more verified ESPN ID mappings")
        else:
            print("⚠️ Low coverage. Need to expand verified mappings")
        
        print("🔧 Frontend will use professional placeholders for unmapped players")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check database connection and try again")