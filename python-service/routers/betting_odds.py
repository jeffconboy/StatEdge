"""
Betting Odds Router
==================

Tank01 MLB betting odds integration for StatEdge FastAPI application.
"""

from fastapi import APIRouter, HTTPException, Query
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Tank01 API configuration
TANK01_API_KEY = "72b26ae8f2msh35f1fcb1609a6afp1bac84jsn1fbbe23c2838"
TANK01_BASE_URL = "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
TANK01_HEADERS = {
    "X-RapidAPI-Key": TANK01_API_KEY,
    "X-RapidAPI-Host": "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
}

def get_tank01_data(endpoint: str, params: dict = None) -> Optional[Dict]:
    """Get data from Tank01 API"""
    try:
        url = f"{TANK01_BASE_URL}{endpoint}"
        response = requests.get(url, headers=TANK01_HEADERS, params=params, timeout=10)
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

@router.get('/live',
           summary="Get Live MLB Betting Odds",
           description="Retrieve current live MLB betting odds including moneyline, spreads, and totals",
           response_description="Live betting odds for all MLB games",
           tags=["Betting Odds"])
async def get_live_mlb_odds():
    """
    ## Live MLB Betting Odds
    
    Get real-time betting odds for all MLB games including:
    - **Moneyline**: Win/loss odds for each team
    - **Spreads**: Point spread betting lines  
    - **Totals**: Over/under run totals
    
    ### Data Updates
    - Updated every minute during live games
    - Includes pre-game and in-play odds
    - Coverage from major sportsbooks
    
    ### Response Format
    ```json
    {
        "success": true,
        "data": [
            {
                "game_id": "20250726_BOS@NYY",
                "home_team": "NYY",
                "away_team": "BOS", 
                "game_time": "7:05p",
                "odds": {
                    "moneyline": {"home": "-150", "away": "+130"},
                    "spread": {"home": {"line": "-1.5", "odds": "+110"}},
                    "total": {"over": {"line": "8.5", "odds": "-110"}}
                }
            }
        ],
        "count": 15,
        "timestamp": "2025-07-26T19:30:00Z"
    }
    ```
    """
    try:
        logger.info("🎯 Getting live MLB betting odds...")
        
        # Get live betting odds
        odds_data = get_tank01_data('/getMLBBettingOdds')
        
        if not odds_data:
            return {
                'success': False,
                'error': 'Failed to fetch live betting odds',
                'data': []
            }
        
        # Format the response
        formatted_odds = []
        
        # Check if odds_data is a list or dict
        if isinstance(odds_data, list):
            games_with_odds = odds_data
        elif isinstance(odds_data, dict) and 'games' in odds_data:
            games_with_odds = odds_data['games']
        else:
            games_with_odds = [odds_data] if odds_data else []
        
        for game in games_with_odds:
            if isinstance(game, dict):
                formatted_game = {
                    'game_id': game.get('gameID', ''),
                    'home_team': game.get('home', game.get('teamIDHome', '')),
                    'away_team': game.get('away', game.get('teamIDAway', '')),
                    'game_time': game.get('gameTime', ''),
                    'game_date': game.get('gameDate', ''),
                    'odds': {
                        'moneyline': {
                            'home': game.get('homeML', ''),
                            'away': game.get('awayML', '')
                        },
                        'spread': {
                            'home': {
                                'line': game.get('homeSpread', ''),
                                'odds': game.get('homeSpreadOdds', '')
                            },
                            'away': {
                                'line': game.get('awaySpread', ''),
                                'odds': game.get('awaySpreadOdds', '')
                            }
                        },
                        'total': {
                            'over': {
                                'line': game.get('totalOver', ''),
                                'odds': game.get('totalOverOdds', '')
                            },
                            'under': {
                                'line': game.get('totalUnder', ''),
                                'odds': game.get('totalUnderOdds', '')
                            }
                        }
                    },
                    'last_updated': datetime.now().isoformat()
                }
                formatted_odds.append(formatted_game)
        
        logger.info(f"✅ Retrieved odds for {len(formatted_odds)} games")
        
        return {
            'success': True,
            'data': formatted_odds,
            'count': len(formatted_odds),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting live MLB odds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get live odds: {str(e)}")

@router.get('/games/today',
           summary="Get Today's MLB Games",
           description="Retrieve today's MLB games with schedule and betting information",
           response_description="Today's MLB games with times and teams",
           tags=["Betting Odds"])
async def get_mlb_games_today():
    """
    ## Today's MLB Games
    
    Get all MLB games scheduled for today including:
    - **Game Schedule**: Times and matchups
    - **Team Information**: Home/away teams
    - **Game Status**: Pre-game, live, completed
    - **Probable Pitchers**: Starting lineups
    
    ### Response Format
    ```json
    {
        "success": true,
        "data": [
            {
                "game_id": "20250726_BOS@NYY",
                "home_team": "NYY",
                "away_team": "BOS",
                "game_time": "7:05p",
                "game_status": "scheduled",
                "probable_pitchers": {
                    "home": "Gerrit Cole",
                    "away": "Garrett Whitlock"
                }
            }
        ],
        "count": 15,
        "date": "20250726"
    }
    ```
    """
    try:
        logger.info("📅 Getting today's MLB games...")
        
        # Get today's date
        today = datetime.now().strftime("%Y%m%d")
        
        # Get games for today
        games_data = get_tank01_data('/getMLBGamesForDate', {'gameDate': today})
        
        if not games_data:
            return {
                'success': False,
                'error': 'Failed to fetch today\'s games',
                'data': []
            }
        
        # Format the games data
        formatted_games = []
        
        games_list = games_data if isinstance(games_data, list) else [games_data]
        
        for game in games_list:
            if isinstance(game, dict):
                formatted_game = {
                    'game_id': game.get('gameID', ''),
                    'home_team': game.get('home', ''),
                    'away_team': game.get('away', ''),
                    'game_time': game.get('gameTime', ''),
                    'game_date': game.get('gameDate', ''),
                    'game_type': game.get('gameType', ''),
                    'home_score': game.get('homeScore', ''),
                    'away_score': game.get('awayScore', ''),
                    'inning': game.get('currentInning', ''),
                    'game_status': game.get('gameStatus', ''),
                    'probable_pitchers': {
                        'home': game.get('homeProbablePitcher', ''),
                        'away': game.get('awayProbablePitcher', '')
                    }
                }
                formatted_games.append(formatted_game)
        
        logger.info(f"✅ Retrieved {len(formatted_games)} games for today")
        
        return {
            'success': True,
            'data': formatted_games,
            'count': len(formatted_games),
            'date': today,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting today's MLB games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get games: {str(e)}")

@router.get('/game/{game_id}',
           summary="Get Game Specific Odds",
           description="Get detailed betting odds for a specific MLB game",
           response_description="Detailed betting odds for the specified game",
           tags=["Betting Odds"])
async def get_game_odds(game_id: str):
    """
    ## Game Specific Betting Odds
    
    Get detailed betting odds for a specific MLB game by game ID.
    
    ### Parameters
    - **game_id**: Game identifier (e.g., "20250726_BOS@NYY")
    
    ### Response Format
    ```json
    {
        "success": true,
        "data": {
            "game_id": "20250726_BOS@NYY",
            "home_team": "NYY",
            "away_team": "BOS",
            "odds": {
                "moneyline": {"home": "-150", "away": "+130"},
                "spread": {"home": {"line": "-1.5", "odds": "+110"}},
                "total": {"over": {"line": "8.5", "odds": "-110"}}
            },
            "last_updated": "2025-07-26T19:30:00Z"
        }
    }
    ```
    """
    try:
        logger.info(f"🎯 Getting odds for game: {game_id}")
        
        # Get all live odds and filter for specific game
        odds_data = get_tank01_data('/getMLBBettingOdds')
        
        if not odds_data:
            raise HTTPException(status_code=500, detail="Failed to fetch betting odds")
        
        # Find the specific game
        games_list = odds_data if isinstance(odds_data, list) else [odds_data]
        
        for game in games_list:
            if isinstance(game, dict) and game.get('gameID') == game_id:
                formatted_game = {
                    'game_id': game.get('gameID', ''),
                    'home_team': game.get('home', game.get('teamIDHome', '')),
                    'away_team': game.get('away', game.get('teamIDAway', '')),
                    'game_time': game.get('gameTime', ''),
                    'odds': {
                        'moneyline': {
                            'home': game.get('homeML', ''),
                            'away': game.get('awayML', '')
                        },
                        'spread': {
                            'home': {
                                'line': game.get('homeSpread', ''),
                                'odds': game.get('homeSpreadOdds', '')
                            },
                            'away': {
                                'line': game.get('awaySpread', ''),
                                'odds': game.get('awaySpreadOdds', '')
                            }
                        },
                        'total': {
                            'over': {
                                'line': game.get('totalOver', ''),
                                'odds': game.get('totalOverOdds', '')
                            },
                            'under': {
                                'line': game.get('totalUnder', ''),
                                'odds': game.get('totalUnderOdds', '')
                            }
                        }
                    },
                    'last_updated': datetime.now().isoformat()
                }
                
                return {
                    'success': True,
                    'data': formatted_game,
                    'timestamp': datetime.now().isoformat()
                }
        
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting odds for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get game odds: {str(e)}")

@router.get('/teams',
           summary="Get MLB Teams",
           description="Get list of all MLB teams with basic information",
           response_description="List of MLB teams",
           tags=["Betting Odds"])
async def get_mlb_teams():
    """
    ## MLB Teams
    
    Get comprehensive list of all MLB teams with basic information.
    
    ### Response Format
    ```json
    {
        "success": true,
        "data": [
            {
                "team_id": "NYY",
                "team_name": "New York Yankees",
                "division": "AL East",
                "league": "American League"
            }
        ]
    }
    ```
    """
    try:
        logger.info("🏟️ Getting MLB teams...")
        
        teams_data = get_tank01_data('/getMLBTeams')
        
        if not teams_data:
            raise HTTPException(status_code=500, detail="Failed to fetch MLB teams")
        
        return {
            'success': True,
            'data': teams_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting MLB teams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get teams: {str(e)}")

@router.get('/test',
           summary="Test Tank01 API Connection",
           description="Test the Tank01 API connection and available endpoints",
           response_description="API test results and available endpoints",
           tags=["Betting Odds"])
async def test_tank01_connection():
    """
    ## Tank01 API Test
    
    Test the Tank01 API connection and check which endpoints are available.
    Useful for debugging and verifying API access.
    
    ### Response Format
    ```json
    {
        "success": true,
        "api_status": "connected",
        "available_endpoints": [
            "/getMLBBettingOdds",
            "/getMLBGamesForDate",
            "/getMLBTeams"
        ],
        "sample_data": {...}
    }
    ```
    """
    try:
        logger.info("🔍 Testing Tank01 API connection...")
        
        # Test available endpoints
        endpoints = [
            "/getMLBBettingOdds",
            "/getMLBGamesForDate", 
            "/getMLBPlayerList",
            "/getMLBTeams"
        ]
        
        working_endpoints = []
        
        for endpoint in endpoints:
            try:
                url = f"{TANK01_BASE_URL}{endpoint}"
                params = {'gameDate': datetime.now().strftime("%Y%m%d")} if 'Date' in endpoint else None
                response = requests.get(url, headers=TANK01_HEADERS, params=params, timeout=5)
                
                if response.status_code == 200:
                    working_endpoints.append(endpoint)
                    
            except Exception:
                continue
        
        # Get sample data
        sample_data = None
        if "/getMLBGamesForDate" in working_endpoints:
            sample_data = get_tank01_data('/getMLBGamesForDate', {
                'gameDate': datetime.now().strftime("%Y%m%d")
            })
        
        return {
            'success': True,
            'api_status': 'connected' if working_endpoints else 'disconnected',
            'available_endpoints': working_endpoints,
            'sample_data': sample_data[:1] if isinstance(sample_data, list) and sample_data else sample_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error testing Tank01 API: {e}")
        return {
            'success': False,
            'api_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }