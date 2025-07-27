from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import os
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sports_user:sports_secure_2025@sports-db:5432/sports_data")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create FastAPI app
app = FastAPI(
    title="StatEdge API",
    description="Baseball analytics and betting research API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "StatEdge Backend API"}

@app.get("/api/players/trending")
async def get_trending_players(limit: int = 10):
    """Get trending players with real stats from recent games"""
    
    async with AsyncSessionLocal() as session:
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
            logger.error(f"Error getting trending players: {str(e)}")
            # Return empty list if query fails - frontend will handle gracefully
            return []

@app.get("/api/players/search")
async def search_players(query: str, limit: int = 10):
    """Search for players by name"""
    
    async with AsyncSessionLocal() as session:
        try:
            search_query = text("""
                SELECT id, player_id, full_name, team_id, position_name, status_code
                FROM mlb_players 
                WHERE full_name ILIKE :search_term
                ORDER BY 
                    CASE WHEN full_name ILIKE :exact_term THEN 1 ELSE 2 END,
                    full_name
                LIMIT :limit
            """)
            
            result = await session.execute(search_query, {
                "search_term": f"%{query}%",
                "exact_term": f"{query}%",
                "limit": limit
            })
            
            players = []
            for row in result.fetchall():
                players.append({
                    "id": row[0],
                    "mlb_id": row[1],
                    "name": row[2],
                    "team": row[3],
                    "position": row[4],
                    "active": row[5]
                })
            
            return {"players": players}
            
        except Exception as e:
            logger.error(f"Error searching players: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error searching players: {str(e)}")

@app.get("/api/players/{player_id}/summary")
async def get_player_summary(player_id: int):
    """Get player summary with basic info"""
    
    async with AsyncSessionLocal() as session:
        try:
            player_query = text("""
                SELECT id, player_id, full_name, team_id, position_name
                FROM mlb_players WHERE player_id = :player_id
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
                "position": player_row[4]
            }
            
            return {"player_info": player_info}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting player summary: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting player summary: {str(e)}")

@app.get("/api/games/today")
async def get_todays_games():
    """Get today's games - placeholder endpoint"""
    return {
        "games": [
            {
                "id": "game1",
                "homeTeam": {"name": "Yankees", "abbreviation": "NYY"},
                "awayTeam": {"name": "Red Sox", "abbreviation": "BOS"},
                "homeScore": 0,
                "awayScore": 0,
                "status": "scheduled",
                "time": "7:00 PM ET"
            }
        ],
        "date": "2025-07-27",
        "total_games": 1,
        "last_updated": "2025-07-27T01:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)