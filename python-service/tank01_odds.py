#!/usr/bin/env python3
"""
Tank01 MLB Betting Odds Integration
==================================

Integrates Tank01 MLB live betting odds API with StatEdge.
"""

import requests
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Tank01MLB:
    """Tank01 MLB API client for betting odds and live stats"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
        }
    
    def get_mlb_odds(self) -> Optional[Dict]:
        """Get current MLB betting odds"""
        try:
            url = f"{self.base_url}/getNBABettingOdds"  # Check if this endpoint works for MLB too
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Retrieved odds data: {len(data.get('body', []))} games")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get MLB odds: {e}")
            return None
    
    def get_mlb_games_today(self) -> Optional[Dict]:
        """Get today's MLB games with odds"""
        try:
            url = f"{self.base_url}/getMLBGamesForDate"
            params = {
                "gameDate": datetime.now().strftime("%Y%m%d")
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Retrieved today's games: {len(data.get('body', []))} games")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get today's games: {e}")
            return None
    
    def get_mlb_live_odds(self) -> Optional[Dict]:
        """Get live MLB betting odds"""
        try:
            url = f"{self.base_url}/getMLBBettingOdds"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Retrieved live MLB odds")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get live MLB odds: {e}")
            return None
    
    def get_available_endpoints(self) -> List[str]:
        """Test available endpoints"""
        endpoints = [
            "/getMLBBettingOdds",
            "/getMLBGamesForDate", 
            "/getMLBPlayerList",
            "/getMLBTeams",
            "/getMLBGames",
            "/getNBABettingOdds"  # Sometimes APIs share endpoints
        ]
        
        working_endpoints = []
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, headers=self.headers, timeout=5)
                
                if response.status_code == 200:
                    working_endpoints.append(endpoint)
                    logger.info(f"✅ {endpoint} - Working")
                else:
                    logger.warning(f"⚠️  {endpoint} - Status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ {endpoint} - Error: {e}")
        
        return working_endpoints


def test_tank01_api():
    """Test Tank01 API with your key"""
    
    # Your RapidAPI key
    api_key = "72b26ae8f2msh35f1fcb1609a6afp1bac84jsn1fbbe23c2838"
    
    logger.info("🏁 Testing Tank01 MLB API...")
    
    # Initialize client
    tank01 = Tank01MLB(api_key)
    
    # Test available endpoints
    logger.info("🔍 Checking available endpoints...")
    working_endpoints = tank01.get_available_endpoints()
    
    if working_endpoints:
        logger.info(f"📋 Working endpoints: {working_endpoints}")
        
        # Test getting MLB odds
        logger.info("📊 Testing MLB odds...")
        odds_data = tank01.get_mlb_live_odds()
        
        if odds_data:
            logger.info("🎯 Sample odds data:")
            print(json.dumps(odds_data, indent=2)[:500] + "...")
        
        # Test getting today's games
        logger.info("📅 Testing today's games...")
        games_data = tank01.get_mlb_games_today()
        
        if games_data:
            logger.info("⚾ Sample games data:")
            print(json.dumps(games_data, indent=2)[:500] + "...")
            
    else:
        logger.error("❌ No working endpoints found")
    
    logger.info("🏁 Tank01 API test complete!")


if __name__ == "__main__":
    test_tank01_api()