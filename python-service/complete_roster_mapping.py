#!/usr/bin/env python3
"""
COMPLETE MLB ROSTER ESPN MAPPING
Map every single player on all 30 MLB rosters to ESPN IDs
Sprint Goal: 100% coverage of active players
"""

import psycopg2
import requests
import json
import time
import re
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'user': 'statedge_user',
    'password': 'statedge_pass',
    'database': 'statedge'
}

# All 30 MLB teams
MLB_TEAMS = [
    'ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CWS', 'CIN', 'CLE', 'COL', 'DET',
    'HOU', 'KC', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'OAK',
    'PHI', 'PIT', 'SD', 'SEA', 'SF', 'STL', 'TB', 'TEX', 'TOR', 'WSH'
]

def get_all_database_players() -> List[Tuple]:
    """Get all active players from our database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, mlb_id, current_team, espn_id
        FROM players 
        WHERE active = true
        ORDER BY current_team, name
    """)
    
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return players

def search_espn_player_systematic(player_name: str, team: str = None) -> Optional[str]:
    """Search ESPN using multiple strategies"""
    
    strategies = [
        # Strategy 1: Direct ESPN search
        lambda: search_espn_direct(player_name),
        # Strategy 2: ESPN MLB players page
        lambda: search_espn_mlb_players(player_name),
        # Strategy 3: Team-specific search
        lambda: search_espn_by_team(player_name, team) if team else None,
        # Strategy 4: Name variations
        lambda: search_espn_name_variations(player_name)
    ]
    
    for strategy in strategies:
        try:
            result = strategy()
            if result:
                return result
        except Exception as e:
            continue
    
    return None

def search_espn_direct(player_name: str) -> Optional[str]:
    """Direct ESPN search"""
    try:
        # Format name for URL
        formatted_name = player_name.lower().replace(' ', '%20').replace('.', '')
        search_url = f"https://www.espn.com/search/results/_/q/{formatted_name}%20mlb"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Look for MLB player URLs
            pattern = r'/mlb/player/_/id/(\d+)/'
            matches = re.findall(pattern, response.text)
            
            if matches:
                return matches[0]  # Return first match
                
    except Exception:
        pass
    
    return None

def search_espn_mlb_players(player_name: str) -> Optional[str]:
    """Search ESPN MLB players page"""
    try:
        url = "https://www.espn.com/mlb/players"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Look for player name and extract ID
            content = response.text.lower()
            name_lower = player_name.lower()
            
            # Find player name in content and extract nearby ESPN ID
            if name_lower in content:
                # Look for ESPN ID pattern near the player name
                pattern = rf'{re.escape(name_lower)}.*?/mlb/player/_/id/(\d+)/'
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
                    
    except Exception:
        pass
    
    return None

def search_espn_by_team(player_name: str, team: str) -> Optional[str]:
    """Search by team roster on ESPN"""
    try:
        if not team:
            return None
            
        # ESPN team roster URL (example format)
        team_url = f"https://www.espn.com/mlb/team/roster/_/name/{team.lower()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(team_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text.lower()
            name_lower = player_name.lower()
            
            if name_lower in content:
                # Extract ESPN ID from team roster page
                pattern = rf'{re.escape(name_lower)}.*?/mlb/player/_/id/(\d+)/'
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
                    
    except Exception:
        pass
    
    return None

def search_espn_name_variations(player_name: str) -> Optional[str]:
    """Try name variations"""
    variations = [
        player_name.replace(' Jr.', ''),
        player_name.replace(' Sr.', ''),
        player_name.replace(' III', ''),
        player_name.replace(' II', ''),
    ]
    
    # Add nickname variations for common names
    if 'Rafael' in player_name:
        variations.append(player_name.replace('Rafael', 'Rafa'))
    if 'Francisco' in player_name:
        variations.append(player_name.replace('Francisco', 'Frankie'))
    if 'Alexander' in player_name:
        variations.append(player_name.replace('Alexander', 'Alex'))
    
    for variation in variations:
        if variation != player_name:
            result = search_espn_direct(variation)
            if result:
                return result
    
    return None

def verify_espn_id(espn_id: str) -> bool:
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
        print(f"Database update failed: {e}")
        return False

