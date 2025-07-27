"""
Tank01 API Service
==================

Service class for interacting with Tank01 MLB betting odds API.
"""

import requests
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class Tank01Service:
    """Tank01 MLB API client for betting odds and game data"""
    
    def __init__(self):
        self.api_key = os.getenv("TANK01_API_KEY", "72b26ae8f2msh35f1fcb1609a6afp1bac84jsn1fbbe23c2838")
        self.base_url = "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
        }
    
    async def _make_request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make async request to Tank01 API"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, headers=self.headers, params=params, timeout=10)
            )
            
            response.raise_for_status()
            
            data = response.json()
            if data.get('statusCode') == 200:
                return data.get('body', {})
            else:
                logger.error(f"Tank01 API error: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Tank01 data from {endpoint}: {e}")
            return None
    
    async def get_betting_odds(self) -> Optional[List[Dict]]:
        """Get current MLB betting odds"""
        try:
            logger.info("🎯 Getting MLB betting odds from Tank01...")
            
            data = await self._make_request('/getMLBBettingOdds')
            
            if not data:
                return None
            
            # Normalize response format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'games' in data:
                return data['games']
            else:
                return [data] if data else []
                
        except Exception as e:
            logger.error(f"Error getting betting odds: {e}")
            return None
    
    async def get_games_for_date(self, game_date: str) -> Optional[List[Dict]]:
        """Get MLB games for a specific date (YYYYMMDD format)"""
        try:
            logger.info(f"📅 Getting MLB games for {game_date}...")
            
            data = await self._make_request('/getMLBGamesForDate', {'gameDate': game_date})
            
            if not data:
                return None
            
            # Normalize response format
            if isinstance(data, list):
                return data
            else:
                return [data] if data else []
                
        except Exception as e:
            logger.error(f"Error getting games for date {game_date}: {e}")
            return None
    
    async def get_todays_games(self) -> Optional[List[Dict]]:
        """Get today's MLB games"""
        today = datetime.now().strftime("%Y%m%d")
        return await self.get_games_for_date(today)
    
    async def get_mlb_teams(self) -> Optional[List[Dict]]:
        """Get MLB teams information"""
        try:
            logger.info("🏟️ Getting MLB teams...")
            
            data = await self._make_request('/getMLBTeams')
            
            if not data:
                return None
            
            return data if isinstance(data, list) else [data]
                
        except Exception as e:
            logger.error(f"Error getting MLB teams: {e}")
            return None
    
    async def get_player_list(self) -> Optional[List[Dict]]:
        """Get MLB player list"""
        try:
            logger.info("👥 Getting MLB player list...")
            
            data = await self._make_request('/getMLBPlayerList')
            
            if not data:
                return None
            
            return data if isinstance(data, list) else [data]
                
        except Exception as e:
            logger.error(f"Error getting player list: {e}")
            return None
    
    async def get_game_odds(self, game_id: str) -> Optional[Dict]:
        """Get odds for a specific game"""
        try:
            # Get all odds and filter for specific game
            all_odds = await self.get_betting_odds()
            
            if not all_odds:
                return None
            
            for game in all_odds:
                if game.get('gameID') == game_id:
                    return game
            
            return None
                
        except Exception as e:
            logger.error(f"Error getting odds for game {game_id}: {e}")
            return None
    
    async def test_connection(self) -> Dict[str, any]:
        """Test Tank01 API connection"""
        try:
            logger.info("🔍 Testing Tank01 API connection...")
            
            # Test different endpoints
            endpoints = [
                "/getMLBBettingOdds",
                "/getMLBGamesForDate", 
                "/getMLBTeams"
            ]
            
            working_endpoints = []
            
            for endpoint in endpoints:
                try:
                    params = {'gameDate': datetime.now().strftime("%Y%m%d")} if 'Date' in endpoint else None
                    data = await self._make_request(endpoint, params)
                    
                    if data is not None:
                        working_endpoints.append(endpoint)
                        
                except Exception:
                    continue
            
            # Get sample data
            sample_data = None
            if "/getMLBGamesForDate" in working_endpoints:
                sample_data = await self.get_todays_games()
                if sample_data:
                    sample_data = sample_data[:1]  # Just first game as sample
            
            return {
                'success': True if working_endpoints else False,
                'api_status': 'connected' if working_endpoints else 'disconnected',
                'available_endpoints': working_endpoints,
                'sample_data': sample_data,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Error testing Tank01 API: {e}")
            return {
                'success': False,
                'api_status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }