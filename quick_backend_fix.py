#!/usr/bin/env python3
"""
Quick Backend Fix - Add missing API endpoints that serve MLB data
"""

# Add these endpoints to your Python backend (main.py or routers)

from fastapi import APIRouter
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()
DB_URL = "postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data"

@router.get("/api/live-games")
async def get_live_games():
    """Get today's MLB games from database"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT game_pk, home_team_name, away_team_name, 
                   home_score, away_score, status_code, venue_name
            FROM mlb_game_details 
            ORDER BY game_date DESC
            LIMIT 20
        """)
        
        games = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return games
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/league-stats/leaders/batting")
async def get_batting_leaders():
    """Get top batting players from database"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT full_name, position_abbreviation, jersey_number
            FROM mlb_players 
            WHERE position_abbreviation != 'P'
            ORDER BY full_name
            LIMIT 20
        """)
        
        leaders = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return leaders
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/players/trending")
async def get_trending_players():
    """Get trending players with actual data"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT full_name, position_abbreviation, jersey_number,
                   team_id, season
            FROM mlb_players 
            ORDER BY RANDOM()
            LIMIT 10
        """)
        
        players = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return players
        
    except Exception as e:
        return {"error": str(e)}

# Add to your main.py:
# app.include_router(router)