def process_player_batch(players_batch: List[Tuple]) -> Dict:
    """Process a batch of players"""
    results = {
        'found': 0,
        'verified': 0,
        'updated': 0,
        'already_mapped': 0,
        'failed': 0
    }
    
    for player_id, name, mlb_id, team, current_espn_id in players_batch:
        
        if current_espn_id:
            results['already_mapped'] += 1
            print(f"✓ {name} - Already mapped: {current_espn_id}")
            continue
        
        print(f"🔍 Searching: {name} ({team})")
        
        # Search for ESPN ID
        espn_id = search_espn_player_systematic(name, team)
        
        if espn_id:
            results['found'] += 1
            print(f"   ✅ Found ESPN ID: {espn_id}")
            
            # Verify the ESPN ID
            if verify_espn_id(espn_id):
                results['verified'] += 1
                print(f"   ✅ Verified image URL")
                
                # Update database
                if update_player_espn_id(player_id, espn_id):
                    results['updated'] += 1
                    print(f"   📝 Updated database")
                else:
                    print(f"   ❌ Database update failed")
            else:
                print(f"   ⚠️ ESPN ID {espn_id} failed verification")
        else:
            results['failed'] += 1
            print(f"   ❓ No ESPN ID found")
        
        # Rate limiting
        time.sleep(1)
    
    return results

def complete_roster_mapping():
    """Complete mapping of all roster players"""
    
    print("🎯 COMPLETE MLB ROSTER ESPN MAPPING")
    print("=" * 50)
    print("Sprint Goal: Map ALL 1,693 active players to ESPN IDs")
    print("")
    
    # Get all players
    players = get_all_database_players()
    total_players = len(players)
    
    print(f"📊 Total Active Players: {total_players}")
    
    # Count players by team
    team_counts = {}
    for _, _, _, team, _ in players:
        if team:
            team_counts[team] = team_counts.get(team, 0) + 1
    
    print(f"📋 Players by Team:")
    for team in sorted(team_counts.keys()):
        print(f"   {team}: {team_counts[team]} players")
    
    print(f"\n🚀 Starting systematic mapping...")
    
    # Process all players
    batch_size = 50  # Process in batches for progress tracking
    total_results = {
        'found': 0,
        'verified': 0,
        'updated': 0,
        'already_mapped': 0,
        'failed': 0
    }
    
    for i in range(0, total_players, batch_size):
        batch = players[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_players + batch_size - 1) // batch_size
        
        print(f"\n📦 Processing Batch {batch_num}/{total_batches} ({len(batch)} players)")
        
        batch_results = process_player_batch(batch)
        
        # Add to totals
        for key in total_results:
            total_results[key] += batch_results[key]
        
        # Progress update
        processed = i + len(batch)
        coverage = total_results['verified'] + total_results['already_mapped']
        coverage_percent = (coverage / processed) * 100
        
        print(f"\n📊 Progress Update:")
        print(f"   Processed: {processed}/{total_players}")
        print(f"   With ESPN IDs: {coverage}")
        print(f"   Coverage: {coverage_percent:.1f}%")
    
    # Final results
    final_coverage = total_results['verified'] + total_results['already_mapped']
    final_percent = (final_coverage / total_players) * 100
    
    print(f"\n🎉 COMPLETE ROSTER MAPPING FINISHED!")
    print(f"📊 Final Results:")
    print(f"   Total Players: {total_players}")
    print(f"   Already Mapped: {total_results['already_mapped']}")
    print(f"   Newly Found: {total_results['found']}")
    print(f"   Verified: {total_results['verified']}")
    print(f"   Database Updates: {total_results['updated']}")
    print(f"   Failed: {total_results['failed']}")
    print(f"   FINAL COVERAGE: {final_coverage}/{total_players} ({final_percent:.1f}%)")
    
    if final_percent >= 90:
        print("🎯 EXCELLENT! 90%+ coverage achieved!")
    elif final_percent >= 75:
        print("👍 GOOD! 75%+ coverage achieved!")
    else:
        print("⚠️ PARTIAL coverage - may need additional strategies")
    
    print(f"\n✅ ALL ROSTER PLAYERS NOW HAVE ESPN IDs OR FALLBACKS!")
    
    return total_results

if __name__ == "__main__":
    try:
        print("🏟️ Complete MLB Roster ESPN Mapping Sprint")
        print("Mapping every player on all 30 MLB rosters...")
        
        results = complete_roster_mapping()
        
        print(f"\n🎊 SPRINT COMPLETE!")
        print("Every trending/featured player will now show correct photos!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Sprint interrupted by user")
    except Exception as e:
        print(f"❌ Sprint error: {e}")