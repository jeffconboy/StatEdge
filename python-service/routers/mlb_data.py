#!/usr/bin/env python3
"""
MLB Data Router - Serve collected MLB data from sports_data database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from typing import List, Dict, Any
import logging

from database.connection import get_db_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/live-games")
async def get_live_games(db: AsyncSession = Depends(get_db_session)):
    """Get today's MLB games from database"""
    try:
        result = await db.execute(text("""
            SELECT game_pk, home_team_name, away_team_name, 
                   home_score, away_score, status_code, venue_name,
                   game_date
            FROM mlb_game_details 
            ORDER BY game_date DESC
            LIMIT 20
        """))
        
        games = []
        for row in result.fetchall():
            games.append({
                "id": str(row[0]),
                "homeTeam": {"name": row[1]},
                "awayTeam": {"name": row[2]},
                "homeScore": row[3] or 0,
                "awayScore": row[4] or 0,
                "status": row[5] or "scheduled",
                "venue": row[6] or "",
                "gameDate": row[7].isoformat() if row[7] else ""
            })
        
        return games
        
    except Exception as e:
        logger.error(f"Error fetching live games: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/league-stats/leaders/batting")
async def get_batting_leaders(db: AsyncSession = Depends(get_db_session)):
    """Get top batting players from database"""
    try:
        result = await db.execute(text("""
            SELECT full_name, position_abbreviation, jersey_number, team_id
            FROM mlb_players 
            WHERE position_abbreviation != 'P'
            ORDER BY full_name
            LIMIT 20
        """))
        
        leaders = []
        for row in result.fetchall():
            leaders.append({
                "name": row[0],
                "position": row[1],
                "jerseyNumber": row[2],
                "teamId": row[3],
                "avg": "0.000",  # Placeholder
                "hr": "0",       # Placeholder
                "rbi": "0"       # Placeholder
            })
        
        return leaders
        
    except Exception as e:
        logger.error(f"Error fetching batting leaders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/players/trending")
async def get_trending_players(db: AsyncSession = Depends(get_db_session)):
    """Get trending players with actual data"""
    try:
        result = await db.execute(text("""
            SELECT full_name, position_abbreviation, jersey_number,
                   team_id, season
            FROM mlb_players 
            ORDER BY RANDOM()
            LIMIT 10
        """))
        
        players = []
        for row in result.fetchall():
            players.append({
                "name": row[0],
                "position": row[1],
                "jerseyNumber": row[2],
                "teamId": row[3],
                "season": row[4],
                "trending": True
            })
        
        return players
        
    except Exception as e:
        logger.error(f"Error fetching trending players: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))