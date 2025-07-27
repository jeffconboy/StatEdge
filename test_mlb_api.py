#!/usr/bin/env python3
"""
Test script to explore MLB Stats API endpoints and understand data structure
"""
import requests
import json
from datetime import datetime

def test_schedule_endpoint():
    """Test the schedule endpoint for daily games"""
    print("=== Testing Schedule Endpoint ===")
    
    # Test with current date
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher,linescore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Games: {data.get('totalGames', 0)}")
        
        if data.get('dates') and len(data['dates']) > 0:
            games = data['dates'][0].get('games', [])
            if games:
                print(f"Sample game structure:")
                print(json.dumps(games[0], indent=2)[:1000] + "...")
            else:
                print("No games found for today")
        
        return data
        
    except requests.RequestException as e:
        print(f"Error fetching schedule: {e}")
        return None

def test_teams_endpoint():
    """Test the teams endpoint for roster data"""
    print("\n=== Testing Teams Endpoint ===")
    
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1&season=2024"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Teams: {len(data.get('teams', []))}")
        
        if data.get('teams'):
            team = data['teams'][0]
            print(f"Sample team structure:")
            print(json.dumps(team, indent=2))
            
            # Test roster for this team
            team_id = team['id']
            roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active"
            roster_response = requests.get(roster_url, timeout=10)
            
            if roster_response.status_code == 200:
                roster_data = roster_response.json()
                print(f"\nRoster for {team['name']}:")
                print(f"Total Players: {len(roster_data.get('roster', []))}")
                if roster_data.get('roster'):
                    print(f"Sample player structure:")
                    print(json.dumps(roster_data['roster'][0], indent=2))
        
        return data
        
    except requests.RequestException as e:
        print(f"Error fetching teams: {e}")
        return None

def test_game_boxscore():
    """Test boxscore endpoint for lineup data"""
    print("\n=== Testing Boxscore Endpoint ===")
    
    # First get a recent game ID
    schedule_url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2024-10-01&endDate=2024-10-31"
    
    try:
        schedule_response = requests.get(schedule_url, timeout=10)
        schedule_response.raise_for_status()
        schedule_data = schedule_response.json()
        
        # Find a completed game
        game_id = None
        for date_info in schedule_data.get('dates', []):
            for game in date_info.get('games', []):
                if game.get('status', {}).get('statusCode') == 'F':  # Final
                    game_id = game['gamePk']
                    break
            if game_id:
                break
        
        if game_id:
            boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
            response = requests.get(boxscore_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            print(f"Boxscore for Game ID: {game_id}")
            print(f"Status Code: {response.status_code}")
            
            # Show structure of teams data
            if 'teams' in data:
                print("Teams structure available")
                for team_type in ['away', 'home']:
                    if team_type in data['teams']:
                        team_data = data['teams'][team_type]
                        print(f"\n{team_type.capitalize()} team structure keys:")
                        print(list(team_data.keys()))
                        
                        if 'players' in team_data:
                            players = team_data['players']
                            print(f"Number of players: {len(players)}")
                            if players:
                                player_id = list(players.keys())[0]
                                print(f"Sample player data:")
                                print(json.dumps(players[player_id], indent=2)[:500] + "...")
            
            return data
        else:
            print("No completed games found in recent data")
            return None
            
    except requests.RequestException as e:
        print(f"Error fetching boxscore: {e}")
        return None

if __name__ == "__main__":
    print("MLB Stats API Testing")
    print("=" * 50)
    
    schedule_data = test_schedule_endpoint()
    teams_data = test_teams_endpoint()
    boxscore_data = test_game_boxscore()
    
    print("\n" + "=" * 50)
    print("API Testing Complete!")