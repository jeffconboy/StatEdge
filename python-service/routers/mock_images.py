"""
Mock Image API for testing - provides hardcoded image URLs for demo
Sprint: Player & Team Images Integration
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

# Mock player data with actual MLB CDN URLs
MOCK_PLAYERS = {
    "1": {  # Aaron Judge
        "player_id": 1,
        "mlb_id": 592450,
        "name": "Aaron Judge",
        "headshot_url": "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/592450/headshot/67/current",
        "team_code": "NYY",
        "team_logo_url": "https://www.mlbstatic.com/team-logos/132.svg",
        "team_primary_color": "#0C2340"
    },
    "6": {  # Mike Trout
        "player_id": 6,
        "mlb_id": 545361,
        "name": "Mike Trout",
        "headshot_url": "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/545361/headshot/67/current",
        "team_code": "LAA",
        "team_logo_url": "https://www.mlbstatic.com/team-logos/108.svg",
        "team_primary_color": "#BA0021"
    },
    "7": {  # Manny Machado
        "player_id": 7,
        "mlb_id": 592518,
        "name": "Manny Machado",
        "headshot_url": "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/592518/headshot/67/current",
        "team_code": "SD",
        "team_logo_url": "https://www.mlbstatic.com/team-logos/135.svg",
        "team_primary_color": "#2F241D"
    },
    "3": {  # Ronald Acuna Jr
        "player_id": 3,
        "mlb_id": 665742,
        "name": "Ronald Acuna Jr.",
        "headshot_url": "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/665742/headshot/67/current",
        "team_code": "ATL",
        "team_logo_url": "https://www.mlbstatic.com/team-logos/144.svg",
        "team_primary_color": "#CE1141"
    }
}

MOCK_TEAMS = {
    "NYY": {
        "team_code": "NYY",
        "full_name": "New York Yankees",
        "city": "New York",
        "logo_url": "https://www.mlbstatic.com/team-logos/132.svg",
        "primary_color": "#0C2340",
        "secondary_color": "#C4CED4"
    },
    "LAA": {
        "team_code": "LAA", 
        "full_name": "Los Angeles Angels",
        "city": "Los Angeles",
        "logo_url": "https://www.mlbstatic.com/team-logos/108.svg",
        "primary_color": "#BA0021",
        "secondary_color": "#003263"
    },
    "ATL": {
        "team_code": "ATL",
        "full_name": "Atlanta Braves", 
        "city": "Atlanta",
        "logo_url": "https://www.mlbstatic.com/team-logos/144.svg",
        "primary_color": "#CE1141",
        "secondary_color": "#13274F"
    },
    "SD": {
        "team_code": "SD",
        "full_name": "San Diego Padres",
        "city": "San Diego", 
        "logo_url": "https://www.mlbstatic.com/team-logos/135.svg",
        "primary_color": "#2F241D",
        "secondary_color": "#FFC425"
    }
}

@router.get("/player/{player_id}/headshot")
async def get_player_headshot_mock(player_id: str) -> Dict[str, Any]:
    """Mock player headshot endpoint"""
    
    player_data = MOCK_PLAYERS.get(player_id)
    if not player_data:
        # Generate generic headshot for any player ID
        return {
            "player_id": int(player_id),
            "name": f"Player {player_id}",
            "headshot_url": "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/generic/headshot/67/current",
            "fallback_url": "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/generic/headshot/67/current",
            "team_logo_url": "https://www.mlbstatic.com/team-logos/generic.svg",
            "team_primary_color": "#000000",
            "team_code": "MLB"
        }
    
    return {
        **player_data,
        "fallback_url": "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/generic/headshot/67/current"
    }

@router.get("/team/{team_code}/logo")
async def get_team_logo_mock(team_code: str) -> Dict[str, Any]:
    """Mock team logo endpoint"""
    
    team_data = MOCK_TEAMS.get(team_code.upper())
    if not team_data:
        return {
            "team_code": team_code.upper(),
            "full_name": f"{team_code} Team",
            "city": "Unknown",
            "logo_url": "https://www.mlbstatic.com/team-logos/generic.svg",
            "primary_color": "#000000",
            "secondary_color": "#FFFFFF"
        }
    
    return team_data

@router.get("/trending-with-images")
async def get_trending_players_with_images_mock(limit: int = 4) -> Dict[str, Any]:
    """Mock trending players with images"""
    
    trending_players = []
    player_keys = list(MOCK_PLAYERS.keys())[:limit]
    
    for i, player_id in enumerate(player_keys):
        player_data = MOCK_PLAYERS[player_id]
        team_data = MOCK_TEAMS.get(player_data["team_code"], {})
        
        trending_players.append({
            "id": player_data["player_id"],
            "name": player_data["name"],
            "team": player_data["team_code"],
            "position": ["RF", "CF", "3B", "OF"][i],
            "headshot_url": player_data["headshot_url"],
            "team_full_name": team_data.get("full_name", player_data["team_code"]),
            "team_logo_url": player_data["team_logo_url"],
            "team_primary_color": player_data["team_primary_color"],
            "recent_activity": [131, 119, 117, 110][i]
        })
    
    return {
        "trending_players": trending_players,
        "count": len(trending_players)
    }

@router.get("/batch/players")
async def get_batch_player_images_mock(player_ids: str) -> Dict[str, Any]:
    """Mock batch player images"""
    
    ids = [id.strip() for id in player_ids.split(',') if id.strip()]
    players = {}
    
    for player_id in ids[:10]:  # Limit to 10
        player_data = MOCK_PLAYERS.get(player_id)
        if player_data:
            players[player_id] = {
                "name": player_data["name"],
                "headshot_url": player_data["headshot_url"],
                "team_code": player_data["team_code"],
                "team_logo_url": player_data["team_logo_url"],
                "team_primary_color": player_data["team_primary_color"]
            }
    
    return {
        "players": players,
        "count": len(players)
    }