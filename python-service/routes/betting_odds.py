"""
Betting Odds API Routes
======================

Tank01 MLB betting odds integration for StatEdge.
"""

from flask import Blueprint, jsonify, request
import requests
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Create blueprint
betting_odds_bp = Blueprint('betting_odds', __name__)

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

@betting_odds_bp.route('/mlb/odds/live', methods=['GET'])
def get_live_mlb_odds():
    """Get live MLB betting odds"""
    try:
        logger.info("🎯 Getting live MLB betting odds...")
        
        # Get live betting odds
        odds_data = get_tank01_data('/getMLBBettingOdds')
        
        if not odds_data:
            return jsonify({
                'error': 'Failed to fetch live betting odds',
                'data': []
            }), 500
        
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
        
        return jsonify({
            'success': True,
            'data': formatted_odds,
            'count': len(formatted_odds),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting live MLB odds: {e}")
        return jsonify({
            'error': str(e),
            'data': []
        }), 500

@betting_odds_bp.route('/mlb/games/today', methods=['GET'])
def get_mlb_games_today():
    """Get today's MLB games with betting info"""
    try:
        logger.info("📅 Getting today's MLB games...")
        
        # Get today's date
        today = datetime.now().strftime("%Y%m%d")
        
        # Get games for today
        games_data = get_tank01_data('/getMLBGamesForDate', {'gameDate': today})
        
        if not games_data:
            return jsonify({
                'error': 'Failed to fetch today\'s games',
                'data': []
            }), 500
        
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
        
        return jsonify({
            'success': True,
            'data': formatted_games,
            'count': len(formatted_games),
            'date': today,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting today's MLB games: {e}")
        return jsonify({
            'error': str(e),
            'data': []
        }), 500

@betting_odds_bp.route('/mlb/odds/game/<game_id>', methods=['GET'])
def get_game_odds(game_id):
    """Get betting odds for a specific game"""
    try:
        logger.info(f"🎯 Getting odds for game: {game_id}")
        
        # Get all live odds and filter for specific game
        odds_data = get_tank01_data('/getMLBBettingOdds')
        
        if not odds_data:
            return jsonify({
                'error': 'Failed to fetch betting odds',
                'data': {}
            }), 500
        
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
                
                return jsonify({
                    'success': True,
                    'data': formatted_game,
                    'timestamp': datetime.now().isoformat()
                })
        
        return jsonify({
            'error': f'Game {game_id} not found',
            'data': {}
        }), 404
        
    except Exception as e:
        logger.error(f"❌ Error getting odds for game {game_id}: {e}")
        return jsonify({
            'error': str(e),
            'data': {}
        }), 500

@betting_odds_bp.route('/mlb/teams', methods=['GET'])
def get_mlb_teams():
    """Get MLB teams data"""
    try:
        logger.info("🏟️ Getting MLB teams...")
        
        teams_data = get_tank01_data('/getMLBTeams')
        
        if not teams_data:
            return jsonify({
                'error': 'Failed to fetch MLB teams',
                'data': []
            }), 500
        
        return jsonify({
            'success': True,
            'data': teams_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting MLB teams: {e}")
        return jsonify({
            'error': str(e),
            'data': []
        }), 500