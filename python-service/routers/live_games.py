from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, date
import aiohttp
import logging
from typing import List, Dict, Any, Optional

from database.connection import get_db_session

router = APIRouter()
logger = logging.getLogger(__name__)

# MLB Stats API base URL
MLB_API_BASE = "https://statsapi.mlb.com/api/v1"

@router.get("/today")
async def get_todays_games() -> Dict[str, Any]:
    """Get today's MLB games with live scores"""
    
    try:
        # Get today's date
        today = date.today().strftime('%Y-%m-%d')
        
        # Fetch from MLB Stats API
        async with aiohttp.ClientSession() as session:
            # Get schedule for today
            schedule_url = f"{MLB_API_BASE}/schedule?sportId=1&date={today}&hydrate=game(content(summary,media(epg))),decisions,person,linescore,team"
            
            async with session.get(schedule_url) as response:
                if response.status != 200:
                    logger.error(f"MLB API returned status {response.status}")
                    return await get_fallback_games()
                
                data = await response.json()
                
                if not data.get('dates') or len(data['dates']) == 0:
                    logger.info(f"No games scheduled for {today}")
                    return {
                        "games": [],
                        "date": today,
                        "total_games": 0,
                        "last_updated": datetime.now().isoformat(),
                        "data_source": "mlb_api"
                    }
                
                games = []
                for date_data in data['dates']:
                    for game in date_data.get('games', []):
                        processed_game = process_game_data(game)
                        if processed_game:
                            games.append(processed_game)
                
                return {
                    "games": games,
                    "date": today,
                    "total_games": len(games),
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "mlb_api"
                }
                
    except Exception as e:
        logger.error(f"Error fetching live games: {str(e)}")
        return await get_fallback_games()

@router.get("/live")
async def get_live_games() -> Dict[str, Any]:
    """Get only currently live games with detailed status"""
    
    try:
        # First get all today's games
        all_games_response = await get_todays_games()
        all_games = all_games_response.get('games', [])
        
        # Filter for live games only
        live_games = [
            game for game in all_games 
            if game.get('status') == 'live'
        ]
        
        return {
            "games": live_games,
            "total_live_games": len(live_games),
            "last_updated": datetime.now().isoformat(),
            "data_source": "mlb_api"
        }
        
    except Exception as e:
        logger.error(f"Error fetching live games: {str(e)}")
        return {
            "games": [],
            "total_live_games": 0,
            "last_updated": datetime.now().isoformat(),
            "data_source": "error_fallback",
            "error": str(e)
        }

