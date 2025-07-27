from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
from typing import List, Dict, Any

from database.connection import get_db_session
from models.requests import PlayerSearchRequest, PlayerStatsRequest, PlayerStatsResponse

router = APIRouter()

@router.post("/search")
async def search_players(
    request: PlayerSearchRequest,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Search for players by name"""
    
    try:
        query = text("""
            SELECT id, player_id, full_name, team_id, position_name, status_code, NULL as bio_data
            FROM mlb_players 
            WHERE full_name ILIKE :search_term
            ORDER BY 
                CASE WHEN full_name ILIKE :exact_term THEN 1 ELSE 2 END,
                full_name
            LIMIT :limit
        """)
        
        result = await session.execute(query, {
            "search_term": f"%{request.query}%",
            "exact_term": f"{request.query}%",
            "limit": request.limit
        })
        
        players = []
        for row in result.fetchall():
            players.append({
                "id": row[0],
                "mlb_id": row[1],
                "name": row[2],
                "team": row[3],
                "position": row[4],
                "active": row[5],
                "bio": json.loads(row[6]) if row[6] else {}
            })
        
        return {"players": players}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching players: {str(e)}")

@router.get("/{player_id}/stats")
async def get_player_stats(
    player_id: int,
    stat_types: str = "batting,pitching,statcast",
    season: int = None,
    days_back: int = 365,
    session: AsyncSession = Depends(get_db_session)
) -> PlayerStatsResponse:
    """Get comprehensive player statistics"""
    
    try:
        # Get player info including AI portrait  
        player_query = text("""
            SELECT id, player_id, full_name, team_id, position_name, NULL as bio_data, NULL as ai_portrait_url, NULL as ai_portrait_no_bg_url
            FROM mlb_players WHERE id = :player_id
        """)
        
        result = await session.execute(player_query, {"player_id": player_id})
        player_row = result.fetchone()
        
        if not player_row:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_info = {
            "id": player_row[0],
            "mlb_id": player_row[1],
            "name": player_row[2],
            "team": player_row[3],
            "position": player_row[4],
            "bio": json.loads(player_row[5]) if player_row[5] else {},
            "ai_portrait_url": player_row[6],
            "ai_portrait_no_bg_url": player_row[7]
        }
        
        response_data = {"player_info": player_info}
        requested_types = stat_types.split(",")
        
        # Get Statcast data with recent HR performance
        if "statcast" in requested_types:
            statcast_query = text("""
                SELECT game_date, events, launch_speed, launch_angle, hit_distance_sc
                FROM statcast 
                WHERE batter = :mlb_id 
                AND game_date >= CURRENT_DATE - INTERVAL '%s days'
                AND events IS NOT NULL
                ORDER BY game_date DESC
                LIMIT 100
            """ % days_back)
            
            result = await session.execute(statcast_query, {"mlb_id": player_row[1]})
            statcast_data = []
            hr_by_game = {}
            
            for row in result.fetchall():
                game_date = row[0]
                events = row[1]
                
                # Track HRs by game date
                if game_date:
                    date_key = game_date.strftime('%Y-%m-%d')
                    if date_key not in hr_by_game:
                        hr_by_game[date_key] = 0
                    if events == 'home_run':
                        hr_by_game[date_key] += 1
                
                statcast_data.append({
                    "game_date": game_date.isoformat() if game_date else None,
                    "events": events,
                    "launch_speed": row[2],
                    "launch_angle": row[3], 
                    "hit_distance": row[4]
                })
            
            response_data["statcast_data"] = statcast_data
            response_data["recent_hr_games"] = hr_by_game
        
        # Get FanGraphs batting data - using actual database columns
        if "batting" in requested_types:
            batting_query = text("""
                SELECT "IDfg", "Season", "Name", "Team", "AVG", "HR", "RBI", "OBP", "SLG", "WAR", "wOBA", "ISO", "BABIP"
                FROM fangraphs_batting 
                WHERE "IDfg" = :player_id
                ORDER BY "Season" DESC
            """)
            
            result = await session.execute(batting_query, {"player_id": player_row[1]})  # Use mlb_id
            batting_data = []
            
            for row in result.fetchall():
                batting_data.append({
                    "player_id": row[0],
                    "season": row[1], 
                    "name": row[2],
                    "team": row[3],
                    "stats": {
                        "avg": float(row[4]) if row[4] else 0,
                        "hr": int(row[5]) if row[5] else 0,
                        "rbi": int(row[6]) if row[6] else 0,
                        "obp": float(row[7]) if row[7] else 0,
                        "slg": float(row[8]) if row[8] else 0,
                        "war": float(row[9]) if row[9] else 0,
                        "woba": float(row[10]) if row[10] else 0,
                        "iso": float(row[11]) if row[11] else 0,
                        "babip": float(row[12]) if row[12] else 0
                    }
                })
            
            response_data["fangraphs_batting"] = batting_data
        
        # Get FanGraphs pitching data - using actual database columns
        if "pitching" in requested_types:
            pitching_query = text("""
                SELECT "IDfg", "Season", "Name", "Team", "ERA", "W", "L", "SO", "WAR", "IP", "WHIP", "HR"
                FROM fangraphs_pitching 
                WHERE "IDfg" = :player_id
                ORDER BY "Season" DESC
            """)
            
            result = await session.execute(pitching_query, {"player_id": player_row[1]})  # Use mlb_id
            pitching_data = []
            
            for row in result.fetchall():
                pitching_data.append({
                    "player_id": row[0],
                    "season": row[1],
                    "name": row[2], 
                    "team": row[3],
                    "stats": {
                        "era": float(row[4]) if row[4] else 0,
                        "wins": int(row[5]) if row[5] else 0,
                        "losses": int(row[6]) if row[6] else 0,
                        "strikeouts": int(row[7]) if row[7] else 0,
                        "war": float(row[8]) if row[8] else 0,
                        "innings_pitched": float(row[9]) if row[9] else 0,
                        "whip": float(row[10]) if row[10] else 0,
                        "home_runs_allowed": int(row[11]) if row[11] else 0
                    }
                })
            
            response_data["fangraphs_pitching"] = pitching_data
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting player stats: {str(e)}")

@router.get("/{player_id}/summary")
async def get_player_summary(
    player_id: int,
    session: AsyncSession = Depends(get_db_session)
) -> PlayerStatsResponse:
    """Get player summary with portrait info"""
    
    try:
        # Get player info including AI portrait  
        player_query = text("""
            SELECT id, player_id, full_name, team_id, position_name, NULL as bio_data, NULL as ai_portrait_url, NULL as ai_portrait_no_bg_url
            FROM mlb_players WHERE id = :player_id
        """)
        
        result = await session.execute(player_query, {"player_id": player_id})
        player_row = result.fetchone()
        
        if not player_row:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_info = {
            "id": player_row[0],
            "mlb_id": player_row[1],
            "name": player_row[2],
            "team": player_row[3],
            "position": player_row[4],
            "bio": json.loads(player_row[5]) if player_row[5] else {},
            "ai_portrait_url": player_row[6],
            "ai_portrait_no_bg_url": player_row[7]
        }
        
        return {"player_info": player_info}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting player summary: {str(e)}")

@router.post("/bulk-stats")
async def get_bulk_player_stats(
    player_ids: List[int],
    stat_types: List[str] = ["batting", "statcast"],
    session: AsyncSession = Depends(get_db_session)
) -> Dict[int, Dict[str, Any]]:
    """Get stats for multiple players at once"""
    
    try:
        results = {}
        
        for player_id in player_ids[:10]:  # Limit to 10 players
            try:
                stats = await get_player_stats(
                    player_id=player_id,
                    stat_types=",".join(stat_types),
                    session=session
                )
                results[player_id] = stats.dict()
            except:
                results[player_id] = {"error": "Player not found"}
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bulk stats: {str(e)}")

@router.get("/trending")
async def get_trending_players(
    limit: int = 10,  
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Get trending players with real stats from recent games"""
    
    try:
        # Get trending players - JOIN with mlb_players for correct names and positions
        query = text("""
            WITH recent_stats AS (
                SELECT 
                    s.batter as mlb_id,
                    mp.full_name as name,
                    mp.position_name as position,
                    COUNT(*) as plate_appearances,
                    COUNT(CASE WHEN s.events IN ('single', 'double', 'triple', 'home_run', 'field_out', 'grounded_into_double_play', 'force_out', 'fielders_choice', 'strikeout') THEN 1 END) as at_bats,
                    COUNT(CASE WHEN s.events IN ('single', 'double', 'triple', 'home_run') THEN 1 END) as hits,
                    COUNT(CASE WHEN s.events = 'home_run' THEN 1 END) as home_runs,
                    COUNT(CASE WHEN s.events IN ('walk', 'intent_walk', 'hit_by_pitch') THEN 1 END) as walks,
                    COUNT(CASE WHEN s.events = 'strikeout' THEN 1 END) as strikeouts,
                    AVG(CASE 
                        WHEN s.launch_speed IS NOT NULL AND s.launch_speed > 0 
                        THEN s.launch_speed
                        ELSE NULL 
                    END) as avg_exit_velocity
                FROM statcast s
                JOIN mlb_players mp ON s.batter = mp.player_id
                WHERE s.game_date >= CURRENT_DATE - INTERVAL '30 days'
                  AND (mp.position_name LIKE '%Outfield%' OR mp.position_name LIKE '%Infield%' OR mp.position_name = 'Catcher' OR mp.position_name = 'Designated Hitter')
                GROUP BY s.batter, mp.full_name, mp.position_name
                HAVING COUNT(CASE WHEN s.events IN ('single', 'double', 'triple', 'home_run', 'field_out', 'grounded_into_double_play', 'force_out', 'fielders_choice', 'strikeout') THEN 1 END) >= 20
            )
            SELECT mlb_id, name, position, plate_appearances, at_bats, hits, home_runs, walks, strikeouts, avg_exit_velocity,
                   CASE 
                       WHEN at_bats > 0 THEN ROUND(hits::NUMERIC / at_bats, 3)
                       ELSE 0.000
                   END as batting_average
            FROM recent_stats
            WHERE at_bats >= 20
            ORDER BY home_runs DESC, batting_average DESC, plate_appearances DESC
            LIMIT :limit
        """)
        
        result = await session.execute(query, {"limit": limit})
        
        # Team abbreviations to full names mapping
        team_names = {
            'NYY': 'New York Yankees', 'BOS': 'Boston Red Sox', 'TB': 'Tampa Bay Rays',
            'TOR': 'Toronto Blue Jays', 'BAL': 'Baltimore Orioles', 'CWS': 'Chicago White Sox',
            'MIN': 'Minnesota Twins', 'DET': 'Detroit Tigers', 'CLE': 'Cleveland Guardians',
            'KC': 'Kansas City Royals', 'HOU': 'Houston Astros', 'TEX': 'Texas Rangers',
            'SEA': 'Seattle Mariners', 'LAA': 'Los Angeles Angels', 'OAK': 'Oakland Athletics',
            'ATL': 'Atlanta Braves', 'NYM': 'New York Mets', 'PHI': 'Philadelphia Phillies',
            'WSH': 'Washington Nationals', 'MIA': 'Miami Marlins', 'CHC': 'Chicago Cubs',
            'MIL': 'Milwaukee Brewers', 'CIN': 'Cincinnati Reds', 'STL': 'St. Louis Cardinals',
            'PIT': 'Pittsburgh Pirates', 'LAD': 'Los Angeles Dodgers', 'SF': 'San Francisco Giants',
            'SD': 'San Diego Padres', 'COL': 'Colorado Rockies', 'ARI': 'Arizona Diamondbacks'
        }
        
        trending = []
        for row in result.fetchall():
            trending.append({
                "id": row[0],        # mlb_id
                "name": row[1],      # name  
                "team": "MLB",
                "team_full_name": "Major League Baseball",
                "position": row[2],  # position
                "mlb_id": row[0],
                "local_image_path": None,
                "recent_activity": row[3],  # plate_appearances
                "stats": {
                    "at_bats": row[4],      # at_bats
                    "hits": row[5],         # hits
                    "home_runs": row[6],    # home_runs
                    "walks": row[7],        # walks
                    "strikeouts": row[8],   # strikeouts
                    "batting_average": float(row[10]) if row[10] else 0.000,  # batting_average
                    "avg_exit_velocity": round(float(row[9]), 1) if row[9] else None  # avg_exit_velocity
                }
            })
        
        return trending
        
    except Exception as e:
        import logging
        logging.error(f"Error getting trending players: {str(e)}")
        
        # Fallback to simpler query if complex one fails
        try:
            fallback_query = text("""
                SELECT p.id, p.full_name, p.player_id, NULL as local_image_path,
                       COUNT(*) as recent_activity
                FROM mlb_players p
                JOIN statcast s ON p.player_id = s.batter
                WHERE s.game_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY p.id, p.full_name, p.player_id
                ORDER BY recent_activity DESC
                LIMIT :limit
            """)
            
            result = await session.execute(fallback_query, {"limit": limit})
            
            trending = []
            for row in result.fetchall():
                trending.append({
                    "id": row[0],
                    "name": row[1],
                    "team": "MLB",
                    "team_full_name": "Major League Baseball",
                    "position": "Player",
                    "mlb_id": row[0], 
                    "local_image_path": None,
                    "recent_activity": row[4],
                    "stats": {
                        "at_bats": row[4],
                        "hits": 0,
                        "home_runs": 0, 
                        "walks": 0,
                        "strikeouts": 0,
                        "batting_average": 0.000,
                        "avg_exit_velocity": None
                    }
                })
            
            return trending
            
        except Exception as fallback_error:
            # Return empty list if all fails - frontend will handle gracefully
            return []