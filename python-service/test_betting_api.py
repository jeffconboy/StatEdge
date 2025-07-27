#!/usr/bin/env python3
"""
Test Tank01 Betting API Integration
==================================

Test the Tank01 betting odds API endpoints directly.
"""

import requests
import json
from datetime import datetime

# Tank01 API configuration
TANK01_API_KEY = "72b26ae8f2msh35f1fcb1609a6afp1bac84jsn1fbbe23c2838"
TANK01_BASE_URL = "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
TANK01_HEADERS = {
    "X-RapidAPI-Key": TANK01_API_KEY,
    "X-RapidAPI-Host": "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
}

def test_betting_odds():
    """Test getting MLB betting odds"""
    print("🎯 Testing MLB Betting Odds...")
    
    try:
        url = f"{TANK01_BASE_URL}/getMLBBettingOdds"
        response = requests.get(url, headers=TANK01_HEADERS, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Betting odds retrieved successfully!")
            print(f"Response structure: {list(data.keys())}")
            
            if 'body' in data and data['body']:
                games = data['body']
                if isinstance(games, list):
                    print(f"📊 Found {len(games)} games with odds")
                    
                    # Show sample game
                    if games:
                        sample_game = games[0]
                        print("\n🏆 Sample Game Odds:")
                        print(f"Game ID: {sample_game.get('gameID', 'N/A')}")
                        print(f"Teams: {sample_game.get('away', 'N/A')} @ {sample_game.get('home', 'N/A')}")
                        print(f"Time: {sample_game.get('gameTime', 'N/A')}")
                        print(f"Home ML: {sample_game.get('homeML', 'N/A')}")
                        print(f"Away ML: {sample_game.get('awayML', 'N/A')}")
                        print(f"Home Spread: {sample_game.get('homeSpread', 'N/A')}")
                        print(f"Total Over: {sample_game.get('totalOver', 'N/A')}")
                else:
                    print(f"📊 Odds data type: {type(games)}")
            else:
                print("⚠️ No games found in response")
                
        else:
            print(f"❌ Failed to get betting odds: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing betting odds: {e}")

def test_todays_games():
    """Test getting today's games"""
    print("\n📅 Testing Today's Games...")
    
    try:
        today = datetime.now().strftime("%Y%m%d")
        url = f"{TANK01_BASE_URL}/getMLBGamesForDate"
        params = {"gameDate": today}
        
        response = requests.get(url, headers=TANK01_HEADERS, params=params, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Today's games retrieved successfully!")
            
            if 'body' in data and data['body']:
                games = data['body']
                if isinstance(games, list):
                    print(f"⚾ Found {len(games)} games today")
                    
                    # Show sample games
                    for i, game in enumerate(games[:3]):  # Show first 3 games
                        print(f"\n🏟️ Game {i+1}:")
                        print(f"  {game.get('away', 'N/A')} @ {game.get('home', 'N/A')}")
                        print(f"  Time: {game.get('gameTime', 'N/A')}")
                        print(f"  Status: {game.get('gameStatus', 'N/A')}")
                else:
                    print(f"⚾ Single game data: {type(games)}")
            else:
                print("⚠️ No games found for today")
                
        else:
            print(f"❌ Failed to get today's games: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing today's games: {e}")

def test_teams():
    """Test getting MLB teams"""
    print("\n🏟️ Testing MLB Teams...")
    
    try:
        url = f"{TANK01_BASE_URL}/getMLBTeams"
        response = requests.get(url, headers=TANK01_HEADERS, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ MLB teams retrieved successfully!")
            
            if 'body' in data and data['body']:
                teams = data['body']
                print(f"🏟️ Found {len(teams)} teams" if isinstance(teams, list) else f"Teams data type: {type(teams)}")
                
                # Show sample teams
                if isinstance(teams, list) and teams:
                    for i, team in enumerate(teams[:5]):  # Show first 5 teams
                        print(f"  {i+1}. {team}")
            else:
                print("⚠️ No teams found")
                
        else:
            print(f"❌ Failed to get teams: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing teams: {e}")

if __name__ == "__main__":
    print("🏁 Tank01 MLB Betting API Test")
    print("=" * 50)
    
    test_betting_odds()
    test_todays_games() 
    test_teams()
    
    print("\n🏁 Tank01 API test complete!")