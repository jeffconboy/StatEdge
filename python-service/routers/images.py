"""
Image API endpoints for player headshots and team logos
Sprint: Player & Team Images Integration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, Optional
import logging

from database.connection import get_db_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/player/{player_id}/headshot")
async def get_player_headshot(
    player_id: int,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get player headshot URL with fallback handling"""
    
    try:
        # Get player info and headshot
        query = text("""
            SELECT 
                p.id,
                p.mlb_id,
                p.name,
                p.headshot_url,
                p.headshot_updated_at,
                t.logo_url as team_logo_url,
                t.primary_color,
                t.abbreviation as team_code
            FROM players p
            LEFT JOIN teams t ON p.current_team = t.abbreviation
            WHERE p.id = :player_id
        """)
        
        result = await session.execute(query, {"player_id": player_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Generate headshot URL if not set
        headshot_url = row[3]
        if not headshot_url and row[1]:  # mlb_id exists
            headshot_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{row[1]}/headshot/67/current"
        
        # Fallback URL for missing images
        fallback_url = "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/generic/headshot/67/current"
        
        return {
            "player_id": row[0],
            "mlb_id": row[1],
            "name": row[2],
            "headshot_url": headshot_url or fallback_url,
            "fallback_url": fallback_url,
            "team_logo_url": row[5],
            "team_primary_color": row[6],
            "team_code": row[7],
            "last_updated": row[4].isoformat() if row[4] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player headshot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving player image: {str(e)}")

@router.get("/team/{team_code}/logo")
async def get_team_logo(
    team_code: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get team logo and branding information"""
    
    try:
        query = text("""
            SELECT 
                abbreviation,
                full_name,
                city,
                logo_url,
                primary_color,
                secondary_color,
                league,
                division
            FROM teams
            WHERE abbreviation = :team_code
        """)
        
        result = await session.execute(query, {"team_code": team_code.upper()})
        row = result.fetchone()
        
        if not row:
            # Return generic team info for unknown teams
            return {
                "team_code": team_code.upper(),
                "full_name": f"{team_code} Team",
                "city": "Unknown",
                "logo_url": "https://cdn.mlbstatic.com/team-logos/generic.svg",
                "primary_color": "#000000",
                "secondary_color": "#FFFFFF",
                "league": "MLB",
                "division": "Unknown"
            }
        
        return {
            "team_code": row[0],
            "full_name": row[1],
            "city": row[2],
            "logo_url": row[3],
            "primary_color": row[4],
            "secondary_color": row[5],
            "league": row[6],
            "division": row[7]
        }
        
    except Exception as e:
        logger.error(f"Error getting team logo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving team logo: {str(e)}")

@router.get("/batch/players")
async def get_batch_player_images(
    player_ids: str,  # Comma-separated player IDs
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get multiple player images in one request for performance"""
    
    try:
        # Parse player IDs
        ids = [int(id.strip()) for id in player_ids.split(',') if id.strip().isdigit()]
        if not ids:
            return {"players": {}}
        
        # Limit to prevent abuse
        ids = ids[:20]
        
        query = text("""
            SELECT 
                p.id,
                p.mlb_id,
                p.name,
                p.headshot_url,
                p.current_team,
                t.logo_url as team_logo_url,
                t.primary_color
            FROM players p
            LEFT JOIN teams t ON p.current_team = t.abbreviation
            WHERE p.id = ANY(:player_ids)
        """)
        
        result = await session.execute(query, {"player_ids": ids})
        
        players = {}
        for row in result.fetchall():
            player_id = row[0]
            headshot_url = row[3]
            
            # Generate headshot URL if not set
            if not headshot_url and row[1]:  # mlb_id exists
                headshot_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{row[1]}/headshot/67/current"
            
            players[str(player_id)] = {
                "name": row[2],
                "headshot_url": headshot_url,
                "team_code": row[4],
                "team_logo_url": row[5],
                "team_primary_color": row[6]
            }
        
        return {
            "players": players,
            "count": len(players)
        }
        
    except Exception as e:
        logger.error(f"Error getting batch player images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving player images: {str(e)}")

@router.get("/trending-with-images")
async def get_trending_players_with_images(
    limit: int = 4,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get trending players with their images for dashboard display"""
    
    try:
        query = text("""
            SELECT 
                p.id,
                p.name,
                p.current_team,
                p.primary_position,
                p.headshot_url,
                p.mlb_id,
                t.full_name as team_full_name,
                t.logo_url as team_logo_url,
                t.primary_color as team_primary_color,
                COUNT(sp.id) as recent_activity
            FROM players p
            LEFT JOIN teams t ON p.current_team = t.abbreviation
            LEFT JOIN statcast_pitches sp ON p.mlb_id = sp.batter_id
                AND sp.game_date >= CURRENT_DATE - INTERVAL '7 days'
            WHERE p.active = true
            GROUP BY p.id, p.name, p.current_team, p.primary_position, 
                     p.headshot_url, p.mlb_id, t.full_name, t.logo_url, t.primary_color
            HAVING COUNT(sp.id) > 0
            ORDER BY recent_activity DESC
            LIMIT :limit
        """)
        
        result = await session.execute(query, {"limit": limit})
        
        trending_players = []
        for row in result.fetchall():
            headshot_url = row[4]
            
            # Generate headshot URL if not set
            if not headshot_url and row[5]:  # mlb_id exists
                headshot_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{row[5]}/headshot/67/current"
            
            trending_players.append({
                "id": row[0],
                "name": row[1],
                "team": row[2],
                "position": row[3],
                "headshot_url": headshot_url,
                "team_full_name": row[6],
                "team_logo_url": row[7],
                "team_primary_color": row[8],
                "recent_activity": row[9]
            })
        
        return {
            "trending_players": trending_players,
            "count": len(trending_players)
        }
        
    except Exception as e:
        logger.error(f"Error getting trending players with images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving trending players: {str(e)}")

@router.post("/player/{player_id}/headshot")
async def update_player_headshot(
    player_id: int,
    headshot_data: Dict[str, str],
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Update player headshot URL (admin function)"""
    
    try:
        headshot_url = headshot_data.get("headshot_url")
        if not headshot_url:
            raise HTTPException(status_code=400, detail="headshot_url is required")
        
        query = text("""
            UPDATE players 
            SET headshot_url = :headshot_url, headshot_updated_at = NOW()
            WHERE id = :player_id
            RETURNING id, name, headshot_url
        """)
        
        result = await session.execute(query, {
            "player_id": player_id,
            "headshot_url": headshot_url
        })
        await session.commit()
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return {
            "player_id": row[0],
            "name": row[1],
            "headshot_url": row[2],
            "updated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player headshot: {str(e)}")
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating headshot: {str(e)}")

@router.get("/player-comprehensive/{player_name}")
async def get_comprehensive_player_images(
    player_name: str,
    team_code: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get comprehensive player image data using ESPN mapping with fallbacks"""
    
    try:
        # Use the database function for comprehensive image data
        query = text("""
            SELECT get_player_image_data(:player_name, :team_code) as image_data
        """)
        
        result = await session.execute(query, {
            "player_name": player_name,
            "team_code": team_code
        })
        
        row = result.fetchone()
        if not row or not row[0]:
            # Manual fallback if function doesn't exist yet
            fallback_initials = ''.join([n[0] for n in player_name.split()]).upper()
            team_logo = f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_code.lower()}.png" if team_code else None
            
            return {
                "player_name": player_name,
                "team_code": team_code,
                "headshot_url": f"https://ui-avatars.com/api/?name={fallback_initials}&size=400&background=2563eb&color=ffffff&bold=true&format=png",
                "team_logo_url": team_logo,
                "espn_id": None,
                "has_espn_photo": False,
                "source": "fallback_manual"
            }
        
        image_data = row[0]
        image_data["player_name"] = player_name
        image_data["team_code"] = team_code
        image_data["source"] = "database_function"
        
        return image_data
        
    except Exception as e:
        logger.warning(f"Database function not available, using manual fallback: {str(e)}")
        
        # Manual ESPN ID mapping for known players
        known_espn_ids = {
            'Aaron Judge': '33192',
            'Mike Trout': '30836',
            'Mookie Betts': '33039',
            'Ronald Acuna Jr.': '36185',
            'Vladimir Guerrero Jr.': '35002',
            'Fernando Tatis Jr.': '35983',
            'Juan Soto': '36969',
            'Manny Machado': '31097',
            'Jose Altuve': '30204',
            'Freddie Freeman': '30896',
            'Cal Raleigh': '41292'
        }
        
        espn_id = known_espn_ids.get(player_name)
        
        if espn_id:
            headshot_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
            has_espn_photo = True
        else:
            fallback_initials = ''.join([n[0] for n in player_name.split()]).upper()
            headshot_url = f"https://ui-avatars.com/api/?name={fallback_initials}&size=400&background=2563eb&color=ffffff&bold=true&format=png"
            has_espn_photo = False
        
        team_logo = f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_code.lower()}.png" if team_code else None
        
        return {
            "player_name": player_name,
            "team_code": team_code,
            "headshot_url": headshot_url,
            "team_logo_url": team_logo,
            "espn_id": espn_id,
            "has_espn_photo": has_espn_photo,
            "source": "manual_mapping"
        }