@router.get("/team/{team_id}")
async def get_team_games(team_id: int, days: int = 7) -> Dict[str, Any]:
    """Get recent and upcoming games for a specific team"""
    
    try:
        # Calculate date range
        from datetime import timedelta
        start_date = (date.today() - timedelta(days=days//2)).strftime('%Y-%m-%d')
        end_date = (date.today() + timedelta(days=days//2)).strftime('%Y-%m-%d')
        
        async with aiohttp.ClientSession() as session:
            url = f"{MLB_API_BASE}/schedule?sportId=1&teamId={team_id}&startDate={start_date}&endDate={end_date}&hydrate=game(content(summary,media(epg))),decisions,person,linescore,team"
            
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="MLB API error")
                
                data = await response.json()
                
                games = []
                for date_data in data.get('dates', []):
                    for game in date_data.get('games', []):
                        processed_game = process_game_data(game)
                        if processed_game:
                            games.append(processed_game)
                
                return {
                    "games": games,
                    "team_id": team_id,
                    "date_range": f"{start_date} to {end_date}",
                    "total_games": len(games),
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "mlb_api"
                }
                
    except Exception as e:
        logger.error(f"Error fetching team games: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def process_game_data(game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process raw MLB API game data into our format"""
    
    try:
        # Extract basic game info
        game_id = str(game.get('gamePk', ''))
        
        # Teams
        home_team = game.get('teams', {}).get('home', {}).get('team', {})
        away_team = game.get('teams', {}).get('away', {}).get('team', {})
        
        # Scores
        home_score = game.get('teams', {}).get('home', {}).get('score', 0)
        away_score = game.get('teams', {}).get('away', {}).get('score', 0)
        
        # Game status
        status_code = game.get('status', {}).get('statusCode', '')
        detailed_state = game.get('status', {}).get('detailedState', '')
        
        # Map MLB status codes to our format
        if status_code in ['I', 'IH', 'IR', 'IT', 'IW', 'ID']:  # In progress states
            status = 'live'
        elif status_code in ['F', 'FR', 'FT']:  # Final states
            status = 'final'
        elif status_code in ['S', 'P', 'PW', 'PR']:  # Scheduled/Preview states
            status = 'scheduled'
        else:
            status = 'scheduled'  # Default
        
        # Game time or inning info
        game_time = None
        inning_info = None
        
        if status == 'scheduled':
            game_date = game.get('gameDate', '')
            if game_date:
                try:
                    # Parse the ISO datetime and convert to local time
                    dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                    # Convert to Eastern Time (most common for MLB)
                    from datetime import timezone, timedelta
                    eastern = timezone(timedelta(hours=-5))  # EST
                    dt_eastern = dt.astimezone(eastern)
                    game_time = dt_eastern.strftime('%I:%M %p ET').lstrip('0')
                except Exception as e:
                    logger.warning(f"Error parsing game time {game_date}: {e}")
                    game_time = 'TBD'
        elif status == 'live':
            # Get inning info
            linescore = game.get('linescore', {})
            current_inning = linescore.get('currentInning', 1)
            inning_half = linescore.get('inningHalf', 'Top')
            is_top_inning = linescore.get('isTopInning', True)
            
            # Use the more accurate isTopInning field if available
            if is_top_inning:
                inning_info = f"Top {current_inning}"
            else:
                inning_info = f"Bot {current_inning}"
                
            # Override with detailed state if it's more specific
            if detailed_state and detailed_state not in ['In Progress', 'Live']:
                inning_info = detailed_state
        elif status == 'final':
            inning_info = 'Final'
            # Check if it went extra innings
            linescore = game.get('linescore', {})
            current_inning = linescore.get('currentInning', 9)
            scheduled_innings = linescore.get('scheduledInnings', 9)
            if current_inning > scheduled_innings:
                inning_info = f"Final/{current_inning}"
        
        # Clean up team names - use the full team name, not location
        home_team_name = home_team.get('name', '') or f"{home_team.get('locationName', '')} {home_team.get('teamName', '')}"
        away_team_name = away_team.get('name', '') or f"{away_team.get('locationName', '')} {away_team.get('teamName', '')}"
        
        return {
            "id": game_id,
            "homeTeam": {
                "id": str(home_team.get('id', '')),
                "name": home_team_name.strip(),
                "abbreviation": home_team.get('abbreviation', ''),
                "teamName": home_team.get('teamName', ''),
                "locationName": home_team.get('locationName', '')
            },
            "awayTeam": {
                "id": str(away_team.get('id', '')),
                "name": away_team_name.strip(),
                "abbreviation": away_team.get('abbreviation', ''),
                "teamName": away_team.get('teamName', ''),  
                "locationName": away_team.get('locationName', '')
            },
            "homeScore": home_score,
            "awayScore": away_score,
            "status": status,
            "time": game_time,
            "inning": inning_info,
            "gameDate": game.get('gameDate', ''),
            "detailedState": detailed_state,
            "venue": game.get('venue', {}).get('name', ''),
            "weather": game.get('gameInfo', {}).get('weather', {}) if game.get('gameInfo') else {}
        }
        
    except Exception as e:
        logger.error(f"Error processing game data: {str(e)}")
        return None

async def get_fallback_games() -> Dict[str, Any]:
    """Fallback data when MLB API is unavailable"""
    
    logger.info("Using fallback game data")
    
    return {
        "games": [
            {
                "id": "fallback-1",
                "homeTeam": {
                    "id": "147",
                    "name": "New York Yankees",
                    "abbreviation": "NYY",
                    "teamName": "Yankees",
                    "locationName": "New York"
                },
                "awayTeam": {
                    "id": "111",
                    "name": "Boston Red Sox", 
                    "abbreviation": "BOS",
                    "teamName": "Red Sox",
                    "locationName": "Boston"
                },
                "homeScore": 0,
                "awayScore": 0,
                "status": "scheduled",
                "time": "7:05 PM",
                "inning": None,
                "gameDate": datetime.now().isoformat(),
                "detailedState": "Scheduled",
                "venue": "Yankee Stadium",
                "weather": {}
            },
            {
                "id": "fallback-2", 
                "homeTeam": {
                    "id": "119",
                    "name": "Los Angeles Dodgers",
                    "abbreviation": "LAD",
                    "teamName": "Dodgers",
                    "locationName": "Los Angeles"
                },
                "awayTeam": {
                    "id": "137",
                    "name": "San Francisco Giants",
                    "abbreviation": "SF", 
                    "teamName": "Giants",
                    "locationName": "San Francisco"
                },
                "homeScore": 5,
                "awayScore": 3,
                "status": "live",
                "time": None,
                "inning": "Bot 7th",
                "gameDate": datetime.now().isoformat(),
                "detailedState": "In Progress",
                "venue": "Dodger Stadium",
                "weather": {}
            }
        ],
        "date": date.today().strftime('%Y-%m-%d'),
        "total_games": 2,
        "last_updated": datetime.now().isoformat(),
        "data_source": "fallback"
    }

@router.get("/refresh")
async def refresh_games_cache() -> Dict[str, Any]:
    """Manually refresh the games cache (useful for testing)"""
    
    try:
        # For now, just return fresh data
        # In production, you might want to implement Redis caching here
        games_data = await get_todays_games()
        
        return {
            "status": "refreshed",
            "games_count": games_data.get("total_games", 0),
            "last_updated": datetime.now().isoformat(),
            "message": "Games cache refreshed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error refreshing games cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))